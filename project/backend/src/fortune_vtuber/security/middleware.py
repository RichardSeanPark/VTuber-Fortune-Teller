"""
보안 미들웨어 모듈
Rate limiting, 보안 헤더, 로깅 등 보안 관련 미들웨어 구현
"""

import time
import logging
import json
import re
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException

try:
    from ..config.logging_config import get_logger, log_security_event_deduplicated
    logger = get_logger(__name__)
except ImportError:
    # Fallback to standard logging if new system not available
    logger = logging.getLogger(__name__)


class SecurityLogger:
    """보안 이벤트 로깅 시스템 - 새로운 통합 로깅 시스템 사용"""
    
    def __init__(self):
        try:
            # 새로운 통합 로깅 시스템 사용
            self.security_logger = get_logger("security")
        except NameError:
            # Fallback: 기존 방식
            self.security_logger = logging.getLogger("security")
            if not self.security_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.security_logger.addHandler(handler)
                self.security_logger.setLevel(logging.INFO)
                self.security_logger.propagate = False
    
    def log_rate_limit_exceeded(self, client_ip: str, endpoint: str, request_count: int):
        """Rate limit 초과 로깅"""
        self.security_logger.warning(
            f"Rate limit exceeded - IP: {client_ip}, "
            f"Endpoint: {endpoint}, Count: {request_count}"
        )
    
    def log_suspicious_activity(self, client_ip: str, user_agent: str, endpoint: str, reason: str):
        """의심스러운 활동 로깅"""
        self.security_logger.warning(
            f"Suspicious activity - IP: {client_ip}, "
            f"User-Agent: {user_agent}, Endpoint: {endpoint}, "
            f"Reason: {reason}"
        )
    
    def log_content_filtered(self, client_ip: str, category: str, confidence: float, content_preview: str):
        """콘텐츠 필터링 로깅"""
        self.security_logger.info(
            f"Content filtered - IP: {client_ip}, "
            f"Category: {category}, Confidence: {confidence:.2f}, "
            f"Preview: {content_preview[:50]}..."
        )
    
    def log_security_event(self, event_type: str, client_ip: str, details: Dict):
        """일반 보안 이벤트 로깅 - 중복 방지 적용"""
        try:
            # 새로운 중복 방지 로깅 시스템 사용
            log_security_event_deduplicated(event_type, client_ip, details)
        except NameError:
            # Fallback: 기존 방식
            self.security_logger.info(
                f"Security event - Type: {event_type}, IP: {client_ip}, "
                f"Details: {json.dumps(details, ensure_ascii=False)}"
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate Limiting 미들웨어"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests: Dict[str, deque] = defaultdict(deque)
        self.security_logger = SecurityLogger()
        
        # 엔드포인트별 특별 제한
        self.endpoint_limits = {
            "/api/v1/fortune": 10,  # 운세 API는 더 엄격하게
            "/api/v1/chat": 30,     # 채팅은 조금 더 여유롭게
            "/api/v1/user": 20,     # 사용자 API 중간
        }
        
        # 화이트리스트 IP (개발/테스트용)
        self.whitelist_ips: Set[str] = {
            "127.0.0.1",
            "::1",
            "localhost"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Rate limiting 검사 및 요청 처리"""
        client_ip = self._get_client_ip(request)
        
        # 화이트리스트 IP는 제한 없음
        if client_ip in self.whitelist_ips:
            return await call_next(request)
        
        # Health check는 제한 없음
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)
        
        current_time = time.time()
        endpoint_group = self._get_endpoint_group(request.url.path)
        rate_limit = self.endpoint_limits.get(endpoint_group, self.requests_per_minute)
        
        # 클라이언트별 요청 기록 정리 (1분 이전 요청 제거)
        client_queue = self.client_requests[client_ip]
        while client_queue and client_queue[0] <= current_time - 60:
            client_queue.popleft()
        
        # 현재 요청 수 확인
        if len(client_queue) >= rate_limit:
            self.security_logger.log_rate_limit_exceeded(
                client_ip, endpoint_group, len(client_queue)
            )
            
            # 429 Too Many Requests 응답
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
                        "status_code": 429
                    },
                    "metadata": {
                        "retry_after": 60,
                        "rate_limit": rate_limit,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                headers={"Retry-After": "60"}
            )
        
        # 현재 요청 기록
        client_queue.append(current_time)
        
        # 의심스러운 패턴 탐지
        self._detect_suspicious_patterns(client_ip, request)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # X-Forwarded-For 헤더 확인 (프록시/로드밸런서 사용시)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # X-Real-IP 헤더 확인
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # 기본 클라이언트 IP
        return request.client.host
    
    def _get_endpoint_group(self, path: str) -> str:
        """엔드포인트 그룹 분류"""
        if path.startswith("/api/v1/fortune"):
            return "/api/v1/fortune"
        elif path.startswith("/api/v1/chat"):
            return "/api/v1/chat"
        elif path.startswith("/api/v1/user"):
            return "/api/v1/user"
        else:
            return "other"
    
    def _detect_suspicious_patterns(self, client_ip: str, request: Request):
        """의심스러운 패턴 탐지"""
        user_agent = request.headers.get("User-Agent", "")
        
        # 의심스러운 User-Agent 패턴
        suspicious_agents = [
            "bot", "crawler", "spider", "scraper", 
            "curl", "wget", "python", "scanner"
        ]
        
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            self.security_logger.log_suspicious_activity(
                client_ip, user_agent, request.url.path, "Suspicious User-Agent"
            )
        
        # 빈 User-Agent
        if not user_agent:
            self.security_logger.log_suspicious_activity(
                client_ip, user_agent, request.url.path, "Empty User-Agent"
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 추가 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 보안 헤더 추가
        security_headers = {
            # XSS 보호
            "X-XSS-Protection": "1; mode=block",
            
            # Content Type 추론 방지
            "X-Content-Type-Options": "nosniff",
            
            # 클릭재킹 방지
            "X-Frame-Options": "DENY",
            
            # HSTS (HTTPS 환경에서만)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # 레퍼러 정책
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # 권한 정책
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_logger = SecurityLogger()
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        # 민감한 엔드포인트 로깅
        sensitive_endpoints = ["/api/v1/user", "/api/v1/chat"]
        should_log = any(request.url.path.startswith(endpoint) for endpoint in sensitive_endpoints)
        
        if should_log:
            self.security_logger.log_security_event(
                "REQUEST_START",
                client_ip,
                {
                    "method": request.method,
                    "path": request.url.path,
                    "user_agent": request.headers.get("User-Agent", ""),
                    "referer": request.headers.get("Referer", "")
                }
            )
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 오류 응답이나 느린 응답 로깅
        if response.status_code >= 400 or process_time > 5.0:
            self.security_logger.log_security_event(
                "REQUEST_ISSUE",
                client_ip,
                {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 3),
                    "slow_request": process_time > 5.0,
                    "error_response": response.status_code >= 400
                }
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        return request.client.host


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """입력 데이터 사니타이징 미들웨어"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_logger = SecurityLogger()
        
        # 위험한 패턴들
        self.sql_injection_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bSELECT\b.*\bFROM\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"('.*OR.*'.*=.*')",
            r"(;.*--)",
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ]
    
    async def dispatch(self, request: Request, call_next):
        # POST 요청의 경우 본문 검사
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # 본문 읽기 (JSON인 경우)
                body = await request.body()
                if body:
                    await self._check_request_body(request, body)
            except Exception as e:
                logger.warning(f"Failed to check request body: {e}")
        
        # 쿼리 파라미터 검사
        await self._check_query_params(request)
        
        return await call_next(request)
    
    async def _check_request_body(self, request: Request, body: bytes):
        """요청 본문 검사"""
        try:
            body_str = body.decode('utf-8').lower()
            client_ip = self._get_client_ip(request)
            
            # SQL Injection 패턴 검사
            for pattern in self.sql_injection_patterns:
                if re.search(pattern, body_str, re.IGNORECASE):
                    self.security_logger.log_security_event(
                        "SQL_INJECTION_ATTEMPT",
                        client_ip,
                        {
                            "path": request.url.path,
                            "pattern": pattern,
                            "body_preview": body_str[:200]
                        }
                    )
            
            # XSS 패턴 검사
            for pattern in self.xss_patterns:
                if re.search(pattern, body_str, re.IGNORECASE):
                    self.security_logger.log_security_event(
                        "XSS_ATTEMPT",
                        client_ip,
                        {
                            "path": request.url.path,
                            "pattern": pattern,
                            "body_preview": body_str[:200]
                        }
                    )
        
        except Exception as e:
            logger.warning(f"Error checking request body: {e}")
    
    async def _check_query_params(self, request: Request):
        """쿼리 파라미터 검사"""
        client_ip = self._get_client_ip(request)
        
        for param_name, param_value in request.query_params.items():
            param_value_lower = param_value.lower()
            
            # SQL Injection 패턴 검사
            for pattern in self.sql_injection_patterns:
                if re.search(pattern, param_value_lower, re.IGNORECASE):
                    self.security_logger.log_security_event(
                        "SQL_INJECTION_ATTEMPT",
                        client_ip,
                        {
                            "path": request.url.path,
                            "param": param_name,
                            "pattern": pattern,
                            "value": param_value[:100]
                        }
                    )
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        return request.client.host


# 전역 인스턴스
security_logger = SecurityLogger()
"""
입력 검증 및 데이터 사니타이징 모듈
Pydantic validator와 보안 검증 함수들
"""

import re
import html
from typing import Any, Optional, List, Dict
from pydantic import validator, Field
from fastapi import HTTPException


class SecurityValidators:
    """보안 검증을 위한 정적 메서드 모음"""
    
    # 위험한 패턴들
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"('.*OR.*'.*=.*')",
        r"(;.*--)",
        r"(\bEXEC\b|\bEXECUTE\b)",
        r"(\bSP_\w+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<form[^>]*>",
        r"<input[^>]*>",
        r"<meta[^>]*>",
        r"<link[^>]*>",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"(;|\||\&|\`)",
        r"(\$\(.*\))",
        r"(\$\{.*\})",
        r"(&&|\|\|)",
        r"(>\s*/dev/null)",
        r"(2>&1)",
    ]
    
    LDAP_INJECTION_PATTERNS = [
        r"(\*\)(\(.*=.*\*)",
        r"(\)\(\&)",
        r"(\)\(\|)",
        r"(\*\)\(\|.*\))",
    ]
    
    @staticmethod
    def check_sql_injection(value: str) -> bool:
        """SQL 인젝션 패턴 검사"""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        for pattern in SecurityValidators.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def check_xss(value: str) -> bool:
        """XSS 패턴 검사"""
        if not isinstance(value, str):
            return False
        
        for pattern in SecurityValidators.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def check_command_injection(value: str) -> bool:
        """Command injection 패턴 검사"""
        if not isinstance(value, str):
            return False
        
        for pattern in SecurityValidators.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                return True
        return False
    
    @staticmethod
    def check_ldap_injection(value: str) -> bool:
        """LDAP injection 패턴 검사"""
        if not isinstance(value, str):
            return False
        
        for pattern in SecurityValidators.LDAP_INJECTION_PATTERNS:
            if re.search(pattern, value):
                return True
        return False
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """HTML 태그 이스케이프"""
        if not isinstance(value, str):
            return value
        return html.escape(value)
    
    @staticmethod
    def validate_text_length(value: str, min_length: int = 0, max_length: int = 1000) -> str:
        """텍스트 길이 검증"""
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        
        if len(value.strip()) < min_length:
            raise ValueError(f"Text must be at least {min_length} characters long")
        
        if len(value) > max_length:
            raise ValueError(f"Text must be no more than {max_length} characters long")
        
        return value.strip()
    
    @staticmethod
    def validate_user_input(value: str, allow_html: bool = False) -> str:
        """사용자 입력 종합 검증"""
        if not value:
            return value
        
        # SQL Injection 검사
        if SecurityValidators.check_sql_injection(value):
            raise ValueError("Potentially malicious input detected (SQL)")
        
        # XSS 검사
        if SecurityValidators.check_xss(value):
            raise ValueError("Potentially malicious input detected (XSS)")
        
        # Command Injection 검사
        if SecurityValidators.check_command_injection(value):
            raise ValueError("Potentially malicious input detected (Command)")
        
        # LDAP Injection 검사
        if SecurityValidators.check_ldap_injection(value):
            raise ValueError("Potentially malicious input detected (LDAP)")
        
        # HTML 이스케이프 (허용하지 않는 경우)
        if not allow_html:
            value = SecurityValidators.sanitize_html(value)
        
        return value
    
    @staticmethod
    def validate_fortune_query(value: str) -> str:
        """운세 쿼리 특별 검증"""
        if not value:
            return value
        
        # 기본 보안 검증
        value = SecurityValidators.validate_user_input(value)
        
        # 운세 관련 특별 검증
        value = SecurityValidators.validate_text_length(value, 1, 500)  # 운세 질문은 최대 500자
        
        # 반복 문자 제한
        if re.search(r'(.)\1{5,}', value):
            raise ValueError("Too many repeated characters")
        
        # 특수문자 남용 방지
        special_char_count = len(re.findall(r'[!@#$%^&*()_+={}\[\]|\\:";\'<>?,./]', value))
        if special_char_count > len(value) * 0.3:
            raise ValueError("Too many special characters")
        
        return value
    
    @staticmethod
    def validate_user_name(value: str) -> str:
        """사용자 이름 검증"""
        if not value:
            return value
        
        # 기본 보안 검증
        value = SecurityValidators.validate_user_input(value)
        
        # 이름 특별 검증
        value = SecurityValidators.validate_text_length(value, 1, 50)
        
        # 한글, 영문, 숫자, 공백만 허용
        if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', value):
            raise ValueError("Name can only contain Korean, English, numbers, and spaces")
        
        return value
    
    @staticmethod
    def validate_birth_date(value: str) -> str:
        """생년월일 검증"""
        if not value:
            return value
        
        # YYYY-MM-DD 형식 검증
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            raise ValueError("Birth date must be in YYYY-MM-DD format")
        
        # 날짜 범위 검증 (1900-2030)
        year = int(value[:4])
        if year < 1900 or year > 2030:
            raise ValueError("Birth year must be between 1900 and 2030")
        
        return value
    
    @staticmethod
    def validate_birth_time(value: str) -> str:
        """태어난 시간 검증"""
        if not value:
            return value
        
        # HH:MM 또는 HH:MM:SS 형식 검증
        if not re.match(r'^\d{2}:\d{2}(:\d{2})?$', value):
            raise ValueError("Birth time must be in HH:MM or HH:MM:SS format")
        
        # 시간 범위 검증
        hour = int(value[:2])
        minute = int(value[3:5])
        
        if hour > 23 or minute > 59:
            raise ValueError("Invalid time format")
        
        return value


def create_security_validator(
    check_sql: bool = True,
    check_xss: bool = True,
    check_command: bool = True,
    check_ldap: bool = True,
    allow_html: bool = False,
    min_length: int = 0,
    max_length: int = 1000
):
    """보안 검증 validator 팩토리 함수"""
    
    def security_validator(cls, value):
        if not value:
            return value
        
        if not isinstance(value, str):
            return value
        
        # 길이 검증
        try:
            value = SecurityValidators.validate_text_length(value, min_length, max_length)
        except ValueError as e:
            raise ValueError(str(e))
        
        # 보안 패턴 검증
        if check_sql and SecurityValidators.check_sql_injection(value):
            raise ValueError("Potentially malicious input detected (SQL injection)")
        
        if check_xss and SecurityValidators.check_xss(value):
            raise ValueError("Potentially malicious input detected (XSS)")
        
        if check_command and SecurityValidators.check_command_injection(value):
            raise ValueError("Potentially malicious input detected (Command injection)")
        
        if check_ldap and SecurityValidators.check_ldap_injection(value):
            raise ValueError("Potentially malicious input detected (LDAP injection)")
        
        # HTML 이스케이프
        if not allow_html:
            value = SecurityValidators.sanitize_html(value)
        
        return value
    
    return validator('*', allow_reuse=True)(security_validator)


# 자주 사용되는 validator들
secure_text_validator = create_security_validator()
secure_short_text_validator = create_security_validator(max_length=100)
secure_name_validator = create_security_validator(max_length=50)
secure_query_validator = create_security_validator(max_length=500)
secure_message_validator = create_security_validator(max_length=2000)


def validate_request_data(data: Dict[str, Any], validation_rules: Dict[str, Dict]) -> Dict[str, Any]:
    """요청 데이터 일괄 검증"""
    validated_data = {}
    
    for field, value in data.items():
        if field in validation_rules:
            rules = validation_rules[field]
            
            # 필수 필드 체크
            if rules.get('required', False) and not value:
                raise HTTPException(
                    status_code=422,
                    detail=f"Field '{field}' is required"
                )
            
            # 타입 체크
            expected_type = rules.get('type')
            if expected_type and value is not None and not isinstance(value, expected_type):
                raise HTTPException(
                    status_code=422,
                    detail=f"Field '{field}' must be of type {expected_type.__name__}"
                )
            
            # 보안 검증
            if isinstance(value, str) and rules.get('security_check', True):
                try:
                    value = SecurityValidators.validate_user_input(
                        value,
                        allow_html=rules.get('allow_html', False)
                    )
                except ValueError as e:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Security validation failed for field '{field}': {str(e)}"
                    )
            
            validated_data[field] = value
        else:
            validated_data[field] = value
    
    return validated_data
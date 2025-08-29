#!/usr/bin/env python3
"""
Live2D Commands 실제 데이터 구조 확인
"""

import requests
import json

def debug_live2d_commands():
    url = "http://127.0.0.1:8001/api/v1/tts/generate"
    
    test_data = {
        "text": "안녕하세요",
        "user_id": "debug",
        "session_id": "debug_live2d",
        "language": "ko-KR",
        "enable_lipsync": True,
        "enable_expressions": True,
        "enable_motions": True
    }
    
    response = requests.post(url, json=test_data, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", {})
        
        live2d_commands = data.get("live2d_commands", [])
        
        print("📋 Live2D Commands 데이터 구조:")
        print("=" * 60)
        
        lipsync_commands = [cmd for cmd in live2d_commands if cmd.get("type") == "lipsync"]
        
        print(f"전체 명령어 수: {len(live2d_commands)}")
        print(f"립싱크 명령어 수: {len(lipsync_commands)}")
        
        if lipsync_commands:
            print(f"\n첫 번째 립싱크 명령어:")
            print(json.dumps(lipsync_commands[0], indent=2, ensure_ascii=False))
            
            print(f"\n두 번째 립싱크 명령어:")  
            if len(lipsync_commands) > 1:
                print(json.dumps(lipsync_commands[1], indent=2, ensure_ascii=False))
            
            print(f"\n마지막 립싱크 명령어:")
            print(json.dumps(lipsync_commands[-1], indent=2, ensure_ascii=False))
        else:
            print("⚠️ 립싱크 명령어가 없습니다!")
            
        print(f"\n다른 명령어 타입들:")
        command_types = set(cmd.get("type") for cmd in live2d_commands)
        for cmd_type in command_types:
            count = sum(1 for cmd in live2d_commands if cmd.get("type") == cmd_type)
            print(f"  {cmd_type}: {count}개")

if __name__ == "__main__":
    debug_live2d_commands()
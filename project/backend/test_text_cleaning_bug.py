#!/usr/bin/env python3
"""
Test script to verify the text cleaning bug
"""

import re

def current_broken_clean_function(text: str) -> str:
    """Current broken version of clean_text_for_tts"""
    if not text:
        return "죄송합니다. 메시지가 없습니다."
    
    original_text = text
    
    # This is the problematic emoji pattern 
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # Miscellaneous Symbols
        "\U000024C2-\U0001F251"  # Enclosed characters - THIS IS THE PROBLEM!
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Clean up spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def fixed_clean_function(text: str) -> str:
    """Fixed version that preserves Korean characters - matches the actual fix"""
    if not text:
        return "죄송합니다. 메시지가 없습니다."
    
    original_text = text
    
    # Properly targeted emoji pattern that doesn't include Korean characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs  
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # Miscellaneous Symbols
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U00002600-\U000026FF"  # Miscellaneous Symbols
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Remove specific problematic symbols for TTS
    special_symbols = ['★', '☆', '♥', '♡', '❤', '💖', '💕', '🎯', '✨', '🌟', 
                      '🔮', '🎴', '🃏', '💫', '⭐', '🌙', '☀', '🌈', '💎',
                      '👑', '🎊', '🎉', '🎈', '🎁', '🌹', '🌸', '🌺', '🌻']
    for symbol in special_symbols:
        text = text.replace(symbol, '')
    
    # Clean up spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Handle empty or problematic results
    problematic_texts = [".", "..", "...", "....", ".....", ". . . .", ". . . . .", ". , . ,", ". , . , . .", "　", " "]
    if not text or text in problematic_texts:
        text = "잠시만 기다려주세요."
    
    if len(text) < 3:
        text = "잠시만 기다려주세요."
    
    return text

def test_text_cleaning():
    """Test both versions with Korean text"""
    test_text = "오늘은 영예롭고 명예로운 하루가 될 것입니다. 새로운 기회를 만나고, 상을 받을 것입니다. 또한, 고마운 사람들과 즐거운 시간을 보내게 됩니다. 오늘은 확신과 긍정에 가득한 하루일 것입니다."
    
    print(f"원본 텍스트: '{test_text}'")
    print(f"길이: {len(test_text)}")
    print()
    
    broken_result = current_broken_clean_function(test_text)
    print(f"현재 (망가진) 결과: '{broken_result}'")
    print(f"길이: {len(broken_result)}")
    print()
    
    fixed_result = fixed_clean_function(test_text)
    print(f"수정된 결과: '{fixed_result}'")  
    print(f"길이: {len(fixed_result)}")
    print()
    
    # Test Korean character unicode ranges
    print("Korean character analysis:")
    for i, char in enumerate(test_text[:10]):  # Check first 10 chars
        unicode_val = ord(char)
        print(f"  '{char}': U+{unicode_val:04X} ({'Korean' if 0xAC00 <= unicode_val <= 0xD7AF else 'Other'})")

if __name__ == "__main__":
    test_text_cleaning()
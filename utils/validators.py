"""
Input validation and sanitization.
"""

import re

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Strips control characters, limits length, and trims whitespace.
    """
    if not text:
        return ""
        
    # Cap length
    text = text[:max_length]
    
    # Remove control characters (except common whitespace like \n, \t)
    # Keeping it simple for the demo.
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()

def is_valid_user_id(user_id: str) -> bool:
    """Basic validation for user_id."""
    return bool(user_id and user_id.isalnum() and len(user_id) < 50)

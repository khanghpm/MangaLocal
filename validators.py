import re

class ValidationError(Exception):
    """Custom validation exception"""
    pass

def validate_email(email):
    """
    Validate email format
    - Must be valid email
    - Max 120 characters
    """
    if not email or len(email) > 120:
        raise ValidationError("Email must be between 1-120 characters")
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Email format is invalid. Please use a valid email address.")
    
    return True

def validate_password(password):
    """
    Validate password strength
    - Min 6 characters
    - Min 1 uppercase
    - Min 1 number
    - Optional: special characters
    """
    if not password:
        raise ValidationError("Password is required")
    
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long")
    
    if len(password) > 100:
        raise ValidationError("Password is too long (max 100 characters)")
    
    # Check if has at least 1 uppercase letter
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least 1 uppercase letter")
    
    # Check if has at least 1 number
    if not re.search(r'[0-9]', password):
        raise ValidationError("Password must contain at least 1 number")
    
    return True

def validate_username(username):
    """
    Validate username (if needed)
    - Alphanumeric + underscore only
    - 3-20 characters
    """
    if not username or len(username) < 3 or len(username) > 20:
        raise ValidationError("Username must be between 3-20 characters")
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError("Username can only contain letters, numbers, and underscores")
    
    return True

def validate_search_query(query):
    """
    Validate search query
    - Not empty
    - Max 100 characters
    """
    if len(query) > 100:
        raise ValidationError("Search query is too long (max 100 characters)")
    
    return True
import hashlib

def mask_email(email: str) -> str:
    """
    Mask email addresses by hashing the local part (before @).
    
    Args:
        email: The email address to mask
        
    Returns:
        Masked email address with hashed local part
    """
    if not email or '@' not in email:
        return email
        
    local_part, domain = email.split('@', 1)
    hashed_local = hashlib.md5(local_part.encode()).hexdigest()
    
    return f"{hashed_local}@{domain}" 

def mask_phone(phone: str) -> str:
    """
    Mask phone numbers by keeping only the last 4 digits and hashing the rest.
    
    Args:
        phone: The phone number to mask
        
    Returns:
        Masked phone number with only last 4 digits visible
    """
    if not phone:
        return phone
    
    # Extract last 4 digits
    last_four = phone[-4:] if len(phone) >= 4 else phone
    
    # Hash the rest of the digits
    if len(phone) > 4:
        prefix = phone[:-4]
        hashed_prefix = hashlib.md5(prefix.encode()).hexdigest()[:8]  # Use first 8 chars of hash
        return f"{hashed_prefix}****{last_four}"
    
    return phone 
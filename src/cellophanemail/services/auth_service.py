"""Authentication service for user signup and login functionality."""

import bcrypt
import random
import re
import uuid
from src.cellophanemail.models.user import User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hash string
    """
    # Convert password to bytes and hash with bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash.
    
    Args:
        password: Plain text password to verify
        hashed: Bcrypt hash to verify against
        
    Returns:
        True if password matches hash, False otherwise
    """
    # Convert inputs to bytes
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    
    # Use bcrypt to check password
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_shield_username(email: str) -> str:
    """Generate a unique shield username from an email address.
    
    Args:
        email: User's email address
        
    Returns:
        Shield username in format: username123
    """
    # Extract the local part of the email (before @)
    local_part = email.split('@')[0]
    
    # Remove special characters and convert to lowercase
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', local_part).lower()
    
    # If name is too long, truncate it
    if len(clean_name) > 10:
        clean_name = clean_name[:10]
    
    # Generate random 3-digit number for uniqueness
    random_number = random.randint(100, 999)
    
    return f"{clean_name}{random_number}"


def generate_verification_token() -> str:
    """Generate a unique verification token for email verification.
    
    Returns:
        UUID-based verification token string
    """
    return str(uuid.uuid4())


async def validate_email_unique(email: str) -> bool:
    """Check if an email address is unique in the database.
    
    Args:
        email: Email address to check
        
    Returns:
        True if email is unique, False if it already exists
    """
    exists = await User.exists().where(User.email == email).run()
    return not exists


async def create_user(email: str, password: str, first_name: str = None, last_name: str = None) -> User:
    """Create a new user with hashed password and shield address.
    
    Args:
        email: User's email address
        password: Plain text password (will be hashed)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        
    Returns:
        Created User instance
    """
    # Hash the password
    password_hash = hash_password(password)
    
    # Generate shield username  
    shield_username = generate_shield_username(email)
    
    # Generate email verification token
    verification_token = generate_verification_token()
    
    # Create user instance
    user = User(
        email=email,
        hashed_password=password_hash,  
        username=shield_username,  
        first_name=first_name,
        last_name=last_name,
        verification_token=verification_token,
        is_verified=False
        # created_at and updated_at are set automatically by Piccolo
    )
    
    # Save to database
    await user.save().run()
    
    return user
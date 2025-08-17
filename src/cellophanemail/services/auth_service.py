"""Authentication service for user signup and login functionality."""

import bcrypt
import httpx
import random
import re
import uuid
from cellophanemail.models.user import User


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


async def create_user_from_oauth_profile(oauth_profile: dict, provider: str) -> User:
    """Create a new user from OAuth profile data.
    
    Args:
        oauth_profile: OAuth profile data containing user information
        provider: OAuth provider name (e.g., "google")
        
    Returns:
        Created User instance
        
    Raises:
        ValueError: If required OAuth profile data is missing
    """
    # Validate required OAuth profile data
    email = oauth_profile.get("email")
    if not email:
        raise ValueError("OAuth profile must contain an email address")
    
    # Extract profile data with defaults
    first_name = oauth_profile.get("given_name")
    last_name = oauth_profile.get("family_name") 
    is_email_verified = oauth_profile.get("email_verified", False)
    oauth_id = oauth_profile.get("sub") or oauth_profile.get("id")  # OAuth provider user ID
    
    # Generate shield username from email
    shield_username = generate_shield_username(email)
    
    # Create user instance - OAuth users don't have passwords
    user = User(
        email=email,
        hashed_password=None,  # OAuth users authenticate via OAuth only
        oauth_provider=provider,  # Store OAuth provider (e.g., "google")
        oauth_id=oauth_id,  # Store provider-specific user ID
        username=shield_username,
        first_name=first_name,
        last_name=last_name,
        is_verified=is_email_verified,  # Trust OAuth provider's verification
        verification_token=None  # Not needed if already verified by OAuth
    )
    
    # Save to database
    await user.save().run()
    
    return user


async def find_or_link_oauth_user(oauth_profile: dict, provider: str) -> User:
    """Find existing user by email and optionally link OAuth credentials.
    
    Args:
        oauth_profile: OAuth profile data containing user information
        provider: OAuth provider name (e.g., "google")
        
    Returns:
        Existing User instance if found, None if not found
    """
    email = oauth_profile.get("email")
    if not email:
        return None
    
    # Look for existing user with this email
    existing_user = await User.select().where(User.email == email).first()
    
    if not existing_user:
        return None
    
    # If user exists but doesn't have OAuth linked, link it
    if not existing_user.oauth_provider:
        oauth_id = oauth_profile.get("sub") or oauth_profile.get("id")
        existing_user.oauth_provider = provider
        existing_user.oauth_id = oauth_id
        await existing_user.save().run()
    
    return existing_user


async def fetch_google_user_profile(auth_code: str) -> dict:
    """Fetch user profile from Google OAuth API using authorization code.
    
    Args:
        auth_code: Google OAuth authorization code
        
    Returns:
        User profile data from Google
    """
    # Google OAuth 2.0 endpoints
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    async with httpx.AsyncClient() as client:
        # Step 1: Exchange authorization code for access token
        token_data = {
            "code": auth_code,
            "client_id": "your_google_client_id",  # TODO: Get from environment
            "client_secret": "your_google_client_secret",  # TODO: Get from environment
            "redirect_uri": "your_redirect_uri",  # TODO: Get from environment
            "grant_type": "authorization_code"
        }
        
        token_response = await client.post(token_url, data=token_data)
        token_info = token_response.json()
        access_token = token_info["access_token"]
        
        # Step 2: Fetch user profile using access token
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await client.get(userinfo_url, headers=headers)
        profile_data = profile_response.json()
        
        return profile_data


async def handle_google_oauth_callback(auth_code: str) -> dict:
    """Handle Google OAuth callback by exchanging code for user profile.
    
    Args:
        auth_code: Google OAuth authorization code from callback
        
    Returns:
        User profile data from Google
    """
    # Fetch user profile using the authorization code
    profile = await fetch_google_user_profile(auth_code)
    
    return profile
"""Authentication service for user signup and login functionality."""

import bcrypt
import re
import secrets
import uuid
from typing import Optional
from ..models.user import User

E164_PATTERN = re.compile(r"^\+[1-9]\d{6,14}$")


def validate_phone_format(phone: str) -> bool:
    """Validate phone number is in E.164 format."""
    return bool(E164_PATTERN.match(phone))


def detect_identifier_type(identifier: str) -> str:
    """Detect whether an identifier is an email or phone number.

    Returns:
        "email" or "phone"
    """
    if identifier.startswith("+") and E164_PATTERN.match(identifier):
        return "phone"
    return "email"


async def validate_phone_unique(phone: str) -> bool:
    """Check if a phone number is unique in the database."""
    exists = await User.exists().where(User.phone_number == phone).run()
    return not exists


async def find_user_by_identifier(identifier: str) -> Optional["User"]:
    """Find a user by email or phone number."""
    id_type = detect_identifier_type(identifier)
    if id_type == "phone":
        return await User.objects().where(User.phone_number == identifier).first()
    return await User.objects().where(User.email == identifier).first()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hash string
    """
    # Convert password to bytes and hash with bcrypt
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash.

    Args:
        password: Plain text password to verify
        hashed: Bcrypt hash to verify against

    Returns:
        True if password matches hash, False otherwise
    """
    # Convert inputs to bytes
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")

    # Use bcrypt to check password
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_shield_username(identifier: str, identifier_type: str = "email") -> str:
    """Generate a unique shield username from an email or phone number.

    Args:
        identifier: User's email address or phone number
        identifier_type: "email" or "phone"

    Returns:
        Shield username in format: username123
    """
    if identifier_type == "phone":
        # Use last 4 digits of phone as base
        clean_name = "user" + identifier[-4:]
    else:
        # Extract the local part of the email (before @)
        local_part = identifier.split("@")[0]
        # Remove special characters and convert to lowercase
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", local_part).lower()

    # If name is too long, truncate it
    if len(clean_name) > 10:
        clean_name = clean_name[:10]

    # Generate cryptographically secure random 3-digit number for uniqueness
    random_number = secrets.randbelow(900) + 100  # Range: 100-999

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


async def create_user(
    password: str,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    """Create a new user with hashed password and shield address.

    Args:
        password: Plain text password (will be hashed)
        email: User's email address (optional if phone provided)
        phone_number: User's phone number in E.164 format (optional if email provided)
        first_name: User's first name (optional)
        last_name: User's last name (optional)

    Returns:
        Created User instance
    """
    # Hash the password
    password_hash = hash_password(password)

    # Determine identifier type for shield username
    if email:
        identifier, identifier_type = email, "email"
    else:
        assert phone_number is not None, "Either email or phone_number must be provided"
        identifier, identifier_type = phone_number, "phone"

    # Generate shield username
    shield_username = generate_shield_username(identifier, identifier_type)

    # Generate email verification token
    verification_token = generate_verification_token()

    # Determine verification method
    verification_method = "email" if email else "phone"

    # Create user instance
    user = User(
        email=email,
        phone_number=phone_number,
        hashed_password=password_hash,
        username=shield_username,
        first_name=first_name,
        last_name=last_name,
        verification_token=verification_token,
        verification_method=verification_method,
        is_verified=False,
    )

    # Save to database
    await user.save().run()

    return user

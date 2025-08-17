"""User service for registration and shield address management."""

import uuid
import logging
from typing import Optional, Tuple
from datetime import datetime

from ..models.user import User, SubscriptionStatus
from ..models.shield_address import ShieldAddress
from ..models.organization import Organization

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and shield address operations."""
    
    @staticmethod
    async def create_user_with_shield(
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Tuple[User, ShieldAddress]:
        """Create a new user with an automatically assigned shield address.
        
        Args:
            email: User's real email address
            password_hash: Pre-hashed password
            first_name: Optional first name
            last_name: Optional last name
            organization_id: Optional organization UUID
            
        Returns:
            Tuple of (User, ShieldAddress) instances
            
        Raises:
            ValueError: If email already exists or organization not found
        """
        try:
            # Check if email already exists
            existing_user = await User.select().where(User.email == email).first()
            if existing_user:
                raise ValueError(f"User with email {email} already exists")
            
            # Validate organization if provided
            if organization_id:
                org = await Organization.select().where(
                    Organization.id == organization_id
                ).first()
                if not org:
                    raise ValueError(f"Organization {organization_id} not found")
                if not org.is_active:
                    raise ValueError(f"Organization {organization_id} is not active")
            
            # Create user with UUID
            user_uuid = uuid.uuid4()
            username = f"user_{user_uuid.hex[:8]}"  # Generate unique username
            
            user = User(
                id=user_uuid,
                email=email,
                username=username,
                hashed_password=password_hash,
                first_name=first_name,
                last_name=last_name,
                organization=organization_id,
                subscription_status=SubscriptionStatus.FREE,
                is_active=True,
                is_verified=False,
                verification_token=str(uuid.uuid4()),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            await user.save()
            logger.info(f"Created user {user.id} with email {email}")
            
            # Create shield address using user's UUID
            shield_address = await ShieldAddress.create_for_user(
                user_id=str(user.id)
            )
            
            logger.info(f"Created shield address {shield_address.shield_address} for user {user.id}")
            
            return user, shield_address
            
        except Exception as e:
            logger.error(f"Failed to create user with shield: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def get_user_by_shield_address(shield_address: str) -> Optional[User]:
        """Get user by shield address with optimized lookup.
        
        This method uses direct UUID extraction for better performance
        than database queries when possible.
        
        Args:
            shield_address: The shield email address
            
        Returns:
            User instance if found, None otherwise
        """
        try:
            # Extract username from shield address (remove @cellophanemail.com if present)
            if "@" in shield_address:
                username = shield_address.split("@")[0]
            else:
                username = shield_address
            
            # Try to find user by username field
            user = await User.select().where(
                User.username == username,
                User.is_active == True
            ).first()
            
            if user:
                return user
            
            # First try direct UUID extraction (faster)
            user_uuid = await ShieldAddress.get_user_id_from_shield(shield_address)
            if user_uuid:
                user = await User.select().where(User.id == user_uuid).first()
                if user:
                    is_active = user.get("is_active") if isinstance(user, dict) else user.is_active
                    if is_active:
                        return user
            
            # Fallback to database lookup (handles edge cases)
            shield_record = await ShieldAddress.select().where(
                ShieldAddress.shield_address == shield_address,
                ShieldAddress.is_active == True
            ).first()
            
            if shield_record:
                # shield_record is a dict, access user ID correctly
                user_id = shield_record.get("user") if isinstance(shield_record, dict) else shield_record.user
                user = await User.select().where(
                    User.id == user_id
                ).first()
                if user:
                    is_active = user.get("is_active") if isinstance(user, dict) else user.is_active
                    if is_active:
                        return user
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to lookup user by shield address {shield_address}: {e}")
            return None
    
    @staticmethod
    async def deactivate_user_shields(user_id: str) -> int:
        """Deactivate all shield addresses for a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Number of shield addresses deactivated
        """
        try:
            shields = await ShieldAddress.select().where(
                ShieldAddress.user == user_id,
                ShieldAddress.is_active == True
            )
            
            count = 0
            for shield in shields:
                await shield.deactivate()
                count += 1
            
            logger.info(f"Deactivated {count} shield addresses for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to deactivate shields for user {user_id}: {e}")
            return 0
    
    @staticmethod
    async def create_additional_shield(user_id: str, domain: str = "cellophanemail.com") -> Optional[ShieldAddress]:
        """Create an additional shield address for a user (premium feature).
        
        Args:
            user_id: User's UUID
            domain: Domain for the shield address
            
        Returns:
            New ShieldAddress instance or None if failed
        """
        try:
            # Check if user exists and is active
            user = await User.select().where(
                User.id == user_id,
                User.is_active == True
            ).first()
            
            if not user:
                logger.warning(f"Cannot create additional shield: user {user_id} not found or inactive")
                return None
            
            # For additional shields, we need a different format to avoid conflicts
            # Generate a new UUID for the shield prefix
            shield_uuid = str(uuid.uuid4()).replace('-', '')
            shield_address_str = f"{shield_uuid}@{domain}"
            
            # Ensure uniqueness
            existing = await ShieldAddress.select().where(
                ShieldAddress.shield_address == shield_address_str
            ).first()
            
            if existing:
                logger.warning(f"Shield address {shield_address_str} already exists")
                return None
            
            shield = ShieldAddress(
                shield_address=shield_address_str,
                user=user_id,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            await shield.save()
            logger.info(f"Created additional shield {shield_address_str} for user {user_id}")
            
            return shield
            
        except Exception as e:
            logger.error(f"Failed to create additional shield for user {user_id}: {e}")
            return None


class ShieldAddressService:
    """Service specifically for shield address operations."""
    
    @staticmethod
    def generate_shield_address(user_uuid: str, domain: str = "cellophanemail.com") -> str:
        """Generate a shield address from user UUID.
        
        Args:
            user_uuid: User's UUID string
            domain: Domain for shield address
            
        Returns:
            Shield email address string
        """
        clean_uuid = str(user_uuid).replace('-', '')
        return f"{clean_uuid}@{domain}"
    
    @staticmethod
    def extract_user_uuid(shield_address: str) -> Optional[str]:
        """Extract user UUID from shield address.
        
        Args:
            shield_address: Shield email address
            
        Returns:
            User UUID string or None if invalid
        """
        return ShieldAddress.get_user_id_from_shield(shield_address)
    
    @staticmethod
    def validate_shield_format(shield_address: str, domain: str = "cellophanemail.com") -> bool:
        """Validate shield address format.
        
        Args:
            shield_address: Shield email address to validate
            domain: Expected domain
            
        Returns:
            True if valid format, False otherwise
        """
        try:
            if '@' not in shield_address:
                return False
                
            local_part, domain_part = shield_address.split('@', 1)
            
            # Check domain
            if domain_part != domain:
                return False
            
            # Check local part (should be UUID without dashes)
            if len(local_part) != 32:
                return False
            
            # Try to parse as hex
            int(local_part, 16)
            return True
            
        except (ValueError, IndexError):
            return False
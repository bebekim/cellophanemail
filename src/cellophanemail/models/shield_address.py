"""ShieldAddress model for CellophoneMail."""

from typing import Optional
from piccolo.table import Table
from piccolo.columns import Varchar, Boolean, Timestamp, ForeignKey, UUID
from datetime import datetime
import uuid
from .user import User


class ShieldAddress(Table, tablename="shield_addresses"):
    """Model for managing shield email addresses that forward to real user emails."""
    
    # Primary identification
    id = UUID(primary_key=True, default=uuid.uuid4)
    shield_address = Varchar(length=255, unique=True, index=True, null=False)
    
    # Relationships
    user = ForeignKey(User, null=False)
    
    # Status
    is_active = Boolean(default=True)
    
    # Timestamps
    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(default=datetime.now)
    
    @classmethod
    async def get_by_shield_address(cls, shield_address: str) -> Optional['ShieldAddress']:
        """Get a ShieldAddress record by shield email address."""
        return await cls.select().where(
            cls.shield_address == shield_address
        ).first()
    
    @classmethod
    async def get_user_by_shield(cls, shield_address: str) -> Optional[User]:
        """Get the User associated with a shield email address."""
        shield_record = await cls.select(cls.user).where(
            cls.shield_address == shield_address
        ).first()
        
        if shield_record:
            return await User.select().where(
                User.id == shield_record.user
            ).first()
        return None
    
    @classmethod
    def generate_uuid_shield(cls, user_id: str, domain: str) -> str:
        """Generate a UUID-based shield address for a user."""
        # Generate a new UUID for the shield address without hyphens
        shield_uuid = uuid.uuid4().hex  # .hex gives UUID without hyphens (32 chars)
        return f"{shield_uuid}@{domain}"
    
    @classmethod
    def create_shield_for_new_user(cls, user_id: str, user_email: str, shield_domain: str) -> str:
        """Create a shield address for a new user during signup."""
        # For now, just generate and return the shield address string
        # Later we can extend this to actually create the database record
        return cls.generate_uuid_shield(user_id, shield_domain)
    
    @classmethod
    async def create_for_user(cls, user_id: str, domain: str = "cellophanemail.com") -> 'ShieldAddress':
        """Create a new shield address for a user with a unique UUID.
        
        Note: We generate a NEW UUID for the shield address rather than using
        the user's UUID directly. This provides better security as the shield
        UUID cannot be used to deduce the user's internal ID.
        """
        max_attempts = 5
        for _ in range(max_attempts):
            # Generate new UUID without hyphens (32 chars)
            shield_uuid = uuid.uuid4().hex
            shield_address = f"{shield_uuid}@{domain}"
            
            # Check if this shield address already exists
            existing = await cls.select().where(
                cls.shield_address == shield_address
            ).first()
            
            if not existing:
                # Create and return the new shield address
                new_shield = cls(
                    shield_address=shield_address,
                    user=user_id
                )
                await new_shield.save()
                return new_shield
        
        raise ValueError(f"Failed to generate unique shield address after {max_attempts} attempts")
    
    @classmethod
    async def get_user_id_from_shield(cls, shield_address: str) -> Optional[str]:
        """Get the user ID associated with a shield address.
        
        Since shield addresses use their own UUIDs (not user UUIDs),
        we need to look up the relationship in the database.
        """
        shield_record = await cls.select(cls.user).where(
            cls.shield_address == shield_address,
            cls.is_active == True
        ).first()
        
        if shield_record:
            # Handle both dict and object formats
            user_id = shield_record.get("user") if isinstance(shield_record, dict) else shield_record.user
            return str(user_id)
        return None
    
    async def deactivate(self) -> 'ShieldAddress':
        """Soft delete this shield address by setting is_active to False."""
        self.is_active = False
        self.updated_at = datetime.now()
        await self.save()
        return self
    
    def __str__(self):
        return f"ShieldAddress(shield_address={self.shield_address}, active={self.is_active})"
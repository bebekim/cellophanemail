"""User accounts manager - facade for easy integration with other components."""

import logging
from typing import Optional, List

from .service import UserAccountService
from .models import (
    UserAccountInfo, UserRegistrationRequest, UserAuthRequest, UserAuthResult,
    ShieldAddressCreationResult, UserUsageStats
)

logger = logging.getLogger(__name__)


class UserAccountManager:
    """
    Manager class that provides a simplified interface to user account operations.
    This serves as the main entry point for other components to interact with
    user accounts functionality.
    """
    
    def __init__(self):
        self.service = UserAccountService()
        self.logger = logging.getLogger(__name__)
        self.logger.info("UserAccountManager initialized")
    
    # Authentication and Registration
    
    async def register_user(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> UserAuthResult:
        """
        Register a new user account.
        
        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            first_name: Optional first name
            last_name: Optional last name
            organization_id: Optional organization UUID
            
        Returns:
            UserAuthResult with registration outcome
        """
        request = UserRegistrationRequest(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            organization_id=organization_id
        )
        
        result = await self.service.register_user(request)
        
        if result.success:
            self.logger.info(f"User registration successful: {email}")
        else:
            self.logger.warning(f"User registration failed: {email} - {result.error_message}")
        
        return result
    
    async def authenticate_user(self, email: str, password: str) -> UserAuthResult:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            UserAuthResult with authentication outcome and tokens
        """
        request = UserAuthRequest(email=email, password=password)
        result = await self.service.authenticate_user(request)
        
        if result.success:
            self.logger.info(f"User authentication successful: {email}")
        else:
            self.logger.warning(f"User authentication failed: {email}")
        
        return result
    
    # User Information
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserAccountInfo]:
        """
        Get user account information by ID.
        
        Args:
            user_id: User's UUID string
            
        Returns:
            UserAccountInfo if found, None otherwise
        """
        return await self.service.get_user_by_id(user_id)
    
    async def get_user_by_shield_address(self, shield_address: str) -> Optional[UserAccountInfo]:
        """
        Get user account information by shield address.
        This is commonly used in email processing to find the target user.
        
        Args:
            shield_address: Shield email address (e.g., "abc123@cellophanemail.com")
            
        Returns:
            UserAccountInfo if found, None otherwise
        """
        # Use the existing service logic for shield address lookup
        from ...services.user_service import UserService
        
        try:
            user = await UserService.get_user_by_shield_address(shield_address)
            if not user:
                return None
            
            # Convert to our feature model
            return await self.service.get_user_by_id(str(user.id))
            
        except Exception as e:
            self.logger.error(f"Failed to get user by shield address {shield_address}: {e}")
            return None
    
    # Shield Address Management
    
    async def create_shield_address(self, user_id: str, domain: str = "cellophanemail.com") -> ShieldAddressCreationResult:
        """
        Create an additional shield address for a user.
        
        Args:
            user_id: User's UUID string
            domain: Domain for the shield address
            
        Returns:
            ShieldAddressCreationResult with outcome
        """
        result = await self.service.create_shield_address(user_id, domain)
        
        if result.success:
            self.logger.info(f"Created shield address for user {user_id}: {result.shield_address}")
        else:
            self.logger.warning(f"Failed to create shield address for user {user_id}: {result.error_message}")
        
        return result
    
    async def get_user_shield_addresses(self, user_id: str) -> List[str]:
        """
        Get all active shield addresses for a user.
        
        Args:
            user_id: User's UUID string
            
        Returns:
            List of shield email addresses
        """
        try:
            user_info = await self.service.get_user_by_id(user_id)
            return user_info.shield_addresses if user_info else []
        except Exception as e:
            self.logger.error(f"Failed to get shield addresses for user {user_id}: {e}")
            return []
    
    # Usage and Statistics
    
    async def get_usage_stats(self, user_id: str) -> Optional[UserUsageStats]:
        """
        Get user usage statistics.
        
        Args:
            user_id: User's UUID string
            
        Returns:
            UserUsageStats if user found, None otherwise
        """
        return await self.service.get_usage_stats(user_id)
    
    # Utility Methods for Integration
    
    async def is_user_active(self, user_id: str) -> bool:
        """
        Check if a user account is active.
        
        Args:
            user_id: User's UUID string
            
        Returns:
            True if user is active, False otherwise
        """
        try:
            user_info = await self.service.get_user_by_id(user_id)
            return user_info.status.value == "active" if user_info else False
        except Exception:
            return False
    
    async def can_user_create_shield_address(self, user_id: str) -> bool:
        """
        Check if user can create additional shield addresses based on their subscription.
        
        Args:
            user_id: User's UUID string
            
        Returns:
            True if user can create more shields, False otherwise
        """
        try:
            user_info = await self.service.get_user_by_id(user_id)
            if not user_info:
                return False
            
            current_count = len(user_info.shield_addresses)
            
            # Define limits based on subscription tier
            limits = {
                "free": 1,
                "starter": 1,
                "professional": 3,
                "unlimited": float('inf')
            }
            
            limit = limits.get(user_info.subscription_tier.value, 1)
            return current_count < limit
            
        except Exception as e:
            self.logger.error(f"Failed to check shield creation limit for user {user_id}: {e}")
            return False
    
    # Health and Monitoring
    
    def get_feature_status(self) -> dict:
        """
        Get the current status of the user accounts feature.
        
        Returns:
            Dictionary with feature status information
        """
        return {
            "feature": "user_accounts",
            "status": "active",
            "version": "1.0.0",
            "capabilities": [
                "user_registration",
                "user_authentication", 
                "shield_address_management",
                "usage_tracking",
                "subscription_management"
            ]
        }
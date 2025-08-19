"""User accounts service - core business logic for user management."""

import logging
import uuid
from typing import Optional, List
from datetime import datetime

from .models import (
    UserAccountInfo, UserRegistrationRequest, UserAuthRequest, UserAuthResult,
    ShieldAddressCreationResult, UserStatus, SubscriptionTier, UserUsageStats
)
from ...services.auth_service import hash_password, verify_password, generate_verification_token
from ...services.jwt_service import create_access_token, create_refresh_token
from ...models.user import User, SubscriptionStatus
from ...models.shield_address import ShieldAddress

logger = logging.getLogger(__name__)


class UserAccountService:
    """
    Self-contained user account service following VSA principles.
    Handles all user-related business logic including registration, authentication,
    shield address management, and user preferences.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def register_user(self, request: UserRegistrationRequest) -> UserAuthResult:
        """
        Register a new user with automatic shield address creation.
        
        Args:
            request: User registration details
            
        Returns:
            UserAuthResult with user info and tokens if successful
        """
        try:
            # Check if user already exists
            existing = await User.exists().where(User.email == request.email).run()
            if existing:
                return UserAuthResult(
                    success=False,
                    error_message="User with this email already exists"
                )
            
            # Hash password
            password_hash = hash_password(request.password)
            
            # Generate verification token
            verification_token = generate_verification_token()
            
            # Create user
            user_id = uuid.uuid4()
            username = f"user_{user_id.hex[:8]}"
            
            user = User(
                id=user_id,
                email=request.email,
                username=username,
                hashed_password=password_hash,
                first_name=request.first_name,
                last_name=request.last_name,
                organization=request.organization_id,
                verification_token=verification_token,
                is_verified=False,
                is_active=True,
                subscription_status=SubscriptionStatus.FREE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            await user.save().run()
            self.logger.info(f"Created user {user_id} with email {request.email}")
            
            # Create primary shield address
            shield_result = await self.create_shield_address(str(user_id))
            if not shield_result.success:
                # Rollback user creation would happen here in production
                self.logger.error(f"Failed to create shield address for user {user_id}")
                return UserAuthResult(
                    success=False,
                    error_message="Failed to create shield address"
                )
            
            # Create user account info
            user_info = UserAccountInfo(
                user_id=str(user_id),
                email=request.email,
                username=username,
                first_name=request.first_name,
                last_name=request.last_name,
                status=UserStatus.PENDING_VERIFICATION,
                subscription_tier=SubscriptionTier.FREE,
                shield_addresses=[shield_result.shield_address],
                organization_id=request.organization_id,
                created_at=user.created_at,
                is_verified=False
            )
            
            # Generate tokens
            access_token = create_access_token(
                user_id=str(user_id),
                email=request.email,
                role="user"
            )
            refresh_token = create_refresh_token(user_id=str(user_id))
            
            return UserAuthResult(
                success=True,
                user_info=user_info,
                access_token=access_token,
                refresh_token=refresh_token
            )
            
        except Exception as e:
            self.logger.error(f"User registration failed: {e}", exc_info=True)
            return UserAuthResult(
                success=False,
                error_message="Registration failed due to system error"
            )
    
    async def authenticate_user(self, request: UserAuthRequest) -> UserAuthResult:
        """
        Authenticate user credentials and return tokens.
        
        Args:
            request: Authentication request with email/password
            
        Returns:
            UserAuthResult with user info and tokens if successful
        """
        try:
            # Find user by email
            user = await User.objects().where(User.email == request.email).first()
            if not user:
                return UserAuthResult(
                    success=False,
                    error_message="Invalid email or password"
                )
            
            # Verify password
            if not verify_password(request.password, user.hashed_password):
                return UserAuthResult(
                    success=False,
                    error_message="Invalid email or password"
                )
            
            # Check if account is active
            if not user.is_active:
                return UserAuthResult(
                    success=False,
                    error_message="Account is deactivated"
                )
            
            # Update last login
            user.last_login = datetime.now()
            user.updated_at = datetime.now()
            await user.save().run()
            
            # Get user's shield addresses
            shield_addresses = await self._get_user_shield_addresses(str(user.id))
            
            # Create user info
            user_info = UserAccountInfo(
                user_id=str(user.id),
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                status=UserStatus.ACTIVE if user.is_active else UserStatus.INACTIVE,
                subscription_tier=self._map_subscription_tier(user.subscription_status),
                shield_addresses=shield_addresses,
                organization_id=str(user.organization) if user.organization else None,
                created_at=user.created_at,
                last_login=user.last_login,
                is_verified=user.is_verified
            )
            
            # Generate tokens
            access_token = create_access_token(
                user_id=str(user.id),
                email=user.email,
                role="user"
            )
            refresh_token = create_refresh_token(user_id=str(user.id))
            
            return UserAuthResult(
                success=True,
                user_info=user_info,
                access_token=access_token,
                refresh_token=refresh_token
            )
            
        except Exception as e:
            self.logger.error(f"User authentication failed: {e}", exc_info=True)
            return UserAuthResult(
                success=False,
                error_message="Authentication failed due to system error"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserAccountInfo]:
        """
        Get user account information by user ID.
        
        Args:
            user_id: User's UUID string
            
        Returns:
            UserAccountInfo if found, None otherwise
        """
        try:
            user = await User.objects().where(User.id == user_id).first()
            if not user:
                return None
            
            shield_addresses = await self._get_user_shield_addresses(user_id)
            
            return UserAccountInfo(
                user_id=str(user.id),
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                status=UserStatus.ACTIVE if user.is_active else UserStatus.INACTIVE,
                subscription_tier=self._map_subscription_tier(user.subscription_status),
                shield_addresses=shield_addresses,
                organization_id=str(user.organization) if user.organization else None,
                created_at=user.created_at,
                last_login=user.last_login,
                is_verified=user.is_verified
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def create_shield_address(self, user_id: str, domain: str = "cellophanemail.com") -> ShieldAddressCreationResult:
        """
        Create a new shield address for a user.
        
        Args:
            user_id: User's UUID string
            domain: Domain for the shield address
            
        Returns:
            ShieldAddressCreationResult with the new address or error
        """
        try:
            # Verify user exists
            user = await User.objects().where(User.id == user_id).first()
            if not user:
                return ShieldAddressCreationResult(
                    success=False,
                    error_message="User not found"
                )
            
            # Create shield address
            shield_address = await ShieldAddress.create_for_user(user_id)
            
            return ShieldAddressCreationResult(
                success=True,
                shield_address=shield_address.shield_address
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create shield address for user {user_id}: {e}")
            return ShieldAddressCreationResult(
                success=False,
                error_message="Failed to create shield address"
            )
    
    async def get_usage_stats(self, user_id: str) -> Optional[UserUsageStats]:
        """
        Get user usage statistics.
        
        Args:
            user_id: User's UUID string
            
        Returns:
            UserUsageStats if user found, None otherwise
        """
        try:
            user = await User.objects().where(User.id == user_id).first()
            if not user:
                return None
            
            # Get shield addresses count
            shield_count = await ShieldAddress.count().where(
                ShieldAddress.user == user_id,
                ShieldAddress.is_active == True
            ).run()
            
            # Get email processing stats (simplified for demo)
            emails_processed = user.emails_processed_month.get("count", 0) if user.emails_processed_month else 0
            
            return UserUsageStats(
                emails_processed_this_month=emails_processed,
                emails_blocked_this_month=0,  # Would be calculated from email_logs
                shield_addresses_active=shield_count,
                api_requests_remaining=user.api_quota_remaining.get("requests", 1000) if user.api_quota_remaining else 1000,
                storage_used_mb=0.0,  # Would be calculated from stored data
                last_activity=user.last_login
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get usage stats for user {user_id}: {e}")
            return None
    
    async def _get_user_shield_addresses(self, user_id: str) -> List[str]:
        """Get all active shield addresses for a user."""
        try:
            shields = await ShieldAddress.select().where(
                ShieldAddress.user == user_id,
                ShieldAddress.is_active == True
            ).run()
            
            return [shield["shield_address"] for shield in shields]
            
        except Exception as e:
            self.logger.error(f"Failed to get shield addresses for user {user_id}: {e}")
            return []
    
    def _map_subscription_tier(self, subscription_status: str) -> SubscriptionTier:
        """Map database subscription status to feature model."""
        mapping = {
            "free": SubscriptionTier.FREE,
            "trial": SubscriptionTier.STARTER,  # Trial users get starter features
            "active": SubscriptionTier.PROFESSIONAL,  # Default active to professional
            "past_due": SubscriptionTier.PROFESSIONAL,
            "canceled": SubscriptionTier.FREE
        }
        return mapping.get(subscription_status, SubscriptionTier.FREE)
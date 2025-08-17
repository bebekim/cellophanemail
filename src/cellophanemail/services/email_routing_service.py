"""Email routing service for shield address validation and user lookup."""

import logging
from dataclasses import dataclass
from typing import Optional

from ..services.user_service import UserService

logger = logging.getLogger(__name__)


@dataclass
class EmailRoutingContext:
    """Context for email routing decisions."""
    shield_address: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    organization_id: Optional[str] = None
    is_valid_domain: bool = False
    is_active_user: bool = False
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class EmailRoutingService:
    """Service for email routing logic and shield address validation."""
    
    def __init__(self, valid_domain: str = "cellophanemail.com"):
        """Initialize routing service with configuration.
        
        Args:
            valid_domain: Domain that shield addresses must belong to
        """
        self.valid_domain = valid_domain
    
    async def validate_and_route_email(self, shield_address: str) -> EmailRoutingContext:
        """Validate shield address and determine routing context.
        
        This method orchestrates the complete routing validation pipeline:
        1. Domain validation
        2. User lookup by shield address
        3. User status verification
        
        Args:
            shield_address: The shield email address to validate
            
        Returns:
            EmailRoutingContext with validation results and routing information
        """
        # Create initial context
        context = EmailRoutingContext(shield_address=shield_address.lower().strip())
        
        try:
            # Step 1: Validate domain
            if not self._validate_domain(context):
                return context
            
            # Step 2: Lookup user by shield address
            if not await self._lookup_user(context):
                return context
            
            # Step 3: Verify user is active
            if not self._verify_user_active(context):
                return context
            
            # If we reach here, routing is successful
            context.is_active_user = True
            logger.info(f"Successfully routed email to user {context.user_id} ({context.user_email})")
            
            return context
            
        except Exception as e:
            logger.error(f"Error in email routing for {shield_address}: {e}", exc_info=True)
            context.error_message = "Internal routing error"
            context.error_code = "ROUTING_ERROR"
            return context
    
    def _validate_domain(self, context: EmailRoutingContext) -> bool:
        """Validate that shield address belongs to correct domain.
        
        # TDD_IMPLEMENT: Domain validation logic
        # TDD_IMPLEMENT: Support for multiple valid domains
        # TDD_IMPLEMENT: Case-insensitive domain matching
        """
        try:
            if not context.shield_address.endswith(f"@{self.valid_domain}"):
                logger.warning(f"Invalid domain in shield address: {context.shield_address}")
                context.error_message = f"Invalid domain. Expected @{self.valid_domain}"
                context.error_code = "INVALID_DOMAIN"
                return False
            
            context.is_valid_domain = True
            return True
            
        except Exception as e:
            logger.error(f"Error validating domain for {context.shield_address}: {e}")
            context.error_message = "Domain validation error"
            context.error_code = "DOMAIN_ERROR"
            return False
    
    async def _lookup_user(self, context: EmailRoutingContext) -> bool:
        """Lookup user by shield address.
        
        # TDD_IMPLEMENT: User lookup with error handling
        # TDD_IMPLEMENT: Handle both dict and object user responses
        # TDD_IMPLEMENT: Graceful handling of missing users
        """
        try:
            user = await UserService.get_user_by_shield_address(context.shield_address)
            
            if not user:
                logger.warning(f"No user found for shield address: {context.shield_address}")
                context.error_message = "Shield address not found"
                context.error_code = "USER_NOT_FOUND"
                return False
            
            # Handle both dict and object responses from UserService
            if isinstance(user, dict):
                context.user_id = str(user.get("id"))
                context.user_email = user.get("email")
                context.organization_id = str(user.get("organization")) if user.get("organization") else None
            else:
                # Assume it's a User model object
                context.user_id = str(user.id)
                context.user_email = user.email
                context.organization_id = str(user.organization) if user.organization else None
            
            return True
            
        except Exception as e:
            logger.error(f"Error looking up user for {context.shield_address}: {e}")
            context.error_message = "User lookup error"
            context.error_code = "LOOKUP_ERROR"
            return False
    
    def _verify_user_active(self, context: EmailRoutingContext) -> bool:
        """Verify that the user account is active.
        
        # TDD_IMPLEMENT: User status verification
        # TDD_IMPLEMENT: Organization status checking
        # TDD_IMPLEMENT: Subscription status validation
        """
        try:
            # Basic validation - ensure we have required user information
            if not context.user_id or not context.user_email:
                logger.warning(f"Incomplete user information for shield {context.shield_address}")
                context.error_message = "User account incomplete"
                context.error_code = "USER_INCOMPLETE"
                return False
            
            # Note: Additional user status validation could be added here
            # For example, checking subscription status, organization limits, etc.
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying user status for {context.shield_address}: {e}")
            context.error_message = "User verification error"
            context.error_code = "VERIFICATION_ERROR"
            return False
    
    def get_http_status_code(self, context: EmailRoutingContext) -> int:
        """Get appropriate HTTP status code based on routing context.
        
        # TDD_IMPLEMENT: Status code mapping for different error types
        # TDD_IMPLEMENT: Consistent error code handling
        """
        if context.is_active_user:
            return 200
        
        error_code_map = {
            "INVALID_DOMAIN": 400,
            "USER_NOT_FOUND": 404,
            "USER_INCOMPLETE": 404,
            "DOMAIN_ERROR": 400,
            "LOOKUP_ERROR": 500,
            "VERIFICATION_ERROR": 500,
            "ROUTING_ERROR": 500,
        }
        
        return error_code_map.get(context.error_code, 500)
    
    def format_error_response(self, context: EmailRoutingContext, message_id: str) -> dict:
        """Format error response for webhook.
        
        # TDD_IMPLEMENT: Consistent error response formatting
        # TDD_IMPLEMENT: Include helpful error details for debugging
        """
        return {
            "error": context.error_message or "Unknown routing error",
            "error_code": context.error_code,
            "message_id": message_id,
            "shield_address": context.shield_address
        }
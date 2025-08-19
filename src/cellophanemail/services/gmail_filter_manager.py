"""Gmail filter and forwarding management service."""

import logging
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailFilterManager:
    """Manage Gmail filters and forwarding rules programmatically."""
    
    def __init__(self, credentials: Credentials):
        """
        Initialize Gmail filter manager.
        
        Args:
            credentials: OAuth2 credentials with Gmail settings scope
        """
        self.service = build('gmail', 'v1', credentials=credentials)
        self.user_id = 'me'  # Special value for authenticated user
    
    def create_abuser_filter(self, abuser_email: str, forward_to: str = None,
                            add_label: str = "Toxic/Blocked",
                            mark_as_read: bool = True,
                            skip_inbox: bool = True) -> Dict:
        """
        Create a Gmail filter to handle emails from an abusive sender.
        
        Args:
            abuser_email: Email address to filter
            forward_to: Email address to forward to (optional)
            add_label: Label to apply to filtered emails
            mark_as_read: Whether to mark emails as read
            skip_inbox: Whether to skip the inbox (archive)
            
        Returns:
            Created filter object
        """
        # Build the filter criteria
        criteria = {
            'from': abuser_email
        }
        
        # Build the filter action
        action = {}
        
        if forward_to:
            action['forward'] = forward_to
        
        if add_label:
            # First ensure the label exists
            label_id = self._ensure_label_exists(add_label)
            action['addLabelIds'] = [label_id]
        
        if skip_inbox:
            action['removeLabelIds'] = ['INBOX']
        
        if mark_as_read:
            action['removeLabelIds'] = action.get('removeLabelIds', []) + ['UNREAD']
        
        # Create the filter
        filter_body = {
            'criteria': criteria,
            'action': action
        }
        
        try:
            result = self.service.users().settings().filters().create(
                userId=self.user_id,
                body=filter_body
            ).execute()
            
            logger.info(f"Created filter for abuser {abuser_email}: {result['id']}")
            return result
            
        except HttpError as error:
            logger.error(f"Failed to create filter: {error}")
            raise
    
    def create_safe_sender_filter(self, safe_email: str, 
                                 star: bool = True,
                                 important: bool = True,
                                 never_spam: bool = True) -> Dict:
        """
        Create a filter for known safe senders.
        
        Args:
            safe_email: Email address of safe sender
            star: Whether to star emails
            important: Whether to mark as important
            never_spam: Whether to never send to spam
            
        Returns:
            Created filter object
        """
        criteria = {
            'from': safe_email,
            'excludeChats': True
        }
        
        action = {}
        
        if star:
            action['addLabelIds'] = ['STARRED']
        
        if important:
            action['addLabelIds'] = action.get('addLabelIds', []) + ['IMPORTANT']
        
        if never_spam:
            action['neverSpam'] = True
        
        filter_body = {
            'criteria': criteria,
            'action': action
        }
        
        try:
            result = self.service.users().settings().filters().create(
                userId=self.user_id,
                body=filter_body
            ).execute()
            
            logger.info(f"Created safe sender filter for {safe_email}: {result['id']}")
            return result
            
        except HttpError as error:
            logger.error(f"Failed to create safe sender filter: {error}")
            raise
    
    def list_filters(self) -> List[Dict]:
        """
        List all existing filters.
        
        Returns:
            List of filter objects
        """
        try:
            results = self.service.users().settings().filters().list(
                userId=self.user_id
            ).execute()
            
            filters = results.get('filter', [])
            logger.info(f"Found {len(filters)} existing filters")
            return filters
            
        except HttpError as error:
            logger.error(f"Failed to list filters: {error}")
            raise
    
    def delete_filter(self, filter_id: str) -> bool:
        """
        Delete a specific filter.
        
        Args:
            filter_id: ID of the filter to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self.service.users().settings().filters().delete(
                userId=self.user_id,
                id=filter_id
            ).execute()
            
            logger.info(f"Deleted filter {filter_id}")
            return True
            
        except HttpError as error:
            logger.error(f"Failed to delete filter {filter_id}: {error}")
            return False
    
    def setup_forwarding_address(self, forward_email: str) -> Dict:
        """
        Add a forwarding address (requires user verification).
        
        Args:
            forward_email: Email address to forward to
            
        Returns:
            Forwarding address object
        """
        try:
            result = self.service.users().settings().forwardingAddresses().create(
                userId=self.user_id,
                body={'forwardingEmail': forward_email}
            ).execute()
            
            logger.info(f"Forwarding address {forward_email} added (pending verification)")
            return result
            
        except HttpError as error:
            logger.error(f"Failed to add forwarding address: {error}")
            raise
    
    def list_forwarding_addresses(self) -> List[Dict]:
        """
        List all configured forwarding addresses.
        
        Returns:
            List of forwarding address objects
        """
        try:
            results = self.service.users().settings().forwardingAddresses().list(
                userId=self.user_id
            ).execute()
            
            addresses = results.get('forwardingAddresses', [])
            logger.info(f"Found {len(addresses)} forwarding addresses")
            return addresses
            
        except HttpError as error:
            logger.error(f"Failed to list forwarding addresses: {error}")
            raise
    
    def _ensure_label_exists(self, label_name: str) -> str:
        """
        Ensure a label exists, creating it if necessary.
        
        Args:
            label_name: Name of the label (can include hierarchy with /)
            
        Returns:
            Label ID
        """
        try:
            # List existing labels
            results = self.service.users().labels().list(userId=self.user_id).execute()
            labels = results.get('labels', [])
            
            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
            
            # Create new label
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            # Handle nested labels (e.g., "Toxic/Blocked")
            if '/' in label_name:
                parts = label_name.split('/')
                parent_name = parts[0]
                
                # Find or create parent label first
                parent_id = None
                for label in labels:
                    if label['name'] == parent_name:
                        parent_id = label['id']
                        break
                
                if not parent_id:
                    parent_label = self.service.users().labels().create(
                        userId=self.user_id,
                        body={'name': parent_name}
                    ).execute()
                    parent_id = parent_label['id']
            
            created_label = self.service.users().labels().create(
                userId=self.user_id,
                body=label_object
            ).execute()
            
            logger.info(f"Created label {label_name}: {created_label['id']}")
            return created_label['id']
            
        except HttpError as error:
            logger.error(f"Failed to ensure label exists: {error}")
            raise
    
    def create_four_horsemen_filters(self, 
                                    toxic_forward_address: str = None,
                                    safe_haven_address: str = None) -> Dict:
        """
        Create a comprehensive set of filters based on Four Horsemen analysis.
        
        Args:
            toxic_forward_address: Where to forward toxic emails (optional)
            safe_haven_address: Safe address for user's real emails
            
        Returns:
            Dictionary of created filters
        """
        created_filters = {
            'toxic': [],
            'safe': [],
            'warning': []
        }
        
        # Create labels for organization
        self._ensure_label_exists("CellophoneMail")
        self._ensure_label_exists("CellophoneMail/Toxic")
        self._ensure_label_exists("CellophoneMail/Warning")
        self._ensure_label_exists("CellophoneMail/Safe")
        
        # Note: In production, these would be populated from your database
        # based on actual Four Horsemen analysis results
        
        logger.info("Four Horsemen filter structure created")
        return created_filters


def setup_gmail_integration(user_email: str, oauth_credentials: Credentials) -> GmailFilterManager:
    """
    Set up Gmail integration for a user.
    
    Args:
        user_email: User's Gmail address
        oauth_credentials: OAuth2 credentials with appropriate scopes
        
    Returns:
        Configured GmailFilterManager instance
    """
    # Required OAuth2 scopes for filter management:
    # - https://www.googleapis.com/auth/gmail.settings.basic
    # - https://www.googleapis.com/auth/gmail.settings.sharing (for forwarding)
    
    manager = GmailFilterManager(oauth_credentials)
    
    # Verify access by listing current filters
    try:
        current_filters = manager.list_filters()
        logger.info(f"Gmail integration successful for {user_email}, found {len(current_filters)} filters")
        return manager
    except Exception as e:
        logger.error(f"Gmail integration failed for {user_email}: {e}")
        raise


# Example usage for adding abuser to filter
async def add_abuser_to_gmail_filter(user_email: str, 
                                    abuser_email: str,
                                    oauth_creds: Credentials,
                                    forward_to_safe: bool = False) -> Dict:
    """
    Add an abusive sender to Gmail filters programmatically.
    
    Args:
        user_email: User's Gmail address
        abuser_email: Email address of the abuser
        oauth_creds: OAuth2 credentials
        forward_to_safe: Whether to forward to a safe address
        
    Returns:
        Created filter details
    """
    manager = GmailFilterManager(oauth_creds)
    
    # Create filter to handle abuser's emails
    filter_result = manager.create_abuser_filter(
        abuser_email=abuser_email,
        forward_to=f"{user_email}.safe@cellophanemail.com" if forward_to_safe else None,
        add_label="CellophoneMail/Toxic",
        mark_as_read=True,
        skip_inbox=True
    )
    
    logger.info(f"Added {abuser_email} to Gmail filters for {user_email}")
    return filter_result
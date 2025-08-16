#!/usr/bin/env python3
"""
Configure Postmark webhook URL programmatically for dev/prod environments.
Manages webhook URLs via Postmark API instead of manual console configuration.
"""

import os
import sys
import requests
import argparse
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on system environment


@dataclass
class PostmarkConfig:
    """Postmark configuration for different environments."""
    
    # Environment webhooks
    WEBHOOKS = {
        "dev": "https://especially-loved-goshawk.ngrok-free.app/webhooks/postmark",
        "prod": "https://cellophanemail.com/webhooks/postmark",
        "local": "http://localhost:8000/webhooks/postmark",
        "test": "https://webhook.site/your-unique-id"  # For testing
    }
    
    # Get from environment or use placeholders
    ACCOUNT_TOKEN = os.getenv("POSTMARK_ACCOUNT_API_TOKEN", "your-account-token")
    SERVER_TOKEN = os.getenv("POSTMARK_SERVER_API_TOKEN", "your-server-token")
    
    # Server ID from your Postmark console
    SERVER_ID = os.getenv("POSTMARK_SERVER_ID", "16684363")  # Your server ID
    
    # Inbound configuration
    INBOUND_DOMAIN = "cellophanemail.com"
    INBOUND_STREAM_ID = "inbound"  # Default inbound stream


class PostmarkAPIClient:
    """Client for Postmark Server API."""
    
    BASE_URL = "https://api.postmarkapp.com"
    
    def __init__(self, account_token: str, server_token: str):
        self.account_token = account_token
        self.server_token = server_token
        self.session = requests.Session()
        
    def _account_headers(self) -> Dict[str, str]:
        """Headers for account-level API calls."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Account-Token": self.account_token
        }
    
    def _server_headers(self) -> Dict[str, str]:
        """Headers for server-level API calls."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.server_token
        }
    
    def get_server_info(self, server_id: str) -> Dict[str, Any]:
        """Get server configuration."""
        url = f"{self.BASE_URL}/servers/{server_id}"
        response = self.session.get(url, headers=self._account_headers())
        response.raise_for_status()
        return response.json()
    
    def update_server(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update server configuration including webhook URLs."""
        url = f"{self.BASE_URL}/servers/{server_id}"
        response = self.session.put(url, json=config, headers=self._account_headers())
        response.raise_for_status()
        return response.json()
    
    def get_message_streams(self, server_id: str) -> Dict[str, Any]:
        """Get all message streams for a server."""
        url = f"{self.BASE_URL}/servers/{server_id}/message-streams"
        response = self.session.get(url, headers=self._server_headers())
        response.raise_for_status()
        return response.json()
    
    def update_message_stream(self, stream_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update a specific message stream configuration."""
        url = f"{self.BASE_URL}/message-streams/{stream_id}"
        response = self.session.patch(url, json=config, headers=self._server_headers())
        response.raise_for_status()
        return response.json()
    
    def test_webhook(self, webhook_url: str) -> bool:
        """Test if webhook URL is reachable."""
        try:
            # Send a test request to the webhook
            test_payload = {
                "From": "test@example.com",
                "To": "test@cellophanemail.com",
                "Subject": "Webhook Test",
                "MessageID": "test-message-id",
                "Date": "2025-01-01T00:00:00Z"
            }
            response = requests.post(webhook_url, json=test_payload, timeout=5)
            return response.status_code in [200, 201, 202, 204, 400, 404]  # Accept various responses
        except Exception as e:
            print(f"⚠️  Webhook test failed: {e}")
            return False


def configure_webhook(env: str, test_only: bool = False) -> None:
    """Configure Postmark webhook for specified environment."""
    
    config = PostmarkConfig()
    
    if env not in config.WEBHOOKS:
        print(f"❌ Unknown environment: {env}")
        print(f"   Available: {', '.join(config.WEBHOOKS.keys())}")
        sys.exit(1)
    
    webhook_url = config.WEBHOOKS[env]
    print(f"🔧 Configuring Postmark for {env} environment")
    print(f"   Webhook URL: {webhook_url}")
    
    # Initialize API client
    client = PostmarkAPIClient(config.ACCOUNT_TOKEN, config.SERVER_TOKEN)
    
    # Test webhook if not in test_only mode
    if not test_only and env in ["dev", "local"]:
        print(f"🧪 Testing webhook connectivity...")
        if not client.test_webhook(webhook_url):
            print(f"⚠️  Warning: Webhook may not be reachable")
            response = input("   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("❌ Configuration cancelled")
                sys.exit(1)
    
    try:
        # Get current server configuration
        print(f"📥 Fetching server configuration...")
        server_info = client.get_server_info(config.SERVER_ID)
        print(f"   Server: {server_info.get('Name', 'Unknown')}")
        
        # Update server with new webhook URL and domain
        print(f"📤 Updating webhook configuration...")
        update_config = {
            "InboundHookUrl": webhook_url,
            "InboundDomain": config.INBOUND_DOMAIN,
            "InboundSpamThreshold": 5  # Optional: configure spam threshold
        }
        
        updated = client.update_server(config.SERVER_ID, update_config)
        
        print(f"✅ Server configuration updated!")
        print(f"   Inbound Domain: {updated.get('InboundDomain', 'Not set')}")
        print(f"   Inbound Webhook: {updated.get('InboundHookUrl', 'Not set')}")
        
        # Also check message streams
        print(f"\n📊 Checking message streams...")
        streams = client.get_message_streams(config.SERVER_ID)
        
        for stream in streams.get("MessageStreams", []):
            if stream.get("MessageStreamType") == "Inbound":
                print(f"   Found inbound stream: {stream.get('ID')}")
                print(f"   Name: {stream.get('Name')}")
                
    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error: {e}")
        print(f"   Response: {e.response.text if e.response else 'No response'}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def get_current_config() -> None:
    """Display current Postmark configuration."""
    
    config = PostmarkConfig()
    client = PostmarkAPIClient(config.ACCOUNT_TOKEN, config.SERVER_TOKEN)
    
    try:
        print(f"📊 Current Postmark Configuration")
        print(f"   Server ID: {config.SERVER_ID}")
        
        server_info = client.get_server_info(config.SERVER_ID)
        
        print(f"\n🔧 Server Settings:")
        print(f"   Name: {server_info.get('Name', 'Not set')}")
        print(f"   Inbound Domain: {server_info.get('InboundDomain', 'Not set')}")
        print(f"   Inbound Webhook: {server_info.get('InboundHookUrl', 'Not set')}")
        print(f"   SMTP Enabled: {server_info.get('SmtpApiActivated', False)}")
        
        # Get message streams
        streams = client.get_message_streams(config.SERVER_ID)
        print(f"\n📬 Message Streams:")
        
        for stream in streams.get("MessageStreams", []):
            print(f"   - {stream.get('Name')} ({stream.get('ID')})")
            print(f"     Type: {stream.get('MessageStreamType')}")
            
    except Exception as e:
        print(f"❌ Error fetching configuration: {e}")
        sys.exit(1)


def main():
    """Main CLI interface."""
    
    parser = argparse.ArgumentParser(
        description="Configure Postmark webhook URL for different environments"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Set webhook command
    set_parser = subparsers.add_parser("set", help="Set webhook URL for environment")
    set_parser.add_argument(
        "env",
        choices=["dev", "prod", "local", "test"],
        help="Environment to configure"
    )
    set_parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only test webhook, don't update configuration"
    )
    
    # Get current config command
    subparsers.add_parser("status", help="Show current configuration")
    
    # Quick switch commands
    subparsers.add_parser("dev", help="Quick switch to dev environment")
    subparsers.add_parser("prod", help="Quick switch to prod environment")
    
    args = parser.parse_args()
    
    # Check for API tokens
    config = PostmarkConfig()
    if config.ACCOUNT_TOKEN == "your-account-token":
        print("❌ Please set POSTMARK_ACCOUNT_API_TOKEN environment variable")
        print("   Get it from: https://account.postmarkapp.com/account/edit")
        sys.exit(1)
    
    if config.SERVER_TOKEN == "your-server-token":
        print("❌ Please set POSTMARK_SERVER_API_TOKEN environment variable")
        print("   Get it from: Your server's API Tokens page in Postmark")
        sys.exit(1)
    
    # Execute commands
    if args.command == "set":
        configure_webhook(args.env, args.test_only)
    elif args.command == "status":
        get_current_config()
    elif args.command == "dev":
        configure_webhook("dev")
    elif args.command == "prod":
        configure_webhook("prod")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
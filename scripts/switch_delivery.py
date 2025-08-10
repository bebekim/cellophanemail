#!/usr/bin/env python3
"""
Quick script to switch email delivery methods between SMTP and Postmark.
Usage: python scripts/switch_delivery.py [smtp|postmark]
"""

import sys
import os
from pathlib import Path

def switch_delivery_method(method):
    """Switch email delivery method in .env file."""
    if method not in ['smtp', 'postmark']:
        print(f"❌ Invalid method '{method}'. Use 'smtp' or 'postmark'")
        return False
    
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print(f"❌ .env file not found at {env_file}")
        return False
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update the EMAIL_DELIVERY_METHOD line
    updated_lines = []
    method_found = False
    
    for line in lines:
        if line.startswith('EMAIL_DELIVERY_METHOD='):
            updated_lines.append(f'EMAIL_DELIVERY_METHOD={method}\n')
            method_found = True
        else:
            updated_lines.append(line)
    
    if not method_found:
        # Add the setting if it doesn't exist
        updated_lines.append(f'EMAIL_DELIVERY_METHOD={method}\n')
    
    # Write updated content back
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    return True

def get_current_method():
    """Get current email delivery method from .env file."""
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return "unknown"
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('EMAIL_DELIVERY_METHOD='):
                return line.split('=', 1)[1].strip()
    
    return "not_set"

def show_status():
    """Show current delivery method and configuration."""
    current = get_current_method()
    print(f"📧 Current email delivery method: {current}")
    
    if current == "smtp":
        print("📤 SMTP Configuration:")
        print("   - Host: smtp.gmail.com:587")
        print("   - Username: goldenfermi@gmail.com")
        print("   - From: noreply@cellophanemail.com")
    elif current == "postmark":
        print("📮 Postmark Configuration:")
        print("   - API: Postmark REST API")
        print("   - Token: 06a5003f-1289-49c3-9f54-67958b6a669e")
        print("   - From: noreply@cellophanemail.com")

def main():
    if len(sys.argv) == 1:
        # No arguments - show current status
        show_status()
        print("\n💡 Usage:")
        print("   python scripts/switch_delivery.py smtp     # Switch to SMTP")
        print("   python scripts/switch_delivery.py postmark # Switch to Postmark")
        return
    
    if len(sys.argv) != 2:
        print("❌ Usage: python scripts/switch_delivery.py [smtp|postmark]")
        sys.exit(1)
    
    method = sys.argv[1].lower()
    
    if method == "status":
        show_status()
        return
    
    current = get_current_method()
    print(f"📧 Current method: {current}")
    
    if current == method:
        print(f"✅ Already using {method} delivery method")
        return
    
    print(f"🔄 Switching from {current} to {method}...")
    
    if switch_delivery_method(method):
        print(f"✅ Successfully switched to {method} delivery method")
        print("🔄 Restart your SMTP server to pick up the changes")
    else:
        print("❌ Failed to switch delivery method")
        sys.exit(1)

if __name__ == "__main__":
    main()
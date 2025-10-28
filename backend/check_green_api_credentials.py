#!/usr/bin/env python3
"""
Check and display current Green API credentials
"""

from credential_manager import GreenAPICredentials

def main():
    print("=" * 60)
    print("🔍 Checking Green API Credentials")
    print("=" * 60)

    green_api = GreenAPICredentials()

    # Check if credentials exist
    if not green_api.has_credentials():
        print("\n❌ No Green API credentials found in database")
        print("\n💡 Next steps:")
        print("1. Get your Green API credentials from https://green-api.com")
        print("2. You'll need: instance_id and token")
        print("3. Update credentials using the web interface settings page")
        print("4. Or use save_green_api_credentials.py script")
        return

    # Get and display credentials
    creds = green_api.get_credentials()

    if not creds:
        print("\n❌ Failed to decrypt credentials")
        print("💡 The encryption key might have changed")
        return

    print("\n✅ Credentials found:")
    print("-" * 60)
    print(f"Instance ID: {creds.get('instance_id', 'NOT SET')}")
    print(f"Token: {creds.get('token', 'NOT SET')[:20]}..." if creds.get('token') else "Token: NOT SET")
    print(f"ID Instance: {creds.get('id_instance', 'NOT SET')}")
    print(f"Saved at: {creds.get('saved_at', 'UNKNOWN')}")
    print("-" * 60)

    # Validate format
    is_valid, message = green_api.validate_credentials(creds)

    if is_valid:
        print("\n✅ Credential format is valid")
    else:
        print(f"\n❌ Credential validation failed: {message}")

    print("\n⚠️  Note: This only checks if credentials exist and are formatted correctly.")
    print("   To test if they work with Green API, try the sync function.")
    print("\n💡 To update credentials, run: python3 save_green_api_credentials.py")

if __name__ == "__main__":
    main()

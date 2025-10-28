#!/usr/bin/env python3
"""
Save/Update Green API credentials
"""

import sys
from credential_manager import GreenAPICredentials

def main():
    print("=" * 60)
    print("🔐 Green API Credentials Setup")
    print("=" * 60)

    # Check if credentials are provided as arguments
    if len(sys.argv) == 3:
        instance_id = sys.argv[1]
        token = sys.argv[2]
        print("\n📥 Using credentials from command line arguments")
    else:
        # Interactive mode
        print("\n💡 Get your credentials from: https://green-api.com")
        print("   Dashboard → Your Instance → Settings")
        print()

        instance_id = input("Enter Instance ID: ").strip()
        token = input("Enter API Token: ").strip()

    if not instance_id or not token:
        print("\n❌ Both Instance ID and Token are required!")
        print("\n📖 Usage:")
        print("   python3 save_green_api_credentials.py <instance_id> <token>")
        print("   OR run without arguments for interactive mode")
        sys.exit(1)

    # Validate format
    green_api = GreenAPICredentials()
    test_creds = {
        "instance_id": instance_id,
        "token": token
    }

    is_valid, message = green_api.validate_credentials(test_creds)

    if not is_valid:
        print(f"\n❌ Validation failed: {message}")
        sys.exit(1)

    print("\n✅ Credential format is valid")
    print("\n💾 Saving credentials...")

    # Save credentials
    try:
        green_api.save_credentials(
            instance_id=instance_id,
            token=token,
            id_instance=instance_id  # Use same value for both fields
        )
        print("✅ Credentials saved successfully!")
        print("\n🔍 Saved credentials:")
        print("-" * 60)
        print(f"Instance ID: {instance_id}")
        print(f"Token: {token[:20]}...")
        print("-" * 60)

        print("\n✅ Done! You can now use the sync functionality.")
        print("💡 Test the connection by clicking 'סנכרן הכל עכשיו' in the web interface")

    except Exception as e:
        print(f"\n❌ Error saving credentials: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

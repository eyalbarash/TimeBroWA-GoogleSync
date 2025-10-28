#!/usr/bin/env python3
"""
Quick checker for Google Calendar credentials setup
"""

import os
import json
from pathlib import Path

def check_credentials():
    project_dir = Path.cwd()
    credentials_file = project_dir / "credentials.json"
    
    print("🔍 Checking Google Calendar API setup...")
    print("="*50)
    
    # Check if credentials.json exists
    if not credentials_file.exists():
        print("❌ credentials.json NOT FOUND")
        print(f"📂 Looking in: {project_dir}")
        print("\n💡 Next steps:")
        print("1. Complete Google Cloud Console setup")
        print("2. Download OAuth2 credentials JSON file")
        print("3. Rename it to 'credentials.json'")
        print("4. Place it in this directory")
        print(f"\n📖 See: calendar_setup_instructions.md")
        return False
    
    # Check if it's a valid credentials file
    try:
        with open(credentials_file) as f:
            creds_data = json.load(f)
        
        if 'installed' in creds_data:
            client_info = creds_data['installed']
            print("✅ credentials.json found and valid!")
            print(f"📱 Client ID: {client_info.get('client_id', 'N/A')[:20]}...")
            print(f"🔗 Auth URI: {client_info.get('auth_uri', 'N/A')}")
            print("\n🎉 Ready to authenticate!")
            print("\n🚀 Run this to create your 12 PM meeting:")
            print("   python3 timebro_calendar.py")
            return True
        else:
            print("❌ Invalid credentials file format")
            print("💡 Make sure you selected 'Desktop application' type")
            return False
            
    except json.JSONDecodeError:
        print("❌ credentials.json is not valid JSON")
        print("💡 Please re-download from Google Cloud Console")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {str(e)}")
        return False

if __name__ == "__main__":
    check_credentials()















#!/usr/bin/env python3
"""
Retrieve WhatsApp messages from a specific contact using Green API
"""

import sys
import json
import requests
from credential_manager import GreenAPICredentials
from datetime import datetime

def format_phone_number(phone):
    """Format phone number to Green API format (remove spaces, hyphens, add country code if needed)"""
    # Remove all non-numeric characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # If starts with 0, replace with 972 (Israel code)
    if phone.startswith('0'):
        phone = '972' + phone[1:]
    
    # If doesn't start with country code, add 972
    if not phone.startswith('972'):
        phone = '972' + phone
    
    # Add @c.us suffix for WhatsApp chat ID
    return f"{phone}@c.us"

def get_all_messages(instance_id, token, count=100):
    """
    Get recent messages using lastIncomingMessages endpoint
    
    Args:
        instance_id: Green API instance ID
        token: Green API token
        count: Number of messages to retrieve
    
    Returns:
        List of messages or None if error
    """
    base_url = f"https://api.green-api.com/waInstance{instance_id}"
    endpoint = f"{base_url}/lastIncomingMessages/{token}"
    
    try:
        # Use minutes parameter to get messages from last 24 hours
        response = requests.get(f"{endpoint}?minutes=1440", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching messages: {e}")
        return None

def filter_messages_by_contact(messages, chat_id):
    """Filter messages from specific contact"""
    if not messages:
        return []
    
    filtered = []
    for msg in messages:
        # Check if message is from the specific chat
        msg_chat_id = msg.get('chatId', '')
        sender_data = msg.get('senderData', {})
        
        if msg_chat_id == chat_id or sender_data.get('chatId') == chat_id:
            filtered.append(msg)
    
    return filtered

def format_message(msg, index):
    """Format a single message for display"""
    msg_data = msg.get('messageData', {})
    msg_type = msg.get('type', msg_data.get('typeMessage', 'unknown'))
    timestamp = msg.get('timestamp', msg_data.get('timestamp', 0))
    
    # Get sender info
    sender_data = msg.get('senderData', {})
    sender_name = sender_data.get('sender', sender_data.get('senderName', 'Unknown'))
    chat_id = sender_data.get('chatId', msg.get('chatId', 'Unknown'))
    
    # Convert timestamp to readable format
    try:
        if isinstance(timestamp, int) and timestamp > 0:
            dt = datetime.fromtimestamp(timestamp)
            timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_str = str(timestamp)
    except:
        timestamp_str = str(timestamp)
    
    print(f"\n{'='*70}")
    print(f"Message #{index + 1}")
    print(f"{'='*70}")
    print(f"📅 Time: {timestamp_str}")
    print(f"👤 From: {sender_name}")
    print(f"💬 Chat: {chat_id}")
    print(f"📝 Type: {msg_type}")
    
    # Extract message content based on type
    text_message = msg_data.get('textMessageData', {}).get('textMessage', '')
    extended_text = msg_data.get('extendedTextMessageData', {}).get('text', '')
    
    if text_message:
        print(f"💬 Message: {text_message}")
    elif extended_text:
        print(f"💬 Message: {extended_text}")
    elif msg_type == 'imageMessage':
        caption = msg_data.get('fileMessageData', {}).get('caption', 'No caption')
        print(f"🖼️  Image: {caption}")
    elif msg_type == 'videoMessage':
        caption = msg_data.get('fileMessageData', {}).get('caption', 'No caption')
        print(f"🎥 Video: {caption}")
    elif msg_type == 'documentMessage':
        filename = msg_data.get('fileMessageData', {}).get('fileName', 'Unknown')
        print(f"📄 Document: {filename}")
    elif msg_type == 'audioMessage':
        print(f"🎵 Audio message")
    else:
        # Show raw data for debugging
        print(f"📦 Raw data:")
        print(json.dumps(msg, indent=2, ensure_ascii=False))

def main():
    if len(sys.argv) < 2:
        print("Usage: python get_messages.py <phone_number> [count]")
        print("Example: python get_messages.py +972535463173")
        print("Example: python get_messages.py 053-546-3173 30")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    message_count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"\n🔍 Retrieving messages from {phone_number}...")
    print("="*70)
    
    # Get credentials
    creds_manager = GreenAPICredentials()
    
    if not creds_manager.has_credentials():
        print("❌ No Green API credentials found!")
        print("💡 Please set up your credentials first using the web interface.")
        sys.exit(1)
    
    creds = creds_manager.get_credentials()
    instance_id = creds.get('instance_id') or creds.get('id_instance')
    token = creds.get('token')
    
    if not instance_id or not token:
        print("❌ Invalid credentials format!")
        sys.exit(1)
    
    print(f"✅ Credentials loaded")
    print(f"🔑 Instance ID: {instance_id}")
    
    # Format phone number
    chat_id = format_phone_number(phone_number)
    print(f"📱 Chat ID: {chat_id}")
    print(f"📊 Fetching recent messages...")
    print()
    
    # Get all recent messages
    result = get_all_messages(instance_id, token)
    
    if result is None:
        print("❌ Failed to retrieve messages")
        sys.exit(1)
    
    # Check for errors in response
    if isinstance(result, dict) and 'error' in result:
        print(f"❌ API Error: {result.get('error')}")
        sys.exit(1)
    
    # Filter messages from specific contact
    all_messages = result if isinstance(result, list) else []
    messages = filter_messages_by_contact(all_messages, chat_id)
    
    # Limit to requested count
    messages = messages[:message_count]
    
    if not messages:
        print(f"📭 No messages found for {phone_number}")
        print(f"💡 Total messages retrieved: {len(all_messages)}")
        sys.exit(0)
    
    print(f"\n✅ Found {len(messages)} messages from {phone_number}\n")
    
    # Display messages
    for i, msg in enumerate(messages):
        format_message(msg, i)
    
    print(f"\n{'='*70}")
    print(f"✅ Retrieved {len(messages)} messages from {phone_number}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

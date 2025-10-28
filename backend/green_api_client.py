"""
Green API client for WhatsApp integration
Handles API communication and connection testing
"""

import requests
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

class GreenAPIClient:
    def __init__(self, instance_id: str, token: str, id_instance: Optional[str] = None):
        self.instance_id = instance_id
        self.token = token
        self.id_instance = id_instance or instance_id
        self.base_url = f"https://api.green-api.com/waInstance{self.instance_id}"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """Make API request to Green API"""
        url = f"{self.base_url}/{endpoint}/{self.token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                return False, {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            return True, response.json()
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout - Green API server not responding"}
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error - Unable to reach Green API server"}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return False, {"error": "Unauthorized - Invalid instance ID or token"}
            elif e.response.status_code == 403:
                return False, {"error": "Forbidden - Check your API permissions"}
            elif e.response.status_code == 404:
                return False, {"error": "Not found - Invalid API endpoint or instance"}
            else:
                return False, {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}
    
    def test_connection(self) -> Tuple[bool, Dict]:
        """Test Green API connection and credentials"""
        success, response = self._make_request("GET", "getSettings")
        
        if success:
            return True, {
                "status": "connected",
                "message": "Successfully connected to Green API",
                "instance_info": response,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return False, {
                "status": "failed",
                "message": "Failed to connect to Green API",
                "error": response.get("error", "Unknown error"),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_account_info(self) -> Tuple[bool, Dict]:
        """Get WhatsApp account information"""
        return self._make_request("GET", "getSettings")
    
    def get_state_instance(self) -> Tuple[bool, Dict]:
        """Get WhatsApp instance state"""
        return self._make_request("GET", "getStateInstance")
    
    def send_message(self, chat_id: str, message: str) -> Tuple[bool, Dict]:
        """Send a test message"""
        data = {
            "chatId": chat_id,
            "message": message
        }
        return self._make_request("POST", "sendMessage", data)
    
    def get_contacts(self) -> Tuple[bool, Dict]:
        """Get WhatsApp contacts"""
        return self._make_request("GET", "getContacts")
    
    def get_chats(self) -> Tuple[bool, Dict]:
        """Get WhatsApp chats"""
        return self._make_request("GET", "getChats")

    def get_chat_history(self, chat_id: str, count: int = 100) -> Tuple[bool, Dict]:
        """Get chat history for a specific chat"""
        data = {
            "chatId": chat_id,
            "count": count
        }
        return self._make_request("POST", "getChatHistory", data)

    def get_chat_history_by_date_range(self, chat_id: str, start_date: datetime, end_date: datetime) -> list:
        """
        Get chat history for a specific date range

        Args:
            chat_id: WhatsApp chat ID (e.g., '972501234567@c.us' or 'group@g.us')
            start_date: Start date (datetime object)
            end_date: End date (datetime object)

        Returns:
            List of messages in the date range
        """
        # Convert dates to timestamps (Green API uses Unix timestamps)
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        # Get messages - Green API doesn't have native date range filtering
        # So we fetch more messages and filter client-side
        success, response = self.get_chat_history(chat_id, count=1000)

        if not success:
            return []

        messages = response if isinstance(response, list) else response.get('messages', [])

        # Filter messages by date range
        filtered_messages = []
        for msg in messages:
            # Green API message timestamp is in seconds
            msg_timestamp = msg.get('timestamp', 0)

            if start_timestamp <= msg_timestamp <= end_timestamp:
                filtered_messages.append(msg)

        return filtered_messages

    def get_credential_help(self) -> Dict:
        """Get help information for finding Green API credentials"""
        return {
            "title": "How to find your Green API credentials",
            "steps": [
                {
                    "step": 1,
                    "title": "Go to Green API Console",
                    "description": "Visit https://console.green-api.com/",
                    "action": "Open the Green API console in your browser"
                },
                {
                    "step": 2,
                    "title": "Create or select an instance",
                    "description": "Create a new WhatsApp instance or select an existing one",
                    "action": "Click 'Create instance' or select from your instances list"
                },
                {
                    "step": 3,
                    "title": "Get your credentials",
                    "description": "Copy the Instance ID and Token from your instance settings",
                    "action": "Look for 'Instance ID' and 'Token' in the instance details"
                },
                {
                    "step": 4,
                    "title": "QR Code setup",
                    "description": "Scan the QR code with your WhatsApp to link the instance",
                    "action": "Use your phone to scan the QR code displayed in the console"
                },
                {
                    "step": 5,
                    "title": "Verify connection",
                    "description": "Make sure the instance shows as 'Authorized' status",
                    "action": "Check that the instance status is green/authorized"
                }
            ],
            "troubleshooting": [
                {
                    "issue": "Invalid credentials error",
                    "solution": "Double-check your Instance ID and Token. Make sure there are no extra spaces."
                },
                {
                    "issue": "Instance not authorized",
                    "solution": "Scan the QR code with your WhatsApp to authorize the instance."
                },
                {
                    "issue": "Connection timeout",
                    "solution": "Check your internet connection and try again. Green API servers might be temporarily unavailable."
                },
                {
                    "issue": "Forbidden error",
                    "solution": "Check your Green API subscription status and permissions."
                }
            ],
            "support": {
                "documentation": "https://green-api.com/docs/",
                "console": "https://console.green-api.com/",
                "support": "https://green-api.com/support/"
            }
        }

class GreenAPITester:
    """Test Green API connection and provide detailed feedback"""
    
    def __init__(self, credential_manager):
        self.credential_manager = credential_manager
    
    def test_credentials(self, instance_id: str, token: str, id_instance: Optional[str] = None) -> Dict:
        """Test Green API credentials and provide detailed feedback"""
        client = GreenAPIClient(instance_id, token, id_instance)
        
        # Test basic connection
        success, response = client.test_connection()
        
        result = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "credentials": {
                "instance_id": instance_id,
                "token": token[:8] + "..." if token else None,  # Mask token for security
                "id_instance": id_instance
            }
        }
        
        if success:
            result.update({
                "message": "✅ Green API connection successful!",
                "details": response,
                "next_steps": [
                    "Credentials are valid and working",
                    "You can now use WhatsApp integration features",
                    "Consider saving these credentials for future use"
                ]
            })
        else:
            result.update({
                "message": "❌ Green API connection failed",
                "error": response.get("error", "Unknown error"),
                "help": client.get_credential_help(),
                "suggestions": self._get_error_suggestions(response.get("error", ""))
            })
        
        return result
    
    def _get_error_suggestions(self, error: str) -> list:
        """Get specific suggestions based on error type"""
        suggestions = []
        
        if "Unauthorized" in error or "401" in error:
            suggestions.extend([
                "Check your Instance ID - it should be a numeric value",
                "Verify your Token is correct and hasn't expired",
                "Make sure there are no extra spaces in your credentials"
            ])
        elif "Forbidden" in error or "403" in error:
            suggestions.extend([
                "Check your Green API subscription status",
                "Verify you have the necessary permissions",
                "Contact Green API support if the issue persists"
            ])
        elif "Not found" in error or "404" in error:
            suggestions.extend([
                "Verify your Instance ID is correct",
                "Make sure the instance exists in your Green API console",
                "Check if the instance has been deleted or deactivated"
            ])
        elif "timeout" in error.lower():
            suggestions.extend([
                "Check your internet connection",
                "Try again in a few minutes - Green API servers might be busy",
                "Check if your firewall is blocking the connection"
            ])
        else:
            suggestions.extend([
                "Double-check all your credentials",
                "Make sure your WhatsApp instance is authorized",
                "Try creating a new instance in Green API console"
            ])
        
        return suggestions
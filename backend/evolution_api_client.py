#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution API Client for WhatsApp Group Management
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvolutionAPIClient:
    """Evolution API client for WhatsApp group management"""
    
    def __init__(self, api_base_url: str = "https://evolution.cigcrm.com", 
                 api_key: str = "A6401FCD5870-4CDB-87C4-6A22F06745CD", 
                 instance: str = None):
        """
        Initialize Evolution API client
        
        Args:
            api_base_url: Evolution API base URL
            api_key: Evolution API key
            instance: WhatsApp instance name
        """
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.instance = instance
        self.session = requests.Session()
        self.session.timeout = 30
        
        self.headers = {
            'apikey': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0
    
    def _rate_limit(self):
        """Implement rate limiting to avoid overwhelming the API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                     retry_count: int = 3) -> Dict:
        """
        Make HTTP request to Evolution API with retry logic
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            data: Request data
            retry_count: Number of retries on failure
            
        Returns:
            API response as dictionary
        """
        self._rate_limit()
        
        url = f"{self.api_base_url}/{endpoint}"
        
        for attempt in range(retry_count):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, headers=self.headers, params=data)
                elif method.upper() == "POST":
                    response = self.session.post(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = self.session.delete(url, headers=self.headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                # Handle empty responses
                if not response.content:
                    return {"success": True}
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == retry_count - 1:
                    return {"error": f"Request failed after {retry_count} attempts: {str(e)}"}
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return {"error": "Maximum retry attempts exceeded"}
    
    def get_groups(self) -> Dict:
        """Get all groups"""
        endpoint = f"group/fetchAllGroups/{self.instance}"
        return self._make_request("GET", endpoint)
    
    def get_group_participants(self, group_id: str) -> Dict:
        """Get group participants"""
        endpoint = f"group/participants/{self.instance}"
        data = {"groupJid": group_id}
        return self._make_request("POST", endpoint, data)
    
    def remove_participant(self, group_id: str, participant_id: str) -> Dict:
        """Remove a participant from a group"""
        endpoint = f"group/removeParticipants/{self.instance}"
        data = {
            "groupJid": group_id,
            "participants": [participant_id]
        }
        return self._make_request("POST", endpoint, data)
    
    def leave_group(self, group_id: str) -> Dict:
        """Leave a group"""
        endpoint = f"group/leaveGroup/{self.instance}"
        data = {"groupJid": group_id}
        return self._make_request("POST", endpoint, data)
    
    def delete_group_completely(self, group_id: str) -> Dict:
        """
        Delete a group completely from WhatsApp using Evolution API by:
        1. Getting all participants
        2. Removing all participants except self
        3. Leaving the group
        
        Args:
            group_id: WhatsApp group ID (e.g., 120363123456789012@g.us)
            
        Returns:
            Dictionary with success status and details
        """
        try:
            logger.info(f"Starting complete deletion of group {group_id} using Evolution API")
            
            # Step 1: Get group participants
            participants_result = self.get_group_participants(group_id)
            if "error" in participants_result:
                return {"success": False, "error": f"Failed to get group participants: {participants_result['error']}"}
            
            participants = participants_result.get("participants", [])
            logger.info(f"Found {len(participants)} participants in group")
            
            # Step 2: Remove all participants except self
            removed_count = 0
            for participant in participants:
                participant_id = participant.get("id")
                if participant_id and not participant.get("isMe", False):
                    logger.info(f"Removing participant {participant_id}")
                    remove_result = self.remove_participant(group_id, participant_id)
                    
                    if "error" not in remove_result:
                        removed_count += 1
                        logger.info(f"Successfully removed participant {participant_id}")
                    else:
                        logger.warning(f"Failed to remove participant {participant_id}: {remove_result['error']}")
                    
                    # Small delay between removals
                    time.sleep(1)
            
            logger.info(f"Removed {removed_count} participants")
            
            # Step 3: Leave the group
            logger.info("Leaving the group...")
            leave_result = self.leave_group(group_id)
            
            if "error" in leave_result:
                return {"success": False, "error": f"Failed to leave group: {leave_result['error']}"}
            
            logger.info("Successfully left the group")
            
            return {
                "success": True, 
                "message": f"Group {group_id} deleted successfully via Evolution API",
                "participants_removed": removed_count,
                "group_left": True,
                "api_used": "evolution"
            }
            
        except Exception as e:
            logger.error(f"Error deleting group {group_id}: {e}")
            return {"success": False, "error": str(e)}


# Convenience function
def get_evolution_api_client(instance: str = None) -> EvolutionAPIClient:
    """
    Get Evolution API client with credentials from environment or parameters
    
    Args:
        instance: WhatsApp instance name (optional, will use env var if not provided)
        
    Returns:
        Evolution API client instance
    """
    import os
    
    if not instance:
        instance = os.getenv("EVOLUTION_INSTANCE")
    
    if not instance:
        raise ValueError("Evolution instance not provided. Set EVOLUTION_INSTANCE environment variable or pass it as parameter.")
    
    return EvolutionAPIClient(instance=instance)


if __name__ == "__main__":
    # Test the Evolution API client
    try:
        client = get_evolution_api_client()
        
        # Test basic functionality
        print("Testing Evolution API connection...")
        groups = client.get_groups()
        print(f"Groups: {json.dumps(groups, indent=2)}")
        
    except Exception as e:
        print(f"Error testing Evolution API client: {e}")

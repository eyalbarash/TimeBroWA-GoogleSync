"""
Secure credential management for Green API
Handles encryption, storage, and validation of API credentials
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import sqlite3
from datetime import datetime, timedelta

class CredentialManager:
    def __init__(self, db_path="credentials.db"):
        self.db_path = db_path
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        self._init_database()
    
    def _get_or_create_key(self):
        """Get or create encryption key for credentials"""
        key_file = "credential_key.key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def _init_database(self):
        """Initialize credentials database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                encrypted_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _encrypt_data(self, data):
        """Encrypt sensitive data"""
        json_data = json.dumps(data)
        encrypted_data = self.cipher.encrypt(json_data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def save_credentials(self, service, credentials):
        """Save encrypted credentials for a service"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if credentials already exist
        cursor.execute("SELECT id FROM credentials WHERE service = ?", (service,))
        existing = cursor.fetchone()
        
        encrypted_data = self._encrypt_data(credentials)
        
        if existing:
            # Update existing credentials
            cursor.execute('''
                UPDATE credentials 
                SET encrypted_data = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE service = ?
            ''', (encrypted_data, service))
        else:
            # Insert new credentials
            cursor.execute('''
                INSERT INTO credentials (service, encrypted_data) 
                VALUES (?, ?)
            ''', (service, encrypted_data))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_credentials(self, service):
        """Retrieve and decrypt credentials for a service"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT encrypted_data FROM credentials WHERE service = ?", (service,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        try:
            return self._decrypt_data(result[0])
        except ValueError as e:
            print(f"Error decrypting credentials: {e}")
            return None
    
    def delete_credentials(self, service):
        """Delete credentials for a service"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM credentials WHERE service = ?", (service,))
        conn.commit()
        conn.close()
        
        return True
    
    def has_credentials(self, service):
        """Check if credentials exist for a service"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM credentials WHERE service = ?", (service,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def list_services(self):
        """List all services with stored credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT service, created_at, updated_at FROM credentials ORDER BY updated_at DESC")
        services = cursor.fetchall()
        conn.close()
        
        return [{"service": row[0], "created_at": row[1], "updated_at": row[2]} for row in services]

class GreenAPICredentials:
    """Green API specific credential management"""
    
    def __init__(self):
        self.credential_manager = CredentialManager()
        self.service_name = "green_api"
    
    def save_credentials(self, instance_id, token, id_instance=None):
        """Save Green API credentials"""
        credentials = {
            "instance_id": instance_id,
            "token": token,
            "id_instance": id_instance,
            "saved_at": datetime.now().isoformat()
        }
        
        return self.credential_manager.save_credentials(self.service_name, credentials)
    
    def get_credentials(self):
        """Get Green API credentials"""
        return self.credential_manager.get_credentials(self.service_name)
    
    def has_credentials(self):
        """Check if Green API credentials exist"""
        return self.credential_manager.has_credentials(self.service_name)
    
    def delete_credentials(self):
        """Delete Green API credentials"""
        return self.credential_manager.delete_credentials(self.service_name)
    
    def validate_credentials(self, credentials):
        """Validate credential format"""
        required_fields = ["instance_id", "token"]
        
        if not credentials:
            return False, "No credentials provided"
        
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                return False, f"Missing or empty field: {field}"
        
        # Validate instance_id format (should be numeric)
        try:
            int(credentials["instance_id"])
        except ValueError:
            return False, "Instance ID must be numeric"
        
        return True, "Credentials format is valid"




















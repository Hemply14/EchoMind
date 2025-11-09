# app/core/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from app.config import settings

class DataEncryptor:
    def __init__(self):
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)
    
    def _get_or_create_key(self):
        key_file = settings.data_dir / "encryption.key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate key from user-specific seed
            seed = os.urandom(32)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'privacy_ai_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(seed))
            
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt(self, data: str) -> bytes:
        return self.fernet.encrypt(data.encode('utf-8'))
    
    def decrypt(self, encrypted_data: bytes) -> str:
        return self.fernet.decrypt(encrypted_data).decode('utf-8')
import os
import json
import base64
from typing import List, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorEncryptionError(Exception):
    """Custom exception for vector encryption/decryption errors"""
    pass

class VectorEncryption:
    def __init__(self, key: bytes = None):
        """
        Initialize the VectorEncryption with a key.
        If no key is provided, it will be read from environment variable VECTOR_ENCRYPTION_KEY.
        The key should be a base64-encoded string.
        """
        key_str = key or os.getenv("VECTOR_ENCRYPTION_KEY")
        if not key_str:
            raise VectorEncryptionError("VECTOR_ENCRYPTION_KEY environment variable is not set.")
            
        try:
            # Decode the base64 key to get raw bytes
            self.key = base64.urlsafe_b64decode(key_str)
            if len(self.key) not in [16, 24, 32]:
                raise VectorEncryptionError(
                    f"Decoded key must be 16, 24, or 32 bytes long after base64 decoding. "
                    f"Got {len(self.key)} bytes."
                )
        except Exception as e:
            raise VectorEncryptionError(f"Invalid encryption key: {str(e)}")
        self.aesgcm = AESGCM(self.key)
        self.iv_length = 12  # 12 bytes for GCM is recommended

    def encrypt_vector(self, vector: List[float]) -> Tuple[bytes, bytes]:
        """
        Encrypt a facial vector.
        
        Args:
            vector: List of floats representing the facial vector
            
        Returns:
            Tuple of (encrypted_data, iv) where both are bytes
        """
        try:
            # Serialize the vector to JSON and encode to bytes
            vector_serialized = json.dumps(vector).encode('utf-8')
            
            # Generate a random IV
            iv = os.urandom(self.iv_length)
            
            # Encrypt the vector
            encrypted_data = self.aesgcm.encrypt(iv, vector_serialized, None)
            
            return encrypted_data, iv
            
        except Exception as e:
            logger.error(f"Error encrypting vector: {str(e)}")
            raise VectorEncryptionError(f"Failed to encrypt vector: {str(e)}")

    def decrypt_vector(self, encrypted_data: bytes, iv) -> List[float]:
        """
        Decrypt an encrypted facial vector.
        
        Args:
            encrypted_data: Encrypted vector data (bytes or base64 string)
            iv: Initialization vector (bytes, base64 string, or string representation of bytes)
            
        Returns:
            List of floats representing the original facial vector
            
        Raises:
            VectorEncryptionError: If decryption fails
        """
        try:
            # Convert IV to bytes if it's a string
            if isinstance(iv, str):
                if iv.startswith('b\'') and iv.endswith('\''):
                    # Handle string representation of bytes (e.g., "b'...'")
                    iv = iv[2:-1].encode('latin-1')
                else:
                    # Try to decode as base64
                    try:
                        iv = base64.b64decode(iv)
                    except Exception:
                        # If base64 decoding fails, try UTF-8 encoding
                        iv = iv.encode('utf-8')
            
            # Ensure encrypted_data is bytes
            if isinstance(encrypted_data, str):
                try:
                    encrypted_data = base64.b64decode(encrypted_data)
                except Exception:
                    encrypted_data = encrypted_data.encode('utf-8')
            
            logger.debug(f"IV type: {type(iv)}, IV value: {iv}")
            logger.debug(f"Encrypted data type: {type(encrypted_data)}, length: {len(encrypted_data) if encrypted_data else 0}")
            
            # Decrypt the data
            decrypted_data = self.aesgcm.decrypt(iv, encrypted_data, None)
            
            # If the data is already a list, return it directly
            if isinstance(decrypted_data, list):
                return decrypted_data
                
            # If it's bytes, decode it first
            if isinstance(decrypted_data, bytes):
                decrypted_data = decrypted_data.decode('utf-8')
                
            # If it's a string, try to parse it as JSON
            if isinstance(decrypted_data, str):
                try:
                    vector = json.loads(decrypted_data)
                    if not isinstance(vector, list):
                        raise ValueError("Decrypted data is not a list")
                except json.JSONDecodeError:
                    # If it's not valid JSON, try to parse it as a string representation of a list
                    try:
                        # Handle string like "[1.0, 2.0, 3.0]"
                        import ast
                        vector = ast.literal_eval(decrypted_data)
                        if not isinstance(vector, list):
                            raise ValueError("Decrypted data is not a list")
                    except (ValueError, SyntaxError):
                        raise ValueError("Could not parse decrypted data as a list")
            
            # Validate the decrypted data
            if not isinstance(vector, list) or not all(isinstance(x, (int, float)) for x in vector):
                raise ValueError("Decrypted data is not a valid vector")
                
            return vector
            
        except (InvalidTag, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error decrypting vector: {str(e)}", exc_info=True)
            raise VectorEncryptionError(f"Failed to decrypt vector: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during decryption: {str(e)}", exc_info=True)
            raise VectorEncryptionError(f"Failed to decrypt vector: {str(e)}")

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key (32 bytes for AES-256) and return it as a base64 string.
        This is useful for generating a secure key to be stored in environment variables.
        """
        return base64.b64encode(os.urandom(32)).decode('utf-8')

# Example usage:
if __name__ == "__main__":
    # Generate a new key (do this once and store it in your environment variables)
    print("Generated key (save this to VECTOR_ENCRYPTION_KEY):")
    print(VectorEncryption.generate_key())
    
    # Example of how to use the encryption/decryption
    try:
        # Initialize with key from environment
        crypto = VectorEncryption()
        
        # Example vector (128-dimensional)
        test_vector = [0.1 * i for i in range(128)]
        
        # Encrypt
        encrypted, iv = crypto.encrypt_vector(test_vector)
        print(f"Encrypted data length: {len(encrypted)} bytes")
        
        # Decrypt
        decrypted = crypto.decrypt_vector(encrypted, iv)
        print(f"Decryption successful: {decrypted == test_vector}")
        
    except VectorEncryptionError as e:
        print(f"Error: {str(e)}")

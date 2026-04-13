from cryptography.fernet import Fernet
from django.conf import settings
def _get_fernet():
    """Retrieve the Fernet instance using the dedicated messaging key."""
    # Ensure the key is bytes, standardizing from environment config
    key = settings.MESSAGING_KEY
    if isinstance(key, str):
        key = key.encode('utf-8')
    return Fernet(key)
def encrypt_message(text: str) -> bytes:
    """Encrypt a plain text string to Fernet AES-256 bytes."""
    if not text:
        return b''
    f = _get_fernet()
    return f.encrypt(text.encode('utf-8'))
def decrypt_message(token) -> str:
    """Decrypt Fernet AES-256 bytes back to a plain text string."""
    if not token:
        return ""
    # Support backward compatibility if token is somehow stored as str
    if isinstance(token, str):
        token = token.encode('utf-8')
    elif isinstance(token, memoryview):
        token = bytes(token)
    elif not isinstance(token, bytes):
        token = bytes(token)
        
    f = _get_fernet()
    try:
        return f.decrypt(token).decode('utf-8')
    except Exception:
        return "[Error: Message could not be decrypted securely]"

from cryptography.fernet import Fernet

from app.config import settings

_fernet = Fernet(settings.FERNET_KEY.encode())


def encrypt_value(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    return _fernet.decrypt(encrypted.encode()).decode()

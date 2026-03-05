from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(sub: str, role: str, no_expiry: bool = False) -> str:
    if no_expiry and settings.MCP_TOKEN_NO_EXPIRY:
        # Non-expiring token for MCP access
        return jwt.encode({"sub": sub, "role": role, "type": "access", "no_expiry": True}, settings.JWT_SECRET, algorithm=ALGORITHM)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode({"sub": sub, "role": role, "exp": expire, "type": "access"}, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(sub: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": sub, "exp": expire, "type": "refresh"}, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str, verify_exp: bool = True) -> dict:
    try:
        if verify_exp:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        else:
            # Don't verify expiration for non-expiring tokens
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM], options={"verify_exp": False})
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e

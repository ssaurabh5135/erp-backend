# app/auth.py
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import hashlib
import os

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ---- Password utils (safe for any length) ----
def _truncate_password(password: str) -> str:
    """
    Convert to SHA256 bytes, truncate to 72 bytes, return hex string.
    """
    sha_bytes = hashlib.sha256(password.encode("utf-8")).digest()  # 32 bytes
    truncated = sha_bytes[:72]  # bcrypt max 72 bytes
    return truncated.hex()  # convert to hex string safe for bcrypt

def hash_password(password: str) -> str:
    pw = _truncate_password(password)
    return pwd_context.hash(pw)

def verify_password(password: str, hashed: str) -> bool:
    pw = _truncate_password(password)
    return pwd_context.verify(pw, hashed)

# ---- JWT utils ----
def create_access_token(subject: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    data = subject.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return {}

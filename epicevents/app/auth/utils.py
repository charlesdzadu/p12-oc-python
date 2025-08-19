import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from ..config import settings


ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def save_token(token: str):
    from ..config import TOKEN_FILE

    TOKEN_FILE.write_text(token)


def load_token() -> Optional[str]:
    from ..config import TOKEN_FILE

    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None


def remove_token():
    from ..config import TOKEN_FILE

    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

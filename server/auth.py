"""JWT helpers for issuing and verifying short-lived tokens."""

import os
import time
from typing import Any, Dict

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_SECONDS = int(os.getenv("TOKEN_EXPIRE_SECONDS", "300"))


def create_token(name: str, room_id: str, expires_in: int = TOKEN_EXPIRE_SECONDS) -> str:
    """Create a signed JWT for a given player name and room.

    Token claims:
    - sub: player name
    - room_id: allowed room to join
    - iat, exp
    """
    now = int(time.time())
    payload: Dict[str, Any] = {"sub": name, "room_id": room_id, "iat": now, "exp": now + expires_in}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT may return bytes in some versions — ensure string
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT. Raises jwt exceptions on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise
    except InvalidTokenError:
        raise

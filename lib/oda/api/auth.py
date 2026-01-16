"""
API Authentication Module - Resolves ODA-RISK-010
==================================================
Provides Bearer token authentication and role-based access control.

Environment Variables:
    ORION_API_SECRET: Secret key for token validation (required in production)
    ORION_AUTH_DISABLED: Set to "true" to disable auth (development only)
"""
import os
import hashlib
import hmac
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration
AUTH_DISABLED = os.getenv("ORION_AUTH_DISABLED", "false").lower() == "true"
API_SECRET = os.getenv("ORION_API_SECRET", "dev-secret-change-in-production")

security = HTTPBearer(auto_error=not AUTH_DISABLED)


def _validate_token(token: str) -> Optional[dict]:
    """Validate API token and return user info."""
    # Simple HMAC-based token: user_id:role:signature
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user_id, role, signature = parts
        expected_sig = hmac.new(
            API_SECRET.encode(), f"{user_id}:{role}".encode(), hashlib.sha256
        ).hexdigest()[:16]
        if hmac.compare_digest(signature, expected_sig):
            return {"user_id": user_id, "role": role}
    except Exception:
        pass
    return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Get authenticated user from token."""
    if AUTH_DISABLED:
        return {"user_id": "dev_user", "role": "admin"}

    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    user = _validate_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


def require_role(*allowed_roles: str):
    """Dependency that requires specific roles."""
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return role_checker


def generate_token(user_id: str, role: str = "user") -> str:
    """Generate API token for a user (utility function)."""
    signature = hmac.new(
        API_SECRET.encode(), f"{user_id}:{role}".encode(), hashlib.sha256
    ).hexdigest()[:16]
    return f"{user_id}:{role}:{signature}"

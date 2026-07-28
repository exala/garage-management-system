import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError

security = HTTPBearer(auto_error=False)

# Cache the JWKS client so we don't re-fetch on every request
_jwks_client: Optional[jwt.PyJWKClient] = None


def _get_jwks_client() -> jwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is not set")
        jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = jwt.PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def verify_supabase_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Validates a Supabase JWT.
    Supports both ES256 (newer Supabase projects) and HS256 (older projects)
    by fetching the public key from Supabase's JWKS endpoint.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["ES256", "HS256"],
            audience="authenticated",
        )
        return payload
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auth configuration error: {str(e)}",
        )

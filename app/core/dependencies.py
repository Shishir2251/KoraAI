from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
import uuid

bearer_scheme = HTTPBearer()


class CurrentUser:
    """Authenticated user context — org_id always from JWT, never from request."""
    def __init__(self, user_id: str, org_id: uuid.UUID, role: str):
        self.user_id = user_id
        self.org_id = org_id
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    payload = decode_token(credentials.credentials)

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    role = payload.get("role")

    if not user_id or not org_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return CurrentUser(user_id=user_id, org_id=uuid.UUID(org_id), role=role)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization
from sqlalchemy import select
import uuid

bearer_scheme = HTTPBearer()


class CurrentUser:
    """Represents the authenticated user with org context baked in."""
    def __init__(self, user: User, org_id: uuid.UUID, role: UserRole):
        self.user = user
        self.org_id = org_id  # Always from JWT — never from request
        self.role = role
        self.user_id = user.id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    Extract and validate user from JWT.
    CRITICAL: org_id is always taken from the token, never from request data.
    """
    payload = decode_token(credentials.credentials)

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    role = payload.get("role")

    if not user_id or not org_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(
        select(User).where(
            User.id == uuid.UUID(user_id),
            User.is_active == True,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    # Validate user still belongs to this org
    if str(user.org_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context mismatch",
        )

    return CurrentUser(
        user=user,
        org_id=uuid.UUID(org_id),
        role=UserRole(role),
    )


async def require_roles(*roles: UserRole):
    """Role-based access control dependency factory."""
    async def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in roles]}",
            )
        return current_user
    return checker


# Convenience dependencies
require_owner = Depends(require_roles(UserRole.OWNER))
require_owner_or_employee = Depends(
    require_roles(UserRole.OWNER, UserRole.EMPLOYEE)
)
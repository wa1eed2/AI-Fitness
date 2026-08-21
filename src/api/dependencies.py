from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from src.database.query_auth_database import (
    get_active_session_by_token,
    get_account_by_user_id
)


bearer_scheme = HTTPBearer(
    auto_error=False
)


def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    )
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    access_token = credentials.credentials

    session = get_active_session_by_token(
        access_token
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    account = get_account_by_user_id(
        session["user_id"]
    )

    if account is None or account["is_active"] != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is unavailable",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    return {
        "user_id": account["user_id"],
        "email": account["email"],
        "is_active": bool(
            account["is_active"]
        ),
        "created_at": account["created_at"],
        "access_token": access_token,
        "session_id": session["session_id"],
        "expires_at": session["expires_at"]
    }


def require_current_user(
    user_id: int,
    current_auth=Depends(
        get_current_auth
    )
):
    if current_auth["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this user's data is forbidden"
        )

    return current_auth
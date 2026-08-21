import sqlite3

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status
)

from src.api.dependencies import (
    get_current_auth
)

from src.api.schemas import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthSessionResponse,
    AuthTokenResponse,
    AuthUserResponse
)

from src.auth.security import (
    hash_password,
    verify_password
)

from src.database.query_auth_database import (
    create_account,
    create_auth_session,
    get_account_by_email,
    get_active_auth_sessions,
    revoke_all_auth_sessions,
    revoke_auth_session
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


def build_token_response(
    account,
    session
):
    return {
        "access_token": session["access_token"],
        "token_type": "bearer",
        "expires_at": session["expires_at"],
        "user_id": account["user_id"],
        "email": account["email"]
    }


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthTokenResponse
)
def register_endpoint(
    request: AuthRegisterRequest
):
    email = str(
        request.email
    )

    existing = get_account_by_email(
        email
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    password_hash = hash_password(
        request.password
    )

    try:
        created = create_account(
            email,
            password_hash
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    account = get_account_by_email(
        email
    )

    session = create_auth_session(
        created["user_id"]
    )

    return build_token_response(
        account,
        session
    )


@router.post(
    "/login",
    response_model=AuthTokenResponse
)
def login_endpoint(
    request: AuthLoginRequest
):
    email = str(
        request.email
    )

    account = get_account_by_email(
        email
    )

    if account is None or account["is_active"] != 1 or not verify_password(request.password, account["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    session = create_auth_session(
        account["user_id"]
    )

    return build_token_response(
        account,
        session
    )


@router.get(
    "/me",
    response_model=AuthUserResponse
)
def get_me_endpoint(
    current_auth=Depends(
        get_current_auth
    )
):
    return {
        "user_id": current_auth["user_id"],
        "email": current_auth["email"],
        "is_active": current_auth["is_active"],
        "created_at": current_auth["created_at"]
    }


@router.get(
    "/sessions",
    response_model=list[AuthSessionResponse]
)
def get_sessions_endpoint(
    current_auth=Depends(
        get_current_auth
    )
):
    return get_active_auth_sessions(
        current_auth["user_id"]
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT
)
def logout_endpoint(
    current_auth=Depends(
        get_current_auth
    )
):
    revoke_auth_session(
        current_auth["access_token"]
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT
)
def logout_all_endpoint(
    current_auth=Depends(
        get_current_auth
    )
):
    revoke_all_auth_sessions(
        current_auth["user_id"]
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
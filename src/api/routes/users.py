from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status
)

from src.api.dependencies import (
    require_current_user
)

from src.api.schemas import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse
)

from src.database.query_user_database import (
    create_user_profile,
    get_user_profile,
    update_user_profile,
    delete_user
)


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


def require_user_profile(
    user_id
):
    profile = get_user_profile(
        user_id
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    return dict(
        profile
    )


@router.post(
    "/{user_id}/profile",
    status_code=status.HTTP_201_CREATED,
    response_model=UserProfileResponse,
    dependencies=[
        Depends(
            require_current_user
        )
    ]
)
def create_user_profile_endpoint(
    user_id: int,
    profile: UserProfileCreate
):
    existing_profile = get_user_profile(
        user_id
    )

    if existing_profile is not None:
        raise HTTPException(
            status_code=409,
            detail="User profile already exists"
        )

    create_user_profile(
        user_id,
        profile.model_dump()
    )

    return require_user_profile(
        user_id
    )


@router.get(
    "/{user_id}/profile",
    response_model=UserProfileResponse,
    dependencies=[
        Depends(
            require_current_user
        )
    ]
)
def get_user_profile_endpoint(
    user_id: int
):
    return require_user_profile(
        user_id
    )


@router.patch(
    "/{user_id}/profile",
    response_model=UserProfileResponse,
    dependencies=[
        Depends(
            require_current_user
        )
    ]
)
def update_user_profile_endpoint(
    user_id: int,
    profile: UserProfileUpdate
):
    updates = profile.model_dump(
        exclude_unset=True
    )

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="At least one profile field must be updated"
        )

    require_user_profile(
        user_id
    )

    update_user_profile(
        user_id,
        updates
    )

    return require_user_profile(
        user_id
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_current_user
        )
    ]
)
def delete_user_endpoint(
    user_id: int
):
    delete_user(
        user_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
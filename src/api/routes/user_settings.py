from fastapi import APIRouter, HTTPException, Response, status

from src.api.schemas import (
    ExercisePreferenceCreate,
    ExercisePreferenceResponse,
    UserLimitationCreate,
    UserLimitationResponse,
    EquipmentAccessCreate,
    EquipmentAccessResponse
)

from src.database.query_user_database import (
    add_exercise_preference,
    get_user_exercise_preferences,
    remove_exercise_preference,
    add_user_limitation,
    get_user_limitations,
    remove_user_limitation,
    add_equipment_access,
    get_user_equipment_access,
    remove_equipment_access
)


ALLOWED_EXERCISE_PREFERENCES = {
    "Preferred",
    "Disliked"
}


router = APIRouter(
    prefix="/api/v1/users",
    tags=["User Settings"]
)


def normalize_rows(
    rows
):
    return [
        dict(row)
        for row in rows
    ]


def validate_exercise_preference(
    preference
):
    if preference not in ALLOWED_EXERCISE_PREFERENCES:
        raise ValueError(f"Invalid exercise preference: {preference}")


def find_exercise_preference(
    user_id,
    exercise_id
):
    preferences = normalize_rows(
        get_user_exercise_preferences(
            user_id
        )
    )

    for preference in preferences:
        if preference["exercise_id"] == exercise_id:
            return preference

    return None


def find_limitation(
    user_id,
    limitation_id
):
    limitations = normalize_rows(
        get_user_limitations(
            user_id
        )
    )

    for limitation in limitations:
        if limitation["limitation_id"] == limitation_id:
            return limitation

    return None


def find_equipment_access(
    user_id,
    equipment
):
    equipment_rows = normalize_rows(
        get_user_equipment_access(
            user_id
        )
    )

    for item in equipment_rows:
        if item["equipment"] == equipment:
            return item

    return None


@router.post(
    "/{user_id}/exercise-preferences",
    status_code=status.HTTP_201_CREATED,
    response_model=ExercisePreferenceResponse
)
def add_exercise_preference_endpoint(
    user_id: int,
    request: ExercisePreferenceCreate
):
    validate_exercise_preference(
        request.preference
    )

    add_exercise_preference(
        user_id,
        request.exercise_id,
        request.preference
    )

    preference = find_exercise_preference(
        user_id,
        request.exercise_id
    )

    if preference is None:
        raise HTTPException(
            status_code=500,
            detail="Exercise preference could not be retrieved after creation"
        )

    return preference


@router.get(
    "/{user_id}/exercise-preferences",
    response_model=list[ExercisePreferenceResponse]
)
def get_exercise_preferences_endpoint(
    user_id: int
):
    return normalize_rows(
        get_user_exercise_preferences(
            user_id
        )
    )


@router.delete(
    "/{user_id}/exercise-preferences/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_exercise_preference_endpoint(
    user_id: int,
    exercise_id: str
):
    existing = find_exercise_preference(
        user_id,
        exercise_id
    )

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Exercise preference not found"
        )

    remove_exercise_preference(
        user_id,
        exercise_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{user_id}/limitations",
    status_code=status.HTTP_201_CREATED,
    response_model=UserLimitationResponse
)
def add_user_limitation_endpoint(
    user_id: int,
    request: UserLimitationCreate
):
    add_user_limitation(
        user_id,
        request.body_area,
        request.limitation_type,
        request.notes
    )

    limitations = normalize_rows(
        get_user_limitations(
            user_id
        )
    )

    matching = [
        limitation
        for limitation in limitations
        if (
            limitation["body_area"] == request.body_area
            and limitation["limitation_type"] == request.limitation_type
            and limitation["notes"] == request.notes
        )
    ]

    if not matching:
        raise HTTPException(
            status_code=500,
            detail="User limitation could not be retrieved after creation"
        )

    matching.sort(
        key=lambda limitation: limitation["limitation_id"],
        reverse=True
    )

    return matching[0]


@router.get(
    "/{user_id}/limitations",
    response_model=list[UserLimitationResponse]
)
def get_user_limitations_endpoint(
    user_id: int
):
    return normalize_rows(
        get_user_limitations(
            user_id
        )
    )


@router.delete(
    "/{user_id}/limitations/{limitation_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_user_limitation_endpoint(
    user_id: int,
    limitation_id: int
):
    limitation = find_limitation(
        user_id,
        limitation_id
    )

    if limitation is None:
        raise HTTPException(
            status_code=404,
            detail="User limitation not found"
        )

    remove_user_limitation(
        limitation_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{user_id}/equipment",
    status_code=status.HTTP_201_CREATED,
    response_model=EquipmentAccessResponse
)
def add_equipment_access_endpoint(
    user_id: int,
    request: EquipmentAccessCreate
):
    add_equipment_access(
        user_id,
        request.equipment,
        request.access_status
    )

    equipment = find_equipment_access(
        user_id,
        request.equipment
    )

    if equipment is None:
        raise HTTPException(
            status_code=500,
            detail="Equipment access could not be retrieved after creation"
        )

    return equipment


@router.get(
    "/{user_id}/equipment",
    response_model=list[EquipmentAccessResponse]
)
def get_equipment_access_endpoint(
    user_id: int
):
    return normalize_rows(
        get_user_equipment_access(
            user_id
        )
    )


@router.delete(
    "/{user_id}/equipment/{equipment}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_equipment_access_endpoint(
    user_id: int,
    equipment: str
):
    existing = find_equipment_access(
        user_id,
        equipment
    )

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Equipment access not found"
        )

    remove_equipment_access(
        user_id,
        equipment
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
from fastapi import APIRouter, HTTPException, Query, Response, status

from src.api.schemas import (
    WorkoutPlanCreate,
    WorkoutSetCreate,
    WorkoutSetUpdate,
    WorkoutFinishRequest,
    WorkoutCancelRequest
)

from src.database.query_workout_log_database import (
    start_workout_from_plan,
    get_active_workout_session,
    get_workout_session,
    get_user_workout_history,
    get_workout_session_exercises,
    get_workout_set_logs,
    log_workout_set,
    update_workout_set,
    delete_workout_set,
    mark_session_exercise_complete,
    mark_session_exercise_incomplete,
    finish_workout_session,
    cancel_workout_session,
    delete_workout_session
)


router = APIRouter(
    prefix="/api/v1/users/{user_id}/workouts",
    tags=["Workouts"]
)


def normalize_payload(
    value
):
    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool
        )
    ):
        return value

    if isinstance(
        value,
        dict
    ):
        return {
            key: normalize_payload(
                item
            )
            for key, item in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple
        )
    ):
        return [
            normalize_payload(
                item
            )
            for item in value
        ]

    if hasattr(
        value,
        "keys"
    ):
        return {
            key: normalize_payload(
                value[key]
            )
            for key in value.keys()
        }

    return value


def require_owned_workout(
    user_id,
    workout_session_id
):
    workout = get_workout_session(
        workout_session_id
    )

    if workout is None:
        raise HTTPException(
            status_code=404,
            detail="Workout session not found"
        )

    workout = normalize_payload(
        workout
    )

    if workout["user_id"] != user_id:
        raise HTTPException(
            status_code=404,
            detail="Workout session not found"
        )

    return workout


def require_owned_session_exercise(
    user_id,
    workout_session_id,
    session_exercise_id
):
    require_owned_workout(
        user_id,
        workout_session_id
    )

    exercises = normalize_payload(
        get_workout_session_exercises(
            workout_session_id
        )
    )

    for exercise in exercises:
        if (
            exercise["session_exercise_id"]
            == session_exercise_id
        ):
            return exercise

    raise HTTPException(
        status_code=404,
        detail="Workout exercise not found"
    )


def require_owned_set_log(
    user_id,
    workout_session_id,
    session_exercise_id,
    set_log_id
):
    require_owned_session_exercise(
        user_id,
        workout_session_id,
        session_exercise_id
    )

    logs = normalize_payload(
        get_workout_set_logs(
            session_exercise_id
        )
    )

    for log in logs:
        if log["set_log_id"] == set_log_id:
            return log

    raise HTTPException(
        status_code=404,
        detail="Workout set log not found"
    )


def build_workout_details(
    user_id,
    workout_session_id
):
    workout = require_owned_workout(
        user_id,
        workout_session_id
    )

    exercises = normalize_payload(
        get_workout_session_exercises(
            workout_session_id
        )
    )

    exercise_details = []

    for exercise in exercises:
        details = dict(
            exercise
        )

        details[
            "sets"
        ] = normalize_payload(
            get_workout_set_logs(
                exercise["session_exercise_id"]
            )
        )

        exercise_details.append(
            details
        )

    return {
        "session": workout,
        "exercises": exercise_details
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
def start_workout_endpoint(
    user_id: int,
    request: WorkoutPlanCreate
):
    workout_plan = request.model_dump(
        exclude_none=True
    )

    workout_session_id = start_workout_from_plan(
        user_id,
        workout_plan
    )

    return build_workout_details(
        user_id,
        workout_session_id
    )


@router.get(
    "/active"
)
def get_active_workout_endpoint(
    user_id: int
):
    workout = get_active_workout_session(
        user_id
    )

    if workout is None:
        raise HTTPException(
            status_code=404,
            detail="No active workout session"
        )

    workout = normalize_payload(
        workout
    )

    return build_workout_details(
        user_id,
        workout["workout_session_id"]
    )


@router.get(
    ""
)
def get_workout_history_endpoint(
    user_id: int,
    limit: int | None = Query(
        default=None,
        ge=1
    ),
    workout_status: str | None = Query(
        default=None,
        alias="status"
    )
):
    history = get_user_workout_history(
        user_id,
        limit=limit,
        status=workout_status
    )

    return normalize_payload(
        history
    )


@router.get(
    "/{workout_session_id}"
)
def get_workout_details_endpoint(
    user_id: int,
    workout_session_id: int
):
    return build_workout_details(
        user_id,
        workout_session_id
    )


@router.post(
    "/{workout_session_id}/exercises/{session_exercise_id}/sets",
    status_code=status.HTTP_201_CREATED
)
def log_workout_set_endpoint(
    user_id: int,
    workout_session_id: int,
    session_exercise_id: int,
    request: WorkoutSetCreate
):
    require_owned_session_exercise(
        user_id,
        workout_session_id,
        session_exercise_id
    )

    log_workout_set(
        session_exercise_id,
        request.set_number,
        reps_completed=request.reps_completed,
        weight_kg=request.weight_kg,
        duration_seconds=request.duration_seconds,
        rir_actual=request.rir_actual,
        rpe_actual=request.rpe_actual
    )

    logs = normalize_payload(
        get_workout_set_logs(
            session_exercise_id
        )
    )

    for log in logs:
        if log["set_number"] == request.set_number:
            return log

    raise HTTPException(
        status_code=500,
        detail="Workout set could not be retrieved after creation"
    )


@router.patch(
    "/{workout_session_id}/exercises/{session_exercise_id}/sets/{set_log_id}"
)
def update_workout_set_endpoint(
    user_id: int,
    workout_session_id: int,
    session_exercise_id: int,
    set_log_id: int,
    request: WorkoutSetUpdate
):
    require_owned_set_log(
        user_id,
        workout_session_id,
        session_exercise_id,
        set_log_id
    )

    updates = request.model_dump(
        exclude_unset=True
    )

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="At least one workout set field must be updated"
        )

    update_workout_set(
        set_log_id,
        **updates
    )

    return require_owned_set_log(
        user_id,
        workout_session_id,
        session_exercise_id,
        set_log_id
    )


@router.delete(
    "/{workout_session_id}/exercises/{session_exercise_id}/sets/{set_log_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_workout_set_endpoint(
    user_id: int,
    workout_session_id: int,
    session_exercise_id: int,
    set_log_id: int
):
    require_owned_set_log(
        user_id,
        workout_session_id,
        session_exercise_id,
        set_log_id
    )

    delete_workout_set(
        set_log_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{workout_session_id}/exercises/{session_exercise_id}/complete"
)
def mark_workout_exercise_complete_endpoint(
    user_id: int,
    workout_session_id: int,
    session_exercise_id: int
):
    require_owned_session_exercise(
        user_id,
        workout_session_id,
        session_exercise_id
    )

    mark_session_exercise_complete(
        session_exercise_id
    )

    return require_owned_session_exercise(
        user_id,
        workout_session_id,
        session_exercise_id
    )


@router.post(
    "/{workout_session_id}/exercises/{session_exercise_id}/incomplete"
)
def mark_workout_exercise_incomplete_endpoint(
    user_id: int,
    workout_session_id: int,
    session_exercise_id: int
):
    require_owned_session_exercise(
        user_id,
        workout_session_id,
        session_exercise_id
    )

    mark_session_exercise_incomplete(
        session_exercise_id
    )

    return require_owned_session_exercise(
        user_id,
        workout_session_id,
        session_exercise_id
    )


@router.post(
    "/{workout_session_id}/finish"
)
def finish_workout_endpoint(
    user_id: int,
    workout_session_id: int,
    request: WorkoutFinishRequest | None = None
):
    require_owned_workout(
        user_id,
        workout_session_id
    )

    actual_duration_minutes = None
    notes = None

    if request is not None:
        actual_duration_minutes = request.actual_duration_minutes
        notes = request.notes

    finish_workout_session(
        workout_session_id,
        actual_duration_minutes=actual_duration_minutes,
        notes=notes
    )

    return build_workout_details(
        user_id,
        workout_session_id
    )


@router.post(
    "/{workout_session_id}/cancel"
)
def cancel_workout_endpoint(
    user_id: int,
    workout_session_id: int,
    request: WorkoutCancelRequest | None = None
):
    require_owned_workout(
        user_id,
        workout_session_id
    )

    notes = None

    if request is not None:
        notes = request.notes

    cancel_workout_session(
        workout_session_id,
        notes=notes
    )

    return build_workout_details(
        user_id,
        workout_session_id
    )


@router.delete(
    "/{workout_session_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_workout_endpoint(
    user_id: int,
    workout_session_id: int
):
    require_owned_workout(
        user_id,
        workout_session_id
    )

    delete_workout_session(
        workout_session_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
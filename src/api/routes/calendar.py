from fastapi import APIRouter, HTTPException, Response, status

from src.api.schemas import (
    ScheduledWorkoutCreate,
    ScheduledWorkoutReschedule,
    ScheduledWorkoutStatusUpdate,
    ScheduledWorkoutCompleteRequest
)

from src.database.query_progress_database import (
    schedule_workout_from_plan,
    get_calendar_workouts,
    get_scheduled_workout,
    reschedule_workout,
    update_scheduled_workout_status,
    complete_scheduled_workout,
    delete_scheduled_workout
)

from src.database.query_workout_log_database import (
    get_workout_session
)


router = APIRouter(
    prefix="/api/v1/users/{user_id}/calendar",
    tags=["Calendar"]
)


def normalize_payload(value):
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {key: normalize_payload(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [normalize_payload(item) for item in value]

    if hasattr(value, "keys"):
        return {key: normalize_payload(value[key]) for key in value.keys()}

    return value


def get_scheduled_workout_header(workout):
    if isinstance(workout, dict) and "scheduled_workout" in workout:
        return workout["scheduled_workout"]

    return workout


def require_owned_scheduled_workout(
    user_id,
    scheduled_workout_id
):
    workout = get_scheduled_workout(
        scheduled_workout_id
    )

    if workout is None:
        raise HTTPException(
            status_code=404,
            detail="Scheduled workout not found"
        )

    workout = normalize_payload(
        workout
    )

    header = get_scheduled_workout_header(
        workout
    )

    if header["user_id"] != user_id:
        raise HTTPException(
            status_code=404,
            detail="Scheduled workout not found"
        )

    return workout


def require_owned_workout_session(
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


def resolve_scheduled_workout_id(
    user_id,
    result
):
    result = normalize_payload(
        result
    )

    if isinstance(result, int):
        return result

    if isinstance(result, dict):
        if "scheduled_workout_id" in result:
            return result["scheduled_workout_id"]

        if (
            "scheduled_workout" in result
            and "scheduled_workout_id" in result["scheduled_workout"]
        ):
            return result["scheduled_workout"]["scheduled_workout_id"]

    workouts = normalize_payload(
        get_calendar_workouts(
            user_id
        )
    )

    if not workouts:
        raise HTTPException(
            status_code=500,
            detail="Scheduled workout could not be retrieved after creation"
        )

    newest = max(
        workouts,
        key=lambda workout: workout["scheduled_workout_id"]
    )

    return newest[
        "scheduled_workout_id"
    ]


@router.post(
    "/workouts",
    status_code=status.HTTP_201_CREATED
)
def schedule_workout_endpoint(
    user_id: int,
    request: ScheduledWorkoutCreate
):
    workout_plan = request.workout_plan.model_dump(
        exclude_none=True
    )

    result = schedule_workout_from_plan(
        user_id,
        request.scheduled_for,
        workout_plan,
        notes=request.notes
    )

    scheduled_workout_id = resolve_scheduled_workout_id(
        user_id,
        result
    )

    return require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )


@router.get("/workouts")
def get_calendar_workouts_endpoint(
    user_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    workout_status: str | None = None
):
    return normalize_payload(
        get_calendar_workouts(
            user_id,
            start_date=start_date,
            end_date=end_date,
            status=workout_status
        )
    )


@router.get("/workouts/{scheduled_workout_id}")
def get_scheduled_workout_endpoint(
    user_id: int,
    scheduled_workout_id: int
):
    return require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )


@router.patch("/workouts/{scheduled_workout_id}/reschedule")
def reschedule_workout_endpoint(
    user_id: int,
    scheduled_workout_id: int,
    request: ScheduledWorkoutReschedule
):
    require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )

    reschedule_workout(
        scheduled_workout_id,
        request.scheduled_for
    )

    return require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )


@router.patch("/workouts/{scheduled_workout_id}/status")
def update_scheduled_workout_status_endpoint(
    user_id: int,
    scheduled_workout_id: int,
    request: ScheduledWorkoutStatusUpdate
):
    require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )

    update_scheduled_workout_status(
        scheduled_workout_id,
        request.status
    )

    return require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )


@router.post("/workouts/{scheduled_workout_id}/complete")
def complete_scheduled_workout_endpoint(
    user_id: int,
    scheduled_workout_id: int,
    request: ScheduledWorkoutCompleteRequest
):
    require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )

    require_owned_workout_session(
        user_id,
        request.workout_session_id
    )

    complete_scheduled_workout(
        scheduled_workout_id,
        request.workout_session_id
    )

    return require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )


@router.delete(
    "/workouts/{scheduled_workout_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_scheduled_workout_endpoint(
    user_id: int,
    scheduled_workout_id: int
):
    require_owned_scheduled_workout(
        user_id,
        scheduled_workout_id
    )

    delete_scheduled_workout(
        scheduled_workout_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
from fastapi import APIRouter, HTTPException, Query, Response, status

from src.api.schemas import (
    ProgressEntryCreate,
    ProgressEntryUpdate,
    BodyMeasurementCreate,
    BodyMeasurementUpdate,
    ActivityLogCreate,
    ActivityLogUpdate,
    ProgressPhotoCreate,
    ProgressPhotoUpdate
)

from src.database.query_progress_database import (
    add_progress_entry,
    get_progress_history,
    add_body_measurement,
    get_body_measurement_history,
    add_activity_log,
    get_activity_history,
    add_progress_photo,
    get_progress_photo_history,
    delete_progress_photo
)

from src.database.query_progress_management import (
    update_progress_entry,
    delete_progress_entry,
    update_body_measurement,
    delete_body_measurement,
    update_activity_log,
    delete_activity_log,
    update_progress_photo_metadata
)


router = APIRouter(
    prefix="/api/v1/users/{user_id}",
    tags=["Progress"]
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


def newest_record(records, id_field):
    records = normalize_payload(records)

    if not records:
        raise HTTPException(status_code=500, detail="Created record could not be retrieved")

    return max(records, key=lambda row: row[id_field])


def find_owned_record(records, id_field, record_id, detail):
    records = normalize_payload(records)

    for record in records:
        if record[id_field] == record_id:
            return record

    raise HTTPException(status_code=404, detail=detail)


def require_progress_entry(user_id, progress_entry_id):
    return find_owned_record(
        get_progress_history(user_id),
        "progress_entry_id",
        progress_entry_id,
        "Progress entry not found"
    )


def require_body_measurement(user_id, body_measurement_id):
    return find_owned_record(
        get_body_measurement_history(user_id),
        "body_measurement_id",
        body_measurement_id,
        "Body measurement not found"
    )


def require_activity_log(user_id, activity_log_id):
    return find_owned_record(
        get_activity_history(user_id),
        "activity_log_id",
        activity_log_id,
        "Activity log not found"
    )


def require_progress_photo(user_id, progress_photo_id):
    return find_owned_record(
        get_progress_photo_history(user_id),
        "progress_photo_id",
        progress_photo_id,
        "Progress photo not found"
    )


@router.post(
    "/progress",
    status_code=status.HTTP_201_CREATED
)
def add_progress_entry_endpoint(
    user_id: int,
    request: ProgressEntryCreate
):
    add_progress_entry(
        user_id,
        weight_kg=request.weight_kg,
        body_fat_percentage=request.body_fat_percentage,
        notes=request.notes
    )

    return newest_record(
        get_progress_history(user_id),
        "progress_entry_id"
    )


@router.get("/progress")
def get_progress_history_endpoint(
    user_id: int,
    limit: int | None = Query(default=None, ge=1)
):
    return normalize_payload(
        get_progress_history(
            user_id,
            limit=limit
        )
    )


@router.patch("/progress/{progress_entry_id}")
def update_progress_entry_endpoint(
    user_id: int,
    progress_entry_id: int,
    request: ProgressEntryUpdate
):
    require_progress_entry(
        user_id,
        progress_entry_id
    )

    updates = request.model_dump(
        exclude_unset=True
    )

    if not updates:
        raise HTTPException(status_code=400, detail="At least one progress field must be updated")

    update_progress_entry(
        user_id,
        progress_entry_id,
        **updates
    )

    return require_progress_entry(
        user_id,
        progress_entry_id
    )


@router.delete(
    "/progress/{progress_entry_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_progress_entry_endpoint(
    user_id: int,
    progress_entry_id: int
):
    require_progress_entry(
        user_id,
        progress_entry_id
    )

    delete_progress_entry(
        user_id,
        progress_entry_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/measurements",
    status_code=status.HTTP_201_CREATED
)
def add_body_measurement_endpoint(
    user_id: int,
    request: BodyMeasurementCreate
):
    add_body_measurement(
        user_id,
        request.body_area,
        request.measurement_cm,
        request.notes
    )

    return newest_record(
        get_body_measurement_history(user_id),
        "body_measurement_id"
    )


@router.get("/measurements")
def get_body_measurements_endpoint(
    user_id: int,
    body_area: str | None = None,
    limit: int | None = Query(default=None, ge=1)
):
    return normalize_payload(
        get_body_measurement_history(
            user_id,
            body_area=body_area,
            limit=limit
        )
    )


@router.patch("/measurements/{body_measurement_id}")
def update_body_measurement_endpoint(
    user_id: int,
    body_measurement_id: int,
    request: BodyMeasurementUpdate
):
    require_body_measurement(
        user_id,
        body_measurement_id
    )

    updates = request.model_dump(
        exclude_unset=True
    )

    if not updates:
        raise HTTPException(status_code=400, detail="At least one measurement field must be updated")

    update_body_measurement(
        user_id,
        body_measurement_id,
        **updates
    )

    return require_body_measurement(
        user_id,
        body_measurement_id
    )


@router.delete(
    "/measurements/{body_measurement_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_body_measurement_endpoint(
    user_id: int,
    body_measurement_id: int
):
    require_body_measurement(
        user_id,
        body_measurement_id
    )

    delete_body_measurement(
        user_id,
        body_measurement_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/activities",
    status_code=status.HTTP_201_CREATED
)
def add_activity_endpoint(
    user_id: int,
    request: ActivityLogCreate
):
    add_activity_log(
        user_id,
        request.activity_type,
        duration_minutes=request.duration_minutes,
        distance_km=request.distance_km,
        steps=request.steps,
        average_speed_kmh=request.average_speed_kmh,
        estimated_calories=request.estimated_calories,
        notes=request.notes
    )

    return newest_record(
        get_activity_history(user_id),
        "activity_log_id"
    )


@router.get("/activities")
def get_activity_history_endpoint(
    user_id: int,
    activity_type: str | None = None,
    limit: int | None = Query(default=None, ge=1)
):
    return normalize_payload(
        get_activity_history(
            user_id,
            activity_type=activity_type,
            limit=limit
        )
    )


@router.patch("/activities/{activity_log_id}")
def update_activity_endpoint(
    user_id: int,
    activity_log_id: int,
    request: ActivityLogUpdate
):
    require_activity_log(
        user_id,
        activity_log_id
    )

    updates = request.model_dump(
        exclude_unset=True
    )

    if not updates:
        raise HTTPException(status_code=400, detail="At least one activity field must be updated")

    update_activity_log(
        user_id,
        activity_log_id,
        **updates
    )

    return require_activity_log(
        user_id,
        activity_log_id
    )


@router.delete(
    "/activities/{activity_log_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_activity_endpoint(
    user_id: int,
    activity_log_id: int
):
    require_activity_log(
        user_id,
        activity_log_id
    )

    delete_activity_log(
        user_id,
        activity_log_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/progress-photos",
    status_code=status.HTTP_201_CREATED
)
def add_progress_photo_endpoint(
    user_id: int,
    request: ProgressPhotoCreate
):
    add_progress_photo(
        user_id,
        request.file_path,
        request.view_type,
        request.is_private,
        request.notes
    )

    return newest_record(
        get_progress_photo_history(user_id),
        "progress_photo_id"
    )


@router.get("/progress-photos")
def get_progress_photos_endpoint(
    user_id: int,
    view_type: str | None = None,
    limit: int | None = Query(default=None, ge=1)
):
    return normalize_payload(
        get_progress_photo_history(
            user_id,
            view_type=view_type,
            limit=limit
        )
    )


@router.patch("/progress-photos/{progress_photo_id}")
def update_progress_photo_endpoint(
    user_id: int,
    progress_photo_id: int,
    request: ProgressPhotoUpdate
):
    require_progress_photo(
        user_id,
        progress_photo_id
    )

    updates = request.model_dump(
        exclude_unset=True
    )

    if not updates:
        raise HTTPException(status_code=400, detail="At least one photo metadata field must be updated")

    update_progress_photo_metadata(
        user_id,
        progress_photo_id,
        **updates
    )

    return require_progress_photo(
        user_id,
        progress_photo_id
    )


@router.delete(
    "/progress-photos/{progress_photo_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_progress_photo_endpoint(
    user_id: int,
    progress_photo_id: int
):
    require_progress_photo(
        user_id,
        progress_photo_id
    )

    delete_progress_photo(
        progress_photo_id
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
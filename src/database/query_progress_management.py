import sqlite3

from src.database.query_progress_database import (
    get_connection,
    is_number,
    ALLOWED_BODY_AREAS,
    ALLOWED_ACTIVITY_TYPES,
    ALLOWED_PHOTO_VIEW_TYPES
)


def validate_positive_integer(
    value,
    field_name
):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")


def validate_optional_notes(
    notes
):
    if notes is not None and not isinstance(notes, str):
        raise ValueError("Notes must be a string")


def get_owned_progress_entry(
    connection,
    user_id,
    progress_entry_id
):
    row = connection.execute(
        """
        SELECT *
        FROM progress_entries
        WHERE progress_entry_id = ?
          AND user_id = ?
        """,
        (
            progress_entry_id,
            user_id
        )
    ).fetchone()

    if row is None:
        raise ValueError("Progress entry not found")

    return row


def get_owned_body_measurement(
    connection,
    user_id,
    body_measurement_id
):
    row = connection.execute(
        """
        SELECT *
        FROM body_measurements
        WHERE body_measurement_id = ?
          AND user_id = ?
        """,
        (
            body_measurement_id,
            user_id
        )
    ).fetchone()

    if row is None:
        raise ValueError("Body measurement not found")

    return row


def get_owned_activity_log(
    connection,
    user_id,
    activity_log_id
):
    row = connection.execute(
        """
        SELECT *
        FROM activity_logs
        WHERE activity_log_id = ?
          AND user_id = ?
        """,
        (
            activity_log_id,
            user_id
        )
    ).fetchone()

    if row is None:
        raise ValueError("Activity log not found")

    return row


def get_owned_progress_photo(
    connection,
    user_id,
    progress_photo_id
):
    row = connection.execute(
        """
        SELECT *
        FROM progress_photos
        WHERE progress_photo_id = ?
          AND user_id = ?
        """,
        (
            progress_photo_id,
            user_id
        )
    ).fetchone()

    if row is None:
        raise ValueError("Progress photo not found")

    return row


def update_progress_entry(
    user_id,
    progress_entry_id,
    weight_kg=None,
    body_fat_percentage=None,
    notes=None
):
    validate_positive_integer(
        progress_entry_id,
        "Progress entry ID"
    )

    validate_optional_notes(
        notes
    )

    updates = []
    parameters = []

    if weight_kg is not None:
        if not is_number(weight_kg):
            raise ValueError("Weight must be a number")

        if weight_kg <= 0:
            raise ValueError("Weight must be greater than 0")

        updates.append(
            "weight_kg = ?"
        )

        parameters.append(
            weight_kg
        )

    if body_fat_percentage is not None:
        if not is_number(body_fat_percentage):
            raise ValueError("Body fat percentage must be a number")

        if (
            body_fat_percentage < 0
            or body_fat_percentage > 100
        ):
            raise ValueError("Body fat percentage must be between 0 and 100")

        updates.append(
            "body_fat_percentage = ?"
        )

        parameters.append(
            body_fat_percentage
        )

    if notes is not None:
        updates.append(
            "notes = ?"
        )

        parameters.append(
            notes
        )

    if not updates:
        raise ValueError("At least one progress field must be updated")

    connection = get_connection()

    try:
        get_owned_progress_entry(
            connection,
            user_id,
            progress_entry_id
        )

        parameters.extend(
            [
                progress_entry_id,
                user_id
            ]
        )

        connection.execute(
            f"""
            UPDATE progress_entries
            SET {", ".join(updates)}
            WHERE progress_entry_id = ?
              AND user_id = ?
            """,
            tuple(parameters)
        )

        connection.commit()

        updated = get_owned_progress_entry(
            connection,
            user_id,
            progress_entry_id
        )

        return dict(
            updated
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_progress_entry(
    user_id,
    progress_entry_id
):
    validate_positive_integer(
        progress_entry_id,
        "Progress entry ID"
    )

    connection = get_connection()

    try:
        get_owned_progress_entry(
            connection,
            user_id,
            progress_entry_id
        )

        connection.execute(
            """
            DELETE FROM progress_entries
            WHERE progress_entry_id = ?
              AND user_id = ?
            """,
            (
                progress_entry_id,
                user_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_body_measurement(
    user_id,
    body_measurement_id,
    body_area=None,
    measurement_cm=None,
    notes=None
):
    validate_positive_integer(
        body_measurement_id,
        "Body measurement ID"
    )

    validate_optional_notes(
        notes
    )

    updates = []
    parameters = []

    if body_area is not None:
        if body_area not in ALLOWED_BODY_AREAS:
            raise ValueError("Invalid body area")

        updates.append(
            "body_area = ?"
        )

        parameters.append(
            body_area
        )

    if measurement_cm is not None:
        if not is_number(measurement_cm):
            raise ValueError("Measurement must be a number")

        if measurement_cm <= 0:
            raise ValueError("Measurement must be greater than 0")

        updates.append(
            "measurement_cm = ?"
        )

        parameters.append(
            measurement_cm
        )

    if notes is not None:
        updates.append(
            "notes = ?"
        )

        parameters.append(
            notes
        )

    if not updates:
        raise ValueError("At least one body measurement field must be updated")

    connection = get_connection()

    try:
        get_owned_body_measurement(
            connection,
            user_id,
            body_measurement_id
        )

        parameters.extend(
            [
                body_measurement_id,
                user_id
            ]
        )

        connection.execute(
            f"""
            UPDATE body_measurements
            SET {", ".join(updates)}
            WHERE body_measurement_id = ?
              AND user_id = ?
            """,
            tuple(parameters)
        )

        connection.commit()

        updated = get_owned_body_measurement(
            connection,
            user_id,
            body_measurement_id
        )

        return dict(
            updated
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_body_measurement(
    user_id,
    body_measurement_id
):
    validate_positive_integer(
        body_measurement_id,
        "Body measurement ID"
    )

    connection = get_connection()

    try:
        get_owned_body_measurement(
            connection,
            user_id,
            body_measurement_id
        )

        connection.execute(
            """
            DELETE FROM body_measurements
            WHERE body_measurement_id = ?
              AND user_id = ?
            """,
            (
                body_measurement_id,
                user_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_activity_log(
    user_id,
    activity_log_id,
    activity_type=None,
    duration_minutes=None,
    distance_km=None,
    steps=None,
    average_speed_kmh=None,
    estimated_calories=None,
    notes=None
):
    validate_positive_integer(
        activity_log_id,
        "Activity log ID"
    )

    validate_optional_notes(
        notes
    )

    updates = []
    parameters = []

    if activity_type is not None:
        if activity_type not in ALLOWED_ACTIVITY_TYPES:
            raise ValueError("Invalid activity type")

        updates.append(
            "activity_type = ?"
        )

        parameters.append(
            activity_type
        )

    numeric_fields = [
        (
            "duration_minutes",
            duration_minutes,
            "Duration"
        ),
        (
            "distance_km",
            distance_km,
            "Distance"
        ),
        (
            "average_speed_kmh",
            average_speed_kmh,
            "Average speed"
        ),
        (
            "estimated_calories",
            estimated_calories,
            "Estimated calories"
        )
    ]

    for column_name, value, field_name in numeric_fields:
        if value is None:
            continue

        if not is_number(value):
            raise ValueError(f"{field_name} must be a number")

        if value < 0:
            raise ValueError(f"{field_name} cannot be negative")

        updates.append(
            f"{column_name} = ?"
        )

        parameters.append(
            value
        )

    if steps is not None:
        if isinstance(steps, bool) or not isinstance(steps, int):
            raise ValueError("Steps must be an integer")

        if steps < 0:
            raise ValueError("Steps cannot be negative")

        updates.append(
            "steps = ?"
        )

        parameters.append(
            steps
        )

    if notes is not None:
        updates.append(
            "notes = ?"
        )

        parameters.append(
            notes
        )

    if not updates:
        raise ValueError("At least one activity field must be updated")

    connection = get_connection()

    try:
        get_owned_activity_log(
            connection,
            user_id,
            activity_log_id
        )

        parameters.extend(
            [
                activity_log_id,
                user_id
            ]
        )

        connection.execute(
            f"""
            UPDATE activity_logs
            SET {", ".join(updates)}
            WHERE activity_log_id = ?
              AND user_id = ?
            """,
            tuple(parameters)
        )

        connection.commit()

        updated = get_owned_activity_log(
            connection,
            user_id,
            activity_log_id
        )

        return dict(
            updated
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_activity_log(
    user_id,
    activity_log_id
):
    validate_positive_integer(
        activity_log_id,
        "Activity log ID"
    )

    connection = get_connection()

    try:
        get_owned_activity_log(
            connection,
            user_id,
            activity_log_id
        )

        connection.execute(
            """
            DELETE FROM activity_logs
            WHERE activity_log_id = ?
              AND user_id = ?
            """,
            (
                activity_log_id,
                user_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_progress_photo_metadata(
    user_id,
    progress_photo_id,
    file_path=None,
    view_type=None,
    is_private=None,
    notes=None
):
    validate_positive_integer(
        progress_photo_id,
        "Progress photo ID"
    )

    validate_optional_notes(
        notes
    )

    updates = []
    parameters = []

    if file_path is not None:
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("File path must be a non-empty string")

        updates.append(
            "file_path = ?"
        )

        parameters.append(
            file_path.strip()
        )

    if view_type is not None:
        if view_type not in ALLOWED_PHOTO_VIEW_TYPES:
            raise ValueError("Invalid photo view type")

        updates.append(
            "view_type = ?"
        )

        parameters.append(
            view_type
        )

    if is_private is not None:
        if not isinstance(is_private, bool):
            raise ValueError("is_private must be a boolean")

        updates.append(
            "is_private = ?"
        )

        parameters.append(
            int(is_private)
        )

    if notes is not None:
        updates.append(
            "notes = ?"
        )

        parameters.append(
            notes
        )

    if not updates:
        raise ValueError("At least one progress photo field must be updated")

    connection = get_connection()

    try:
        get_owned_progress_photo(
            connection,
            user_id,
            progress_photo_id
        )

        parameters.extend(
            [
                progress_photo_id,
                user_id
            ]
        )

        connection.execute(
            f"""
            UPDATE progress_photos
            SET {", ".join(updates)}
            WHERE progress_photo_id = ?
              AND user_id = ?
            """,
            tuple(parameters)
        )

        connection.commit()

        updated = get_owned_progress_photo(
            connection,
            user_id,
            progress_photo_id
        )

        return dict(
            updated
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
import sqlite3

from datetime import date, datetime, timedelta

from src.database.setup_progress_database import DATABASE_PATH


ALLOWED_BODY_AREAS = {
    "Neck",
    "Shoulders",
    "Chest",
    "Waist",
    "Hips",
    "Left Arm",
    "Right Arm",
    "Left Forearm",
    "Right Forearm",
    "Left Thigh",
    "Right Thigh",
    "Left Calf",
    "Right Calf"
}


ALLOWED_ACTIVITY_TYPES = {
    "Walking",
    "Running",
    "Cycling",
    "Hiking",
    "Swimming",
    "Rowing",
    "Sports",
    "Other"
}


ALLOWED_PHOTO_VIEW_TYPES = {
    "Front",
    "Side",
    "Back",
    "Other"
}


ALLOWED_SCHEDULED_WORKOUT_STATUSES = {
    "Planned",
    "Completed",
    "Skipped",
    "Cancelled"
}


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def is_number(
    value
):
    return (
        isinstance(
            value,
            (int, float)
        )
        and not isinstance(
            value,
            bool
        )
    )


def validate_optional_non_negative_number(
    value,
    field_name
):
    if value is None:
        return

    if not is_number(value):
        raise ValueError(f"{field_name} must be a number")

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")


def validate_optional_positive_number(
    value,
    field_name
):
    if value is None:
        return

    if not is_number(value):
        raise ValueError(f"{field_name} must be a number")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")


def normalize_scheduled_datetime(
    value
):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("scheduled_for must be a non-empty string")

    try:
        parsed = datetime.fromisoformat(
            value.strip()
        )

    except ValueError:
        raise ValueError("scheduled_for must use ISO date/time format")

    if parsed.tzinfo is not None:
        raise ValueError("scheduled_for must not contain a timezone offset")

    return parsed.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def normalize_calendar_date(
    value,
    field_name
):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")

    try:
        return date.fromisoformat(
            value.strip()
        )

    except ValueError:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format")


def add_progress_entry(
    user_id,
    weight_kg=None,
    body_fat_percentage=None,
    notes=None
):
    validate_optional_positive_number(
        weight_kg,
        "Weight"
    )

    validate_optional_non_negative_number(
        body_fat_percentage,
        "Body fat percentage"
    )

    if (
        body_fat_percentage is not None
        and body_fat_percentage > 100
    ):
        raise ValueError("Body fat percentage cannot be greater than 100")

    if (
        weight_kg is None
        and body_fat_percentage is None
        and notes is None
    ):
        raise ValueError("Progress entry must contain at least one value")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO progress_entries (
                user_id,
                weight_kg,
                body_fat_percentage,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                weight_kg,
                body_fat_percentage,
                notes
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def add_body_measurement(
    user_id,
    body_area,
    measurement_cm,
    notes=None
):
    if body_area not in ALLOWED_BODY_AREAS:
        raise ValueError("Invalid body area")

    validate_optional_positive_number(
        measurement_cm,
        "Measurement"
    )

    if measurement_cm is None:
        raise ValueError("Measurement is required")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO body_measurements (
                user_id,
                body_area,
                measurement_cm,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                body_area,
                measurement_cm,
                notes
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def add_activity_log(
    user_id,
    activity_type,
    duration_minutes=None,
    distance_km=None,
    steps=None,
    average_speed_kmh=None,
    estimated_calories=None,
    notes=None
):
    if activity_type not in ALLOWED_ACTIVITY_TYPES:
        raise ValueError("Invalid activity type")

    validate_optional_non_negative_number(
        duration_minutes,
        "Duration"
    )

    validate_optional_non_negative_number(
        distance_km,
        "Distance"
    )

    validate_optional_non_negative_number(
        average_speed_kmh,
        "Average speed"
    )

    validate_optional_non_negative_number(
        estimated_calories,
        "Estimated calories"
    )

    if steps is not None:
        if isinstance(steps, bool) or not isinstance(steps, int):
            raise ValueError("Steps must be an integer")

        if steps < 0:
            raise ValueError("Steps cannot be negative")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO activity_logs (
                user_id,
                activity_type,
                duration_minutes,
                distance_km,
                steps,
                average_speed_kmh,
                estimated_calories,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                activity_type,
                duration_minutes,
                distance_km,
                steps,
                average_speed_kmh,
                estimated_calories,
                notes
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_progress_history(
    user_id,
    limit=None
):
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("Limit must be an integer")

        if limit <= 0:
            raise ValueError("Limit must be greater than 0")

    connection = get_connection()

    try:
        sql = """
            SELECT *
            FROM progress_entries
            WHERE user_id = ?
            ORDER BY
                recorded_at DESC,
                progress_entry_id DESC
        """

        parameters = [
            user_id
        ]

        if limit is not None:
            sql += " LIMIT ?"

            parameters.append(
                limit
            )

        rows = connection.execute(
            sql,
            tuple(parameters)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_body_measurement_history(
    user_id,
    body_area=None,
    limit=None
):
    if body_area is not None and body_area not in ALLOWED_BODY_AREAS:
        raise ValueError("Invalid body area")

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("Limit must be an integer")

        if limit <= 0:
            raise ValueError("Limit must be greater than 0")

    connection = get_connection()

    try:
        sql = """
            SELECT *
            FROM body_measurements
            WHERE user_id = ?
        """

        parameters = [
            user_id
        ]

        if body_area is not None:
            sql += " AND body_area = ?"

            parameters.append(
                body_area
            )

        sql += """
            ORDER BY
                recorded_at DESC,
                body_measurement_id DESC
        """

        if limit is not None:
            sql += " LIMIT ?"

            parameters.append(
                limit
            )

        rows = connection.execute(
            sql,
            tuple(parameters)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_activity_history(
    user_id,
    activity_type=None,
    limit=None
):
    if activity_type is not None and activity_type not in ALLOWED_ACTIVITY_TYPES:
        raise ValueError("Invalid activity type")

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("Limit must be an integer")

        if limit <= 0:
            raise ValueError("Limit must be greater than 0")

    connection = get_connection()

    try:
        sql = """
            SELECT *
            FROM activity_logs
            WHERE user_id = ?
        """

        parameters = [
            user_id
        ]

        if activity_type is not None:
            sql += " AND activity_type = ?"

            parameters.append(
                activity_type
            )

        sql += """
            ORDER BY
                started_at DESC,
                activity_log_id DESC
        """

        if limit is not None:
            sql += " LIMIT ?"

            parameters.append(
                limit
            )

        rows = connection.execute(
            sql,
            tuple(parameters)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def add_progress_photo(
    user_id,
    file_path,
    view_type,
    is_private=True,
    notes=None
):
    if not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("File path must be a non-empty string")

    if view_type not in ALLOWED_PHOTO_VIEW_TYPES:
        raise ValueError("Invalid photo view type")

    if not isinstance(is_private, bool):
        raise ValueError("is_private must be a boolean")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO progress_photos (
                user_id,
                file_path,
                view_type,
                is_private,
                notes
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                file_path.strip(),
                view_type,
                int(is_private),
                notes
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_progress_photo_history(
    user_id,
    view_type=None,
    limit=None
):
    if view_type is not None and view_type not in ALLOWED_PHOTO_VIEW_TYPES:
        raise ValueError("Invalid photo view type")

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("Limit must be an integer")

        if limit <= 0:
            raise ValueError("Limit must be greater than 0")

    connection = get_connection()

    try:
        sql = """
            SELECT *
            FROM progress_photos
            WHERE user_id = ?
        """

        parameters = [
            user_id
        ]

        if view_type is not None:
            sql += " AND view_type = ?"

            parameters.append(
                view_type
            )

        sql += """
            ORDER BY
                recorded_at DESC,
                progress_photo_id DESC
        """

        if limit is not None:
            sql += " LIMIT ?"

            parameters.append(
                limit
            )

        rows = connection.execute(
            sql,
            tuple(parameters)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def delete_progress_photo(
    progress_photo_id
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM progress_photos
            WHERE progress_photo_id = ?
            """,
            (
                progress_photo_id,
            )
        )

        if cursor.rowcount == 0:
            raise ValueError("Progress photo not found")

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def schedule_workout_from_plan(
    user_id,
    scheduled_for,
    workout_plan,
    notes=None
):
    normalized_scheduled_for = normalize_scheduled_datetime(
        scheduled_for
    )

    if not isinstance(workout_plan, dict):
        raise ValueError("Workout plan must be a dictionary")

    exercises = workout_plan.get(
        "exercises"
    )

    if not isinstance(exercises, list):
        raise ValueError("Workout plan must contain an exercise list")

    planned_duration = workout_plan.get(
        "session_duration_minutes"
    )

    if planned_duration is not None:
        if not is_number(planned_duration):
            raise ValueError("Planned duration must be a number")

        if planned_duration <= 0:
            raise ValueError("Planned duration must be greater than 0")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO scheduled_workouts (
                user_id,
                scheduled_for,
                primary_goal,
                planned_duration_minutes,
                notes
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                normalized_scheduled_for,
                workout_plan.get("primary_goal"),
                planned_duration,
                notes
            )
        )

        scheduled_workout_id = cursor.lastrowid

        for index, exercise in enumerate(
            exercises,
            start=1
        ):
            if not isinstance(exercise, dict):
                raise ValueError("Workout-plan exercise must be a dictionary")

            exercise_id = exercise.get(
                "exercise_id"
            )

            if not isinstance(exercise_id, str) or not exercise_id.strip():
                raise ValueError("Workout-plan exercise must contain an exercise ID")

            planned_sets = exercise.get(
                "sets"
            )

            if planned_sets is not None:
                if isinstance(planned_sets, bool) or not isinstance(planned_sets, int):
                    raise ValueError("Planned sets must be an integer")

                if planned_sets <= 0:
                    raise ValueError("Planned sets must be greater than 0")

            planned_rest_seconds = exercise.get(
                "rest_seconds"
            )

            validate_optional_non_negative_number(
                planned_rest_seconds,
                "Planned rest"
            )

            planned_exercise_duration = exercise.get(
                "duration_minutes"
            )

            validate_optional_positive_number(
                planned_exercise_duration,
                "Planned exercise duration"
            )

            connection.execute(
                """
                INSERT INTO scheduled_workout_exercises (
                    scheduled_workout_id,
                    exercise_id,
                    exercise_order,
                    planned_sets,
                    planned_reps,
                    planned_rest_seconds,
                    planned_duration_minutes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scheduled_workout_id,
                    exercise_id.strip(),
                    index,
                    planned_sets,
                    exercise.get("reps"),
                    planned_rest_seconds,
                    planned_exercise_duration
                )
            )

        connection.commit()

        return scheduled_workout_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_scheduled_workout(
    scheduled_workout_id
):
    connection = get_connection()

    try:
        workout = connection.execute(
            """
            SELECT *
            FROM scheduled_workouts
            WHERE scheduled_workout_id = ?
            """,
            (
                scheduled_workout_id,
            )
        ).fetchone()

        if workout is None:
            return None

        exercises = connection.execute(
            """
            SELECT *
            FROM scheduled_workout_exercises
            WHERE scheduled_workout_id = ?
            ORDER BY exercise_order
            """,
            (
                scheduled_workout_id,
            )
        ).fetchall()

        result = dict(
            workout
        )

        result["exercises"] = [
            dict(exercise)
            for exercise in exercises
        ]

        return result

    finally:
        connection.close()


def get_calendar_workouts(
    user_id,
    start_date=None,
    end_date=None,
    status=None
):
    parsed_start_date = None
    parsed_end_date = None

    if start_date is not None:
        parsed_start_date = normalize_calendar_date(
            start_date,
            "Start date"
        )

    if end_date is not None:
        parsed_end_date = normalize_calendar_date(
            end_date,
            "End date"
        )

    if (
        parsed_start_date is not None
        and parsed_end_date is not None
        and parsed_start_date > parsed_end_date
    ):
        raise ValueError("Start date cannot be after end date")

    if (
        status is not None
        and status not in ALLOWED_SCHEDULED_WORKOUT_STATUSES
    ):
        raise ValueError("Invalid scheduled workout status")

    connection = get_connection()

    try:
        sql = """
            SELECT *
            FROM scheduled_workouts
            WHERE user_id = ?
        """

        parameters = [
            user_id
        ]

        if parsed_start_date is not None:
            sql += " AND scheduled_for >= ?"

            parameters.append(
                f"{parsed_start_date.isoformat()} 00:00:00"
            )

        if parsed_end_date is not None:
            end_exclusive = (
                parsed_end_date
                + timedelta(
                    days=1
                )
            )

            sql += " AND scheduled_for < ?"

            parameters.append(
                f"{end_exclusive.isoformat()} 00:00:00"
            )

        if status is not None:
            sql += " AND status = ?"

            parameters.append(
                status
            )

        sql += """
            ORDER BY
                scheduled_for ASC,
                scheduled_workout_id ASC
        """

        rows = connection.execute(
            sql,
            tuple(parameters)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def reschedule_workout(
    scheduled_workout_id,
    scheduled_for
):
    normalized_scheduled_for = normalize_scheduled_datetime(
        scheduled_for
    )

    connection = get_connection()

    try:
        workout = connection.execute(
            """
            SELECT status
            FROM scheduled_workouts
            WHERE scheduled_workout_id = ?
            """,
            (
                scheduled_workout_id,
            )
        ).fetchone()

        if workout is None:
            raise ValueError("Scheduled workout not found")

        if workout["status"] != "Planned":
            raise ValueError("Only planned workouts can be rescheduled")

        connection.execute(
            """
            UPDATE scheduled_workouts
            SET scheduled_for = ?
            WHERE scheduled_workout_id = ?
            """,
            (
                normalized_scheduled_for,
                scheduled_workout_id
            )
        )

        connection.commit()

        return normalized_scheduled_for

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_scheduled_workout_status(
    scheduled_workout_id,
    status
):
    if status not in {
        "Skipped",
        "Cancelled"
    }:
        raise ValueError("Scheduled workout status can only be changed to Skipped or Cancelled")

    connection = get_connection()

    try:
        workout = connection.execute(
            """
            SELECT status
            FROM scheduled_workouts
            WHERE scheduled_workout_id = ?
            """,
            (
                scheduled_workout_id,
            )
        ).fetchone()

        if workout is None:
            raise ValueError("Scheduled workout not found")

        if workout["status"] != "Planned":
            raise ValueError("Only planned workouts can change status")

        connection.execute(
            """
            UPDATE scheduled_workouts
            SET status = ?
            WHERE scheduled_workout_id = ?
            """,
            (
                status,
                scheduled_workout_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def complete_scheduled_workout(
    scheduled_workout_id,
    workout_session_id
):
    connection = get_connection()

    try:
        scheduled_workout = connection.execute(
            """
            SELECT *
            FROM scheduled_workouts
            WHERE scheduled_workout_id = ?
            """,
            (
                scheduled_workout_id,
            )
        ).fetchone()

        if scheduled_workout is None:
            raise ValueError("Scheduled workout not found")

        if scheduled_workout["status"] != "Planned":
            raise ValueError("Only planned workouts can be completed")

        workout_session = connection.execute(
            """
            SELECT *
            FROM workout_sessions
            WHERE workout_session_id = ?
            """,
            (
                workout_session_id,
            )
        ).fetchone()

        if workout_session is None:
            raise ValueError("Workout session not found")

        if workout_session["user_id"] != scheduled_workout["user_id"]:
            raise ValueError("Workout session belongs to a different user")

        if workout_session["status"] != "Completed":
            raise ValueError("Workout session must be completed first")

        existing_link = connection.execute(
            """
            SELECT scheduled_workout_id
            FROM scheduled_workouts
            WHERE workout_session_id = ?
            """,
            (
                workout_session_id,
            )
        ).fetchone()

        if existing_link is not None:
            raise ValueError("Workout session is already linked to a scheduled workout")

        connection.execute(
            """
            UPDATE scheduled_workouts
            SET
                status = 'Completed',
                workout_session_id = ?
            WHERE scheduled_workout_id = ?
            """,
            (
                workout_session_id,
                scheduled_workout_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_scheduled_workout(
    scheduled_workout_id
):
    connection = get_connection()

    try:
        workout = connection.execute(
            """
            SELECT status
            FROM scheduled_workouts
            WHERE scheduled_workout_id = ?
            """,
            (
                scheduled_workout_id,
            )
        ).fetchone()

        if workout is None:
            raise ValueError("Scheduled workout not found")

        if workout["status"] == "Completed":
            raise ValueError("Completed scheduled workouts cannot be deleted")

        connection.execute(
            """
            DELETE FROM scheduled_workouts
            WHERE scheduled_workout_id = ?
            """,
            (
                scheduled_workout_id,
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
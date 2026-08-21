import sqlite3

from src.database.setup_workout_log_database import DATABASE_PATH


ALLOWED_WORKOUT_STATUSES = {
    "In Progress",
    "Completed",
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


def _is_number(value):
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


def _validate_optional_non_negative_number(
    value,
    field_name
):
    if value is None:
        return

    if not _is_number(value):
        raise ValueError(f"{field_name} must be a number")

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")


def _validate_positive_integer(
    value,
    field_name
):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")


def _validate_optional_positive_integer(
    value,
    field_name
):
    if value is None:
        return

    _validate_positive_integer(
        value,
        field_name
    )


def _validate_optional_non_negative_integer(
    value,
    field_name
):
    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")


def _validate_optional_rir(
    rir_actual
):
    if rir_actual is None:
        return

    if isinstance(rir_actual, bool) or not isinstance(rir_actual, int):
        raise ValueError("RIR must be an integer")

    if rir_actual < 0 or rir_actual > 10:
        raise ValueError("RIR must be between 0 and 10")


def _validate_optional_rpe(
    rpe_actual
):
    if rpe_actual is None:
        return

    if not _is_number(rpe_actual):
        raise ValueError("RPE must be a number")

    if rpe_actual < 0 or rpe_actual > 10:
        raise ValueError("RPE must be between 0 and 10")


def _get_workout_session_row(
    connection,
    workout_session_id
):
    return connection.execute(
        """
        SELECT *
        FROM workout_sessions
        WHERE workout_session_id = ?
        """,
        (
            workout_session_id,
        )
    ).fetchone()


def _get_session_exercise_row(
    connection,
    session_exercise_id
):
    return connection.execute(
        """
        SELECT
            workout_session_exercises.*,
            workout_sessions.status AS workout_status
        FROM workout_session_exercises
        JOIN workout_sessions
            ON workout_sessions.workout_session_id =
               workout_session_exercises.workout_session_id
        WHERE workout_session_exercises.session_exercise_id = ?
        """,
        (
            session_exercise_id,
        )
    ).fetchone()


def _ensure_workout_in_progress(
    connection,
    workout_session_id
):
    row = _get_workout_session_row(
        connection,
        workout_session_id
    )

    if row is None:
        raise ValueError("Workout session not found")

    if row["status"] != "In Progress":
        raise ValueError("Workout session is not in progress")

    return row


def _ensure_session_exercise_in_progress(
    connection,
    session_exercise_id
):
    row = _get_session_exercise_row(
        connection,
        session_exercise_id
    )

    if row is None:
        raise ValueError("Session exercise not found")

    if row["workout_status"] != "In Progress":
        raise ValueError("Workout session is not in progress")

    return row


def _ensure_no_active_workout(
    connection,
    user_id
):
    row = connection.execute(
        """
        SELECT workout_session_id
        FROM workout_sessions
        WHERE user_id = ?
          AND status = 'In Progress'
        LIMIT 1
        """,
        (
            user_id,
        )
    ).fetchone()

    if row is not None:
        raise ValueError("User already has an active workout session")


def start_workout_session(
    user_id,
    primary_goal=None,
    planned_duration_minutes=None,
    notes=None
):
    _validate_optional_non_negative_number(
        planned_duration_minutes,
        "Planned duration"
    )

    connection = get_connection()

    try:
        _ensure_no_active_workout(
            connection,
            user_id
        )

        cursor = connection.execute(
            """
            INSERT INTO workout_sessions (
                user_id,
                primary_goal,
                planned_duration_minutes,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                primary_goal,
                planned_duration_minutes,
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


def add_workout_session_exercise(
    workout_session_id,
    exercise_id,
    exercise_order,
    planned_sets=None,
    planned_reps=None,
    planned_rest_seconds=None,
    planned_duration_minutes=None
):
    _validate_positive_integer(
        exercise_order,
        "Exercise order"
    )

    _validate_optional_positive_integer(
        planned_sets,
        "Planned sets"
    )

    _validate_optional_non_negative_integer(
        planned_rest_seconds,
        "Planned rest seconds"
    )

    _validate_optional_non_negative_number(
        planned_duration_minutes,
        "Planned duration"
    )

    connection = get_connection()

    try:
        _ensure_workout_in_progress(
            connection,
            workout_session_id
        )

        exercise = connection.execute(
            """
            SELECT exercise_id
            FROM exercises
            WHERE exercise_id = ?
            """,
            (
                exercise_id,
            )
        ).fetchone()

        if exercise is None:
            raise ValueError("Exercise not found")

        cursor = connection.execute(
            """
            INSERT INTO workout_session_exercises (
                workout_session_id,
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
                workout_session_id,
                exercise_id,
                exercise_order,
                planned_sets,
                planned_reps,
                planned_rest_seconds,
                planned_duration_minutes
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def log_workout_set(
    session_exercise_id,
    set_number,
    reps_completed=None,
    weight_kg=None,
    duration_seconds=None,
    rir_actual=None,
    rpe_actual=None
):
    _validate_positive_integer(
        set_number,
        "Set number"
    )

    _validate_optional_non_negative_integer(
        reps_completed,
        "Reps completed"
    )

    _validate_optional_non_negative_number(
        weight_kg,
        "Weight"
    )

    _validate_optional_non_negative_number(
        duration_seconds,
        "Duration seconds"
    )

    _validate_optional_rir(
        rir_actual
    )

    _validate_optional_rpe(
        rpe_actual
    )

    connection = get_connection()

    try:
        _ensure_session_exercise_in_progress(
            connection,
            session_exercise_id
        )

        cursor = connection.execute(
            """
            INSERT INTO workout_set_logs (
                session_exercise_id,
                set_number,
                reps_completed,
                weight_kg,
                duration_seconds,
                rir_actual,
                rpe_actual
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_exercise_id,
                set_number,
                reps_completed,
                weight_kg,
                duration_seconds,
                rir_actual,
                rpe_actual
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_workout_set(
    set_log_id,
    reps_completed=None,
    weight_kg=None,
    duration_seconds=None,
    rir_actual=None,
    rpe_actual=None
):
    _validate_optional_non_negative_integer(
        reps_completed,
        "Reps completed"
    )

    _validate_optional_non_negative_number(
        weight_kg,
        "Weight"
    )

    _validate_optional_non_negative_number(
        duration_seconds,
        "Duration seconds"
    )

    _validate_optional_rir(
        rir_actual
    )

    _validate_optional_rpe(
        rpe_actual
    )

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                workout_set_logs.set_log_id,
                workout_sessions.status
            FROM workout_set_logs
            JOIN workout_session_exercises
                ON workout_session_exercises.session_exercise_id =
                   workout_set_logs.session_exercise_id
            JOIN workout_sessions
                ON workout_sessions.workout_session_id =
                   workout_session_exercises.workout_session_id
            WHERE workout_set_logs.set_log_id = ?
            """,
            (
                set_log_id,
            )
        ).fetchone()

        if row is None:
            raise ValueError("Workout set not found")

        if row["status"] != "In Progress":
            raise ValueError("Workout session is not in progress")

        connection.execute(
            """
            UPDATE workout_set_logs
            SET
                reps_completed = ?,
                weight_kg = ?,
                duration_seconds = ?,
                rir_actual = ?,
                rpe_actual = ?
            WHERE set_log_id = ?
            """,
            (
                reps_completed,
                weight_kg,
                duration_seconds,
                rir_actual,
                rpe_actual,
                set_log_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_workout_set(
    set_log_id
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                workout_set_logs.set_log_id,
                workout_sessions.status
            FROM workout_set_logs
            JOIN workout_session_exercises
                ON workout_session_exercises.session_exercise_id =
                   workout_set_logs.session_exercise_id
            JOIN workout_sessions
                ON workout_sessions.workout_session_id =
                   workout_session_exercises.workout_session_id
            WHERE workout_set_logs.set_log_id = ?
            """,
            (
                set_log_id,
            )
        ).fetchone()

        if row is None:
            raise ValueError("Workout set not found")

        if row["status"] != "In Progress":
            raise ValueError("Workout session is not in progress")

        connection.execute(
            """
            DELETE FROM workout_set_logs
            WHERE set_log_id = ?
            """,
            (
                set_log_id,
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def mark_session_exercise_complete(
    session_exercise_id
):
    connection = get_connection()

    try:
        _ensure_session_exercise_in_progress(
            connection,
            session_exercise_id
        )

        connection.execute(
            """
            UPDATE workout_session_exercises
            SET completed = 1
            WHERE session_exercise_id = ?
            """,
            (
                session_exercise_id,
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def mark_session_exercise_incomplete(
    session_exercise_id
):
    connection = get_connection()

    try:
        _ensure_session_exercise_in_progress(
            connection,
            session_exercise_id
        )

        connection.execute(
            """
            UPDATE workout_session_exercises
            SET completed = 0
            WHERE session_exercise_id = ?
            """,
            (
                session_exercise_id,
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def finish_workout_session(
    workout_session_id,
    actual_duration_minutes=None,
    notes=None
):
    _validate_optional_non_negative_number(
        actual_duration_minutes,
        "Actual duration"
    )

    connection = get_connection()

    try:
        _ensure_workout_in_progress(
            connection,
            workout_session_id
        )

        connection.execute(
            """
            UPDATE workout_sessions
            SET
                status = 'Completed',
                completed_at = CURRENT_TIMESTAMP,
                actual_duration_minutes = ?,
                notes = ?
            WHERE workout_session_id = ?
            """,
            (
                actual_duration_minutes,
                notes,
                workout_session_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def cancel_workout_session(
    workout_session_id,
    notes=None
):
    connection = get_connection()

    try:
        _ensure_workout_in_progress(
            connection,
            workout_session_id
        )

        connection.execute(
            """
            UPDATE workout_sessions
            SET
                status = 'Cancelled',
                completed_at = CURRENT_TIMESTAMP,
                notes = ?
            WHERE workout_session_id = ?
            """,
            (
                notes,
                workout_session_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_workout_session(
    workout_session_id
):
    connection = get_connection()

    try:
        row = _get_workout_session_row(
            connection,
            workout_session_id
        )

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def get_workout_session_exercises(
    workout_session_id
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                workout_session_exercises.*,
                exercises.name AS exercise_name,
                exercises.category AS category,
                exercises.primary_muscle AS primary_muscle
            FROM workout_session_exercises
            JOIN exercises
                ON exercises.exercise_id =
                   workout_session_exercises.exercise_id
            WHERE workout_session_exercises.workout_session_id = ?
            ORDER BY workout_session_exercises.exercise_order
            """,
            (
                workout_session_id,
            )
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_workout_set_logs(
    session_exercise_id
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM workout_set_logs
            WHERE session_exercise_id = ?
            ORDER BY set_number
            """,
            (
                session_exercise_id,
            )
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_workout_session_details(
    workout_session_id
):
    session = get_workout_session(
        workout_session_id
    )

    if session is None:
        return None

    exercises = get_workout_session_exercises(
        workout_session_id
    )

    for exercise in exercises:
        exercise["sets"] = get_workout_set_logs(
            exercise["session_exercise_id"]
        )

    session["exercises"] = exercises

    return session


def get_user_workout_history(
    user_id,
    limit=None,
    status=None
):
    if limit is not None:
        _validate_positive_integer(
            limit,
            "Limit"
        )

    if status is not None and status not in ALLOWED_WORKOUT_STATUSES:
        raise ValueError("Invalid workout status")

    connection = get_connection()

    try:
        sql = """
            SELECT *
            FROM workout_sessions
            WHERE user_id = ?
        """

        parameters = [
            user_id
        ]

        if status is not None:
            sql += " AND status = ?"

            parameters.append(
                status
            )

        sql += """
            ORDER BY
                started_at DESC,
                workout_session_id DESC
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


def get_active_workout_session(
    user_id
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM workout_sessions
            WHERE user_id = ?
              AND status = 'In Progress'
            ORDER BY workout_session_id DESC
            LIMIT 1
            """,
            (
                user_id,
            )
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def get_workout_progress(
    workout_session_id
):
    session = get_workout_session(
        workout_session_id
    )

    if session is None:
        raise ValueError("Workout session not found")

    connection = get_connection()

    try:
        total_exercises = connection.execute(
            """
            SELECT COUNT(*)
            FROM workout_session_exercises
            WHERE workout_session_id = ?
            """,
            (
                workout_session_id,
            )
        ).fetchone()[0]

        completed_exercises = connection.execute(
            """
            SELECT COUNT(*)
            FROM workout_session_exercises
            WHERE workout_session_id = ?
              AND completed = 1
            """,
            (
                workout_session_id,
            )
        ).fetchone()[0]

        logged_sets = connection.execute(
            """
            SELECT COUNT(*)
            FROM workout_set_logs
            JOIN workout_session_exercises
                ON workout_session_exercises.session_exercise_id =
                   workout_set_logs.session_exercise_id
            WHERE workout_session_exercises.workout_session_id = ?
            """,
            (
                workout_session_id,
            )
        ).fetchone()[0]

        if total_exercises == 0:
            completion_percentage = 0.0

        else:
            completion_percentage = round(
                (
                    completed_exercises
                    / total_exercises
                ) * 100,
                2
            )

        return {
            "workout_session_id": workout_session_id,
            "total_exercises": total_exercises,
            "completed_exercises": completed_exercises,
            "logged_sets": logged_sets,
            "completion_percentage": completion_percentage
        }

    finally:
        connection.close()


def delete_workout_session(
    workout_session_id
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM workout_sessions
            WHERE workout_session_id = ?
            """,
            (
                workout_session_id,
            )
        )

        if cursor.rowcount == 0:
            raise ValueError("Workout session not found")

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def start_workout_from_plan(
    user_id,
    workout_plan
):
    if not isinstance(workout_plan, dict):
        raise ValueError("Workout plan must be a dictionary")

    exercises = workout_plan.get(
        "exercises"
    )

    if not isinstance(exercises, list):
        raise ValueError("Workout plan exercises must be a list")

    planned_duration_minutes = workout_plan.get(
        "session_duration_minutes"
    )

    _validate_optional_non_negative_number(
        planned_duration_minutes,
        "Planned duration"
    )

    connection = get_connection()

    try:
        _ensure_no_active_workout(
            connection,
            user_id
        )

        cursor = connection.execute(
            """
            INSERT INTO workout_sessions (
                user_id,
                primary_goal,
                planned_duration_minutes
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                workout_plan.get(
                    "primary_goal"
                ),
                planned_duration_minutes
            )
        )

        workout_session_id = cursor.lastrowid

        for index, exercise in enumerate(
            exercises,
            start=1
        ):
            if not isinstance(exercise, dict):
                raise ValueError("Each workout exercise must be a dictionary")

            exercise_id = exercise.get(
                "exercise_id"
            )

            exercise_order = exercise.get(
                "order",
                index
            )

            planned_sets = exercise.get(
                "sets"
            )

            planned_reps = exercise.get(
                "reps"
            )

            planned_rest_seconds = exercise.get(
                "rest_seconds"
            )

            exercise_duration_minutes = exercise.get(
                "duration_minutes"
            )

            _validate_positive_integer(
                exercise_order,
                "Exercise order"
            )

            _validate_optional_positive_integer(
                planned_sets,
                "Planned sets"
            )

            _validate_optional_non_negative_integer(
                planned_rest_seconds,
                "Planned rest seconds"
            )

            _validate_optional_non_negative_number(
                exercise_duration_minutes,
                "Planned duration"
            )

            existing_exercise = connection.execute(
                """
                SELECT exercise_id
                FROM exercises
                WHERE exercise_id = ?
                """,
                (
                    exercise_id,
                )
            ).fetchone()

            if existing_exercise is None:
                raise ValueError("Exercise not found")

            connection.execute(
                """
                INSERT INTO workout_session_exercises (
                    workout_session_id,
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
                    workout_session_id,
                    exercise_id,
                    exercise_order,
                    planned_sets,
                    planned_reps,
                    planned_rest_seconds,
                    exercise_duration_minutes
                )
            )

        connection.commit()

        return workout_session_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
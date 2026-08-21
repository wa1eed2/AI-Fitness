from src.database.query_workout_log_database import (
    get_connection
)


def validate_exercise_id(
    exercise_id
):
    if not isinstance(exercise_id, str) or not exercise_id.strip():
        raise ValueError("Exercise ID must be a non-empty string")

    return exercise_id.strip()


def get_exercise_metadata(
    exercise_id
):
    normalized_exercise_id = validate_exercise_id(
        exercise_id
    )

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                exercise_id,
                name,
                primary_muscle
            FROM exercises
            WHERE exercise_id = ?
            """,
            (
                normalized_exercise_id,
            )
        ).fetchone()

        if row is None:
            raise ValueError("Exercise not found")

        return dict(
            row
        )

    finally:
        connection.close()


def get_exercise_workout_history(
    user_id,
    exercise_id
):
    metadata = get_exercise_metadata(
        exercise_id
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                ws.workout_session_id,
                ws.started_at,
                ws.completed_at,
                COUNT(
                    DISTINCT wse.session_exercise_id
                ) AS exercise_occurrence_count,
                COUNT(
                    wsl.set_log_id
                ) AS performance_log_count,
                COALESCE(
                    SUM(
                        CASE
                            WHEN wsl.reps_completed IS NOT NULL
                            THEN wsl.reps_completed
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_reps,
                COALESCE(
                    SUM(
                        CASE
                            WHEN wsl.reps_completed IS NOT NULL
                             AND wsl.weight_kg IS NOT NULL
                            THEN wsl.reps_completed * wsl.weight_kg
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_volume_kg,
                MAX(
                    wsl.weight_kg
                ) AS max_weight_kg,
                MAX(
                    wsl.reps_completed
                ) AS max_reps_completed,
                MAX(
                    CASE
                        WHEN wsl.reps_completed IS NOT NULL
                         AND wsl.weight_kg IS NOT NULL
                        THEN wsl.reps_completed * wsl.weight_kg
                        ELSE NULL
                    END
                ) AS max_set_volume_kg
            FROM workout_sessions AS ws
            JOIN workout_session_exercises AS wse
                ON wse.workout_session_id = ws.workout_session_id
            LEFT JOIN workout_set_logs AS wsl
                ON wsl.session_exercise_id = wse.session_exercise_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
              AND wse.exercise_id = ?
            GROUP BY
                ws.workout_session_id,
                ws.started_at,
                ws.completed_at
            ORDER BY
                ws.started_at ASC,
                ws.workout_session_id ASC
            """,
            (
                user_id,
                metadata["exercise_id"]
            )
        ).fetchall()

        return [
            {
                "workout_session_id": row["workout_session_id"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "exercise_occurrence_count": row["exercise_occurrence_count"],
                "performance_log_count": row["performance_log_count"],
                "total_reps": row["total_reps"],
                "total_volume_kg": round(
                    row["total_volume_kg"],
                    2
                ),
                "max_weight_kg": row["max_weight_kg"],
                "max_reps_completed": row["max_reps_completed"],
                "max_set_volume_kg": (
                    round(
                        row["max_set_volume_kg"],
                        2
                    )
                    if row["max_set_volume_kg"] is not None
                    else None
                )
            }
            for row in rows
        ]

    finally:
        connection.close()


def calculate_optional_change(
    latest_value,
    earliest_value
):
    if (
        latest_value is None
        or earliest_value is None
    ):
        return None

    return round(
        latest_value
        - earliest_value,
        2
    )


def get_exercise_progression(
    user_id,
    exercise_id
):
    metadata = get_exercise_metadata(
        exercise_id
    )

    workouts = get_exercise_workout_history(
        user_id,
        metadata["exercise_id"]
    )

    if not workouts:
        return {
            "exercise_id": metadata["exercise_id"],
            "name": metadata["name"],
            "primary_muscle": metadata["primary_muscle"],
            "workout_count": 0,
            "first_started_at": None,
            "latest_started_at": None,
            "first_max_weight_kg": None,
            "latest_max_weight_kg": None,
            "max_weight_change_kg": None,
            "first_total_volume_kg": None,
            "latest_total_volume_kg": None,
            "volume_change_kg": None,
            "all_time_max_weight_kg": None,
            "all_time_max_reps_completed": None,
            "all_time_max_set_volume_kg": None,
            "workouts": []
        }

    first_workout = workouts[0]
    latest_workout = workouts[-1]

    weight_values = [
        workout["max_weight_kg"]
        for workout in workouts
        if workout["max_weight_kg"] is not None
    ]

    rep_values = [
        workout["max_reps_completed"]
        for workout in workouts
        if workout["max_reps_completed"] is not None
    ]

    set_volume_values = [
        workout["max_set_volume_kg"]
        for workout in workouts
        if workout["max_set_volume_kg"] is not None
    ]

    return {
        "exercise_id": metadata["exercise_id"],
        "name": metadata["name"],
        "primary_muscle": metadata["primary_muscle"],
        "workout_count": len(workouts),
        "first_started_at": first_workout["started_at"],
        "latest_started_at": latest_workout["started_at"],
        "first_max_weight_kg": first_workout["max_weight_kg"],
        "latest_max_weight_kg": latest_workout["max_weight_kg"],
        "max_weight_change_kg": calculate_optional_change(
            latest_workout["max_weight_kg"],
            first_workout["max_weight_kg"]
        ),
        "first_total_volume_kg": first_workout["total_volume_kg"],
        "latest_total_volume_kg": latest_workout["total_volume_kg"],
        "volume_change_kg": round(
            latest_workout["total_volume_kg"]
            - first_workout["total_volume_kg"],
            2
        ),
        "all_time_max_weight_kg": (
            max(weight_values)
            if weight_values
            else None
        ),
        "all_time_max_reps_completed": (
            max(rep_values)
            if rep_values
            else None
        ),
        "all_time_max_set_volume_kg": (
            max(set_volume_values)
            if set_volume_values
            else None
        ),
        "workouts": workouts
    }


def get_personal_record_history(
    user_id,
    exercise_id
):
    progression = get_exercise_progression(
        user_id,
        exercise_id
    )

    best_values = {
        "max_weight_kg": None,
        "max_reps_completed": None,
        "max_set_volume_kg": None
    }

    events = []

    for workout in progression["workouts"]:
        metrics = [
            (
                "max_weight_kg",
                workout["max_weight_kg"]
            ),
            (
                "max_reps_completed",
                workout["max_reps_completed"]
            ),
            (
                "max_set_volume_kg",
                workout["max_set_volume_kg"]
            )
        ]

        for metric_name, value in metrics:
            if value is None:
                continue

            previous_record = best_values[
                metric_name
            ]

            if (
                previous_record is None
                or value > previous_record
            ):
                improvement = None

                if previous_record is not None:
                    improvement = round(
                        value
                        - previous_record,
                        2
                    )

                events.append(
                    {
                        "exercise_id": progression["exercise_id"],
                        "name": progression["name"],
                        "metric": metric_name,
                        "value": value,
                        "previous_record": previous_record,
                        "improvement": improvement,
                        "workout_session_id": workout["workout_session_id"],
                        "started_at": workout["started_at"]
                    }
                )

                best_values[
                    metric_name
                ] = value

    return events


def get_exercise_progression_overview(
    user_id
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT DISTINCT
                e.exercise_id
            FROM workout_session_exercises AS wse
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            JOIN exercises AS e
                ON e.exercise_id = wse.exercise_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            ORDER BY
                e.exercise_id ASC
            """,
            (
                user_id,
            )
        ).fetchall()

    finally:
        connection.close()

    result = []

    for row in rows:
        progression = get_exercise_progression(
            user_id,
            row["exercise_id"]
        )

        result.append(
            {
                "exercise_id": progression["exercise_id"],
                "name": progression["name"],
                "primary_muscle": progression["primary_muscle"],
                "workout_count": progression["workout_count"],
                "first_started_at": progression["first_started_at"],
                "latest_started_at": progression["latest_started_at"],
                "latest_max_weight_kg": progression["latest_max_weight_kg"],
                "max_weight_change_kg": progression["max_weight_change_kg"],
                "latest_total_volume_kg": progression["latest_total_volume_kg"],
                "volume_change_kg": progression["volume_change_kg"],
                "all_time_max_weight_kg": progression["all_time_max_weight_kg"],
                "all_time_max_reps_completed": progression["all_time_max_reps_completed"],
                "all_time_max_set_volume_kg": progression["all_time_max_set_volume_kg"]
            }
        )

    return result


def get_training_data_quality_analytics(
    user_id
):
    connection = get_connection()

    try:
        completed_workout_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM workout_sessions
            WHERE user_id = ?
              AND status = 'Completed'
            """,
            (
                user_id,
            )
        ).fetchone()["count"]

        completed_without_exercises = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM workout_sessions AS ws
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
              AND NOT EXISTS (
                    SELECT 1
                    FROM workout_session_exercises AS wse
                    WHERE wse.workout_session_id = ws.workout_session_id
              )
            """,
            (
                user_id,
            )
        ).fetchone()["count"]

        exercise_occurrence_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM workout_session_exercises AS wse
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            """,
            (
                user_id,
            )
        ).fetchone()["count"]

        occurrences_without_logs = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM workout_session_exercises AS wse
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
              AND NOT EXISTS (
                    SELECT 1
                    FROM workout_set_logs AS wsl
                    WHERE wsl.session_exercise_id = wse.session_exercise_id
              )
            """,
            (
                user_id,
            )
        ).fetchone()["count"]

        log_counts = connection.execute(
            """
            SELECT
                COUNT(wsl.set_log_id) AS performance_log_count,
                SUM(
                    CASE
                        WHEN wsl.reps_completed IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS rep_log_count,
                SUM(
                    CASE
                        WHEN wsl.weight_kg IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS weight_log_count,
                SUM(
                    CASE
                        WHEN wsl.duration_seconds IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS duration_log_count,
                SUM(
                    CASE
                        WHEN wsl.reps_completed IS NOT NULL
                         AND wsl.weight_kg IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS weighted_rep_log_count
            FROM workout_set_logs AS wsl
            JOIN workout_session_exercises AS wse
                ON wse.session_exercise_id = wsl.session_exercise_id
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            """,
            (
                user_id,
            )
        ).fetchone()

        occurrences_with_logs = (
            exercise_occurrence_count
            - occurrences_without_logs
        )

        coverage_percentage = 0.0

        if exercise_occurrence_count > 0:
            coverage_percentage = round(
                occurrences_with_logs
                / exercise_occurrence_count
                * 100,
                2
            )

        return {
            "completed_workout_count": completed_workout_count,
            "completed_workout_without_exercises_count": completed_without_exercises,
            "exercise_occurrence_count": exercise_occurrence_count,
            "exercise_occurrence_with_logs_count": occurrences_with_logs,
            "exercise_occurrence_without_logs_count": occurrences_without_logs,
            "exercise_log_coverage_percentage": coverage_percentage,
            "performance_log_count": log_counts["performance_log_count"] or 0,
            "rep_log_count": log_counts["rep_log_count"] or 0,
            "weight_log_count": log_counts["weight_log_count"] or 0,
            "duration_log_count": log_counts["duration_log_count"] or 0,
            "weighted_rep_log_count": log_counts["weighted_rep_log_count"] or 0
        }

    finally:
        connection.close()


def get_progression_analytics_overview(
    user_id
):
    return {
        "exercise_progression": get_exercise_progression_overview(
            user_id
        ),
        "data_quality": get_training_data_quality_analytics(
            user_id
        )
    }
from src.database.query_workout_log_database import (
    get_connection
)


def calculate_weighted_volume(
    reps_completed,
    weight_kg
):
    if reps_completed is None or weight_kg is None:
        return 0.0

    return round(
        reps_completed * weight_kg,
        2
    )


def get_training_volume_analytics(
    user_id
):
    connection = get_connection()

    try:
        workout_row = connection.execute(
            """
            SELECT COUNT(*) AS completed_workout_count
            FROM workout_sessions
            WHERE user_id = ?
              AND status = 'Completed'
            """,
            (
                user_id,
            )
        ).fetchone()

        exercise_row = connection.execute(
            """
            SELECT COUNT(*) AS exercise_occurrence_count
            FROM workout_session_exercises AS wse
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            """,
            (
                user_id,
            )
        ).fetchone()

        set_rows = connection.execute(
            """
            SELECT
                wsl.reps_completed,
                wsl.weight_kg
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
        ).fetchall()

        completed_workout_count = workout_row[
            "completed_workout_count"
        ]

        exercise_occurrence_count = exercise_row[
            "exercise_occurrence_count"
        ]

        performance_log_count = len(
            set_rows
        )

        rep_set_count = sum(
            1
            for row in set_rows
            if row["reps_completed"] is not None
        )

        weighted_set_count = sum(
            1
            for row in set_rows
            if (
                row["reps_completed"] is not None
                and row["weight_kg"] is not None
            )
        )

        total_reps = sum(
            row["reps_completed"] or 0
            for row in set_rows
        )

        total_volume_kg = round(
            sum(
                calculate_weighted_volume(
                    row["reps_completed"],
                    row["weight_kg"]
                )
                for row in set_rows
            ),
            2
        )

        average_reps_per_rep_set = 0.0

        if rep_set_count > 0:
            average_reps_per_rep_set = round(
                total_reps / rep_set_count,
                2
            )

        average_volume_per_completed_workout = 0.0

        if completed_workout_count > 0:
            average_volume_per_completed_workout = round(
                total_volume_kg
                / completed_workout_count,
                2
            )

        return {
            "completed_workout_count": completed_workout_count,
            "exercise_occurrence_count": exercise_occurrence_count,
            "performance_log_count": performance_log_count,
            "rep_set_count": rep_set_count,
            "weighted_set_count": weighted_set_count,
            "total_reps": total_reps,
            "total_volume_kg": total_volume_kg,
            "average_reps_per_rep_set": average_reps_per_rep_set,
            "average_volume_per_completed_workout": average_volume_per_completed_workout
        }

    finally:
        connection.close()


def get_exercise_frequency_analytics(
    user_id
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                e.exercise_id,
                e.name,
                e.primary_muscle,
                COUNT(DISTINCT ws.workout_session_id) AS workout_count,
                COUNT(DISTINCT wse.session_exercise_id) AS exercise_occurrence_count,
                COUNT(wsl.set_log_id) AS performance_log_count,
                COALESCE(
                    SUM(wsl.reps_completed),
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
                ) AS total_volume_kg
            FROM workout_session_exercises AS wse
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            JOIN exercises AS e
                ON e.exercise_id = wse.exercise_id
            LEFT JOIN workout_set_logs AS wsl
                ON wsl.session_exercise_id = wse.session_exercise_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            GROUP BY
                e.exercise_id,
                e.name,
                e.primary_muscle
            ORDER BY
                workout_count DESC,
                exercise_occurrence_count DESC,
                performance_log_count DESC,
                e.exercise_id ASC
            """,
            (
                user_id,
            )
        ).fetchall()

        return [
            {
                "exercise_id": row["exercise_id"],
                "name": row["name"],
                "primary_muscle": row["primary_muscle"],
                "workout_count": row["workout_count"],
                "exercise_occurrence_count": row["exercise_occurrence_count"],
                "performance_log_count": row["performance_log_count"],
                "total_reps": row["total_reps"],
                "total_volume_kg": round(
                    row["total_volume_kg"],
                    2
                )
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_primary_muscle_frequency_analytics(
    user_id
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                e.primary_muscle,
                COUNT(DISTINCT ws.workout_session_id) AS workout_count,
                COUNT(DISTINCT wse.session_exercise_id) AS exercise_occurrence_count,
                COUNT(wsl.set_log_id) AS performance_log_count,
                COALESCE(
                    SUM(wsl.reps_completed),
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
                ) AS total_volume_kg
            FROM workout_session_exercises AS wse
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            JOIN exercises AS e
                ON e.exercise_id = wse.exercise_id
            LEFT JOIN workout_set_logs AS wsl
                ON wsl.session_exercise_id = wse.session_exercise_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            GROUP BY
                e.primary_muscle
            ORDER BY
                workout_count DESC,
                exercise_occurrence_count DESC,
                performance_log_count DESC,
                e.primary_muscle ASC
            """,
            (
                user_id,
            )
        ).fetchall()

        return [
            {
                "primary_muscle": row["primary_muscle"],
                "workout_count": row["workout_count"],
                "exercise_occurrence_count": row["exercise_occurrence_count"],
                "performance_log_count": row["performance_log_count"],
                "total_reps": row["total_reps"],
                "total_volume_kg": round(
                    row["total_volume_kg"],
                    2
                )
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_workout_volume_breakdown(
    user_id
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                ws.workout_session_id,
                ws.started_at,
                ws.completed_at,
                ws.primary_goal,
                ws.actual_duration_minutes,
                COUNT(DISTINCT wse.session_exercise_id) AS exercise_count,
                COUNT(wsl.set_log_id) AS performance_log_count,
                COALESCE(
                    SUM(wsl.reps_completed),
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
                ) AS total_volume_kg
            FROM workout_sessions AS ws
            LEFT JOIN workout_session_exercises AS wse
                ON wse.workout_session_id = ws.workout_session_id
            LEFT JOIN workout_set_logs AS wsl
                ON wsl.session_exercise_id = wse.session_exercise_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            GROUP BY
                ws.workout_session_id,
                ws.started_at,
                ws.completed_at,
                ws.primary_goal,
                ws.actual_duration_minutes
            ORDER BY
                ws.started_at DESC,
                ws.workout_session_id DESC
            """,
            (
                user_id,
            )
        ).fetchall()

        return [
            {
                "workout_session_id": row["workout_session_id"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "primary_goal": row["primary_goal"],
                "actual_duration_minutes": row["actual_duration_minutes"],
                "exercise_count": row["exercise_count"],
                "performance_log_count": row["performance_log_count"],
                "total_reps": row["total_reps"],
                "total_volume_kg": round(
                    row["total_volume_kg"],
                    2
                )
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_training_analytics_overview(
    user_id
):
    return {
        "volume": get_training_volume_analytics(
            user_id
        ),
        "exercise_frequency": get_exercise_frequency_analytics(
            user_id
        ),
        "primary_muscle_frequency": get_primary_muscle_frequency_analytics(
            user_id
        ),
        "workout_breakdown": get_workout_volume_breakdown(
            user_id
        )
    }
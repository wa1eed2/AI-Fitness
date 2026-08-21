from datetime import timedelta

from src.database.query_progress_database import (
    get_progress_history,
    get_body_measurement_history,
    get_activity_history
)

from src.database.query_workout_log_database import (
    get_connection
)

from src.analytics.fitness_analytics import (
    get_analytics_overview
)

from src.analytics.training_analytics import (
    get_training_analytics_overview,
    get_primary_muscle_frequency_analytics,
    get_workout_volume_breakdown
)

from src.analytics.trend_analytics import (
    normalize_reference_date,
    get_window_dates,
    timestamp_to_date,
    get_trend_analytics_overview
)


def validate_positive_integer(
    value,
    field_name
):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")


def get_weight_chart_series(
    user_id,
    days=None,
    reference_date=None
):
    history = get_progress_history(
        user_id
    )

    if days is not None:
        start_date, end_date = get_window_dates(
            days,
            reference_date
        )

        history = [
            entry
            for entry in history
            if (
                entry["weight_kg"] is not None
                and start_date
                <= timestamp_to_date(
                    entry["recorded_at"]
                )
                <= end_date
            )
        ]

    else:
        history = [
            entry
            for entry in history
            if entry["weight_kg"] is not None
        ]

    history.sort(
        key=lambda entry: entry["recorded_at"]
    )

    return [
        {
            "recorded_at": entry["recorded_at"],
            "weight_kg": entry["weight_kg"]
        }
        for entry in history
    ]


def get_body_measurement_chart_series(
    user_id,
    body_area,
    days=None,
    reference_date=None
):
    history = get_body_measurement_history(
        user_id,
        body_area=body_area
    )

    if days is not None:
        start_date, end_date = get_window_dates(
            days,
            reference_date
        )

        history = [
            entry
            for entry in history
            if (
                start_date
                <= timestamp_to_date(
                    entry["recorded_at"]
                )
                <= end_date
            )
        ]

    history.sort(
        key=lambda entry: entry["recorded_at"]
    )

    return [
        {
            "recorded_at": entry["recorded_at"],
            "measurement_cm": entry["measurement_cm"]
        }
        for entry in history
    ]


def get_activity_daily_series(
    user_id,
    days=30,
    reference_date=None
):
    start_date, end_date = get_window_dates(
        days,
        reference_date
    )

    activities = get_activity_history(
        user_id
    )

    daily_data = {}

    current_date = start_date

    while current_date <= end_date:
        daily_data[
            current_date.isoformat()
        ] = {
            "date": current_date.isoformat(),
            "activity_count": 0,
            "duration_minutes": 0.0,
            "distance_km": 0.0,
            "steps": 0,
            "estimated_calories": 0.0
        }

        current_date += timedelta(
            days=1
        )

    for activity in activities:
        activity_date = timestamp_to_date(
            activity["started_at"]
        )

        if not (
            start_date
            <= activity_date
            <= end_date
        ):
            continue

        date_key = activity_date.isoformat()

        daily_data[
            date_key
        ]["activity_count"] += 1

        daily_data[
            date_key
        ]["duration_minutes"] += (
            activity["duration_minutes"] or 0
        )

        daily_data[
            date_key
        ]["distance_km"] += (
            activity["distance_km"] or 0
        )

        daily_data[
            date_key
        ]["steps"] += (
            activity["steps"] or 0
        )

        daily_data[
            date_key
        ]["estimated_calories"] += (
            activity["estimated_calories"] or 0
        )

    result = []

    for item in daily_data.values():
        result.append(
            {
                "date": item["date"],
                "activity_count": item["activity_count"],
                "duration_minutes": round(
                    item["duration_minutes"],
                    2
                ),
                "distance_km": round(
                    item["distance_km"],
                    2
                ),
                "steps": item["steps"],
                "estimated_calories": round(
                    item["estimated_calories"],
                    2
                )
            }
        )

    return result


def get_weekly_training_volume_series(
    user_id,
    weeks=8,
    reference_date=None
):
    validate_positive_integer(
        weeks,
        "Weeks"
    )

    end_date = normalize_reference_date(
        reference_date
    )

    total_days = (
        weeks
        * 7
    )

    start_date = (
        end_date
        - timedelta(
            days=total_days - 1
        )
    )

    workouts = get_workout_volume_breakdown(
        user_id
    )

    result = []

    week_start = start_date

    while week_start <= end_date:
        week_end = min(
            week_start
            + timedelta(
                days=6
            ),
            end_date
        )

        matching_workouts = [
            workout
            for workout in workouts
            if (
                week_start
                <= timestamp_to_date(
                    workout["started_at"]
                )
                <= week_end
            )
        ]

        total_volume = round(
            sum(
                workout["total_volume_kg"]
                for workout in matching_workouts
            ),
            2
        )

        total_reps = sum(
            workout["total_reps"]
            for workout in matching_workouts
        )

        result.append(
            {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "workout_count": len(
                    matching_workouts
                ),
                "total_reps": total_reps,
                "total_volume_kg": total_volume
            }
        )

        week_start = (
            week_end
            + timedelta(
                days=1
            )
        )

    return result


def get_muscle_distribution(
    user_id
):
    muscle_analytics = get_primary_muscle_frequency_analytics(
        user_id
    )

    total_occurrences = sum(
        item["exercise_occurrence_count"]
        for item in muscle_analytics
    )

    result = []

    for item in muscle_analytics:
        percentage = 0.0

        if total_occurrences > 0:
            percentage = round(
                item["exercise_occurrence_count"]
                / total_occurrences
                * 100,
                2
            )

        result.append(
            {
                "primary_muscle": item["primary_muscle"],
                "exercise_occurrence_count": item["exercise_occurrence_count"],
                "workout_count": item["workout_count"],
                "total_reps": item["total_reps"],
                "total_volume_kg": item["total_volume_kg"],
                "distribution_percentage": percentage
            }
        )

    result.sort(
        key=lambda item: (
            -item["exercise_occurrence_count"],
            item["primary_muscle"]
        )
    )

    return result


def get_personal_records(
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
                MAX(wsl.weight_kg) AS max_weight_kg,
                MAX(wsl.reps_completed) AS max_reps_completed,
                MAX(
                    CASE
                        WHEN wsl.reps_completed IS NOT NULL
                         AND wsl.weight_kg IS NOT NULL
                        THEN wsl.reps_completed * wsl.weight_kg
                        ELSE NULL
                    END
                ) AS max_set_volume_kg
            FROM workout_set_logs AS wsl
            JOIN workout_session_exercises AS wse
                ON wse.session_exercise_id = wsl.session_exercise_id
            JOIN workout_sessions AS ws
                ON ws.workout_session_id = wse.workout_session_id
            JOIN exercises AS e
                ON e.exercise_id = wse.exercise_id
            WHERE ws.user_id = ?
              AND ws.status = 'Completed'
            GROUP BY
                e.exercise_id,
                e.name,
                e.primary_muscle
            ORDER BY
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


def get_dashboard_analytics(
    user_id,
    reference_date=None
):
    normalized_reference_date = normalize_reference_date(
        reference_date
    )

    return {
        "reference_date": normalized_reference_date.isoformat(),
        "overview": get_analytics_overview(
            user_id
        ),
        "training": get_training_analytics_overview(
            user_id
        ),
        "trends": get_trend_analytics_overview(
            user_id,
            reference_date=normalized_reference_date.isoformat()
        ),
        "charts": {
            "weight_90_days": get_weight_chart_series(
                user_id,
                days=90,
                reference_date=normalized_reference_date.isoformat()
            ),
            "activity_30_days": get_activity_daily_series(
                user_id,
                days=30,
                reference_date=normalized_reference_date.isoformat()
            ),
            "training_volume_8_weeks": get_weekly_training_volume_series(
                user_id,
                weeks=8,
                reference_date=normalized_reference_date.isoformat()
            )
        },
        "muscle_distribution": get_muscle_distribution(
            user_id
        ),
        "personal_records": get_personal_records(
            user_id
        )
    }
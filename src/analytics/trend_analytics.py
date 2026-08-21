from datetime import date, datetime, timedelta

from src.database.query_progress_database import (
    get_activity_history,
    get_body_measurement_history,
    get_progress_history,
    get_calendar_workouts
)

from src.database.query_workout_log_database import (
    get_user_workout_history
)

from src.analytics.training_analytics import (
    get_workout_volume_breakdown
)


def validate_days(
    days
):
    if isinstance(days, bool) or not isinstance(days, int):
        raise ValueError("Days must be an integer")

    if days <= 0:
        raise ValueError("Days must be greater than 0")


def normalize_reference_date(
    reference_date=None
):
    if reference_date is None:
        return date.today()

    if not isinstance(reference_date, str) or not reference_date.strip():
        raise ValueError("Reference date must be a YYYY-MM-DD string")

    try:
        return date.fromisoformat(
            reference_date.strip()
        )

    except ValueError:
        raise ValueError("Reference date must use YYYY-MM-DD format")


def timestamp_to_date(
    value
):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Timestamp must be a non-empty string")

    try:
        return datetime.fromisoformat(
            value.strip()
        ).date()

    except ValueError:
        raise ValueError("Timestamp contains an invalid date")


def get_window_dates(
    days,
    reference_date=None
):
    validate_days(
        days
    )

    end_date = normalize_reference_date(
        reference_date
    )

    start_date = (
        end_date
        - timedelta(
            days=days - 1
        )
    )

    return (
        start_date,
        end_date
    )


def date_is_in_window(
    value,
    start_date,
    end_date
):
    event_date = timestamp_to_date(
        value
    )

    return (
        start_date
        <= event_date
        <= end_date
    )


def calculate_change_percentage(
    current_value,
    previous_value
):
    if previous_value == 0:
        if current_value == 0:
            return 0.0

        return None

    return round(
        (
            current_value
            - previous_value
        )
        / previous_value
        * 100,
        2
    )


def get_activity_window_analytics(
    user_id,
    days,
    reference_date=None
):
    start_date, end_date = get_window_dates(
        days,
        reference_date
    )

    activities = get_activity_history(
        user_id
    )

    filtered = [
        activity
        for activity in activities
        if date_is_in_window(
            activity["started_at"],
            start_date,
            end_date
        )
    ]

    total_duration_minutes = round(
        sum(
            activity["duration_minutes"] or 0
            for activity in filtered
        ),
        2
    )

    total_distance_km = round(
        sum(
            activity["distance_km"] or 0
            for activity in filtered
        ),
        2
    )

    total_steps = sum(
        activity["steps"] or 0
        for activity in filtered
    )

    total_estimated_calories = round(
        sum(
            activity["estimated_calories"] or 0
            for activity in filtered
        ),
        2
    )

    activity_type_counts = {}

    for activity in filtered:
        activity_type = activity[
            "activity_type"
        ]

        activity_type_counts[
            activity_type
        ] = (
            activity_type_counts.get(
                activity_type,
                0
            )
            + 1
        )

    average_daily_steps = round(
        total_steps / days,
        2
    )

    average_activity_minutes_per_day = round(
        total_duration_minutes / days,
        2
    )

    return {
        "days": days,
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "activity_count": len(filtered),
        "total_duration_minutes": total_duration_minutes,
        "average_activity_minutes_per_day": average_activity_minutes_per_day,
        "total_distance_km": total_distance_km,
        "total_steps": total_steps,
        "average_daily_steps": average_daily_steps,
        "total_estimated_calories": total_estimated_calories,
        "activity_type_counts": activity_type_counts
    }


def get_standard_activity_windows(
    user_id,
    reference_date=None
):
    return {
        "7_days": get_activity_window_analytics(
            user_id,
            7,
            reference_date
        ),
        "30_days": get_activity_window_analytics(
            user_id,
            30,
            reference_date
        ),
        "90_days": get_activity_window_analytics(
            user_id,
            90,
            reference_date
        )
    }


def get_workout_frequency_trend(
    user_id,
    days=28,
    reference_date=None
):
    start_date, end_date = get_window_dates(
        days,
        reference_date
    )

    workouts = get_user_workout_history(
        user_id
    )

    completed_workouts = [
        workout
        for workout in workouts
        if (
            workout["status"] == "Completed"
            and date_is_in_window(
                workout["started_at"],
                start_date,
                end_date
            )
        )
    ]

    training_dates = {
        timestamp_to_date(
            workout["started_at"]
        )
        for workout in completed_workouts
    }

    weekly_counts = []

    bucket_start = start_date

    while bucket_start <= end_date:
        bucket_end = min(
            bucket_start
            + timedelta(
                days=6
            ),
            end_date
        )

        count = sum(
            1
            for workout in completed_workouts
            if (
                bucket_start
                <= timestamp_to_date(
                    workout["started_at"]
                )
                <= bucket_end
            )
        )

        weekly_counts.append(
            {
                "week_start": bucket_start.isoformat(),
                "week_end": bucket_end.isoformat(),
                "completed_workout_count": count
            }
        )

        bucket_start = (
            bucket_end
            + timedelta(
                days=1
            )
        )

    week_count = len(
        weekly_counts
    )

    weeks_with_training = sum(
        1
        for bucket in weekly_counts
        if bucket["completed_workout_count"] > 0
    )

    average_workouts_per_week = 0.0
    weekly_consistency_percentage = 0.0

    if week_count > 0:
        average_workouts_per_week = round(
            len(completed_workouts)
            / week_count,
            2
        )

        weekly_consistency_percentage = round(
            weeks_with_training
            / week_count
            * 100,
            2
        )

    return {
        "days": days,
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "completed_workout_count": len(completed_workouts),
        "training_day_count": len(training_dates),
        "week_count": week_count,
        "weeks_with_training": weeks_with_training,
        "average_workouts_per_week": average_workouts_per_week,
        "weekly_consistency_percentage": weekly_consistency_percentage,
        "weekly_completed_counts": weekly_counts
    }


def get_volume_trend(
    user_id,
    days=30,
    reference_date=None
):
    current_start, current_end = get_window_dates(
        days,
        reference_date
    )

    previous_end = (
        current_start
        - timedelta(
            days=1
        )
    )

    previous_start = (
        previous_end
        - timedelta(
            days=days - 1
        )
    )

    workouts = get_workout_volume_breakdown(
        user_id
    )

    current_workouts = []
    previous_workouts = []

    for workout in workouts:
        workout_date = timestamp_to_date(
            workout["started_at"]
        )

        if (
            current_start
            <= workout_date
            <= current_end
        ):
            current_workouts.append(
                workout
            )

        elif (
            previous_start
            <= workout_date
            <= previous_end
        ):
            previous_workouts.append(
                workout
            )

    current_volume = round(
        sum(
            workout["total_volume_kg"]
            for workout in current_workouts
        ),
        2
    )

    previous_volume = round(
        sum(
            workout["total_volume_kg"]
            for workout in previous_workouts
        ),
        2
    )

    volume_change = round(
        current_volume
        - previous_volume,
        2
    )

    current_average = 0.0
    previous_average = 0.0

    if current_workouts:
        current_average = round(
            current_volume
            / len(current_workouts),
            2
        )

    if previous_workouts:
        previous_average = round(
            previous_volume
            / len(previous_workouts),
            2
        )

    return {
        "days": days,
        "current_window_start": current_start.isoformat(),
        "current_window_end": current_end.isoformat(),
        "previous_window_start": previous_start.isoformat(),
        "previous_window_end": previous_end.isoformat(),
        "current_workout_count": len(current_workouts),
        "previous_workout_count": len(previous_workouts),
        "current_volume_kg": current_volume,
        "previous_volume_kg": previous_volume,
        "volume_change_kg": volume_change,
        "volume_change_percentage": calculate_change_percentage(
            current_volume,
            previous_volume
        ),
        "current_average_volume_per_workout_kg": current_average,
        "previous_average_volume_per_workout_kg": previous_average
    }


def get_weight_trend(
    user_id,
    days=90,
    reference_date=None
):
    start_date, end_date = get_window_dates(
        days,
        reference_date
    )

    history = get_progress_history(
        user_id
    )

    entries = [
        entry
        for entry in history
        if (
            entry["weight_kg"] is not None
            and date_is_in_window(
                entry["recorded_at"],
                start_date,
                end_date
            )
        )
    ]

    if not entries:
        return {
            "days": days,
            "window_start": start_date.isoformat(),
            "window_end": end_date.isoformat(),
            "entry_count": 0,
            "latest_weight_kg": None,
            "earliest_weight_kg": None,
            "weight_change_kg": None
        }

    latest = entries[0]
    earliest = entries[-1]

    return {
        "days": days,
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "entry_count": len(entries),
        "latest_weight_kg": latest["weight_kg"],
        "earliest_weight_kg": earliest["weight_kg"],
        "weight_change_kg": round(
            latest["weight_kg"]
            - earliest["weight_kg"],
            2
        )
    }


def get_measurement_trend(
    user_id,
    body_area,
    days=90,
    reference_date=None
):
    start_date, end_date = get_window_dates(
        days,
        reference_date
    )

    history = get_body_measurement_history(
        user_id,
        body_area=body_area
    )

    entries = [
        entry
        for entry in history
        if date_is_in_window(
            entry["recorded_at"],
            start_date,
            end_date
        )
    ]

    if not entries:
        return {
            "body_area": body_area,
            "days": days,
            "window_start": start_date.isoformat(),
            "window_end": end_date.isoformat(),
            "entry_count": 0,
            "latest_measurement_cm": None,
            "earliest_measurement_cm": None,
            "measurement_change_cm": None
        }

    latest = entries[0]
    earliest = entries[-1]

    return {
        "body_area": body_area,
        "days": days,
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "entry_count": len(entries),
        "latest_measurement_cm": latest["measurement_cm"],
        "earliest_measurement_cm": earliest["measurement_cm"],
        "measurement_change_cm": round(
            latest["measurement_cm"]
            - earliest["measurement_cm"],
            2
        )
    }


def get_calendar_adherence_trend(
    user_id,
    days=30,
    reference_date=None
):
    start_date, end_date = get_window_dates(
        days,
        reference_date
    )

    workouts = get_calendar_workouts(
        user_id
    )

    filtered = [
        workout
        for workout in workouts
        if date_is_in_window(
            workout["scheduled_for"],
            start_date,
            end_date
        )
    ]

    status_counts = {
        "Planned": 0,
        "Completed": 0,
        "Skipped": 0,
        "Cancelled": 0
    }

    for workout in filtered:
        status = workout[
            "status"
        ]

        if status in status_counts:
            status_counts[
                status
            ] += 1

    opportunity_count = (
        status_counts["Completed"]
        + status_counts["Skipped"]
    )

    completion_rate = 0.0

    if opportunity_count > 0:
        completion_rate = round(
            status_counts["Completed"]
            / opportunity_count
            * 100,
            2
        )

    return {
        "days": days,
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "scheduled_workout_count": len(filtered),
        "planned_count": status_counts["Planned"],
        "completed_count": status_counts["Completed"],
        "skipped_count": status_counts["Skipped"],
        "cancelled_count": status_counts["Cancelled"],
        "adherence_opportunity_count": opportunity_count,
        "completion_rate_percentage": completion_rate
    }


def get_trend_analytics_overview(
    user_id,
    reference_date=None
):
    return {
        "activity_windows": get_standard_activity_windows(
            user_id,
            reference_date
        ),
        "workout_frequency_28_days": get_workout_frequency_trend(
            user_id,
            days=28,
            reference_date=reference_date
        ),
        "volume_30_days": get_volume_trend(
            user_id,
            days=30,
            reference_date=reference_date
        ),
        "weight_90_days": get_weight_trend(
            user_id,
            days=90,
            reference_date=reference_date
        ),
        "calendar_adherence_30_days": get_calendar_adherence_trend(
            user_id,
            days=30,
            reference_date=reference_date
        )
    }
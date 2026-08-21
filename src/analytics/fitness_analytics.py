from src.database.query_progress_database import (
    get_progress_history,
    get_activity_history,
    get_calendar_workouts
)

from src.database.query_workout_log_database import (
    get_user_workout_history
)


def calculate_percentage(
    numerator,
    denominator
):
    if denominator == 0:
        return 0.0

    return round(
        numerator / denominator * 100,
        2
    )


def get_weight_analytics(
    user_id
):
    history = get_progress_history(
        user_id
    )

    weight_entries = [
        entry
        for entry in history
        if entry["weight_kg"] is not None
    ]

    if not weight_entries:
        return {
            "entry_count": 0,
            "latest_weight_kg": None,
            "earliest_weight_kg": None,
            "weight_change_kg": None
        }

    latest_weight = weight_entries[0][
        "weight_kg"
    ]

    earliest_weight = weight_entries[-1][
        "weight_kg"
    ]

    return {
        "entry_count": len(weight_entries),
        "latest_weight_kg": latest_weight,
        "earliest_weight_kg": earliest_weight,
        "weight_change_kg": round(
            latest_weight - earliest_weight,
            2
        )
    }


def get_body_fat_analytics(
    user_id
):
    history = get_progress_history(
        user_id
    )

    body_fat_entries = [
        entry
        for entry in history
        if entry["body_fat_percentage"] is not None
    ]

    if not body_fat_entries:
        return {
            "entry_count": 0,
            "latest_body_fat_percentage": None,
            "earliest_body_fat_percentage": None,
            "body_fat_change_percentage_points": None
        }

    latest_body_fat = body_fat_entries[0][
        "body_fat_percentage"
    ]

    earliest_body_fat = body_fat_entries[-1][
        "body_fat_percentage"
    ]

    return {
        "entry_count": len(body_fat_entries),
        "latest_body_fat_percentage": latest_body_fat,
        "earliest_body_fat_percentage": earliest_body_fat,
        "body_fat_change_percentage_points": round(
            latest_body_fat - earliest_body_fat,
            2
        )
    }


def get_activity_analytics(
    user_id
):
    activities = get_activity_history(
        user_id
    )

    total_duration_minutes = round(
        sum(
            activity["duration_minutes"] or 0
            for activity in activities
        ),
        2
    )

    total_distance_km = round(
        sum(
            activity["distance_km"] or 0
            for activity in activities
        ),
        2
    )

    total_steps = sum(
        activity["steps"] or 0
        for activity in activities
    )

    total_estimated_calories = round(
        sum(
            activity["estimated_calories"] or 0
            for activity in activities
        ),
        2
    )

    activity_type_counts = {}

    for activity in activities:
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

    average_duration_minutes = 0.0

    if activities:
        average_duration_minutes = round(
            total_duration_minutes / len(activities),
            2
        )

    return {
        "activity_count": len(activities),
        "total_duration_minutes": total_duration_minutes,
        "average_duration_minutes": average_duration_minutes,
        "total_distance_km": total_distance_km,
        "total_steps": total_steps,
        "total_estimated_calories": total_estimated_calories,
        "activity_type_counts": activity_type_counts
    }


def get_workout_consistency_analytics(
    user_id
):
    workouts = get_user_workout_history(
        user_id
    )

    completed_workouts = [
        workout
        for workout in workouts
        if workout["status"] == "Completed"
    ]

    cancelled_workouts = [
        workout
        for workout in workouts
        if workout["status"] == "Cancelled"
    ]

    active_workouts = [
        workout
        for workout in workouts
        if workout["status"] == "In Progress"
    ]

    terminal_workout_count = (
        len(completed_workouts)
        + len(cancelled_workouts)
    )

    completion_rate = calculate_percentage(
        len(completed_workouts),
        terminal_workout_count
    )

    total_completed_minutes = round(
        sum(
            workout["actual_duration_minutes"] or 0
            for workout in completed_workouts
        ),
        2
    )

    average_completed_duration_minutes = 0.0

    if completed_workouts:
        average_completed_duration_minutes = round(
            total_completed_minutes
            / len(completed_workouts),
            2
        )

    return {
        "total_workout_count": len(workouts),
        "completed_workout_count": len(completed_workouts),
        "cancelled_workout_count": len(cancelled_workouts),
        "active_workout_count": len(active_workouts),
        "terminal_workout_count": terminal_workout_count,
        "completion_rate_percentage": completion_rate,
        "total_completed_minutes": total_completed_minutes,
        "average_completed_duration_minutes": average_completed_duration_minutes
    }


def get_calendar_adherence_analytics(
    user_id
):
    workouts = get_calendar_workouts(
        user_id
    )

    status_counts = {
        "Planned": 0,
        "Completed": 0,
        "Skipped": 0,
        "Cancelled": 0
    }

    for workout in workouts:
        status = workout[
            "status"
        ]

        if status in status_counts:
            status_counts[
                status
            ] += 1

    adherence_denominator = (
        status_counts["Completed"]
        + status_counts["Skipped"]
    )

    completion_rate = calculate_percentage(
        status_counts["Completed"],
        adherence_denominator
    )

    return {
        "scheduled_workout_count": len(workouts),
        "planned_count": status_counts["Planned"],
        "completed_count": status_counts["Completed"],
        "skipped_count": status_counts["Skipped"],
        "cancelled_count": status_counts["Cancelled"],
        "adherence_opportunity_count": adherence_denominator,
        "completion_rate_percentage": completion_rate
    }


def get_analytics_overview(
    user_id
):
    return {
        "weight": get_weight_analytics(
            user_id
        ),
        "body_fat": get_body_fat_analytics(
            user_id
        ),
        "activity": get_activity_analytics(
            user_id
        ),
        "workout_consistency": get_workout_consistency_analytics(
            user_id
        ),
        "calendar_adherence": get_calendar_adherence_analytics(
            user_id
        )
    }
from datetime import datetime

from src.database.query_progress_database import (
    get_progress_history,
    get_body_measurement_history,
    get_activity_history,
    get_progress_photo_history,
    get_calendar_workouts
)

from src.database.query_workout_log_database import (
    get_user_workout_history
)


def parse_event_time(
    value,
    field_name
):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty timestamp")

    try:
        return datetime.fromisoformat(
            value.strip()
        )

    except ValueError:
        raise ValueError(f"{field_name} contains an invalid timestamp")


def create_timeline_event(
    event_type,
    event_time,
    source_id,
    data
):
    parse_event_time(
        event_time,
        "Event time"
    )

    return {
        "event_type": event_type,
        "event_time": event_time,
        "source_id": source_id,
        "data": data
    }


def build_progress_timeline(
    user_id,
    include_private_photos=True
):
    if not isinstance(include_private_photos, bool):
        raise ValueError("include_private_photos must be a boolean")

    events = []

    progress_entries = get_progress_history(
        user_id
    )

    for entry in progress_entries:
        events.append(
            create_timeline_event(
                "progress_entry",
                entry["recorded_at"],
                entry["progress_entry_id"],
                {
                    "weight_kg": entry["weight_kg"],
                    "body_fat_percentage": entry["body_fat_percentage"],
                    "notes": entry["notes"]
                }
            )
        )

    measurements = get_body_measurement_history(
        user_id
    )

    for measurement in measurements:
        events.append(
            create_timeline_event(
                "body_measurement",
                measurement["recorded_at"],
                measurement["body_measurement_id"],
                {
                    "body_area": measurement["body_area"],
                    "measurement_cm": measurement["measurement_cm"],
                    "notes": measurement["notes"]
                }
            )
        )

    activities = get_activity_history(
        user_id
    )

    for activity in activities:
        events.append(
            create_timeline_event(
                "activity",
                activity["started_at"],
                activity["activity_log_id"],
                {
                    "activity_type": activity["activity_type"],
                    "duration_minutes": activity["duration_minutes"],
                    "distance_km": activity["distance_km"],
                    "steps": activity["steps"],
                    "average_speed_kmh": activity["average_speed_kmh"],
                    "estimated_calories": activity["estimated_calories"],
                    "notes": activity["notes"]
                }
            )
        )

    photos = get_progress_photo_history(
        user_id
    )

    for photo in photos:
        if (
            not include_private_photos
            and photo["is_private"] == 1
        ):
            continue

        events.append(
            create_timeline_event(
                "progress_photo",
                photo["recorded_at"],
                photo["progress_photo_id"],
                {
                    "file_path": photo["file_path"],
                    "view_type": photo["view_type"],
                    "is_private": bool(photo["is_private"]),
                    "notes": photo["notes"]
                }
            )
        )

    scheduled_workouts = get_calendar_workouts(
        user_id
    )

    for workout in scheduled_workouts:
        if (
            workout["status"] == "Completed"
            and workout["workout_session_id"] is not None
        ):
            continue

        events.append(
            create_timeline_event(
                "scheduled_workout",
                workout["scheduled_for"],
                workout["scheduled_workout_id"],
                {
                    "primary_goal": workout["primary_goal"],
                    "planned_duration_minutes": workout["planned_duration_minutes"],
                    "status": workout["status"],
                    "workout_session_id": workout["workout_session_id"],
                    "notes": workout["notes"]
                }
            )
        )

    workout_sessions = get_user_workout_history(
        user_id
    )

    for workout in workout_sessions:
        events.append(
            create_timeline_event(
                "workout_session",
                workout["started_at"],
                workout["workout_session_id"],
                {
                    "status": workout["status"],
                    "primary_goal": workout["primary_goal"],
                    "planned_duration_minutes": workout["planned_duration_minutes"],
                    "actual_duration_minutes": workout["actual_duration_minutes"],
                    "completed_at": workout["completed_at"],
                    "notes": workout["notes"]
                }
            )
        )

    events.sort(
        key=lambda event: (
            parse_event_time(
                event["event_time"],
                "Event time"
            ),
            event["event_type"],
            event["source_id"]
        ),
        reverse=True
    )

    return events


def get_progress_summary(
    user_id
):
    progress_entries = get_progress_history(
        user_id
    )

    measurements = get_body_measurement_history(
        user_id
    )

    activities = get_activity_history(
        user_id
    )

    photos = get_progress_photo_history(
        user_id
    )

    scheduled_workouts = get_calendar_workouts(
        user_id
    )

    workout_sessions = get_user_workout_history(
        user_id
    )

    weight_entries = [
        entry
        for entry in progress_entries
        if entry["weight_kg"] is not None
    ]

    body_fat_entries = [
        entry
        for entry in progress_entries
        if entry["body_fat_percentage"] is not None
    ]

    latest_weight_kg = None
    weight_change_kg = None

    if weight_entries:
        latest_weight_kg = weight_entries[0][
            "weight_kg"
        ]

        if len(weight_entries) >= 2:
            weight_change_kg = round(
                weight_entries[0]["weight_kg"]
                - weight_entries[-1]["weight_kg"],
                2
            )

        else:
            weight_change_kg = 0.0

    latest_body_fat_percentage = None
    body_fat_change_percentage_points = None

    if body_fat_entries:
        latest_body_fat_percentage = body_fat_entries[0][
            "body_fat_percentage"
        ]

        if len(body_fat_entries) >= 2:
            body_fat_change_percentage_points = round(
                body_fat_entries[0]["body_fat_percentage"]
                - body_fat_entries[-1]["body_fat_percentage"],
                2
            )

        else:
            body_fat_change_percentage_points = 0.0

    latest_measurements_cm = {}

    for measurement in measurements:
        body_area = measurement[
            "body_area"
        ]

        if body_area not in latest_measurements_cm:
            latest_measurements_cm[
                body_area
            ] = measurement[
                "measurement_cm"
            ]

    total_activity_minutes = round(
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

    completed_workouts = sum(
        1
        for workout in workout_sessions
        if workout["status"] == "Completed"
    )

    cancelled_workouts = sum(
        1
        for workout in workout_sessions
        if workout["status"] == "Cancelled"
    )

    calendar_status_counts = {
        "Planned": 0,
        "Completed": 0,
        "Skipped": 0,
        "Cancelled": 0
    }

    for workout in scheduled_workouts:
        status = workout[
            "status"
        ]

        if status in calendar_status_counts:
            calendar_status_counts[
                status
            ] += 1

    return {
        "latest_weight_kg": latest_weight_kg,
        "weight_change_kg": weight_change_kg,
        "latest_body_fat_percentage": latest_body_fat_percentage,
        "body_fat_change_percentage_points": body_fat_change_percentage_points,
        "latest_measurements_cm": latest_measurements_cm,
        "body_measurement_count": len(measurements),
        "activity_session_count": len(activities),
        "total_activity_minutes": total_activity_minutes,
        "total_distance_km": total_distance_km,
        "total_steps": total_steps,
        "total_estimated_calories": total_estimated_calories,
        "progress_photo_count": len(photos),
        "completed_workout_count": completed_workouts,
        "cancelled_workout_count": cancelled_workouts,
        "calendar_planned_count": calendar_status_counts["Planned"],
        "calendar_completed_count": calendar_status_counts["Completed"],
        "calendar_skipped_count": calendar_status_counts["Skipped"],
        "calendar_cancelled_count": calendar_status_counts["Cancelled"]
    }
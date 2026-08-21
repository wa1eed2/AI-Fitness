from src.database.setup_progress_database import (
    setup_progress_database
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_progress_database import (
    add_progress_entry,
    add_body_measurement,
    add_activity_log,
    add_progress_photo,
    schedule_workout_from_plan,
    update_scheduled_workout_status,
    complete_scheduled_workout
)

from src.database.query_workout_log_database import (
    start_workout_from_plan,
    finish_workout_session,
    cancel_workout_session
)

from src.progress.progress_timeline import (
    build_progress_timeline,
    get_progress_summary
)


def test_empty_progress_timeline():
    user_id = create_user()

    try:
        timeline = build_progress_timeline(
            user_id
        )

        if timeline != []:
            raise ValueError("FAIL: Empty user returned progress timeline events")

        print("PASS: Empty user returns empty progress timeline")

    finally:
        delete_user(user_id)


def test_progress_timeline_contains_progress_entry():
    user_id = create_user()

    try:
        progress_entry_id = add_progress_entry(
            user_id,
            weight_kg=80
        )

        timeline = build_progress_timeline(
            user_id
        )

        matching_events = [
            event
            for event in timeline
            if (
                event["event_type"] == "progress_entry"
                and event["source_id"] == progress_entry_id
            )
        ]

        if len(matching_events) != 1:
            raise ValueError("FAIL: Progress entry did not appear in timeline")

        if matching_events[0]["data"]["weight_kg"] != 80:
            raise ValueError("FAIL: Timeline progress entry returned incorrect weight")

        print("PASS: Progress entries appear in progress timeline")

    finally:
        delete_user(user_id)


def test_progress_timeline_contains_all_event_types():
    user_id = create_user()

    try:
        add_progress_entry(
            user_id,
            weight_kg=80
        )

        add_body_measurement(
            user_id,
            "Waist",
            84
        )

        add_activity_log(
            user_id,
            "Walking",
            duration_minutes=30
        )

        add_progress_photo(
            user_id,
            "front.jpg",
            "Front"
        )

        schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        workout_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=30
        )

        timeline = build_progress_timeline(
            user_id
        )

        event_types = {
            event["event_type"]
            for event in timeline
        }

        expected_types = {
            "progress_entry",
            "body_measurement",
            "activity",
            "progress_photo",
            "scheduled_workout",
            "workout_session"
        }

        if not expected_types.issubset(event_types):
            raise ValueError("FAIL: Progress timeline is missing one or more event types")

        print("PASS: Progress timeline combines all progress event types")

    finally:
        delete_user(user_id)


def test_progress_timeline_returns_newest_first():
    user_id = create_user()

    try:
        schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        schedule_workout_from_plan(
            user_id,
            "2026-09-01 18:00:00",
            {
                "exercises": []
            }
        )

        timeline = build_progress_timeline(
            user_id
        )

        scheduled_events = [
            event
            for event in timeline
            if event["event_type"] == "scheduled_workout"
        ]

        if scheduled_events[0]["event_time"] != "2026-09-01 18:00:00":
            raise ValueError("FAIL: Progress timeline did not return newest scheduled event first")

        if scheduled_events[1]["event_time"] != "2026-08-25 18:00:00":
            raise ValueError("FAIL: Progress timeline returned incorrect event order")

        print("PASS: Progress timeline returns newest events first")

    finally:
        delete_user(user_id)


def test_private_photos_can_be_hidden_from_timeline():
    user_id = create_user()

    try:
        add_progress_photo(
            user_id,
            "private.jpg",
            "Front",
            is_private=True
        )

        add_progress_photo(
            user_id,
            "public.jpg",
            "Side",
            is_private=False
        )

        timeline = build_progress_timeline(
            user_id,
            include_private_photos=False
        )

        photo_events = [
            event
            for event in timeline
            if event["event_type"] == "progress_photo"
        ]

        if len(photo_events) != 1:
            raise ValueError("FAIL: Private-photo filtering returned incorrect photo count")

        if photo_events[0]["data"]["file_path"] != "public.jpg":
            raise ValueError("FAIL: Private-photo filtering returned incorrect photo")

        print("PASS: Private progress photos can be hidden from timeline")

    finally:
        delete_user(user_id)


def test_invalid_private_photo_option_rejected():
    user_id = create_user()

    try:
        invalid_values = [
            1,
            0,
            "yes",
            None
        ]

        for value in invalid_values:
            try:
                build_progress_timeline(
                    user_id,
                    include_private_photos=value
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid private-photo option was accepted: {value}")

        print("PASS: Progress timeline requires boolean private-photo option")

    finally:
        delete_user(user_id)


def test_completed_calendar_workout_not_duplicated_in_timeline():
    user_id = create_user()

    try:
        plan = {
            "primary_goal": "General Fitness",
            "session_duration_minutes": 45,
            "exercises": []
        }

        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            plan
        )

        workout_session_id = start_workout_from_plan(
            user_id,
            plan
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=40
        )

        complete_scheduled_workout(
            scheduled_workout_id,
            workout_session_id
        )

        timeline = build_progress_timeline(
            user_id
        )

        linked_schedule_events = [
            event
            for event in timeline
            if (
                event["event_type"] == "scheduled_workout"
                and event["source_id"] == scheduled_workout_id
            )
        ]

        session_events = [
            event
            for event in timeline
            if (
                event["event_type"] == "workout_session"
                and event["source_id"] == workout_session_id
            )
        ]

        if len(linked_schedule_events) != 0:
            raise ValueError("FAIL: Completed linked calendar workout was duplicated in timeline")

        if len(session_events) != 1:
            raise ValueError("FAIL: Completed workout session was missing from timeline")

        print("PASS: Completed linked workout is not duplicated in timeline")

    finally:
        delete_user(user_id)


def test_empty_progress_summary():
    user_id = create_user()

    try:
        summary = get_progress_summary(
            user_id
        )

        if summary["latest_weight_kg"] is not None:
            raise ValueError("FAIL: Empty summary returned a weight")

        if summary["weight_change_kg"] is not None:
            raise ValueError("FAIL: Empty summary returned weight change")

        if summary["activity_session_count"] != 0:
            raise ValueError("FAIL: Empty summary returned activity sessions")

        if summary["completed_workout_count"] != 0:
            raise ValueError("FAIL: Empty summary returned completed workouts")

        if summary["progress_photo_count"] != 0:
            raise ValueError("FAIL: Empty summary returned progress photos")

        print("PASS: Empty user returns empty progress summary")

    finally:
        delete_user(user_id)


def test_progress_summary_calculates_weight_change():
    user_id = create_user()

    try:
        add_progress_entry(
            user_id,
            weight_kg=82
        )

        add_progress_entry(
            user_id,
            weight_kg=80
        )

        summary = get_progress_summary(
            user_id
        )

        if summary["latest_weight_kg"] != 80:
            raise ValueError("FAIL: Progress summary returned incorrect latest weight")

        if summary["weight_change_kg"] != -2:
            raise ValueError("FAIL: Progress summary returned incorrect weight change")

        print("PASS: Progress summary calculates weight change")

    finally:
        delete_user(user_id)


def test_progress_summary_calculates_body_fat_change():
    user_id = create_user()

    try:
        add_progress_entry(
            user_id,
            body_fat_percentage=22
        )

        add_progress_entry(
            user_id,
            body_fat_percentage=19.5
        )

        summary = get_progress_summary(
            user_id
        )

        if summary["latest_body_fat_percentage"] != 19.5:
            raise ValueError("FAIL: Progress summary returned incorrect latest body fat")

        if summary["body_fat_change_percentage_points"] != -2.5:
            raise ValueError("FAIL: Progress summary returned incorrect body-fat change")

        print("PASS: Progress summary calculates body-fat change")

    finally:
        delete_user(user_id)


def test_progress_summary_returns_latest_measurements():
    user_id = create_user()

    try:
        add_body_measurement(
            user_id,
            "Waist",
            86
        )

        add_body_measurement(
            user_id,
            "Chest",
            100
        )

        add_body_measurement(
            user_id,
            "Waist",
            84
        )

        summary = get_progress_summary(
            user_id
        )

        if summary["latest_measurements_cm"]["Waist"] != 84:
            raise ValueError("FAIL: Summary returned incorrect latest waist measurement")

        if summary["latest_measurements_cm"]["Chest"] != 100:
            raise ValueError("FAIL: Summary returned incorrect latest chest measurement")

        if summary["body_measurement_count"] != 3:
            raise ValueError("FAIL: Summary returned incorrect body measurement count")

        print("PASS: Progress summary returns latest body measurements")

    finally:
        delete_user(user_id)


def test_progress_summary_totals_activity():
    user_id = create_user()

    try:
        add_activity_log(
            user_id,
            "Walking",
            duration_minutes=30,
            distance_km=2.5,
            steps=4000,
            estimated_calories=150
        )

        add_activity_log(
            user_id,
            "Running",
            duration_minutes=20,
            distance_km=4,
            steps=3000,
            estimated_calories=250
        )

        summary = get_progress_summary(
            user_id
        )

        if summary["activity_session_count"] != 2:
            raise ValueError("FAIL: Activity summary returned incorrect session count")

        if summary["total_activity_minutes"] != 50:
            raise ValueError("FAIL: Activity summary returned incorrect duration")

        if summary["total_distance_km"] != 6.5:
            raise ValueError("FAIL: Activity summary returned incorrect distance")

        if summary["total_steps"] != 7000:
            raise ValueError("FAIL: Activity summary returned incorrect step count")

        if summary["total_estimated_calories"] != 400:
            raise ValueError("FAIL: Activity summary returned incorrect estimated calories")

        print("PASS: Progress summary totals activity metrics")

    finally:
        delete_user(user_id)


def test_progress_summary_counts_photos():
    user_id = create_user()

    try:
        add_progress_photo(
            user_id,
            "front.jpg",
            "Front"
        )

        add_progress_photo(
            user_id,
            "side.jpg",
            "Side"
        )

        summary = get_progress_summary(
            user_id
        )

        if summary["progress_photo_count"] != 2:
            raise ValueError("FAIL: Progress summary returned incorrect photo count")

        print("PASS: Progress summary counts progress photos")

    finally:
        delete_user(user_id)


def test_progress_summary_counts_workout_sessions():
    user_id = create_user()

    try:
        first_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            first_session_id,
            actual_duration_minutes=30
        )

        second_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        cancel_workout_session(
            second_session_id,
            notes="Test cancellation"
        )

        summary = get_progress_summary(
            user_id
        )

        if summary["completed_workout_count"] != 1:
            raise ValueError("FAIL: Summary returned incorrect completed workout count")

        if summary["cancelled_workout_count"] != 1:
            raise ValueError("FAIL: Summary returned incorrect cancelled workout count")

        print("PASS: Progress summary counts workout sessions")

    finally:
        delete_user(user_id)


def test_progress_summary_counts_calendar_statuses():
    user_id = create_user()

    try:
        planned_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        skipped_id = schedule_workout_from_plan(
            user_id,
            "2026-08-26 18:00:00",
            {
                "exercises": []
            }
        )

        cancelled_id = schedule_workout_from_plan(
            user_id,
            "2026-08-27 18:00:00",
            {
                "exercises": []
            }
        )

        completed_id = schedule_workout_from_plan(
            user_id,
            "2026-08-28 18:00:00",
            {
                "exercises": []
            }
        )

        update_scheduled_workout_status(
            skipped_id,
            "Skipped"
        )

        update_scheduled_workout_status(
            cancelled_id,
            "Cancelled"
        )

        workout_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=30
        )

        complete_scheduled_workout(
            completed_id,
            workout_session_id
        )

        summary = get_progress_summary(
            user_id
        )

        if summary["calendar_planned_count"] != 1:
            raise ValueError("FAIL: Summary returned incorrect Planned count")

        if summary["calendar_completed_count"] != 1:
            raise ValueError("FAIL: Summary returned incorrect Completed count")

        if summary["calendar_skipped_count"] != 1:
            raise ValueError("FAIL: Summary returned incorrect Skipped count")

        if summary["calendar_cancelled_count"] != 1:
            raise ValueError("FAIL: Summary returned incorrect Cancelled count")

        if planned_id is None:
            raise ValueError("FAIL: Planned calendar workout was not created")

        print("PASS: Progress summary counts calendar statuses")

    finally:
        delete_user(user_id)


if __name__ == "__main__":
    setup_progress_database()

    test_empty_progress_timeline()
    test_progress_timeline_contains_progress_entry()
    test_progress_timeline_contains_all_event_types()
    test_progress_timeline_returns_newest_first()
    test_private_photos_can_be_hidden_from_timeline()
    test_invalid_private_photo_option_rejected()
    test_completed_calendar_workout_not_duplicated_in_timeline()

    test_empty_progress_summary()
    test_progress_summary_calculates_weight_change()
    test_progress_summary_calculates_body_fat_change()
    test_progress_summary_returns_latest_measurements()
    test_progress_summary_totals_activity()
    test_progress_summary_counts_photos()
    test_progress_summary_counts_workout_sessions()
    test_progress_summary_counts_calendar_statuses()
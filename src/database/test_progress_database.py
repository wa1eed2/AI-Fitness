import sqlite3

from src.database.setup_progress_database import (
    DATABASE_PATH,
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
    get_progress_history,
    get_body_measurement_history,
    get_activity_history,
    add_progress_photo,
    get_progress_photo_history,
    delete_progress_photo,
    schedule_workout_from_plan,
    get_scheduled_workout,
    get_calendar_workouts,
    reschedule_workout,
    update_scheduled_workout_status,
    complete_scheduled_workout,
    delete_scheduled_workout
)

from src.database.query_workout_log_database import (
    start_workout_from_plan,
    finish_workout_session
)


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def test_progress_tables_exist():
    setup_progress_database()

    connection = get_connection()

    try:
        expected_tables = {
            "progress_entries",
            "body_measurements",
            "activity_logs",
            "progress_photos",
            "scheduled_workouts",
            "scheduled_workout_exercises"
        }

        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        existing_tables = {
            row["name"]
            for row in rows
        }

        if not expected_tables.issubset(existing_tables):
            raise ValueError("FAIL: One or more progress/calendar tables are missing")

        print("PASS: Progress and calendar database tables exist")

    finally:
        connection.close()


def test_add_progress_entry():
    user_id = create_user()

    try:
        progress_entry_id = add_progress_entry(
            user_id,
            weight_kg=80.5,
            body_fat_percentage=18.0,
            notes="Baseline"
        )

        if not isinstance(progress_entry_id, int):
            raise ValueError("FAIL: Progress entry did not return integer ID")

        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT *
                FROM progress_entries
                WHERE progress_entry_id = ?
                """,
                (
                    progress_entry_id,
                )
            ).fetchone()

            if row["weight_kg"] != 80.5:
                raise ValueError("FAIL: Progress weight was not saved")

            if row["body_fat_percentage"] != 18.0:
                raise ValueError("FAIL: Body-fat percentage was not saved")

        finally:
            connection.close()

        print("PASS: Progress entry saves correctly")

    finally:
        delete_user(user_id)


def test_invalid_body_fat_rejected():
    user_id = create_user()

    try:
        invalid_values = [
            -1,
            101,
            True,
            "20"
        ]

        for value in invalid_values:
            try:
                add_progress_entry(
                    user_id,
                    body_fat_percentage=value
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid body-fat percentage was accepted: {value}")

        print("PASS: Invalid body-fat percentages rejected")

    finally:
        delete_user(user_id)


def test_add_body_measurement():
    user_id = create_user()

    try:
        measurement_id = add_body_measurement(
            user_id,
            "Waist",
            84.5
        )

        if not isinstance(measurement_id, int):
            raise ValueError("FAIL: Body measurement did not return integer ID")

        print("PASS: Body measurement saves correctly")

    finally:
        delete_user(user_id)


def test_invalid_body_area_rejected():
    user_id = create_user()

    try:
        try:
            add_body_measurement(
                user_id,
                "Wing Span",
                180
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Invalid body area was accepted")

        print("PASS: Invalid body area rejected")

    finally:
        delete_user(user_id)


def test_add_activity_log():
    user_id = create_user()

    try:
        activity_log_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=45,
            distance_km=3.8,
            steps=5600,
            average_speed_kmh=5.1,
            estimated_calories=210
        )

        if not isinstance(activity_log_id, int):
            raise ValueError("FAIL: Activity log did not return integer ID")

        print("PASS: Activity log saves correctly")

    finally:
        delete_user(user_id)


def test_invalid_weight_rejected():
    user_id = create_user()

    try:
        invalid_values = [
            0,
            -1,
            True,
            "80"
        ]

        for value in invalid_values:
            try:
                add_progress_entry(
                    user_id,
                    weight_kg=value
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid weight was accepted: {value}")

        print("PASS: Invalid weights rejected")

    finally:
        delete_user(user_id)


def test_empty_progress_entry_rejected():
    user_id = create_user()

    try:
        try:
            add_progress_entry(
                user_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Empty progress entry was accepted")

        print("PASS: Empty progress entry rejected")

    finally:
        delete_user(user_id)


def test_invalid_measurement_rejected():
    user_id = create_user()

    try:
        invalid_values = [
            None,
            0,
            -1,
            True,
            "85"
        ]

        for value in invalid_values:
            try:
                add_body_measurement(
                    user_id,
                    "Waist",
                    value
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid body measurement was accepted: {value}")

        print("PASS: Invalid body measurements rejected")

    finally:
        delete_user(user_id)


def test_invalid_activity_type_rejected():
    user_id = create_user()

    try:
        try:
            add_activity_log(
                user_id,
                "Flying"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Invalid activity type was accepted")

        print("PASS: Invalid activity type rejected")

    finally:
        delete_user(user_id)


def test_invalid_activity_values_rejected():
    user_id = create_user()

    try:
        invalid_cases = [
            {
                "duration_minutes": -1
            },
            {
                "distance_km": -1
            },
            {
                "average_speed_kmh": -1
            },
            {
                "estimated_calories": -1
            },
            {
                "steps": -1
            },
            {
                "steps": 10.5
            },
            {
                "steps": True
            }
        ]

        for values in invalid_cases:
            try:
                add_activity_log(
                    user_id,
                    "Walking",
                    **values
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid activity values were accepted: {values}")

        print("PASS: Invalid activity values rejected")

    finally:
        delete_user(user_id)


def test_progress_history_returns_newest_first():
    user_id = create_user()

    try:
        first_id = add_progress_entry(
            user_id,
            weight_kg=82
        )

        second_id = add_progress_entry(
            user_id,
            weight_kg=81
        )

        history = get_progress_history(
            user_id
        )

        history_ids = [
            entry["progress_entry_id"]
            for entry in history
        ]

        if history_ids[:2] != [
            second_id,
            first_id
        ]:
            raise ValueError("FAIL: Progress history is not newest first")

        print("PASS: Progress history returns newest entries first")

    finally:
        delete_user(user_id)


def test_progress_history_limit():
    user_id = create_user()

    try:
        for weight in [
            82,
            81,
            80
        ]:
            add_progress_entry(
                user_id,
                weight_kg=weight
            )

        history = get_progress_history(
            user_id,
            limit=2
        )

        if len(history) != 2:
            raise ValueError("FAIL: Progress history limit was not applied")

        print("PASS: Progress history limit works correctly")

    finally:
        delete_user(user_id)


def test_body_measurement_history_filters_area():
    user_id = create_user()

    try:
        add_body_measurement(
            user_id,
            "Waist",
            84
        )

        add_body_measurement(
            user_id,
            "Chest",
            100
        )

        add_body_measurement(
            user_id,
            "Waist",
            83
        )

        history = get_body_measurement_history(
            user_id,
            body_area="Waist"
        )

        if len(history) != 2:
            raise ValueError("FAIL: Waist measurement history returned incorrect count")

        for entry in history:
            if entry["body_area"] != "Waist":
                raise ValueError("FAIL: Body measurement history returned wrong body area")

        print("PASS: Body measurement history filters by area")

    finally:
        delete_user(user_id)


def test_activity_history_filters_activity_type():
    user_id = create_user()

    try:
        add_activity_log(
            user_id,
            "Walking",
            duration_minutes=30
        )

        add_activity_log(
            user_id,
            "Running",
            duration_minutes=20
        )

        add_activity_log(
            user_id,
            "Walking",
            duration_minutes=40
        )

        history = get_activity_history(
            user_id,
            activity_type="Walking"
        )

        if len(history) != 2:
            raise ValueError("FAIL: Walking activity history returned incorrect count")

        for activity in history:
            if activity["activity_type"] != "Walking":
                raise ValueError("FAIL: Activity history returned wrong activity type")

        print("PASS: Activity history filters by activity type")

    finally:
        delete_user(user_id)


def test_user_delete_cascades_progress_data():
    user_id = create_user()

    progress_entry_id = add_progress_entry(
        user_id,
        weight_kg=80
    )

    measurement_id = add_body_measurement(
        user_id,
        "Waist",
        84
    )

    activity_id = add_activity_log(
        user_id,
        "Walking",
        steps=5000
    )

    photo_id = add_progress_photo(
        user_id,
        "photo.jpg",
        "Front"
    )

    scheduled_workout_id = schedule_workout_from_plan(
        user_id,
        "2026-08-25 18:00:00",
        {
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 3,
                    "reps": "8-12",
                    "rest_seconds": 90
                }
            ]
        }
    )

    delete_user(
        user_id
    )

    connection = get_connection()

    try:
        progress_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM progress_entries
            WHERE progress_entry_id = ?
            """,
            (
                progress_entry_id,
            )
        ).fetchone()[0]

        measurement_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM body_measurements
            WHERE body_measurement_id = ?
            """,
            (
                measurement_id,
            )
        ).fetchone()[0]

        activity_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM activity_logs
            WHERE activity_log_id = ?
            """,
            (
                activity_id,
            )
        ).fetchone()[0]

        photo_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM progress_photos
            WHERE progress_photo_id = ?
            """,
            (
                photo_id,
            )
        ).fetchone()[0]

        scheduled_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM scheduled_workouts
            WHERE scheduled_workout_id = ?
            """,
            (
                scheduled_workout_id,
            )
        ).fetchone()[0]

        scheduled_exercise_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM scheduled_workout_exercises
            WHERE scheduled_workout_id = ?
            """,
            (
                scheduled_workout_id,
            )
        ).fetchone()[0]

        if progress_count != 0:
            raise ValueError("FAIL: User deletion did not remove progress entry")

        if measurement_count != 0:
            raise ValueError("FAIL: User deletion did not remove body measurement")

        if activity_count != 0:
            raise ValueError("FAIL: User deletion did not remove activity log")

        if photo_count != 0:
            raise ValueError("FAIL: User deletion did not remove progress photo metadata")

        if scheduled_count != 0:
            raise ValueError("FAIL: User deletion did not remove scheduled workout")

        if scheduled_exercise_count != 0:
            raise ValueError("FAIL: Scheduled exercises did not cascade after user deletion")

        print("PASS: User deletion cascades through progress and calendar data")

    finally:
        connection.close()


def test_add_progress_photo():
    user_id = create_user()

    try:
        photo_id = add_progress_photo(
            user_id,
            "data/progress/user_1/front_001.jpg",
            "Front",
            notes="Baseline photo"
        )

        if not isinstance(photo_id, int):
            raise ValueError("FAIL: Progress photo did not return integer ID")

        photos = get_progress_photo_history(
            user_id
        )

        if len(photos) != 1:
            raise ValueError("FAIL: Progress photo was not saved")

        if photos[0]["file_path"] != "data/progress/user_1/front_001.jpg":
            raise ValueError("FAIL: Progress photo path was incorrect")

        if photos[0]["is_private"] != 1:
            raise ValueError("FAIL: Progress photo did not default to private")

        print("PASS: Progress photo metadata saves correctly")

    finally:
        delete_user(user_id)


def test_invalid_progress_photo_path_rejected():
    user_id = create_user()

    try:
        invalid_values = [
            "",
            "   ",
            None,
            123
        ]

        for value in invalid_values:
            try:
                add_progress_photo(
                    user_id,
                    value,
                    "Front"
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid photo path was accepted: {value}")

        print("PASS: Invalid progress photo paths rejected")

    finally:
        delete_user(user_id)


def test_invalid_progress_photo_view_rejected():
    user_id = create_user()

    try:
        try:
            add_progress_photo(
                user_id,
                "photo.jpg",
                "Diagonal"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Invalid progress photo view was accepted")

        print("PASS: Invalid progress photo view rejected")

    finally:
        delete_user(user_id)


def test_invalid_progress_photo_privacy_rejected():
    user_id = create_user()

    try:
        invalid_values = [
            1,
            0,
            "private",
            None
        ]

        for value in invalid_values:
            try:
                add_progress_photo(
                    user_id,
                    "photo.jpg",
                    "Front",
                    is_private=value
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid photo privacy value was accepted: {value}")

        print("PASS: Progress photo privacy requires boolean value")

    finally:
        delete_user(user_id)


def test_progress_photo_history_filters_view():
    user_id = create_user()

    try:
        add_progress_photo(
            user_id,
            "front_1.jpg",
            "Front"
        )

        add_progress_photo(
            user_id,
            "side_1.jpg",
            "Side"
        )

        add_progress_photo(
            user_id,
            "front_2.jpg",
            "Front"
        )

        photos = get_progress_photo_history(
            user_id,
            view_type="Front"
        )

        if len(photos) != 2:
            raise ValueError("FAIL: Front progress photo history returned incorrect count")

        for photo in photos:
            if photo["view_type"] != "Front":
                raise ValueError("FAIL: Progress photo history returned incorrect view type")

        print("PASS: Progress photo history filters by view type")

    finally:
        delete_user(user_id)


def test_delete_progress_photo():
    user_id = create_user()

    try:
        photo_id = add_progress_photo(
            user_id,
            "photo.jpg",
            "Front"
        )

        delete_progress_photo(
            photo_id
        )

        photos = get_progress_photo_history(
            user_id
        )

        if len(photos) != 0:
            raise ValueError("FAIL: Progress photo metadata was not deleted")

        print("PASS: Progress photo metadata deletes correctly")

    finally:
        delete_user(user_id)


def test_schedule_workout_from_plan():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-24 18:00:00",
            {
                "primary_goal": "Strength",
                "session_duration_minutes": 60,
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 3,
                        "reps": "8-12",
                        "rest_seconds": 90
                    },
                    {
                        "exercise_id": "E006",
                        "duration_minutes": 10
                    }
                ]
            }
        )

        if not isinstance(scheduled_workout_id, int):
            raise ValueError("FAIL: Scheduled workout did not return integer ID")

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

            if workout["status"] != "Planned":
                raise ValueError("FAIL: New scheduled workout did not use Planned status")

            if workout["primary_goal"] != "Strength":
                raise ValueError("FAIL: Scheduled workout did not save primary goal")

            if len(exercises) != 2:
                raise ValueError("FAIL: Scheduled workout did not save both exercises")

            if exercises[0]["exercise_order"] != 1:
                raise ValueError("FAIL: First scheduled exercise had incorrect order")

            if exercises[1]["exercise_order"] != 2:
                raise ValueError("FAIL: Second scheduled exercise had incorrect order")

        finally:
            connection.close()

        print("PASS: Workout schedules directly from recommendation plan")

    finally:
        delete_user(user_id)


def test_get_scheduled_workout():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:30:00",
            {
                "primary_goal": "Strength",
                "session_duration_minutes": 60,
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 3,
                        "reps": "8-12",
                        "rest_seconds": 90
                    }
                ]
            }
        )

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout is None:
            raise ValueError("FAIL: Scheduled workout was not retrieved")

        if workout["scheduled_for"] != "2026-08-25 18:30:00":
            raise ValueError("FAIL: Scheduled workout returned incorrect date")

        if len(workout["exercises"]) != 1:
            raise ValueError("FAIL: Scheduled workout did not include nested exercises")

        print("PASS: Scheduled workout retrieval includes exercises")

    finally:
        delete_user(user_id)


def test_calendar_workouts_filter_date_range():
    user_id = create_user()

    try:
        for scheduled_for in [
            "2026-08-20 18:00:00",
            "2026-08-25 18:00:00",
            "2026-08-30 18:00:00"
        ]:
            schedule_workout_from_plan(
                user_id,
                scheduled_for,
                {
                    "primary_goal": "General Fitness",
                    "session_duration_minutes": 45,
                    "exercises": []
                }
            )

        workouts = get_calendar_workouts(
            user_id,
            start_date="2026-08-24",
            end_date="2026-08-26"
        )

        if len(workouts) != 1:
            raise ValueError("FAIL: Calendar date range returned incorrect workout count")

        if workouts[0]["scheduled_for"] != "2026-08-25 18:00:00":
            raise ValueError("FAIL: Calendar date range returned incorrect workout")

        print("PASS: Calendar workouts filter by date range")

    finally:
        delete_user(user_id)


def test_calendar_workouts_return_chronological_order():
    user_id = create_user()

    try:
        schedule_workout_from_plan(
            user_id,
            "2026-08-30 18:00:00",
            {
                "exercises": []
            }
        )

        schedule_workout_from_plan(
            user_id,
            "2026-08-20 18:00:00",
            {
                "exercises": []
            }
        )

        schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        workouts = get_calendar_workouts(
            user_id
        )

        dates = [
            workout["scheduled_for"]
            for workout in workouts
        ]

        if dates != sorted(dates):
            raise ValueError("FAIL: Calendar workouts were not chronological")

        print("PASS: Calendar workouts return in chronological order")

    finally:
        delete_user(user_id)


def test_reschedule_workout():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-24 18:00:00",
            {
                "exercises": []
            }
        )

        result = reschedule_workout(
            scheduled_workout_id,
            "2026-08-27 19:30:00"
        )

        if result != "2026-08-27 19:30:00":
            raise ValueError("FAIL: Reschedule returned incorrect date")

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout["scheduled_for"] != "2026-08-27 19:30:00":
            raise ValueError("FAIL: Rescheduled date was not saved")

        print("PASS: Planned workout reschedules correctly")

    finally:
        delete_user(user_id)


def test_calendar_workouts_are_isolated_by_user():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        schedule_workout_from_plan(
            first_user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        schedule_workout_from_plan(
            second_user_id,
            "2026-08-25 19:00:00",
            {
                "exercises": []
            }
        )

        first_user_workouts = get_calendar_workouts(
            first_user_id
        )

        second_user_workouts = get_calendar_workouts(
            second_user_id
        )

        if len(first_user_workouts) != 1:
            raise ValueError("FAIL: First user's calendar returned incorrect count")

        if len(second_user_workouts) != 1:
            raise ValueError("FAIL: Second user's calendar returned incorrect count")

        if first_user_workouts[0]["user_id"] != first_user_id:
            raise ValueError("FAIL: First user's calendar leaked another user's workout")

        if second_user_workouts[0]["user_id"] != second_user_id:
            raise ValueError("FAIL: Second user's calendar leaked another user's workout")

        print("PASS: Calendar workouts are isolated by user")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


def test_scheduled_workout_can_be_skipped():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        update_scheduled_workout_status(
            scheduled_workout_id,
            "Skipped"
        )

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout["status"] != "Skipped":
            raise ValueError("FAIL: Scheduled workout did not become Skipped")

        print("PASS: Planned workout can be marked Skipped")

    finally:
        delete_user(user_id)


def test_scheduled_workout_can_be_cancelled():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        update_scheduled_workout_status(
            scheduled_workout_id,
            "Cancelled"
        )

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout["status"] != "Cancelled":
            raise ValueError("FAIL: Scheduled workout did not become Cancelled")

        print("PASS: Planned workout can be marked Cancelled")

    finally:
        delete_user(user_id)


def test_scheduled_workout_cannot_be_completed_without_session():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        try:
            update_scheduled_workout_status(
                scheduled_workout_id,
                "Completed"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Scheduled workout was completed without workout session")

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout["status"] != "Planned":
            raise ValueError("FAIL: Failed completion changed scheduled workout status")

        print("PASS: Scheduled workout cannot fake completion")

    finally:
        delete_user(user_id)


def test_completed_workout_session_links_to_calendar():
    user_id = create_user()

    try:
        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 3,
                    "reps": "8-12",
                    "rest_seconds": 90
                }
            ]
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
            actual_duration_minutes=45
        )

        complete_scheduled_workout(
            scheduled_workout_id,
            workout_session_id
        )

        scheduled_workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if scheduled_workout["status"] != "Completed":
            raise ValueError("FAIL: Scheduled workout did not become Completed")

        if scheduled_workout["workout_session_id"] != workout_session_id:
            raise ValueError("FAIL: Scheduled workout did not link workout session")

        print("PASS: Completed workout session links to calendar workout")

    finally:
        delete_user(user_id)


def test_in_progress_session_cannot_complete_calendar_workout():
    user_id = create_user()

    try:
        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
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

        try:
            complete_scheduled_workout(
                scheduled_workout_id,
                workout_session_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: In-progress session completed calendar workout")

        scheduled_workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if scheduled_workout["status"] != "Planned":
            raise ValueError("FAIL: Failed completion changed calendar status")

        print("PASS: In-progress workout cannot complete calendar workout")

    finally:
        delete_user(user_id)


def test_calendar_rejects_other_users_workout_session():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            first_user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        workout_session_id = start_workout_from_plan(
            second_user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=30
        )

        try:
            complete_scheduled_workout(
                scheduled_workout_id,
                workout_session_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Calendar accepted another user's workout session")

        print("PASS: Calendar rejects another user's workout session")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


def test_calendar_filters_by_status():
    user_id = create_user()

    try:
        first_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        schedule_workout_from_plan(
            user_id,
            "2026-08-26 18:00:00",
            {
                "exercises": []
            }
        )

        update_scheduled_workout_status(
            first_id,
            "Skipped"
        )

        skipped = get_calendar_workouts(
            user_id,
            status="Skipped"
        )

        planned = get_calendar_workouts(
            user_id,
            status="Planned"
        )

        if len(skipped) != 1:
            raise ValueError("FAIL: Calendar returned incorrect Skipped count")

        if len(planned) != 1:
            raise ValueError("FAIL: Calendar returned incorrect Planned count")

        print("PASS: Calendar workouts filter by status")

    finally:
        delete_user(user_id)


def test_invalid_scheduled_datetime_rejected():
    user_id = create_user()

    try:
        invalid_values = [
            "",
            "tomorrow at six",
            "2026/08/25 18:00:00",
            "2026-99-99 18:00:00",
            "2026-08-25T18:00:00+00:00",
            True
        ]

        for value in invalid_values:
            try:
                schedule_workout_from_plan(
                    user_id,
                    value,
                    {
                        "exercises": []
                    }
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid scheduled datetime was accepted: {value}")

        print("PASS: Invalid scheduled workout datetimes rejected")

    finally:
        delete_user(user_id)


def test_invalid_calendar_date_range_rejected():
    user_id = create_user()

    try:
        try:
            get_calendar_workouts(
                user_id,
                start_date="2026-08-30",
                end_date="2026-08-20"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Calendar accepted start date after end date")

        print("PASS: Invalid calendar date range rejected")

    finally:
        delete_user(user_id)


def test_terminal_scheduled_workout_cannot_be_rescheduled():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        update_scheduled_workout_status(
            scheduled_workout_id,
            "Skipped"
        )

        try:
            reschedule_workout(
                scheduled_workout_id,
                "2026-08-30 18:00:00"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Skipped workout was allowed to reschedule")

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout["scheduled_for"] != "2026-08-25 18:00:00":
            raise ValueError("FAIL: Failed reschedule changed workout date")

        print("PASS: Terminal scheduled workout cannot be rescheduled")

    finally:
        delete_user(user_id)


def test_terminal_scheduled_workout_cannot_change_status_again():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "exercises": []
            }
        )

        update_scheduled_workout_status(
            scheduled_workout_id,
            "Skipped"
        )

        try:
            update_scheduled_workout_status(
                scheduled_workout_id,
                "Cancelled"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Terminal scheduled workout changed status twice")

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout["status"] != "Skipped":
            raise ValueError("FAIL: Failed status change modified terminal status")

        print("PASS: Terminal scheduled workout cannot change status again")

    finally:
        delete_user(user_id)


def test_duplicate_workout_session_link_rejected():
    user_id = create_user()

    try:
        plan = {
            "primary_goal": "General Fitness",
            "session_duration_minutes": 45,
            "exercises": []
        }

        first_scheduled_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            plan
        )

        second_scheduled_id = schedule_workout_from_plan(
            user_id,
            "2026-08-27 18:00:00",
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
            first_scheduled_id,
            workout_session_id
        )

        try:
            complete_scheduled_workout(
                second_scheduled_id,
                workout_session_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: One workout session linked to two scheduled workouts")

        second_workout = get_scheduled_workout(
            second_scheduled_id
        )

        if second_workout["status"] != "Planned":
            raise ValueError("FAIL: Duplicate-link failure changed second workout status")

        if second_workout["workout_session_id"] is not None:
            raise ValueError("FAIL: Duplicate-link failure saved workout session ID")

        print("PASS: Duplicate workout-session calendar link rejected")

    finally:
        delete_user(user_id)


def test_delete_planned_scheduled_workout():
    user_id = create_user()

    try:
        scheduled_workout_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            {
                "primary_goal": "Strength",
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 3,
                        "reps": "8-12",
                        "rest_seconds": 90
                    }
                ]
            }
        )

        delete_scheduled_workout(
            scheduled_workout_id
        )

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout is not None:
            raise ValueError("FAIL: Scheduled workout was not deleted")

        connection = get_connection()

        try:
            exercise_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM scheduled_workout_exercises
                WHERE scheduled_workout_id = ?
                """,
                (
                    scheduled_workout_id,
                )
            ).fetchone()[0]

            if exercise_count != 0:
                raise ValueError("FAIL: Scheduled exercises did not cascade after deletion")

        finally:
            connection.close()

        print("PASS: Planned scheduled workout deletes with exercises")

    finally:
        delete_user(user_id)


def test_completed_scheduled_workout_cannot_be_deleted():
    user_id = create_user()

    try:
        plan = {
            "primary_goal": "Strength",
            "session_duration_minutes": 60,
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
            actual_duration_minutes=50
        )

        complete_scheduled_workout(
            scheduled_workout_id,
            workout_session_id
        )

        try:
            delete_scheduled_workout(
                scheduled_workout_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Completed scheduled workout was deleted")

        workout = get_scheduled_workout(
            scheduled_workout_id
        )

        if workout is None:
            raise ValueError("FAIL: Completed scheduled workout disappeared")

        if workout["status"] != "Completed":
            raise ValueError("FAIL: Completed scheduled workout lost status")

        print("PASS: Completed scheduled workout cannot be deleted")

    finally:
        delete_user(user_id)


def test_delete_missing_scheduled_workout_rejected():
    try:
        delete_scheduled_workout(
            999999999
        )

    except ValueError:
        pass

    else:
        raise ValueError("FAIL: Missing scheduled workout deletion was accepted")

    print("PASS: Missing scheduled workout deletion rejected")


def test_invalid_scheduled_exercise_rolls_back_transaction():
    user_id = create_user()

    try:
        try:
            schedule_workout_from_plan(
                user_id,
                "2026-08-25 18:00:00",
                {
                    "primary_goal": "Strength",
                    "session_duration_minutes": 60,
                    "exercises": [
                        {
                            "exercise_id": "E001",
                            "sets": 3,
                            "reps": "8-12",
                            "rest_seconds": 90
                        },
                        {
                            "exercise_id": "E999999",
                            "sets": 3,
                            "reps": "8-12",
                            "rest_seconds": 90
                        }
                    ]
                }
            )

        except (ValueError, sqlite3.IntegrityError):
            pass

        else:
            raise ValueError("FAIL: Invalid scheduled exercise was accepted")

        connection = get_connection()

        try:
            workout_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM scheduled_workouts
                WHERE user_id = ?
                """,
                (
                    user_id,
                )
            ).fetchone()[0]

            exercise_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM scheduled_workout_exercises
                WHERE scheduled_workout_id IN (
                    SELECT scheduled_workout_id
                    FROM scheduled_workouts
                    WHERE user_id = ?
                )
                """,
                (
                    user_id,
                )
            ).fetchone()[0]

            if workout_count != 0:
                raise ValueError("FAIL: Invalid plan left scheduled workout behind")

            if exercise_count != 0:
                raise ValueError("FAIL: Invalid plan left scheduled exercises behind")

        finally:
            connection.close()

        print("PASS: Invalid scheduled exercise rolls back entire transaction")

    finally:
        delete_user(user_id)


def test_invalid_calendar_status_filter_rejected():
    user_id = create_user()

    try:
        try:
            get_calendar_workouts(
                user_id,
                status="Done"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Invalid calendar status filter was accepted")

        print("PASS: Invalid calendar status filter rejected")

    finally:
        delete_user(user_id)


if __name__ == "__main__":
    test_progress_tables_exist()
    test_add_progress_entry()
    test_invalid_body_fat_rejected()
    test_add_body_measurement()
    test_invalid_body_area_rejected()
    test_add_activity_log()
    test_invalid_weight_rejected()
    test_empty_progress_entry_rejected()
    test_invalid_measurement_rejected()
    test_invalid_activity_type_rejected()
    test_invalid_activity_values_rejected()
    test_progress_history_returns_newest_first()
    test_progress_history_limit()
    test_body_measurement_history_filters_area()
    test_activity_history_filters_activity_type()
    test_user_delete_cascades_progress_data()

    test_add_progress_photo()
    test_invalid_progress_photo_path_rejected()
    test_invalid_progress_photo_view_rejected()
    test_invalid_progress_photo_privacy_rejected()
    test_progress_photo_history_filters_view()
    test_delete_progress_photo()

    test_schedule_workout_from_plan()
    test_get_scheduled_workout()
    test_calendar_workouts_filter_date_range()
    test_calendar_workouts_return_chronological_order()
    test_reschedule_workout()
    test_calendar_workouts_are_isolated_by_user()
    test_scheduled_workout_can_be_skipped()
    test_scheduled_workout_can_be_cancelled()
    test_scheduled_workout_cannot_be_completed_without_session()
    test_completed_workout_session_links_to_calendar()
    test_in_progress_session_cannot_complete_calendar_workout()
    test_calendar_rejects_other_users_workout_session()
    test_calendar_filters_by_status()

    test_invalid_scheduled_datetime_rejected()
    test_invalid_calendar_date_range_rejected()
    test_terminal_scheduled_workout_cannot_be_rescheduled()
    test_terminal_scheduled_workout_cannot_change_status_again()
    test_duplicate_workout_session_link_rejected()
    test_delete_planned_scheduled_workout()
    test_completed_scheduled_workout_cannot_be_deleted()
    test_delete_missing_scheduled_workout_rejected()
    test_invalid_scheduled_exercise_rolls_back_transaction()
    test_invalid_calendar_status_filter_rejected()
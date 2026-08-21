from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_progress_database import (
    get_connection
)

from src.database.query_workout_log_database import (
    start_workout_from_plan,
    get_workout_session_exercises,
    log_workout_set,
    finish_workout_session,
    cancel_workout_session
)

from src.analytics.progression_analytics import (
    get_exercise_metadata,
    get_exercise_workout_history,
    get_exercise_progression,
    get_personal_record_history,
    get_exercise_progression_overview,
    get_training_data_quality_analytics,
    get_progression_analytics_overview
)


def set_workout_timestamp(
    workout_session_id,
    timestamp
):
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE workout_sessions
            SET started_at = ?,
                completed_at = ?
            WHERE workout_session_id = ?
            """,
            (
                timestamp,
                timestamp,
                workout_session_id
            )
        )

        connection.commit()

    finally:
        connection.close()


def create_completed_workout(
    user_id,
    exercise_id,
    timestamp,
    set_logs
):
    workout_session_id = start_workout_from_plan(
        user_id,
        {
            "primary_goal": "Strength",
            "exercises": [
                {
                    "exercise_id": exercise_id,
                    "sets": max(
                        1,
                        len(set_logs)
                    ),
                    "reps": "8-12",
                    "rest_seconds": 90
                }
            ]
        }
    )

    exercises = get_workout_session_exercises(
        workout_session_id
    )

    session_exercise_id = exercises[0][
        "session_exercise_id"
    ]

    for set_number, set_data in enumerate(
        set_logs,
        start=1
    ):
        log_workout_set(
            session_exercise_id,
            set_number,
            reps_completed=set_data.get(
                "reps"
            ),
            weight_kg=set_data.get(
                "weight_kg"
            ),
            duration_seconds=set_data.get(
                "duration_seconds"
            )
        )

    finish_workout_session(
        workout_session_id,
        actual_duration_minutes=30
    )

    set_workout_timestamp(
        workout_session_id,
        timestamp
    )

    return workout_session_id


def test_invalid_exercise_id_rejected():
    invalid_values = [
        "",
        "   ",
        None,
        1,
        True
    ]

    for value in invalid_values:
        try:
            get_exercise_metadata(
                value
            )

        except ValueError:
            continue

        raise ValueError(f"FAIL: Invalid exercise ID was accepted: {value}")

    print("PASS: Progression analytics rejects invalid exercise IDs")


def test_missing_exercise_rejected():
    try:
        get_exercise_metadata(
            "E999999"
        )

    except ValueError:
        print("PASS: Progression analytics rejects missing exercises")
        return

    raise ValueError("FAIL: Missing exercise was accepted")


def test_empty_exercise_progression():
    user_id = create_user()

    try:
        progression = get_exercise_progression(
            user_id,
            "E001"
        )

        if progression["workout_count"] != 0:
            raise ValueError("FAIL: Empty progression returned workouts")

        if progression["latest_max_weight_kg"] is not None:
            raise ValueError("FAIL: Empty progression returned latest weight")

        if progression["workouts"] != []:
            raise ValueError("FAIL: Empty progression returned workout history")

        print("PASS: Empty exercise progression returns correct defaults")

    finally:
        delete_user(user_id)


def test_exercise_workout_history_is_chronological():
    user_id = create_user()

    try:
        first_id = create_completed_workout(
            user_id,
            "E001",
            "2026-08-01 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 40
                }
            ]
        )

        second_id = create_completed_workout(
            user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 50
                }
            ]
        )

        history = get_exercise_workout_history(
            user_id,
            "E001"
        )

        if history[0]["workout_session_id"] != first_id:
            raise ValueError("FAIL: Exercise progression did not return oldest workout first")

        if history[1]["workout_session_id"] != second_id:
            raise ValueError("FAIL: Exercise progression did not return latest workout last")

        print("PASS: Exercise progression history returns chronological workouts")

    finally:
        delete_user(user_id)


def test_exercise_progression_calculates_changes():
    user_id = create_user()

    try:
        create_completed_workout(
            user_id,
            "E001",
            "2026-08-01 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 40
                }
            ]
        )

        create_completed_workout(
            user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 60
                }
            ]
        )

        progression = get_exercise_progression(
            user_id,
            "E001"
        )

        if progression["workout_count"] != 2:
            raise ValueError("FAIL: Exercise progression returned incorrect workout count")

        if progression["first_max_weight_kg"] != 40:
            raise ValueError("FAIL: Exercise progression returned incorrect first weight")

        if progression["latest_max_weight_kg"] != 60:
            raise ValueError("FAIL: Exercise progression returned incorrect latest weight")

        if progression["max_weight_change_kg"] != 20:
            raise ValueError("FAIL: Exercise progression returned incorrect weight change")

        if progression["first_total_volume_kg"] != 400:
            raise ValueError("FAIL: Exercise progression returned incorrect first volume")

        if progression["latest_total_volume_kg"] != 600:
            raise ValueError("FAIL: Exercise progression returned incorrect latest volume")

        if progression["volume_change_kg"] != 200:
            raise ValueError("FAIL: Exercise progression returned incorrect volume change")

        print("PASS: Exercise progression calculates first-to-latest changes")

    finally:
        delete_user(user_id)


def test_exercise_progression_tracks_all_time_maximums():
    user_id = create_user()

    try:
        create_completed_workout(
            user_id,
            "E001",
            "2026-08-01 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 40
                }
            ]
        )

        create_completed_workout(
            user_id,
            "E001",
            "2026-08-10 10:00:00",
            [
                {
                    "reps": 8,
                    "weight_kg": 70
                }
            ]
        )

        create_completed_workout(
            user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 15,
                    "weight_kg": 50
                }
            ]
        )

        progression = get_exercise_progression(
            user_id,
            "E001"
        )

        if progression["all_time_max_weight_kg"] != 70:
            raise ValueError("FAIL: Progression returned incorrect all-time weight record")

        if progression["all_time_max_reps_completed"] != 15:
            raise ValueError("FAIL: Progression returned incorrect all-time rep record")

        if progression["all_time_max_set_volume_kg"] != 750:
            raise ValueError("FAIL: Progression returned incorrect all-time set-volume record")

        print("PASS: Exercise progression tracks all-time performance maximums")

    finally:
        delete_user(user_id)


def test_bodyweight_progression_does_not_invent_weight():
    user_id = create_user()

    try:
        create_completed_workout(
            user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 15
                }
            ]
        )

        progression = get_exercise_progression(
            user_id,
            "E001"
        )

        if progression["latest_max_weight_kg"] is not None:
            raise ValueError("FAIL: Bodyweight progression invented external weight")

        if progression["latest_total_volume_kg"] != 0:
            raise ValueError("FAIL: Bodyweight progression invented weighted volume")

        if progression["all_time_max_reps_completed"] != 15:
            raise ValueError("FAIL: Bodyweight progression failed to track reps")

        print("PASS: Bodyweight progression tracks reps without invented weight")

    finally:
        delete_user(user_id)


def test_cancelled_workouts_are_excluded_from_progression():
    user_id = create_user()

    try:
        create_completed_workout(
            user_id,
            "E001",
            "2026-08-01 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 50
                }
            ]
        )

        cancelled_id = start_workout_from_plan(
            user_id,
            {
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 1,
                        "reps": "10",
                        "rest_seconds": 60
                    }
                ]
            }
        )

        exercises = get_workout_session_exercises(
            cancelled_id
        )

        log_workout_set(
            exercises[0]["session_exercise_id"],
            1,
            reps_completed=20,
            weight_kg=100
        )

        cancel_workout_session(
            cancelled_id
        )

        progression = get_exercise_progression(
            user_id,
            "E001"
        )

        if progression["workout_count"] != 1:
            raise ValueError("FAIL: Cancelled workout entered progression history")

        if progression["all_time_max_weight_kg"] != 50:
            raise ValueError("FAIL: Cancelled workout created progression weight record")

        print("PASS: Exercise progression uses completed workouts only")

    finally:
        delete_user(user_id)


def test_personal_record_history_detects_improvements():
    user_id = create_user()

    try:
        create_completed_workout(
            user_id,
            "E001",
            "2026-08-01 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 40
                }
            ]
        )

        create_completed_workout(
            user_id,
            "E001",
            "2026-08-10 10:00:00",
            [
                {
                    "reps": 8,
                    "weight_kg": 50
                }
            ]
        )

        create_completed_workout(
            user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 12,
                    "weight_kg": 45
                }
            ]
        )

        records = get_personal_record_history(
            user_id,
            "E001"
        )

        weight_records = [
            event
            for event in records
            if event["metric"] == "max_weight_kg"
        ]

        rep_records = [
            event
            for event in records
            if event["metric"] == "max_reps_completed"
        ]

        if len(weight_records) != 2:
            raise ValueError("FAIL: Personal-record history returned incorrect weight-record count")

        if weight_records[-1]["value"] != 50:
            raise ValueError("FAIL: Personal-record history returned incorrect latest weight record")

        if weight_records[-1]["improvement"] != 10:
            raise ValueError("FAIL: Personal-record history returned incorrect weight improvement")

        if rep_records[-1]["value"] != 12:
            raise ValueError("FAIL: Personal-record history returned incorrect rep record")

        print("PASS: Personal-record history detects new performance records")

    finally:
        delete_user(user_id)


def test_personal_record_history_ignores_non_records():
    user_id = create_user()

    try:
        create_completed_workout(
            user_id,
            "E001",
            "2026-08-01 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 60
                }
            ]
        )

        create_completed_workout(
            user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 8,
                    "weight_kg": 50
                }
            ]
        )

        records = get_personal_record_history(
            user_id,
            "E001"
        )

        weight_records = [
            event
            for event in records
            if event["metric"] == "max_weight_kg"
        ]

        if len(weight_records) != 1:
            raise ValueError("FAIL: Lower later weight was incorrectly treated as a PR")

        print("PASS: Personal-record history ignores non-record performances")

    finally:
        delete_user(user_id)


def test_exercise_progression_overview():
    user_id = create_user()

    try:
        create_completed_workout(
            user_id,
            "E001",
            "2026-08-19 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 40
                }
            ]
        )

        create_completed_workout(
            user_id,
            "E002",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 5,
                    "weight_kg": 80
                }
            ]
        )

        overview = get_exercise_progression_overview(
            user_id
        )

        exercise_ids = {
            item["exercise_id"]
            for item in overview
        }

        if exercise_ids != {
            "E001",
            "E002"
        }:
            raise ValueError("FAIL: Exercise progression overview returned incorrect exercises")

        print("PASS: Exercise progression overview summarizes trained exercises")

    finally:
        delete_user(user_id)


def test_progression_analytics_are_isolated_by_user():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        create_completed_workout(
            first_user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 50
                }
            ]
        )

        progression = get_exercise_progression(
            second_user_id,
            "E001"
        )

        if progression["workout_count"] != 0:
            raise ValueError("FAIL: Progression analytics leaked another user's workouts")

        print("PASS: Exercise progression analytics are isolated by user")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


def test_empty_training_data_quality():
    user_id = create_user()

    try:
        analytics = get_training_data_quality_analytics(
            user_id
        )

        if analytics["completed_workout_count"] != 0:
            raise ValueError("FAIL: Empty data-quality analytics returned workouts")

        if analytics["exercise_occurrence_count"] != 0:
            raise ValueError("FAIL: Empty data-quality analytics returned exercises")

        if analytics["performance_log_count"] != 0:
            raise ValueError("FAIL: Empty data-quality analytics returned logs")

        if analytics["exercise_log_coverage_percentage"] != 0.0:
            raise ValueError("FAIL: Empty data-quality analytics returned coverage")

        print("PASS: Empty training data-quality analytics returns correct defaults")

    finally:
        delete_user(user_id)


def test_training_data_quality_detects_missing_logs():
    user_id = create_user()

    try:
        logged_id = start_workout_from_plan(
            user_id,
            {
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 1,
                        "reps": "10",
                        "rest_seconds": 60
                    }
                ]
            }
        )

        logged_exercises = get_workout_session_exercises(
            logged_id
        )

        log_workout_set(
            logged_exercises[0]["session_exercise_id"],
            1,
            reps_completed=10,
            weight_kg=50
        )

        finish_workout_session(
            logged_id,
            actual_duration_minutes=20
        )

        unlogged_id = start_workout_from_plan(
            user_id,
            {
                "exercises": [
                    {
                        "exercise_id": "E002",
                        "sets": 1,
                        "reps": "5",
                        "rest_seconds": 120
                    }
                ]
            }
        )

        finish_workout_session(
            unlogged_id,
            actual_duration_minutes=20
        )

        analytics = get_training_data_quality_analytics(
            user_id
        )

        if analytics["exercise_occurrence_count"] != 2:
            raise ValueError("FAIL: Data-quality analytics returned incorrect exercise count")

        if analytics["exercise_occurrence_with_logs_count"] != 1:
            raise ValueError("FAIL: Data-quality analytics returned incorrect logged-exercise count")

        if analytics["exercise_occurrence_without_logs_count"] != 1:
            raise ValueError("FAIL: Data-quality analytics failed to detect missing logs")

        if analytics["exercise_log_coverage_percentage"] != 50.0:
            raise ValueError("FAIL: Data-quality analytics returned incorrect coverage percentage")

        if analytics["weighted_rep_log_count"] != 1:
            raise ValueError("FAIL: Data-quality analytics returned incorrect weighted log count")

        print("PASS: Training data-quality analytics detects missing exercise logs")

    finally:
        delete_user(user_id)


def test_training_data_quality_detects_empty_completed_workout():
    user_id = create_user()

    try:
        workout_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=20
        )

        analytics = get_training_data_quality_analytics(
            user_id
        )

        if analytics["completed_workout_count"] != 1:
            raise ValueError("FAIL: Data-quality analytics returned incorrect completed count")

        if analytics["completed_workout_without_exercises_count"] != 1:
            raise ValueError("FAIL: Data-quality analytics failed to detect empty workout")

        print("PASS: Training data-quality analytics detects completed workouts without exercises")

    finally:
        delete_user(user_id)


def test_progression_overview_contains_all_sections():
    user_id = create_user()

    try:
        overview = get_progression_analytics_overview(
            user_id
        )

        expected_sections = {
            "exercise_progression",
            "data_quality"
        }

        if set(overview.keys()) != expected_sections:
            raise ValueError("FAIL: Progression overview returned incorrect sections")

        print("PASS: Progression analytics overview combines final Stage 10 sections")

    finally:
        delete_user(user_id)


if __name__ == "__main__":
    test_invalid_exercise_id_rejected()
    test_missing_exercise_rejected()
    test_empty_exercise_progression()
    test_exercise_workout_history_is_chronological()
    test_exercise_progression_calculates_changes()
    test_exercise_progression_tracks_all_time_maximums()
    test_bodyweight_progression_does_not_invent_weight()
    test_cancelled_workouts_are_excluded_from_progression()
    test_personal_record_history_detects_improvements()
    test_personal_record_history_ignores_non_records()
    test_exercise_progression_overview()
    test_progression_analytics_are_isolated_by_user()
    test_empty_training_data_quality()
    test_training_data_quality_detects_missing_logs()
    test_training_data_quality_detects_empty_completed_workout()
    test_progression_overview_contains_all_sections()
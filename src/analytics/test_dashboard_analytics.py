from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_progress_database import (
    get_connection,
    add_progress_entry,
    add_body_measurement,
    add_activity_log
)

from src.database.query_workout_log_database import (
    start_workout_from_plan,
    get_workout_session_exercises,
    log_workout_set,
    finish_workout_session
)

from src.database.query_exercise_database import (
    get_exercise_by_id
)

from src.analytics.dashboard_analytics import (
    get_weight_chart_series,
    get_body_measurement_chart_series,
    get_activity_daily_series,
    get_weekly_training_volume_series,
    get_muscle_distribution,
    get_personal_records,
    get_dashboard_analytics
)


REFERENCE_DATE = "2026-08-21"


def set_database_timestamp(
    table_name,
    id_column,
    record_id,
    timestamp_column,
    timestamp_value
):
    allowed_tables = {
        "progress_entries",
        "body_measurements",
        "activity_logs",
        "workout_sessions"
    }

    allowed_id_columns = {
        "progress_entry_id",
        "body_measurement_id",
        "activity_log_id",
        "workout_session_id"
    }

    allowed_timestamp_columns = {
        "recorded_at",
        "started_at",
        "completed_at"
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid test table")

    if id_column not in allowed_id_columns:
        raise ValueError("Invalid test ID column")

    if timestamp_column not in allowed_timestamp_columns:
        raise ValueError("Invalid test timestamp column")

    connection = get_connection()

    try:
        connection.execute(
            f"""
            UPDATE {table_name}
            SET {timestamp_column} = ?
            WHERE {id_column} = ?
            """,
            (
                timestamp_value,
                record_id
            )
        )

        connection.commit()

    finally:
        connection.close()


def create_completed_weighted_workout(
    user_id,
    exercise_id,
    started_at,
    set_logs
):
    workout_session_id = start_workout_from_plan(
        user_id,
        {
            "primary_goal": "Strength",
            "exercises": [
                {
                    "exercise_id": exercise_id,
                    "sets": len(set_logs),
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
            reps_completed=set_data["reps"],
            weight_kg=set_data.get(
                "weight_kg"
            )
        )

    finish_workout_session(
        workout_session_id,
        actual_duration_minutes=30
    )

    set_database_timestamp(
        "workout_sessions",
        "workout_session_id",
        workout_session_id,
        "started_at",
        started_at
    )

    set_database_timestamp(
        "workout_sessions",
        "workout_session_id",
        workout_session_id,
        "completed_at",
        started_at
    )

    return workout_session_id


def test_weight_chart_series_returns_oldest_first():
    user_id = create_user()

    try:
        first_id = add_progress_entry(
            user_id,
            weight_kg=82
        )

        second_id = add_progress_entry(
            user_id,
            weight_kg=80
        )

        set_database_timestamp(
            "progress_entries",
            "progress_entry_id",
            first_id,
            "recorded_at",
            "2026-08-01 08:00:00"
        )

        set_database_timestamp(
            "progress_entries",
            "progress_entry_id",
            second_id,
            "recorded_at",
            "2026-08-20 08:00:00"
        )

        series = get_weight_chart_series(
            user_id
        )

        if len(series) != 2:
            raise ValueError("FAIL: Weight chart returned incorrect number of points")

        if series[0]["weight_kg"] != 82:
            raise ValueError("FAIL: Weight chart did not return oldest point first")

        if series[1]["weight_kg"] != 80:
            raise ValueError("FAIL: Weight chart did not return newest point last")

        print("PASS: Weight chart series returns chronological data")

    finally:
        delete_user(user_id)


def test_weight_chart_series_filters_date_window():
    user_id = create_user()

    try:
        recent_id = add_progress_entry(
            user_id,
            weight_kg=80
        )

        old_id = add_progress_entry(
            user_id,
            weight_kg=85
        )

        set_database_timestamp(
            "progress_entries",
            "progress_entry_id",
            recent_id,
            "recorded_at",
            "2026-08-20 08:00:00"
        )

        set_database_timestamp(
            "progress_entries",
            "progress_entry_id",
            old_id,
            "recorded_at",
            "2026-01-01 08:00:00"
        )

        series = get_weight_chart_series(
            user_id,
            days=30,
            reference_date=REFERENCE_DATE
        )

        if len(series) != 1:
            raise ValueError("FAIL: Weight chart date window returned incorrect number of points")

        if series[0]["weight_kg"] != 80:
            raise ValueError("FAIL: Weight chart date window returned incorrect point")

        print("PASS: Weight chart series filters rolling date window")

    finally:
        delete_user(user_id)


def test_body_measurement_chart_series():
    user_id = create_user()

    try:
        first_id = add_body_measurement(
            user_id,
            "Waist",
            86
        )

        second_id = add_body_measurement(
            user_id,
            "Waist",
            84
        )

        set_database_timestamp(
            "body_measurements",
            "body_measurement_id",
            first_id,
            "recorded_at",
            "2026-08-01 08:00:00"
        )

        set_database_timestamp(
            "body_measurements",
            "body_measurement_id",
            second_id,
            "recorded_at",
            "2026-08-20 08:00:00"
        )

        series = get_body_measurement_chart_series(
            user_id,
            "Waist"
        )

        if len(series) != 2:
            raise ValueError("FAIL: Measurement chart returned incorrect number of points")

        if series[0]["measurement_cm"] != 86:
            raise ValueError("FAIL: Measurement chart returned incorrect earliest value")

        if series[1]["measurement_cm"] != 84:
            raise ValueError("FAIL: Measurement chart returned incorrect latest value")

        print("PASS: Body measurement chart series returns chronological values")

    finally:
        delete_user(user_id)


def test_activity_daily_series_includes_zero_days():
    user_id = create_user()

    try:
        activity_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=30,
            distance_km=2,
            steps=3000,
            estimated_calories=150
        )

        set_database_timestamp(
            "activity_logs",
            "activity_log_id",
            activity_id,
            "started_at",
            "2026-08-20 10:00:00"
        )

        series = get_activity_daily_series(
            user_id,
            days=3,
            reference_date=REFERENCE_DATE
        )

        if len(series) != 3:
            raise ValueError("FAIL: Daily activity chart did not include every day")

        if series[0]["date"] != "2026-08-19":
            raise ValueError("FAIL: Daily activity chart returned incorrect start date")

        if series[0]["steps"] != 0:
            raise ValueError("FAIL: Empty activity day did not return zero steps")

        if series[1]["steps"] != 3000:
            raise ValueError("FAIL: Activity day returned incorrect steps")

        if series[2]["steps"] != 0:
            raise ValueError("FAIL: Final empty activity day did not return zero steps")

        print("PASS: Activity chart fills missing days with zero values")

    finally:
        delete_user(user_id)


def test_activity_daily_series_combines_same_day_activity():
    user_id = create_user()

    try:
        first_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=20,
            distance_km=1.5,
            steps=2000,
            estimated_calories=100
        )

        second_id = add_activity_log(
            user_id,
            "Running",
            duration_minutes=30,
            distance_km=5,
            steps=4000,
            estimated_calories=300
        )

        for activity_id in [
            first_id,
            second_id
        ]:
            set_database_timestamp(
                "activity_logs",
                "activity_log_id",
                activity_id,
                "started_at",
                "2026-08-20 10:00:00"
            )

        series = get_activity_daily_series(
            user_id,
            days=2,
            reference_date=REFERENCE_DATE
        )

        day = series[0]

        if day["date"] != "2026-08-20":
            raise ValueError("FAIL: Combined activity returned incorrect date")

        if day["activity_count"] != 2:
            raise ValueError("FAIL: Same-day activity count was incorrect")

        if day["duration_minutes"] != 50:
            raise ValueError("FAIL: Same-day duration total was incorrect")

        if day["distance_km"] != 6.5:
            raise ValueError("FAIL: Same-day distance total was incorrect")

        if day["steps"] != 6000:
            raise ValueError("FAIL: Same-day step total was incorrect")

        if day["estimated_calories"] != 400:
            raise ValueError("FAIL: Same-day estimated calories were incorrect")

        print("PASS: Activity chart aggregates multiple activities per day")

    finally:
        delete_user(user_id)


def test_weekly_training_volume_series():
    user_id = create_user()

    try:
        create_completed_weighted_workout(
            user_id,
            "E001",
            "2026-08-10 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 50
                }
            ]
        )

        create_completed_weighted_workout(
            user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 75
                }
            ]
        )

        series = get_weekly_training_volume_series(
            user_id,
            weeks=2,
            reference_date=REFERENCE_DATE
        )

        if len(series) != 2:
            raise ValueError("FAIL: Weekly training volume returned incorrect bucket count")

        if series[0]["total_volume_kg"] != 500:
            raise ValueError("FAIL: First training-volume week returned incorrect volume")

        if series[1]["total_volume_kg"] != 750:
            raise ValueError("FAIL: Second training-volume week returned incorrect volume")

        if series[0]["workout_count"] != 1:
            raise ValueError("FAIL: First training-volume week returned incorrect workout count")

        if series[1]["workout_count"] != 1:
            raise ValueError("FAIL: Second training-volume week returned incorrect workout count")

        print("PASS: Weekly training-volume chart aggregates completed workouts")

    finally:
        delete_user(user_id)


def test_invalid_week_count_rejected():
    user_id = create_user()

    try:
        invalid_values = [
            0,
            -1,
            True,
            1.5,
            "8"
        ]

        for value in invalid_values:
            try:
                get_weekly_training_volume_series(
                    user_id,
                    weeks=value,
                    reference_date=REFERENCE_DATE
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid dashboard week count was accepted: {value}")

        print("PASS: Dashboard analytics rejects invalid week counts")

    finally:
        delete_user(user_id)


def test_muscle_distribution_uses_exercise_occurrences():
    user_id = create_user()

    try:
        first_exercise = get_exercise_by_id(
            "E001"
        )

        second_exercise = get_exercise_by_id(
            "E002"
        )

        if (
            first_exercise["primary_muscle"]
            == second_exercise["primary_muscle"]
        ):
            raise ValueError("FAIL: Test requires exercises with different primary muscles")

        create_completed_weighted_workout(
            user_id,
            "E001",
            "2026-08-18 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 20
                }
            ]
        )

        create_completed_weighted_workout(
            user_id,
            "E001",
            "2026-08-19 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 20
                }
            ]
        )

        create_completed_weighted_workout(
            user_id,
            "E002",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 5,
                    "weight_kg": 100
                }
            ]
        )

        distribution = get_muscle_distribution(
            user_id
        )

        first_muscle = next(
            item
            for item in distribution
            if (
                item["primary_muscle"]
                == first_exercise["primary_muscle"]
            )
        )

        second_muscle = next(
            item
            for item in distribution
            if (
                item["primary_muscle"]
                == second_exercise["primary_muscle"]
            )
        )

        if first_muscle["exercise_occurrence_count"] != 2:
            raise ValueError("FAIL: Muscle distribution returned incorrect first occurrence count")

        if second_muscle["exercise_occurrence_count"] != 1:
            raise ValueError("FAIL: Muscle distribution returned incorrect second occurrence count")

        if first_muscle["distribution_percentage"] != 66.67:
            raise ValueError("FAIL: Muscle distribution returned incorrect first percentage")

        if second_muscle["distribution_percentage"] != 33.33:
            raise ValueError("FAIL: Muscle distribution returned incorrect second percentage")

        print("PASS: Muscle distribution uses exercise-selection frequency")

    finally:
        delete_user(user_id)


def test_personal_records_detect_maximums():
    user_id = create_user()

    try:
        create_completed_weighted_workout(
            user_id,
            "E001",
            "2026-08-20 10:00:00",
            [
                {
                    "reps": 10,
                    "weight_kg": 50
                },
                {
                    "reps": 8,
                    "weight_kg": 70
                },
                {
                    "reps": 15,
                    "weight_kg": 40
                }
            ]
        )

        records = get_personal_records(
            user_id
        )

        record = next(
            item
            for item in records
            if item["exercise_id"] == "E001"
        )

        if record["max_weight_kg"] != 70:
            raise ValueError("FAIL: Personal record returned incorrect maximum weight")

        if record["max_reps_completed"] != 15:
            raise ValueError("FAIL: Personal record returned incorrect maximum reps")

        if record["max_set_volume_kg"] != 600:
            raise ValueError("FAIL: Personal record returned incorrect maximum set volume")

        print("PASS: Personal-record analytics detects exercise maximums")

    finally:
        delete_user(user_id)


def test_personal_records_ignore_cancelled_workouts():
    user_id = create_user()

    try:
        completed_session_id = start_workout_from_plan(
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

        completed_exercises = get_workout_session_exercises(
            completed_session_id
        )

        log_workout_set(
            completed_exercises[0]["session_exercise_id"],
            1,
            reps_completed=10,
            weight_kg=50
        )

        finish_workout_session(
            completed_session_id,
            actual_duration_minutes=20
        )

        cancelled_session_id = start_workout_from_plan(
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

        cancelled_exercises = get_workout_session_exercises(
            cancelled_session_id
        )

        log_workout_set(
            cancelled_exercises[0]["session_exercise_id"],
            1,
            reps_completed=20,
            weight_kg=100
        )

        connection = get_connection()

        try:
            connection.execute(
                """
                UPDATE workout_sessions
                SET status = 'Cancelled'
                WHERE workout_session_id = ?
                """,
                (
                    cancelled_session_id,
                )
            )

            connection.commit()

        finally:
            connection.close()

        records = get_personal_records(
            user_id
        )

        record = next(
            item
            for item in records
            if item["exercise_id"] == "E001"
        )

        if record["max_weight_kg"] != 50:
            raise ValueError("FAIL: Cancelled workout created a personal weight record")

        if record["max_reps_completed"] != 10:
            raise ValueError("FAIL: Cancelled workout created a personal rep record")

        print("PASS: Personal records use completed workouts only")

    finally:
        delete_user(user_id)


def test_empty_personal_records():
    user_id = create_user()

    try:
        records = get_personal_records(
            user_id
        )

        if records != []:
            raise ValueError("FAIL: Empty user returned personal records")

        print("PASS: Empty user returns no personal records")

    finally:
        delete_user(user_id)


def test_dashboard_payload_contains_all_sections():
    user_id = create_user()

    try:
        dashboard = get_dashboard_analytics(
            user_id,
            reference_date=REFERENCE_DATE
        )

        expected_sections = {
            "reference_date",
            "overview",
            "training",
            "trends",
            "charts",
            "muscle_distribution",
            "personal_records"
        }

        if set(dashboard.keys()) != expected_sections:
            raise ValueError("FAIL: Dashboard payload returned incorrect top-level sections")

        expected_charts = {
            "weight_90_days",
            "activity_30_days",
            "training_volume_8_weeks"
        }

        if set(dashboard["charts"].keys()) != expected_charts:
            raise ValueError("FAIL: Dashboard payload returned incorrect chart sections")

        if dashboard["reference_date"] != REFERENCE_DATE:
            raise ValueError("FAIL: Dashboard payload returned incorrect reference date")

        print("PASS: Dashboard analytics combines frontend-ready sections")

    finally:
        delete_user(user_id)


def test_dashboard_analytics_are_isolated_by_user():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        progress_id = add_progress_entry(
            first_user_id,
            weight_kg=80
        )

        set_database_timestamp(
            "progress_entries",
            "progress_entry_id",
            progress_id,
            "recorded_at",
            "2026-08-20 08:00:00"
        )

        dashboard = get_dashboard_analytics(
            second_user_id,
            reference_date=REFERENCE_DATE
        )

        if dashboard["charts"]["weight_90_days"] != []:
            raise ValueError("FAIL: Dashboard leaked another user's weight data")

        if dashboard["personal_records"] != []:
            raise ValueError("FAIL: Dashboard leaked another user's training records")

        if dashboard["muscle_distribution"] != []:
            raise ValueError("FAIL: Dashboard leaked another user's muscle analytics")

        print("PASS: Dashboard analytics are isolated by user")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


if __name__ == "__main__":
    test_weight_chart_series_returns_oldest_first()
    test_weight_chart_series_filters_date_window()
    test_body_measurement_chart_series()
    test_activity_daily_series_includes_zero_days()
    test_activity_daily_series_combines_same_day_activity()
    test_weekly_training_volume_series()
    test_invalid_week_count_rejected()
    test_muscle_distribution_uses_exercise_occurrences()
    test_personal_records_detect_maximums()
    test_personal_records_ignore_cancelled_workouts()
    test_empty_personal_records()
    test_dashboard_payload_contains_all_sections()
    test_dashboard_analytics_are_isolated_by_user()
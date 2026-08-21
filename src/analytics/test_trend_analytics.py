from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_progress_database import (
    get_connection,
    add_progress_entry,
    add_body_measurement,
    add_activity_log,
    schedule_workout_from_plan,
    update_scheduled_workout_status,
    complete_scheduled_workout
)

from src.database.query_workout_log_database import (
    start_workout_from_plan,
    get_workout_session_exercises,
    log_workout_set,
    finish_workout_session,
    cancel_workout_session
)

from src.analytics.trend_analytics import (
    get_window_dates,
    get_activity_window_analytics,
    get_standard_activity_windows,
    get_workout_frequency_trend,
    get_volume_trend,
    get_weight_trend,
    get_measurement_trend,
    get_calendar_adherence_trend,
    get_trend_analytics_overview
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
    started_at,
    reps,
    weight_kg
):
    workout_session_id = start_workout_from_plan(
        user_id,
        {
            "primary_goal": "Strength",
            "exercises": [
                {
                    "exercise_id": "E001",
                    "sets": 1,
                    "reps": "8-12",
                    "rest_seconds": 90
                }
            ]
        }
    )

    exercises = get_workout_session_exercises(
        workout_session_id
    )

    log_workout_set(
        exercises[0]["session_exercise_id"],
        1,
        reps_completed=reps,
        weight_kg=weight_kg
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


def test_invalid_window_days_rejected():
    invalid_values = [
        0,
        -1,
        True,
        7.5,
        "30"
    ]

    for value in invalid_values:
        try:
            get_window_dates(
                value,
                REFERENCE_DATE
            )

        except ValueError:
            continue

        raise ValueError(f"FAIL: Invalid analytics window was accepted: {value}")

    print("PASS: Trend analytics rejects invalid window sizes")


def test_invalid_reference_date_rejected():
    invalid_values = [
        "",
        "21-08-2026",
        "2026/08/21",
        "2026-99-99",
        True
    ]

    for value in invalid_values:
        try:
            get_window_dates(
                30,
                value
            )

        except ValueError:
            continue

        raise ValueError(f"FAIL: Invalid reference date was accepted: {value}")

    print("PASS: Trend analytics rejects invalid reference dates")


def test_activity_window_filters_by_date():
    user_id = create_user()

    try:
        recent_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=30,
            distance_km=2,
            steps=3000,
            estimated_calories=100
        )

        older_id = add_activity_log(
            user_id,
            "Running",
            duration_minutes=20,
            distance_km=4,
            steps=2000,
            estimated_calories=200
        )

        outside_id = add_activity_log(
            user_id,
            "Cycling",
            duration_minutes=60,
            distance_km=20,
            estimated_calories=400
        )

        set_database_timestamp(
            "activity_logs",
            "activity_log_id",
            recent_id,
            "started_at",
            "2026-08-20 10:00:00"
        )

        set_database_timestamp(
            "activity_logs",
            "activity_log_id",
            older_id,
            "started_at",
            "2026-08-10 10:00:00"
        )

        set_database_timestamp(
            "activity_logs",
            "activity_log_id",
            outside_id,
            "started_at",
            "2026-05-01 10:00:00"
        )

        analytics = get_activity_window_analytics(
            user_id,
            7,
            REFERENCE_DATE
        )

        if analytics["activity_count"] != 1:
            raise ValueError("FAIL: Seven-day activity window returned incorrect count")

        if analytics["total_duration_minutes"] != 30:
            raise ValueError("FAIL: Seven-day activity window returned incorrect duration")

        if analytics["total_steps"] != 3000:
            raise ValueError("FAIL: Seven-day activity window returned incorrect steps")

        if analytics["average_daily_steps"] != 428.57:
            raise ValueError("FAIL: Seven-day activity window returned incorrect daily step average")

        print("PASS: Activity analytics filters data by rolling date window")

    finally:
        delete_user(user_id)


def test_standard_activity_windows():
    user_id = create_user()

    try:
        first_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=10,
            steps=1000
        )

        second_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=20,
            steps=2000
        )

        third_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=30,
            steps=3000
        )

        set_database_timestamp(
            "activity_logs",
            "activity_log_id",
            first_id,
            "started_at",
            "2026-08-20 10:00:00"
        )

        set_database_timestamp(
            "activity_logs",
            "activity_log_id",
            second_id,
            "started_at",
            "2026-08-10 10:00:00"
        )

        set_database_timestamp(
            "activity_logs",
            "activity_log_id",
            third_id,
            "started_at",
            "2026-06-15 10:00:00"
        )

        windows = get_standard_activity_windows(
            user_id,
            REFERENCE_DATE
        )

        if windows["7_days"]["activity_count"] != 1:
            raise ValueError("FAIL: Seven-day standard window returned incorrect count")

        if windows["30_days"]["activity_count"] != 2:
            raise ValueError("FAIL: Thirty-day standard window returned incorrect count")

        if windows["90_days"]["activity_count"] != 3:
            raise ValueError("FAIL: Ninety-day standard window returned incorrect count")

        print("PASS: Standard activity analytics builds 7, 30 and 90-day windows")

    finally:
        delete_user(user_id)


def test_workout_frequency_builds_weekly_buckets():
    user_id = create_user()

    try:
        workout_dates = [
            "2026-07-26 10:00:00",
            "2026-08-02 10:00:00",
            "2026-08-03 10:00:00",
            "2026-08-20 10:00:00"
        ]

        for started_at in workout_dates:
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

            set_database_timestamp(
                "workout_sessions",
                "workout_session_id",
                workout_session_id,
                "started_at",
                started_at
            )

        analytics = get_workout_frequency_trend(
            user_id,
            days=28,
            reference_date=REFERENCE_DATE
        )

        counts = [
            bucket["completed_workout_count"]
            for bucket in analytics["weekly_completed_counts"]
        ]

        if counts != [1, 2, 0, 1]:
            raise ValueError("FAIL: Workout frequency returned incorrect weekly buckets")

        if analytics["completed_workout_count"] != 4:
            raise ValueError("FAIL: Workout frequency returned incorrect completed count")

        if analytics["training_day_count"] != 4:
            raise ValueError("FAIL: Workout frequency returned incorrect training-day count")

        if analytics["weeks_with_training"] != 3:
            raise ValueError("FAIL: Workout frequency returned incorrect active-week count")

        if analytics["weekly_consistency_percentage"] != 75.0:
            raise ValueError("FAIL: Workout frequency returned incorrect consistency percentage")

        if analytics["average_workouts_per_week"] != 1.0:
            raise ValueError("FAIL: Workout frequency returned incorrect weekly average")

        print("PASS: Workout frequency builds rolling weekly consistency buckets")

    finally:
        delete_user(user_id)


def test_cancelled_workouts_do_not_count_toward_frequency():
    user_id = create_user()

    try:
        completed_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            completed_id,
            actual_duration_minutes=30
        )

        set_database_timestamp(
            "workout_sessions",
            "workout_session_id",
            completed_id,
            "started_at",
            "2026-08-20 10:00:00"
        )

        cancelled_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        cancel_workout_session(
            cancelled_id
        )

        set_database_timestamp(
            "workout_sessions",
            "workout_session_id",
            cancelled_id,
            "started_at",
            "2026-08-20 12:00:00"
        )

        analytics = get_workout_frequency_trend(
            user_id,
            days=7,
            reference_date=REFERENCE_DATE
        )

        if analytics["completed_workout_count"] != 1:
            raise ValueError("FAIL: Cancelled workout entered workout-frequency analytics")

        print("PASS: Workout frequency counts completed workouts only")

    finally:
        delete_user(user_id)


def test_volume_trend_compares_equal_periods():
    user_id = create_user()

    try:
        create_completed_weighted_workout(
            user_id,
            "2026-08-10 10:00:00",
            reps=10,
            weight_kg=50
        )

        create_completed_weighted_workout(
            user_id,
            "2026-08-20 10:00:00",
            reps=10,
            weight_kg=75
        )

        analytics = get_volume_trend(
            user_id,
            days=7,
            reference_date=REFERENCE_DATE
        )

        if analytics["previous_volume_kg"] != 500:
            raise ValueError("FAIL: Volume trend returned incorrect previous volume")

        if analytics["current_volume_kg"] != 750:
            raise ValueError("FAIL: Volume trend returned incorrect current volume")

        if analytics["volume_change_kg"] != 250:
            raise ValueError("FAIL: Volume trend returned incorrect absolute volume change")

        if analytics["volume_change_percentage"] != 50.0:
            raise ValueError("FAIL: Volume trend returned incorrect percentage change")

        print("PASS: Training volume trend compares equal rolling periods")

    finally:
        delete_user(user_id)


def test_volume_percentage_is_none_without_previous_baseline():
    user_id = create_user()

    try:
        create_completed_weighted_workout(
            user_id,
            "2026-08-20 10:00:00",
            reps=10,
            weight_kg=50
        )

        analytics = get_volume_trend(
            user_id,
            days=7,
            reference_date=REFERENCE_DATE
        )

        if analytics["previous_volume_kg"] != 0:
            raise ValueError("FAIL: Empty previous volume period did not return zero")

        if analytics["current_volume_kg"] != 500:
            raise ValueError("FAIL: Current volume period returned incorrect value")

        if analytics["volume_change_percentage"] is not None:
            raise ValueError("FAIL: Volume percentage was invented without previous baseline")

        print("PASS: Volume trend avoids undefined percentage without previous baseline")

    finally:
        delete_user(user_id)


def test_weight_trend_filters_rolling_window():
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

        third_id = add_progress_entry(
            user_id,
            weight_kg=79
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
            "2026-08-15 08:00:00"
        )

        set_database_timestamp(
            "progress_entries",
            "progress_entry_id",
            third_id,
            "recorded_at",
            "2026-08-20 08:00:00"
        )

        analytics = get_weight_trend(
            user_id,
            days=30,
            reference_date=REFERENCE_DATE
        )

        if analytics["entry_count"] != 3:
            raise ValueError("FAIL: Weight trend returned incorrect entry count")

        if analytics["earliest_weight_kg"] != 82:
            raise ValueError("FAIL: Weight trend returned incorrect earliest weight")

        if analytics["latest_weight_kg"] != 79:
            raise ValueError("FAIL: Weight trend returned incorrect latest weight")

        if analytics["weight_change_kg"] != -3:
            raise ValueError("FAIL: Weight trend returned incorrect weight change")

        print("PASS: Weight trend calculates change inside rolling window")

    finally:
        delete_user(user_id)


def test_measurement_trend_calculates_body_area_change():
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

        analytics = get_measurement_trend(
            user_id,
            "Waist",
            days=30,
            reference_date=REFERENCE_DATE
        )

        if analytics["entry_count"] != 2:
            raise ValueError("FAIL: Measurement trend returned incorrect count")

        if analytics["earliest_measurement_cm"] != 86:
            raise ValueError("FAIL: Measurement trend returned incorrect earliest value")

        if analytics["latest_measurement_cm"] != 84:
            raise ValueError("FAIL: Measurement trend returned incorrect latest value")

        if analytics["measurement_change_cm"] != -2:
            raise ValueError("FAIL: Measurement trend returned incorrect measurement change")

        print("PASS: Body measurement trend calculates longitudinal change")

    finally:
        delete_user(user_id)


def test_calendar_adherence_trend_filters_window():
    user_id = create_user()

    try:
        plan = {
            "exercises": []
        }

        completed_id = schedule_workout_from_plan(
            user_id,
            "2026-08-16 18:00:00",
            plan
        )

        skipped_id = schedule_workout_from_plan(
            user_id,
            "2026-08-17 18:00:00",
            plan
        )

        cancelled_id = schedule_workout_from_plan(
            user_id,
            "2026-08-18 18:00:00",
            plan
        )

        schedule_workout_from_plan(
            user_id,
            "2026-08-19 18:00:00",
            plan
        )

        schedule_workout_from_plan(
            user_id,
            "2026-08-01 18:00:00",
            plan
        )

        workout_session_id = start_workout_from_plan(
            user_id,
            plan
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=30
        )

        complete_scheduled_workout(
            completed_id,
            workout_session_id
        )

        update_scheduled_workout_status(
            skipped_id,
            "Skipped"
        )

        update_scheduled_workout_status(
            cancelled_id,
            "Cancelled"
        )

        analytics = get_calendar_adherence_trend(
            user_id,
            days=7,
            reference_date=REFERENCE_DATE
        )

        if analytics["scheduled_workout_count"] != 4:
            raise ValueError("FAIL: Calendar trend included workout outside rolling window")

        if analytics["completed_count"] != 1:
            raise ValueError("FAIL: Calendar trend returned incorrect completed count")

        if analytics["skipped_count"] != 1:
            raise ValueError("FAIL: Calendar trend returned incorrect skipped count")

        if analytics["cancelled_count"] != 1:
            raise ValueError("FAIL: Calendar trend returned incorrect cancelled count")

        if analytics["planned_count"] != 1:
            raise ValueError("FAIL: Calendar trend returned incorrect planned count")

        if analytics["completion_rate_percentage"] != 50.0:
            raise ValueError("FAIL: Calendar trend returned incorrect adherence rate")

        print("PASS: Calendar adherence trend filters rolling date window")

    finally:
        delete_user(user_id)


def test_trend_analytics_overview_contains_sections():
    user_id = create_user()

    try:
        overview = get_trend_analytics_overview(
            user_id,
            reference_date=REFERENCE_DATE
        )

        expected_sections = {
            "activity_windows",
            "workout_frequency_28_days",
            "volume_30_days",
            "weight_90_days",
            "calendar_adherence_30_days"
        }

        if set(overview.keys()) != expected_sections:
            raise ValueError("FAIL: Trend analytics overview returned incorrect sections")

        if set(overview["activity_windows"].keys()) != {
            "7_days",
            "30_days",
            "90_days"
        }:
            raise ValueError("FAIL: Trend overview returned incorrect standard activity windows")

        print("PASS: Trend analytics overview combines rolling analytics sections")

    finally:
        delete_user(user_id)


def test_trend_analytics_are_isolated_by_user():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        activity_id = add_activity_log(
            first_user_id,
            "Walking",
            steps=5000
        )

        set_database_timestamp(
            "activity_logs",
            "activity_log_id",
            activity_id,
            "started_at",
            "2026-08-20 10:00:00"
        )

        analytics = get_activity_window_analytics(
            second_user_id,
            7,
            REFERENCE_DATE
        )

        if analytics["activity_count"] != 0:
            raise ValueError("FAIL: Trend analytics leaked another user's activity")

        if analytics["total_steps"] != 0:
            raise ValueError("FAIL: Trend analytics leaked another user's steps")

        print("PASS: Trend analytics are isolated by user")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


if __name__ == "__main__":
    test_invalid_window_days_rejected()
    test_invalid_reference_date_rejected()
    test_activity_window_filters_by_date()
    test_standard_activity_windows()
    test_workout_frequency_builds_weekly_buckets()
    test_cancelled_workouts_do_not_count_toward_frequency()
    test_volume_trend_compares_equal_periods()
    test_volume_percentage_is_none_without_previous_baseline()
    test_weight_trend_filters_rolling_window()
    test_measurement_trend_calculates_body_area_change()
    test_calendar_adherence_trend_filters_window()
    test_trend_analytics_overview_contains_sections()
    test_trend_analytics_are_isolated_by_user()
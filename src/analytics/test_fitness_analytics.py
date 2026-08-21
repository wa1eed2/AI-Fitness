from src.database.setup_progress_database import (
    setup_progress_database
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_progress_database import (
    add_progress_entry,
    add_activity_log,
    schedule_workout_from_plan,
    update_scheduled_workout_status,
    complete_scheduled_workout
)

from src.database.query_workout_log_database import (
    start_workout_from_plan,
    finish_workout_session,
    cancel_workout_session
)

from src.analytics.fitness_analytics import (
    calculate_percentage,
    get_weight_analytics,
    get_body_fat_analytics,
    get_activity_analytics,
    get_workout_consistency_analytics,
    get_calendar_adherence_analytics,
    get_analytics_overview
)


def test_percentage_calculation():
    if calculate_percentage(3, 4) != 75.0:
        raise ValueError("FAIL: Percentage calculation returned incorrect result")

    if calculate_percentage(1, 3) != 33.33:
        raise ValueError("FAIL: Percentage calculation did not round correctly")

    print("PASS: Analytics percentage calculation works correctly")


def test_percentage_handles_zero_denominator():
    result = calculate_percentage(
        5,
        0
    )

    if result != 0.0:
        raise ValueError("FAIL: Zero denominator did not return zero percentage")

    print("PASS: Analytics percentage handles zero denominator")


def test_empty_weight_analytics():
    user_id = create_user()

    try:
        analytics = get_weight_analytics(
            user_id
        )

        if analytics["entry_count"] != 0:
            raise ValueError("FAIL: Empty weight analytics returned entries")

        if analytics["latest_weight_kg"] is not None:
            raise ValueError("FAIL: Empty weight analytics returned latest weight")

        if analytics["weight_change_kg"] is not None:
            raise ValueError("FAIL: Empty weight analytics returned weight change")

        print("PASS: Empty weight analytics returns correct defaults")

    finally:
        delete_user(user_id)


def test_weight_analytics_calculates_change():
    user_id = create_user()

    try:
        add_progress_entry(
            user_id,
            weight_kg=84
        )

        add_progress_entry(
            user_id,
            weight_kg=82.5
        )

        add_progress_entry(
            user_id,
            weight_kg=81
        )

        analytics = get_weight_analytics(
            user_id
        )

        if analytics["entry_count"] != 3:
            raise ValueError("FAIL: Weight analytics returned incorrect entry count")

        if analytics["latest_weight_kg"] != 81:
            raise ValueError("FAIL: Weight analytics returned incorrect latest weight")

        if analytics["earliest_weight_kg"] != 84:
            raise ValueError("FAIL: Weight analytics returned incorrect earliest weight")

        if analytics["weight_change_kg"] != -3:
            raise ValueError("FAIL: Weight analytics returned incorrect change")

        print("PASS: Weight analytics calculates longitudinal change")

    finally:
        delete_user(user_id)


def test_body_fat_analytics_calculates_change():
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

        analytics = get_body_fat_analytics(
            user_id
        )

        if analytics["entry_count"] != 2:
            raise ValueError("FAIL: Body-fat analytics returned incorrect entry count")

        if analytics["latest_body_fat_percentage"] != 19.5:
            raise ValueError("FAIL: Body-fat analytics returned incorrect latest value")

        if analytics["earliest_body_fat_percentage"] != 22:
            raise ValueError("FAIL: Body-fat analytics returned incorrect earliest value")

        if analytics["body_fat_change_percentage_points"] != -2.5:
            raise ValueError("FAIL: Body-fat analytics returned incorrect change")

        print("PASS: Body-fat analytics calculates longitudinal change")

    finally:
        delete_user(user_id)


def test_activity_analytics_empty_user():
    user_id = create_user()

    try:
        analytics = get_activity_analytics(
            user_id
        )

        if analytics["activity_count"] != 0:
            raise ValueError("FAIL: Empty activity analytics returned activities")

        if analytics["total_duration_minutes"] != 0:
            raise ValueError("FAIL: Empty activity analytics returned duration")

        if analytics["total_steps"] != 0:
            raise ValueError("FAIL: Empty activity analytics returned steps")

        if analytics["activity_type_counts"] != {}:
            raise ValueError("FAIL: Empty activity analytics returned type counts")

        print("PASS: Empty activity analytics returns correct defaults")

    finally:
        delete_user(user_id)


def test_activity_analytics_totals_metrics():
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

        add_activity_log(
            user_id,
            "Walking",
            duration_minutes=40,
            distance_km=3,
            steps=5000,
            estimated_calories=200
        )

        analytics = get_activity_analytics(
            user_id
        )

        if analytics["activity_count"] != 3:
            raise ValueError("FAIL: Activity analytics returned incorrect session count")

        if analytics["total_duration_minutes"] != 90:
            raise ValueError("FAIL: Activity analytics returned incorrect duration")

        if analytics["average_duration_minutes"] != 30:
            raise ValueError("FAIL: Activity analytics returned incorrect average duration")

        if analytics["total_distance_km"] != 9.5:
            raise ValueError("FAIL: Activity analytics returned incorrect distance")

        if analytics["total_steps"] != 12000:
            raise ValueError("FAIL: Activity analytics returned incorrect steps")

        if analytics["total_estimated_calories"] != 600:
            raise ValueError("FAIL: Activity analytics returned incorrect estimated calories")

        if analytics["activity_type_counts"]["Walking"] != 2:
            raise ValueError("FAIL: Activity analytics returned incorrect Walking count")

        if analytics["activity_type_counts"]["Running"] != 1:
            raise ValueError("FAIL: Activity analytics returned incorrect Running count")

        print("PASS: Activity analytics totals metrics correctly")

    finally:
        delete_user(user_id)


def test_workout_consistency_empty_user():
    user_id = create_user()

    try:
        analytics = get_workout_consistency_analytics(
            user_id
        )

        if analytics["total_workout_count"] != 0:
            raise ValueError("FAIL: Empty workout analytics returned workouts")

        if analytics["completion_rate_percentage"] != 0.0:
            raise ValueError("FAIL: Empty workout analytics returned completion rate")

        print("PASS: Empty workout consistency analytics returns correct defaults")

    finally:
        delete_user(user_id)


def test_workout_consistency_calculates_completion_rate():
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
            actual_duration_minutes=40
        )

        second_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            second_session_id,
            actual_duration_minutes=50
        )

        third_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        cancel_workout_session(
            third_session_id,
            notes="Analytics cancellation test"
        )

        analytics = get_workout_consistency_analytics(
            user_id
        )

        if analytics["total_workout_count"] != 3:
            raise ValueError("FAIL: Workout analytics returned incorrect workout count")

        if analytics["completed_workout_count"] != 2:
            raise ValueError("FAIL: Workout analytics returned incorrect completed count")

        if analytics["cancelled_workout_count"] != 1:
            raise ValueError("FAIL: Workout analytics returned incorrect cancelled count")

        if analytics["completion_rate_percentage"] != 66.67:
            raise ValueError("FAIL: Workout analytics returned incorrect completion rate")

        if analytics["total_completed_minutes"] != 90:
            raise ValueError("FAIL: Workout analytics returned incorrect total duration")

        if analytics["average_completed_duration_minutes"] != 45:
            raise ValueError("FAIL: Workout analytics returned incorrect average duration")

        print("PASS: Workout consistency analytics calculates completion rate")

    finally:
        delete_user(user_id)


def test_active_workout_does_not_reduce_completion_rate():
    user_id = create_user()

    try:
        completed_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            completed_session_id,
            actual_duration_minutes=30
        )

        start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        analytics = get_workout_consistency_analytics(
            user_id
        )

        if analytics["active_workout_count"] != 1:
            raise ValueError("FAIL: Workout analytics did not count active workout")

        if analytics["completion_rate_percentage"] != 100.0:
            raise ValueError("FAIL: Active workout incorrectly reduced completion rate")

        print("PASS: Active workout does not reduce terminal completion rate")

    finally:
        delete_user(user_id)


def test_calendar_adherence_empty_user():
    user_id = create_user()

    try:
        analytics = get_calendar_adherence_analytics(
            user_id
        )

        if analytics["scheduled_workout_count"] != 0:
            raise ValueError("FAIL: Empty calendar analytics returned workouts")

        if analytics["completion_rate_percentage"] != 0.0:
            raise ValueError("FAIL: Empty calendar analytics returned completion rate")

        print("PASS: Empty calendar adherence analytics returns correct defaults")

    finally:
        delete_user(user_id)


def test_calendar_adherence_calculates_completion_rate():
    user_id = create_user()

    try:
        plan = {
            "exercises": []
        }

        completed_schedule_id = schedule_workout_from_plan(
            user_id,
            "2026-08-25 18:00:00",
            plan
        )

        skipped_schedule_id = schedule_workout_from_plan(
            user_id,
            "2026-08-26 18:00:00",
            plan
        )

        cancelled_schedule_id = schedule_workout_from_plan(
            user_id,
            "2026-08-27 18:00:00",
            plan
        )

        schedule_workout_from_plan(
            user_id,
            "2026-08-28 18:00:00",
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
            completed_schedule_id,
            workout_session_id
        )

        update_scheduled_workout_status(
            skipped_schedule_id,
            "Skipped"
        )

        update_scheduled_workout_status(
            cancelled_schedule_id,
            "Cancelled"
        )

        analytics = get_calendar_adherence_analytics(
            user_id
        )

        if analytics["scheduled_workout_count"] != 4:
            raise ValueError("FAIL: Calendar analytics returned incorrect total count")

        if analytics["completed_count"] != 1:
            raise ValueError("FAIL: Calendar analytics returned incorrect completed count")

        if analytics["skipped_count"] != 1:
            raise ValueError("FAIL: Calendar analytics returned incorrect skipped count")

        if analytics["cancelled_count"] != 1:
            raise ValueError("FAIL: Calendar analytics returned incorrect cancelled count")

        if analytics["planned_count"] != 1:
            raise ValueError("FAIL: Calendar analytics returned incorrect planned count")

        if analytics["adherence_opportunity_count"] != 2:
            raise ValueError("FAIL: Calendar analytics returned incorrect adherence denominator")

        if analytics["completion_rate_percentage"] != 50.0:
            raise ValueError("FAIL: Calendar analytics returned incorrect completion rate")

        print("PASS: Calendar adherence analytics calculates completion rate")

    finally:
        delete_user(user_id)


def test_analytics_overview_contains_all_sections():
    user_id = create_user()

    try:
        overview = get_analytics_overview(
            user_id
        )

        expected_sections = {
            "weight",
            "body_fat",
            "activity",
            "workout_consistency",
            "calendar_adherence"
        }

        if set(overview.keys()) != expected_sections:
            raise ValueError("FAIL: Analytics overview returned incorrect sections")

        print("PASS: Analytics overview combines all high-level sections")

    finally:
        delete_user(user_id)


def test_analytics_are_isolated_by_user():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        add_progress_entry(
            first_user_id,
            weight_kg=80
        )

        add_activity_log(
            first_user_id,
            "Walking",
            steps=5000
        )

        second_overview = get_analytics_overview(
            second_user_id
        )

        if second_overview["weight"]["entry_count"] != 0:
            raise ValueError("FAIL: Weight analytics leaked another user's data")

        if second_overview["activity"]["activity_count"] != 0:
            raise ValueError("FAIL: Activity analytics leaked another user's data")

        print("PASS: High-level analytics are isolated by user")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


if __name__ == "__main__":
    setup_progress_database()

    test_percentage_calculation()
    test_percentage_handles_zero_denominator()

    test_empty_weight_analytics()
    test_weight_analytics_calculates_change()
    test_body_fat_analytics_calculates_change()

    test_activity_analytics_empty_user()
    test_activity_analytics_totals_metrics()

    test_workout_consistency_empty_user()
    test_workout_consistency_calculates_completion_rate()
    test_active_workout_does_not_reduce_completion_rate()

    test_calendar_adherence_empty_user()
    test_calendar_adherence_calculates_completion_rate()

    test_analytics_overview_contains_all_sections()
    test_analytics_are_isolated_by_user()
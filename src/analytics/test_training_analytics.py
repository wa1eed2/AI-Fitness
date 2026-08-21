from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_workout_log_database import (
    start_workout_from_plan,
    get_workout_session_exercises,
    log_workout_set,
    finish_workout_session,
    cancel_workout_session
)

from src.database.query_exercise_database import (
    get_exercise_by_id
)

from src.analytics.training_analytics import (
    calculate_weighted_volume,
    get_training_volume_analytics,
    get_exercise_frequency_analytics,
    get_primary_muscle_frequency_analytics,
    get_workout_volume_breakdown,
    get_training_analytics_overview
)


def test_weighted_volume_calculation():
    result = calculate_weighted_volume(
        10,
        50
    )

    if result != 500:
        raise ValueError("FAIL: Weighted training volume calculation was incorrect")

    print("PASS: Weighted training volume calculates reps times weight")


def test_weighted_volume_handles_missing_values():
    cases = [
        (
            None,
            50
        ),
        (
            10,
            None
        ),
        (
            None,
            None
        )
    ]

    for reps, weight in cases:
        result = calculate_weighted_volume(
            reps,
            weight
        )

        if result != 0.0:
            raise ValueError("FAIL: Missing reps or weight produced training volume")

    print("PASS: Weighted volume handles missing performance values")


def test_empty_training_volume_analytics():
    user_id = create_user()

    try:
        analytics = get_training_volume_analytics(
            user_id
        )

        if analytics["completed_workout_count"] != 0:
            raise ValueError("FAIL: Empty training analytics returned workouts")

        if analytics["performance_log_count"] != 0:
            raise ValueError("FAIL: Empty training analytics returned performance logs")

        if analytics["total_reps"] != 0:
            raise ValueError("FAIL: Empty training analytics returned reps")

        if analytics["total_volume_kg"] != 0:
            raise ValueError("FAIL: Empty training analytics returned volume")

        print("PASS: Empty training volume analytics returns correct defaults")

    finally:
        delete_user(user_id)


def test_training_volume_totals_weighted_sets():
    user_id = create_user()

    try:
        workout_session_id = start_workout_from_plan(
            user_id,
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

        exercises = get_workout_session_exercises(
            workout_session_id
        )

        session_exercise_id = exercises[0][
            "session_exercise_id"
        ]

        log_workout_set(
            session_exercise_id,
            1,
            reps_completed=10,
            weight_kg=50
        )

        log_workout_set(
            session_exercise_id,
            2,
            reps_completed=8,
            weight_kg=60
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=45
        )

        analytics = get_training_volume_analytics(
            user_id
        )

        if analytics["completed_workout_count"] != 1:
            raise ValueError("FAIL: Training analytics returned incorrect workout count")

        if analytics["exercise_occurrence_count"] != 1:
            raise ValueError("FAIL: Training analytics returned incorrect exercise count")

        if analytics["performance_log_count"] != 2:
            raise ValueError("FAIL: Training analytics returned incorrect performance log count")

        if analytics["rep_set_count"] != 2:
            raise ValueError("FAIL: Training analytics returned incorrect rep-set count")

        if analytics["weighted_set_count"] != 2:
            raise ValueError("FAIL: Training analytics returned incorrect weighted-set count")

        if analytics["total_reps"] != 18:
            raise ValueError("FAIL: Training analytics returned incorrect total reps")

        if analytics["total_volume_kg"] != 980:
            raise ValueError("FAIL: Training analytics returned incorrect weighted volume")

        if analytics["average_reps_per_rep_set"] != 9:
            raise ValueError("FAIL: Training analytics returned incorrect average reps")

        if analytics["average_volume_per_completed_workout"] != 980:
            raise ValueError("FAIL: Training analytics returned incorrect average workout volume")

        print("PASS: Training analytics totals weighted sets correctly")

    finally:
        delete_user(user_id)


def test_bodyweight_reps_do_not_invent_weighted_volume():
    user_id = create_user()

    try:
        workout_session_id = start_workout_from_plan(
            user_id,
            {
                "primary_goal": "General Fitness",
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 2,
                        "reps": "8-12",
                        "rest_seconds": 60
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

        log_workout_set(
            session_exercise_id,
            1,
            reps_completed=12
        )

        log_workout_set(
            session_exercise_id,
            2,
            reps_completed=10
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=30
        )

        analytics = get_training_volume_analytics(
            user_id
        )

        if analytics["rep_set_count"] != 2:
            raise ValueError("FAIL: Bodyweight rep sets were not counted")

        if analytics["total_reps"] != 22:
            raise ValueError("FAIL: Bodyweight reps were not counted")

        if analytics["weighted_set_count"] != 0:
            raise ValueError("FAIL: Bodyweight sets were incorrectly counted as weighted")

        if analytics["total_volume_kg"] != 0:
            raise ValueError("FAIL: Bodyweight exercise invented external-weight volume")

        print("PASS: Bodyweight reps are tracked without invented weighted volume")

    finally:
        delete_user(user_id)


def test_duration_log_does_not_create_reps_or_volume():
    user_id = create_user()

    try:
        workout_session_id = start_workout_from_plan(
            user_id,
            {
                "primary_goal": "Endurance",
                "exercises": [
                    {
                        "exercise_id": "E006",
                        "duration_minutes": 10
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

        log_workout_set(
            session_exercise_id,
            1,
            duration_seconds=600
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=10
        )

        analytics = get_training_volume_analytics(
            user_id
        )

        if analytics["performance_log_count"] != 1:
            raise ValueError("FAIL: Duration performance log was not counted")

        if analytics["rep_set_count"] != 0:
            raise ValueError("FAIL: Duration log was incorrectly counted as rep set")

        if analytics["total_reps"] != 0:
            raise ValueError("FAIL: Duration log produced reps")

        if analytics["total_volume_kg"] != 0:
            raise ValueError("FAIL: Duration log produced weighted volume")

        print("PASS: Duration logs remain separate from rep and volume analytics")

    finally:
        delete_user(user_id)


def test_only_completed_workouts_count_toward_training_volume():
    user_id = create_user()

    try:
        completed_id = start_workout_from_plan(
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
            completed_id
        )

        log_workout_set(
            completed_exercises[0]["session_exercise_id"],
            1,
            reps_completed=10,
            weight_kg=50
        )

        finish_workout_session(
            completed_id,
            actual_duration_minutes=20
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

        cancelled_exercises = get_workout_session_exercises(
            cancelled_id
        )

        log_workout_set(
            cancelled_exercises[0]["session_exercise_id"],
            1,
            reps_completed=20,
            weight_kg=100
        )

        cancel_workout_session(
            cancelled_id
        )

        analytics = get_training_volume_analytics(
            user_id
        )

        if analytics["completed_workout_count"] != 1:
            raise ValueError("FAIL: Cancelled workout was counted as completed training")

        if analytics["total_reps"] != 10:
            raise ValueError("FAIL: Cancelled workout reps entered training analytics")

        if analytics["total_volume_kg"] != 500:
            raise ValueError("FAIL: Cancelled workout volume entered training analytics")

        print("PASS: Training volume uses completed workouts only")

    finally:
        delete_user(user_id)


def test_exercise_frequency_analytics():
    user_id = create_user()

    try:
        for weight in [
            40,
            50
        ]:
            workout_session_id = start_workout_from_plan(
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
                workout_session_id
            )

            log_workout_set(
                exercises[0]["session_exercise_id"],
                1,
                reps_completed=10,
                weight_kg=weight
            )

            finish_workout_session(
                workout_session_id,
                actual_duration_minutes=20
            )

        analytics = get_exercise_frequency_analytics(
            user_id
        )

        e001 = next(
            item
            for item in analytics
            if item["exercise_id"] == "E001"
        )

        if e001["workout_count"] != 2:
            raise ValueError("FAIL: Exercise frequency returned incorrect workout count")

        if e001["exercise_occurrence_count"] != 2:
            raise ValueError("FAIL: Exercise frequency returned incorrect occurrence count")

        if e001["performance_log_count"] != 2:
            raise ValueError("FAIL: Exercise frequency returned incorrect log count")

        if e001["total_reps"] != 20:
            raise ValueError("FAIL: Exercise frequency returned incorrect reps")

        if e001["total_volume_kg"] != 900:
            raise ValueError("FAIL: Exercise frequency returned incorrect volume")

        print("PASS: Exercise frequency analytics aggregates completed training")

    finally:
        delete_user(user_id)


def test_primary_muscle_frequency_deduplicates_workout_exposure():
    user_id = create_user()

    try:
        exercise = get_exercise_by_id(
            "E001"
        )

        primary_muscle = exercise[
            "primary_muscle"
        ]

        workout_session_id = start_workout_from_plan(
            user_id,
            {
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 1,
                        "reps": "10",
                        "rest_seconds": 60
                    },
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
            workout_session_id
        )

        for exercise_row in exercises:
            log_workout_set(
                exercise_row["session_exercise_id"],
                1,
                reps_completed=10,
                weight_kg=50
            )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=30
        )

        analytics = get_primary_muscle_frequency_analytics(
            user_id
        )

        muscle = next(
            item
            for item in analytics
            if item["primary_muscle"] == primary_muscle
        )

        if muscle["workout_count"] != 1:
            raise ValueError("FAIL: Muscle frequency double-counted one workout exposure")

        if muscle["exercise_occurrence_count"] != 2:
            raise ValueError("FAIL: Muscle frequency returned incorrect exercise occurrence count")

        if muscle["performance_log_count"] != 2:
            raise ValueError("FAIL: Muscle frequency returned incorrect performance log count")

        if muscle["total_reps"] != 20:
            raise ValueError("FAIL: Muscle frequency returned incorrect total reps")

        if muscle["total_volume_kg"] != 1000:
            raise ValueError("FAIL: Muscle frequency returned incorrect volume")

        print("PASS: Primary-muscle frequency separates workout exposure from exercise occurrences")

    finally:
        delete_user(user_id)


def test_workout_volume_breakdown():
    user_id = create_user()

    try:
        workout_session_id = start_workout_from_plan(
            user_id,
            {
                "primary_goal": "Strength",
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "sets": 2,
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

        log_workout_set(
            session_exercise_id,
            1,
            reps_completed=10,
            weight_kg=40
        )

        log_workout_set(
            session_exercise_id,
            2,
            reps_completed=8,
            weight_kg=50
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=35
        )

        breakdown = get_workout_volume_breakdown(
            user_id
        )

        workout = breakdown[0]

        if workout["workout_session_id"] != workout_session_id:
            raise ValueError("FAIL: Workout breakdown returned incorrect session")

        if workout["exercise_count"] != 1:
            raise ValueError("FAIL: Workout breakdown returned incorrect exercise count")

        if workout["performance_log_count"] != 2:
            raise ValueError("FAIL: Workout breakdown returned incorrect log count")

        if workout["total_reps"] != 18:
            raise ValueError("FAIL: Workout breakdown returned incorrect reps")

        if workout["total_volume_kg"] != 800:
            raise ValueError("FAIL: Workout breakdown returned incorrect volume")

        if workout["actual_duration_minutes"] != 35:
            raise ValueError("FAIL: Workout breakdown returned incorrect duration")

        print("PASS: Per-workout training volume breakdown calculates correctly")

    finally:
        delete_user(user_id)


def test_workout_breakdown_returns_newest_first():
    user_id = create_user()

    try:
        first_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            first_id,
            actual_duration_minutes=20
        )

        second_id = start_workout_from_plan(
            user_id,
            {
                "exercises": []
            }
        )

        finish_workout_session(
            second_id,
            actual_duration_minutes=30
        )

        breakdown = get_workout_volume_breakdown(
            user_id
        )

        if breakdown[0]["workout_session_id"] != second_id:
            raise ValueError("FAIL: Workout volume breakdown did not return newest workout first")

        if breakdown[1]["workout_session_id"] != first_id:
            raise ValueError("FAIL: Workout volume breakdown returned incorrect workout order")

        print("PASS: Workout volume breakdown returns newest sessions first")

    finally:
        delete_user(user_id)


def test_training_analytics_are_isolated_by_user():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        workout_session_id = start_workout_from_plan(
            first_user_id,
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
            workout_session_id
        )

        log_workout_set(
            exercises[0]["session_exercise_id"],
            1,
            reps_completed=10,
            weight_kg=50
        )

        finish_workout_session(
            workout_session_id,
            actual_duration_minutes=20
        )

        second_user_analytics = get_training_volume_analytics(
            second_user_id
        )

        if second_user_analytics["completed_workout_count"] != 0:
            raise ValueError("FAIL: Training analytics leaked another user's workouts")

        if second_user_analytics["total_reps"] != 0:
            raise ValueError("FAIL: Training analytics leaked another user's reps")

        if second_user_analytics["total_volume_kg"] != 0:
            raise ValueError("FAIL: Training analytics leaked another user's volume")

        print("PASS: Training analytics are isolated by user")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


def test_training_analytics_overview_contains_all_sections():
    user_id = create_user()

    try:
        overview = get_training_analytics_overview(
            user_id
        )

        expected_sections = {
            "volume",
            "exercise_frequency",
            "primary_muscle_frequency",
            "workout_breakdown"
        }

        if set(overview.keys()) != expected_sections:
            raise ValueError("FAIL: Training analytics overview returned incorrect sections")

        print("PASS: Training analytics overview combines all training sections")

    finally:
        delete_user(user_id)


if __name__ == "__main__":
    test_weighted_volume_calculation()
    test_weighted_volume_handles_missing_values()
    test_empty_training_volume_analytics()
    test_training_volume_totals_weighted_sets()
    test_bodyweight_reps_do_not_invent_weighted_volume()
    test_duration_log_does_not_create_reps_or_volume()
    test_only_completed_workouts_count_toward_training_volume()
    test_exercise_frequency_analytics()
    test_primary_muscle_frequency_deduplicates_workout_exposure()
    test_workout_volume_breakdown()
    test_workout_breakdown_returns_newest_first()
    test_training_analytics_are_isolated_by_user()
    test_training_analytics_overview_contains_all_sections()
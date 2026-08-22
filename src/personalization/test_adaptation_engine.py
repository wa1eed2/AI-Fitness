from src.personalization.adaptation_engine import (
    ACTION_INSUFFICIENT_DATA,
    ACTION_MAINTAIN,
    ACTION_PROGRESS_CAUTIOUSLY,
    ACTION_REDUCE_VOLUME,
    calculate_expected_recent_sessions,
    calculate_recent_completed_workouts,
    evaluate_training_adaptation,
    summarize_progression
)


REFERENCE_DATE = "2026-08-21"


def fake_profile(user_id):
    return {
        "user_id": user_id,
        "training_days_per_week": 3
    }


def strong_training(user_id):
    return {
        "volume": {
            "completed_workout_count": 10
        },
        "exercise_frequency": [],
        "primary_muscle_frequency": [],
        "workout_breakdown": [
            {
                "workout_session_id": 1,
                "started_at": "2026-08-09T10:00:00"
            },
            {
                "workout_session_id": 2,
                "started_at": "2026-08-11T10:00:00"
            },
            {
                "workout_session_id": 3,
                "started_at": "2026-08-13T10:00:00"
            },
            {
                "workout_session_id": 4,
                "started_at": "2026-08-16T10:00:00"
            },
            {
                "workout_session_id": 5,
                "started_at": "2026-08-18T10:00:00"
            },
            {
                "workout_session_id": 6,
                "started_at": "2026-08-20T10:00:00"
            }
        ]
    }


def sparse_recent_training(user_id):
    return {
        "volume": {
            "completed_workout_count": 10
        },
        "exercise_frequency": [],
        "primary_muscle_frequency": [],
        "workout_breakdown": [
            {
                "workout_session_id": 1,
                "started_at": "2026-08-20T10:00:00"
            }
        ]
    }


def positive_progression(user_id):
    return {
        "exercise_progression": [
            {
                "exercise_id": "E001",
                "workout_count": 4,
                "max_weight_change_kg": 5.0,
                "volume_change_kg": 250.0
            },
            {
                "exercise_id": "E002",
                "workout_count": 3,
                "max_weight_change_kg": 2.5,
                "volume_change_kg": 100.0
            },
            {
                "exercise_id": "E003",
                "workout_count": 3,
                "max_weight_change_kg": 0.0,
                "volume_change_kg": 0.0
            }
        ],
        "data_quality": {
            "exercise_log_coverage_percentage": 90.0
        }
    }


def negative_progression(user_id):
    return {
        "exercise_progression": [
            {
                "exercise_id": "E001",
                "workout_count": 4,
                "max_weight_change_kg": -5.0,
                "volume_change_kg": -250.0
            },
            {
                "exercise_id": "E002",
                "workout_count": 4,
                "max_weight_change_kg": -2.5,
                "volume_change_kg": -100.0
            }
        ],
        "data_quality": {
            "exercise_log_coverage_percentage": 90.0
        }
    }


def low_quality_progression(user_id):
    result = positive_progression(
        user_id
    )

    result[
        "data_quality"
    ][
        "exercise_log_coverage_percentage"
    ] = 30.0

    return result


def normal_recovery(
    user_id,
    reference_date=None
):
    return {
        "signal_status": "normal",
        "high_exertion_signal": False,
        "recent_performance_log_count": 8,
        "recent_rpe_log_count": 8,
        "recent_rir_log_count": 8,
        "average_rpe": 7.5,
        "average_rir": 2.5,
        "high_rpe_ratio": 0.125,
        "low_rir_ratio": 0.125,
        "sufficient_exertion_data": True
    }


def high_exertion_recovery(
    user_id,
    reference_date=None
):
    return {
        "signal_status": "high_exertion",
        "high_exertion_signal": True,
        "recent_performance_log_count": 8,
        "recent_rpe_log_count": 8,
        "recent_rir_log_count": 8,
        "average_rpe": 9.2,
        "average_rir": 0.75,
        "high_rpe_ratio": 0.75,
        "low_rir_ratio": 0.75,
        "sufficient_exertion_data": True
    }


def insufficient_recovery(
    user_id,
    reference_date=None
):
    return {
        "signal_status": "insufficient_data",
        "high_exertion_signal": False,
        "recent_performance_log_count": 2,
        "recent_rpe_log_count": 2,
        "recent_rir_log_count": 2,
        "average_rpe": 9.5,
        "average_rir": 0.5,
        "high_rpe_ratio": 1.0,
        "low_rir_ratio": 1.0,
        "sufficient_exertion_data": False
    }


def test_recent_workout_count():
    count = calculate_recent_completed_workouts(
        strong_training(
            1
        )[
            "workout_breakdown"
        ],
        REFERENCE_DATE
    )

    if count != 6:
        raise ValueError(f"FAIL: Expected 6 recent workouts, got {count}")

    print("PASS: Adaptation engine counts recent completed workouts deterministically")


def test_expected_sessions():
    expected = calculate_expected_recent_sessions(
        3
    )

    if expected != 6:
        raise ValueError(f"FAIL: Expected 6 planned sessions in 14 days, got {expected}")

    print("PASS: Adaptation engine derives recent session expectation from profile")


def test_progression_summary():
    summary = summarize_progression(
        positive_progression(
            1
        )[
            "exercise_progression"
        ]
    )

    if summary["eligible_exercise_count"] != 3:
        raise ValueError("FAIL: Eligible progression count is incorrect")

    if summary["positive_progression_count"] != 2:
        raise ValueError("FAIL: Positive progression count is incorrect")

    if summary["positive_progression_ratio"] != 0.6667:
        raise ValueError("FAIL: Positive progression ratio is incorrect")

    print("PASS: Exercise progression is summarized without LLM inference")


def test_missing_profile_returns_insufficient_data():
    result = evaluate_training_adaptation(
        user_id=1,
        reference_date=REFERENCE_DATE,
        profile_loader=lambda user_id: None,
        training_loader=strong_training,
        progression_loader=positive_progression,
        recovery_loader=normal_recovery
    )

    if result["action"] != ACTION_INSUFFICIENT_DATA:
        raise ValueError("FAIL: Missing profile did not block adaptation")

    if "PROFILE_REQUIRED" not in result["reason_codes"]:
        raise ValueError("FAIL: Missing-profile reason was not recorded")

    print("PASS: Adaptation requires a valid user profile")


def test_too_few_completed_workouts_blocks_adaptation():
    def low_training(user_id):
        result = strong_training(
            user_id
        )

        result[
            "volume"
        ][
            "completed_workout_count"
        ] = 2

        return result

    result = evaluate_training_adaptation(
        user_id=1,
        reference_date=REFERENCE_DATE,
        profile_loader=fake_profile,
        training_loader=low_training,
        progression_loader=positive_progression,
        recovery_loader=normal_recovery
    )

    if result["action"] != ACTION_INSUFFICIENT_DATA:
        raise ValueError("FAIL: Adaptation was allowed with too few completed workouts")

    print("PASS: Adaptation refuses to act on too little workout history")


def test_low_logging_coverage_blocks_adaptation():
    result = evaluate_training_adaptation(
        user_id=1,
        reference_date=REFERENCE_DATE,
        profile_loader=fake_profile,
        training_loader=strong_training,
        progression_loader=low_quality_progression,
        recovery_loader=normal_recovery
    )

    if result["action"] != ACTION_INSUFFICIENT_DATA:
        raise ValueError("FAIL: Poor logging coverage did not block adaptation")

    print("PASS: Adaptation refuses to overinterpret poor-quality workout logs")


def test_insufficient_recovery_data_blocks_progression():
    result = evaluate_training_adaptation(
        user_id=1,
        reference_date=REFERENCE_DATE,
        profile_loader=fake_profile,
        training_loader=strong_training,
        progression_loader=positive_progression,
        recovery_loader=insufficient_recovery
    )

    if result["action"] != ACTION_MAINTAIN:
        raise ValueError("FAIL: Sparse RPE/RIR data allowed training progression")

    if "RECOVERY_DATA_INSUFFICIENT_FOR_PROGRESSION" not in result["reason_codes"]:
        raise ValueError("FAIL: Missing recovery-data reason was lost")

    print("PASS: Cautious progression requires enough recent RPE and RIR data")


def test_positive_progression_with_normal_recovery_proposes_progression():
    result = evaluate_training_adaptation(
        user_id=1,
        reference_date=REFERENCE_DATE,
        profile_loader=fake_profile,
        training_loader=strong_training,
        progression_loader=positive_progression,
        recovery_loader=normal_recovery
    )

    if result["action"] != ACTION_PROGRESS_CAUTIOUSLY:
        raise ValueError(f"FAIL: Strong safe training data returned {result['action']}")

    if result["recommendation"]["automatic_application"] is not False:
        raise ValueError("FAIL: Adaptation proposal allowed automatic application")

    if result["recommendation"]["requires_user_confirmation"] is not True:
        raise ValueError("FAIL: Progression proposal does not require confirmation")

    print("PASS: Positive progression with normal exertion creates cautious proposal")


def test_high_exertion_plus_negative_progression_proposes_reduction():
    result = evaluate_training_adaptation(
        user_id=1,
        reference_date=REFERENCE_DATE,
        profile_loader=fake_profile,
        training_loader=strong_training,
        progression_loader=negative_progression,
        recovery_loader=high_exertion_recovery
    )

    if result["action"] != ACTION_REDUCE_VOLUME:
        raise ValueError(f"FAIL: High exertion plus decline returned {result['action']}")

    if result["recommendation"]["requires_user_confirmation"] is not True:
        raise ValueError("FAIL: Volume-reduction proposal does not require confirmation")

    if result["recommendation"]["automatic_application"] is not False:
        raise ValueError("FAIL: Volume reduction was marked for automatic application")

    print("PASS: High exertion plus declining progression can propose volume reduction")


def test_high_exertion_without_decline_does_not_reduce_volume():
    result = evaluate_training_adaptation(
        user_id=1,
        reference_date=REFERENCE_DATE,
        profile_loader=fake_profile,
        training_loader=strong_training,
        progression_loader=positive_progression,
        recovery_loader=high_exertion_recovery
    )

    if result["action"] != ACTION_MAINTAIN:
        raise ValueError("FAIL: High exertion alone triggered volume reduction")

    if "NO_DECLINING_PROGRESSION_CONFIRMATION" not in result["reason_codes"]:
        raise ValueError("FAIL: Conservative high-exertion reason was not preserved")

    print("PASS: High exertion alone cannot trigger training-volume reduction")


def test_sparse_recent_training_maintains_plan():
    result = evaluate_training_adaptation(
        user_id=1,
        reference_date=REFERENCE_DATE,
        profile_loader=fake_profile,
        training_loader=sparse_recent_training,
        progression_loader=positive_progression,
        recovery_loader=normal_recovery
    )

    if result["action"] != ACTION_MAINTAIN:
        raise ValueError("FAIL: Sparse recent training incorrectly triggered adaptation")

    print("PASS: Sparse recent training prevents progression or reduction")


def test_invalid_user_id_rejected():
    try:
        evaluate_training_adaptation(
            user_id=True,
            reference_date=REFERENCE_DATE,
            profile_loader=fake_profile,
            training_loader=strong_training,
            progression_loader=positive_progression,
            recovery_loader=normal_recovery
        )

    except ValueError:
        print("PASS: Adaptation evaluator rejects invalid user identity")
        return

    raise ValueError("FAIL: Invalid adaptation user ID was accepted")


if __name__ == "__main__":
    test_recent_workout_count()
    test_expected_sessions()
    test_progression_summary()
    test_missing_profile_returns_insufficient_data()
    test_too_few_completed_workouts_blocks_adaptation()
    test_low_logging_coverage_blocks_adaptation()
    test_insufficient_recovery_data_blocks_progression()
    test_positive_progression_with_normal_recovery_proposes_progression()
    test_high_exertion_plus_negative_progression_proposes_reduction()
    test_high_exertion_without_decline_does_not_reduce_volume()
    test_sparse_recent_training_maintains_plan()
    test_invalid_user_id_rejected()
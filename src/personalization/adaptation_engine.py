from datetime import date, datetime, timedelta

from src.analytics.progression_analytics import (
    get_progression_analytics_overview
)

from src.analytics.training_analytics import (
    get_training_analytics_overview
)

from src.database.query_user_database import (
    get_user_profile
)


ACTION_INSUFFICIENT_DATA = "insufficient_data"
ACTION_MAINTAIN = "maintain"
ACTION_PROGRESS_CAUTIOUSLY = "progress_cautiously"
ACTION_REDUCE_VOLUME = "reduce_volume"


MIN_COMPLETED_WORKOUTS = 3
MIN_LOG_COVERAGE_PERCENTAGE = 50.0
RECENT_WINDOW_DAYS = 14
MIN_RECENT_COMPLETION_RATIO_FOR_PROGRESSION = 0.75
MIN_POSITIVE_PROGRESSION_RATIO = 0.50
MIN_EXERCISE_WORKOUTS_FOR_PROGRESSION = 2


def validate_user_id(user_id):
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id < 1:
        raise ValueError("user_id must be a positive integer")


def normalize_reference_date(reference_date=None):
    if reference_date is None:
        return date.today()

    if isinstance(reference_date, datetime):
        return reference_date.date()

    if isinstance(reference_date, date):
        return reference_date

    if isinstance(reference_date, str):
        value = reference_date.strip()

        if not value:
            raise ValueError("reference_date cannot be empty")

        try:
            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            ).date()

        except ValueError as error:
            raise ValueError("reference_date must be an ISO date or datetime") from error

    raise ValueError("reference_date must be a date, datetime, ISO string, or None")


def normalize_started_at(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            return None

        try:
            return datetime.fromisoformat(
                normalized.replace(
                    "Z",
                    "+00:00"
                )
            ).date()

        except ValueError:
            return None

    return None


def get_required_dictionary(container, key):
    if not isinstance(container, dict):
        raise ValueError("Analytics result must be a dictionary")

    value = container.get(
        key
    )

    if not isinstance(value, dict):
        raise ValueError(f"Analytics result requires dictionary section: {key}")

    return value


def get_required_list(container, key):
    if not isinstance(container, dict):
        raise ValueError("Analytics result must be a dictionary")

    value = container.get(
        key
    )

    if not isinstance(value, list):
        raise ValueError(f"Analytics result requires list section: {key}")

    return value


def calculate_recent_completed_workouts(
    workout_breakdown,
    reference_date,
    window_days=RECENT_WINDOW_DAYS
):
    if not isinstance(workout_breakdown, list):
        raise ValueError("workout_breakdown must be a list")

    if not isinstance(window_days, int) or isinstance(window_days, bool) or window_days < 1:
        raise ValueError("window_days must be a positive integer")

    normalized_reference_date = normalize_reference_date(
        reference_date
    )

    start_date = (
        normalized_reference_date
        - timedelta(
            days=window_days - 1
        )
    )

    count = 0

    for workout in workout_breakdown:
        if not isinstance(workout, dict):
            continue

        started_at = normalize_started_at(
            workout.get(
                "started_at"
            )
        )

        if started_at is None:
            continue

        if start_date <= started_at <= normalized_reference_date:
            count += 1

    return count


def calculate_expected_recent_sessions(
    training_days_per_week,
    window_days=RECENT_WINDOW_DAYS
):
    if not isinstance(training_days_per_week, int) or isinstance(training_days_per_week, bool):
        raise ValueError("training_days_per_week must be an integer")

    if training_days_per_week < 0 or training_days_per_week > 7:
        raise ValueError("training_days_per_week must be between 0 and 7")

    if not isinstance(window_days, int) or isinstance(window_days, bool) or window_days < 1:
        raise ValueError("window_days must be a positive integer")

    return round(
        training_days_per_week
        * window_days
        / 7,
        2
    )


def calculate_completion_ratio(
    completed_sessions,
    expected_sessions
):
    if isinstance(completed_sessions, bool) or not isinstance(completed_sessions, (int, float)):
        raise ValueError("completed_sessions must be numeric")

    if isinstance(expected_sessions, bool) or not isinstance(expected_sessions, (int, float)):
        raise ValueError("expected_sessions must be numeric")

    if completed_sessions < 0 or expected_sessions < 0:
        raise ValueError("Session counts cannot be negative")

    if expected_sessions == 0:
        return None

    return round(
        completed_sessions
        / expected_sessions,
        4
    )


def classify_exercise_progression(exercise):
    if not isinstance(exercise, dict):
        raise ValueError("Exercise progression must be a dictionary")

    workout_count = exercise.get(
        "workout_count",
        0
    )

    if not isinstance(workout_count, int) or isinstance(workout_count, bool):
        raise ValueError("Exercise workout_count must be an integer")

    if workout_count < MIN_EXERCISE_WORKOUTS_FOR_PROGRESSION:
        return "insufficient"

    weight_change = exercise.get(
        "max_weight_change_kg"
    )

    volume_change = exercise.get(
        "volume_change_kg"
    )

    changes = [
        value
        for value in (
            weight_change,
            volume_change
        )
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
    ]

    if any(
        value > 0
        for value in changes
    ):
        return "positive"

    if changes and any(
        value < 0
        for value in changes
    ):
        return "negative"

    return "stable"


def summarize_progression(exercise_progression):
    if not isinstance(exercise_progression, list):
        raise ValueError("exercise_progression must be a list")

    summary = {
        "exercise_count": len(
            exercise_progression
        ),
        "eligible_exercise_count": 0,
        "positive_progression_count": 0,
        "stable_progression_count": 0,
        "negative_progression_count": 0,
        "insufficient_progression_count": 0,
        "positive_progression_ratio": None
    }

    for exercise in exercise_progression:
        classification = classify_exercise_progression(
            exercise
        )

        if classification == "insufficient":
            summary[
                "insufficient_progression_count"
            ] += 1

            continue

        summary[
            "eligible_exercise_count"
        ] += 1

        if classification == "positive":
            summary[
                "positive_progression_count"
            ] += 1

        elif classification == "negative":
            summary[
                "negative_progression_count"
            ] += 1

        else:
            summary[
                "stable_progression_count"
            ] += 1

    eligible_count = summary[
        "eligible_exercise_count"
    ]

    if eligible_count > 0:
        summary[
            "positive_progression_ratio"
        ] = round(
            summary[
                "positive_progression_count"
            ]
            / eligible_count,
            4
        )

    return summary


def build_recommendation(
    action
):
    if action == ACTION_PROGRESS_CAUTIOUSLY:
        return {
            "change_type": "training_progression",
            "change_scope": "one training variable at a time",
            "automatic_application": False,
            "requires_user_confirmation": True,
            "message": (
                "The available training data supports considering a cautious progression. "
                "The system should propose a specific change separately and must not apply "
                "it without user confirmation."
            )
        }

    if action == ACTION_REDUCE_VOLUME:
        return {
            "change_type": "training_reduction",
            "change_scope": "not yet enabled",
            "automatic_application": False,
            "requires_user_confirmation": True,
            "message": (
                "Training reduction requires recovery or exertion signals that are not "
                "evaluated by this stage."
            )
        }

    if action == ACTION_MAINTAIN:
        return {
            "change_type": "none",
            "change_scope": None,
            "automatic_application": False,
            "requires_user_confirmation": False,
            "message": "Maintain the current training approach until stronger adaptation evidence is available."
        }

    return {
        "change_type": "none",
        "change_scope": None,
        "automatic_application": False,
        "requires_user_confirmation": False,
        "message": "More reliable training data is required before proposing an adaptation."
    }


def determine_adaptation_action(
    profile,
    completed_workout_count,
    log_coverage_percentage,
    recent_completion_ratio,
    progression_summary
):
    reason_codes = []

    if completed_workout_count < MIN_COMPLETED_WORKOUTS:
        reason_codes.append(
            "INSUFFICIENT_COMPLETED_WORKOUTS"
        )

    if log_coverage_percentage < MIN_LOG_COVERAGE_PERCENTAGE:
        reason_codes.append(
            "INSUFFICIENT_LOG_COVERAGE"
        )

    if reason_codes:
        return (
            ACTION_INSUFFICIENT_DATA,
            reason_codes
        )

    training_days = profile[
        "training_days_per_week"
    ]

    if training_days == 0:
        return (
            ACTION_MAINTAIN,
            [
                "NO_SCHEDULED_TRAINING_DAYS"
            ]
        )

    if recent_completion_ratio is None:
        return (
            ACTION_MAINTAIN,
            [
                "RECENT_COMPLETION_RATIO_UNAVAILABLE"
            ]
        )

    if recent_completion_ratio < 0.50:
        return (
            ACTION_MAINTAIN,
            [
                "RECENT_TRAINING_BELOW_PROGRESSION_THRESHOLD"
            ]
        )

    eligible_count = progression_summary[
        "eligible_exercise_count"
    ]

    if eligible_count == 0:
        return (
            ACTION_MAINTAIN,
            [
                "NO_EXERCISES_WITH_ENOUGH_PROGRESSION_HISTORY"
            ]
        )

    positive_ratio = progression_summary[
        "positive_progression_ratio"
    ]

    if (
        recent_completion_ratio
        >= MIN_RECENT_COMPLETION_RATIO_FOR_PROGRESSION
        and positive_ratio is not None
        and positive_ratio
        >= MIN_POSITIVE_PROGRESSION_RATIO
    ):
        return (
            ACTION_PROGRESS_CAUTIOUSLY,
            [
                "SUFFICIENT_RECENT_TRAINING",
                "POSITIVE_EXERCISE_PROGRESSION"
            ]
        )

    if progression_summary[
        "negative_progression_count"
    ] > 0:
        return (
            ACTION_MAINTAIN,
            [
                "MIXED_OR_NEGATIVE_PROGRESSION",
                "RECOVERY_SIGNAL_REQUIRED_BEFORE_REDUCTION"
            ]
        )

    return (
        ACTION_MAINTAIN,
        [
            "PROGRESSION_THRESHOLD_NOT_REACHED"
        ]
    )


def evaluate_training_adaptation(
    user_id,
    reference_date=None,
    profile_loader=None,
    training_loader=None,
    progression_loader=None
):
    validate_user_id(
        user_id
    )

    normalized_reference_date = normalize_reference_date(
        reference_date
    )

    if profile_loader is None:
        profile_loader = get_user_profile

    if training_loader is None:
        training_loader = get_training_analytics_overview

    if progression_loader is None:
        progression_loader = get_progression_analytics_overview

    if not callable(profile_loader):
        raise ValueError("profile_loader must be callable")

    if not callable(training_loader):
        raise ValueError("training_loader must be callable")

    if not callable(progression_loader):
        raise ValueError("progression_loader must be callable")

    profile = profile_loader(
        user_id
    )

    if profile is None:
        return {
            "user_id": user_id,
            "action": ACTION_INSUFFICIENT_DATA,
            "reason_codes": [
                "PROFILE_REQUIRED"
            ],
            "signals": {
                "reference_date": normalized_reference_date.isoformat()
            },
            "recommendation": build_recommendation(
                ACTION_INSUFFICIENT_DATA
            )
        }

    training_days_per_week = profile.get(
        "training_days_per_week"
    )

    if not isinstance(training_days_per_week, int) or isinstance(training_days_per_week, bool):
        raise ValueError("User profile requires integer training_days_per_week")

    training = training_loader(
        user_id
    )

    progression = progression_loader(
        user_id
    )

    volume = get_required_dictionary(
        training,
        "volume"
    )

    workout_breakdown = get_required_list(
        training,
        "workout_breakdown"
    )

    data_quality = get_required_dictionary(
        progression,
        "data_quality"
    )

    exercise_progression = get_required_list(
        progression,
        "exercise_progression"
    )

    completed_workout_count = volume.get(
        "completed_workout_count"
    )

    if not isinstance(completed_workout_count, int) or isinstance(completed_workout_count, bool):
        raise ValueError("Training analytics requires integer completed_workout_count")

    coverage = data_quality.get(
        "exercise_log_coverage_percentage"
    )

    if isinstance(coverage, bool) or not isinstance(coverage, (int, float)):
        raise ValueError("Progression analytics requires numeric exercise_log_coverage_percentage")

    recent_completed_workouts = calculate_recent_completed_workouts(
        workout_breakdown,
        normalized_reference_date
    )

    expected_recent_sessions = calculate_expected_recent_sessions(
        training_days_per_week
    )

    recent_completion_ratio = calculate_completion_ratio(
        recent_completed_workouts,
        expected_recent_sessions
    )

    progression_summary = summarize_progression(
        exercise_progression
    )

    action, reason_codes = determine_adaptation_action(
        profile=profile,
        completed_workout_count=completed_workout_count,
        log_coverage_percentage=coverage,
        recent_completion_ratio=recent_completion_ratio,
        progression_summary=progression_summary
    )

    return {
        "user_id": user_id,
        "action": action,
        "reason_codes": reason_codes,
        "signals": {
            "reference_date": normalized_reference_date.isoformat(),
            "completed_workout_count": completed_workout_count,
            "exercise_log_coverage_percentage": round(
                coverage,
                2
            ),
            "training_days_per_week": training_days_per_week,
            "recent_window_days": RECENT_WINDOW_DAYS,
            "recent_completed_workouts": recent_completed_workouts,
            "expected_recent_sessions": expected_recent_sessions,
            "recent_completion_ratio": recent_completion_ratio,
            "progression": progression_summary
        },
        "recommendation": build_recommendation(
            action
        )
    }
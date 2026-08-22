from src.database.query_user_database import (
    get_user_profile,
    get_user_equipment_access,
    get_user_exercise_preferences,
    get_user_limitations,
    get_user_nutrition_target,
    get_user_food_allergies
)

from src.database.query_workout_log_database import (
    get_user_workout_history
)

from src.database.query_progress_database import (
    get_activity_history,
    get_body_measurement_history,
    get_progress_history
)


DEFAULT_HISTORY_LIMIT = 5
MAX_HISTORY_LIMIT = 20


def validate_user_context_inputs(
    user_id,
    history_limit
):
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id < 1:
        raise ValueError("user_id must be a positive integer")

    if not isinstance(history_limit, int) or isinstance(history_limit, bool):
        raise ValueError("history_limit must be an integer")

    if history_limit < 1 or history_limit > MAX_HISTORY_LIMIT:
        raise ValueError(f"history_limit must be between 1 and {MAX_HISTORY_LIMIT}")


def normalize_value(
    value
):
    if value is None:
        return None

    if isinstance(
        value,
        dict
    ):
        return {
            key: normalize_value(
                item
            )
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple)
    ):
        return [
            normalize_value(
                item
            )
            for item in value
        ]

    if hasattr(
        value,
        "keys"
    ):
        try:
            return {
                key: normalize_value(
                    value[
                        key
                    ]
                )
                for key in value.keys()
            }
        except (TypeError, KeyError):
            pass

    if hasattr(
        value,
        "item"
    ):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass

    return value


def build_user_context(
    user_id,
    history_limit=DEFAULT_HISTORY_LIMIT
):
    validate_user_context_inputs(
        user_id,
        history_limit
    )

    profile = get_user_profile(
        user_id
    )

    equipment = get_user_equipment_access(
        user_id
    )

    preferences = get_user_exercise_preferences(
        user_id
    )

    limitations = get_user_limitations(
        user_id
    )

    nutrition_target = get_user_nutrition_target(
        user_id
    )

    allergies = get_user_food_allergies(
        user_id
    )

    workout_history = get_user_workout_history(
        user_id,
        limit=history_limit
    )

    progress_history = get_progress_history(
        user_id,
        limit=history_limit
    )

    body_measurements = get_body_measurement_history(
        user_id,
        limit=history_limit
    )

    activities = get_activity_history(
        user_id,
        limit=history_limit
    )

    return {
        "user_id": user_id,
        "profile": normalize_value(
            profile
        ),
        "equipment_access": normalize_value(
            equipment
        ),
        "exercise_preferences": normalize_value(
            preferences
        ),
        "limitations": normalize_value(
            limitations
        ),
        "nutrition_target": normalize_value(
            nutrition_target
        ),
        "food_allergies": normalize_value(
            allergies
        ),
        "recent_workouts": normalize_value(
            workout_history
        ),
        "recent_progress": normalize_value(
            progress_history
        ),
        "recent_body_measurements": normalize_value(
            body_measurements
        ),
        "recent_activities": normalize_value(
            activities
        )
    }


def get_user_context_summary(
    context
):
    if not isinstance(context, dict):
        raise ValueError("User context must be a dictionary")

    return {
        "has_profile": context.get("profile") is not None,
        "equipment_count": len(context.get("equipment_access") or []),
        "preference_count": len(context.get("exercise_preferences") or []),
        "limitation_count": len(context.get("limitations") or []),
        "has_nutrition_target": context.get("nutrition_target") is not None,
        "allergy_count": len(context.get("food_allergies") or []),
        "recent_workout_count": len(context.get("recent_workouts") or []),
        "recent_progress_count": len(context.get("recent_progress") or []),
        "recent_measurement_count": len(context.get("recent_body_measurements") or []),
        "recent_activity_count": len(context.get("recent_activities") or [])
    }
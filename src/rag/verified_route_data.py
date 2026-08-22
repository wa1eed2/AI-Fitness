import json

from src.rag.question_classifier import (
    ROUTE_COACHING,
    ROUTE_NUTRITION,
    ROUTE_PERSONAL_DATA
)


DEFAULT_MAX_VERIFIED_DATA_CHARS = 7000
MIN_MAX_VERIFIED_DATA_CHARS = 500
MAX_MAX_VERIFIED_DATA_CHARS = 20000


SUPPORTED_VERIFIED_DATA_ROUTES = {
    ROUTE_COACHING,
    ROUTE_NUTRITION,
    ROUTE_PERSONAL_DATA
}


def validate_user_id(user_id):
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id < 1:
        raise ValueError("user_id must be a positive integer")


def validate_verified_data_char_limit(max_chars):
    if not isinstance(max_chars, int) or isinstance(max_chars, bool):
        raise ValueError("max_verified_data_chars must be an integer")

    if max_chars < MIN_MAX_VERIFIED_DATA_CHARS or max_chars > MAX_MAX_VERIFIED_DATA_CHARS:
        raise ValueError(f"max_verified_data_chars must be between {MIN_MAX_VERIFIED_DATA_CHARS} and {MAX_MAX_VERIFIED_DATA_CHARS}")


def to_json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {
            str(key): to_json_safe(item)
            for key, item in value.items()
        }

    if hasattr(value, "keys") and callable(value.keys):
        return {
            str(key): to_json_safe(value[key])
            for key in value.keys()
        }

    if isinstance(value, (list, tuple)):
        return [
            to_json_safe(item)
            for item in value
        ]

    if isinstance(value, set):
        return [
            to_json_safe(item)
            for item in sorted(
                value,
                key=str
            )
        ]

    isoformat = getattr(
        value,
        "isoformat",
        None
    )

    if callable(isoformat):
        try:
            return isoformat()
        except (TypeError, ValueError):
            pass

    return str(
        value
    )


def load_nutrition_route_data(user_id):
    from src.database.query_user_database import (
        get_user_food_allergies,
        get_user_nutrition_target
    )

    return {
        "nutrition_target": get_user_nutrition_target(
            user_id
        ),
        "food_allergies": get_user_food_allergies(
            user_id
        )
    }


def load_personal_analytics_route_data(user_id):
    from src.analytics.dashboard_analytics import (
        get_dashboard_analytics
    )

    from src.analytics.progression_analytics import (
        get_progression_analytics_overview
    )

    from src.analytics.training_analytics import (
        get_training_analytics_overview
    )

    from src.analytics.trend_analytics import (
        get_trend_analytics_overview
    )

    return {
        "dashboard_analytics": get_dashboard_analytics(
            user_id
        ),
        "training_analytics": get_training_analytics_overview(
            user_id
        ),
        "trend_analytics": get_trend_analytics_overview(
            user_id
        ),
        "progression_analytics": get_progression_analytics_overview(
            user_id
        )
    }


def build_verified_route_data(
    user_id,
    route,
    nutrition_loader=None,
    analytics_loader=None
):
    validate_user_id(
        user_id
    )

    if route not in SUPPORTED_VERIFIED_DATA_ROUTES:
        raise ValueError("Unsupported verified-data route")

    if nutrition_loader is None:
        nutrition_loader = load_nutrition_route_data

    if analytics_loader is None:
        analytics_loader = load_personal_analytics_route_data

    if not callable(nutrition_loader):
        raise ValueError("nutrition_loader must be callable")

    if not callable(analytics_loader):
        raise ValueError("analytics_loader must be callable")

    if route == ROUTE_NUTRITION:
        return {
            "route": route,
            "source": "deterministic_nutrition_system",
            "data": to_json_safe(
                nutrition_loader(
                    user_id
                )
            )
        }

    if route == ROUTE_PERSONAL_DATA:
        return {
            "route": route,
            "source": "deterministic_analytics_system",
            "data": to_json_safe(
                analytics_loader(
                    user_id
                )
            )
        }

    return {
        "route": route,
        "source": "no_route_specific_tool",
        "data": {}
    }


def get_verified_route_data_summary(route_data):
    if not isinstance(route_data, dict):
        raise ValueError("Verified route data must be a dictionary")

    data = route_data.get(
        "data",
        {}
    )

    if not isinstance(data, dict):
        raise ValueError("Verified route data payload must be a dictionary")

    available_sections = list(
        data.keys()
    )

    non_empty_sections = [
        key
        for key, value in data.items()
        if value not in (
            None,
            "",
            [],
            {}
        )
    ]

    return {
        "route": route_data.get(
            "route"
        ),
        "source": route_data.get(
            "source"
        ),
        "available_sections": available_sections,
        "non_empty_sections": non_empty_sections
    }


def serialize_verified_route_data(
    route_data,
    max_chars=DEFAULT_MAX_VERIFIED_DATA_CHARS
):
    if not isinstance(route_data, dict):
        raise ValueError("Verified route data must be a dictionary")

    validate_verified_data_char_limit(
        max_chars
    )

    safe_data = to_json_safe(
        route_data
    )

    serialized = json.dumps(
        safe_data,
        ensure_ascii=False,
        indent=2,
        sort_keys=True
    )

    if len(serialized) <= max_chars:
        return serialized

    marker = "\n...[VERIFIED ROUTE DATA TRUNCATED]"

    available = (
        max_chars
        - len(marker)
    )

    if available <= 0:
        return marker[
            :max_chars
        ]

    return (
        serialized[
            :available
        ]
        + marker
    )
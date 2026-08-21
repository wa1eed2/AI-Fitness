from datetime import date, datetime

from fastapi import APIRouter

from src.analytics.fitness_analytics import (
    get_analytics_overview
)

from src.analytics.training_analytics import (
    get_training_analytics_overview
)

from src.analytics.trend_analytics import (
    get_trend_analytics_overview
)

from src.analytics.dashboard_analytics import (
    get_dashboard_analytics
)

from src.analytics.progression_analytics import (
    get_progression_analytics_overview,
    get_exercise_progression_overview,
    get_exercise_progression,
    get_training_data_quality_analytics
)


router = APIRouter(
    prefix="/api/v1/users/{user_id}/analytics",
    tags=["Analytics"]
)


def normalize_payload(
    value
):
    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool
        )
    ):
        return value

    if isinstance(
        value,
        (
            date,
            datetime
        )
    ):
        return value.isoformat()

    if isinstance(
        value,
        dict
    ):
        return {
            key: normalize_payload(
                item
            )
            for key, item in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set
        )
    ):
        return [
            normalize_payload(
                item
            )
            for item in value
        ]

    if hasattr(
        value,
        "keys"
    ):
        return {
            key: normalize_payload(
                value[key]
            )
            for key in value.keys()
        }

    if hasattr(
        value,
        "item"
    ) and callable(
        value.item
    ):
        return normalize_payload(
            value.item()
        )

    return value


@router.get("")
def get_fitness_analytics_endpoint(
    user_id: int
):
    return normalize_payload(
        get_analytics_overview(
            user_id
        )
    )


@router.get("/training")
def get_training_analytics_endpoint(
    user_id: int
):
    return normalize_payload(
        get_training_analytics_overview(
            user_id
        )
    )


@router.get("/trends")
def get_trend_analytics_endpoint(
    user_id: int,
    reference_date: str | None = None
):
    return normalize_payload(
        get_trend_analytics_overview(
            user_id,
            reference_date=reference_date
        )
    )


@router.get("/dashboard")
def get_dashboard_analytics_endpoint(
    user_id: int,
    reference_date: str | None = None
):
    return normalize_payload(
        get_dashboard_analytics(
            user_id,
            reference_date=reference_date
        )
    )


@router.get("/progression")
def get_progression_analytics_endpoint(
    user_id: int
):
    return normalize_payload(
        get_progression_analytics_overview(
            user_id
        )
    )


@router.get("/progression/exercises")
def get_exercise_progression_overview_endpoint(
    user_id: int
):
    return normalize_payload(
        get_exercise_progression_overview(
            user_id
        )
    )


@router.get("/progression/exercises/{exercise_id}")
def get_exercise_progression_endpoint(
    user_id: int,
    exercise_id: str
):
    return normalize_payload(
        get_exercise_progression(
            user_id,
            exercise_id
        )
    )


@router.get("/data-quality")
def get_training_data_quality_endpoint(
    user_id: int
):
    return normalize_payload(
        get_training_data_quality_analytics(
            user_id
        )
    )
from decimal import (
    Decimal,
    ROUND_HALF_UP
)

from src.database.query_adaptation_application_database import (
    create_profile_adaptation_application,
    get_adaptation_application_by_proposal,
    rollback_profile_adaptation_application
)

from src.database.query_adaptation_database import (
    get_adaptation_proposal
)

from src.database.query_user_database import (
    get_user_profile
)

from src.database.validate_user_profile import (
    validate_user_profile
)


ACTION_PROGRESS_CAUTIOUSLY = "progress_cautiously"
ACTION_REDUCE_VOLUME = "reduce_volume"

ADAPTIVE_FIELD = "session_duration_minutes"

POLICY_VERSION = "session-duration-v1"

PROGRESSION_PERCENT = 0.10
REDUCTION_PERCENT = 0.15

MIN_ABSOLUTE_CHANGE_MINUTES = 1
MAX_ABSOLUTE_CHANGE_MINUTES = 10

MIN_ADAPTIVE_SESSION_DURATION = 15
MAX_ADAPTIVE_SESSION_DURATION = 120


PROFILE_VALIDATION_FIELDS = (
    "age",
    "sex",
    "height_cm",
    "weight_kg",
    "fitness_level",
    "primary_goal",
    "training_days_per_week",
    "session_duration_minutes",
    "preferred_environment"
)


class AdaptationProposalNotFoundError(LookupError):
    pass


class AdaptationApplicationNotFoundError(LookupError):
    pass


class AdaptationAlreadyAppliedError(RuntimeError):
    pass


def validate_duration(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Session duration must be numeric")

    if value <= 0:
        raise ValueError("Session duration must be greater than 0")

    if float(value).is_integer() is not True:
        raise ValueError("Session duration must represent a whole number of minutes")

    return int(
        value
    )


def round_half_up_to_integer(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Adaptive duration change must be numeric")

    return int(
        Decimal(
            str(
                value
            )
        ).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )
    )


def calculate_bounded_delta(raw_delta):
    rounded_delta = round_half_up_to_integer(
        raw_delta
    )

    return min(
        max(
            rounded_delta,
            MIN_ABSOLUTE_CHANGE_MINUTES
        ),
        MAX_ABSOLUTE_CHANGE_MINUTES
    )


def derive_session_duration_change(
    action,
    current_duration_minutes
):
    current = validate_duration(
        current_duration_minutes
    )

    if action == ACTION_PROGRESS_CAUTIOUSLY:
        if current >= MAX_ADAPTIVE_SESSION_DURATION:
            raise ValueError("Session duration is already at the adaptive maximum")

        raw_delta = (
            current
            * PROGRESSION_PERCENT
        )

        delta = calculate_bounded_delta(
            raw_delta
        )

        after = min(
            current + delta,
            MAX_ADAPTIVE_SESSION_DURATION
        )

    elif action == ACTION_REDUCE_VOLUME:
        if current <= MIN_ADAPTIVE_SESSION_DURATION:
            raise ValueError("Session duration is already at the adaptive minimum")

        raw_delta = (
            current
            * REDUCTION_PERCENT
        )

        delta = calculate_bounded_delta(
            raw_delta
        )

        after = max(
            current - delta,
            MIN_ADAPTIVE_SESSION_DURATION
        )

    else:
        raise ValueError("This adaptation action cannot modify training")

    after = int(
        after
    )

    change_amount = (
        after
        - current
    )

    change_percent = round(
        change_amount
        / current
        * 100,
        2
    )

    return {
        "field_name": ADAPTIVE_FIELD,
        "before_value": current,
        "after_value": after,
        "change_amount": change_amount,
        "change_percent": change_percent,
        "policy_version": POLICY_VERSION
    }


def build_profile_validation_payload(
    profile,
    new_session_duration
):
    if not isinstance(profile, dict):
        raise ValueError("User profile must be a dictionary")

    payload = {
        field: profile.get(
            field
        )
        for field in PROFILE_VALIDATION_FIELDS
    }

    payload[
        ADAPTIVE_FIELD
    ] = new_session_duration

    return payload


def validate_prospective_profile(
    profile,
    change
):
    payload = build_profile_validation_payload(
        profile,
        change[
            "after_value"
        ]
    )

    validate_user_profile(
        payload
    )

    return payload


def apply_accepted_adaptation(
    user_id,
    proposal_id
):
    proposal = get_adaptation_proposal(
        user_id,
        proposal_id
    )

    if proposal is None:
        raise AdaptationProposalNotFoundError("Adaptation proposal not found")

    if proposal[
        "status"
    ] != "accepted":
        raise ValueError("Adaptation proposal must be accepted before application")

    action = proposal[
        "action"
    ]

    if action not in {
        ACTION_PROGRESS_CAUTIOUSLY,
        ACTION_REDUCE_VOLUME
    }:
        raise ValueError("This adaptation proposal does not contain an applicable training change")

    existing = get_adaptation_application_by_proposal(
        user_id,
        proposal_id
    )

    if existing is not None:
        raise AdaptationAlreadyAppliedError("Adaptation proposal has already been applied")

    profile = get_user_profile(
        user_id
    )

    if profile is None:
        raise ValueError("User profile not found")

    change = derive_session_duration_change(
        action,
        profile[
            ADAPTIVE_FIELD
        ]
    )

    validate_prospective_profile(
        profile,
        change
    )

    try:
        application = create_profile_adaptation_application(
            user_id=user_id,
            proposal_id=proposal_id,
            action=action,
            field_name=change[
                "field_name"
            ],
            before_value=change[
                "before_value"
            ],
            after_value=change[
                "after_value"
            ],
            change_amount=change[
                "change_amount"
            ],
            change_percent=change[
                "change_percent"
            ],
            policy_version=change[
                "policy_version"
            ]
        )

    except ValueError as error:
        if "already been applied" in str(
            error
        ):
            raise AdaptationAlreadyAppliedError(str(error)) from error

        raise

    updated_profile = get_user_profile(
        user_id
    )

    return {
        "proposal": proposal,
        "application": application,
        "profile": updated_profile,
        "applied": True
    }


def rollback_applied_adaptation(
    user_id,
    application_id
):
    application = rollback_profile_adaptation_application(
        user_id,
        application_id
    )

    if application is None:
        raise AdaptationApplicationNotFoundError("Adaptation application not found")

    profile = get_user_profile(
        user_id
    )

    return {
        "application": application,
        "profile": profile,
        "rolled_back": True
    }
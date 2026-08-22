from src.database.query_adaptation_database import (
    create_adaptation_proposal,
    resolve_adaptation_proposal
)

from src.database.query_user_database import (
    create_user,
    create_user_profile,
    delete_user,
    get_user_profile
)

from src.personalization.adaptation_application_service import (
    AdaptationAlreadyAppliedError,
    apply_accepted_adaptation,
    derive_session_duration_change,
    rollback_applied_adaptation
)


def valid_profile(
    session_duration_minutes=60
):
    return {
        "age": 30,
        "sex": "Male",
        "height_cm": 180,
        "weight_kg": 80,
        "fitness_level": "Intermediate",
        "primary_goal": "General Fitness",
        "training_days_per_week": 3,
        "session_duration_minutes": session_duration_minutes,
        "preferred_environment": "Gym"
    }


def sample_evaluation(
    action
):
    return {
        "action": action,
        "reason_codes": [
            "TEST_SIGNAL"
        ],
        "signals": {
            "test": True
        },
        "recommendation": {
            "change_type": "training",
            "automatic_application": False,
            "requires_user_confirmation": True
        }
    }


def create_accepted_proposal(
    user_id,
    action
):
    proposal = create_adaptation_proposal(
        user_id,
        sample_evaluation(
            action
        )
    )

    return resolve_adaptation_proposal(
        user_id,
        proposal[
            "proposal_id"
        ],
        "accepted"
    )


def test_progression_increases_duration_by_ten_percent():
    change = derive_session_duration_change(
        "progress_cautiously",
        60
    )

    if change["after_value"] != 66:
        raise ValueError(f"FAIL: Expected 66-minute progression, got {change['after_value']}")

    if change["change_percent"] != 10:
        raise ValueError("FAIL: Progression percentage is not 10%")

    print("PASS: Cautious progression applies bounded ten-percent duration increase")


def test_reduction_decreases_duration_by_fifteen_percent():
    change = derive_session_duration_change(
        "reduce_volume",
        60
    )

    if change["after_value"] != 51:
        raise ValueError(f"FAIL: Expected 51-minute reduction, got {change['after_value']}")

    if change["change_percent"] != -15:
        raise ValueError("FAIL: Reduction percentage is not negative fifteen percent")

    print("PASS: Volume reduction applies bounded fifteen-percent duration decrease")


def test_progression_has_absolute_upper_change_bound():
    change = derive_session_duration_change(
        "progress_cautiously",
        110
    )

    if change["after_value"] != 120:
        raise ValueError("FAIL: Progression exceeded ten-minute bounded adjustment")

    if change["change_amount"] != 10:
        raise ValueError("FAIL: Progression absolute change bound is incorrect")

    print("PASS: Progression cannot add more than ten minutes at once")


def test_reduction_has_absolute_duration_floor():
    change = derive_session_duration_change(
        "reduce_volume",
        16
    )

    if change["after_value"] != 15:
        raise ValueError("FAIL: Reduction crossed minimum adaptive duration")

    print("PASS: Volume reduction respects fifteen-minute adaptive floor")


def test_unsupported_action_cannot_modify_profile():
    try:
        derive_session_duration_change(
            "maintain",
            60
        )

    except ValueError:
        print("PASS: Non-applicable adaptation action cannot modify profile")
        return

    raise ValueError("FAIL: Maintain action created a profile modification")


def test_pending_proposal_cannot_be_applied():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = create_adaptation_proposal(
            user_id,
            sample_evaluation(
                "progress_cautiously"
            )
        )

        try:
            apply_accepted_adaptation(
                user_id,
                proposal[
                    "proposal_id"
                ]
            )

        except ValueError:
            if get_user_profile(
                user_id
            )[
                "session_duration_minutes"
            ] != 60:
                raise ValueError("FAIL: Pending proposal modified profile before rejection")

            print("PASS: Pending proposal cannot modify training profile")
            return

        raise ValueError("FAIL: Pending adaptation proposal was applied")

    finally:
        delete_user(
            user_id
        )


def test_accepted_proposal_applies_exact_bounded_change():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = create_accepted_proposal(
            user_id,
            "progress_cautiously"
        )

        result = apply_accepted_adaptation(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        if result["applied"] is not True:
            raise ValueError("FAIL: Accepted adaptation did not report applied state")

        if result["profile"]["session_duration_minutes"] != 66:
            raise ValueError("FAIL: Accepted adaptation did not update session duration")

        if result["application"]["before_value"] != 60:
            raise ValueError("FAIL: Adaptation audit lost before value")

        if result["application"]["after_value"] != 66:
            raise ValueError("FAIL: Adaptation audit lost after value")

        print("PASS: Explicit application performs one bounded audited profile change")

    finally:
        delete_user(
            user_id
        )


def test_same_proposal_cannot_be_applied_twice():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = create_accepted_proposal(
            user_id,
            "progress_cautiously"
        )

        apply_accepted_adaptation(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        try:
            apply_accepted_adaptation(
                user_id,
                proposal[
                    "proposal_id"
                ]
            )

        except AdaptationAlreadyAppliedError:
            print("PASS: Accepted adaptation proposal cannot be applied twice")
            return

        raise ValueError("FAIL: Adaptation proposal was applied more than once")

    finally:
        delete_user(
            user_id
        )


def test_explicit_rollback_restores_previous_duration():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = create_accepted_proposal(
            user_id,
            "reduce_volume"
        )

        applied = apply_accepted_adaptation(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        result = rollback_applied_adaptation(
            user_id,
            applied[
                "application"
            ][
                "application_id"
            ]
        )

        if result["rolled_back"] is not True:
            raise ValueError("FAIL: Rollback did not report success")

        if result["profile"]["session_duration_minutes"] != 60:
            raise ValueError("FAIL: Rollback did not restore original session duration")

        if result["application"]["status"] != "rolled_back":
            raise ValueError("FAIL: Rollback audit status was not updated")

        print("PASS: Explicit adaptation rollback restores audited previous value")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    test_progression_increases_duration_by_ten_percent()
    test_reduction_decreases_duration_by_fifteen_percent()
    test_progression_has_absolute_upper_change_bound()
    test_reduction_has_absolute_duration_floor()
    test_unsupported_action_cannot_modify_profile()
    test_pending_proposal_cannot_be_applied()
    test_accepted_proposal_applies_exact_bounded_change()
    test_same_proposal_cannot_be_applied_twice()
    test_explicit_rollback_restores_previous_duration()
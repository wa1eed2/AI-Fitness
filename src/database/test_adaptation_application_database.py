from src.database.query_adaptation_application_database import (
    create_profile_adaptation_application,
    get_adaptation_application,
    get_adaptation_application_by_proposal,
    get_user_adaptation_applications,
    rollback_profile_adaptation_application
)

from src.database.query_adaptation_database import (
    create_adaptation_proposal,
    resolve_adaptation_proposal
)

from src.database.query_user_database import (
    create_user,
    create_user_profile,
    delete_user,
    get_user_profile,
    update_user_profile
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


def accepted_proposal(
    user_id
):
    evaluation = {
        "action": "progress_cautiously",
        "reason_codes": [
            "TEST"
        ],
        "signals": {
            "test": True
        },
        "recommendation": {
            "requires_user_confirmation": True,
            "automatic_application": False
        }
    }

    proposal = create_adaptation_proposal(
        user_id,
        evaluation
    )

    return resolve_adaptation_proposal(
        user_id,
        proposal[
            "proposal_id"
        ],
        "accepted"
    )


def create_application(
    user_id,
    proposal_id
):
    return create_profile_adaptation_application(
        user_id=user_id,
        proposal_id=proposal_id,
        action="progress_cautiously",
        field_name="session_duration_minutes",
        before_value=60,
        after_value=66,
        change_amount=6,
        change_percent=10,
        policy_version="test-v1"
    )


def test_application_is_persisted():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = accepted_proposal(
            user_id
        )

        application = create_application(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        loaded = get_adaptation_application(
            user_id,
            application[
                "application_id"
            ]
        )

        if loaded is None:
            raise ValueError("FAIL: Adaptation application was not persisted")

        if loaded["status"] != "applied":
            raise ValueError("FAIL: New adaptation application is not marked applied")

        print("PASS: Applied adaptation has persistent audit record")

    finally:
        delete_user(
            user_id
        )


def test_profile_change_and_audit_are_written_together():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = accepted_proposal(
            user_id
        )

        application = create_application(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        profile = get_user_profile(
            user_id
        )

        if profile["session_duration_minutes"] != 66:
            raise ValueError("FAIL: Atomic adaptation transaction did not change profile")

        if application["before_value"] != 60 or application["after_value"] != 66:
            raise ValueError("FAIL: Atomic adaptation audit contains wrong state transition")

        print("PASS: Profile mutation and adaptation audit occur in one transaction")

    finally:
        delete_user(
            user_id
        )


def test_duplicate_application_is_rejected():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = accepted_proposal(
            user_id
        )

        create_application(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        try:
            create_profile_adaptation_application(
                user_id=user_id,
                proposal_id=proposal[
                    "proposal_id"
                ],
                action="progress_cautiously",
                field_name="session_duration_minutes",
                before_value=66,
                after_value=72,
                change_amount=6,
                change_percent=9.09,
                policy_version="test-v1"
            )

        except ValueError:
            print("PASS: Database prevents duplicate application of one proposal")
            return

        raise ValueError("FAIL: Same proposal created multiple application records")

    finally:
        delete_user(
            user_id
        )


def test_application_lookup_is_owner_scoped():
    owner_id = create_user()
    other_id = create_user()

    try:
        create_user_profile(
            owner_id,
            valid_profile()
        )

        proposal = accepted_proposal(
            owner_id
        )

        application = create_application(
            owner_id,
            proposal[
                "proposal_id"
            ]
        )

        result = get_adaptation_application(
            other_id,
            application[
                "application_id"
            ]
        )

        if result is not None:
            raise ValueError("FAIL: Cross-user application audit was visible")

        print("PASS: Adaptation application audit is owner scoped")

    finally:
        delete_user(
            owner_id
        )

        delete_user(
            other_id
        )


def test_application_can_be_found_by_proposal():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = accepted_proposal(
            user_id
        )

        application = create_application(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        loaded = get_adaptation_application_by_proposal(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        if loaded["application_id"] != application["application_id"]:
            raise ValueError("FAIL: Application could not be found from proposal")

        print("PASS: Adaptation proposal links to its application audit")

    finally:
        delete_user(
            user_id
        )


def test_application_history_can_be_listed():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = accepted_proposal(
            user_id
        )

        application = create_application(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        history = get_user_adaptation_applications(
            user_id
        )

        if not any(
            item[
                "application_id"
            ] == application[
                "application_id"
            ]
            for item in history
        ):
            raise ValueError("FAIL: Adaptation application history omitted audit")

        print("PASS: Adaptation application history can be listed")

    finally:
        delete_user(
            user_id
        )


def test_rollback_restores_previous_value():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = accepted_proposal(
            user_id
        )

        application = create_application(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        rolled_back = rollback_profile_adaptation_application(
            user_id,
            application[
                "application_id"
            ]
        )

        profile = get_user_profile(
            user_id
        )

        if profile["session_duration_minutes"] != 60:
            raise ValueError("FAIL: Database rollback did not restore before value")

        if rolled_back["status"] != "rolled_back":
            raise ValueError("FAIL: Database rollback did not update audit status")

        if rolled_back["rolled_back_at"] is None:
            raise ValueError("FAIL: Rollback timestamp was not recorded")

        print("PASS: Adaptation rollback restores previous profile value and records audit")

    finally:
        delete_user(
            user_id
        )


def test_profile_drift_blocks_rollback():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        proposal = accepted_proposal(
            user_id
        )

        application = create_application(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        changed_profile = valid_profile(
            session_duration_minutes=70
        )

        update_user_profile(
            user_id,
            changed_profile
        )

        try:
            rollback_profile_adaptation_application(
                user_id,
                application[
                    "application_id"
                ]
            )

        except ValueError as error:
            if "rollback refused" not in str(
                error
            ):
                raise ValueError(f"FAIL: Wrong profile-drift error: {error}")

            if get_user_profile(
                user_id
            )[
                "session_duration_minutes"
            ] != 70:
                raise ValueError("FAIL: Refused rollback still modified newer profile value")

            print("PASS: Rollback refuses to overwrite later user profile changes")
            return

        raise ValueError("FAIL: Rollback overwrote profile after subsequent change")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    test_application_is_persisted()
    test_profile_change_and_audit_are_written_together()
    test_duplicate_application_is_rejected()
    test_application_lookup_is_owner_scoped()
    test_application_can_be_found_by_proposal()
    test_application_history_can_be_listed()
    test_rollback_restores_previous_value()
    test_profile_drift_blocks_rollback()
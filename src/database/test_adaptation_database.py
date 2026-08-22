from src.database.query_adaptation_database import (
    create_adaptation_proposal,
    delete_adaptation_proposal,
    get_adaptation_proposal,
    get_user_adaptation_proposals,
    resolve_adaptation_proposal
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.setup_adaptation_database import (
    setup_adaptation_database
)


def sample_evaluation(
    action="progress_cautiously"
):
    return {
        "action": action,
        "reason_codes": [
            "SUFFICIENT_RECENT_TRAINING",
            "POSITIVE_EXERCISE_PROGRESSION"
        ],
        "signals": {
            "completed_workout_count": 10,
            "recent_completion_ratio": 1.0,
            "exercise_log_coverage_percentage": 90.0
        },
        "recommendation": {
            "change_type": "training_progression",
            "automatic_application": False,
            "requires_user_confirmation": True
        }
    }


def test_create_and_get_proposal():
    user_id = create_user()

    try:
        proposal = create_adaptation_proposal(
            user_id,
            sample_evaluation()
        )

        loaded = get_adaptation_proposal(
            user_id,
            proposal[
                "proposal_id"
            ]
        )

        if loaded is None:
            raise ValueError("FAIL: Adaptation proposal could not be retrieved")

        if loaded["status"] != "pending":
            raise ValueError("FAIL: New adaptation proposal is not pending")

        if loaded["action"] != "progress_cautiously":
            raise ValueError("FAIL: Adaptation action was not persisted")

        print("PASS: Adaptation proposal can be stored and retrieved")

    finally:
        delete_user(
            user_id
        )


def test_json_fields_round_trip():
    user_id = create_user()

    try:
        proposal = create_adaptation_proposal(
            user_id,
            sample_evaluation()
        )

        if proposal["signals"]["completed_workout_count"] != 10:
            raise ValueError("FAIL: Adaptation signals did not survive JSON storage")

        if proposal["reason_codes"][0] != "SUFFICIENT_RECENT_TRAINING":
            raise ValueError("FAIL: Adaptation reason codes did not survive JSON storage")

        print("PASS: Adaptation proposal structured data round-trips through SQLite")

    finally:
        delete_user(
            user_id
        )


def test_user_proposals_are_owner_scoped():
    owner_id = create_user()
    other_id = create_user()

    try:
        proposal = create_adaptation_proposal(
            owner_id,
            sample_evaluation()
        )

        result = get_adaptation_proposal(
            other_id,
            proposal[
                "proposal_id"
            ]
        )

        if result is not None:
            raise ValueError("FAIL: Cross-user adaptation proposal was visible")

        print("PASS: Adaptation proposals are scoped to authenticated user ownership")

    finally:
        delete_user(
            owner_id
        )

        delete_user(
            other_id
        )


def test_list_user_proposals():
    user_id = create_user()

    try:
        create_adaptation_proposal(
            user_id,
            sample_evaluation(
                "maintain"
            )
        )

        create_adaptation_proposal(
            user_id,
            sample_evaluation(
                "progress_cautiously"
            )
        )

        proposals = get_user_adaptation_proposals(
            user_id,
            limit=20
        )

        if len(proposals) < 2:
            raise ValueError("FAIL: User proposal list omitted stored proposals")

        print("PASS: User adaptation proposal history can be listed")

    finally:
        delete_user(
            user_id
        )


def test_accept_pending_proposal():
    user_id = create_user()

    try:
        proposal = create_adaptation_proposal(
            user_id,
            sample_evaluation()
        )

        resolved = resolve_adaptation_proposal(
            user_id,
            proposal[
                "proposal_id"
            ],
            "accepted"
        )

        if resolved["status"] != "accepted":
            raise ValueError("FAIL: Adaptation proposal was not accepted")

        if resolved["resolved_at"] is None:
            raise ValueError("FAIL: Accepted proposal has no resolution timestamp")

        print("PASS: Pending adaptation proposal can be explicitly accepted")

    finally:
        delete_user(
            user_id
        )


def test_reject_pending_proposal():
    user_id = create_user()

    try:
        proposal = create_adaptation_proposal(
            user_id,
            sample_evaluation()
        )

        resolved = resolve_adaptation_proposal(
            user_id,
            proposal[
                "proposal_id"
            ],
            "rejected"
        )

        if resolved["status"] != "rejected":
            raise ValueError("FAIL: Adaptation proposal was not rejected")

        print("PASS: Pending adaptation proposal can be explicitly rejected")

    finally:
        delete_user(
            user_id
        )


def test_resolved_proposal_cannot_be_resolved_again():
    user_id = create_user()

    try:
        proposal = create_adaptation_proposal(
            user_id,
            sample_evaluation()
        )

        resolve_adaptation_proposal(
            user_id,
            proposal[
                "proposal_id"
            ],
            "accepted"
        )

        try:
            resolve_adaptation_proposal(
                user_id,
                proposal[
                    "proposal_id"
                ],
                "rejected"
            )

        except ValueError:
            print("PASS: Resolved adaptation proposal cannot be changed silently")
            return

        raise ValueError("FAIL: Resolved adaptation proposal was changed a second time")

    finally:
        delete_user(
            user_id
        )


def test_delete_is_owner_scoped():
    owner_id = create_user()
    other_id = create_user()

    try:
        proposal = create_adaptation_proposal(
            owner_id,
            sample_evaluation()
        )

        deleted = delete_adaptation_proposal(
            other_id,
            proposal[
                "proposal_id"
            ]
        )

        if deleted:
            raise ValueError("FAIL: Another user deleted adaptation proposal")

        existing = get_adaptation_proposal(
            owner_id,
            proposal[
                "proposal_id"
            ]
        )

        if existing is None:
            raise ValueError("FAIL: Owner proposal disappeared after unauthorized delete")

        print("PASS: Adaptation proposal deletion is owner scoped")

    finally:
        delete_user(
            owner_id
        )

        delete_user(
            other_id
        )


if __name__ == "__main__":
    setup_adaptation_database()

    test_create_and_get_proposal()
    test_json_fields_round_trip()
    test_user_proposals_are_owner_scoped()
    test_list_user_proposals()
    test_accept_pending_proposal()
    test_reject_pending_proposal()
    test_resolved_proposal_cannot_be_resolved_again()
    test_delete_is_owner_scoped()
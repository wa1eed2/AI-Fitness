from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)

from src.database.query_adaptation_database import (
    create_adaptation_proposal,
    resolve_adaptation_proposal
)

from src.database.query_user_database import (
    create_user_profile,
    get_user_profile
)


def valid_profile():
    return {
        "age": 30,
        "sex": "Male",
        "height_cm": 180,
        "weight_kg": 80,
        "fitness_level": "Intermediate",
        "primary_goal": "General Fitness",
        "training_days_per_week": 3,
        "session_duration_minutes": 60,
        "preferred_environment": "Gym"
    }


def create_proposal(
    user_id,
    action="progress_cautiously",
    accept=False
):
    evaluation = {
        "action": action,
        "reason_codes": [
            "API_TEST"
        ],
        "signals": {
            "api_test": True
        },
        "recommendation": {
            "change_type": "training",
            "automatic_application": False,
            "requires_user_confirmation": True
        }
    }

    proposal = create_adaptation_proposal(
        user_id,
        evaluation
    )

    if accept:
        proposal = resolve_adaptation_proposal(
            user_id,
            proposal[
                "proposal_id"
            ],
            "accepted"
        )

    return proposal


def test_apply_requires_authentication():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-apply-auth"
    )

    try:
        create_user_profile(
            account[
                "user_id"
            ],
            valid_profile()
        )

        proposal = create_proposal(
            account[
                "user_id"
            ],
            accept=True
        )

        response = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply"
        )

        if response.status_code != 401:
            raise ValueError(f"FAIL: Unauthenticated adaptation apply returned HTTP {response.status_code}")

        print("PASS: Applying accepted adaptation requires authentication")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_pending_proposal_cannot_be_applied():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-apply-pending"
    )

    try:
        create_user_profile(
            account[
                "user_id"
            ],
            valid_profile()
        )

        proposal = create_proposal(
            account[
                "user_id"
            ],
            accept=False
        )

        response = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Pending proposal apply returned HTTP {response.status_code}")

        if get_user_profile(
            account[
                "user_id"
            ]
        )[
            "session_duration_minutes"
        ] != 60:
            raise ValueError("FAIL: Pending API proposal changed profile")

        print("PASS: API refuses to apply proposal before explicit acceptance")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_accepted_proposal_can_be_explicitly_applied():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-apply-success"
    )

    try:
        create_user_profile(
            account[
                "user_id"
            ],
            valid_profile()
        )

        proposal = create_proposal(
            account[
                "user_id"
            ],
            accept=True
        )

        response = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Accepted adaptation apply returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["applied"] is not True:
            raise ValueError("FAIL: API application did not report applied state")

        if data["profile"]["session_duration_minutes"] != 66:
            raise ValueError("FAIL: API applied incorrect bounded profile change")

        if data["application"]["field_name"] != "session_duration_minutes":
            raise ValueError("FAIL: API applied non-allowlisted field")

        print("PASS: API explicitly applies one bounded accepted adaptation")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_cross_user_proposal_cannot_be_applied():
    client = create_test_client()

    owner = register_account(
        client,
        "adaptation-apply-owner"
    )

    other = register_account(
        client,
        "adaptation-apply-other"
    )

    try:
        create_user_profile(
            owner[
                "user_id"
            ],
            valid_profile()
        )

        create_user_profile(
            other[
                "user_id"
            ],
            valid_profile()
        )

        proposal = create_proposal(
            owner[
                "user_id"
            ],
            accept=True
        )

        response = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply",
            headers=auth_headers(
                other
            )
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Cross-user adaptation apply returned HTTP {response.status_code}")

        print("PASS: Adaptation application API enforces proposal ownership")

    finally:
        safe_delete_user(
            owner[
                "user_id"
            ]
        )

        safe_delete_user(
            other[
                "user_id"
            ]
        )


def test_proposal_cannot_be_applied_twice():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-apply-twice"
    )

    try:
        create_user_profile(
            account[
                "user_id"
            ],
            valid_profile()
        )

        proposal = create_proposal(
            account[
                "user_id"
            ],
            accept=True
        )

        first = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply",
            headers=auth_headers(
                account
            )
        )

        if first.status_code != 200:
            raise ValueError("FAIL: Initial adaptation application failed")

        second = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply",
            headers=auth_headers(
                account
            )
        )

        if second.status_code != 409:
            raise ValueError(f"FAIL: Duplicate adaptation apply returned HTTP {second.status_code}")

        print("PASS: API prevents duplicate application of accepted proposal")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_application_history_is_owner_scoped():
    client = create_test_client()

    owner = register_account(
        client,
        "adaptation-history-owner"
    )

    other = register_account(
        client,
        "adaptation-history-other"
    )

    try:
        create_user_profile(
            owner[
                "user_id"
            ],
            valid_profile()
        )

        proposal = create_proposal(
            owner[
                "user_id"
            ],
            accept=True
        )

        applied = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply",
            headers=auth_headers(
                owner
            )
        )

        if applied.status_code != 200:
            raise ValueError("FAIL: Could not create application history fixture")

        owner_history = client.get(
            "/api/v1/adaptations/applications/history",
            headers=auth_headers(
                owner
            )
        )

        other_history = client.get(
            "/api/v1/adaptations/applications/history",
            headers=auth_headers(
                other
            )
        )

        if owner_history.status_code != 200 or other_history.status_code != 200:
            raise ValueError("FAIL: Adaptation application history endpoint failed")

        if len(
            owner_history.json()
        ) < 1:
            raise ValueError("FAIL: Owner application history omitted audit")

        if other_history.json():
            raise ValueError("FAIL: Another user could see adaptation application audit")

        print("PASS: Adaptation application history is authenticated and owner scoped")

    finally:
        safe_delete_user(
            owner[
                "user_id"
            ]
        )

        safe_delete_user(
            other[
                "user_id"
            ]
        )


def test_applied_adaptation_can_be_explicitly_rolled_back():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-api-rollback"
    )

    try:
        create_user_profile(
            account[
                "user_id"
            ],
            valid_profile()
        )

        proposal = create_proposal(
            account[
                "user_id"
            ],
            action="reduce_volume",
            accept=True
        )

        applied_response = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply",
            headers=auth_headers(
                account
            )
        )

        if applied_response.status_code != 200:
            raise ValueError(f"FAIL: Could not apply rollback fixture: {applied_response.text}")

        application_id = applied_response.json()[
            "application"
        ][
            "application_id"
        ]

        if get_user_profile(
            account[
                "user_id"
            ]
        )[
            "session_duration_minutes"
        ] != 51:
            raise ValueError("FAIL: Reduction fixture did not apply expected value")

        rollback_response = client.post(
            f"/api/v1/adaptations/applications/{application_id}/rollback",
            headers=auth_headers(
                account
            )
        )

        if rollback_response.status_code != 200:
            raise ValueError(f"FAIL: Rollback returned HTTP {rollback_response.status_code}: {rollback_response.text}")

        data = rollback_response.json()

        if data["rolled_back"] is not True:
            raise ValueError("FAIL: API rollback did not report success")

        if data["profile"]["session_duration_minutes"] != 60:
            raise ValueError("FAIL: API rollback did not restore previous duration")

        print("PASS: API supports explicit audited rollback of applied adaptation")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_cross_user_rollback_is_hidden():
    client = create_test_client()

    owner = register_account(
        client,
        "adaptation-rollback-owner"
    )

    other = register_account(
        client,
        "adaptation-rollback-other"
    )

    try:
        create_user_profile(
            owner[
                "user_id"
            ],
            valid_profile()
        )

        proposal = create_proposal(
            owner[
                "user_id"
            ],
            accept=True
        )

        applied = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/apply",
            headers=auth_headers(
                owner
            )
        )

        application_id = applied.json()[
            "application"
        ][
            "application_id"
        ]

        response = client.post(
            f"/api/v1/adaptations/applications/{application_id}/rollback",
            headers=auth_headers(
                other
            )
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Cross-user rollback returned HTTP {response.status_code}")

        print("PASS: Adaptation rollback hides cross-user application records")

    finally:
        safe_delete_user(
            owner[
                "user_id"
            ]
        )

        safe_delete_user(
            other[
                "user_id"
            ]
        )


def test_openapi_documents_controlled_application_routes():
    client = create_test_client()

    response = client.get(
        "/openapi.json"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: OpenAPI schema could not be retrieved")

    paths = response.json()[
        "paths"
    ]

    required_paths = [
        "/api/v1/adaptations/{proposal_id}/apply",
        "/api/v1/adaptations/{proposal_id}/application",
        "/api/v1/adaptations/applications/history",
        "/api/v1/adaptations/applications/{application_id}/rollback"
    ]

    for path in required_paths:
        if path not in paths:
            raise ValueError(f"FAIL: OpenAPI missing adaptation application route: {path}")

    print("PASS: OpenAPI documents controlled adaptation application and rollback")


if __name__ == "__main__":
    test_apply_requires_authentication()
    test_pending_proposal_cannot_be_applied()
    test_accepted_proposal_can_be_explicitly_applied()
    test_cross_user_proposal_cannot_be_applied()
    test_proposal_cannot_be_applied_twice()
    test_application_history_is_owner_scoped()
    test_applied_adaptation_can_be_explicitly_rolled_back()
    test_cross_user_rollback_is_hidden()
    test_openapi_documents_controlled_application_routes()
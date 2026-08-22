from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)


def create_adaptation(client, account):
    response = client.post(
        "/api/v1/adaptations/evaluate",
        headers=auth_headers(
            account
        ),
        json={
            "reference_date": "2026-08-21"
        }
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Could not create adaptation proposal: {response.text}")

    return response.json()


def test_adaptation_evaluation_requires_authentication():
    client = create_test_client()

    response = client.post(
        "/api/v1/adaptations/evaluate",
        json={}
    )

    if response.status_code != 401:
        raise ValueError(f"FAIL: Unauthenticated adaptation evaluation returned HTTP {response.status_code}")

    print("PASS: Adaptation evaluation requires authentication")


def test_authenticated_user_can_create_proposal():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-create"
    )

    try:
        proposal = create_adaptation(
            client,
            account
        )

        if proposal["user_id"] != account["user_id"]:
            raise ValueError("FAIL: Adaptation proposal used incorrect authenticated user")

        if proposal["status"] != "pending":
            raise ValueError("FAIL: New adaptation proposal is not pending")

        if proposal["action"] != "insufficient_data":
            raise ValueError("FAIL: New user without profile should produce insufficient-data proposal")

        print("PASS: Authenticated user can create deterministic adaptation proposal")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_authenticated_user_can_list_proposals():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-list"
    )

    try:
        created = create_adaptation(
            client,
            account
        )

        response = client.get(
            "/api/v1/adaptations",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Adaptation list returned HTTP {response.status_code}")

        proposals = response.json()

        if not any(
            proposal["proposal_id"] == created["proposal_id"]
            for proposal in proposals
        ):
            raise ValueError("FAIL: Adaptation list omitted user's proposal")

        print("PASS: Authenticated user can list own adaptation proposals")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_authenticated_user_can_get_proposal():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-get"
    )

    try:
        created = create_adaptation(
            client,
            account
        )

        response = client.get(
            f"/api/v1/adaptations/{created['proposal_id']}",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Adaptation detail returned HTTP {response.status_code}")

        if response.json()["proposal_id"] != created["proposal_id"]:
            raise ValueError("FAIL: Adaptation detail returned incorrect proposal")

        print("PASS: Authenticated user can retrieve own adaptation proposal")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_cross_user_proposal_is_hidden():
    client = create_test_client()

    owner = register_account(
        client,
        "adaptation-owner"
    )

    other = register_account(
        client,
        "adaptation-other"
    )

    try:
        proposal = create_adaptation(
            client,
            owner
        )

        response = client.get(
            f"/api/v1/adaptations/{proposal['proposal_id']}",
            headers=auth_headers(
                other
            )
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Cross-user adaptation lookup returned HTTP {response.status_code}")

        print("PASS: Adaptation API hides cross-user proposals")

    finally:
        safe_delete_user(
            owner["user_id"]
        )

        safe_delete_user(
            other["user_id"]
        )


def test_user_can_explicitly_accept_proposal():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-accept"
    )

    try:
        proposal = create_adaptation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/accept",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Adaptation acceptance returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["proposal"]["status"] != "accepted":
            raise ValueError("FAIL: Adaptation proposal was not marked accepted")

        if data["applied"] is not False:
            raise ValueError("FAIL: Accepted adaptation was silently applied")

        print("PASS: User can explicitly accept proposal without applying training change")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_user_can_explicitly_reject_proposal():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-reject"
    )

    try:
        proposal = create_adaptation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/reject",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Adaptation rejection returned HTTP {response.status_code}")

        data = response.json()

        if data["proposal"]["status"] != "rejected":
            raise ValueError("FAIL: Adaptation proposal was not rejected")

        if data["applied"] is not False:
            raise ValueError("FAIL: Rejected adaptation unexpectedly applied change")

        print("PASS: User can explicitly reject adaptation proposal")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_resolved_proposal_cannot_be_changed_again():
    client = create_test_client()

    account = register_account(
        client,
        "adaptation-resolve-once"
    )

    try:
        proposal = create_adaptation(
            client,
            account
        )

        first = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/accept",
            headers=auth_headers(
                account
            )
        )

        if first.status_code != 200:
            raise ValueError("FAIL: Initial adaptation resolution failed")

        second = client.post(
            f"/api/v1/adaptations/{proposal['proposal_id']}/reject",
            headers=auth_headers(
                account
            )
        )

        if second.status_code != 400:
            raise ValueError(f"FAIL: Second adaptation resolution returned HTTP {second.status_code}")

        print("PASS: Adaptation API prevents silently changing resolved proposal")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_openapi_documents_adaptation_routes():
    client = create_test_client()

    response = client.get(
        "/openapi.json"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: OpenAPI schema could not be retrieved")

    paths = response.json()[
        "paths"
    ]

    required = [
        "/api/v1/adaptations/evaluate",
        "/api/v1/adaptations",
        "/api/v1/adaptations/{proposal_id}",
        "/api/v1/adaptations/{proposal_id}/accept",
        "/api/v1/adaptations/{proposal_id}/reject"
    ]

    for path in required:
        if path not in paths:
            raise ValueError(f"FAIL: OpenAPI is missing adaptation route: {path}")

    print("PASS: OpenAPI documents authenticated adaptation workflow")


if __name__ == "__main__":
    test_adaptation_evaluation_requires_authentication()
    test_authenticated_user_can_create_proposal()
    test_authenticated_user_can_list_proposals()
    test_authenticated_user_can_get_proposal()
    test_cross_user_proposal_is_hidden()
    test_user_can_explicitly_accept_proposal()
    test_user_can_explicitly_reject_proposal()
    test_resolved_proposal_cannot_be_changed_again()
    test_openapi_documents_adaptation_routes()
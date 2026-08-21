from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)


def test_add_preferred_exercise():
    client = create_test_client()
    account = register_account(client, "preferred")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/exercise-preferences",
            headers=auth_headers(account),
            json={
                "exercise_id": "E001",
                "preference": "Preferred"
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Preferred exercise returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["exercise_id"] != "E001":
            raise ValueError("FAIL: Preference API returned incorrect exercise")

        if data["preference"] != "Preferred":
            raise ValueError("FAIL: Preference API returned incorrect preference")

        print("PASS: API adds preferred exercise")

    finally:
        safe_delete_user(account["user_id"])


def test_add_disliked_exercise():
    client = create_test_client()
    account = register_account(client, "disliked")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/exercise-preferences",
            headers=auth_headers(account),
            json={
                "exercise_id": "E002",
                "preference": "Disliked"
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Disliked exercise returned HTTP {response.status_code}: {response.text}")

        if response.json()["preference"] != "Disliked":
            raise ValueError("FAIL: Disliked exercise returned incorrect preference")

        print("PASS: API adds disliked exercise")

    finally:
        safe_delete_user(account["user_id"])


def test_get_exercise_preferences():
    client = create_test_client()
    account = register_account(client, "preferences-get")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/exercise-preferences",
            headers=headers,
            json={
                "exercise_id": "E001",
                "preference": "Preferred"
            }
        )

        client.post(
            f"/api/v1/users/{account['user_id']}/exercise-preferences",
            headers=headers,
            json={
                "exercise_id": "E002",
                "preference": "Disliked"
            }
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/exercise-preferences",
            headers=headers
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Exercise preferences GET returned HTTP {response.status_code}: {response.text}")

        preferences = response.json()

        if len(preferences) != 2:
            raise ValueError("FAIL: Exercise preferences GET returned incorrect count")

        exercise_ids = {
            item["exercise_id"]
            for item in preferences
        }

        if exercise_ids != {"E001", "E002"}:
            raise ValueError("FAIL: Exercise preferences GET returned incorrect exercises")

        print("PASS: API retrieves exercise preferences")

    finally:
        safe_delete_user(account["user_id"])


def test_invalid_exercise_preference_rejected():
    client = create_test_client()
    account = register_account(client, "preference-invalid")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/exercise-preferences",
            headers=auth_headers(account),
            json={
                "exercise_id": "E001",
                "preference": "Favorite Forever"
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Invalid exercise preference returned HTTP {response.status_code} instead of 400")

        print("PASS: API rejects invalid exercise preference")

    finally:
        safe_delete_user(account["user_id"])


def test_remove_exercise_preference():
    client = create_test_client()
    account = register_account(client, "preference-remove")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/exercise-preferences",
            headers=headers,
            json={
                "exercise_id": "E001",
                "preference": "Preferred"
            }
        )

        response = client.delete(
            f"/api/v1/users/{account['user_id']}/exercise-preferences/E001",
            headers=headers
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: Exercise preference DELETE returned HTTP {response.status_code}")

        remaining = client.get(
            f"/api/v1/users/{account['user_id']}/exercise-preferences",
            headers=headers
        ).json()

        if remaining != []:
            raise ValueError("FAIL: Exercise preference remained after deletion")

        print("PASS: API removes exercise preference")

    finally:
        safe_delete_user(account["user_id"])


def test_missing_exercise_preference_returns_404():
    client = create_test_client()
    account = register_account(client, "preference-missing")

    try:
        response = client.delete(
            f"/api/v1/users/{account['user_id']}/exercise-preferences/E001",
            headers=auth_headers(account)
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Missing exercise preference returned HTTP {response.status_code} instead of 404")

        print("PASS: Missing exercise preference returns HTTP 404")

    finally:
        safe_delete_user(account["user_id"])


def test_add_user_limitation():
    client = create_test_client()
    account = register_account(client, "limitation-add")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/limitations",
            headers=auth_headers(account),
            json={
                "body_area": "Knee",
                "limitation_type": "Pain",
                "notes": "Avoid painful range"
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Limitation creation returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["body_area"] != "Knee":
            raise ValueError("FAIL: Limitation API returned incorrect body area")

        if data["limitation_type"] != "Pain":
            raise ValueError("FAIL: Limitation API returned incorrect limitation type")

        print("PASS: API adds user limitation")

    finally:
        safe_delete_user(account["user_id"])


def test_invalid_limitation_body_area_rejected():
    client = create_test_client()
    account = register_account(client, "limitation-area")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/limitations",
            headers=auth_headers(account),
            json={
                "body_area": "Wing",
                "limitation_type": "Pain"
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Invalid limitation body area returned HTTP {response.status_code} instead of 400")

        print("PASS: API rejects invalid limitation body area")

    finally:
        safe_delete_user(account["user_id"])


def test_invalid_limitation_type_rejected():
    client = create_test_client()
    account = register_account(client, "limitation-type")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/limitations",
            headers=auth_headers(account),
            json={
                "body_area": "Knee",
                "limitation_type": "Tired"
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Invalid limitation type returned HTTP {response.status_code} instead of 400")

        print("PASS: API rejects invalid limitation type")

    finally:
        safe_delete_user(account["user_id"])


def test_get_user_limitations():
    client = create_test_client()
    account = register_account(client, "limitations-get")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/limitations",
            headers=headers,
            json={
                "body_area": "Knee",
                "limitation_type": "Pain"
            }
        )

        client.post(
            f"/api/v1/users/{account['user_id']}/limitations",
            headers=headers,
            json={
                "body_area": "Shoulder",
                "limitation_type": "Limited ROM"
            }
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/limitations",
            headers=headers
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: User limitations GET returned HTTP {response.status_code}")

        limitations = response.json()

        if len(limitations) != 2:
            raise ValueError("FAIL: User limitations GET returned incorrect count")

        body_areas = {
            item["body_area"]
            for item in limitations
        }

        if body_areas != {"Knee", "Shoulder"}:
            raise ValueError("FAIL: User limitations GET returned incorrect body areas")

        print("PASS: API retrieves user limitations")

    finally:
        safe_delete_user(account["user_id"])


def test_remove_user_limitation():
    client = create_test_client()
    account = register_account(client, "limitation-remove")
    headers = auth_headers(account)

    try:
        created = client.post(
            f"/api/v1/users/{account['user_id']}/limitations",
            headers=headers,
            json={
                "body_area": "Knee",
                "limitation_type": "Pain"
            }
        ).json()

        limitation_id = created["limitation_id"]

        response = client.delete(
            f"/api/v1/users/{account['user_id']}/limitations/{limitation_id}",
            headers=headers
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: User limitation DELETE returned HTTP {response.status_code}")

        remaining = client.get(
            f"/api/v1/users/{account['user_id']}/limitations",
            headers=headers
        ).json()

        if remaining != []:
            raise ValueError("FAIL: User limitation remained after deletion")

        print("PASS: API removes user limitation")

    finally:
        safe_delete_user(account["user_id"])


def test_user_cannot_delete_another_users_limitation():
    client = create_test_client()
    first = register_account(client, "limitation-owner")
    second = register_account(client, "limitation-other")

    try:
        created = client.post(
            f"/api/v1/users/{first['user_id']}/limitations",
            headers=auth_headers(first),
            json={
                "body_area": "Knee",
                "limitation_type": "Pain"
            }
        ).json()

        limitation_id = created["limitation_id"]

        response = client.delete(
            f"/api/v1/users/{second['user_id']}/limitations/{limitation_id}",
            headers=auth_headers(second)
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Another user's limitation ID returned HTTP {response.status_code} instead of 404")

        remaining = client.get(
            f"/api/v1/users/{first['user_id']}/limitations",
            headers=auth_headers(first)
        ).json()

        if len(remaining) != 1:
            raise ValueError("FAIL: Ownership test modified another user's limitation")

        print("PASS: API protects limitation ownership")

    finally:
        safe_delete_user(first["user_id"])
        safe_delete_user(second["user_id"])


def test_add_equipment_access():
    client = create_test_client()
    account = register_account(client, "equipment-add")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=auth_headers(account),
            json={
                "equipment": "Dumbbell",
                "access_status": "Available"
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Equipment creation returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["equipment"] != "Dumbbell":
            raise ValueError("FAIL: Equipment API returned incorrect equipment")

        if data["access_status"] != "Available":
            raise ValueError("FAIL: Equipment API returned incorrect access status")

        print("PASS: API adds equipment access")

    finally:
        safe_delete_user(account["user_id"])


def test_unavailable_equipment_is_supported():
    client = create_test_client()
    account = register_account(client, "equipment-unavailable")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=auth_headers(account),
            json={
                "equipment": "Barbell",
                "access_status": "Unavailable"
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Unavailable equipment returned HTTP {response.status_code}")

        if response.json()["access_status"] != "Unavailable":
            raise ValueError("FAIL: Equipment API returned incorrect unavailable status")

        print("PASS: API stores unavailable equipment access")

    finally:
        safe_delete_user(account["user_id"])


def test_invalid_equipment_rejected():
    client = create_test_client()
    account = register_account(client, "equipment-invalid")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=auth_headers(account),
            json={
                "equipment": "Rocket Launcher",
                "access_status": "Available"
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Invalid equipment returned HTTP {response.status_code} instead of 400")

        print("PASS: API rejects invalid equipment")

    finally:
        safe_delete_user(account["user_id"])


def test_invalid_equipment_status_rejected():
    client = create_test_client()
    account = register_account(client, "equipment-status")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=auth_headers(account),
            json={
                "equipment": "Dumbbell",
                "access_status": "Sometimes"
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Invalid equipment status returned HTTP {response.status_code} instead of 400")

        print("PASS: API rejects invalid equipment access status")

    finally:
        safe_delete_user(account["user_id"])


def test_get_equipment_access():
    client = create_test_client()
    account = register_account(client, "equipment-get")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=headers,
            json={
                "equipment": "Dumbbell",
                "access_status": "Available"
            }
        )

        client.post(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=headers,
            json={
                "equipment": "Barbell",
                "access_status": "Unavailable"
            }
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=headers
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Equipment access GET returned HTTP {response.status_code}")

        equipment = response.json()

        if len(equipment) != 2:
            raise ValueError("FAIL: Equipment access GET returned incorrect count")

        names = {
            item["equipment"]
            for item in equipment
        }

        if names != {"Dumbbell", "Barbell"}:
            raise ValueError("FAIL: Equipment access GET returned incorrect equipment")

        print("PASS: API retrieves equipment access")

    finally:
        safe_delete_user(account["user_id"])


def test_remove_equipment_access():
    client = create_test_client()
    account = register_account(client, "equipment-remove")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=headers,
            json={
                "equipment": "Dumbbell",
                "access_status": "Available"
            }
        )

        response = client.delete(
            f"/api/v1/users/{account['user_id']}/equipment/Dumbbell",
            headers=headers
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: Equipment DELETE returned HTTP {response.status_code}")

        remaining = client.get(
            f"/api/v1/users/{account['user_id']}/equipment",
            headers=headers
        ).json()

        if remaining != []:
            raise ValueError("FAIL: Equipment access remained after deletion")

        print("PASS: API removes equipment access")

    finally:
        safe_delete_user(account["user_id"])


def test_user_settings_are_isolated_by_user():
    client = create_test_client()
    first = register_account(client, "settings-first")
    second = register_account(client, "settings-second")

    try:
        client.post(
            f"/api/v1/users/{first['user_id']}/exercise-preferences",
            headers=auth_headers(first),
            json={
                "exercise_id": "E001",
                "preference": "Preferred"
            }
        )

        client.post(
            f"/api/v1/users/{first['user_id']}/limitations",
            headers=auth_headers(first),
            json={
                "body_area": "Knee",
                "limitation_type": "Pain"
            }
        )

        client.post(
            f"/api/v1/users/{first['user_id']}/equipment",
            headers=auth_headers(first),
            json={
                "equipment": "Dumbbell",
                "access_status": "Available"
            }
        )

        preferences = client.get(
            f"/api/v1/users/{second['user_id']}/exercise-preferences",
            headers=auth_headers(second)
        ).json()

        limitations = client.get(
            f"/api/v1/users/{second['user_id']}/limitations",
            headers=auth_headers(second)
        ).json()

        equipment = client.get(
            f"/api/v1/users/{second['user_id']}/equipment",
            headers=auth_headers(second)
        ).json()

        if preferences != []:
            raise ValueError("FAIL: Exercise preferences leaked between users")

        if limitations != []:
            raise ValueError("FAIL: Limitations leaked between users")

        if equipment != []:
            raise ValueError("FAIL: Equipment access leaked between users")

        print("PASS: User configuration API is isolated by user")

    finally:
        safe_delete_user(first["user_id"])
        safe_delete_user(second["user_id"])


def test_user_settings_routes_appear_in_openapi():
    client = create_test_client()

    response = client.get(
        "/openapi.json"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: OpenAPI schema was unavailable")

    paths = response.json()["paths"]

    expected_paths = {
        "/api/v1/users/{user_id}/exercise-preferences",
        "/api/v1/users/{user_id}/exercise-preferences/{exercise_id}",
        "/api/v1/users/{user_id}/limitations",
        "/api/v1/users/{user_id}/limitations/{limitation_id}",
        "/api/v1/users/{user_id}/equipment",
        "/api/v1/users/{user_id}/equipment/{equipment}"
    }

    if not expected_paths.issubset(set(paths.keys())):
        raise ValueError("FAIL: OpenAPI schema is missing user-settings routes")

    security = paths[
        "/api/v1/users/{user_id}/equipment"
    ][
        "get"
    ].get(
        "security"
    )

    if not security:
        raise ValueError("FAIL: User-settings routes are not documented as authenticated")

    print("PASS: OpenAPI documentation includes authenticated user-settings routes")


if __name__ == "__main__":
    test_add_preferred_exercise()
    test_add_disliked_exercise()
    test_get_exercise_preferences()
    test_invalid_exercise_preference_rejected()
    test_remove_exercise_preference()
    test_missing_exercise_preference_returns_404()

    test_add_user_limitation()
    test_invalid_limitation_body_area_rejected()
    test_invalid_limitation_type_rejected()
    test_get_user_limitations()
    test_remove_user_limitation()
    test_user_cannot_delete_another_users_limitation()

    test_add_equipment_access()
    test_unavailable_equipment_is_supported()
    test_invalid_equipment_rejected()
    test_invalid_equipment_status_rejected()
    test_get_equipment_access()
    test_remove_equipment_access()

    test_user_settings_are_isolated_by_user()
    test_user_settings_routes_appear_in_openapi()
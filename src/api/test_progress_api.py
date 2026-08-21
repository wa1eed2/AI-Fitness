from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)


def test_add_progress_entry():
    client = create_test_client()
    account = register_account(client, "progress-add")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/progress",
            headers=auth_headers(account),
            json={
                "weight_kg": 80,
                "body_fat_percentage": 18,
                "notes": "Baseline"
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Progress entry returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["weight_kg"] != 80:
            raise ValueError("FAIL: Progress API returned incorrect weight")

        print("PASS: API adds progress entry")

    finally:
        safe_delete_user(account["user_id"])


def test_get_progress_history():
    client = create_test_client()
    account = register_account(client, "progress-history")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/progress",
            headers=headers,
            json={"weight_kg": 80}
        )

        client.post(
            f"/api/v1/users/{account['user_id']}/progress",
            headers=headers,
            json={"weight_kg": 79}
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/progress",
            headers=headers
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Progress history returned HTTP {response.status_code}: {response.text}")

        if len(response.json()) != 2:
            raise ValueError("FAIL: Progress history returned incorrect count")

        print("PASS: API retrieves progress history")

    finally:
        safe_delete_user(account["user_id"])


def test_update_progress_entry():
    client = create_test_client()
    account = register_account(client, "progress-update")
    headers = auth_headers(account)

    try:
        created = client.post(
            f"/api/v1/users/{account['user_id']}/progress",
            headers=headers,
            json={"weight_kg": 80}
        ).json()

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/progress/{created['progress_entry_id']}",
            headers=headers,
            json={"weight_kg": 78.5}
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Progress PATCH returned HTTP {response.status_code}: {response.text}")

        if response.json()["weight_kg"] != 78.5:
            raise ValueError("FAIL: Progress PATCH did not update weight")

        print("PASS: API updates progress entry")

    finally:
        safe_delete_user(account["user_id"])


def test_delete_progress_entry():
    client = create_test_client()
    account = register_account(client, "progress-delete")
    headers = auth_headers(account)

    try:
        created = client.post(
            f"/api/v1/users/{account['user_id']}/progress",
            headers=headers,
            json={"weight_kg": 80}
        ).json()

        response = client.delete(
            f"/api/v1/users/{account['user_id']}/progress/{created['progress_entry_id']}",
            headers=headers
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: Progress DELETE returned HTTP {response.status_code}")

        remaining = client.get(
            f"/api/v1/users/{account['user_id']}/progress",
            headers=headers
        ).json()

        if remaining != []:
            raise ValueError("FAIL: Progress entry remained after deletion")

        print("PASS: API deletes progress entry")

    finally:
        safe_delete_user(account["user_id"])


def test_add_body_measurement():
    client = create_test_client()
    account = register_account(client, "measurement-add")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/measurements",
            headers=auth_headers(account),
            json={
                "body_area": "Waist",
                "measurement_cm": 85,
                "notes": "Morning"
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Measurement returned HTTP {response.status_code}: {response.text}")

        if response.json()["body_area"] != "Waist":
            raise ValueError("FAIL: Measurement returned incorrect body area")

        print("PASS: API adds body measurement")

    finally:
        safe_delete_user(account["user_id"])


def test_filter_body_measurements():
    client = create_test_client()
    account = register_account(client, "measurement-filter")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/measurements",
            headers=headers,
            json={
                "body_area": "Waist",
                "measurement_cm": 85
            }
        )

        client.post(
            f"/api/v1/users/{account['user_id']}/measurements",
            headers=headers,
            json={
                "body_area": "Chest",
                "measurement_cm": 100
            }
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/measurements",
            headers=headers,
            params={
                "body_area": "Waist"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Measurement filter returned HTTP {response.status_code}: {response.text}")

        if len(response.json()) != 1:
            raise ValueError("FAIL: Measurement filter returned incorrect count")

        print("PASS: API filters body measurements")

    finally:
        safe_delete_user(account["user_id"])


def test_update_body_measurement():
    client = create_test_client()
    account = register_account(client, "measurement-update")
    headers = auth_headers(account)

    try:
        created = client.post(
            f"/api/v1/users/{account['user_id']}/measurements",
            headers=headers,
            json={
                "body_area": "Waist",
                "measurement_cm": 85
            }
        ).json()

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/measurements/{created['body_measurement_id']}",
            headers=headers,
            json={
                "measurement_cm": 83
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Measurement PATCH returned HTTP {response.status_code}: {response.text}")

        if response.json()["measurement_cm"] != 83:
            raise ValueError("FAIL: Measurement PATCH returned incorrect value")

        print("PASS: API updates body measurement")

    finally:
        safe_delete_user(account["user_id"])


def test_add_activity():
    client = create_test_client()
    account = register_account(client, "activity-add")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/activities",
            headers=auth_headers(account),
            json={
                "activity_type": "Walking",
                "duration_minutes": 45,
                "distance_km": 4,
                "steps": 6000,
                "average_speed_kmh": 5.3,
                "estimated_calories": 250
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Activity returned HTTP {response.status_code}: {response.text}")

        if response.json()["activity_type"] != "Walking":
            raise ValueError("FAIL: Activity API returned incorrect activity type")

        print("PASS: API adds activity log")

    finally:
        safe_delete_user(account["user_id"])


def test_filter_activities():
    client = create_test_client()
    account = register_account(client, "activity-filter")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/activities",
            headers=headers,
            json={
                "activity_type": "Walking",
                "duration_minutes": 30
            }
        )

        client.post(
            f"/api/v1/users/{account['user_id']}/activities",
            headers=headers,
            json={
                "activity_type": "Running",
                "duration_minutes": 20
            }
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/activities",
            headers=headers,
            params={
                "activity_type": "Walking"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Activity filter returned HTTP {response.status_code}: {response.text}")

        if len(response.json()) != 1:
            raise ValueError("FAIL: Activity filter returned incorrect count")

        print("PASS: API filters activity history")

    finally:
        safe_delete_user(account["user_id"])


def test_update_activity():
    client = create_test_client()
    account = register_account(client, "activity-update")
    headers = auth_headers(account)

    try:
        created = client.post(
            f"/api/v1/users/{account['user_id']}/activities",
            headers=headers,
            json={
                "activity_type": "Walking",
                "steps": 5000
            }
        ).json()

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/activities/{created['activity_log_id']}",
            headers=headers,
            json={
                "steps": 7000
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Activity PATCH returned HTTP {response.status_code}: {response.text}")

        if response.json()["steps"] != 7000:
            raise ValueError("FAIL: Activity PATCH returned incorrect steps")

        print("PASS: API updates activity log")

    finally:
        safe_delete_user(account["user_id"])


def test_add_progress_photo_metadata():
    client = create_test_client()
    account = register_account(client, "photo-add")

    try:
        response = client.post(
            f"/api/v1/users/{account['user_id']}/progress-photos",
            headers=auth_headers(account),
            json={
                "file_path": "private/progress/front-001.jpg",
                "view_type": "Front",
                "is_private": True,
                "notes": "Baseline"
            }
        )

        if response.status_code != 201:
            raise ValueError(f"FAIL: Progress photo returned HTTP {response.status_code}: {response.text}")

        if response.json()["is_private"] not in (1, True):
            raise ValueError("FAIL: Progress photo was not stored as private")

        print("PASS: API adds private progress photo metadata")

    finally:
        safe_delete_user(account["user_id"])


def test_filter_progress_photos():
    client = create_test_client()
    account = register_account(client, "photo-filter")
    headers = auth_headers(account)

    try:
        client.post(
            f"/api/v1/users/{account['user_id']}/progress-photos",
            headers=headers,
            json={
                "file_path": "front.jpg",
                "view_type": "Front"
            }
        )

        client.post(
            f"/api/v1/users/{account['user_id']}/progress-photos",
            headers=headers,
            json={
                "file_path": "side.jpg",
                "view_type": "Side"
            }
        )

        response = client.get(
            f"/api/v1/users/{account['user_id']}/progress-photos",
            headers=headers,
            params={
                "view_type": "Front"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Progress photo filter returned HTTP {response.status_code}: {response.text}")

        if len(response.json()) != 1:
            raise ValueError("FAIL: Progress photo filter returned incorrect count")

        print("PASS: API filters progress photos")

    finally:
        safe_delete_user(account["user_id"])


def test_update_progress_photo_metadata():
    client = create_test_client()
    account = register_account(client, "photo-update")
    headers = auth_headers(account)

    try:
        created = client.post(
            f"/api/v1/users/{account['user_id']}/progress-photos",
            headers=headers,
            json={
                "file_path": "front.jpg",
                "view_type": "Front",
                "is_private": True
            }
        ).json()

        response = client.patch(
            f"/api/v1/users/{account['user_id']}/progress-photos/{created['progress_photo_id']}",
            headers=headers,
            json={
                "notes": "Updated note"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Progress photo PATCH returned HTTP {response.status_code}: {response.text}")

        if response.json()["notes"] != "Updated note":
            raise ValueError("FAIL: Progress photo metadata was not updated")

        print("PASS: API updates progress photo metadata")

    finally:
        safe_delete_user(account["user_id"])


def test_delete_progress_photo_metadata():
    client = create_test_client()
    account = register_account(client, "photo-delete")
    headers = auth_headers(account)

    try:
        created = client.post(
            f"/api/v1/users/{account['user_id']}/progress-photos",
            headers=headers,
            json={
                "file_path": "front.jpg",
                "view_type": "Front"
            }
        ).json()

        response = client.delete(
            f"/api/v1/users/{account['user_id']}/progress-photos/{created['progress_photo_id']}",
            headers=headers
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: Progress photo DELETE returned HTTP {response.status_code}")

        remaining = client.get(
            f"/api/v1/users/{account['user_id']}/progress-photos",
            headers=headers
        ).json()

        if remaining != []:
            raise ValueError("FAIL: Progress photo remained after deletion")

        print("PASS: API deletes progress photo metadata")

    finally:
        safe_delete_user(account["user_id"])


def test_progress_data_isolated_by_user():
    client = create_test_client()

    first = register_account(
        client,
        "progress-first"
    )

    second = register_account(
        client,
        "progress-second"
    )

    try:
        client.post(
            f"/api/v1/users/{first['user_id']}/progress",
            headers=auth_headers(first),
            json={
                "weight_kg": 80
            }
        )

        response = client.get(
            f"/api/v1/users/{second['user_id']}/progress",
            headers=auth_headers(second)
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Second user's progress GET returned HTTP {response.status_code}")

        if response.json() != []:
            raise ValueError("FAIL: Progress data leaked between users")

        print("PASS: Progress API is isolated by user")

    finally:
        safe_delete_user(first["user_id"])
        safe_delete_user(second["user_id"])


def test_progress_routes_appear_in_openapi():
    client = create_test_client()

    paths = client.get(
        "/openapi.json"
    ).json()[
        "paths"
    ]

    expected = {
        "/api/v1/users/{user_id}/progress",
        "/api/v1/users/{user_id}/progress/{progress_entry_id}",
        "/api/v1/users/{user_id}/measurements",
        "/api/v1/users/{user_id}/measurements/{body_measurement_id}",
        "/api/v1/users/{user_id}/activities",
        "/api/v1/users/{user_id}/activities/{activity_log_id}",
        "/api/v1/users/{user_id}/progress-photos",
        "/api/v1/users/{user_id}/progress-photos/{progress_photo_id}"
    }

    if not expected.issubset(set(paths.keys())):
        raise ValueError("FAIL: OpenAPI schema is missing progress routes")

    security = paths[
        "/api/v1/users/{user_id}/progress"
    ][
        "get"
    ].get(
        "security"
    )

    if not security:
        raise ValueError("FAIL: Progress routes are not documented as authenticated")

    print("PASS: OpenAPI documentation includes authenticated progress routes")


if __name__ == "__main__":
    test_add_progress_entry()
    test_get_progress_history()
    test_update_progress_entry()
    test_delete_progress_entry()

    test_add_body_measurement()
    test_filter_body_measurements()
    test_update_body_measurement()

    test_add_activity()
    test_filter_activities()
    test_update_activity()

    test_add_progress_photo_metadata()
    test_filter_progress_photos()
    test_update_progress_photo_metadata()
    test_delete_progress_photo_metadata()

    test_progress_data_isolated_by_user()
    test_progress_routes_appear_in_openapi()
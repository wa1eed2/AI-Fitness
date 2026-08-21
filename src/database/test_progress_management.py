from src.database.setup_progress_database import (
    setup_progress_database
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.query_progress_database import (
    add_progress_entry,
    add_body_measurement,
    add_activity_log,
    add_progress_photo,
    get_progress_history,
    get_body_measurement_history,
    get_activity_history,
    get_progress_photo_history
)

from src.database.query_progress_management import (
    update_progress_entry,
    delete_progress_entry,
    update_body_measurement,
    delete_body_measurement,
    update_activity_log,
    delete_activity_log,
    update_progress_photo_metadata
)

from src.progress.progress_timeline import (
    build_progress_timeline,
    get_progress_summary
)


def test_update_progress_entry():
    user_id = create_user()

    try:
        progress_entry_id = add_progress_entry(
            user_id,
            weight_kg=82,
            body_fat_percentage=20,
            notes="Original"
        )

        updated = update_progress_entry(
            user_id,
            progress_entry_id,
            weight_kg=81,
            body_fat_percentage=19.5,
            notes="Updated"
        )

        if updated["weight_kg"] != 81:
            raise ValueError("FAIL: Progress update did not save weight")

        if updated["body_fat_percentage"] != 19.5:
            raise ValueError("FAIL: Progress update did not save body fat")

        if updated["notes"] != "Updated":
            raise ValueError("FAIL: Progress update did not save notes")

        print("PASS: Progress entry updates correctly")

    finally:
        delete_user(user_id)


def test_invalid_progress_update_rejected():
    user_id = create_user()

    try:
        progress_entry_id = add_progress_entry(
            user_id,
            weight_kg=80
        )

        invalid_updates = [
            {
                "weight_kg": 0
            },
            {
                "weight_kg": -1
            },
            {
                "weight_kg": True
            },
            {
                "body_fat_percentage": -1
            },
            {
                "body_fat_percentage": 101
            },
            {
                "body_fat_percentage": True
            }
        ]

        for values in invalid_updates:
            try:
                update_progress_entry(
                    user_id,
                    progress_entry_id,
                    **values
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid progress update was accepted: {values}")

        print("PASS: Invalid progress updates rejected")

    finally:
        delete_user(user_id)


def test_delete_progress_entry():
    user_id = create_user()

    try:
        progress_entry_id = add_progress_entry(
            user_id,
            weight_kg=80
        )

        delete_progress_entry(
            user_id,
            progress_entry_id
        )

        history = get_progress_history(
            user_id
        )

        if len(history) != 0:
            raise ValueError("FAIL: Progress entry was not deleted")

        print("PASS: Progress entry deletes correctly")

    finally:
        delete_user(user_id)


def test_progress_entry_ownership_protected():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        progress_entry_id = add_progress_entry(
            first_user_id,
            weight_kg=80
        )

        try:
            update_progress_entry(
                second_user_id,
                progress_entry_id,
                weight_kg=70
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Another user updated progress entry")

        try:
            delete_progress_entry(
                second_user_id,
                progress_entry_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Another user deleted progress entry")

        history = get_progress_history(
            first_user_id
        )

        if len(history) != 1:
            raise ValueError("FAIL: Ownership failure modified progress history")

        if history[0]["weight_kg"] != 80:
            raise ValueError("FAIL: Ownership failure changed progress weight")

        print("PASS: Progress entries are protected by user ownership")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


def test_update_body_measurement():
    user_id = create_user()

    try:
        measurement_id = add_body_measurement(
            user_id,
            "Waist",
            86
        )

        updated = update_body_measurement(
            user_id,
            measurement_id,
            body_area="Waist",
            measurement_cm=84,
            notes="Updated measurement"
        )

        if updated["measurement_cm"] != 84:
            raise ValueError("FAIL: Body measurement update saved incorrect value")

        if updated["notes"] != "Updated measurement":
            raise ValueError("FAIL: Body measurement update did not save notes")

        print("PASS: Body measurement updates correctly")

    finally:
        delete_user(user_id)


def test_invalid_body_measurement_update_rejected():
    user_id = create_user()

    try:
        measurement_id = add_body_measurement(
            user_id,
            "Waist",
            84
        )

        invalid_updates = [
            {
                "body_area": "Wing"
            },
            {
                "measurement_cm": 0
            },
            {
                "measurement_cm": -1
            },
            {
                "measurement_cm": True
            }
        ]

        for values in invalid_updates:
            try:
                update_body_measurement(
                    user_id,
                    measurement_id,
                    **values
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid body measurement update was accepted: {values}")

        print("PASS: Invalid body measurement updates rejected")

    finally:
        delete_user(user_id)


def test_delete_body_measurement():
    user_id = create_user()

    try:
        measurement_id = add_body_measurement(
            user_id,
            "Waist",
            84
        )

        delete_body_measurement(
            user_id,
            measurement_id
        )

        history = get_body_measurement_history(
            user_id
        )

        if len(history) != 0:
            raise ValueError("FAIL: Body measurement was not deleted")

        print("PASS: Body measurement deletes correctly")

    finally:
        delete_user(user_id)


def test_update_activity_log():
    user_id = create_user()

    try:
        activity_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=30,
            distance_km=2,
            steps=3000
        )

        updated = update_activity_log(
            user_id,
            activity_id,
            activity_type="Running",
            duration_minutes=25,
            distance_km=4.5,
            steps=4000,
            average_speed_kmh=10.8,
            estimated_calories=300,
            notes="Updated activity"
        )

        if updated["activity_type"] != "Running":
            raise ValueError("FAIL: Activity update did not save type")

        if updated["duration_minutes"] != 25:
            raise ValueError("FAIL: Activity update did not save duration")

        if updated["distance_km"] != 4.5:
            raise ValueError("FAIL: Activity update did not save distance")

        if updated["steps"] != 4000:
            raise ValueError("FAIL: Activity update did not save steps")

        if updated["estimated_calories"] != 300:
            raise ValueError("FAIL: Activity update did not save estimated calories")

        print("PASS: Activity log updates correctly")

    finally:
        delete_user(user_id)


def test_zero_activity_values_allowed():
    user_id = create_user()

    try:
        activity_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=20,
            distance_km=2,
            steps=2000
        )

        updated = update_activity_log(
            user_id,
            activity_id,
            duration_minutes=0,
            distance_km=0,
            steps=0,
            average_speed_kmh=0,
            estimated_calories=0
        )

        if updated["duration_minutes"] != 0:
            raise ValueError("FAIL: Zero activity duration was not saved")

        if updated["distance_km"] != 0:
            raise ValueError("FAIL: Zero activity distance was not saved")

        if updated["steps"] != 0:
            raise ValueError("FAIL: Zero activity steps were not saved")

        print("PASS: Zero activity values are allowed")

    finally:
        delete_user(user_id)


def test_invalid_activity_update_rejected():
    user_id = create_user()

    try:
        activity_id = add_activity_log(
            user_id,
            "Walking"
        )

        invalid_updates = [
            {
                "activity_type": "Flying"
            },
            {
                "duration_minutes": -1
            },
            {
                "distance_km": -1
            },
            {
                "steps": -1
            },
            {
                "steps": 10.5
            },
            {
                "steps": True
            },
            {
                "average_speed_kmh": -1
            },
            {
                "estimated_calories": -1
            }
        ]

        for values in invalid_updates:
            try:
                update_activity_log(
                    user_id,
                    activity_id,
                    **values
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid activity update was accepted: {values}")

        print("PASS: Invalid activity updates rejected")

    finally:
        delete_user(user_id)


def test_delete_activity_log():
    user_id = create_user()

    try:
        activity_id = add_activity_log(
            user_id,
            "Walking",
            steps=5000
        )

        delete_activity_log(
            user_id,
            activity_id
        )

        history = get_activity_history(
            user_id
        )

        if len(history) != 0:
            raise ValueError("FAIL: Activity log was not deleted")

        print("PASS: Activity log deletes correctly")

    finally:
        delete_user(user_id)


def test_activity_log_ownership_protected():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        activity_id = add_activity_log(
            first_user_id,
            "Walking",
            steps=5000
        )

        try:
            update_activity_log(
                second_user_id,
                activity_id,
                steps=100
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Another user updated activity log")

        try:
            delete_activity_log(
                second_user_id,
                activity_id
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Another user deleted activity log")

        history = get_activity_history(
            first_user_id
        )

        if history[0]["steps"] != 5000:
            raise ValueError("FAIL: Ownership failure changed activity data")

        print("PASS: Activity logs are protected by user ownership")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


def test_update_progress_photo_metadata():
    user_id = create_user()

    try:
        photo_id = add_progress_photo(
            user_id,
            "old.jpg",
            "Front",
            is_private=True
        )

        updated = update_progress_photo_metadata(
            user_id,
            photo_id,
            file_path="new.jpg",
            view_type="Side",
            is_private=False,
            notes="Updated photo"
        )

        if updated["file_path"] != "new.jpg":
            raise ValueError("FAIL: Photo update did not save file path")

        if updated["view_type"] != "Side":
            raise ValueError("FAIL: Photo update did not save view")

        if updated["is_private"] != 0:
            raise ValueError("FAIL: Photo update did not save privacy")

        if updated["notes"] != "Updated photo":
            raise ValueError("FAIL: Photo update did not save notes")

        print("PASS: Progress photo metadata updates correctly")

    finally:
        delete_user(user_id)


def test_invalid_progress_photo_update_rejected():
    user_id = create_user()

    try:
        photo_id = add_progress_photo(
            user_id,
            "photo.jpg",
            "Front"
        )

        invalid_updates = [
            {
                "file_path": ""
            },
            {
                "file_path": "   "
            },
            {
                "view_type": "Diagonal"
            },
            {
                "is_private": 1
            },
            {
                "is_private": "yes"
            }
        ]

        for values in invalid_updates:
            try:
                update_progress_photo_metadata(
                    user_id,
                    photo_id,
                    **values
                )

            except ValueError:
                continue

            raise ValueError(f"FAIL: Invalid progress photo update was accepted: {values}")

        print("PASS: Invalid progress photo metadata updates rejected")

    finally:
        delete_user(user_id)


def test_progress_photo_ownership_protected():
    first_user_id = create_user()
    second_user_id = create_user()

    try:
        photo_id = add_progress_photo(
            first_user_id,
            "photo.jpg",
            "Front"
        )

        try:
            update_progress_photo_metadata(
                second_user_id,
                photo_id,
                view_type="Side"
            )

        except ValueError:
            pass

        else:
            raise ValueError("FAIL: Another user updated progress photo metadata")

        photos = get_progress_photo_history(
            first_user_id
        )

        if photos[0]["view_type"] != "Front":
            raise ValueError("FAIL: Ownership failure changed progress photo")

        print("PASS: Progress photos are protected by user ownership")

    finally:
        delete_user(first_user_id)
        delete_user(second_user_id)


def test_empty_update_requests_rejected():
    user_id = create_user()

    try:
        progress_id = add_progress_entry(
            user_id,
            weight_kg=80
        )

        measurement_id = add_body_measurement(
            user_id,
            "Waist",
            84
        )

        activity_id = add_activity_log(
            user_id,
            "Walking"
        )

        photo_id = add_progress_photo(
            user_id,
            "photo.jpg",
            "Front"
        )

        actions = [
            lambda: update_progress_entry(
                user_id,
                progress_id
            ),
            lambda: update_body_measurement(
                user_id,
                measurement_id
            ),
            lambda: update_activity_log(
                user_id,
                activity_id
            ),
            lambda: update_progress_photo_metadata(
                user_id,
                photo_id
            )
        ]

        for action in actions:
            try:
                action()

            except ValueError:
                continue

            raise ValueError("FAIL: Empty update request was accepted")

        print("PASS: Empty progress update requests rejected")

    finally:
        delete_user(user_id)


def test_missing_progress_resources_rejected():
    user_id = create_user()

    try:
        actions = [
            lambda: update_progress_entry(
                user_id,
                999999999,
                weight_kg=80
            ),
            lambda: delete_progress_entry(
                user_id,
                999999999
            ),
            lambda: update_body_measurement(
                user_id,
                999999999,
                measurement_cm=80
            ),
            lambda: delete_body_measurement(
                user_id,
                999999999
            ),
            lambda: update_activity_log(
                user_id,
                999999999,
                steps=1000
            ),
            lambda: delete_activity_log(
                user_id,
                999999999
            ),
            lambda: update_progress_photo_metadata(
                user_id,
                999999999,
                view_type="Front"
            )
        ]

        for action in actions:
            try:
                action()

            except ValueError:
                continue

            raise ValueError("FAIL: Missing progress resource was accepted")

        print("PASS: Missing progress resources rejected")

    finally:
        delete_user(user_id)


def test_timeline_reflects_progress_updates():
    user_id = create_user()

    try:
        progress_id = add_progress_entry(
            user_id,
            weight_kg=82
        )

        activity_id = add_activity_log(
            user_id,
            "Walking",
            steps=3000
        )

        update_progress_entry(
            user_id,
            progress_id,
            weight_kg=80
        )

        update_activity_log(
            user_id,
            activity_id,
            steps=5000
        )

        timeline = build_progress_timeline(
            user_id
        )

        progress_events = [
            event
            for event in timeline
            if event["event_type"] == "progress_entry"
        ]

        activity_events = [
            event
            for event in timeline
            if event["event_type"] == "activity"
        ]

        if progress_events[0]["data"]["weight_kg"] != 80:
            raise ValueError("FAIL: Timeline did not reflect updated progress weight")

        if activity_events[0]["data"]["steps"] != 5000:
            raise ValueError("FAIL: Timeline did not reflect updated activity steps")

        print("PASS: Progress timeline reflects updated records")

    finally:
        delete_user(user_id)


def test_timeline_reflects_deleted_records():
    user_id = create_user()

    try:
        progress_id = add_progress_entry(
            user_id,
            weight_kg=80
        )

        activity_id = add_activity_log(
            user_id,
            "Walking",
            steps=3000
        )

        delete_progress_entry(
            user_id,
            progress_id
        )

        delete_activity_log(
            user_id,
            activity_id
        )

        timeline = build_progress_timeline(
            user_id
        )

        if timeline != []:
            raise ValueError("FAIL: Timeline retained deleted progress records")

        print("PASS: Progress timeline removes deleted records")

    finally:
        delete_user(user_id)


def test_summary_reflects_updated_progress_data():
    user_id = create_user()

    try:
        first_progress_id = add_progress_entry(
            user_id,
            weight_kg=82
        )

        second_progress_id = add_progress_entry(
            user_id,
            weight_kg=81
        )

        activity_id = add_activity_log(
            user_id,
            "Walking",
            duration_minutes=20,
            steps=3000
        )

        update_progress_entry(
            user_id,
            second_progress_id,
            weight_kg=79
        )

        update_activity_log(
            user_id,
            activity_id,
            duration_minutes=30,
            steps=5000
        )

        summary = get_progress_summary(
            user_id
        )

        if summary["latest_weight_kg"] != 79:
            raise ValueError("FAIL: Summary did not reflect updated latest weight")

        if summary["weight_change_kg"] != -3:
            raise ValueError("FAIL: Summary did not reflect updated weight change")

        if summary["total_activity_minutes"] != 30:
            raise ValueError("FAIL: Summary did not reflect updated activity duration")

        if summary["total_steps"] != 5000:
            raise ValueError("FAIL: Summary did not reflect updated steps")

        if first_progress_id is None:
            raise ValueError("FAIL: First progress entry was not created")

        print("PASS: Progress summary reflects updated records")

    finally:
        delete_user(user_id)


if __name__ == "__main__":
    setup_progress_database()

    test_update_progress_entry()
    test_invalid_progress_update_rejected()
    test_delete_progress_entry()
    test_progress_entry_ownership_protected()

    test_update_body_measurement()
    test_invalid_body_measurement_update_rejected()
    test_delete_body_measurement()

    test_update_activity_log()
    test_zero_activity_values_allowed()
    test_invalid_activity_update_rejected()
    test_delete_activity_log()
    test_activity_log_ownership_protected()

    test_update_progress_photo_metadata()
    test_invalid_progress_photo_update_rejected()
    test_progress_photo_ownership_protected()

    test_empty_update_requests_rejected()
    test_missing_progress_resources_rejected()
    test_timeline_reflects_progress_updates()
    test_timeline_reflects_deleted_records()
    test_summary_reflects_updated_progress_data()
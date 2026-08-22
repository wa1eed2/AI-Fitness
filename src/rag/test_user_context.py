from src.database.query_user_database import (
    add_equipment_access,
    add_exercise_preference,
    add_user_limitation,
    create_user,
    create_user_profile,
    delete_user
)

from src.nutrition.nutrition_targets import (
    generate_nutrition_target_for_user
)

from src.database.query_progress_database import (
    add_activity_log,
    add_progress_entry
)

from src.rag.user_context import (
    build_user_context,
    get_user_context_summary
)


def valid_profile():
    return {
        "age": 25,
        "sex": "Male",
        "height_cm": 180,
        "weight_kg": 80,
        "fitness_level": "Intermediate",
        "primary_goal": "Strength",
        "training_days_per_week": 4,
        "session_duration_minutes": 60,
        "preferred_environment": "Gym"
    }


def test_empty_user_context_has_stable_structure():
    user_id = create_user()

    try:
        context = build_user_context(
            user_id
        )

        expected = {
            "user_id",
            "profile",
            "equipment_access",
            "exercise_preferences",
            "limitations",
            "nutrition_target",
            "food_allergies",
            "recent_workouts",
            "recent_progress",
            "recent_body_measurements",
            "recent_activities"
        }

        if set(context.keys()) != expected:
            raise ValueError("FAIL: User context returned unexpected structure")

        print("PASS: User context has stable top-level structure")

    finally:
        delete_user(
            user_id
        )


def test_user_context_contains_profile():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        context = build_user_context(
            user_id
        )

        if context["profile"] is None:
            raise ValueError("FAIL: User context omitted profile")

        if context["profile"]["primary_goal"] != "Strength":
            raise ValueError("FAIL: User context returned incorrect primary goal")

        if context["profile"]["weight_kg"] != 80:
            raise ValueError("FAIL: User context returned incorrect weight")

        print("PASS: User context includes profile data")

    finally:
        delete_user(
            user_id
        )


def test_user_context_contains_equipment():
    user_id = create_user()

    try:
        add_equipment_access(
            user_id,
            "Dumbbell",
            "Available"
        )

        context = build_user_context(
            user_id
        )

        if len(context["equipment_access"]) != 1:
            raise ValueError("FAIL: User equipment was not included in context")

        if context["equipment_access"][0]["equipment"] != "Dumbbell":
            raise ValueError("FAIL: User context returned incorrect equipment")

        print("PASS: User context includes equipment access")

    finally:
        delete_user(
            user_id
        )


def test_user_context_contains_exercise_preferences():
    user_id = create_user()

    try:
        add_exercise_preference(
            user_id,
            "E001",
            "Preferred"
        )

        context = build_user_context(
            user_id
        )

        if len(context["exercise_preferences"]) != 1:
            raise ValueError("FAIL: Exercise preference was not included")

        if context["exercise_preferences"][0]["preference"] != "Preferred":
            raise ValueError("FAIL: User context returned incorrect exercise preference")

        print("PASS: User context includes exercise preferences")

    finally:
        delete_user(
            user_id
        )


def test_user_context_contains_limitations():
    user_id = create_user()

    try:
        add_user_limitation(
            user_id,
            "Knee",
            "Pain",
            "Avoid painful range"
        )

        context = build_user_context(
            user_id
        )

        if len(context["limitations"]) != 1:
            raise ValueError("FAIL: User limitation was not included")

        if context["limitations"][0]["body_area"] != "Knee":
            raise ValueError("FAIL: User context returned incorrect limitation")

        print("PASS: User context includes safety limitations")

    finally:
        delete_user(
            user_id
        )


def test_user_context_contains_generated_nutrition_target():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        generate_nutrition_target_for_user(
            user_id=user_id
        )

        context = build_user_context(
            user_id
        )

        target = context[
            "nutrition_target"
        ]

        if target is None:
            raise ValueError("FAIL: Generated nutrition target was not included")

        required = {
            "calorie_target",
            "protein_g",
            "carbs_g",
            "fat_g"
        }

        if not required.issubset(
            target.keys()
        ):
            raise ValueError("FAIL: Nutrition target context is missing macro fields")

        print("PASS: User context includes automatic nutrition targets")

    finally:
        delete_user(
            user_id
        )


def test_user_context_contains_recent_progress():
    user_id = create_user()

    try:
        add_progress_entry(
            user_id,
            weight_kg=80
        )

        context = build_user_context(
            user_id
        )

        if len(context["recent_progress"]) != 1:
            raise ValueError("FAIL: Recent progress was not included")

        if context["recent_progress"][0]["weight_kg"] != 80:
            raise ValueError("FAIL: User context returned incorrect progress data")

        print("PASS: User context includes recent progress")

    finally:
        delete_user(
            user_id
        )


def test_user_context_contains_recent_activity():
    user_id = create_user()

    try:
        add_activity_log(
            user_id,
            "Walking",
            duration_minutes=30,
            steps=4000
        )

        context = build_user_context(
            user_id
        )

        if len(context["recent_activities"]) != 1:
            raise ValueError("FAIL: Recent activity was not included")

        if context["recent_activities"][0]["activity_type"] != "Walking":
            raise ValueError("FAIL: User context returned incorrect activity type")

        print("PASS: User context includes recent activity")

    finally:
        delete_user(
            user_id
        )


def test_context_summary_does_not_expose_full_personal_data():
    user_id = create_user()

    try:
        create_user_profile(
            user_id,
            valid_profile()
        )

        add_user_limitation(
            user_id,
            "Knee",
            "Pain",
            "Private limitation note"
        )

        context = build_user_context(
            user_id
        )

        summary = get_user_context_summary(
            context
        )

        if "profile" in summary:
            raise ValueError("FAIL: Context summary exposed full profile")

        if "limitations" in summary:
            raise ValueError("FAIL: Context summary exposed limitation details")

        if not summary["has_profile"]:
            raise ValueError("FAIL: Context summary did not report profile availability")

        if summary["limitation_count"] != 1:
            raise ValueError("FAIL: Context summary returned incorrect limitation count")

        print("PASS: User context summary avoids echoing detailed personal data")

    finally:
        delete_user(
            user_id
        )


def test_history_limit_is_respected():
    user_id = create_user()

    try:
        for value in [
            80,
            79,
            78
        ]:
            add_progress_entry(
                user_id,
                weight_kg=value
            )

        context = build_user_context(
            user_id,
            history_limit=2
        )

        if len(context["recent_progress"]) != 2:
            raise ValueError("FAIL: User context ignored history limit")

        print("PASS: User context respects history limit")

    finally:
        delete_user(
            user_id
        )


def test_invalid_user_id_rejected():
    try:
        build_user_context(
            0
        )

    except ValueError:
        print("PASS: User context rejects invalid user ID")
        return

    raise ValueError("FAIL: Invalid user ID was accepted")


def test_invalid_history_limit_rejected():
    try:
        build_user_context(
            1,
            history_limit=0
        )

    except ValueError:
        print("PASS: User context rejects invalid history limit")
        return

    raise ValueError("FAIL: Invalid history limit was accepted")


if __name__ == "__main__":
    test_empty_user_context_has_stable_structure()
    test_user_context_contains_profile()
    test_user_context_contains_equipment()
    test_user_context_contains_exercise_preferences()
    test_user_context_contains_limitations()
    test_user_context_contains_generated_nutrition_target()
    test_user_context_contains_recent_progress()
    test_user_context_contains_recent_activity()
    test_context_summary_does_not_expose_full_personal_data()
    test_history_limit_is_respected()
    test_invalid_user_id_rejected()
    test_invalid_history_limit_rejected()
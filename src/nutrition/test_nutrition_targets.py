from src.database.query_user_database import (
    create_user,
    create_user_profile,
    update_user_profile,
    get_user_nutrition_target,
    delete_user
)

from src.nutrition.nutrition_targets import (
    generate_nutrition_target_for_user
)

def test_generate_nutrition_target_for_user():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Gym"
        }

        create_user_profile(
            user_id,
            profile
        )

        result = generate_nutrition_target_for_user(
            user_id=user_id,
            activity_level="Moderately Active",
            nutrition_goal="Maintenance",
            protein_g_per_kg=1.6,
            fat_percentage=0.25
        )

        saved_target = get_user_nutrition_target(
            user_id
        )

        if saved_target is None:
            raise ValueError(
                "FAIL: Nutrition target was not saved"
            )

        if (
            saved_target["nutrition_target_id"]
            != result["nutrition_target_id"]
        ):
            raise ValueError(
                "FAIL: Saved nutrition target ID does not match"
            )

        print(
            "PASS: Nutrition target generated and saved automatically"
        )

    finally:
        delete_user(user_id)


def test_regenerate_nutrition_target_updates_existing():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Gym"
        }

        create_user_profile(
            user_id,
            profile
        )

        first_result = generate_nutrition_target_for_user(
            user_id=user_id,
            activity_level="Moderately Active",
            nutrition_goal="Maintenance",
            protein_g_per_kg=1.6,
            fat_percentage=0.25
        )

        second_result = generate_nutrition_target_for_user(
            user_id=user_id,
            activity_level="Very Active",
            nutrition_goal="Muscle Gain",
            protein_g_per_kg=2.0,
            fat_percentage=0.25
        )

        saved_target = get_user_nutrition_target(user_id)

        if (
            first_result["nutrition_target_id"]
            != second_result["nutrition_target_id"]
        ):
            raise ValueError("FAIL: Regeneration created a new nutrition target")

        if saved_target["activity_level"] != "Very Active":
            raise ValueError("FAIL: Activity level was not updated")

        if saved_target["nutrition_goal"] != "Muscle Gain":
            raise ValueError("FAIL: Nutrition goal was not updated")

        print("PASS: Existing nutrition target regenerated and updated")

    finally:
        delete_user(user_id)


def test_generate_nutrition_target_without_profile():
    user_id = create_user()

    try:
        try:
            generate_nutrition_target_for_user(
                user_id=user_id,
                activity_level="Moderately Active",
                nutrition_goal="Maintenance",
                protein_g_per_kg=1.6,
                fat_percentage=0.25
            )

        except ValueError:
            print("PASS: Missing user profile rejected")

        else:
            raise ValueError("FAIL: Nutrition target generated without user profile")

    finally:
        delete_user(user_id)


def test_profile_change_recalculates_nutrition_target():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Gym"
        }

        create_user_profile(
            user_id,
            profile
        )

        first_result = generate_nutrition_target_for_user(
            user_id=user_id,
            activity_level="Moderately Active",
            nutrition_goal="Maintenance",
            protein_g_per_kg=1.6,
            fat_percentage=0.25
        )

        first_bmr = first_result["target"]["bmr"]

        update_user_profile(user_id, {"weight_kg": 85})

        second_result = generate_nutrition_target_for_user(
            user_id=user_id,
            activity_level="Moderately Active",
            nutrition_goal="Maintenance",
            protein_g_per_kg=1.6,
            fat_percentage=0.25
        )

        second_bmr = second_result["target"]["bmr"]

        if second_bmr <= first_bmr:
            raise ValueError("FAIL: BMR was not recalculated after weight change")

        if (
            first_result["nutrition_target_id"]
            != second_result["nutrition_target_id"]
        ):
            raise ValueError("FAIL: Weight change created a duplicate nutrition target")

        print("PASS: Profile change recalculated nutrition target")

    finally:
        delete_user(user_id)

def test_default_macro_settings():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Gym"
        }

        create_user_profile(
            user_id,
            profile
        )

        result = generate_nutrition_target_for_user(
            user_id=user_id,
            activity_level="Moderately Active",
            nutrition_goal="Maintenance"
        )

        if result["target"]["protein_g"] <= 0:
            raise ValueError("FAIL: Default protein setting was not applied")

        if result["target"]["fat_g"] <= 0:
            raise ValueError("FAIL: Default fat setting was not applied")

        print("PASS: Default macro settings applied automatically")

    finally:
        delete_user(user_id)

def test_activity_level_generated_from_profile():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Gym"
        }

        create_user_profile(
            user_id,
            profile
        )

        result = generate_nutrition_target_for_user(
            user_id=user_id,
            nutrition_goal="Maintenance"
        )

        if (
            result["target"]["activity_level"]
            != "Moderately Active"
        ):
            raise ValueError("FAIL: Activity level was not generated from profile")

        print("PASS: Activity level generated automatically from profile")

    finally:
        delete_user(user_id)

def test_manual_activity_level_override():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "General Fitness",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Gym"
        }

        create_user_profile(
            user_id,
            profile
        )

        result = generate_nutrition_target_for_user(
            user_id=user_id,
            nutrition_goal="Maintenance",
            activity_level="Very Active"
        )

        if (
            result["target"]["activity_level"]
            != "Very Active"
        ):
            raise ValueError("FAIL: Manual activity level did not override automatic value")

        print("PASS: Manual activity level override applied correctly")

    finally:
        delete_user(user_id)

def test_nutrition_goal_generated_from_profile():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "Fat Loss",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Gym"
        }

        create_user_profile(
            user_id,
            profile
        )

        result = generate_nutrition_target_for_user(
            user_id=user_id
        )

        if (
            result["target"]["nutrition_goal"]
            != "Fat Loss"
        ):
            raise ValueError("FAIL: Nutrition goal was not generated from profile")

        print("PASS: Nutrition goal generated automatically from profile")

    finally:
        delete_user(user_id)

def test_non_nutrition_goal_defaults_to_maintenance():
    user_id = create_user()

    try:
        profile = {
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

        create_user_profile(
            user_id,
            profile
        )

        result = generate_nutrition_target_for_user(
            user_id=user_id
        )

        if (
            result["target"]["nutrition_goal"]
            != "Maintenance"
        ):
            raise ValueError("FAIL: Strength goal did not default to Maintenance")

        print("PASS: Non-nutrition goal defaulted to Maintenance")

    finally:
        delete_user(user_id)

def test_manual_nutrition_goal_override():
    user_id = create_user()

    try:
        profile = {
            "age": 25,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": 80,
            "fitness_level": "Intermediate",
            "primary_goal": "Fat Loss",
            "training_days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_environment": "Gym"
        }

        create_user_profile(
            user_id,
            profile
        )

        result = generate_nutrition_target_for_user(
            user_id=user_id,
            nutrition_goal="Maintenance"
        )

        if (
            result["target"]["nutrition_goal"]
            != "Maintenance"
        ):
            raise ValueError("FAIL: Manual nutrition goal did not override profile goal")

        print("PASS: Manual nutrition goal override applied correctly")

    finally:
        delete_user(user_id)

if __name__ == "__main__":
    test_generate_nutrition_target_for_user()
    test_regenerate_nutrition_target_updates_existing()
    test_generate_nutrition_target_without_profile()
    test_profile_change_recalculates_nutrition_target()
    test_activity_level_generated_from_profile()
    test_manual_activity_level_override()
    test_nutrition_goal_generated_from_profile()
    test_non_nutrition_goal_defaults_to_maintenance()
    test_manual_nutrition_goal_override()
import sqlite3

from unittest.mock import patch

from src.database.setup_exercise_database import db_path
from src.database.setup_user_database import setup_user_database

from src.database.query_user_database import (
    create_user,
    delete_user,
    create_food,
    add_food_allergen,
    add_food_allergy
)

from src.nutrition.meal_recommendations import (
    recommend_foods_for_user,
    build_meal_recommendation,
    calculate_macro_score,
    rank_foods_by_macros
)


setup_user_database()


# ============================================================
# HELPERS
# ============================================================

def cleanup_foods(names):
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.cursor()

    placeholders = ", ".join(
        ["?"] * len(names)
    )

    cursor.execute(
        f"""
        DELETE FROM foods
        WHERE name IN ({placeholders})
        """,
        names
    )

    connection.commit()
    connection.close()


# ============================================================
# ALLERGY SAFETY TEST
# ============================================================

def test_allergenic_food_is_never_recommended():
    safe_food_name = (
        "Recommendation Chicken Test"
    )

    unsafe_food_name = (
        "Recommendation Peanut Protein Test"
    )

    food_names = [
        safe_food_name,
        unsafe_food_name
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        safe_food_id = create_food(
            safe_food_name,
            100,
            165,
            31,
            0,
            3.6
        )

        unsafe_food_id = create_food(
            unsafe_food_name,
            100,
            200,
            30,
            10,
            8
        )

        add_food_allergen(
            unsafe_food_id,
            "Peanuts"
        )

        add_food_allergy(
            user_id,
            "Peanuts"
        )

        recommendations = (
            recommend_foods_for_user(
                user_id,
                min_protein_g=20,
                max_calories=300
            )
        )

        recommendation_ids = [
            food["food_id"]
            for food in recommendations
        ]

        if (
            safe_food_id in recommendation_ids
            and unsafe_food_id
            not in recommendation_ids
        ):
            print(
                "PASS: Allergenic food excluded "
                "from recommendations"
            )

        else:
            raise ValueError(
                "FAIL: Allergy filtering failed "
                "in recommendations"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)


# ============================================================
# RANKING TEST
# ============================================================

def test_recommendations_are_ranked():
    food_names = [
        "Ranking Chicken Test",
        "Ranking Turkey Test",
        "Ranking Yogurt Test"
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        chicken_id = create_food(
            "Ranking Chicken Test",
            100,
            200,
            30,
            0,
            5
        )

        turkey_id = create_food(
            "Ranking Turkey Test",
            100,
            180,
            30,
            0,
            4
        )

        yogurt_id = create_food(
            "Ranking Yogurt Test",
            100,
            150,
            20,
            10,
            3
        )

        recommendations = (
            recommend_foods_for_user(
                user_id,
                min_protein_g=20,
                max_calories=300
            )
        )

        # Other foods may already exist in the database.
        # We only compare the three foods created
        # specifically for this ranking test.
        recommendation_ids = [
            food["food_id"]
            for food in recommendations
            if food["food_id"] in {
                chicken_id,
                turkey_id,
                yogurt_id
            }
        ]

        expected_order = [
            turkey_id,
            chicken_id,
            yogurt_id
        ]

        if recommendation_ids == expected_order:
            print(
                "PASS: Food recommendations "
                "ranked correctly"
            )

        else:
            print(
                "Actual order:",
                recommendation_ids
            )

            print(
                "Expected order:",
                expected_order
            )

            raise ValueError(
                "FAIL: Food recommendations "
                "were ranked incorrectly"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)


# ============================================================
# BASIC MEAL BUILDER TEST
# ============================================================

def test_build_meal_recommendation():
    food_names = [
        "Meal Builder Chicken Test",
        "Meal Builder Yogurt Test",
        "Meal Builder Peanut Test"
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        create_food(
            "Meal Builder Chicken Test",
            100,
            200,
            30,
            0,
            5
        )

        create_food(
            "Meal Builder Yogurt Test",
            100,
            150,
            20,
            10,
            3
        )

        peanut_id = create_food(
            "Meal Builder Peanut Test",
            100,
            180,
            35,
            8,
            6
        )

        add_food_allergen(
            peanut_id,
            "Peanuts"
        )

        add_food_allergy(
            user_id,
            "Peanuts"
        )

        result = build_meal_recommendation(
            user_id=user_id,
            target_calories=500,
            target_protein_g=40
        )

        selected_ids = [
            food["food_id"]
            for food in result["foods"]
        ]

        if (
            len(selected_ids) > 0
            and result["total_calories"] <= 500
            and result["total_protein_g"] >= 40
            and peanut_id not in selected_ids
            and result["protein_target_met"] is True
        ):
            print(
                "PASS: Meal recommendation built "
                "safely and correctly"
            )

        else:
            print(
                "Meal recommendation result:"
            )

            print(result)

            raise ValueError(
                "FAIL: Meal recommendation "
                "did not meet requirements"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)


# ============================================================
# SERVING CALCULATION TEST
# ============================================================

def test_meal_recommendation_servings():
    food_names = [
        "Serving Calculation Chicken Test"
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        create_food(
            "Serving Calculation Chicken Test",
            100,
            165,
            31,
            0,
            3.6
        )

        result = build_meal_recommendation(
            user_id=user_id,
            target_calories=500,
            target_protein_g=40
        )

        selected_foods = result["foods"]

        if (
            len(selected_foods) > 0
            and all(
                food["servings"] > 0
                for food in selected_foods
            )
            and result["total_calories"] <= 500
            and result["total_protein_g"] >= 40
        ):
            print(
                "PASS: Meal serving quantities "
                "calculated correctly"
            )

        else:
            print(
                "Meal recommendation result:"
            )

            print(result)

            raise ValueError(
                "FAIL: Meal serving quantities "
                "were incorrect"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)


# ============================================================
# INVALID CALORIE TARGET TEST
# ============================================================

def test_invalid_target_calories():
    user_id = create_user()

    try:
        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories=0,
                target_protein_g=40
            )

        except ValueError:
            print(
                "PASS: Invalid meal calorie "
                "target rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid meal calorie "
                "target was accepted"
            )

    finally:
        delete_user(user_id)


# ============================================================
# INVALID PROTEIN TARGET TEST
# ============================================================

def test_invalid_target_protein():
    user_id = create_user()

    try:
        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories=500,
                target_protein_g=-10
            )

        except ValueError:
            print(
                "PASS: Invalid meal protein "
                "target rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid meal protein "
                "target was accepted"
            )

    finally:
        delete_user(user_id)


# ============================================================
# INVALID TARGET TYPE TEST
# ============================================================

def test_invalid_target_types():
    user_id = create_user()

    try:
        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories="500",
                target_protein_g=40
            )

        except ValueError:
            print(
                "PASS: Non-numeric calorie "
                "target rejected"
            )

        else:
            raise ValueError(
                "FAIL: Non-numeric calorie "
                "target was accepted"
            )

        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories=500,
                target_protein_g="40"
            )

        except ValueError:
            print(
                "PASS: Non-numeric protein "
                "target rejected"
            )

        else:
            raise ValueError(
                "FAIL: Non-numeric protein "
                "target was accepted"
            )

    finally:
        delete_user(user_id)


# ============================================================
# UNREACHABLE PROTEIN TEST
# ============================================================

def test_unreachable_protein_target():
    food_names = [
        "Unreachable Protein Test"
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        create_food(
            "Unreachable Protein Test",
            100,
            200,
            10,
            20,
            8
        )

        # Extremely small calorie budget and
        # extremely large protein target.
        result = build_meal_recommendation(
            user_id=user_id,
            target_calories=1,
            target_protein_g=100000
        )

        if (
            result["total_calories"] <= 1
            and result["total_protein_g"]
            < 100000
            and result["protein_target_met"] is False
        ):
            print(
                "PASS: Unreachable protein "
                "target handled correctly"
            )

        else:
            print(
                "Meal recommendation result:"
            )

            print(result)

            raise ValueError(
                "FAIL: Unreachable protein "
                "target was handled incorrectly"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)


# ============================================================
# CALORIE TARGET TEST
# ============================================================

def test_calorie_target_met():
    food_names = [
        "Calorie Target Met Test"
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        create_food(
            "Calorie Target Met Test",
            100,
            200,
            20,
            20,
            5
        )

        result = build_meal_recommendation(
            user_id=user_id,
            target_calories=500,
            target_protein_g=45
        )

        minimum_calories = 500 * 0.8

        if (
            result["calorie_target_met"] is True
            and result["total_calories"]
            >= minimum_calories
            and result["total_calories"] <= 500
        ):
            print(
                "PASS: Calorie target status "
                "calculated correctly"
            )

        else:
            print(
                "Meal recommendation result:"
            )

            print(result)

            raise ValueError(
                "FAIL: Calorie target status "
                "was incorrect"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)


# ============================================================
# ALLERGY SAFETY INSIDE BUILDER TEST
# ============================================================

def test_builder_never_uses_allergenic_food():
    food_names = [
        "Builder Safe Protein Test",
        "Builder Unsafe Protein Test"
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        safe_food_id = create_food(
            "Builder Safe Protein Test",
            100,
            220,
            25,
            10,
            8
        )

        unsafe_food_id = create_food(
            "Builder Unsafe Protein Test",
            100,
            150,
            50,
            5,
            2
        )

        add_food_allergen(
            unsafe_food_id,
            "Peanuts"
        )

        add_food_allergy(
            user_id,
            "Peanuts"
        )

        result = build_meal_recommendation(
            user_id=user_id,
            target_calories=500,
            target_protein_g=40
        )

        selected_ids = [
            food["food_id"]
            for food in result["foods"]
        ]

        if (
            unsafe_food_id not in selected_ids
            and len(selected_ids) > 0
        ):
            print(
                "PASS: Meal builder preserved "
                "allergy hard filter"
            )

        else:
            print(
                "Meal recommendation result:"
            )

            print(result)

            raise ValueError(
                "FAIL: Meal builder selected "
                "an allergenic food"
            )

        # This variable is intentionally used only
        # to ensure our safe test food was created.
        if safe_food_id <= 0:
            raise ValueError(
                "FAIL: Safe food was not created"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)

def test_meal_macro_totals():
    food_names = [
        "Macro Totals Test Food"
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        create_food(
            "Macro Totals Test Food",
            100,
            200,
            20,
            10,
            5
        )

        result = build_meal_recommendation(
            user_id=user_id,
            target_calories=500,
            target_protein_g=40
        )

        if (
            "total_carbs_g" in result
            and "total_fat_g" in result
            and result["total_carbs_g"] >= 0
            and result["total_fat_g"] >= 0
        ):
            print(
                "PASS: Meal carbohydrate and fat totals calculated"
            )

        else:
            print("Result:", result)

            raise ValueError(
                "FAIL: Meal carbohydrate or fat totals were incorrect"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)

def test_macro_target_status():
    food_names = [
        "Macro Target Status Test"
    ]

    cleanup_foods(food_names)

    user_id = create_user()

    try:
        create_food(
            "Macro Target Status Test",
            100,
            250,
            25,
            30,
            10
        )

        result = build_meal_recommendation(
            user_id=user_id,
            target_calories=500,
            target_protein_g=40,
            target_carbs_g=40,
            target_fat_g=10
        )

        if (
            "carb_target_met" in result
            and "fat_target_met" in result
        ):
            print(
                "PASS: Carb and fat target status returned"
            )

        else:
            print("Result:", result)

            raise ValueError(
                "FAIL: Carb or fat target status missing"
            )

    finally:
        cleanup_foods(food_names)
        delete_user(user_id)


def test_invalid_macro_targets():
    user_id = create_user()

    try:
        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories=500,
                target_protein_g=40,
                target_carbs_g=-10
            )

        except ValueError:
            print(
                "PASS: Invalid carb target rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid carb target was accepted"
            )

        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories=500,
                target_protein_g=40,
                target_fat_g="10"
            )

        except ValueError:
            print(
                "PASS: Invalid fat target rejected"
            )

        else:
            raise ValueError(
                "FAIL: Invalid fat target was accepted"
            )

    finally:
        delete_user(user_id)


def test_macro_score_changes_with_targets():
    high_protein_food = {
        "protein_g": 30,
        "carbs_g": 5,
        "fat_g": 3
    }

    high_carb_food = {
        "protein_g": 10,
        "carbs_g": 40,
        "fat_g": 5
    }

    # Scenario 1:
    # Protein is the main remaining need.
    protein_food_score = calculate_macro_score(
        high_protein_food,
        remaining_protein=30,
        remaining_carbs=5,
        remaining_fat=3
    )

    carb_food_score = calculate_macro_score(
        high_carb_food,
        remaining_protein=30,
        remaining_carbs=5,
        remaining_fat=3
    )

    if protein_food_score > carb_food_score:
        print(
            "PASS: High-protein food ranked higher "
            "when protein need is greater"
        )
    else:
        raise ValueError(
            "FAIL: Protein-focused macro ranking was incorrect"
        )

    # Scenario 2:
    # Carbohydrates are now the main remaining need.
    protein_food_score = calculate_macro_score(
        high_protein_food,
        remaining_protein=5,
        remaining_carbs=40,
        remaining_fat=5
    )

    carb_food_score = calculate_macro_score(
        high_carb_food,
        remaining_protein=5,
        remaining_carbs=40,
        remaining_fat=5
    )

    if carb_food_score > protein_food_score:
        print(
            "PASS: High-carb food ranked higher "
            "when carbohydrate need is greater"
        )
    else:
        raise ValueError(
            "FAIL: Carb-focused macro ranking was incorrect"
        )

def test_macro_weights_change_ranking():
    protein_food = {
        "protein_g": 30,
        "carbs_g": 5,
        "fat_g": 3
    }

    carb_food = {
        "protein_g": 10,
        "carbs_g": 40,
        "fat_g": 5
    }

    protein_focused_score_1 = calculate_macro_score(
        protein_food,
        remaining_protein=30,
        remaining_carbs=40,
        remaining_fat=10,
        protein_weight=2.0,
        carb_weight=0.5,
        fat_weight=0.5
    )

    protein_focused_score_2 = calculate_macro_score(
        carb_food,
        remaining_protein=30,
        remaining_carbs=40,
        remaining_fat=10,
        protein_weight=2.0,
        carb_weight=0.5,
        fat_weight=0.5
    )

    if protein_focused_score_1 > protein_focused_score_2:
        print(
            "PASS: Protein weight changed ranking correctly"
        )
    else:
        raise ValueError(
            "FAIL: Protein weighting did not affect ranking correctly"
        )

    carb_focused_score_1 = calculate_macro_score(
        protein_food,
        remaining_protein=30,
        remaining_carbs=40,
        remaining_fat=10,
        protein_weight=0.5,
        carb_weight=2.0,
        fat_weight=0.5
    )

    carb_focused_score_2 = calculate_macro_score(
        carb_food,
        remaining_protein=30,
        remaining_carbs=40,
        remaining_fat=10,
        protein_weight=0.5,
        carb_weight=2.0,
        fat_weight=0.5
    )

    if carb_focused_score_2 > carb_focused_score_1:
        print(
            "PASS: Carb weight changed ranking correctly"
        )
    else:
        raise ValueError(
            "FAIL: Carb weighting did not affect ranking correctly"
        )

def test_invalid_macro_weights():
    user_id = create_user()

    try:
        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories=500,
                target_protein_g=40,
                protein_weight=-1
            )

        except ValueError:
            print(
                "PASS: Negative protein weight rejected"
            )

        else:
            raise ValueError(
                "FAIL: Negative protein weight was accepted"
            )

        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories=500,
                target_protein_g=40,
                carb_weight="high"
            )

        except ValueError:
            print(
                "PASS: Non-numeric carb weight rejected"
            )

        else:
            raise ValueError(
                "FAIL: Non-numeric carb weight was accepted"
            )

        try:
            build_meal_recommendation(
                user_id=user_id,
                target_calories=500,
                target_protein_g=40,
                fat_weight=-0.5
            )

        except ValueError:
            print(
                "PASS: Negative fat weight rejected"
            )

        else:
            raise ValueError(
                "FAIL: Negative fat weight was accepted"
            )

    finally:
        delete_user(user_id)

def test_dynamic_macro_reranking():
    protein_food = {
        "food_id": 1,
        "name": "Protein Food",
        "protein_g": 30,
        "carbs_g": 5,
        "fat_g": 2,
        "calories": 170
    }

    carb_food = {
        "food_id": 2,
        "name": "Carb Food",
        "protein_g": 10,
        "carbs_g": 40,
        "fat_g": 5,
        "calories": 250
    }

    foods = [
        protein_food,
        carb_food
    ]

    # First situation:
    # Protein is the stronger remaining need.
    first_ranking = rank_foods_by_macros(
        foods,
        remaining_protein=30,
        remaining_carbs=10,
        remaining_fat=5,
        protein_weight=2.0,
        carb_weight=0.5,
        fat_weight=0.5
    )

    if first_ranking[0]["food_id"] != 1:
        raise ValueError(
            "FAIL: Protein food should rank first initially"
        )

    # Second situation:
    # Protein has been satisfied.
    # Carbs are now the larger remaining need.
    second_ranking = rank_foods_by_macros(
        foods,
        remaining_protein=0,
        remaining_carbs=40,
        remaining_fat=10,
        protein_weight=2.0,
        carb_weight=0.5,
        fat_weight=0.5
    )

    if second_ranking[0]["food_id"] == 2:
        print(
            "PASS: Dynamic macro re-ranking changed food priority"
        )
    else:
        raise ValueError(
            "FAIL: Dynamic macro re-ranking did not change priority"
        )

def test_phase_2_prefers_remaining_macro_need():
    foods = [
        {
            "food_id": 1,
            "name": "Protein Food",
            "protein_g": 30,
            "carbs_g": 5,
            "fat_g": 2,
            "calories": 200
        },
        {
            "food_id": 2,
            "name": "Carb Food",
            "protein_g": 5,
            "carbs_g": 40,
            "fat_g": 2,
            "calories": 180
        },
        {
            "food_id": 3,
            "name": "Fat Food",
            "protein_g": 5,
            "carbs_g": 5,
            "fat_g": 10,
            "calories": 180
        }
    ]

    with patch(
        "src.nutrition.meal_recommendations.recommend_foods_for_user",
        return_value=foods
    ):
        result = build_meal_recommendation(
            user_id=1,
            target_calories=500,
            target_protein_g=30,
            target_carbs_g=50,
            target_fat_g=10,
            protein_weight=3.0,
            carb_weight=1.0,
            fat_weight=1.0
        )

    selected_names = [
        food["name"]
        for food in result["foods"]
    ]

    if selected_names[0] != "Protein Food":
        raise ValueError(
            "FAIL: Protein food should be selected in Phase 1"
        )

    if "Carb Food" in selected_names:
        print(
            "PASS: Phase 2 preferred food matching remaining carb need"
        )
    else:
        raise ValueError(
            "FAIL: Phase 2 did not prefer remaining carb need"
        )


# ============================================================
# RUN TESTS
# ============================================================

def run_tests():
    test_recommendations_are_ranked()
    test_allergenic_food_is_never_recommended()
    test_build_meal_recommendation()
    test_meal_recommendation_servings()
    test_invalid_target_calories()
    test_invalid_target_protein()
    test_invalid_target_types()
    test_unreachable_protein_target()
    test_calorie_target_met()
    test_builder_never_uses_allergenic_food()
    test_meal_macro_totals()
    test_macro_target_status()
    test_invalid_macro_targets()
    test_macro_score_changes_with_targets()
    test_macro_weights_change_ranking()
    test_invalid_macro_weights()
    test_dynamic_macro_reranking()
    test_phase_2_prefers_remaining_macro_need()

    print(
        "\nPASS: All meal recommendation tests completed"
    )


if __name__ == "__main__":
    run_tests()
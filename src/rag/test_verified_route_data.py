from src.rag.question_classifier import (
    ROUTE_COACHING,
    ROUTE_NUTRITION,
    ROUTE_PERSONAL_DATA
)

from src.rag.verified_route_data import (
    build_verified_route_data,
    get_verified_route_data_summary,
    serialize_verified_route_data
)


def fake_nutrition_loader(user_id):
    return {
        "nutrition_target": {
            "calorie_target": 2400,
            "protein_g": 180,
            "carbs_g": 250,
            "fat_g": 75
        },
        "food_allergies": [
            {
                "allergen": "Peanuts"
            }
        ]
    }


def fake_analytics_loader(user_id):
    return {
        "dashboard_analytics": {
            "completed_workouts": 12
        },
        "training_analytics": {
            "training_sessions": 4
        },
        "trend_analytics": {
            "weight_direction": "stable"
        },
        "progression_analytics": {
            "progressing_exercises": 3
        }
    }


def test_nutrition_route_uses_deterministic_loader():
    result = build_verified_route_data(
        1,
        ROUTE_NUTRITION,
        nutrition_loader=fake_nutrition_loader,
        analytics_loader=fake_analytics_loader
    )

    if result["source"] != "deterministic_nutrition_system":
        raise ValueError("FAIL: Nutrition route returned incorrect deterministic source")

    if result["data"]["nutrition_target"]["protein_g"] != 180:
        raise ValueError("FAIL: Nutrition route lost verified macro target")

    print("PASS: Nutrition route uses deterministic nutrition data")


def test_nutrition_route_preserves_allergy_data():
    result = build_verified_route_data(
        1,
        ROUTE_NUTRITION,
        nutrition_loader=fake_nutrition_loader,
        analytics_loader=fake_analytics_loader
    )

    allergies = result["data"]["food_allergies"]

    if allergies[0]["allergen"] != "Peanuts":
        raise ValueError("FAIL: Nutrition route lost deterministic allergy constraint")

    print("PASS: Nutrition route preserves allergy safety data")


def test_personal_route_uses_analytics_loader():
    result = build_verified_route_data(
        1,
        ROUTE_PERSONAL_DATA,
        nutrition_loader=fake_nutrition_loader,
        analytics_loader=fake_analytics_loader
    )

    if result["source"] != "deterministic_analytics_system":
        raise ValueError("FAIL: Personal-data route returned incorrect source")

    if result["data"]["dashboard_analytics"]["completed_workouts"] != 12:
        raise ValueError("FAIL: Personal-data route lost dashboard analytics")

    print("PASS: Personal-data route uses deterministic analytics")


def test_personal_route_contains_all_analytics_sections():
    result = build_verified_route_data(
        1,
        ROUTE_PERSONAL_DATA,
        nutrition_loader=fake_nutrition_loader,
        analytics_loader=fake_analytics_loader
    )

    expected = {
        "dashboard_analytics",
        "training_analytics",
        "trend_analytics",
        "progression_analytics"
    }

    if set(result["data"].keys()) != expected:
        raise ValueError("FAIL: Personal-data route is missing analytics sections")

    print("PASS: Personal-data route combines major analytics systems")


def test_coaching_route_does_not_invent_tool_data():
    result = build_verified_route_data(
        1,
        ROUTE_COACHING,
        nutrition_loader=fake_nutrition_loader,
        analytics_loader=fake_analytics_loader
    )

    if result["data"] != {}:
        raise ValueError("FAIL: General coaching route unexpectedly created deterministic tool data")

    print("PASS: General coaching route does not fabricate route-specific tool output")


def test_verified_summary_does_not_echo_values():
    route_data = build_verified_route_data(
        1,
        ROUTE_NUTRITION,
        nutrition_loader=fake_nutrition_loader,
        analytics_loader=fake_analytics_loader
    )

    summary = get_verified_route_data_summary(
        route_data
    )

    if "nutrition_target" not in summary["available_sections"]:
        raise ValueError("FAIL: Verified-data summary omitted nutrition section")

    if "2400" in str(summary) or "180" in str(summary) or "Peanuts" in str(summary):
        raise ValueError("FAIL: Verified-data summary echoed detailed route data")

    print("PASS: Verified-data summary exposes structure without detailed values")


def test_verified_serialization_contains_exact_values():
    route_data = build_verified_route_data(
        1,
        ROUTE_NUTRITION,
        nutrition_loader=fake_nutrition_loader,
        analytics_loader=fake_analytics_loader
    )

    serialized = serialize_verified_route_data(
        route_data
    )

    if '"protein_g": 180' not in serialized:
        raise ValueError("FAIL: Verified data serializer omitted exact macro value")

    if "Peanuts" not in serialized:
        raise ValueError("FAIL: Verified data serializer omitted allergy value")

    print("PASS: Verified application data serializes exact deterministic values")


def test_verified_serialization_is_bounded():
    route_data = {
        "route": ROUTE_PERSONAL_DATA,
        "source": "test",
        "data": {
            "large": "A" * 5000
        }
    }

    serialized = serialize_verified_route_data(
        route_data,
        max_chars=500
    )

    if len(serialized) > 500:
        raise ValueError("FAIL: Verified route data exceeded character budget")

    if "TRUNCATED" not in serialized:
        raise ValueError("FAIL: Verified route data did not mark truncation")

    print("PASS: Verified route data respects prompt character budget")


def test_invalid_route_rejected():
    try:
        build_verified_route_data(
            1,
            "unsupported",
            nutrition_loader=fake_nutrition_loader,
            analytics_loader=fake_analytics_loader
        )

    except ValueError:
        print("PASS: Verified route data rejects unsupported route")
        return

    raise ValueError("FAIL: Unsupported verified-data route was accepted")


def test_invalid_user_id_rejected():
    try:
        build_verified_route_data(
            True,
            ROUTE_NUTRITION,
            nutrition_loader=fake_nutrition_loader,
            analytics_loader=fake_analytics_loader
        )

    except ValueError:
        print("PASS: Verified route data rejects invalid user ID")
        return

    raise ValueError("FAIL: Invalid verified-data user ID was accepted")


if __name__ == "__main__":
    test_nutrition_route_uses_deterministic_loader()
    test_nutrition_route_preserves_allergy_data()
    test_personal_route_uses_analytics_loader()
    test_personal_route_contains_all_analytics_sections()
    test_coaching_route_does_not_invent_tool_data()
    test_verified_summary_does_not_echo_values()
    test_verified_serialization_contains_exact_values()
    test_verified_serialization_is_bounded()
    test_invalid_route_rejected()
    test_invalid_user_id_rejected()
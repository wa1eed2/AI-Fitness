from src.rag.question_classifier import (
    ROUTE_COACHING,
    ROUTE_NUTRITION,
    ROUTE_PERSONAL_DATA,
    ROUTE_RESEARCH,
    ROUTE_SAFETY,
    ROUTE_UNKNOWN,
    SAFETY_LEVEL_CAUTION,
    SAFETY_LEVEL_URGENT,
    classify_question
)


def assert_route(question, expected_route):
    result = classify_question(
        question
    )

    if result["route"] != expected_route:
        raise ValueError(f"FAIL: '{question}' routed to {result['route']} instead of {expected_route}")

    return result


def test_research_question():
    assert_route(
        "What does research say about hypertrophy volume?",
        ROUTE_RESEARCH
    )

    print("PASS: Explicit research question routes to RAG")


def test_systematic_review_question():
    assert_route(
        "Summarize this systematic review about resistance training",
        ROUTE_RESEARCH
    )

    print("PASS: Review terminology routes to research")


def test_umbrella_review_title_routes_to_research():
    assert_route(
        "Resistance Training Variables for Optimization of Muscle Hypertrophy: An Umbrella Review",
        ROUTE_RESEARCH
    )

    print("PASS: Existing paper-title queries route to research")


def test_research_nutrition_question_prefers_research():
    assert_route(
        "What does the evidence say about protein intake?",
        ROUTE_RESEARCH
    )

    print("PASS: Research intent takes precedence over nutrition routing")


def test_nutrition_question():
    assert_route(
        "What is my daily protein target?",
        ROUTE_NUTRITION
    )

    print("PASS: Nutrition target question routes to nutrition")


def test_meal_question():
    assert_route(
        "Can you build me a meal around my macros?",
        ROUTE_NUTRITION
    )

    print("PASS: Meal question routes to nutrition")


def test_personal_workout_question():
    assert_route(
        "How was my workout yesterday?",
        ROUTE_PERSONAL_DATA
    )

    print("PASS: Personal workout question routes to personal data")


def test_progress_question():
    assert_route(
        "Can you summarize my progress?",
        ROUTE_PERSONAL_DATA
    )

    print("PASS: Progress question routes to personal data")


def test_coaching_question():
    assert_route(
        "Motivate me before my workout",
        ROUTE_COACHING
    )

    print("PASS: Motivation question routes to coaching")


def test_general_message_defaults_to_coaching():
    assert_route(
        "Help me stay consistent this week",
        ROUTE_COACHING
    )

    print("PASS: General coaching conversation defaults safely")


def test_pain_routes_to_safety():
    result = assert_route(
        "My knee hurts when I squat",
        ROUTE_SAFETY
    )

    if result["safety_level"] != SAFETY_LEVEL_CAUTION:
        raise ValueError("FAIL: Ordinary pain signal did not receive caution level")

    print("PASS: Pain signal routes to safety caution")


def test_chest_pain_routes_to_urgent_safety():
    result = assert_route(
        "I have sharp chest pain while exercising",
        ROUTE_SAFETY
    )

    if result["safety_level"] != SAFETY_LEVEL_URGENT:
        raise ValueError("FAIL: Chest-pain signal did not receive urgent level")

    print("PASS: Chest pain routes to urgent safety response")


def test_safety_takes_precedence_over_research():
    result = assert_route(
        "What does research say about chest pain during exercise?",
        ROUTE_SAFETY
    )

    if result["safety_level"] != SAFETY_LEVEL_URGENT:
        raise ValueError("FAIL: Safety precedence lost urgent classification")

    print("PASS: Safety classification takes precedence over research intent")


def test_gibberish_routes_to_unknown():
    assert_route(
        "zzzxqvplmnkjhgfd",
        ROUTE_UNKNOWN
    )

    print("PASS: Probable gibberish routes to unknown")


def test_empty_question_rejected():
    try:
        classify_question(
            "   "
        )

    except ValueError:
        print("PASS: Question classifier rejects empty input")
        return

    raise ValueError("FAIL: Empty classifier input was accepted")


if __name__ == "__main__":
    test_research_question()
    test_systematic_review_question()
    test_umbrella_review_title_routes_to_research()
    test_research_nutrition_question_prefers_research()
    test_nutrition_question()
    test_meal_question()
    test_personal_workout_question()
    test_progress_question()
    test_coaching_question()
    test_general_message_defaults_to_coaching()
    test_pain_routes_to_safety()
    test_chest_pain_routes_to_urgent_safety()
    test_safety_takes_precedence_over_research()
    test_gibberish_routes_to_unknown()
    test_empty_question_rejected()
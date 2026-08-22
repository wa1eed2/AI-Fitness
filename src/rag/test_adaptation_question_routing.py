from src.rag.question_classifier import (
    ROUTE_ADAPTATION,
    ROUTE_NUTRITION,
    ROUTE_PERSONAL_DATA,
    ROUTE_RESEARCH,
    ROUTE_SAFETY,
    ROUTE_WORKOUT,
    classify_question
)


def test_progression_question_routes_to_adaptation():
    result = classify_question(
        "Should I increase my training?"
    )

    if result["route"] != ROUTE_ADAPTATION:
        raise ValueError(f"FAIL: Progression question routed to {result['route']}")

    print("PASS: Training progression question routes to deterministic adaptation")


def test_reduction_question_routes_to_adaptation():
    result = classify_question(
        "Should I reduce my training volume?"
    )

    if result["route"] != ROUTE_ADAPTATION:
        raise ValueError(f"FAIL: Reduction question routed to {result['route']}")

    print("PASS: Training-volume reduction question routes to deterministic adaptation")


def test_recovery_question_routes_to_adaptation():
    result = classify_question(
        "How is my recovery looking?"
    )

    if result["route"] != ROUTE_ADAPTATION:
        raise ValueError(f"FAIL: Recovery question routed to {result['route']}")

    print("PASS: Personal recovery question routes to adaptation analytics")


def test_safety_precedes_adaptation():
    result = classify_question(
        "My knee hurts; should I increase my training?"
    )

    if result["route"] != ROUTE_SAFETY:
        raise ValueError("FAIL: Adaptation routing overrode deterministic safety")

    print("PASS: Safety signals take precedence over adaptation requests")


def test_research_precedes_adaptation():
    result = classify_question(
        "What does research say about whether I should increase my training volume?"
    )

    if result["route"] != ROUTE_RESEARCH:
        raise ValueError("FAIL: Adaptation routing overrode explicit research request")

    print("PASS: Explicit research intent remains evidence-grounded RAG")


def test_workout_generation_remains_separate():
    result = classify_question(
        "Build me a workout"
    )

    if result["route"] != ROUTE_WORKOUT:
        raise ValueError("FAIL: Workout generation was swallowed by adaptation route")

    print("PASS: Workout generation remains separate from adaptation")


def test_training_history_remains_personal_data():
    result = classify_question(
        "How has my training been?"
    )

    if result["route"] != ROUTE_PERSONAL_DATA:
        raise ValueError(f"FAIL: Training-history question routed to {result['route']}")

    print("PASS: Training-history review remains personal-data routing")


def test_nutrition_progression_language_does_not_route_adaptation():
    result = classify_question(
        "Should I increase my protein?"
    )

    if result["route"] != ROUTE_NUTRITION:
        raise ValueError(f"FAIL: Protein question routed to {result['route']}")

    print("PASS: Nutrition changes are not confused with training adaptation")


if __name__ == "__main__":
    test_progression_question_routes_to_adaptation()
    test_reduction_question_routes_to_adaptation()
    test_recovery_question_routes_to_adaptation()
    test_safety_precedes_adaptation()
    test_research_precedes_adaptation()
    test_workout_generation_remains_separate()
    test_training_history_remains_personal_data()
    test_nutrition_progression_language_does_not_route_adaptation()
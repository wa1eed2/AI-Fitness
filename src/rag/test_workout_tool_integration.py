from src.database.query_ai_conversation_database import (
    create_ai_conversation,
    get_ai_conversation_messages
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.rag.conversation_service import (
    ConversationNotFoundError
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)

from src.rag.question_classifier import (
    ROUTE_WORKOUT,
    classify_question
)

from src.rag.workout_action_classifier import (
    ACTION_SINGLE_WORKOUT,
    ACTION_WEEKLY_WORKOUT,
    classify_workout_action
)

from src.rag.workout_tool_service import (
    WorkoutSafetyValidationError,
    build_verified_workout_package,
    generate_workout_conversation_answer
)


def fake_profile_getter(user_id):
    return {
        "user_id": user_id,
        "fitness_level": "Beginner",
        "primary_goal": "General Fitness",
        "session_duration_minutes": 45,
        "training_days_per_week": 3,
        "preferred_environment": "Home"
    }


def fake_candidate_getter(user_id):
    return [
        {
            "exercise_id": "E001",
            "name": "Push-Up"
        },
        {
            "exercise_id": "E005",
            "name": "Bodyweight Reverse Lunge"
        },
        {
            "exercise_id": "E010",
            "name": "Plank"
        }
    ]


def fake_single_builder(user_id, exercise_count=None):
    return {
        "status": "ready",
        "estimated_duration_minutes": 35,
        "warm_up_minutes": 5,
        "cool_down_minutes": 5,
        "exercises": [
            {
                "exercise_id": "E001",
                "name": "Push-Up",
                "order": 1,
                "sets": 3,
                "reps": "8-12",
                "rest_seconds": 60
            },
            {
                "exercise_id": "E005",
                "name": "Bodyweight Reverse Lunge",
                "order": 2,
                "sets": 3,
                "reps": "8-12",
                "rest_seconds": 60
            }
        ]
    }


def fake_weekly_builder(user_id, exercise_count=None):
    return {
        "status": "ready",
        "training_days_per_week": 2,
        "days": [
            {
                "day": 1,
                "exercises": [
                    {
                        "exercise_id": "E001",
                        "name": "Push-Up",
                        "order": 1,
                        "sets": 3,
                        "reps": "8-12"
                    }
                ]
            },
            {
                "day": 2,
                "exercises": [
                    {
                        "exercise_id": "E005",
                        "name": "Bodyweight Reverse Lunge",
                        "order": 1,
                        "sets": 3,
                        "reps": "8-12"
                    }
                ]
            }
        ]
    }


def test_workout_question_routes_to_workout():
    result = classify_question("Build me a workout")

    if result["route"] != ROUTE_WORKOUT:
        raise ValueError("FAIL: Workout-generation request did not use workout route")

    print("PASS: Explicit workout-generation request routes to deterministic workout system")


def test_weekly_workout_is_detected():
    result = classify_workout_action("Build me a weekly workout plan")

    if result["action"] != ACTION_WEEKLY_WORKOUT:
        raise ValueError("FAIL: Weekly workout request was not detected")

    print("PASS: Workout action classifier detects weekly plan request")


def test_single_workout_is_default_action():
    result = classify_workout_action("Build me a workout")

    if result["action"] != ACTION_SINGLE_WORKOUT:
        raise ValueError("FAIL: Single workout request returned incorrect action")

    print("PASS: Workout action classifier defaults to single workout")


def test_missing_profile_blocks_builder():
    builder_calls = []

    def missing_profile(user_id):
        return None

    def tracked_builder(user_id, exercise_count=None):
        builder_calls.append(True)
        return fake_single_builder(user_id, exercise_count)

    package = build_verified_workout_package(
        user_id=1,
        workout_action=ACTION_SINGLE_WORKOUT,
        profile_getter=missing_profile,
        candidate_getter=fake_candidate_getter,
        single_workout_builder=tracked_builder,
        weekly_workout_builder=fake_weekly_builder
    )

    if package["status"] != "profile_required":
        raise ValueError("FAIL: Missing profile returned incorrect workout status")

    if builder_calls:
        raise ValueError("FAIL: Workout builder ran without required profile")

    print("PASS: Missing profile blocks deterministic workout generation")


def test_no_candidates_blocks_builder():
    builder_calls = []

    def no_candidates(user_id):
        return []

    def tracked_builder(user_id, exercise_count=None):
        builder_calls.append(True)
        return fake_single_builder(user_id, exercise_count)

    package = build_verified_workout_package(
        user_id=1,
        workout_action=ACTION_SINGLE_WORKOUT,
        profile_getter=fake_profile_getter,
        candidate_getter=no_candidates,
        single_workout_builder=tracked_builder,
        weekly_workout_builder=fake_weekly_builder
    )

    if package["status"] != "workout_unavailable":
        raise ValueError("FAIL: Empty candidate set returned incorrect status")

    if builder_calls:
        raise ValueError("FAIL: Workout builder ran despite empty candidate set")

    print("PASS: Empty safe candidate set blocks workout generation")


def test_safe_workout_is_accepted():
    package = build_verified_workout_package(
        user_id=1,
        workout_action=ACTION_SINGLE_WORKOUT,
        profile_getter=fake_profile_getter,
        candidate_getter=fake_candidate_getter,
        single_workout_builder=fake_single_builder,
        weekly_workout_builder=fake_weekly_builder
    )

    if package["status"] != "workout_ready":
        raise ValueError("FAIL: Safe deterministic workout was not accepted")

    if package["selected_exercise_count"] != 2:
        raise ValueError("FAIL: Selected exercise count was incorrect")

    print("PASS: Safe deterministic workout passes candidate validation")


def test_unsafe_exercise_is_rejected():
    def unsafe_builder(user_id, exercise_count=None):
        return {
            "exercises": [
                {
                    "exercise_id": "E999",
                    "name": "Unsafe Exercise",
                    "sets": 3,
                    "reps": 10
                }
            ]
        }

    try:
        build_verified_workout_package(
            user_id=1,
            workout_action=ACTION_SINGLE_WORKOUT,
            profile_getter=fake_profile_getter,
            candidate_getter=fake_candidate_getter,
            single_workout_builder=unsafe_builder,
            weekly_workout_builder=fake_weekly_builder
        )

    except WorkoutSafetyValidationError:
        print("PASS: Workout safety validation rejects exercise outside candidate set")
        return

    raise ValueError("FAIL: Workout outside safe candidate set was accepted")


def test_weekly_builder_is_used():
    package = build_verified_workout_package(
        user_id=1,
        workout_action=ACTION_WEEKLY_WORKOUT,
        profile_getter=fake_profile_getter,
        candidate_getter=fake_candidate_getter,
        single_workout_builder=fake_single_builder,
        weekly_workout_builder=fake_weekly_builder
    )

    if package["workout_plan"]["training_days_per_week"] != 2:
        raise ValueError("FAIL: Weekly workout builder was not used")

    print("PASS: Weekly workout action uses deterministic weekly planner")


def test_model_does_not_receive_exercise_names():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(user_id)

        provider = FakeLLMProvider(
            "The workout uses two prescribed movements with structured sets and rest periods."
        )

        result = generate_workout_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a workout",
            workout_action=ACTION_SINGLE_WORKOUT,
            provider=provider,
            profile_getter=fake_profile_getter,
            candidate_getter=fake_candidate_getter,
            single_workout_builder=fake_single_builder,
            weekly_workout_builder=fake_weekly_builder
        )

        prompt = provider.calls[0]["user_prompt"]

        if "Push-Up" in prompt or "Bodyweight Reverse Lunge" in prompt:
            raise ValueError("FAIL: Exercise names were exposed to workout explanation model")

        if '"sets": 3' not in prompt:
            raise ValueError("FAIL: Workout explanation model did not receive deterministic prescription")

        if result["workout_plan"]["exercises"][0]["name"] != "Push-Up":
            raise ValueError("FAIL: Full deterministic workout was not returned to application")

        print("PASS: Groq receives workout structure without exercise-selection authority")

    finally:
        delete_user(user_id)


def test_missing_profile_does_not_call_provider():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(user_id)

        provider = FakeLLMProvider(
            "This must not be used."
        )

        result = generate_workout_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a workout",
            workout_action=ACTION_SINGLE_WORKOUT,
            provider=provider,
            profile_getter=lambda user_id: None,
            candidate_getter=fake_candidate_getter,
            single_workout_builder=fake_single_builder,
            weekly_workout_builder=fake_weekly_builder
        )

        if result["status"] != "profile_required":
            raise ValueError("FAIL: Missing profile returned incorrect response status")

        if provider.calls:
            raise ValueError("FAIL: Provider was called despite missing workout profile")

        print("PASS: Missing profile returns deterministic response without model call")

    finally:
        delete_user(user_id)


def test_successful_workout_is_persisted():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(user_id)

        provider = FakeLLMProvider(
            "Your generated workout contains a structured two-exercise session."
        )

        result = generate_workout_conversation_answer(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Build me a workout",
            workout_action=ACTION_SINGLE_WORKOUT,
            provider=provider,
            profile_getter=fake_profile_getter,
            candidate_getter=fake_candidate_getter,
            single_workout_builder=fake_single_builder,
            weekly_workout_builder=fake_weekly_builder
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation["conversation_id"],
            limit=20
        )

        if result["status"] != "workout_generated":
            raise ValueError("FAIL: Successful workout returned incorrect status")

        if len(messages) != 2:
            raise ValueError("FAIL: Workout conversation exchange was not persisted")

        if messages[-1]["retrieval_status"] != "workout:workout_generated":
            raise ValueError("FAIL: Stored workout explanation lost route metadata")

        print("PASS: Successful deterministic workout exchange is persisted")

    finally:
        delete_user(user_id)


def test_workout_model_cannot_invent_research_citation():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(user_id)

        provider = FakeLLMProvider(
            "This workout is scientifically perfect [P999]."
        )

        try:
            generate_workout_conversation_answer(
                user_id=user_id,
                conversation_id=conversation["conversation_id"],
                question="Build me a workout",
                workout_action=ACTION_SINGLE_WORKOUT,
                provider=provider,
                profile_getter=fake_profile_getter,
                candidate_getter=fake_candidate_getter,
                single_workout_builder=fake_single_builder,
                weekly_workout_builder=fake_weekly_builder
            )

        except ValueError as error:
            if "invented research citations" not in str(error):
                raise ValueError(f"FAIL: Wrong fabricated-citation error: {error}")

            print("PASS: Workout explanation cannot fabricate research citations")
            return

        raise ValueError("FAIL: Workout explanation accepted fabricated citation")

    finally:
        delete_user(user_id)


def test_cross_user_workout_is_blocked_before_tools():
    owner_id = create_user()
    other_id = create_user()

    profile_calls = []

    try:
        conversation = create_ai_conversation(owner_id)

        def tracked_profile_getter(user_id):
            profile_calls.append(user_id)
            return fake_profile_getter(user_id)

        try:
            generate_workout_conversation_answer(
                user_id=other_id,
                conversation_id=conversation["conversation_id"],
                question="Build me a workout",
                workout_action=ACTION_SINGLE_WORKOUT,
                provider=FakeLLMProvider("Unused"),
                profile_getter=tracked_profile_getter,
                candidate_getter=fake_candidate_getter,
                single_workout_builder=fake_single_builder,
                weekly_workout_builder=fake_weekly_builder
            )

        except ConversationNotFoundError:
            if profile_calls:
                raise ValueError("FAIL: Workout tools ran before conversation ownership validation")

            print("PASS: Workout generation validates conversation ownership before tools")
            return

        raise ValueError("FAIL: Cross-user workout generation was allowed")

    finally:
        delete_user(owner_id)
        delete_user(other_id)


if __name__ == "__main__":
    test_workout_question_routes_to_workout()
    test_weekly_workout_is_detected()
    test_single_workout_is_default_action()
    test_missing_profile_blocks_builder()
    test_no_candidates_blocks_builder()
    test_safe_workout_is_accepted()
    test_unsafe_exercise_is_rejected()
    test_weekly_builder_is_used()
    test_model_does_not_receive_exercise_names()
    test_missing_profile_does_not_call_provider()
    test_successful_workout_is_persisted()
    test_workout_model_cannot_invent_research_citation()
    test_cross_user_workout_is_blocked_before_tools()
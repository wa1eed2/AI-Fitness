import sqlite3

from src.database.query_ai_conversation_database import (
    DB_PATH,
    add_ai_conversation_exchange,
    create_ai_conversation,
    delete_ai_conversation,
    get_ai_conversation,
    get_ai_conversation_messages,
    get_user_ai_conversations,
    update_ai_conversation_title
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.setup_ai_conversation_database import (
    setup_ai_conversation_database
)


def test_tables_exist():
    connection = sqlite3.connect(
        DB_PATH
    )

    try:
        names = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        if "ai_conversations" not in names or "ai_messages" not in names:
            raise ValueError("FAIL: AI conversation tables were not created")

        print("PASS: AI conversation database tables exist")

    finally:
        connection.close()


def test_create_conversation():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id,
            "Training questions"
        )

        if conversation["user_id"] != user_id:
            raise ValueError("FAIL: Conversation belongs to wrong user")

        if conversation["title"] != "Training questions":
            raise ValueError("FAIL: Conversation title was incorrect")

        print("PASS: AI conversation can be created")

    finally:
        delete_user(
            user_id
        )


def test_default_conversation_title():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        if conversation["title"] != "New conversation":
            raise ValueError("FAIL: Default conversation title was incorrect")

        print("PASS: AI conversation has stable default title")

    finally:
        delete_user(
            user_id
        )


def test_user_conversations_are_isolated():
    user_1 = create_user()
    user_2 = create_user()

    try:
        conversation = create_ai_conversation(
            user_1,
            "Private conversation"
        )

        user_2_result = get_ai_conversation(
            user_2,
            conversation[
                "conversation_id"
            ]
        )

        if user_2_result is not None:
            raise ValueError("FAIL: Cross-user conversation lookup succeeded")

        print("PASS: AI conversations enforce user ownership")

    finally:
        delete_user(
            user_1
        )

        delete_user(
            user_2
        )


def test_list_user_conversations():
    user_id = create_user()

    try:
        create_ai_conversation(
            user_id,
            "Conversation One"
        )

        create_ai_conversation(
            user_id,
            "Conversation Two"
        )

        conversations = get_user_ai_conversations(
            user_id
        )

        if len(conversations) != 2:
            raise ValueError("FAIL: User conversation list returned incorrect count")

        print("PASS: User AI conversations can be listed")

    finally:
        delete_user(
            user_id
        )


def test_update_conversation_title():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        updated = update_ai_conversation_title(
            user_id,
            conversation[
                "conversation_id"
            ],
            "Hypertrophy discussion"
        )

        if updated["title"] != "Hypertrophy discussion":
            raise ValueError("FAIL: Conversation title was not updated")

        print("PASS: AI conversation title can be updated")

    finally:
        delete_user(
            user_id
        )


def test_exchange_is_stored_in_order():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        exchange = add_ai_conversation_exchange(
            user_id=user_id,
            conversation_id=conversation[
                "conversation_id"
            ],
            user_content="What is hypertrophy?",
            assistant_content="Muscle growth [P001].",
            citations=[
                {
                    "paper_id": "P001",
                    "citation_id": "[P001]"
                }
            ],
            retrieval_status="high_relevance",
            citation_repair_used=True
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation[
                "conversation_id"
            ],
            limit=20
        )

        if len(messages) != 2:
            raise ValueError("FAIL: Conversation exchange did not create two messages")

        if messages[0]["role"] != "user" or messages[1]["role"] != "assistant":
            raise ValueError("FAIL: Conversation messages were stored out of order")

        if exchange["assistant_message"]["citations"][0]["paper_id"] != "P001":
            raise ValueError("FAIL: Assistant citation metadata was not stored")

        if not exchange["assistant_message"]["citation_repair_used"]:
            raise ValueError("FAIL: Citation-repair metadata was not stored")

        print("PASS: AI conversation exchange stores messages and citation metadata")

    finally:
        delete_user(
            user_id
        )


def test_message_limit_returns_latest_messages():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        for number in range(
            1,
            4
        ):
            add_ai_conversation_exchange(
                user_id=user_id,
                conversation_id=conversation[
                    "conversation_id"
                ],
                user_content=f"Question {number}",
                assistant_content=f"Answer {number}",
                citations=[],
                retrieval_status="test",
                citation_repair_used=False
            )

        messages = get_ai_conversation_messages(
            user_id,
            conversation[
                "conversation_id"
            ],
            limit=2
        )

        if len(messages) != 2:
            raise ValueError("FAIL: Conversation message limit was ignored")

        if messages[0]["content"] != "Question 3":
            raise ValueError("FAIL: Conversation history did not return latest exchange")

        if messages[1]["content"] != "Answer 3":
            raise ValueError("FAIL: Latest assistant message was incorrect")

        print("PASS: Conversation history limit preserves newest messages")

    finally:
        delete_user(
            user_id
        )


def test_message_count_updates():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        add_ai_conversation_exchange(
            user_id=user_id,
            conversation_id=conversation[
                "conversation_id"
            ],
            user_content="Question",
            assistant_content="Answer",
            citations=[],
            retrieval_status="test"
        )

        refreshed = get_ai_conversation(
            user_id,
            conversation[
                "conversation_id"
            ]
        )

        if refreshed["message_count"] != 2:
            raise ValueError("FAIL: Conversation message count was incorrect")

        print("PASS: Conversation metadata tracks message count")

    finally:
        delete_user(
            user_id
        )


def test_delete_conversation():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        conversation_id = conversation[
            "conversation_id"
        ]

        deleted = delete_ai_conversation(
            user_id,
            conversation_id
        )

        if not deleted:
            raise ValueError("FAIL: Existing conversation was not deleted")

        if get_ai_conversation(
            user_id,
            conversation_id
        ) is not None:
            raise ValueError("FAIL: Deleted conversation still exists")

        print("PASS: AI conversation can be deleted")

    finally:
        delete_user(
            user_id
        )


def test_invalid_title_rejected():
    user_id = create_user()

    try:
        try:
            create_ai_conversation(
                user_id,
                "   "
            )

        except ValueError:
            print("PASS: Empty AI conversation title is rejected")
            return

        raise ValueError("FAIL: Empty conversation title was accepted")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    setup_ai_conversation_database()

    test_tables_exist()
    test_create_conversation()
    test_default_conversation_title()
    test_user_conversations_are_isolated()
    test_list_user_conversations()
    test_update_conversation_title()
    test_exchange_is_stored_in_order()
    test_message_limit_returns_latest_messages()
    test_message_count_updates()
    test_delete_conversation()
    test_invalid_title_rejected()
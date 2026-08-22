import json
import sqlite3
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "database"
    / "ai_fitness.db"
)

DEFAULT_CONVERSATION_TITLE = "New conversation"
MAX_TITLE_LENGTH = 120
MAX_LIST_LIMIT = 100
MAX_MESSAGE_LIMIT = 20


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def validate_positive_integer(value, field_name):
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def validate_title(title):
    if not isinstance(title, str):
        raise ValueError("Conversation title must be a string")

    normalized = title.strip()

    if not normalized:
        raise ValueError("Conversation title cannot be empty")

    if len(normalized) > MAX_TITLE_LENGTH:
        raise ValueError(f"Conversation title cannot exceed {MAX_TITLE_LENGTH} characters")

    return normalized


def validate_limit(limit, maximum, field_name="limit"):
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError(f"{field_name} must be an integer")

    if limit < 1 or limit > maximum:
        raise ValueError(f"{field_name} must be between 1 and {maximum}")


def serialize_citations(citations):
    if citations is None:
        return None

    if not isinstance(citations, list):
        raise ValueError("Citations must be a list")

    for citation in citations:
        if not isinstance(citation, dict):
            raise ValueError("Each citation must be a dictionary")

    return json.dumps(
        citations,
        ensure_ascii=False,
        separators=(",", ":")
    )


def deserialize_citations(value):
    if value is None:
        return []

    parsed = json.loads(value)

    if not isinstance(parsed, list):
        raise ValueError("Stored conversation citations are invalid")

    return parsed


def row_to_conversation(row):
    if row is None:
        return None

    return dict(row)


def row_to_message(row):
    if row is None:
        return None

    message = dict(row)

    message["citations"] = deserialize_citations(
        message.pop(
            "citations_json"
        )
    )

    message["citation_repair_used"] = bool(
        message[
            "citation_repair_used"
        ]
    )

    return message


def user_exists(connection, user_id):
    row = connection.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    return row is not None


def conversation_owned(connection, user_id, conversation_id):
    row = connection.execute(
        """
        SELECT conversation_id
        FROM ai_conversations
        WHERE conversation_id = ?
          AND user_id = ?
        """,
        (
            conversation_id,
            user_id
        )
    ).fetchone()

    return row is not None


def create_ai_conversation(user_id, title=None):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    if title is None:
        normalized_title = DEFAULT_CONVERSATION_TITLE
    else:
        normalized_title = validate_title(
            title
        )

    connection = get_connection()

    try:
        if not user_exists(
            connection,
            user_id
        ):
            raise ValueError("User does not exist")

        cursor = connection.execute(
            """
            INSERT INTO ai_conversations (
                user_id,
                title
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                normalized_title
            )
        )

        conversation_id = cursor.lastrowid

        connection.commit()

        return get_ai_conversation(
            user_id,
            conversation_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_ai_conversation(user_id, conversation_id):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        conversation_id,
        "conversation_id"
    )

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                c.conversation_id,
                c.user_id,
                c.title,
                c.created_at,
                c.updated_at,
                (
                    SELECT COUNT(*)
                    FROM ai_messages m
                    WHERE m.conversation_id = c.conversation_id
                ) AS message_count
            FROM ai_conversations c
            WHERE c.conversation_id = ?
              AND c.user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        ).fetchone()

        return row_to_conversation(
            row
        )

    finally:
        connection.close()


def get_user_ai_conversations(user_id, limit=20):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_limit(
        limit,
        MAX_LIST_LIMIT
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                c.conversation_id,
                c.user_id,
                c.title,
                c.created_at,
                c.updated_at,
                (
                    SELECT COUNT(*)
                    FROM ai_messages m
                    WHERE m.conversation_id = c.conversation_id
                ) AS message_count
            FROM ai_conversations c
            WHERE c.user_id = ?
            ORDER BY
                c.updated_at DESC,
                c.conversation_id DESC
            LIMIT ?
            """,
            (
                user_id,
                limit
            )
        ).fetchall()

        return [
            row_to_conversation(
                row
            )
            for row in rows
        ]

    finally:
        connection.close()


def update_ai_conversation_title(user_id, conversation_id, title):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        conversation_id,
        "conversation_id"
    )

    normalized_title = validate_title(
        title
    )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE ai_conversations
            SET
                title = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ?
              AND user_id = ?
            """,
            (
                normalized_title,
                conversation_id,
                user_id
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            return None

        return get_ai_conversation(
            user_id,
            conversation_id
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_ai_conversation_messages(user_id, conversation_id, limit=8):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        conversation_id,
        "conversation_id"
    )

    validate_limit(
        limit,
        MAX_MESSAGE_LIMIT
    )

    connection = get_connection()

    try:
        if not conversation_owned(
            connection,
            user_id,
            conversation_id
        ):
            return None

        rows = connection.execute(
            """
            SELECT *
            FROM (
                SELECT
                    message_id,
                    conversation_id,
                    role,
                    content,
                    citations_json,
                    retrieval_status,
                    citation_repair_used,
                    created_at
                FROM ai_messages
                WHERE conversation_id = ?
                ORDER BY message_id DESC
                LIMIT ?
            )
            ORDER BY message_id ASC
            """,
            (
                conversation_id,
                limit
            )
        ).fetchall()

        return [
            row_to_message(
                row
            )
            for row in rows
        ]

    finally:
        connection.close()


def add_ai_conversation_exchange(
    user_id,
    conversation_id,
    user_content,
    assistant_content,
    citations=None,
    retrieval_status=None,
    citation_repair_used=False
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        conversation_id,
        "conversation_id"
    )

    if not isinstance(user_content, str) or not user_content.strip():
        raise ValueError("User message must be a non-empty string")

    if not isinstance(assistant_content, str) or not assistant_content.strip():
        raise ValueError("Assistant message must be a non-empty string")

    if not isinstance(citation_repair_used, bool):
        raise ValueError("citation_repair_used must be a boolean")

    if retrieval_status is not None:
        if not isinstance(retrieval_status, str) or not retrieval_status.strip():
            raise ValueError("retrieval_status must be a non-empty string or None")

        retrieval_status = retrieval_status.strip()

    citations_json = serialize_citations(
        citations
    )

    connection = get_connection()

    try:
        if not conversation_owned(
            connection,
            user_id,
            conversation_id
        ):
            return None

        user_cursor = connection.execute(
            """
            INSERT INTO ai_messages (
                conversation_id,
                role,
                content,
                citations_json,
                retrieval_status,
                citation_repair_used
            )
            VALUES (?, 'user', ?, NULL, NULL, 0)
            """,
            (
                conversation_id,
                user_content.strip()
            )
        )

        user_message_id = user_cursor.lastrowid

        assistant_cursor = connection.execute(
            """
            INSERT INTO ai_messages (
                conversation_id,
                role,
                content,
                citations_json,
                retrieval_status,
                citation_repair_used
            )
            VALUES (?, 'assistant', ?, ?, ?, ?)
            """,
            (
                conversation_id,
                assistant_content.strip(),
                citations_json,
                retrieval_status,
                int(
                    citation_repair_used
                )
            )
        )

        assistant_message_id = assistant_cursor.lastrowid

        connection.execute(
            """
            UPDATE ai_conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ?
              AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        )

        user_row = connection.execute(
            """
            SELECT *
            FROM ai_messages
            WHERE message_id = ?
            """,
            (user_message_id,)
        ).fetchone()

        assistant_row = connection.execute(
            """
            SELECT *
            FROM ai_messages
            WHERE message_id = ?
            """,
            (assistant_message_id,)
        ).fetchone()

        connection.commit()

        return {
            "user_message": row_to_message(
                user_row
            ),
            "assistant_message": row_to_message(
                assistant_row
            )
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_ai_conversation(user_id, conversation_id):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        conversation_id,
        "conversation_id"
    )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM ai_conversations
            WHERE conversation_id = ?
              AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
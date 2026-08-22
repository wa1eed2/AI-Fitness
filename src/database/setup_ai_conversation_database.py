import sqlite3
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "database"
    / "ai_fitness.db"
)


def setup_ai_conversation_database():
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_conversations (
                conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                citations_json TEXT,
                retrieval_status TEXT,
                citation_repair_used INTEGER NOT NULL DEFAULT 0
                    CHECK (citation_repair_used IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (conversation_id)
                    REFERENCES ai_conversations(conversation_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ai_conversations_user
            ON ai_conversations(user_id, updated_at)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation
            ON ai_messages(conversation_id, message_id)
            """
        )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    setup_ai_conversation_database()
    print("PASS: AI conversation database tables are ready")
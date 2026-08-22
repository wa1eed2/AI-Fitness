from src.database.query_workout_log_database import (
    get_connection
)


def setup_adaptation_database():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS adaptation_proposals (
                proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL CHECK (
                    action IN (
                        'insufficient_data',
                        'maintain',
                        'progress_cautiously',
                        'reduce_volume'
                    )
                ),
                status TEXT NOT NULL DEFAULT 'pending' CHECK (
                    status IN (
                        'pending',
                        'accepted',
                        'rejected'
                    )
                ),
                reason_codes_json TEXT NOT NULL,
                signals_json TEXT NOT NULL,
                recommendation_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                FOREIGN KEY (
                    user_id
                )
                REFERENCES users (
                    user_id
                )
                ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_adaptation_proposals_user_created
            ON adaptation_proposals (
                user_id,
                created_at DESC,
                proposal_id DESC
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_adaptation_proposals_user_status
            ON adaptation_proposals (
                user_id,
                status
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    setup_adaptation_database()
    print("Adaptation proposal database setup complete")
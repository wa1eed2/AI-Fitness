import sqlite3
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "database"
    / "ai_fitness.db"
)


def get_vision_database_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        str(
            DATABASE_PATH
        )
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def setup_vision_database():
    connection = get_vision_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vision_analyses (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exercise TEXT NOT NULL
                    CHECK(exercise IN ('squat')),
                status TEXT NOT NULL
                    CHECK(status IN ('analyzed', 'insufficient_data')),
                rep_count INTEGER NOT NULL
                    CHECK(rep_count >= 0),
                source_filename TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL
                    CHECK(file_size_bytes > 0),
                sample_every_n_frames INTEGER NOT NULL
                    CHECK(sample_every_n_frames > 0),
                video_metadata_json TEXT NOT NULL,
                detection_summary_json TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                repetitions_json TEXT NOT NULL,
                limitations_json TEXT NOT NULL,
                analysis_result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (
                    strftime(
                        '%Y-%m-%dT%H:%M:%fZ',
                        'now'
                    )
                ),
                FOREIGN KEY(user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_vision_analyses_user_created
            ON vision_analyses(
                user_id,
                created_at DESC
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    setup_vision_database()

    print("Vision analysis database setup complete")
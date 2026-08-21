import sqlite3

from pathlib import Path


DATABASE_PATH = Path(
    "data/database/ai_fitness.db"
)


def setup_workout_log_database():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_sessions (
                workout_session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                status TEXT NOT NULL DEFAULT 'In Progress'
                    CHECK (status IN ('In Progress', 'Completed', 'Cancelled')),
                primary_goal TEXT,
                planned_duration_minutes REAL,
                actual_duration_minutes REAL,
                notes TEXT,
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_session_exercises (
                session_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_session_id INTEGER NOT NULL,
                exercise_id TEXT NOT NULL,
                exercise_order INTEGER NOT NULL CHECK (exercise_order > 0),
                planned_sets INTEGER,
                planned_reps TEXT,
                planned_rest_seconds INTEGER,
                planned_duration_minutes REAL,
                completed INTEGER NOT NULL DEFAULT 0
                    CHECK (completed IN (0, 1)),
                FOREIGN KEY (workout_session_id)
                    REFERENCES workout_sessions(workout_session_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (exercise_id)
                    REFERENCES exercises(exercise_id)
                    ON DELETE RESTRICT,
                UNIQUE(workout_session_id, exercise_order)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_set_logs (
                set_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_exercise_id INTEGER NOT NULL,
                set_number INTEGER NOT NULL CHECK (set_number > 0),
                reps_completed INTEGER CHECK (reps_completed >= 0),
                weight_kg REAL CHECK (weight_kg >= 0),
                duration_seconds REAL CHECK (duration_seconds >= 0),
                rir_actual INTEGER CHECK (rir_actual BETWEEN 0 AND 10),
                rpe_actual REAL CHECK (rpe_actual BETWEEN 0 AND 10),
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_exercise_id)
                    REFERENCES workout_session_exercises(session_exercise_id)
                    ON DELETE CASCADE,
                UNIQUE(session_exercise_id, set_number)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id
            ON workout_sessions(user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_workout_sessions_status
            ON workout_sessions(status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_workout_session_exercises_session_id
            ON workout_session_exercises(workout_session_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_workout_set_logs_session_exercise_id
            ON workout_set_logs(session_exercise_id)
            """
        )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    setup_workout_log_database()

    print("Workout log database setup complete")
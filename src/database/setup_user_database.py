import sqlite3

from src.database.setup_exercise_database import db_path

def setup_user_database():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            age INTEGER,
            sex TEXT,
            height_cm REAL,
            weight_kg REAL,
            fitness_level TEXT,
            primary_goal TEXT,
            training_days_per_week INTEGER,
            session_duration_minutes INTEGER,
            preferred_environment TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()

if __name__ == '__main__':
    setup_user_database()



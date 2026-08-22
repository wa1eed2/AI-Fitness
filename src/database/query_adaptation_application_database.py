from src.database.query_workout_log_database import (
    get_connection
)

from src.database.setup_adaptation_database import (
    setup_adaptation_database
)


VALID_APPLICATION_ACTIONS = {
    "progress_cautiously",
    "reduce_volume"
}

VALID_APPLICATION_FIELDS = {
    "session_duration_minutes"
}


def validate_positive_integer(
    value,
    field_name
):
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def validate_numeric(
    value,
    field_name
):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")


def validate_limit(limit):
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("limit must be an integer")

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")


def values_match(
    first,
    second,
    tolerance=0.000001
):
    if isinstance(first, bool) or isinstance(second, bool):
        return False

    if not isinstance(first, (int, float)) or not isinstance(second, (int, float)):
        return False

    return abs(
        float(first)
        - float(second)
    ) <= tolerance


def row_to_adaptation_application(row):
    if row is None:
        return None

    return {
        "application_id": row[
            "application_id"
        ],
        "proposal_id": row[
            "proposal_id"
        ],
        "user_id": row[
            "user_id"
        ],
        "action": row[
            "action"
        ],
        "field_name": row[
            "field_name"
        ],
        "before_value": row[
            "before_value"
        ],
        "after_value": row[
            "after_value"
        ],
        "change_amount": row[
            "change_amount"
        ],
        "change_percent": row[
            "change_percent"
        ],
        "policy_version": row[
            "policy_version"
        ],
        "status": row[
            "status"
        ],
        "applied_at": row[
            "applied_at"
        ],
        "rolled_back_at": row[
            "rolled_back_at"
        ]
    }


def create_profile_adaptation_application(
    user_id,
    proposal_id,
    action,
    field_name,
    before_value,
    after_value,
    change_amount,
    change_percent,
    policy_version
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        proposal_id,
        "proposal_id"
    )

    if action not in VALID_APPLICATION_ACTIONS:
        raise ValueError("Unsupported adaptation application action")

    if field_name not in VALID_APPLICATION_FIELDS:
        raise ValueError("Unsupported adaptation application field")

    validate_numeric(
        before_value,
        "before_value"
    )

    validate_numeric(
        after_value,
        "after_value"
    )

    validate_numeric(
        change_amount,
        "change_amount"
    )

    validate_numeric(
        change_percent,
        "change_percent"
    )

    if not isinstance(policy_version, str) or not policy_version.strip():
        raise ValueError("policy_version must be a non-empty string")

    setup_adaptation_database()

    connection = get_connection()

    try:
        connection.execute(
            "BEGIN IMMEDIATE"
        )

        proposal = connection.execute(
            """
            SELECT
                proposal_id,
                user_id,
                action,
                status
            FROM adaptation_proposals
            WHERE proposal_id = ?
              AND user_id = ?
            """,
            (
                proposal_id,
                user_id
            )
        ).fetchone()

        if proposal is None:
            raise ValueError("Adaptation proposal not found")

        if proposal[
            "status"
        ] != "accepted":
            raise ValueError("Adaptation proposal must be accepted before application")

        if proposal[
            "action"
        ] != action:
            raise ValueError("Adaptation proposal action changed before application")

        existing = connection.execute(
            """
            SELECT application_id
            FROM adaptation_applications
            WHERE proposal_id = ?
            """,
            (
                proposal_id,
            )
        ).fetchone()

        if existing is not None:
            raise ValueError("Adaptation proposal has already been applied")

        profile = connection.execute(
            """
            SELECT
                session_duration_minutes
            FROM user_profiles
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        ).fetchone()

        if profile is None:
            raise ValueError("User profile not found")

        current_value = profile[
            field_name
        ]

        if not values_match(
            current_value,
            before_value
        ):
            raise ValueError("User profile changed after adaptation was calculated")

        connection.execute(
            """
            UPDATE user_profiles
            SET session_duration_minutes = ?
            WHERE user_id = ?
            """,
            (
                after_value,
                user_id
            )
        )

        cursor = connection.execute(
            """
            INSERT INTO adaptation_applications (
                proposal_id,
                user_id,
                action,
                field_name,
                before_value,
                after_value,
                change_amount,
                change_percent,
                policy_version,
                status
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                'applied'
            )
            """,
            (
                proposal_id,
                user_id,
                action,
                field_name,
                before_value,
                after_value,
                change_amount,
                change_percent,
                policy_version.strip()
            )
        )

        application_id = cursor.lastrowid

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM adaptation_applications
            WHERE application_id = ?
              AND user_id = ?
            """,
            (
                application_id,
                user_id
            )
        ).fetchone()

        return row_to_adaptation_application(
            row
        )

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_adaptation_application(
    user_id,
    application_id
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        application_id,
        "application_id"
    )

    setup_adaptation_database()

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM adaptation_applications
            WHERE application_id = ?
              AND user_id = ?
            """,
            (
                application_id,
                user_id
            )
        ).fetchone()

        return row_to_adaptation_application(
            row
        )

    finally:
        connection.close()


def get_adaptation_application_by_proposal(
    user_id,
    proposal_id
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        proposal_id,
        "proposal_id"
    )

    setup_adaptation_database()

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM adaptation_applications
            WHERE proposal_id = ?
              AND user_id = ?
            """,
            (
                proposal_id,
                user_id
            )
        ).fetchone()

        return row_to_adaptation_application(
            row
        )

    finally:
        connection.close()


def get_user_adaptation_applications(
    user_id,
    limit=20
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_limit(
        limit
    )

    setup_adaptation_database()

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM adaptation_applications
            WHERE user_id = ?
            ORDER BY
                applied_at DESC,
                application_id DESC
            LIMIT ?
            """,
            (
                user_id,
                limit
            )
        ).fetchall()

        return [
            row_to_adaptation_application(
                row
            )
            for row in rows
        ]

    finally:
        connection.close()


def rollback_profile_adaptation_application(
    user_id,
    application_id
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        application_id,
        "application_id"
    )

    setup_adaptation_database()

    connection = get_connection()

    try:
        connection.execute(
            "BEGIN IMMEDIATE"
        )

        application = connection.execute(
            """
            SELECT *
            FROM adaptation_applications
            WHERE application_id = ?
              AND user_id = ?
            """,
            (
                application_id,
                user_id
            )
        ).fetchone()

        if application is None:
            return None

        if application[
            "status"
        ] != "applied":
            raise ValueError("Adaptation application has already been rolled back")

        field_name = application[
            "field_name"
        ]

        if field_name not in VALID_APPLICATION_FIELDS:
            raise ValueError("Stored adaptation field is not rollback-safe")

        profile = connection.execute(
            """
            SELECT
                session_duration_minutes
            FROM user_profiles
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        ).fetchone()

        if profile is None:
            raise ValueError("User profile not found")

        current_value = profile[
            field_name
        ]

        if not values_match(
            current_value,
            application[
                "after_value"
            ]
        ):
            raise ValueError(
                "Current profile no longer matches the applied adaptation; rollback refused"
            )

        connection.execute(
            """
            UPDATE user_profiles
            SET session_duration_minutes = ?
            WHERE user_id = ?
            """,
            (
                application[
                    "before_value"
                ],
                user_id
            )
        )

        connection.execute(
            """
            UPDATE adaptation_applications
            SET
                status = 'rolled_back',
                rolled_back_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
              AND user_id = ?
              AND status = 'applied'
            """,
            (
                application_id,
                user_id
            )
        )

        connection.commit()

        updated = connection.execute(
            """
            SELECT *
            FROM adaptation_applications
            WHERE application_id = ?
              AND user_id = ?
            """,
            (
                application_id,
                user_id
            )
        ).fetchone()

        return row_to_adaptation_application(
            updated
        )

    except:
        connection.rollback()
        raise

    finally:
        connection.close()
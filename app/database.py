"""
SQLite persistence for the simulated CRM service.

Responsibilities:
- Create the CRM leads table.
- Save incoming leads.
- Retrieve previously stored leads.
"""

import sqlite3
from sqlite3 import IntegrityError
from pathlib import Path


# Resolve the database path relative to the project,
# not the terminal's current working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "crm.db"


def get_connection():
    """Open a SQLite connection with named-row access."""

    connection = sqlite3.connect(DATABASE_PATH)

    # Allow access to columns by name instead of index.
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create the leads table if it does not already exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                received_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def find_lead(reference):
    """Find a stored lead by its external reference."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, reference, name, email, message, received_at
            FROM leads
            WHERE reference = ?
            """,
            (reference,)
        ).fetchone()

    return dict(row) if row else None



def save_lead(lead):
    """
    Save a lead without overwriting an existing record.

    Returns:
        "created"   - A new lead was inserted.
        "duplicate" - The same lead already exists.
        "conflict"  - The reference belongs to different lead data.
    """

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO leads (reference, name, email, message)
                VALUES (?, ?, ?, ?)
                """,
                (
                    lead.reference,
                    lead.name,
                    lead.email,
                    lead.message,
                ),
            )

        return "created"

    except IntegrityError:
        # Another request may have already inserted this reference.
        # Read the committed record before deciding what happened.
        existing = find_lead(lead.reference)

        if existing is None:
            # The constraint failure was not a reference duplicate.
            raise

        if (
            existing["name"] == lead.name
            and existing["email"] == lead.email
            and existing["message"] == lead.message
        ):
            return "duplicate"

        return "conflict"


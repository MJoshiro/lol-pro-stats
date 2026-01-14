"""
Database connection manager for LoL Pro Player Stats System.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_db_path() -> str:
    """Get the full path to the database file."""
    return config.get_db_path_file()


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    Ensures connections are properly closed after use.
    
    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players")
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize the database with required tables.
    Creates tables if they don't exist.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Create players table with raw totals for accurate stat computation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ign TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT '',
                team TEXT DEFAULT '',
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                total_gold INTEGER DEFAULT 0,
                total_cs INTEGER DEFAULT 0,
                total_damage INTEGER DEFAULT 0,
                total_minutes REAL DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_players_ign ON players(ign)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_players_role ON players(role)
        """)
        
        conn.commit()
        print(f"Database initialized at: {get_db_path()}")


if __name__ == "__main__":
    # Test database initialization
    init_db()
    print("Database setup complete!")

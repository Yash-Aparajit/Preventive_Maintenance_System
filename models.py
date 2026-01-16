import sqlite3

DB_NAME = "app.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ASSET MASTER TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT UNIQUE NOT NULL,
            asset_name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            rotation_slot INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active'
        )
    """)

        # PM WEEKLY ATTENDANCE TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pm_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT NOT NULL,
            week_number INTEGER NOT NULL,
            status TEXT CHECK(status IN ('DONE', 'MISSED')) NOT NULL,
            recorded_on TEXT NOT NULL,
            UNIQUE(asset_id, week_number)
        )
    """)


    conn.commit()
    conn.close()

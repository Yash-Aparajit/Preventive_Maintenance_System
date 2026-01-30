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

    # EVENTS TABLE (MANUAL LOGS)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_subtype TEXT,
            description TEXT NOT NULL,
            cost REAL,
            name TEXT,
            created_on TEXT NOT NULL
        )
    """)

        # FINDINGS TAG MASTER (SYSTEM CONTROLLED)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS finding_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT NOT NULL,
            tag_code TEXT NOT NULL,
            tag_label TEXT NOT NULL,
            UNIQUE(asset_type, tag_code)
        )
    """)

    # FINDINGS LOG (LINKED TO PM WEEK)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS findings_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT NOT NULL,
            week_number INTEGER NOT NULL,
            tag_code TEXT NOT NULL,
            note TEXT,
            created_on TEXT NOT NULL,
            UNIQUE(asset_id, week_number, tag_code)
        )
    """)

        # AUTO-SEED DEFAULT FINDING TAGS (safe insert)
    default_tags = {
        "Machine": [
            ("DUST_CLEANED", "Dust cleaned"),
            ("SENSOR_CLEANED", "Sensor cleaned"),
            ("LOOSE_CONNECTION", "Loose connection tightened"),
            ("PRESSURE_ADJUSTED", "Pressure adjusted"),
            ("LUBRICATED", "Lubrication done"),
        ],
        "Nut Runner": [
            ("DUST_CLEANED", "Dust cleaned"),
            ("TORQUE_ADJUSTED", "Torque adjusted"),
            ("SOCKET_CHANGED", "Socket changed"),
            ("BIT_CHANGED", "Bit changed"),
            ("LOOSE_CONNECTION", "Loose connection tightened"),
        ],
        "Fixture": [
            ("CLEANED", "Cleaned"),
            ("ALIGNMENT_ADJUSTED", "Alignment adjusted"),
            ("PIN_CHECKED", "Pin/locator checked"),
            ("CLAMP_CHECKED", "Clamp checked"),
            ("FASTENER_TIGHTENED", "Fastener tightened"),
        ],
        "Trolley": [
            ("CLEANED", "Cleaned"),
            ("WHEEL_CHECKED", "Wheel checked"),
            ("FASTENER_TIGHTENED", "Fastener tightened"),
            ("BEARING_CHECKED", "Bearing checked"),
            ("WELD_INSPECTED", "Weld inspected"),
        ]
    }

    for asset_type, tags in default_tags.items():
        for code, label in tags:
            cur.execute("""
                INSERT OR IGNORE INTO finding_tags (asset_type, tag_code, tag_label)
                VALUES (?, ?, ?)
            """, (asset_type, code, label))

    conn.commit()
    conn.close()

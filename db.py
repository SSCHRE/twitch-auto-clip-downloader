import sqlite3

DB_FILE = "clips.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clips (
        clip_id TEXT PRIMARY KEY,
        channel TEXT,
        title TEXT,
        url TEXT,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        uploaded INTEGER DEFAULT 0
    )
    """)

    # Migration for existing databases
    c.execute("PRAGMA table_info(clips)")
    columns = [row[1] for row in c.fetchall()]

    if "uploaded" not in columns:
        c.execute("""
        ALTER TABLE clips
        ADD COLUMN uploaded INTEGER DEFAULT 0
        """)

    conn.commit()
    conn.close()

def has_clip(clip_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        "SELECT 1 FROM clips WHERE clip_id = ?",
        (clip_id,)
    )

    result = c.fetchone() is not None

    conn.close()
    return result

def save_clip(clip_id, channel, title, url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    INSERT OR IGNORE INTO clips
    (
        clip_id,
        channel,
        title,
        url
    )
    VALUES (?, ?, ?, ?)
    """, (
        clip_id,
        channel,
        title,
        url
    ))

    conn.commit()
    conn.close()

def is_uploaded(clip_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    SELECT uploaded
    FROM clips
    WHERE clip_id = ?
    """, (clip_id,))

    result = c.fetchone()

    conn.close()

    return result is not None and result[0] == 1

def mark_uploaded(clip_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    UPDATE clips
    SET uploaded = 1
    WHERE clip_id = ?
    """, (clip_id,))

    conn.commit()
    conn.close()

def get_unuploaded_clips():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    SELECT clip_id
    FROM clips
    WHERE uploaded = 0
    """)

    results = [
        row[0]
        for row in c.fetchall()
    ]

    conn.close()

    return results

def mark_all_uploaded():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    UPDATE clips
    SET uploaded = 1
    WHERE uploaded = 0
    """)

    conn.commit()
    conn.close()
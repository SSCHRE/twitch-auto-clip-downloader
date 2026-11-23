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

    c.execute("""
    CREATE TABLE IF NOT EXISTS vods (
        vod_id TEXT PRIMARY KEY,
        channel TEXT,
        title TEXT,
        url TEXT,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        uploaded INTEGER DEFAULT 0,
        created_at TEXT
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

    if "created_at" not in columns:
        c.execute("""
        ALTER TABLE clips
        ADD COLUMN created_at TEXT
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

def save_clip(clip_id, channel, title, url, created_at=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    INSERT OR IGNORE INTO clips
    (
        clip_id,
        channel,
        title,
        url,
        created_at
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        clip_id,
        channel,
        title,
        url,
        created_at,
    ))

    if created_at:
        c.execute("""
        UPDATE clips
        SET created_at = ?
        WHERE clip_id = ?
          AND created_at IS NULL
        """, (created_at, clip_id))

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


def has_vod(vod_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        "SELECT 1 FROM vods WHERE vod_id = ?",
        (vod_id,)
    )

    result = c.fetchone() is not None

    conn.close()
    return result


def save_vod(vod_id, channel, title, url, created_at=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    INSERT OR IGNORE INTO vods
    (
        vod_id,
        channel,
        title,
        url,
        created_at
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        vod_id,
        channel,
        title,
        url,
        created_at,
    ))

    if created_at:
        c.execute("""
        UPDATE vods
        SET created_at = ?
        WHERE vod_id = ?
          AND created_at IS NULL
        """, (created_at, vod_id))

    conn.commit()
    conn.close()


def get_unuploaded_vods():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    SELECT vod_id
    FROM vods
    WHERE uploaded = 0
    """)

    results = [
        row[0]
        for row in c.fetchall()
    ]

    conn.close()

    return results


def mark_all_vods_uploaded():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    UPDATE vods
    SET uploaded = 1
    WHERE uploaded = 0
    """)

    conn.commit()
    conn.close()

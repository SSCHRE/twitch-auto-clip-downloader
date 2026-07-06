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
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def has_clip(clip_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT 1 FROM clips WHERE clip_id = ?", (clip_id,))
    result = c.fetchone() is not None

    conn.close()
    return result

def save_clip(clip_id, channel, title, url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    INSERT OR IGNORE INTO clips (clip_id, channel, title, url)
    VALUES (?, ?, ?, ?)
    """, (clip_id, channel, title, url))

    conn.commit()
    conn.close()

def get_latest_clip_time(channel):
    # return ISO timestamp or None
    pass

def save_latest_clip_time(channel, created_at):
    pass
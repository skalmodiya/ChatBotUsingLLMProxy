import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "chatbot.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id            TEXT PRIMARY KEY,
                title         TEXT NOT NULL DEFAULT 'New Chat',
                provider      TEXT NOT NULL DEFAULT '',
                model         TEXT NOT NULL DEFAULT '',
                system_prompt TEXT NOT NULL DEFAULT '',
                is_compare    INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                provider    TEXT NOT NULL DEFAULT '',
                model       TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
        """)
    # Safe migrations for existing DBs
    _migrate(conn_factory=_conn)


def _migrate(conn_factory):
    migrations = [
        ("sessions",  "is_compare",  "ALTER TABLE sessions ADD COLUMN is_compare INTEGER NOT NULL DEFAULT 0"),
        ("messages",  "provider",    "ALTER TABLE messages ADD COLUMN provider TEXT NOT NULL DEFAULT ''"),
        ("messages",  "model",       "ALTER TABLE messages ADD COLUMN model TEXT NOT NULL DEFAULT ''"),
    ]
    with conn_factory() as conn:
        for table, col, sql in migrations:
            existing = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if col not in existing:
                conn.execute(sql)


def _now():
    return datetime.now(timezone.utc).isoformat()


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(provider="", model="", system_prompt="", is_compare=False):
    sid = str(uuid.uuid4())
    now = _now()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO sessions(id, provider, model, system_prompt, is_compare, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
            (sid, provider, model, system_prompt, int(is_compare), now, now),
        )
    return sid


def list_sessions():
    with _conn() as conn:
        rows = conn.execute("""
            SELECT s.id, s.title, s.provider, s.model, s.updated_at, s.is_compare,
                   (SELECT content FROM messages
                    WHERE session_id = s.id ORDER BY id DESC LIMIT 1) AS preview
            FROM sessions s
            ORDER BY s.updated_at DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_session(session_id):
    with _conn() as conn:
        session = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not session:
            return None
        msgs = conn.execute(
            "SELECT role, content, provider, model, created_at FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return {"session": dict(session), "messages": [dict(m) for m in msgs]}


def update_session_title(session_id, title):
    with _conn() as conn:
        conn.execute(
            "UPDATE sessions SET title=?, updated_at=? WHERE id=?",
            (title[:120], _now(), session_id),
        )


def update_session_meta(session_id, provider=None, model=None, system_prompt=None):
    fields, vals = [], []
    if provider is not None:
        fields.append("provider=?"); vals.append(provider)
    if model is not None:
        fields.append("model=?"); vals.append(model)
    if system_prompt is not None:
        fields.append("system_prompt=?"); vals.append(system_prompt)
    if not fields:
        return
    fields.append("updated_at=?"); vals.append(_now())
    vals.append(session_id)
    with _conn() as conn:
        conn.execute(f"UPDATE sessions SET {', '.join(fields)} WHERE id=?", vals)


def delete_session(session_id):
    with _conn() as conn:
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))


def delete_all_sessions():
    with _conn() as conn:
        conn.execute("DELETE FROM sessions")


# ── Messages ──────────────────────────────────────────────────────────────────

def append_messages(session_id, pairs):
    """pairs: list of (role, content, provider, model) tuples"""
    now = _now()
    with _conn() as conn:
        conn.executemany(
            "INSERT INTO messages(session_id, role, content, provider, model, created_at) VALUES(?,?,?,?,?,?)",
            [(session_id, role, content, prov, mdl, now) for role, content, prov, mdl in pairs],
        )
        conn.execute("UPDATE sessions SET updated_at=? WHERE id=?", (now, session_id))

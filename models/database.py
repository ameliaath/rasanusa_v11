"""
models/database.py
──────────────────
Koneksi SQLite dan inisialisasi tabel.
Satu tempat untuk semua urusan database — kalau mau ganti ke PostgreSQL
nanti cukup edit file ini saja.
"""
import sqlite3, os

DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'rasanusa.db')


def get_db():
    """Buka koneksi SQLite, baris dikembalikan sebagai dict-like Row."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Buat semua tabel kalau belum ada. Dipanggil sekali saat app start."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    UNIQUE NOT NULL,
            password   TEXT    NOT NULL,
            is_admin   INTEGER NOT NULL DEFAULT 0,
            created_at TEXT    DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS favorites (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            recipe_id  INTEGER NOT NULL,
            created_at TEXT    DEFAULT (datetime('now','localtime')),
            UNIQUE(user_id, recipe_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            recipe_id  INTEGER NOT NULL,
            text       TEXT    NOT NULL,
            created_at TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS checklists (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            recipe_id  INTEGER NOT NULL,
            items      TEXT    NOT NULL DEFAULT '[]',
            UNIQUE(user_id, recipe_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS ratings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            recipe_id  INTEGER NOT NULL,
            stars      INTEGER NOT NULL DEFAULT 0,
            UNIQUE(user_id, recipe_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            recipe_id  INTEGER NOT NULL,
            title      TEXT    NOT NULL,
            category   TEXT    NOT NULL,
            visited_at TEXT    NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS preferences (
            user_id    INTEGER PRIMARY KEY,
            vegetarian INTEGER DEFAULT 0,
            no_spicy   INTEGER DEFAULT 0,
            no_seafood INTEGER DEFAULT 0,
            no_gluten  INTEGER DEFAULT 0,
            no_nuts    INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS flavor_profile (
            user_id        INTEGER PRIMARY KEY,
            spicy_level    INTEGER DEFAULT 0,
            sweet_level    INTEGER DEFAULT 0,
            savory_level   INTEGER DEFAULT 0,
            sour_level     INTEGER DEFAULT 0,
            servings       INTEGER DEFAULT 2,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    # Tambah kolom is_admin kalau belum ada (migrasi aman)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    # Buat akun admin default kalau belum ada
    from werkzeug.security import generate_password_hash
    existing = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (?,?,1)",
            ('admin', generate_password_hash('admin123'))
        )
        conn.commit()
    conn.close()

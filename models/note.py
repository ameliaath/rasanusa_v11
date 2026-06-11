"""
models/note.py
──────────────
Semua query yang berhubungan dengan tabel notes dan checklists.
"""
import json
from models.database import get_db


# ── Notes ─────────────────────────────────────────────────────────────────────

def get_notes(user_id, recipe_id):
    """Ambil semua catatan milik user untuk resep tertentu."""
    conn = get_db()
    rows = conn.execute(
        'SELECT id, text FROM notes WHERE user_id=? AND recipe_id=? ORDER BY id',
        (user_id, recipe_id)
    ).fetchall()
    conn.close()
    return [{'id': r['id'], 'text': r['text']} for r in rows]


def add_note(user_id, recipe_id, text):
    """Tambah catatan baru. Return list catatan terbaru."""
    conn = get_db()
    conn.execute(
        'INSERT INTO notes (user_id, recipe_id, text) VALUES (?, ?, ?)',
        (user_id, recipe_id, text)
    )
    conn.commit()
    rows = conn.execute(
        'SELECT id, text FROM notes WHERE user_id=? AND recipe_id=? ORDER BY id',
        (user_id, recipe_id)
    ).fetchall()
    conn.close()
    return [{'id': r['id'], 'text': r['text']} for r in rows]


def delete_note(user_id, note_id):
    """Hapus catatan berdasarkan ID (pastikan milik user yang benar)."""
    conn = get_db()
    conn.execute(
        'DELETE FROM notes WHERE id=? AND user_id=?', (note_id, user_id)
    )
    conn.commit()
    conn.close()


# ── Checklists ────────────────────────────────────────────────────────────────

def get_checklist(user_id, recipe_id):
    """Ambil checklist bahan untuk resep tertentu."""
    conn = get_db()
    row = conn.execute(
        'SELECT items FROM checklists WHERE user_id=? AND recipe_id=?',
        (user_id, recipe_id)
    ).fetchone()
    conn.close()
    return json.loads(row['items']) if row else []


def save_checklist(user_id, recipe_id, items):
    """Simpan / update checklist bahan."""
    conn = get_db()
    conn.execute(
        '''INSERT INTO checklists (user_id, recipe_id, items) VALUES (?,?,?)
           ON CONFLICT(user_id, recipe_id) DO UPDATE SET items=excluded.items''',
        (user_id, recipe_id, json.dumps(items))
    )
    conn.commit()
    conn.close()

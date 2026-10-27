"""Saving and loading session notes in the local database (AppData)."""
import time

def notes_for_session(conn, session_id):
    return conn.execute(
        "SELECT id, title, body FROM notes WHERE session_id IS ? ORDER BY id",
        (session_id,),
    ).fetchall()

def create_note(conn, session_id, title, body):
    cur = conn.execute(
        "INSERT INTO notes (session_id, title, body, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, title, body, time.time()),
    )
    return cur.lastrowid

def update_note(conn, note_id, title, body):
    conn.execute(
        "UPDATE notes SET title = ?, body = ?, updated_at = ? WHERE id = ?",
        (title, body, time.time(), note_id),
    )

def delete_note(conn, note_id):
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))

def session_ids_with_notes(conn):
    rows = conn.execute(
        "SELECT DISTINCT session_id FROM notes WHERE session_id IS NOT NULL"
    ).fetchall()
    return [row[0] for row in rows]
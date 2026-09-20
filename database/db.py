"""
Repository layer for database operations.
Dual-mode: uses SQLite locally, and Postgres via DATABASE_URL if configured.
Uses sqlite3 or psycopg2 depending on the environment.
"""

import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

from config.settings import settings

# ── Connection Management ───────────────────────────────────────────────

@contextmanager
def get_db_connection():
    """Yields a database connection depending on the environment."""
    if settings.is_production:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(settings.DATABASE_URL)
        # Use DictCursor to return dicts instead of tuples
        conn.cursor_factory = psycopg2.extras.DictCursor
    else:
        # SQLite
        # Ensure directory exists
        if str(settings.sqlite_path) != ":memory:":
            settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(settings.sqlite_path)
        conn.row_factory = sqlite3.Row
        
    try:
        yield conn
    finally:
        conn.close()

# ── Schema Creation ─────────────────────────────────────────────────────

def init_db():
    """Initializes the database schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Dialect differences
        is_pg = settings.is_production
        
        # Books
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY,
                title TEXT,
                author TEXT,
                genre TEXT,
                sub_genre TEXT,
                pages INTEGER,
                reading_level TEXT,
                avg_rating REAL,
                publish_year INTEGER,
                description TEXT,
                tags TEXT
            )
        """)
        
        # Users
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                created_at {"TIMESTAMP" if is_pg else "DATETIME"} DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Preferences
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT PRIMARY KEY REFERENCES users(user_id),
                favorite_genres TEXT,
                favorite_authors TEXT,
                reading_level TEXT,
                preferred_length TEXT,
                reading_goal TEXT,
                current_mood TEXT,
                updated_at {"TIMESTAMP" if is_pg else "DATETIME"} DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Reading History
        id_col = "id SERIAL PRIMARY KEY" if is_pg else "id INTEGER PRIMARY KEY AUTOINCREMENT"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS reading_history (
                {id_col},
                user_id TEXT REFERENCES users(user_id),
                book_id TEXT REFERENCES books(book_id),
                status TEXT,
                rated REAL,
                added_at {"TIMESTAMP" if is_pg else "DATETIME"} DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, book_id)
            )
        """)
        
        # Favorites
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS favorites (
                {id_col},
                user_id TEXT REFERENCES users(user_id),
                book_id TEXT REFERENCES books(book_id),
                added_at {"TIMESTAMP" if is_pg else "DATETIME"} DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, book_id)
            )
        """)
        
        # Feedback
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS feedback (
                {id_col},
                user_id TEXT REFERENCES users(user_id),
                book_id TEXT REFERENCES books(book_id),
                sentiment TEXT,
                reason TEXT,
                created_at {"TIMESTAMP" if is_pg else "DATETIME"} DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, book_id)
            )
        """)
        
        # Recommendations
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS recommendations (
                {id_col},
                user_id TEXT REFERENCES users(user_id),
                book_id TEXT REFERENCES books(book_id),
                request_text TEXT,
                score REAL,
                explanation TEXT,
                shown_at {"TIMESTAMP" if is_pg else "DATETIME"} DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

# ── Parameter Placeholder Helper ────────────────────────────────────────

def _param(name: str) -> str:
    """Returns the correct parameter placeholder for the SQL dialect."""
    return f"%({name})s" if settings.is_production else f":{name}"

# ── Repositories ────────────────────────────────────────────────────────

def get_user_profile(user_id: str) -> Dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM preferences WHERE user_id = {_param('user_id')}", {"user_id": user_id})
        row = cursor.fetchone()
        
        defaults = {
            "user_id": user_id,
            "favorite_genres": "",
            "favorite_authors": "",
            "reading_level": "medium",
            "preferred_length": "medium",
            "reading_goal": "",
            "current_mood": ""
        }
        
        if row:
            profile = dict(row)
            # Coalesce None values to defaults (SQLite returns None for unset columns)
            for key, default_val in defaults.items():
                if profile.get(key) is None:
                    profile[key] = default_val
            return profile
            
        return defaults

def update_user_preference(user_id: str, field: str, value: str):
    valid_fields = ["favorite_genres", "favorite_authors", "reading_level", 
                    "preferred_length", "reading_goal", "current_mood"]
    if field not in valid_fields:
        raise ValueError(f"Invalid preference field: {field}")
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Upsert logic depends on dialect.
        if settings.is_production:
            cursor.execute(f"""
                INSERT INTO preferences (user_id, {field}) 
                VALUES ({_param('user_id')}, {_param('val')})
                ON CONFLICT (user_id) DO UPDATE SET {field} = EXCLUDED.{field}
            """, {"user_id": user_id, "val": value})
        else:
            cursor.execute(f"""
                INSERT INTO preferences (user_id, {field}) 
                VALUES ({_param('user_id')}, {_param('val')})
                ON CONFLICT(user_id) DO UPDATE SET {field}=excluded.{field}
            """, {"user_id": user_id, "val": value})
            
        conn.commit()

def get_reading_history(user_id: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT rh.book_id, rh.status, rh.rated, b.title 
            FROM reading_history rh
            JOIN books b ON rh.book_id = b.book_id
            WHERE rh.user_id = {_param('user_id')}
        """, {"user_id": user_id})
        return [dict(row) for row in cursor.fetchall()]

def mark_as_read(user_id: str, book_id: str, rating: Optional[float] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if settings.is_production:
            cursor.execute(f"""
                INSERT INTO reading_history (user_id, book_id, status, rated)
                VALUES ({_param('uid')}, {_param('bid')}, 'read', {_param('rat')})
                ON CONFLICT (user_id, book_id) DO UPDATE 
                SET status = 'read', rated = EXCLUDED.rated
            """, {"uid": user_id, "bid": book_id, "rat": rating})
        else:
            cursor.execute(f"""
                INSERT INTO reading_history (user_id, book_id, status, rated)
                VALUES ({_param('uid')}, {_param('bid')}, 'read', {_param('rat')})
                ON CONFLICT(user_id, book_id) DO UPDATE 
                SET status = 'read', rated = excluded.rated
            """, {"uid": user_id, "bid": book_id, "rat": rating})
            
        conn.commit()

def record_feedback(user_id: str, book_id: str, sentiment: str, reason: Optional[str] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if settings.is_production:
            cursor.execute(f"""
                INSERT INTO feedback (user_id, book_id, sentiment, reason)
                VALUES ({_param('uid')}, {_param('bid')}, {_param('sen')}, {_param('rsn')})
                ON CONFLICT (user_id, book_id) DO UPDATE 
                SET sentiment = EXCLUDED.sentiment, reason = EXCLUDED.reason
            """, {"uid": user_id, "bid": book_id, "sen": sentiment, "rsn": reason})
        else:
            cursor.execute(f"""
                INSERT INTO feedback (user_id, book_id, sentiment, reason)
                VALUES ({_param('uid')}, {_param('bid')}, {_param('sen')}, {_param('rsn')})
                ON CONFLICT(user_id, book_id) DO UPDATE 
                SET sentiment = excluded.sentiment, reason = excluded.reason
            """, {"uid": user_id, "bid": book_id, "sen": sentiment, "rsn": reason})
            
        conn.commit()

def get_feedback(user_id: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT f.book_id, f.sentiment, b.genre, b.author, b.tags 
            FROM feedback f
            JOIN books b ON f.book_id = b.book_id
            WHERE f.user_id = {_param('uid')}
        """, {"uid": user_id})
        return [dict(row) for row in cursor.fetchall()]

def search_books(query: str = "", genre: str = "", author: str = "", 
                 max_length: Optional[int] = None, reading_level: str = "", 
                 limit: int = 20) -> List[Dict[str, Any]]:
    
    where_clauses = []
    params = {}
    
    if query:
        where_clauses.append(f"(title LIKE {_param('q')} OR description LIKE {_param('q')} OR tags LIKE {_param('q')})")
        params["q"] = f"%{query}%"
    if genre:
        where_clauses.append(f"genre LIKE {_param('g')}")
        params["g"] = f"%{genre}%"
    if author:
        where_clauses.append(f"author LIKE {_param('a')}")
        params["a"] = f"%{author}%"
    if max_length:
        where_clauses.append(f"pages <= {_param('l')}")
        params["l"] = max_length
    if reading_level:
        where_clauses.append(f"reading_level = {_param('rl')}")
        params["rl"] = reading_level
        
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    sql = f"SELECT * FROM books WHERE {where_sql} LIMIT {limit}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

def get_book_details(book_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM books WHERE book_id = {_param('bid')}", {"bid": book_id})
        row = cursor.fetchone()
        return dict(row) if row else None

def get_book_details_multi(book_ids: List[str]) -> List[Dict[str, Any]]:
    if not book_ids:
        return []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if settings.is_production:
            # psycopg2 uses = ANY(%s)
            cursor.execute("SELECT * FROM books WHERE book_id = ANY(%s)", (book_ids,))
        else:
            # sqlite uses IN (?, ?, ?)
            placeholders = ",".join("?" for _ in book_ids)
            cursor.execute(f"SELECT * FROM books WHERE book_id IN ({placeholders})", book_ids)
        return [dict(row) for row in cursor.fetchall()]

def add_to_favorites(user_id: str, book_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if settings.is_production:
            cursor.execute(f"""
                INSERT INTO favorites (user_id, book_id)
                VALUES ({_param('uid')}, {_param('bid')})
                ON CONFLICT (user_id, book_id) DO NOTHING
            """, {"uid": user_id, "bid": book_id})
        else:
            cursor.execute(f"""
                INSERT INTO favorites (user_id, book_id)
                VALUES ({_param('uid')}, {_param('bid')})
                ON CONFLICT(user_id, book_id) DO NOTHING
            """, {"uid": user_id, "bid": book_id})
            
        conn.commit()

def log_recommendations(user_id: str, request_text: str, recommendations: List[Dict[str, Any]]):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for rec in recommendations:
            cursor.execute(f"""
                INSERT INTO recommendations (user_id, book_id, request_text, score, explanation)
                VALUES ({_param('uid')}, {_param('bid')}, {_param('req')}, {_param('scr')}, {_param('exp')})
            """, {
                "uid": user_id, 
                "bid": rec.get("book_id"),
                "req": request_text,
                "scr": rec.get("score"),
                "exp": rec.get("explanation")
            })
        conn.commit()

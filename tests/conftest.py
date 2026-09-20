import pytest
import os
import sqlite3
from pathlib import Path

# Override config for tests before importing modules
os.environ["DATABASE_PATH"] = ":memory:" # Use in-memory SQLite for tests
os.environ["CHROMA_PERSIST_DIR"] = "" # Disable chroma persistence for tests

from database import db
from config.settings import settings

@pytest.fixture(autouse=True, scope="function")
def setup_test_db(monkeypatch, tmp_path):
    test_db = tmp_path / "test.db"
    # Mock the sqlite_path property to return the temp path
    monkeypatch.setattr(settings.__class__, "sqlite_path", property(lambda self: test_db))
    # Initialize the schema
    db.init_db()
    
    # Insert test data
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books")
        cursor.execute("DELETE FROM users")
        
        cursor.execute("""
            INSERT INTO books (book_id, title, author, genre, sub_genre, pages, reading_level, avg_rating, description, tags)
            VALUES 
            ('B999', 'Test Sci-Fi Book', 'Test Author', 'Science Fiction', 'Space Opera', 350, 'medium', 4.5, 'A great book.', 'space, future'),
            ('B998', 'Test Romance Book', 'Author B', 'Romance', 'Contemporary', 200, 'easy', 4.0, 'A sweet romance.', 'love, modern')
        """)
        
        cursor.execute("INSERT INTO users (user_id, display_name) VALUES ('test_user', 'Test User')")
        
        # Give user a preference
        cursor.execute("""
            INSERT INTO preferences (user_id, favorite_genres, reading_level)
            VALUES ('test_user', 'Science Fiction', 'medium')
        """)
        
        conn.commit()
    
    yield

from database import db

def test_get_user_profile():
    profile = db.get_user_profile("test_user")
    assert profile["user_id"] == "test_user"
    assert "Science Fiction" in profile["favorite_genres"]

def test_update_preference():
    db.update_user_preference("test_user", "current_mood", "adventurous")
    profile = db.get_user_profile("test_user")
    assert profile["current_mood"] == "adventurous"

def test_search_books():
    books = db.search_books(genre="Science Fiction")
    assert len(books) == 1
    assert books[0]["title"] == "Test Sci-Fi Book"
    
    books2 = db.search_books(query="sweet")
    assert len(books2) == 1
    assert books2[0]["genre"] == "Romance"

def test_mark_as_read():
    db.mark_as_read("test_user", "B998", 4.0)
    history = db.get_reading_history("test_user")
    assert len(history) == 1
    assert history[0]["book_id"] == "B998"
    assert history[0]["rated"] == 4.0

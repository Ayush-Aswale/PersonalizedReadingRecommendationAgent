import json
from tools.user_tools import get_user_profile
from tools.book_tools import search_books
from tools.composite_tools import get_recommendation_candidates

def test_get_user_profile_tool():
    res = get_user_profile.invoke({"user_id": "test_user"})
    data = json.loads(res)
    assert data["favorite_genres"] == "Science Fiction"

def test_search_books_tool():
    res = search_books.invoke({"genre": "Romance"})
    data = json.loads(res)
    assert len(data) == 1
    assert data[0]["title"] == "Test Romance Book"

def test_composite_tool():
    res = get_recommendation_candidates.invoke({"user_id": "test_user", "query": "space", "genre": ""})
    data = json.loads(res)
    assert "candidates" in data
    # Sci-fi book should be top candidate
    assert len(data["candidates"]) > 0
    assert data["candidates"][0]["book_id"] == "B999"

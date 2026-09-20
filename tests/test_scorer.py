from recommender.scorer import compute_score, match_reading_level

def test_match_reading_level():
    assert match_reading_level("easy", "easy") == 1.0
    assert match_reading_level("medium", "easy") == 0.5
    assert match_reading_level("hard", "easy") == 0.0

def test_compute_score():
    book = {
        "book_id": "B999",
        "genre": "Science Fiction",
        "author": "Test Author",
        "avg_rating": 4.5,
        "reading_level": "medium",
        "pages": 350,
        "tags": "space, future"
    }
    user_profile = {
        "favorite_genres": "Science Fiction, Fantasy",
        "reading_level": "medium"
    }
    
    # Test 1: Basic fit
    res = compute_score(book, user_profile, {}, set(), [])
    assert res["score"] > 0
    assert any("favorite genre" in r for r in res["reasons"])
    
    # Test 2: Already read
    res2 = compute_score(book, user_profile, {}, {"B999"}, [])
    assert res2["score"] < 0
    assert "Already read" in res2["reasons"]
    
    # Test 3: Disliked genre adjustment
    res3 = compute_score(
        book, user_profile, {}, set(), 
        [{"sentiment": "dislike", "genre": "Science Fiction"}]
    )
    assert res3["score"] < res["score"] # Score should drop due to dislike penalty

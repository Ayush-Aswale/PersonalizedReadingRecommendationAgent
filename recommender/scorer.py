"""
Deterministic scoring function for book recommendations.
Computes a score for a book based on user profile, request, and history.
"""

from typing import Dict, Any, Optional
import math

# Configurable weights
WEIGHTS = {
    "genre_match": 3.0,
    "author_match": 2.5,
    "semantic_similarity": 2.0,
    "rating_score": 1.5,
    "reading_level_fit": 1.5,
    "length_fit": 1.0,
    "mood_fit": 1.0,
    "feedback_adjustment_liked": 1.0,
    "feedback_adjustment_disliked": -1.5,
    "already_read_penalty": -100.0,
}

def normalize_rating(rating: float) -> float:
    """Normalize a 1-5 rating to 0-1 range."""
    if not rating:
        return 0.0
    return min(max(rating / 5.0, 0.0), 1.0)

def match_reading_level(book_level: str, user_level: str, request_level: Optional[str] = None) -> float:
    """Returns a score between 0 and 1 based on reading level match."""
    target_level = request_level or user_level
    if not target_level or not book_level:
        return 0.5 # Neutral
        
    target_level = target_level.lower()
    book_level = book_level.lower()
    
    if book_level == target_level:
        return 1.0
    
    # Adjacent levels get partial score
    levels = ["easy", "medium", "hard"]
    try:
        book_idx = levels.index(book_level)
        target_idx = levels.index(target_level)
        diff = abs(book_idx - target_idx)
        if diff == 1:
            return 0.5
        return 0.0
    except ValueError:
        return 0.5

def match_length(book_pages: int, user_length: str, request_length: Optional[str] = None) -> float:
    """Returns a score between 0 and 1 based on book length match."""
    target_length = request_length or user_length
    if not target_length or not book_pages:
        return 0.5
        
    target_length = target_length.lower()
    
    # Length buckets (heuristic)
    if book_pages < 250:
        book_bucket = "short"
    elif book_pages > 450:
        book_bucket = "long"
    else:
        book_bucket = "medium"
        
    if book_bucket == target_length:
        return 1.0
        
    # Adjacent buckets
    buckets = ["short", "medium", "long"]
    try:
        book_idx = buckets.index(book_bucket)
        target_idx = buckets.index(target_length)
        diff = abs(book_idx - target_idx)
        if diff == 1:
            return 0.5
        return 0.0
    except ValueError:
        return 0.5

def compute_score(
    book: Dict[str, Any],
    user_profile: Dict[str, Any],
    request_hints: Dict[str, Any],
    read_history: set,
    feedback_history: list,
    semantic_score: float = 0.0
) -> Dict[str, Any]:
    """
    Computes deterministic score for a book.
    Returns dict with final score and breakdown of matched signals.
    """
    reasons = []
    total_score = 0.0
    
    # 1. Hard exclude if already read
    if book["book_id"] in read_history:
        return {"score": -100.0, "reasons": ["Already read"]}
        
    # 2. Genre Match
    fav_genres = [g.strip().lower() for g in user_profile.get("favorite_genres", "").split(",") if g.strip()]
    req_genre = request_hints.get("genre", "").lower()
    book_genre = str(book.get("genre", "")).lower()
    
    genre_score = 0.0
    if req_genre and req_genre in book_genre:
        genre_score = 1.0
        reasons.append(f"Matches requested genre '{req_genre}'")
    elif book_genre in fav_genres:
        genre_score = 0.8
        reasons.append(f"Matches favorite genre '{book.get('genre')}'")
        
    total_score += WEIGHTS["genre_match"] * genre_score
    
    # 3. Author Match
    fav_authors = [a.strip().lower() for a in user_profile.get("favorite_authors", "").split(",") if a.strip()]
    req_author = request_hints.get("author", "").lower()
    book_author = str(book.get("author", "")).lower()
    
    author_score = 0.0
    if req_author and req_author in book_author:
        author_score = 1.0
        reasons.append(f"Matches requested author '{req_author}'")
    elif book_author in fav_authors:
        author_score = 0.9
        reasons.append(f"By favorite author '{book.get('author')}'")
        
    total_score += WEIGHTS["author_match"] * author_score
    
    # 4. Semantic Similarity
    if semantic_score > 0:
        total_score += WEIGHTS["semantic_similarity"] * semantic_score
        if semantic_score > 0.6:
            reasons.append("Strongly fits request vibe/similarity")
            
    # 5. Rating Score
    rating = book.get("avg_rating", 0.0)
    rating_score = normalize_rating(rating)
    total_score += WEIGHTS["rating_score"] * rating_score
    if rating >= 4.5:
        reasons.append("Highly rated")
        
    # 6. Reading Level Fit
    level_score = match_reading_level(
        book.get("reading_level", ""),
        user_profile.get("reading_level", ""),
        request_hints.get("reading_level")
    )
    total_score += WEIGHTS["reading_level_fit"] * level_score
    if level_score == 1.0:
        reasons.append("Fits preferred reading level")
        
    # 7. Length Fit
    length_score = match_length(
        book.get("pages", 0),
        user_profile.get("preferred_length", ""),
        request_hints.get("length")
    )
    total_score += WEIGHTS["length_fit"] * length_score
    if length_score == 1.0:
        reasons.append("Fits preferred length")
        
    # 8. Mood Fit
    req_mood = request_hints.get("mood", "").lower()
    user_mood = user_profile.get("current_mood", "").lower()
    target_mood = req_mood or user_mood
    
    mood_score = 0.0
    if target_mood:
        book_tags = str(book.get("tags", "")).lower()
        if target_mood in book_tags or target_mood in book_genre:
            mood_score = 1.0
            reasons.append(f"Matches mood '{target_mood}'")
    total_score += WEIGHTS["mood_fit"] * mood_score
    
    # 9. Feedback Adjustment
    # If user liked a book with similar genre/tags, boost. If disliked, penalty.
    feedback_score = 0.0
    for fb in feedback_history:
        # Avoid penalizing explicitly requested genres
        if fb["sentiment"] == "dislike" and fb["genre"].lower() == book_genre and not req_genre:
            feedback_score += WEIGHTS["feedback_adjustment_disliked"]
        elif fb["sentiment"] == "like" and fb["genre"].lower() == book_genre:
            feedback_score += WEIGHTS["feedback_adjustment_liked"]
            
    # Cap feedback adjustment
    feedback_score = max(min(feedback_score, 2.0), -2.0)
    total_score += feedback_score
    if feedback_score > 0:
        reasons.append("Similar to books you liked")
    elif feedback_score < 0:
        reasons.append("Adjusted based on past dislikes")
        
    # Fallback reason
    if not reasons:
        reasons.append("Good general match")
        
    return {
        "score": round(total_score, 2),
        "reasons": reasons
    }

"""
Ranker module. Takes candidate books from various sources (SQL, Vector Store),
applies hard filters (read/disliked), calls the scorer, and returns top-N.
"""

from typing import List, Dict, Any, Tuple
from recommender.scorer import compute_score
from config.settings import settings

def rank_candidates(
    candidates: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    request_hints: Dict[str, Any],
    read_history: set,
    feedback_history: list,
    semantic_scores: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    Ranks candidates using deterministic scorer.
    - candidates: list of book dicts (from DB)
    - semantic_scores: dict mapping book_id -> float (0-1) similarity
    """
    semantic_scores = semantic_scores or {}
    
    scored_candidates = []
    
    # Deduplicate candidates by book_id
    seen_ids = set()
    unique_candidates = []
    for book in candidates:
        if book["book_id"] not in seen_ids:
            seen_ids.add(book["book_id"])
            unique_candidates.append(book)
            
    for book in unique_candidates:
        # Get semantic score if available
        sim_score = semantic_scores.get(book["book_id"], 0.0)
        
        # Compute score
        score_result = compute_score(
            book=book,
            user_profile=user_profile,
            request_hints=request_hints,
            read_history=read_history,
            feedback_history=feedback_history,
            semantic_score=sim_score
        )
        
        # Apply hard filter
        if score_result["score"] < 0:
            continue
            
        # Combine book info with score/reasons
        ranked_book = book.copy()
        ranked_book["score"] = score_result["score"]
        ranked_book["match_reasons"] = score_result["reasons"]
        
        scored_candidates.append(ranked_book)
        
    # Sort descending by score
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # Return Top-N
    return scored_candidates[:settings.MAX_RECOMMENDATIONS]

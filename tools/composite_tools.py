"""
Composite tools that orchestrate multiple steps (e.g., fetch profile, fetch history, search, rank)
in a single tool call to simplify the agent's job.
"""

import json
from typing import Optional
from langchain.tools import tool
from pydantic import BaseModel, Field

from database import db
from rag import vector_store
from recommender.ranker import rank_candidates

class GetRecommendationsInput(BaseModel):
    user_id: str = Field(..., description="The user's ID")
    query: str = Field(default="", description="Keyword or vibe description")
    genre: str = Field(default="", description="Target genre if known")

@tool("get_recommendation_candidates", args_schema=GetRecommendationsInput)
def get_recommendation_candidates(user_id: str, query: str = "", genre: str = "") -> str:
    """
    All-in-one tool that fetches the user's profile, history, searches for matching books,
    and returns a ranked list of candidates. Use this as the primary way to generate recommendations.
    Returns JSON.
    """
    try:
        # 1. Fetch user context
        profile = db.get_user_profile(user_id)
        history = db.get_reading_history(user_id)
        read_set = {h["book_id"] for h in history if h["status"] == "read"}
        feedback = db.get_feedback(user_id)
        
        # 2. Gather candidates
        candidates = []
        semantic_scores = {}
        
        # SQL search
        sql_books = db.search_books(query=query, genre=genre, limit=20)
        candidates.extend(sql_books)
        
        # Semantic search if query provided
        if query:
            sim_results = vector_store.find_similar_books(query, top_k=10)
            if sim_results:
                book_ids = [meta["book_id"] for meta, score in sim_results if "book_id" in meta]
                if book_ids:
                    sim_books = db.get_book_details_multi(book_ids)
                    candidates.extend(sim_books)
                    # map scores
                    for meta, score in sim_results:
                        if "book_id" in meta:
                            semantic_scores[meta["book_id"]] = score
        
        # 3. Rank
        request_hints = {"genre": genre, "mood": query} # simplistic mapping
        ranked = rank_candidates(
            candidates=candidates,
            user_profile=profile,
            request_hints=request_hints,
            read_history=read_set,
            feedback_history=feedback,
            semantic_scores=semantic_scores
        )
        
        if not ranked:
            return json.dumps({"message": "No matching books found.", "candidates": []})
            
        # Return only the essential info for the LLM to write explanations
        results_for_llm = []
        for r in ranked:
            results_for_llm.append({
                "book_id": r["book_id"],
                "title": r["title"],
                "author": r["author"],
                "genre": r["genre"],
                "pages": r["pages"],
                "avg_rating": r["avg_rating"],
                "description": r["description"],
                "score": r["score"],
                "match_reasons": r["match_reasons"]
            })
            
        return json.dumps({"candidates": results_for_llm})
        
    except Exception as e:
        return json.dumps({"error": str(e)})

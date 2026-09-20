"""
Book-related agent tools for searching and fetching details.
"""

from typing import List, Dict, Any, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import json

from database import db
from rag import vector_store

class SearchBooksInput(BaseModel):
    query: str = Field(default="", description="Keyword to search in title, description, or tags")
    genre: str = Field(default="", description="Genre to filter by")
    author: str = Field(default="", description="Author to filter by")
    max_length_pages: Optional[int] = Field(default=None, description="Maximum number of pages")
    reading_level: str = Field(default="", description="Target reading level: 'easy', 'medium', or 'hard'")

@tool("search_books", args_schema=SearchBooksInput)
def search_books(query: str = "", genre: str = "", author: str = "", max_length_pages: Optional[int] = None, reading_level: str = "") -> str:
    """
    Search the book catalog for books matching structured filters (genre, author, pages, etc.)
    Returns a JSON string of candidate book records.
    """
    try:
        books = db.search_books(
            query=query,
            genre=genre,
            author=author,
            max_length=max_length_pages,
            reading_level=reading_level,
            limit=15
        )
        return json.dumps(books)
    except Exception as e:
        return json.dumps({"error": str(e)})

class GetBookDetailsInput(BaseModel):
    book_id: str = Field(..., description="The unique book_id (e.g. 'B0001')")

@tool("get_book_details", args_schema=GetBookDetailsInput)
def get_book_details(book_id: str) -> str:
    """
    Fetch the full record for a single book by its ID.
    Returns JSON.
    """
    try:
        book = db.get_book_details(book_id)
        if book:
            return json.dumps(book)
        return json.dumps({"error": f"Book {book_id} not found."})
    except Exception as e:
        return json.dumps({"error": str(e)})

class FindSimilarBooksInput(BaseModel):
    query: str = Field(..., description="Text describing the desired book vibe, or a specific book title to match")
    top_k: int = Field(default=10, description="Number of results to return")

@tool("find_similar_books", args_schema=FindSimilarBooksInput)
def find_similar_books(query: str, top_k: int = 10) -> str:
    """
    Semantic similarity search to find books that match a 'vibe' or are similar to a given title.
    Uses vector embeddings. Returns JSON.
    """
    try:
        results = vector_store.find_similar_books(query, top_k=top_k)
        if not results:
            return json.dumps({"error": "Semantic search unavailable or no matches found."})
            
        # Results is a list of (metadata_dict, score)
        # Rehydrate full book details from DB for the top results
        book_ids = [meta["book_id"] for meta, score in results if "book_id" in meta]
        
        if not book_ids:
            return json.dumps({"error": "No book_ids found in vector store metadata."})
            
        books = db.get_book_details_multi(book_ids)
        
        # Attach semantic score to each returned book
        # Map book_id -> score
        score_map = {meta["book_id"]: score for meta, score in results if "book_id" in meta}
        for b in books:
            b["semantic_score"] = score_map.get(b["book_id"], 0.0)
            
        return json.dumps(books)
    except Exception as e:
        return json.dumps({"error": str(e)})

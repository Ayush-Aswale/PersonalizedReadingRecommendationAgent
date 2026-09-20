"""
User-related agent tools for reading preferences, history, and feedback.
"""

from typing import Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import json

from database import db

class GetUserProfileInput(BaseModel):
    user_id: str = Field(..., description="The user's ID")

@tool("get_user_profile", args_schema=GetUserProfileInput)
def get_user_profile(user_id: str) -> str:
    """
    Retrieve stored preferences and profile for the active user.
    Returns JSON.
    """
    try:
        profile = db.get_user_profile(user_id)
        return json.dumps(profile)
    except Exception as e:
        return json.dumps({"error": str(e)})

class GetReadingHistoryInput(BaseModel):
    user_id: str = Field(..., description="The user's ID")

@tool("get_reading_history", args_schema=GetReadingHistoryInput)
def get_reading_history(user_id: str) -> str:
    """
    Retrieve books the user has already marked as read.
    Returns JSON.
    """
    try:
        history = db.get_reading_history(user_id)
        return json.dumps(history)
    except Exception as e:
        return json.dumps({"error": str(e)})

class UpdateUserPreferenceInput(BaseModel):
    user_id: str = Field(..., description="The user's ID")
    field: str = Field(..., description="The preference field to update: 'favorite_genres', 'favorite_authors', 'reading_level', 'preferred_length', 'reading_goal', 'current_mood'")
    value: str = Field(..., description="The new value for the preference field")

@tool("update_user_preference", args_schema=UpdateUserPreferenceInput)
def update_user_preference(user_id: str, field: str, value: str) -> str:
    """
    Persist a new or changed preference the user expressed conversationally.
    Returns confirmation JSON.
    """
    try:
        db.update_user_preference(user_id, field, value)
        return json.dumps({"updated": True, "field": field, "value": value})
    except Exception as e:
        return json.dumps({"error": str(e)})

class RecordFeedbackInput(BaseModel):
    user_id: str = Field(..., description="The user's ID")
    book_id: str = Field(..., description="The ID of the book being reacted to")
    sentiment: str = Field(..., description="'like' or 'dislike'")
    reason: Optional[str] = Field(default=None, description="Optional reason for the sentiment")

@tool("record_feedback", args_schema=RecordFeedbackInput)
def record_feedback(user_id: str, book_id: str, sentiment: str, reason: Optional[str] = None) -> str:
    """
    Store like/dislike signal tied to a book.
    Returns confirmation JSON.
    """
    try:
        db.record_feedback(user_id, book_id, sentiment, reason)
        return json.dumps({"updated": True, "action": f"Recorded {sentiment} for {book_id}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

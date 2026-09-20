"""
Manages conversational memory for the agent.

In LangChain 1.x / LangGraph, memory is handled via MemorySaver checkpointer
and thread-based conversation IDs, not the old ConversationBufferWindowMemory.

We keep a simple in-memory message store per user as a sliding window,
and inject the history as messages into the agent invocation.
"""

from typing import Dict, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from config.settings import settings

# In-memory session store: user_id -> list of messages
_session_memories: Dict[str, List[BaseMessage]] = {}

def get_history(user_id: str) -> List[BaseMessage]:
    """Returns the conversation history for a user (sliding window)."""
    if user_id not in _session_memories:
        _session_memories[user_id] = []
    # Return the last k*2 messages (k exchanges = k user + k assistant)
    window = settings.CONVERSATION_MEMORY_WINDOW * 2
    return _session_memories[user_id][-window:]

def save_turn(user_id: str, user_message: str, agent_response: str):
    """Saves a user/agent exchange to the session memory."""
    if user_id not in _session_memories:
        _session_memories[user_id] = []
    _session_memories[user_id].append(HumanMessage(content=user_message))
    _session_memories[user_id].append(AIMessage(content=agent_response))
    
    # Trim to max window
    window = settings.CONVERSATION_MEMORY_WINDOW * 2
    if len(_session_memories[user_id]) > window:
        _session_memories[user_id] = _session_memories[user_id][-window:]

def clear_history(user_id: str):
    """Clears memory for a user."""
    _session_memories.pop(user_id, None)

"""
Agent Orchestrator.
Assembles the LangGraph ReAct agent, binds tools, handles memory, and executes turns.

Updated for LangChain 1.x / LangGraph API:
- Uses langgraph.prebuilt.create_react_agent instead of the removed
  langchain.agents.create_tool_calling_agent / AgentExecutor
- Uses message-based input/output format
- Conversation memory is a sliding-window message list
"""

import json
from typing import Dict, Any, List

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_agent

from config.settings import settings
from agent.prompts import SYSTEM_PROMPT
from tools.book_tools import search_books, get_book_details, find_similar_books
from tools.user_tools import get_user_profile, get_reading_history, update_user_preference, record_feedback
from tools.composite_tools import get_recommendation_candidates
from memory.conversation_memory import get_history, save_turn
from utils.logging_utils import get_agent_trace_callback

# Global agent graph instance
_agent_graph = None

def get_agent():
    """Initializes and returns the LangGraph ReAct agent."""
    global _agent_graph
    if _agent_graph is not None:
        return _agent_graph

    if not settings.has_groq_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    # 1. LLM
    llm = ChatGroq(
        model_name=settings.GROQ_MODEL_NAME,
        api_key=settings.GROQ_API_KEY,
        temperature=0.2,
        max_tokens=1024,
    )
    
    # 2. Tools
    tools = [
        search_books,
        get_book_details,
        find_similar_books,
        get_user_profile,
        get_reading_history,
        update_user_preference,
        record_feedback,
        get_recommendation_candidates
    ]
    
    # 3. Create agent (LangChain 1.x API)
    # create_agent takes system_prompt as a string
    _agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    
    return _agent_graph

def run_turn(user_id: str, message: str) -> Dict[str, Any]:
    """
    Executes a single conversational turn for the given user.
    Returns a dict with 'response' (text), 'trace' (list of tool calls).
    """
    if not message.strip():
        return {"response": "Please enter a valid message.", "trace": []}
        
    try:
        agent = get_agent()
    except ValueError as e:
        return {"response": f"Error: {e}. Please check .env configuration.", "trace": []}
        
    # Build message list: history + current user message
    history = get_history(user_id)
    messages = list(history) + [HumanMessage(content=message)]
    
    # Callback handler to capture tool trace
    trace_callback = get_agent_trace_callback()
    
    try:
        # LangGraph agent expects {"messages": [...]} and returns {"messages": [...]}
        result = agent.invoke(
            {"messages": messages},
            config={
                "callbacks": [trace_callback],
                "recursion_limit": settings.MAX_AGENT_ITERATIONS * 2 + 2,
            }
        )
        
        # Extract the final AI message from the result
        result_messages = result.get("messages", [])
        
        # Find the last AIMessage that isn't a tool call
        output_text = "I couldn't generate a response."
        for msg in reversed(result_messages):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                output_text = msg.content
                break
        
        # Save to conversation memory
        save_turn(user_id, message, output_text)
        trace_data = trace_callback.get_trace()
        recommendations = []
        
        # Extract structured recommendations from trace
        for t in trace_data:
            if t.get("tool") == "get_recommendation_candidates" and "data" in t:
                data = t["data"]
                if isinstance(data, dict) and "candidates" in data:
                    recommendations = data["candidates"]
                    break
        
        return {
            "response": output_text,
            "recommendations": recommendations,
            "trace": trace_data
        }
    except Exception as e:
        print(f"Agent error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": "I encountered an error while processing your request. Please try again.",
            "trace": trace_callback.get_trace() + [{"tool": "Error", "result": str(e)}]
        }

import pytest
import os

# We skip this test if we don't have a GROQ key configured locally, 
# as it makes an actual LLM call.
@pytest.mark.skipif(not os.environ.get("GROQ_API_KEY"), reason="Requires GROQ API key")
def test_agent_integration():
    from agent.orchestrator import run_turn
    
    # We ask a simple question that should trigger a tool call
    result = run_turn("test_user", "My user_id is test_user. I want a space opera science fiction book.")
    
    assert "response" in result
    assert "trace" in result
    
    # The trace should show it tried to use get_recommendation_candidates or search_books
    tools_used = [t["tool"] for t in result["trace"]]
    assert len(tools_used) > 0
    
    # The new architecture returns structured recommendations
    assert "recommendations" in result
    
    # We should have candidates
    assert len(result["recommendations"]) > 0, f"No recommendations found. Trace: {result['trace']}"
    
    # The response or recommendations should mention the test book (LLM may use unicode hyphens)
    response_normalized = result["response"].replace("\u2011", "-")  # non-breaking hyphen
    book_titles = [b.get("title", "") for b in result["recommendations"]]
    
    found_in_text = "Test Sci-Fi Book" in response_normalized or "Test Sci" in result["response"]
    found_in_recs = any("Test Sci-Fi Book" in t for t in book_titles)
    
    assert found_in_text or found_in_recs, f"Book not found in text ({response_normalized}) or recommendations ({book_titles})"

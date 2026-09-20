"""
Logging utilities, specifically the Agent Trace Callback handler.
This powers the Agent Activity panel in the UI.

Updated for LangChain 1.x / LangGraph callback interface.
"""

from typing import Dict, Any, List, Optional, Sequence
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from uuid import UUID


class AgentTraceCallbackHandler(BaseCallbackHandler):
    """
    Captures tool execution events during an agent's reasoning pass.
    Compatible with LangChain 1.x callback interface.
    """
    def __init__(self):
        self.trace = []
        
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when a tool starts running."""
        tool_name = serialized.get("name", "unknown_tool")
        # Truncate input for display
        display_input = str(input_str)
        if len(display_input) > 200:
            display_input = display_input[:197] + "..."
        self.trace.append({
            "tool": tool_name,
            "input": display_input,
            "status": "started"
        })
        
    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when a tool ends running."""
        if self.trace:
            last_action = self.trace[-1]
            last_action["status"] = "finished"
            
            # Extract the actual string content if output is a ToolMessage
            if hasattr(output, "content"):
                output_str = str(output.content)
            else:
                output_str = str(output)
            
            # Attempt to parse structured JSON from tool output (e.g. get_recommendation_candidates)
            try:
                import json
                parsed = json.loads(output_str)
                last_action["data"] = parsed
            except Exception:
                pass
            
            # Truncate output if it's too long for the summary display
            if len(output_str) > 200:
                last_action["result"] = output_str[:197] + "..."
            else:
                last_action["result"] = output_str
                
    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when a tool errors."""
        if self.trace:
            last_action = self.trace[-1]
            last_action["status"] = "error"
            last_action["result"] = str(error)

    def get_trace(self) -> List[Dict[str, Any]]:
        return self.trace


def get_agent_trace_callback() -> AgentTraceCallbackHandler:
    return AgentTraceCallbackHandler()

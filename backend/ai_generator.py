"""
AI Generator module for Claude API interactions with sequential tool calling support.

This module provides the AIGenerator class that handles communication with Anthropic's
Claude API, including support for sequential tool calling where Claude can make up to
2 tool calls in separate API rounds.
"""
from typing import Dict, Any, Optional, List, Tuple
import anthropic


class AIGenerator:
    """Handles interactions with Anthropic's Claude API with sequential tool calling."""

    MAX_TOOL_ROUNDS = 2
    DEFAULT_TEMPERATURE = 0
    DEFAULT_MAX_TOKENS = 800

    SYSTEM_PROMPT = """You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool for questions about specific course content
- You may make up to 2 sequential searches per query for complex questions
- For comparison questions, search each topic separately to gather complete information
- For multi-part questions, use multiple searches to address each part thoroughly
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly

Response Protocol:
- Provide direct, concise answers based on search results
- Be educational and use examples when helpful
- Cite course names and lesson numbers when referencing specific content

All responses must be:
1. Brief and focused
2. Educational
3. Clear and accessible
4. Example-supported when helpful"""

    def __init__(self, api_key: str, model: str):
        """
        Initialize the AI generator.

        Args:
            api_key: Anthropic API key
            model: Model identifier (e.g., "claude-3-5-sonnet-20241022")
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.temperature = self.DEFAULT_TEMPERATURE
        self.max_tokens = self.DEFAULT_MAX_TOKENS

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        tool_manager: Optional[Any] = None
    ) -> str:
        """
        Generate AI response with sequential tool calling support.

        This method implements a loop-based approach where Claude can make up to
        MAX_TOOL_ROUNDS sequential tool calls, allowing it to reason about previous
        results before deciding on next actions.

        Args:
            query: The user's question
            conversation_history: Previous conversation context (formatted string)
            tools: Available tools for Claude to use
            tool_manager: Manager to execute tool calls (must have execute_tool method)

        Returns:
            Generated response string
        """
        # Build system content with optional history
        system_content = self._build_system_content(conversation_history)

        # Initialize message chain
        messages = [{"role": "user", "content": query}]

        # Track rounds for termination
        current_round = 0

        # Main loop for sequential tool calling
        while current_round <= self.MAX_TOOL_ROUNDS:
            # Determine if tools should be included this round
            # Tools available for rounds 0 and 1, excluded for round 2+ to force final response
            include_tools = tools is not None and current_round < self.MAX_TOOL_ROUNDS

            # Make API call
            response = self._make_api_call(
                messages=messages,
                system_content=system_content,
                tools=tools if include_tools else None
            )

            # TERMINATION CONDITION 1: Claude provided final text response
            if response.stop_reason != "tool_use":
                return self._extract_text(response)

            # TERMINATION CONDITION 2: Max rounds reached
            if current_round >= self.MAX_TOOL_ROUNDS:
                # Force final response without tools
                return self._make_final_response(messages, system_content)

            # Execute tools and get results
            tool_results, execution_error = self._execute_tools(response, tool_manager)

            # TERMINATION CONDITION 3: Critical tool execution error (no results produced)
            if execution_error and not tool_results:
                # Build error message and try to get a response anyway
                return self._handle_tool_error(messages, response, execution_error, system_content)

            # Update message chain for next round
            messages = self._build_tool_result_messages(messages, response, tool_results)

            # Increment round counter
            current_round += 1

        # Fallback: force final response (should not normally reach here)
        return self._make_final_response(messages, system_content)

    def _build_system_content(self, conversation_history: Optional[str]) -> str:
        """
        Build system content with optional conversation history.

        Args:
            conversation_history: Previous conversation context

        Returns:
            Complete system prompt string
        """
        content = self.SYSTEM_PROMPT
        if conversation_history:
            content += f"\n\nPrevious conversation:\n{conversation_history}"
        return content

    def _make_api_call(
        self,
        messages: List[Dict],
        system_content: str,
        tools: Optional[List[Dict]] = None
    ) -> Any:
        """
        Execute API call with consistent parameters.

        Args:
            messages: Conversation message chain
            system_content: System prompt content
            tools: Optional tools to make available

        Returns:
            API response object
        """
        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_content,
            "messages": messages
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = {"type": "auto"}

        return self.client.messages.create(**params)

    def _extract_text(self, response: Any) -> str:
        """
        Extract text content from API response.

        Args:
            response: API response object

        Returns:
            Extracted text string or empty string if no text found
        """
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        return ""

    def _execute_tools(
        self,
        response: Any,
        tool_manager: Optional[Any]
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Execute all tool calls in the response.

        Args:
            response: API response containing tool_use blocks
            tool_manager: Manager with execute_tool method

        Returns:
            Tuple of (tool_results list, error message or None)
        """
        if tool_manager is None:
            return [], "No tool_manager provided"

        tool_results = []
        critical_error = None

        for block in response.content:
            if block.type == "tool_use":
                try:
                    result = tool_manager.execute_tool(
                        tool_name=block.name,
                        **block.input
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
                except Exception as e:
                    error_msg = f"Error executing {block.name}: {str(e)}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": error_msg,
                        "is_error": True
                    })
                    # Track error but continue executing other tools
                    critical_error = error_msg

        # Only return critical error if NO results were produced
        return tool_results, critical_error if not tool_results else None

    def _build_tool_result_messages(
        self,
        messages: List[Dict],
        response: Any,
        tool_results: List[Dict]
    ) -> List[Dict]:
        """
        Append assistant's tool_use and user's tool_result to message chain.

        This preserves the conversation context for subsequent rounds, allowing
        Claude to see what tools it called and what results it received.

        Args:
            messages: Current message chain
            response: API response containing tool_use blocks
            tool_results: List of tool_result dictionaries

        Returns:
            Updated message chain
        """
        # Build assistant content blocks from response
        assistant_content = []
        for block in response.content:
            if block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        # Append assistant message with tool_use blocks
        messages.append({
            "role": "assistant",
            "content": assistant_content
        })

        # Append user message with tool_results
        messages.append({
            "role": "user",
            "content": tool_results
        })

        return messages

    def _make_final_response(
        self,
        messages: List[Dict],
        system_content: str
    ) -> str:
        """
        Make final API call without tools to force text response.

        Called when max rounds are reached to ensure Claude provides
        a final text response rather than requesting more tool calls.

        Args:
            messages: Current message chain
            system_content: System prompt content

        Returns:
            Final text response
        """
        response = self._make_api_call(
            messages=messages,
            system_content=system_content,
            tools=None
        )
        return self._extract_text(response)

    def _handle_tool_error(
        self,
        messages: List[Dict],
        response: Any,
        error: str,
        system_content: str
    ) -> str:
        """
        Handle critical tool execution errors gracefully.

        When tool execution fails completely (no results produced), this method
        attempts to get a response from Claude anyway by including the error
        as a tool_result.

        Args:
            messages: Current message chain
            response: API response that contained failed tool calls
            error: Error message
            system_content: System prompt content

        Returns:
            Response string (either from Claude or fallback error message)
        """
        # Build error tool_result
        tool_result = {
            "type": "tool_result",
            "tool_use_id": response.content[0].id if response.content else "unknown",
            "content": f"Tool execution failed: {error}",
            "is_error": True
        }

        # Update messages with error
        messages = self._build_tool_result_messages(messages, response, [tool_result])

        # Try to get a response anyway
        try:
            return self._make_final_response(messages, system_content)
        except Exception:
            return f"I encountered an error while searching: {error}"
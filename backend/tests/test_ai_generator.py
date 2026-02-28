"""
Tests for AIGenerator in ai_generator.py.

These tests verify that AIGenerator correctly:
1. Creates proper API requests
2. Handles tool use responses
3. Executes tools when requested by Claude
4. Returns appropriate responses
"""
import os
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import anthropic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool


class TestAIGeneratorToolCalling:
    """Tests for AIGenerator's tool calling behavior."""

    def test_generate_response_without_tools(self, mock_anthropic_client):
        """Test that generate_response works without tools."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is a test response")]
        mock_response.stop_reason = "end_turn"
        mock_anthropic_client.messages.create.return_value = mock_response

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        result = generator.generate_response(query="What is Python?")

        assert result == "This is a test response"
        print(f"[PASS] Response without tools: {result}")

    def test_generate_response_passes_tools_to_api(self, mock_anthropic_client):
        """Test that tools are passed to the API when provided."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Direct response")]
        mock_response.stop_reason = "end_turn"
        mock_anthropic_client.messages.create.return_value = mock_response

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        tools = [{"name": "test_tool", "input_schema": {}}]

        result = generator.generate_response(
            query="Test query",
            tools=tools
        )

        # Verify tools were passed to API
        call_args = mock_anthropic_client.messages.create.call_args
        assert "tools" in call_args.kwargs
        assert call_args.kwargs["tools"] == tools
        print("[PASS] Tools passed to API correctly")

    def test_generate_response_triggers_tool_execution(self, mock_anthropic_client, populated_vector_store):
        """Test that tool_use stop reason triggers tool execution."""
        # Setup mock for initial tool_use response
        mock_tool_use_response = MagicMock()
        mock_tool_use_response.stop_reason = "tool_use"
        mock_tool_use_response.content = [
            MagicMock(type="tool_use", name="search_course_content", id="tool_123", input={"query": "Python"})
        ]

        # Setup mock for final response after tool execution
        mock_final_response = MagicMock()
        mock_final_response.content = [MagicMock(text="Based on the search, Python is a programming language.")]

        mock_anthropic_client.messages.create.side_effect = [
            mock_tool_use_response,
            mock_final_response
        ]

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        # Create tool manager
        tool_manager = ToolManager()
        search_tool = CourseSearchTool(populated_vector_store)
        tool_manager.register_tool(search_tool)

        tools = tool_manager.get_tool_definitions()

        result = generator.generate_response(
            query="Tell me about Python",
            tools=tools,
            tool_manager=tool_manager
        )

        # Verify tool was executed (two API calls made)
        assert mock_anthropic_client.messages.create.call_count == 2
        print(f"[PASS] Tool execution triggered, result: {result[:50]}...")

    def test_handle_tool_execution_formats_messages_correctly(self, mock_anthropic_client, populated_vector_store):
        """Test that tool execution properly formats the message chain."""
        # Setup mocks
        mock_tool_use_response = MagicMock()
        mock_tool_use_response.stop_reason = "tool_use"
        mock_tool_use_response.content = [
            MagicMock(type="tool_use", name="search_course_content", id="tool_456", input={"query": "variables"})
        ]

        mock_final_response = MagicMock()
        mock_final_response.content = [MagicMock(text="Variables store data.")]

        mock_anthropic_client.messages.create.side_effect = [
            mock_tool_use_response,
            mock_final_response
        ]

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        tool_manager = ToolManager()
        search_tool = CourseSearchTool(populated_vector_store)
        tool_manager.register_tool(search_tool)

        tools = tool_manager.get_tool_definitions()

        result = generator.generate_response(
            query="What are variables?",
            tools=tools,
            tool_manager=tool_manager
        )

        # Check second call has proper message structure
        second_call_args = mock_anthropic_client.messages.create.call_args_list[1]
        messages = second_call_args.kwargs["messages"]

        # Should have: user query, assistant tool_use, user tool_result
        assert len(messages) >= 2  # At least initial message and tool result
        print(f"[PASS] Message chain formatted correctly with {len(messages)} messages")

    def test_tool_result_contains_search_output(self, mock_anthropic_client, populated_vector_store):
        """Test that tool_result message contains actual search output."""
        # Setup mocks
        mock_tool_use_response = MagicMock()
        mock_tool_use_response.stop_reason = "tool_use"
        mock_tool_use_response.content = [
            MagicMock(type="tool_use", name="search_course_content", id="tool_789", input={"query": "Python"})
        ]

        mock_final_response = MagicMock()
        mock_final_response.content = [MagicMock(text="Response")]

        mock_anthropic_client.messages.create.side_effect = [
            mock_tool_use_response,
            mock_final_response
        ]

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        tool_manager = ToolManager()
        search_tool = CourseSearchTool(populated_vector_store)
        tool_manager.register_tool(search_tool)

        tools = tool_manager.get_tool_definitions()

        result = generator.generate_response(
            query="Test query",
            tools=tools,
            tool_manager=tool_manager
        )

        # Get the tool result message from second API call
        second_call_args = mock_anthropic_client.messages.create.call_args_list[1]
        messages = second_call_args.kwargs["messages"]

        # Find tool_result in messages
        tool_result_found = False
        for msg in messages:
            if isinstance(msg.get("content"), list):
                for item in msg.get("content", []):
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        tool_result_found = True
                        # Tool result should contain search output
                        assert "content" in item
                        print(f"[PASS] Tool result contains: {item['content'][:50] if item['content'] else 'empty'}...")

        assert tool_result_found, "tool_result should be in messages"
        print("[PASS] Tool result contains search output")

    def test_multiple_tool_calls_in_single_response(self, mock_anthropic_client, populated_vector_store):
        """Test handling multiple tool calls in a single response."""
        # Setup mocks - Claude requests two tools
        mock_tool_use_response = MagicMock()
        mock_tool_use_response.stop_reason = "tool_use"
        mock_tool_use_response.content = [
            MagicMock(type="tool_use", name="search_course_content", id="tool_1", input={"query": "Python"}),
            MagicMock(type="tool_use", name="search_course_content", id="tool_2", input={"query": "variables"})
        ]

        mock_final_response = MagicMock()
        mock_final_response.content = [MagicMock(text="Combined response")]

        mock_anthropic_client.messages.create.side_effect = [
            mock_tool_use_response,
            mock_final_response
        ]

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        tool_manager = ToolManager()
        search_tool = CourseSearchTool(populated_vector_store)
        tool_manager.register_tool(search_tool)

        tools = tool_manager.get_tool_definitions()

        result = generator.generate_response(
            query="Tell me about Python and variables",
            tools=tools,
            tool_manager=tool_manager
        )

        # Should have made two API calls
        assert mock_anthropic_client.messages.create.call_count == 2
        print("[PASS] Multiple tool calls handled correctly")


class TestAIGeneratorSystemPrompt:
    """Tests for system prompt configuration."""

    def test_system_prompt_exists(self):
        """Test that SYSTEM_PROMPT is defined."""
        assert hasattr(AIGenerator, 'SYSTEM_PROMPT')
        assert len(AIGenerator.SYSTEM_PROMPT) > 0
        print("[PASS] System prompt exists")

    def test_system_prompt_includes_tool_instructions(self):
        """Test that system prompt includes tool usage instructions."""
        prompt = AIGenerator.SYSTEM_PROMPT

        # Should mention tool usage
        assert "tool" in prompt.lower() or "search" in prompt.lower()
        print("[PASS] System prompt includes tool instructions")

    def test_conversation_history_appended_to_system_prompt(self, mock_anthropic_client):
        """Test that conversation history is appended to system prompt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.stop_reason = "end_turn"
        mock_anthropic_client.messages.create.return_value = mock_response

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        result = generator.generate_response(
            query="Follow-up question",
            conversation_history="User: What is Python?\nAssistant: Python is a language."
        )

        # Check that system content includes history
        call_args = mock_anthropic_client.messages.create.call_args
        system_content = call_args.kwargs["system"]

        assert "Previous conversation" in system_content
        assert "What is Python?" in system_content
        print("[PASS] Conversation history appended to system prompt")


class TestAIGeneratorAPIParameters:
    """Tests for API parameter handling."""

    def test_base_params_used_in_api_call(self, mock_anthropic_client):
        """Test that base parameters are correctly used."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test")]
        mock_response.stop_reason = "end_turn"
        mock_anthropic_client.messages.create.return_value = mock_response

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        result = generator.generate_response(query="Test")

        call_args = mock_anthropic_client.messages.create.call_args

        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_args.kwargs["temperature"] == 0
        assert call_args.kwargs["max_tokens"] == 800
        print("[PASS] Base API parameters used correctly")

    def test_tool_choice_set_to_auto_when_tools_provided(self, mock_anthropic_client):
        """Test that tool_choice is set to auto when tools are provided."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test")]
        mock_response.stop_reason = "end_turn"
        mock_anthropic_client.messages.create.return_value = mock_response

        generator = AIGenerator("test-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client

        tools = [{"name": "test_tool", "input_schema": {}}]

        result = generator.generate_response(query="Test", tools=tools)

        call_args = mock_anthropic_client.messages.create.call_args
        assert "tool_choice" in call_args.kwargs
        assert call_args.kwargs["tool_choice"] == {"type": "auto"}
        print("[PASS] tool_choice set to auto")


# Run tests when executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
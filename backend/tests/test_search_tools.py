"""
Tests for CourseSearchTool in search_tools.py.

These tests verify that the CourseSearchTool correctly:
1. Executes searches against the vector store
2. Handles various parameter combinations
3. Returns properly formatted results
4. Handles errors gracefully
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


class TestCourseSearchToolExecute:
    """Tests for CourseSearchTool.execute() method."""

    def test_execute_with_query_only_returns_results(self, populated_vector_store):
        """Test that execute with just a query returns results from the vector store."""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="Python programming")

        # Should return formatted results
        assert result is not None
        assert isinstance(result, str)
        assert "Introduction to Python" in result
        print(f"[PASS] Query returned results: {result[:100]}...")

    def test_execute_with_course_name_filter(self, populated_vector_store):
        """Test that execute with course_name filter works correctly."""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="variables", course_name="Python")

        # Should find the course and return results
        assert result is not None
        assert isinstance(result, str)
        print(f"[PASS] Course filter query returned: {result[:100]}...")

    def test_execute_with_lesson_number_filter(self, populated_vector_store):
        """Test that execute with lesson_number filter works correctly."""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="data types", lesson_number=2)

        assert result is not None
        assert isinstance(result, str)
        print(f"[PASS] Lesson filter query returned: {result[:100]}...")

    def test_execute_with_all_filters(self, populated_vector_store):
        """Test execute with all parameters specified."""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(
            query="variables", course_name="Introduction to Python", lesson_number=2
        )

        assert result is not None
        assert isinstance(result, str)
        print(f"[PASS] All filters query returned: {result[:100]}...")

    def test_execute_returns_no_results_message_for_empty_query(
        self, mock_vector_store
    ):
        """Test that empty results return appropriate message."""
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="nonexistent content xyz123")

        assert "No relevant content found" in result
        print(f"[PASS] Empty results returned appropriate message: {result}")

    def test_execute_handles_nonexistent_course(self, populated_vector_store):
        """Test that nonexistent course name returns appropriate error."""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="test", course_name="Nonexistent Course XYZ")

        assert "No course found matching" in result
        print(f"[PASS] Nonexistent course handled: {result}")

    def test_execute_populates_last_sources(self, populated_vector_store):
        """Test that execute populates last_sources for UI display."""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="Python")

        # Check that sources were populated
        assert len(tool.last_sources) > 0
        source = tool.last_sources[0]
        assert "course_title" in source
        assert "display_text" in source
        print(f"[PASS] Sources populated: {tool.last_sources}")

    def test_execute_stores_lesson_links_in_sources(self, populated_vector_store):
        """Test that lesson links are included in sources when available."""
        tool = CourseSearchTool(populated_vector_store)

        result = tool.execute(query="Python")

        # Check sources have lesson_link field
        assert len(tool.last_sources) > 0
        source = tool.last_sources[0]
        assert "lesson_link" in source
        print(f"[PASS] Lesson link in sources: {source.get('lesson_link')}")

    def test_get_tool_definition_structure(self, populated_vector_store):
        """Test that get_tool_definition returns correct Anthropic format."""
        tool = CourseSearchTool(populated_vector_store)

        definition = tool.get_tool_definition()

        assert definition["name"] == "search_course_content"
        assert "input_schema" in definition
        assert "properties" in definition["input_schema"]
        assert "query" in definition["input_schema"]["properties"]
        assert "course_name" in definition["input_schema"]["properties"]
        assert "lesson_number" in definition["input_schema"]["properties"]
        assert definition["input_schema"]["required"] == ["query"]
        print("[PASS] Tool definition structure is correct")


class TestToolManager:
    """Tests for ToolManager class."""

    def test_register_tool(self, populated_vector_store):
        """Test that tools can be registered successfully."""
        manager = ToolManager()
        tool = CourseSearchTool(populated_vector_store)

        manager.register_tool(tool)

        assert "search_course_content" in manager.tools
        print("[PASS] Tool registered successfully")

    def test_get_tool_definitions(self, populated_vector_store):
        """Test getting all tool definitions."""
        manager = ToolManager()
        tool = CourseSearchTool(populated_vector_store)
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()

        assert len(definitions) == 1
        assert definitions[0]["name"] == "search_course_content"
        print("[PASS] Tool definitions retrieved correctly")

    def test_execute_tool_by_name(self, populated_vector_store):
        """Test executing a tool by name."""
        manager = ToolManager()
        tool = CourseSearchTool(populated_vector_store)
        manager.register_tool(tool)

        result = manager.execute_tool("search_course_content", query="Python")

        assert result is not None
        assert isinstance(result, str)
        print(f"[PASS] Tool executed by name: {result[:50]}...")

    def test_execute_nonexistent_tool_returns_error(self):
        """Test that executing nonexistent tool returns error message."""
        manager = ToolManager()

        result = manager.execute_tool("nonexistent_tool", query="test")

        assert "not found" in result
        print(f"[PASS] Nonexistent tool handled: {result}")

    def test_get_last_sources_from_tool(self, populated_vector_store):
        """Test retrieving last sources from registered tools."""
        manager = ToolManager()
        tool = CourseSearchTool(populated_vector_store)
        manager.register_tool(tool)

        # Execute a search
        manager.execute_tool("search_course_content", query="Python")

        # Get sources
        sources = manager.get_last_sources()

        assert len(sources) > 0
        print(f"[PASS] Sources retrieved from manager: {sources}")

    def test_reset_sources(self, populated_vector_store):
        """Test that reset_sources clears all tool sources."""
        manager = ToolManager()
        tool = CourseSearchTool(populated_vector_store)
        manager.register_tool(tool)

        # Execute a search
        manager.execute_tool("search_course_content", query="Python")

        # Verify sources exist
        assert len(manager.get_last_sources()) > 0

        # Reset sources
        manager.reset_sources()

        # Verify sources are cleared
        assert len(manager.get_last_sources()) == 0
        print("[PASS] Sources reset successfully")


class TestSearchResultsDataClass:
    """Tests for SearchResults dataclass."""

    def test_from_chroma_creates_valid_results(self):
        """Test creating SearchResults from ChromaDB output."""
        chroma_output = {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"key": "value"}, {"key2": "value2"}]],
            "distances": [[0.1, 0.2]],
        }

        results = SearchResults.from_chroma(chroma_output)

        assert results.documents == ["doc1", "doc2"]
        assert results.metadata == [{"key": "value"}, {"key2": "value2"}]
        assert results.distances == [0.1, 0.2]
        assert results.error is None
        print("[PASS] SearchResults created from ChromaDB output")

    def test_empty_creates_error_results(self):
        """Test creating empty SearchResults with error."""
        results = SearchResults.empty("Test error message")

        assert results.documents == []
        assert results.metadata == []
        assert results.error == "Test error message"
        print("[PASS] Empty SearchResults created with error")

    def test_is_empty_detects_empty_results(self):
        """Test is_empty method."""
        empty_results = SearchResults(documents=[], metadata=[], distances=[])
        non_empty_results = SearchResults(
            documents=["doc"], metadata=[{}], distances=[0.1]
        )

        assert empty_results.is_empty() is True
        assert non_empty_results.is_empty() is False
        print("[PASS] is_empty works correctly")


# Run tests when executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

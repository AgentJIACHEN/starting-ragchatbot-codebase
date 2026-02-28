"""
Diagnostic tests for the VectorStore to identify the 'query failed' issue.
These tests focus on the actual ChromaDB data and vector store operations.
"""
import os
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector_store import VectorStore, SearchResults
from models import Course, CourseChunk


class TestVectorStoreCourseResolution:
    """Tests for course name resolution in VectorStore."""

    def test_resolve_course_name_finds_exact_match(self, populated_vector_store):
        """Test that exact course name matches are found."""
        result = populated_vector_store._resolve_course_name("Introduction to Python")

        assert result is not None
        assert result == "Introduction to Python"
        print(f"[PASS] Exact match found: {result}")

    def test_resolve_course_name_finds_partial_match(self, populated_vector_store):
        """Test that partial course name matches are found."""
        result = populated_vector_store._resolve_course_name("Python")

        assert result is not None
        assert "Python" in result
        print(f"[PASS] Partial match found: {result}")

    def test_resolve_course_name_returns_none_for_nonexistent(self, populated_vector_store):
        """Test that nonexistent course name returns None."""
        # This is the critical test - it should return None for truly nonexistent courses
        result = populated_vector_store._resolve_course_name("Completely Made Up Course XYZ123")

        # If this returns a result, there's a bug in _resolve_course_name
        if result is not None:
            print(f"[FAIL] _resolve_course_name returned '{result}' for nonexistent course - this is the bug!")
            print("       It should return None when no course matches.")
        else:
            print(f"[PASS] Nonexistent course returned None as expected")
        assert result is None, f"Expected None but got '{result}'"

    def test_resolve_course_name_with_empty_catalog(self, mock_vector_store):
        """Test resolution with empty course catalog."""
        result = mock_vector_store._resolve_course_name("Any Course")

        assert result is None
        print("[PASS] Empty catalog returns None")


class TestVectorStoreSearch:
    """Tests for VectorStore.search() method."""

    def test_search_without_filters_returns_results(self, populated_vector_store):
        """Test basic search without filters."""
        results = populated_vector_store.search(query="Python programming")

        assert not results.is_empty()
        assert len(results.documents) > 0
        print(f"[PASS] Basic search returned {len(results.documents)} results")

    def test_search_with_valid_course_filter(self, populated_vector_store):
        """Test search with a valid course name filter."""
        results = populated_vector_store.search(
            query="variables",
            course_name="Introduction to Python"
        )

        # Should not have error
        assert results.error is None
        print(f"[PASS] Search with valid course filter: {len(results.documents)} results, error={results.error}")

    def test_search_with_nonexistent_course_returns_error(self, populated_vector_store):
        """Test that searching with nonexistent course returns error."""
        results = populated_vector_store.search(
            query="test",
            course_name="Nonexistent Course XYZ"
        )

        # THIS IS THE KEY TEST - should return error about course not found
        if results.error:
            print(f"[PASS] Nonexistent course returned error: {results.error}")
        else:
            print(f"[FAIL] Nonexistent course did NOT return error!")
            print(f"       Results: {results.documents[:100] if results.documents else 'empty'}")
            print("       This indicates _resolve_course_name or search is not working correctly.")

        assert results.error is not None, "Expected error for nonexistent course but got none"
        assert "No course found" in results.error

    def test_search_with_lesson_filter_only(self, populated_vector_store):
        """Test search with only lesson number filter."""
        results = populated_vector_store.search(
            query="Python",
            lesson_number=1
        )

        # Lesson-only filter should work
        assert results.error is None
        print(f"[PASS] Lesson-only filter: {len(results.documents)} results")


class TestVectorStoreDataIntegrity:
    """Tests to verify data is stored correctly in ChromaDB."""

    def test_course_catalog_has_data(self, populated_vector_store):
        """Test that course catalog contains the expected course."""
        # Get all items from catalog
        all_items = populated_vector_store.course_catalog.get()

        print(f"[INFO] Course catalog IDs: {all_items.get('ids', [])}")
        print(f"[INFO] Course catalog count: {len(all_items.get('ids', []))}")

        assert len(all_items.get('ids', [])) > 0, "Course catalog should have items"
        print("[PASS] Course catalog has data")

    def test_course_content_has_data(self, populated_vector_store):
        """Test that course content contains chunks."""
        # Get count from content collection
        all_items = populated_vector_store.course_content.get()

        print(f"[INFO] Course content count: {len(all_items.get('ids', []))}")

        assert len(all_items.get('ids', [])) > 0, "Course content should have chunks"
        print("[PASS] Course content has data")

    def test_course_metadata_stored_correctly(self, populated_vector_store):
        """Test that course metadata is stored with correct structure."""
        results = populated_vector_store.course_catalog.get()

        if results.get('metadatas'):
            for meta in results['metadatas']:
                assert 'title' in meta, "Metadata should have 'title'"
                print(f"[INFO] Course metadata: title={meta.get('title')}")
                print("[PASS] Course metadata structure is correct")
        else:
            print("[WARN] No metadata found in catalog")

    def test_content_chunks_have_correct_metadata(self, populated_vector_store):
        """Test that content chunks have course_title metadata."""
        results = populated_vector_store.course_content.get(limit=5)

        if results.get('metadatas'):
            for meta in results['metadatas'][:3]:
                assert 'course_title' in meta, "Chunk metadata should have 'course_title'"
                print(f"[INFO] Chunk metadata: course_title={meta.get('course_title')}, lesson={meta.get('lesson_number')}")
            print("[PASS] Content chunks have correct metadata structure")
        else:
            print("[WARN] No content chunks found")


class TestVectorStoreFilterBuilding:
    """Tests for ChromaDB filter building."""

    def test_build_filter_with_course_only(self, populated_vector_store):
        """Test filter building with course title only."""
        filter_dict = populated_vector_store._build_filter("Introduction to Python", None)

        assert filter_dict is not None
        assert filter_dict == {"course_title": "Introduction to Python"}
        print(f"[PASS] Course-only filter: {filter_dict}")

    def test_build_filter_with_lesson_only(self, populated_vector_store):
        """Test filter building with lesson number only."""
        filter_dict = populated_vector_store._build_filter(None, 2)

        assert filter_dict is not None
        assert filter_dict == {"lesson_number": 2}
        print(f"[PASS] Lesson-only filter: {filter_dict}")

    def test_build_filter_with_both(self, populated_vector_store):
        """Test filter building with both course and lesson."""
        filter_dict = populated_vector_store._build_filter("Introduction to Python", 1)

        assert filter_dict is not None
        assert "$and" in filter_dict
        print(f"[PASS] Combined filter: {filter_dict}")

    def test_build_filter_with_none(self, populated_vector_store):
        """Test filter building with no filters."""
        filter_dict = populated_vector_store._build_filter(None, None)

        assert filter_dict is None
        print(f"[PASS] No filter returned None")


class TestRealWorldScenarios:
    """Tests that simulate real user queries."""

    def test_query_for_course_content(self, populated_vector_store):
        """Test a typical content query."""
        tool_manager = Mock()
        from search_tools import CourseSearchTool

        tool = CourseSearchTool(populated_vector_store)
        result = tool.execute(query="What is Python used for?")

        print(f"[INFO] Query result: {result[:200]}...")
        assert "Python" in result or "No relevant content" in result
        print("[PASS] Content query works")

    def test_query_for_specific_lesson(self, populated_vector_store):
        """Test query for specific lesson content."""
        from search_tools import CourseSearchTool

        tool = CourseSearchTool(populated_vector_store)
        result = tool.execute(query="variables", lesson_number=2)

        print(f"[INFO] Lesson query result: {result[:200]}...")
        assert "Lesson 2" in result or "No relevant content" in result
        print("[PASS] Lesson-specific query works")

    def test_query_with_course_and_lesson(self, populated_vector_store):
        """Test combined course and lesson query."""
        from search_tools import CourseSearchTool

        tool = CourseSearchTool(populated_vector_store)
        result = tool.execute(
            query="data types",
            course_name="Python",
            lesson_number=2
        )

        print(f"[INFO] Combined query result: {result[:200]}...")
        print("[PASS] Combined query works")


# Run tests when executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
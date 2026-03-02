"""
Test configuration and shared fixtures for the RAG system tests.
"""

import os
import shutil
import sys
import tempfile
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def temp_chroma_path():
    """Create a temporary directory for ChromaDB during tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_vector_store(temp_chroma_path):
    """Create a VectorStore with a temporary ChromaDB instance."""
    from vector_store import VectorStore

    store = VectorStore(
        chroma_path=temp_chroma_path, embedding_model="all-MiniLM-L6-v2", max_results=5
    )
    return store


@pytest.fixture
def sample_course():
    """Create a sample Course object for testing."""
    from models import Course, Lesson

    return Course(
        title="Introduction to Python",
        course_link="https://example.com/python",
        instructor="John Doe",
        lessons=[
            Lesson(
                lesson_number=1,
                title="Getting Started",
                lesson_link="https://example.com/lesson1",
            ),
            Lesson(
                lesson_number=2,
                title="Variables and Types",
                lesson_link="https://example.com/lesson2",
            ),
        ],
    )


@pytest.fixture
def sample_chunks():
    """Create sample CourseChunk objects for testing."""
    from models import CourseChunk

    return [
        CourseChunk(
            content="Course Introduction to Python Lesson 1 content: Python is a versatile programming language used for web development, data science, and automation.",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=0,
        ),
        CourseChunk(
            content="Course Introduction to Python Lesson 2 content: Variables in Python are containers for storing data values. Python has several data types including strings, integers, and floats.",
            course_title="Introduction to Python",
            lesson_number=2,
            chunk_index=1,
        ),
        CourseChunk(
            content="Course Introduction to Python Lesson 2 content: Type conversion allows you to convert between different data types using functions like str(), int(), and float().",
            course_title="Introduction to Python",
            lesson_number=2,
            chunk_index=2,
        ),
    ]


@pytest.fixture
def populated_vector_store(mock_vector_store, sample_course, sample_chunks):
    """Create a VectorStore pre-populated with sample data."""
    mock_vector_store.add_course_metadata(sample_course)
    mock_vector_store.add_course_content(sample_chunks)
    return mock_vector_store


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client for testing."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    from dataclasses import dataclass

    @dataclass
    class MockConfig:
        ANTHROPIC_API_KEY: str = "test-api-key"
        ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
        EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
        CHUNK_SIZE: int = 800
        CHUNK_OVERLAP: int = 100
        MAX_RESULTS: int = 5
        MAX_HISTORY: int = 2
        CHROMA_PATH: str = "./test_chroma_db"

    return MockConfig()

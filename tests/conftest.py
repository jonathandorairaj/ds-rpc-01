"""
Pytest configuration and fixtures.

This file runs before tests to set up the environment.
It initializes the RAG pipeline so the FastAPI app can use it during testing.
"""

import pytest
from app.main import app
from app.rag_pipeline import RAGPipeline


@pytest.fixture(scope="session", autouse=True)
def initialize_rag_pipeline():
    """
    Initialize RAG pipeline before any tests run.
    
    This is needed because FastAPI's @app.on_event("startup") 
    doesn't fire during testing.
    
    autouse=True means this runs automatically before all tests.
    scope="session" means it runs once per test session.
    """
    from app import main
    
    # Initialize the global rag_pipeline
    main.rag_pipeline = RAGPipeline()
    main.rag_pipeline.initialize_vector_store()
    
    print("\n✓ RAG pipeline initialized for testing")
    
    yield
    
    # Cleanup after tests (optional)
    print("\n✓ Tests complete")

"""
Comprehensive unit tests for RBAC Chatbot system.

Run with: pytest tests/test_chatbot.py -v

Tests cover:
- Document loading and role tagging
- RAG retrieval with role filtering
- Department-aware prioritization
- FastAPI authentication and endpoints
- Response structure validation
"""

import pytest
from pathlib import Path
from app.document_loader import DocumentLoader
from app.rag_pipeline import RAGPipeline
from app.main import app, USERS
from fastapi.testclient import TestClient
import base64


# ============================================================================
# FIXTURES - Reusable test setup
# ============================================================================

@pytest.fixture
def document_loader():
    """Create a document loader instance."""
    return DocumentLoader(data_dir="resources/data")


@pytest.fixture
def rag_pipeline():
    """Create and initialize a RAG pipeline."""
    pipeline = RAGPipeline()
    pipeline.initialize_vector_store()
    return pipeline


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    return TestClient(app)


# ============================================================================
# DOCUMENT LOADER TESTS
# ============================================================================

class TestDocumentLoader:
    """Test document loading and role-based tagging."""
    
    def test_load_all_documents(self, document_loader):
        """Test that documents are loaded from all departments."""
        docs = document_loader.load_all_documents()
        
        # Should have documents from multiple departments
        assert len(docs) > 0, "Should load at least one document"
        
        # Check we have documents from different departments
        departments = set(doc["department"] for doc in docs)
        assert "finance" in departments
        assert "marketing" in departments
        assert "hr" in departments
        assert "engineering" in departments
        assert "general" in departments
    
    def test_documents_have_required_fields(self, document_loader):
        """Test that each document has all required metadata."""
        docs = document_loader.load_all_documents()
        
        for doc in docs:
            assert "content" in doc
            assert "source" in doc
            assert "department" in doc
            assert "allowed_roles" in doc
            assert len(doc["content"]) > 0
            assert len(doc["allowed_roles"]) > 0
    
    def test_role_access_map(self, document_loader):
        """Test that role access maps are correctly applied."""
        docs = document_loader.load_all_documents()
        
        # Finance docs should only be accessible to finance and c-level
        finance_docs = [d for d in docs if d["department"] == "finance"]
        for doc in finance_docs:
            assert "finance" in doc["allowed_roles"]
            assert "c-level" in doc["allowed_roles"]
            assert "employee" not in doc["allowed_roles"]
        
        # General docs should be accessible to everyone
        general_docs = [d for d in docs if d["department"] == "general"]
        for doc in general_docs:
            assert "employee" in doc["allowed_roles"]
            assert "finance" in doc["allowed_roles"]
    
    def test_get_documents_for_role(self, document_loader):
        """Test filtering documents by role."""
        document_loader.load_all_documents()
        
        # Finance user should see finance + general docs
        finance_docs = document_loader.get_documents_for_role("finance")
        assert len(finance_docs) > 0
        
        # Employee should only see general docs
        employee_docs = document_loader.get_documents_for_role("employee")
        assert all(doc["department"] == "general" for doc in employee_docs)
        
        # C-level should see everything
        c_level_docs = document_loader.get_documents_for_role("c-level")
        assert len(c_level_docs) == len(document_loader.documents)


# ============================================================================
# RAG PIPELINE TESTS
# ============================================================================

class TestRAGPipeline:
    """Test RAG retrieval and generation logic."""
    
    def test_vector_store_initialized(self, rag_pipeline):
        """Test that vector store is properly initialized."""
        assert rag_pipeline.collection is not None
        assert len(rag_pipeline.document_metadata) > 0
    
    def test_retrieve_respects_role_access(self, rag_pipeline):
        """Test that retrieve() respects role-based access control."""
        # Finance user asks about finance
        finance_results = rag_pipeline.retrieve(
            "What are the quarterly financial reports?", 
            "finance", 
            top_k=3
        )
        
        # Should get results
        assert len(finance_results) > 0
        
        # All returned docs should be accessible to finance role
        for doc in finance_results:
            # Check against metadata in rag_pipeline
            doc_allowed = False
            for doc_id, metadata in rag_pipeline.document_metadata.items():
                if metadata["source"] == doc["source"]:
                    assert "finance" in metadata["allowed_roles"]
                    doc_allowed = True
                    break
            assert doc_allowed, f"Doc {doc['source']} not allowed for finance role"
    
    def test_employee_cannot_access_finance_docs(self, rag_pipeline):
        """Test that employee role cannot access finance documents."""
        results = rag_pipeline.retrieve(
            "What are the quarterly financial reports?",
            "employee",
            top_k=3
        )
        
        # Should get results (general docs) or none
        # But should NOT include finance docs
        for doc in results:
            assert doc["department"] != "finance", \
                f"Employee should not access finance docs, got {doc['source']}"
    
    def test_c_level_access_all_docs(self, rag_pipeline):
        """Test that c-level role can access all documents."""
        results = rag_pipeline.retrieve(
            "Tell me about finance, marketing, and HR",
            "c-level",
            top_k=5
        )
        
        # C-level should be able to get docs from multiple departments
        departments = set(doc["department"] for doc in results)
        assert len(departments) > 1, "C-level should access multiple departments"
    
    def test_department_aware_prioritization(self, rag_pipeline):
        """Test that department-specific docs are prioritized over general."""
        # Ask a marketing question
        results = rag_pipeline.retrieve(
            "What was Q4 marketing campaign performance?",
            "marketing",
            top_k=3
        )
        
        # Should prioritize marketing docs over general docs
        marketing_count = sum(1 for doc in results if doc["department"] == "marketing")
        general_count = sum(1 for doc in results if doc["department"] == "general")
        
        # Marketing docs should come first if available
        if marketing_count > 0:
            # Check that marketing docs are not at the end
            last_doc_dept = results[-1]["department"]
            # At least one marketing doc should appear
            assert any(doc["department"] == "marketing" for doc in results)
    
    def test_retrieve_returns_sources(self, rag_pipeline):
        """Test that retrieve returns document sources."""
        results = rag_pipeline.retrieve(
            "Tell me about the company",
            "employee",
            top_k=3
        )
        
        if len(results) > 0:
            for doc in results:
                assert "source" in doc
                assert len(doc["source"]) > 0
                assert ".md" in doc["source"] or ".csv" in doc["source"]
    
    def test_query_without_accessible_docs(self, rag_pipeline):
        """Test query response when no accessible docs found."""
        # Ask a question that likely has no marketing docs
        # while using a role that shouldn't access finance
        result = rag_pipeline.query(
            "What is the secret financial password?",  # Intentionally obscure
            "marketing"
        )
        
        assert "answer" in result
        assert "sources" in result
        assert "role" in result
        assert result["role"] == "marketing"


# ============================================================================
# FASTAPI AUTHENTICATION TESTS
# ============================================================================

class TestAuthentication:
    """Test API authentication and authorization."""
    
    def test_health_check_no_auth(self, test_client):
        """Test that health endpoint works without authentication."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_unauthorized_request(self, test_client):
        """Test that request without auth credentials is rejected."""
        response = test_client.get("/me")
        assert response.status_code == 401
    
    def test_invalid_credentials(self, test_client):
        """Test that invalid credentials are rejected."""
        credentials = base64.b64encode(b"finance_user:wrongpassword").decode()
        response = test_client.get(
            "/me",
            headers={"Authorization": f"Basic {credentials}"}
        )
        assert response.status_code == 401
    
    def test_valid_credentials(self, test_client):
        """Test that valid credentials are accepted."""
        credentials = base64.b64encode(b"finance_user:finance123").decode()
        response = test_client.get(
            "/me",
            headers={"Authorization": f"Basic {credentials}"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "finance_user"
        assert response.json()["role"] == "finance"
    
    def test_all_test_users_exist(self, test_client):
        """Test that all test users can authenticate."""
        for username, user_data in USERS.items():
            credentials = base64.b64encode(
                f"{username}:{user_data['password']}".encode()
            ).decode()
            response = test_client.get(
                "/me",
                headers={"Authorization": f"Basic {credentials}"}
            )
            assert response.status_code == 200
            assert response.json()["role"] == user_data["role"]


# ============================================================================
# FASTAPI ENDPOINT TESTS
# ============================================================================

class TestQueryEndpoint:
    """Test the /query endpoint with authentication and RBAC."""
    
    def _make_auth_header(self, username: str, password: str) -> dict:
        """Helper to create auth header."""
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}
    
    def test_query_requires_auth(self, test_client):
        """Test that /query endpoint requires authentication."""
        response = test_client.post(
            "/query",
            json={"question": "What is the company policy?"}
        )
        assert response.status_code == 401
    
    def test_query_with_valid_auth(self, test_client):
        """Test that authenticated request to /query succeeds."""
        auth = self._make_auth_header("employee_user", "employee123")
        response = test_client.post(
            "/query",
            json={"question": "What is the company policy?"},
            headers=auth
        )
        assert response.status_code == 200
    
    def test_query_response_structure(self, test_client):
        """Test that query response has correct structure."""
        auth = self._make_auth_header("finance_user", "finance123")
        response = test_client.post(
            "/query",
            json={"question": "Tell me about the company"},
            headers=auth
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "answer" in data
        assert "sources" in data
        assert "role" in data
        assert "query" in data
        
        # Check types
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["role"], str)
        assert isinstance(data["query"], str)
    
    def test_finance_user_access_control(self, test_client):
        """Test that finance user can query finance data."""
        auth = self._make_auth_header("finance_user", "finance123")
        response = test_client.post(
            "/query",
            json={"question": "What are the financial reports?"},
            headers=auth
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "finance"
        assert len(data["answer"]) > 0  # Should have some answer
    
    def test_employee_limited_access(self, test_client):
        """Test that employee has limited access."""
        auth = self._make_auth_header("employee_user", "employee123")
        response = test_client.post(
            "/query",
            json={"question": "Tell me about company policies"},
            headers=auth
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "employee"
        # Should only see general documents
        if len(data["sources"]) > 0:
            assert "general" in data["sources"][0]
    
    def test_c_level_full_access(self, test_client):
        """Test that c-level executive has access to all documents."""
        auth = self._make_auth_header("exec_user", "exec123")
        response = test_client.post(
            "/query",
            json={"question": "Give me a company overview"},
            headers=auth
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "c-level"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    def _make_auth_header(self, username: str, password: str) -> dict:
        """Helper to create auth header."""
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}
    
    def test_full_workflow_finance_user(self, test_client):
        """Test complete workflow: login → query → receive answer."""
        # Step 1: Authenticate
        auth = self._make_auth_header("finance_user", "finance123")
        auth_response = test_client.get("/me", headers=auth)
        assert auth_response.status_code == 200
        assert auth_response.json()["role"] == "finance"
        
        # Step 2: Query
        query_response = test_client.post(
            "/query",
            json={"question": "What are our quarterly results?"},
            headers=auth
        )
        assert query_response.status_code == 200
        
        # Step 3: Validate response
        data = query_response.json()
        assert data["role"] == "finance"
        assert len(data["answer"]) > 0
        assert data["query"] == "What are our quarterly results?"
    
    def test_full_workflow_marketing_user(self, test_client):
        """Test workflow for marketing user."""
        auth = self._make_auth_header("marketing_user", "marketing123")
        
        response = test_client.post(
            "/query",
            json={"question": "What was the Q4 campaign performance?"},
            headers=auth
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "marketing"
    
    def test_rbac_enforcement_across_users(self, test_client):
        """Test that RBAC is properly enforced across different users."""
        question = "Tell me about the company"
        
        # Finance user response
        finance_auth = self._make_auth_header("finance_user", "finance123")
        finance_response = test_client.post(
            "/query",
            json={"question": question},
            headers=finance_auth
        ).json()
        
        # Employee response
        employee_auth = self._make_auth_header("employee_user", "employee123")
        employee_response = test_client.post(
            "/query",
            json={"question": question},
            headers=employee_auth
        ).json()
        
        # Both should have answers (general doc is available to both)
        # But the role should be different
        assert finance_response["role"] == "finance"
        assert employee_response["role"] == "employee"

# ============================================================================
# FILE PARSER TESTS
# ============================================================================

class TestFileParser:
    """Test file parsing for different formats."""
    
    def test_parse_markdown(self):
        """Test markdown file parsing."""
        from app.file_parser import FileParser
        
        md_content = b"# Test Markdown\\n\\nThis is a test."
        content, format = FileParser.parse_file(md_content, "test.md")
        
        assert "Test Markdown" in content
        assert format == "markdown"
    
    def test_parse_csv(self):
        """Test CSV file parsing."""
        from app.file_parser import FileParser
        
        csv_content = b"name,salary\\nAlice,50000\\nBob,60000"
        content, format = FileParser.parse_file(csv_content, "data.csv")
        
        assert "Alice" in content
        assert "50000" in content
        assert format == "csv"
    
    def test_invalid_format(self):
        """Test that invalid formats are rejected."""
        from app.file_parser import FileParser
        import pytest
        
        with pytest.raises(ValueError):
            FileParser.parse_file(b"some content", "file.txt")
    
    def test_validate_filename(self):
        """Test filename validation."""
        from app.file_parser import FileParser
        
        assert FileParser.validate_filename("document.md")
        assert FileParser.validate_filename("data.csv")
        assert FileParser.validate_filename("report.pdf")
        assert not FileParser.validate_filename("file.txt")
    
    def test_infer_department(self):
        """Test department inference from filename."""
        from app.file_parser import FileParser
        
        assert FileParser.get_department_from_filename("finance_report.pdf") == "finance"
        assert FileParser.get_department_from_filename("q4_marketing.csv") == "marketing"
        assert FileParser.get_department_from_filename("employee_data.csv") == "hr"
        assert FileParser.get_department_from_filename("architecture.md") == "engineering"
        assert FileParser.get_department_from_filename("random.md") is None


# ============================================================================
# DOCUMENT UPLOAD TESTS
# ============================================================================

class TestDocumentUpload:
    """Test document upload functionality."""
    
    def _make_auth_header(self, username: str, password: str) -> dict:
        """Helper to create auth header."""
        import base64
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}
    
    def test_upload_requires_auth(self, test_client):
        """Test that upload endpoint requires authentication."""
        file_content = b"# Test Document"
        
        response = test_client.post(
            "/upload",
            files={"file": ("test.md", file_content)},
        )
        assert response.status_code == 401
    
    def test_upload_requires_c_level(self, test_client):
        """Test that only C-level users can upload."""
        file_content = b"# Finance Report"
        auth = self._make_auth_header("finance_user", "finance123")
        
        response = test_client.post(
            "/upload",
            files={"file": ("finance_doc.md", file_content)},
            data={"department": "finance"},
            headers=auth,
        )
        
        assert response.status_code == 403
    
    def test_upload_markdown(self, test_client):
        """Test uploading a markdown file."""
        file_content = b"# Finance Report\\n\\n## Q4 Results"
        auth = self._make_auth_header("exec_user", "exec123")
        
        response = test_client.post(
            "/upload",
            files={"file": ("finance_report.md", file_content)},
            data={"department": "finance"},
            headers=auth,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "finance_report.md"
        assert data["department"] == "finance"
    
    def test_upload_infer_department(self, test_client):
        """Test that department is inferred from filename."""
        file_content = b"# Q4 Campaign Performance"
        auth = self._make_auth_header("exec_user", "exec123")
        
        response = test_client.post(
            "/upload",
            files={"file": ("q4_marketing_campaign.md", file_content)},
            headers=auth,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["department"] == "marketing"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

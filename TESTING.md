# Testing Guide for RBAC Chatbot

## 🧪 Running the Tests

### Prerequisites
Make sure you have pytest installed:
```bash
pip install pytest httpx
```

### Run All Tests
```bash
cd /path/to/ds-rpc-01
pytest tests/test_chatbot.py -v
```

The `-v` flag makes output verbose (shows each test).

### Run Specific Test Class
```bash
pytest tests/test_chatbot.py::TestDocumentLoader -v
pytest tests/test_chatbot.py::TestRAGPipeline -v
pytest tests/test_chatbot.py::TestAuthentication -v
```

### Run a Single Test
```bash
pytest tests/test_chatbot.py::TestDocumentLoader::test_load_all_documents -v
```

---

## 📋 Test Structure & What Each Tests

### **TestDocumentLoader** - Document Loading & Tagging
```
✓ test_load_all_documents
  → Verifies documents load from all 5 departments

✓ test_documents_have_required_fields
  → Checks each doc has content, source, department, allowed_roles

✓ test_role_access_map
  → Verifies correct role → department mapping
  → Finance docs only accessible to finance + c-level

✓ test_get_documents_for_role
  → Employee should only see general docs
  → Finance should see finance + general docs
  → C-level should see everything
```

**Why this matters:** Tests that document tagging is correct. If this fails, RBAC won't work.

---

### **TestRAGPipeline** - Retrieval & Generation Logic
```
✓ test_vector_store_initialized
  → Chroma vector database is set up

✓ test_retrieve_respects_role_access
  → Finance user gets finance docs
  → Proves RBAC works at retrieval time

✓ test_employee_cannot_access_finance_docs
  → Employee asks about finance
  → Should NOT get finance docs (access denied)

✓ test_c_level_access_all_docs
  → C-level can access multiple departments

✓ test_department_aware_prioritization
  → When asking about marketing, marketing docs come first
  → General docs only added if needed

✓ test_retrieve_returns_sources
  → Retrieved docs have source citations
```

**Why this matters:** Tests the core RAG logic and RBAC enforcement.

---

### **TestAuthentication** - User Login & Credentials
```
✓ test_health_check_no_auth
  → /health endpoint works without login

✓ test_unauthorized_request
  → Request without credentials is rejected

✓ test_invalid_credentials
  → Wrong password is rejected

✓ test_valid_credentials
  → Correct username/password accepted
  → Returns correct role

✓ test_all_test_users_exist
  → All 6 test accounts work
```

**Why this matters:** Tests authentication layer. Without this, anyone could query.

---

### **TestQueryEndpoint** - API Functionality
```
✓ test_query_requires_auth
  → Can't query without logging in

✓ test_query_with_valid_auth
  → Authenticated request succeeds

✓ test_query_response_structure
  → Response has all required fields:
    - answer
    - sources
    - role
    - query

✓ test_finance_user_access_control
  → Finance user gets finance docs when querying

✓ test_employee_limited_access
  → Employee only gets general docs

✓ test_c_level_full_access
  → C-level gets docs from multiple departments
```

**Why this matters:** Tests the actual API endpoints that Streamlit calls.

---

### **TestIntegration** - End-to-End Workflows
```
✓ test_full_workflow_finance_user
  1. Login as finance_user
  2. Query: "What are our quarterly results?"
  3. Verify answer is returned with role

✓ test_full_workflow_marketing_user
  1. Login as marketing_user
  2. Query about campaign performance
  3. Verify response

✓ test_rbac_enforcement_across_users
  → Same question, different users
  → Verify they get different access levels
```

**Why this matters:** Tests the complete system from login to response.

---

## 🎯 Expected Output

When you run `pytest tests/test_chatbot.py -v`, you should see:

```
tests/test_chatbot.py::TestDocumentLoader::test_load_all_documents PASSED
tests/test_chatbot.py::TestDocumentLoader::test_documents_have_required_fields PASSED
tests/test_chatbot.py::TestDocumentLoader::test_role_access_map PASSED
tests/test_chatbot.py::TestDocumentLoader::test_get_documents_for_role PASSED
tests/test_chatbot.py::TestRAGPipeline::test_vector_store_initialized PASSED
tests/test_chatbot.py::TestRAGPipeline::test_retrieve_respects_role_access PASSED
... (many more)

======================== 25 passed in 12.5s ========================
```

All tests should **PASS** ✅

---

## 🚨 If Tests Fail

### Failure: "No documents found"
- Check that `resources/data/` folder exists with markdown files
- Run: `find resources/data -type f`

### Failure: "Cannot connect to Ollama"
- Run `ollama serve` in another terminal
- Verify: `ollama list` shows `phi`

### Failure: "API initialization error"
- Make sure FastAPI can import all modules
- Run: `python -c "from app.main import app"`

---

## 📊 Code Coverage

These tests cover:
- ✅ **Document Loading** - 4 tests
- ✅ **RAG Logic** - 7 tests
- ✅ **Authentication** - 5 tests
- ✅ **API Endpoints** - 6 tests
- ✅ **Integration** - 3 tests
- **Total: 25 tests**

---

## 🧠 What You're Learning

By writing and understanding these tests, you're learning:

1. **Test Structure** - Using pytest fixtures, classes, parametrization
2. **Unit Testing** - Testing individual components in isolation
3. **Integration Testing** - Testing components working together
4. **RBAC Testing** - How to verify access control works
5. **API Testing** - Testing FastAPI endpoints
6. **Mocking** - (You could extend this with mocks of Ollama)

---

## 💡 Next Steps

After all tests pass:
1. Show test output in interview: "I wrote 25 unit/integration tests covering..."
2. Add more edge cases if you want: "What if user is deleted?"
3. Add performance tests: "How fast is retrieval?"
4. Add security tests: "Can I access docs I shouldn't?"

---

## Running Tests Locally

```bash
# Install dependencies if you haven't
pip install pytest httpx

# Run all tests with verbose output
pytest tests/test_chatbot.py -v

# Run specific test class
pytest tests/test_chatbot.py::TestRAGPipeline -v

# Run one specific test
pytest tests/test_chatbot.py::TestRAGPipeline::test_retrieve_respects_role_access -v

# Run with coverage (if you install coverage)
pytest tests/test_chatbot.py --cov=app --cov-report=html
```

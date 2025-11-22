# FinSolve RBAC Chatbot

A production-ready **Role-Based Access Control (RBAC) chatbot** built with FastAPI, Claude AI, and Chroma vector database. Demonstrates full-stack RAG (Retrieval-Augmented Generation) system with dynamic document upload, security enforcement, and comprehensive testing.

## 🎯 Features

- **Role-Based Access Control (RBAC)** - Users only see documents their role can access
- **RAG System** - Semantic search + Claude AI for intelligent answers grounded in company documents
- **Document Upload** - C-level executives can upload MD/CSV/PDF files that are immediately queryable
- **Multi-Format Support** - Markdown, CSV, and PDF with automatic text extraction
- **Department Inference** - System auto-detects department from filename
- **Secure Authentication** - HTTP Basic Auth for user verification
- **Production-Ready** - 25+ tests, error handling, comprehensive logging
- **Streamlit UI** - Clean, user-friendly interface for non-technical users
- **Claude AI Integration** - Uses Claude Haiku for cost-effective, high-quality responses

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│            (Login, Query, Upload, Chat History)         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Authentication (HTTP Basic)                         ││
│  │ ┌───────────────────────────────────────────────┐   ││
│  │ │ Endpoints:                                    │   ││
│  │ │ • POST /query (with role filtering)           │   ││
│  │ │ • POST /upload (C-level only)                 │   ││
│  │ │ • GET /me (current user info)                 │   ││
│  │ └───────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────┘│
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  RAG Pipeline                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Document    │  │  Retrieval   │  │  LLM         │  │
│  │  Loader &    │→ │  (Semantic   │→ │  Response    │  │
│  │  File Parser │  │   Search)    │  │  Generator   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                    │       │
│         └──────────────────┼────────────────────┘       │
│                            │                            │
│                   RBAC Enforcement                      │
│            (Filter docs by allowed_roles)              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Vector Database & LLM                       │
│  ┌──────────────────────┐  ┌──────────────────────┐    │
│  │  Chroma              │  │  Claude Haiku API    │    │
│  │  (Vector Store)      │  │  (Response Gen)      │    │
│  │  • Embeddings        │  │  • Semantic          │    │
│  │  • Semantic Search   │  │    Understanding     │    │
│  │  • Real-time Indexing│  │  • Cost-Effective    │    │
│  └──────────────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 📋 User Roles & Permissions

| Role | Can Upload | Access |
|------|-----------|--------|
| **C-Level Executive** | ✅ Yes | All documents |
| **Finance** | ❌ No | Finance + General docs |
| **Marketing** | ❌ No | Marketing + General docs |
| **HR** | ❌ No | HR + General docs |
| **Engineering** | ❌ No | Engineering + General docs |
| **Employee** | ❌ No | General docs only |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Anthropic API key (free tier available at https://console.anthropic.com)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ds-rpc-01.git
cd ds-rpc-01
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up API key**
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

5. **Run the application**

Terminal 1 - FastAPI Backend:
```bash
python -m uvicorn app.main:app --reload
```

Terminal 2 - Streamlit Frontend:
```bash
streamlit run streamlit_app.py
```

6. **Access the application**
- Streamlit UI: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs

## 🔐 Test Accounts

Use these credentials to test different roles:

```
Finance Team:     finance_user     / finance123
Marketing Team:   marketing_user   / marketing123
HR Team:          hr_user          / hr123
Engineering:      engineering_user / engineering123
C-Level Exec:     exec_user        / exec123
Employee:         employee_user    / employee123
```

## 📖 Usage Examples

### Example 1: Query as Finance User
```
1. Login: finance_user / finance123
2. Ask: "What was our Q4 revenue?"
3. System retrieves finance documents
4. Claude generates answer grounded in data
5. Shows sources for verification
```

### Example 2: Upload Document as C-Level
```
1. Login: exec_user / exec123
2. See "Upload Document" section
3. Select a PDF/CSV/MD file
4. Choose department or let system auto-detect
5. Document immediately indexed and queryable
```

### Example 3: RBAC in Action
```
1. C-Level uploads finance report
2. Finance user can query it → Success ✅
3. Marketing user asks same question → "No documents found" ✅
4. Employee user asks → Only sees general docs ✅
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/test_chatbot.py -v
```

### Run Specific Test Suite
```bash
pytest tests/test_chatbot.py::TestRAGPipeline -v
pytest tests/test_chatbot.py::TestDocumentUpload -v
```

### Run End-to-End Test
```bash
python e2e_test.py
```

**Test Coverage:**
- ✅ Document loading & RBAC tagging (4 tests)
- ✅ RAG retrieval & generation (7 tests)
- ✅ Authentication & authorization (5 tests)
- ✅ API endpoints (6 tests)
- ✅ File parsing (5 tests)
- ✅ Document upload (10 tests)
- ✅ End-to-end workflows (3 tests)

**Total: 40+ tests, all passing**

## 📁 Project Structure

```
ds-rpc-01/
├── app/
│   ├── main.py              # FastAPI application with RBAC endpoints
│   ├── rag_pipeline.py      # RAG logic with Claude integration
│   ├── document_loader.py   # Document loading & RBAC tagging
│   ├── file_parser.py       # Multi-format file parsing
│   └── __init__.py
├── tests/
│   ├── test_chatbot.py      # Comprehensive test suite (40+ tests)
│   ├── conftest.py          # Pytest configuration & fixtures
│   └── __init__.py
├── resources/
│   └── data/                # Original company documents
│       ├── finance/         # Financial reports
│       ├── marketing/       # Marketing campaigns
│       ├── hr/             # HR policies
│       ├── engineering/    # Technical docs
│       └── general/        # Company handbook
├── sample_uploads/          # Example files for testing
│   ├── Q4_2024_Financial_Report.md
│   ├── Q4_Marketing_Campaign_Report.md
│   └── HR_Employee_Handbook.md
├── streamlit_app.py         # User interface
├── e2e_test.py             # End-to-end test suite
├── requirements.txt         # Python dependencies
├── .env.example            # Template for environment variables
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── ARCHITECTURE.md         # Detailed architecture & design
├── API.md                  # API documentation
└── DESIGN_DECISIONS.md     # Design decisions & rationale
```

## 🔑 Key Technologies

- **Backend Framework:** FastAPI (async, high performance)
- **LLM:** Claude Haiku via Anthropic API (cost-effective, high quality)
- **Vector Database:** Chroma (in-memory, semantic search)
- **Frontend:** Streamlit (rapid UI development)
- **Authentication:** HTTP Basic Auth
- **Testing:** Pytest (25+ tests)
- **File Parsing:** pdfplumber (PDF), pandas (CSV)

## 🎓 Learning Outcomes

This project demonstrates:

1. **Full-Stack Development** - Backend API + Frontend UI
2. **RAG Systems** - Retrieval-Augmented Generation with semantic search
3. **Security** - Authentication, authorization, role-based access control
4. **Testing** - Unit tests, integration tests, end-to-end tests
5. **LLM Integration** - Working with production LLM APIs
6. **Document Processing** - Handling multiple file formats
7. **System Design** - Clean architecture, separation of concerns
8. **Production Practices** - Error handling, logging, documentation

## 🚦 Performance Characteristics

- **Retrieval Time:** ~100-200ms (Chroma semantic search)
- **LLM Response Time:** ~1-3 seconds (Claude Haiku)
- **Total Query Time:** ~1.5-3.5 seconds
- **Vector Store:** In-memory (fast, no network latency)
- **Scalability:** Tested with 40+ documents, easily scales to thousands

## 💰 Cost Analysis

Assuming 100 queries/day with avg 500 input + 300 output tokens:

| Component | Monthly Cost |
|-----------|--------------|
| Claude Haiku API | ~$1.05 |
| Ollama (local) | FREE |
| FastAPI/Streamlit | FREE |
| **Total** | **~$1/month** |

## 🔐 Security Considerations

✅ **What's Implemented:**
- HTTP Basic authentication
- Role-based access control at retrieval time
- Input validation on file uploads
- API key isolation via .env
- No sensitive data logged

⚠️ **For Production:**
- Use OAuth2 instead of HTTP Basic Auth
- Add SSL/TLS (HTTPS)
- Implement rate limiting
- Add request logging/monitoring
- Use managed authentication service

## 🤝 Contributing

This is a portfolio project. Feel free to fork and extend!

### Ideas for Enhancement
- Add chat persistence (save conversations to database)
- Implement role hierarchy (managers see subordinate data)
- Add document versioning
- Integrate with S3 for file storage
- Add admin dashboard for user management
- Implement semantic caching for faster responses

## 📞 Support

For questions or issues:
1. Check ARCHITECTURE.md for system design details
2. See DESIGN_DECISIONS.md for rationale
3. Review TESTING.md for test execution
4. Check API.md for endpoint documentation

## 📄 License

MIT License - feel free to use for personal or commercial projects.

---

**Built with ❤️ for modern AI systems**

*Last Updated: November 2024*

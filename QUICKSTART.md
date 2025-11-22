# FinSolve RBAC Chatbot - Quick Start Guide

## 🚀 Setup (5 minutes)

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Ensure Ollama is Running
Make sure you have Ollama running with Mistral model loaded:
```bash
ollama serve
```
(Keep this running in a separate terminal)

Verify Mistral is available:
```bash
ollama list
```
You should see `mistral` in the list.

---

## ▶️ Run the Application

### Terminal 1: Start FastAPI Backend
```bash
cd /path/to/ds-rpc-01
python -m uvicorn app.main:app --reload
```

You should see:
```
✓ Loaded X documents into vector store
✓ RAG pipeline initialized on startup
Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Start Streamlit Frontend
```bash
cd /path/to/ds-rpc-01
streamlit run streamlit_app.py
```

This will open the chatbot UI in your browser (usually http://localhost:8501)

---

## 🔐 Test Accounts

Use any of these to login:

| Role | Username | Password |
|------|----------|----------|
| Finance | finance_user | finance123 |
| Marketing | marketing_user | marketing123 |
| HR | hr_user | hr123 |
| Engineering | engineering_user | engineering123 |
| C-Level Executive | exec_user | exec123 |
| Employee | employee_user | employee123 |

Each role can only see documents from their department(s).

---

## 📋 What's Implemented

✅ **Authentication** - HTTP Basic Auth with role assignment  
✅ **RAG Pipeline** - Document retrieval + LLM response generation  
✅ **Role-Based Access Control** - Users only see relevant documents  
✅ **Vector Store** - Chroma with automatic embeddings  
✅ **LLM Integration** - Ollama/Mistral for response generation  
✅ **Streamlit UI** - User-friendly chatbot interface  
✅ **FastAPI Backend** - RESTful API with endpoints  

---

## 🧪 Test It

1. **Login as Finance user** and ask: "What are the quarterly financial reports?"
   - Should return finance documents only

2. **Login as Marketing user** and ask the same question
   - Should get "No documents found" (no access to finance docs)

3. **Login as C-Level executive** and ask: "What are the quarterly financial reports?"
   - Should return finance documents (C-level has full access)

4. **Login as Employee** and ask: "What are company policies?"
   - Should return employee handbook

---

## 🐛 Troubleshooting

**"Cannot connect to Ollama"**
- Make sure `ollama serve` is running in another terminal
- Check: `curl http://localhost:11434/api/tags`

**"Cannot connect to API"**
- Make sure FastAPI is running: `python -m uvicorn app.main:app --reload`
- Check: `curl http://localhost:8000/health`

**"No documents found"**
- Check that `resources/data/` folder has markdown/CSV files
- Run: `python -c "from app.document_loader import DocumentLoader; d = DocumentLoader(); docs = d.load_all_documents(); print(f'Loaded {len(docs)} docs')"`

**Slow response time**
- First query can be slow (~10-30s) while Ollama initializes
- Subsequent queries are faster
- You can reduce `top_k` in RAG pipeline for faster retrieval

---

## 📁 Project Structure

```
ds-rpc-01/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with auth & endpoints
│   ├── rag_pipeline.py      # RAG logic with role filtering
│   └── document_loader.py   # Load & tag documents
├── resources/
│   └── data/                # Company documents (finance, marketing, hr, etc.)
├── streamlit_app.py         # Streamlit UI
├── requirements.txt         # Dependencies
└── README.md               # This file
```

---

## ⏱️ Timeline

This project was built in ~2 hours with:
- Document loading and role mapping (20 min)
- RAG pipeline setup (40 min)
- FastAPI endpoints (30 min)
- Streamlit UI (25 min)
- Testing and debugging (5 min)

You can extend it further by:
- Adding more complex role hierarchies
- Implementing persistent chat history
- Adding document upload functionality
- Integrating with actual company databases
- Fine-tuning prompts for better responses

---

## 📚 Key Files Explained

### `app/document_loader.py`
Loads markdown and CSV files from `resources/data/` and tags them with:
- Department (finance, marketing, hr, engineering, general)
- Allowed roles (which roles can access)

### `app/rag_pipeline.py`
Handles:
- Vector embedding and storage (Chroma)
- Semantic search on user queries
- Role-based filtering of results
- LLM response generation (Ollama)

### `app/main.py`
FastAPI application with:
- HTTP Basic authentication
- `/query` endpoint for chatbot
- Role-based access control
- Startup event to initialize RAG pipeline

### `streamlit_app.py`
User interface with:
- Login form
- Query input
- Answer display with sources
- Chat history

---

Happy chatting! 🚀

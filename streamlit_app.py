import streamlit as st
import requests
import base64
from typing import Optional

# Page config
st.set_page_config(
    page_title="FinSolve RBAC Chatbot",
    page_icon="🤖",
    layout="wide",
)

# API base URL
API_URL = "http://localhost:8000"

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.password = None
    st.session_state.role = None
    st.session_state.chat_history = []


def make_auth_header(username: str, password: str) -> dict:
    """Create Basic Auth header."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


def test_connection():
    """Test if API is running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def login(username: str, password: str):
    """Authenticate user."""
    try:
        auth_header = make_auth_header(username, password)
        response = requests.get(
            f"{API_URL}/me",
            headers=auth_header,
            timeout=5,
        )
        
        if response.status_code == 200:
            user_data = response.json()
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.password = password
            st.session_state.role = user_data["role"]
            st.session_state.chat_history = []
            st.success(f"✓ Logged in as {username} ({user_data['role'].upper()} role)")
            return True
        else:
            st.error("❌ Invalid credentials")
            return False
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API at {API_URL}. Make sure FastAPI is running.")
        return False
    except Exception as e:
        st.error(f"❌ Login failed: {str(e)}")
        return False


def query_chatbot(question: str) -> Optional[dict]:
    """Send query to chatbot API."""
    try:
        auth_header = make_auth_header(st.session_state.username, st.session_state.password)
        response = requests.post(
            f"{API_URL}/query",
            json={"question": question},
            headers=auth_header,
            timeout=30,
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Query failed: {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Query timed out. Ollama might be slow. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API. Make sure FastAPI is running on {API_URL}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def upload_document(file, department: str) -> Optional[dict]:
    """Upload document to API."""
    try:
        auth_header = make_auth_header(st.session_state.username, st.session_state.password)
        
        files = {"file": (file.name, file, "application/octet-stream")}
        response = requests.post(
            f"{API_URL}/upload",
            files=files,
            data={"department": department},
            headers={"Authorization": auth_header["Authorization"]},
            timeout=30,
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API. Make sure FastAPI is running.")
        return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None


# Main UI
st.title("🤖 FinSolve RBAC Chatbot")
st.markdown("Role-based access to company documents with AI-powered answers")

# Check API connection
if not test_connection():
    st.error(
        f"⚠️ **Cannot connect to API at {API_URL}**\n\n"
        "Make sure FastAPI is running:\n"
        "```bash\npython -m uvicorn app.main:app --reload\n```"
    )
    st.stop()

# Authentication section
if not st.session_state.authenticated:
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔐 Login")
        
        # Show available test accounts
        with st.expander("📋 Available Test Accounts"):
            st.write("""
            **Finance Team:** finance_user / finance123
            
            **Marketing Team:** marketing_user / marketing123
            
            **HR Team:** hr_user / hr123
            
            **Engineering Team:** engineering_user / engineering123
            
            **C-Level Executive:** exec_user / exec123
            
            **Employee:** employee_user / employee123
            """)
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button", type="primary"):
            login(username, password)
    
    with col2:
        st.subheader("ℹ️ About")
        st.write("""
        This is a **Role-Based Access Control (RBAC)** chatbot for FinSolve Technologies.
        
        Each role has access to different company documents:
        - **Finance:** Financial reports, expenses
        - **Marketing:** Campaign data, sales metrics
        - **HR:** Employee data, payroll
        - **Engineering:** Technical docs, processes
        - **C-Level:** Full access + upload documents
        - **Employee:** General info, policies
        
        The chatbot uses **RAG** (Retrieval-Augmented Generation) to answer questions based on company documents.
        """)

else:
    # Authenticated section
    st.sidebar.success(f"✓ Logged in as **{st.session_state.username}**")
    st.sidebar.info(f"Role: **{st.session_state.role.upper()}**")
    
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state.authenticated = False
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    # Show different UI based on role
    if st.session_state.role == "c-level":
        # C-level users can upload documents
        st.subheader("📤 Upload Document")
        
        with st.expander("Upload new document (MD, CSV, or PDF)", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                uploaded_file = st.file_uploader(
                    "Choose a file",
                    type=["md", "csv", "pdf"],
                    key="file_uploader"
                )
            
            with col2:
                department_options = {
                    "Auto-detect": None,
                    "Finance": "finance",
                    "Marketing": "marketing",
                    "HR": "hr",
                    "Engineering": "engineering",
                    "General": "general",
                }
                selected_dept = st.selectbox(
                    "Department (or auto-detect)",
                    options=department_options.keys(),
                    key="dept_select"
                )
                department = department_options[selected_dept]
            
            if uploaded_file is not None:
                if st.button("🚀 Upload", key="upload_button"):
                    with st.spinner("Uploading document..."):
                        result = upload_document(uploaded_file, department)
                    
                    if result:
                        st.success("✓ Document uploaded successfully!")
                        st.info(f"""
                        **Uploaded:** {result['filename']}
                        **Department:** {result['department']}
                        **Accessible to:** {', '.join(result['accessible_roles'])}
                        **Document ID:** {result['doc_id']}
                        """)
    
    st.divider()
    
    # Query section
    st.subheader("💬 Ask a Question")
    
    question = st.text_area(
        "Enter your question:",
        placeholder="e.g., 'What are the Q4 marketing campaign results?' or 'Tell me about the company benefits'",
        key="query_input",
        height=100
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        submit_button = st.button("🔍 Ask", type="primary", use_container_width=True)
    
    # Process query
    if submit_button and question.strip():
        with st.spinner("🔄 Retrieving relevant documents and generating answer..."):
            result = query_chatbot(question)
        
        if result:
            # Add to chat history
            st.session_state.chat_history.append({
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
            })
            
            # Display answer
            st.success("✓ Answer Generated")
            st.markdown("### Answer")
            st.write(result["answer"])
            
            # Display sources
            if result["sources"]:
                with st.expander("📚 Sources"):
                    for source in result["sources"]:
                        st.write(f"- {source}")
    
    # Chat history
    if st.session_state.chat_history:
        st.divider()
        st.subheader("📖 Chat History")
        
        for i, exchange in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"Q: {exchange['question'][:60]}..."):
                st.markdown("**Question:**")
                st.write(exchange["question"])
                st.markdown("**Answer:**")
                st.write(exchange["answer"])
                st.markdown("**Sources:**")
                for source in exchange["sources"]:
                    st.write(f"- {source}")
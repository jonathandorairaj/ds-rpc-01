from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import secrets
from app.rag_pipeline import RAGPipeline
from app.file_parser import FileParser

# Initialize FastAPI app
app = FastAPI(title="FinSolve RBAC Chatbot", version="1.0.0")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBasic()

# Mock user database with roles
USERS = {
    "finance_user": {"password": "finance123", "role": "finance"},
    "marketing_user": {"password": "marketing123", "role": "marketing"},
    "hr_user": {"password": "hr123", "role": "hr"},
    "engineering_user": {"password": "engineering123", "role": "engineering"},
    "exec_user": {"password": "exec123", "role": "c-level"},
    "employee_user": {"password": "employee123", "role": "employee"},
}

# Initialize RAG pipeline (lazy loaded)
rag_pipeline = None


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list
    role: str
    query: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    doc_id: str
    department: str
    accessible_roles: list


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    """Authenticate user and return their role."""
    user = USERS.get(credentials.username)
    
    if not user or not secrets.compare_digest(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return {
        "username": credentials.username,
        "role": user["role"],
    }


@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on startup."""
    global rag_pipeline
    rag_pipeline = RAGPipeline()
    rag_pipeline.initialize_vector_store()
    print("✓ RAG pipeline initialized on startup")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@app.post("/query", response_model=QueryResponse)
async def query_chatbot(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
) -> QueryResponse:
    """
    Query the RAG chatbot with role-based access control.
    
    Only returns documents the user's role has access to.
    """
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        result = rag_pipeline.query(request.question, current_user["role"])
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    department: str = None,
    current_user: dict = Depends(get_current_user),
) -> UploadResponse:
    """
    Upload a new document (MD, CSV, or PDF) to the chatbot.
    
    Only C-level users can upload documents.
    
    Args:
        file: Document file to upload (MD, CSV, or PDF)
        department: Department this document belongs to (optional)
                   If not provided, will try to infer from filename
        
    Returns:
        Upload confirmation with document ID and accessible roles
    """
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    # Only c-level can upload documents
    if current_user["role"] != "c-level":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only C-level executives can upload documents",
        )
    
    try:
        # Validate file format
        if not FileParser.validate_filename(file.filename):
            raise ValueError(
                f"Unsupported file format. Supported: MD, CSV, PDF"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Parse file
        content, file_format = FileParser.parse_file(file_content, file.filename)
        
        # Determine department
        if not department:
            inferred_dept = FileParser.get_department_from_filename(file.filename)
            if inferred_dept:
                department = inferred_dept
            else:
                raise ValueError(
                    "Could not infer department from filename. "
                    "Please specify department (finance, marketing, hr, engineering, general)"
                )
        
        # Validate department
        valid_departments = ["finance", "marketing", "hr", "engineering", "general"]
        if department not in valid_departments:
            raise ValueError(
                f"Invalid department: {department}. "
                f"Valid departments: {', '.join(valid_departments)}"
            )
        
        # Determine which roles can access this document
        if department == "general":
            accessible_roles = ["finance", "marketing", "hr", "engineering", "c-level", "employee"]
        else:
            accessible_roles = [department, "c-level"]
        
        # Add to vector store
        doc_id = rag_pipeline.add_document(
            content=content,
            source=file.filename,
            department=department,
            allowed_roles=accessible_roles,
        )
        
        return UploadResponse(
            message=f"Document uploaded successfully",
            filename=file.filename,
            doc_id=doc_id,
            department=department,
            accessible_roles=accessible_roles,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/roles")
async def get_available_roles():
    """Get available roles and their test credentials."""
    return {
        "roles": {
            "finance": {
                "username": "finance_user",
                "password": "finance123",
                "access": "Financial reports, marketing expenses, equipment costs, reimbursements",
            },
            "marketing": {
                "username": "marketing_user",
                "password": "marketing123",
                "access": "Campaign performance, customer feedback, sales metrics",
            },
            "hr": {
                "username": "hr_user",
                "password": "hr123",
                "access": "Employee data, attendance, payroll, performance reviews",
            },
            "engineering": {
                "username": "engineering_user",
                "password": "engineering123",
                "access": "Technical architecture, development processes, operational guidelines",
            },
            "c-level": {
                "username": "exec_user",
                "password": "exec123",
                "access": "Full access to all company data + ability to upload documents",
            },
            "employee": {
                "username": "employee_user",
                "password": "employee123",
                "access": "General company info, policies, events, FAQs",
            },
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
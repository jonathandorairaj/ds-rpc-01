import os
from typing import List, Dict, Tuple
import requests
import json
from chromadb.config import Settings
from anthropic import Anthropic
import chromadb
from chromadb.utils import embedding_functions
from app.document_loader import DocumentLoader
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class RAGPipeline:
    """RAG pipeline with role-based access control and document upload support."""

    def __init__(self):
        # Initialize Anthropic client (uses ANTHROPIC_API_KEY env var)
        self.client = Anthropic()
        self.model = "claude-3-5-haiku-20241022"  # Cheapest good model

        # Initialize Chroma vector store
        self.client_chroma = chromadb.Client()
        self.collection = None
        self.document_metadata = {}
        self.doc_counter = 0
    
    # def __init__(self, ollama_url: str = "http://localhost:11434"):
    #     self.ollama_url = ollama_url
    #     self.model = "phi"
        
    #     # Initialize Chroma with in-memory persistence
    #     self.client = chromadb.Client()
    #     self.collection = None
    #     self.document_metadata = {}  # Track which docs go where
    #     self.doc_counter = 0  # Counter for doc IDs
        
    def initialize_vector_store(self):
        """Load documents and create vector embeddings."""
        loader = DocumentLoader()
        documents = loader.load_all_documents()
        
        if not documents:
            raise ValueError("No documents loaded. Check resources/data folder.")
        
        # Create or get collection
        self.collection = self.client_chroma.get_or_create_collection(
            name="rbac_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add documents to vector store with metadata
        for i, doc in enumerate(documents):
            doc_id = f"doc_{i}"
            self.document_metadata[doc_id] = {
                "source": doc["source"],
                "department": doc["department"],
                "allowed_roles": doc["allowed_roles"],
            }
            self.doc_counter = i + 1
            
            # Add to Chroma with content and metadata
            self.collection.add(
                ids=[doc_id],
                documents=[doc["content"]],
                metadatas=[{
                    "source": doc["source"],
                    "department": doc["department"],
                }]
            )
        
        print(f"✓ Loaded {len(documents)} documents into vector store")
    
    def add_document(
        self,
        content: str,
        source: str,
        department: str,
        allowed_roles: List[str]
    ) -> str:
        """
        Add a new document to the vector store (for uploaded files).
        
        Args:
            content: Document text content
            source: Source identifier (filename)
            department: Department this doc belongs to
            allowed_roles: List of roles that can access this doc
            
        Returns:
            doc_id: The ID of the added document
        """
        if not self.collection:
            raise RuntimeError("Vector store not initialized")
        
        # Generate new doc ID
        doc_id = f"doc_{self.doc_counter}"
        self.doc_counter += 1
        
        # Store metadata
        self.document_metadata[doc_id] = {
            "source": source,
            "department": department,
            "allowed_roles": allowed_roles,
        }
        
        # Add to Chroma
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[{
                "source": source,
                "department": department,
            }]
        )
        
        return doc_id
    
    def retrieve(self, query: str, role: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve documents relevant to query, filtered by role.
        Prioritizes department-specific docs, then general docs.
        """
        if not self.collection:
            raise RuntimeError("Vector store not initialized. Call initialize_vector_store() first.")
        
        # Query the vector store with extra results to filter
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k * 3,  # Get extra to filter by role and dept
        )
        
        # Separate department-specific and general docs
        department_specific = []
        general_docs = []
        
        doc_ids = results["ids"][0] if results["ids"] else []
        docs = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        
        for idx, (doc_id, doc, metadata) in enumerate(zip(doc_ids, docs, metadatas)):
            # Check if role has access to this document's department
            allowed_roles = self.document_metadata.get(doc_id, {}).get("allowed_roles", [])
            department = metadata.get("department", "")
            
            if role in allowed_roles or role == "c-level":
                doc_item = {
                    "content": doc,
                    "source": metadata["source"],
                    "department": department,
                }
                
                # Separate into department-specific vs general
                if department == "general":
                    general_docs.append(doc_item)
                else:
                    department_specific.append(doc_item)
        
        # Prioritize department-specific docs, then add general docs
        retrieved = department_specific[:top_k]
        
        # If not enough department-specific docs, add general docs
        if len(retrieved) < top_k:
            remaining = top_k - len(retrieved)
            retrieved.extend(general_docs[:remaining])
        
        return retrieved
    
    def generate_response(self, query: str, context: List[Dict]) -> str:
        context_str = ""
        for i, doc in enumerate(context, 1):
            context_str += f"\n[Source {i}: {doc['source']}]\n{doc['content']}\n"
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Based on these company documents, answer the question clearly and concisely.

    DOCUMENTS:
    {context_str}

    QUESTION: {query}

    ANSWER:"""
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
#     def generate_response(self, query: str, context: List[Dict]) -> str:
#         """Generate response using Ollama/Mistral with retrieved context."""
#         # Build context string
#         context_str = ""
#         for i, doc in enumerate(context, 1):
#             context_str += f"\n[Source {i}: {doc['source']}]\n{doc['content']}\n"
        
#         prompt = f"""You are a helpful company assistant. Answer the user's question based on the provided company documents.

# COMPANY DOCUMENTS:
# {context_str}

# USER QUESTION: {query}

# ANSWER:"""
        
#         try:
#             response = requests.post(
#                 f"{self.ollama_url}/api/generate",
#                 json={
#                     "model": self.model,
#                     "prompt": prompt,
#                     "stream": False,
#                 },
#                 timeout=30,
#             )
#             response.raise_for_status()
#             result = response.json()
#             return result.get("response", "Error generating response")
#         except requests.exceptions.ConnectionError:
#             return "Error: Cannot connect to Ollama. Make sure 'ollama serve' is running."
#         except Exception as e:
#             return f"Error: {str(e)}"
    
    def query(self, question: str, role: str) -> Dict:
        """Complete RAG pipeline: retrieve + generate."""
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(question, role)
        
        if not retrieved_docs:
            return {
                "answer": f"No documents found accessible to {role} role for this query.",
                "sources": [],
                "role": role,
                "query": question,
            }
        
        # Generate response
        answer = self.generate_response(question, retrieved_docs)
        
        return {
            "answer": answer,
            "sources": [doc["source"] for doc in retrieved_docs],
            "role": role,
            "query": question,
        }
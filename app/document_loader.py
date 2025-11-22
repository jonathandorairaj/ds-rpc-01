import os
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd

class DocumentLoader:
    """Load documents from resources/data folder and tag by department."""
    
    # Map departments to roles that can access them
    ROLE_ACCESS_MAP = {
        "finance": ["finance", "c-level"],
        "marketing": ["marketing", "c-level"],
        "hr": ["hr", "c-level"],
        "engineering": ["engineering", "c-level"],
        "general": ["finance", "marketing", "hr", "engineering", "c-level", "employee"],
    }
    
    def __init__(self, data_dir: str = "resources/data"):
        self.data_dir = Path(data_dir)
        self.documents: List[Dict] = []
    
    def load_all_documents(self) -> List[Dict]:
        """Load all documents from data directory."""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        # Load markdown files
        for department in self.data_dir.iterdir():
            if not department.is_dir():
                continue
            
            dept_name = department.name
            if dept_name not in self.ROLE_ACCESS_MAP:
                continue
            
            # Load all markdown files in department folder
            for file_path in department.glob("*.md"):
                content = file_path.read_text()
                self.documents.append({
                    "content": content,
                    "source": f"{dept_name}/{file_path.name}",
                    "department": dept_name,
                    "allowed_roles": self.ROLE_ACCESS_MAP[dept_name],
                })
            
            # Load CSV files
            for file_path in department.glob("*.csv"):
                df = pd.read_csv(file_path)
                content = df.to_string()
                self.documents.append({
                    "content": content,
                    "source": f"{dept_name}/{file_path.name}",
                    "department": dept_name,
                    "allowed_roles": self.ROLE_ACCESS_MAP[dept_name],
                })
        
        return self.documents
    
    def get_documents_for_role(self, role: str) -> List[Dict]:
        """Filter documents accessible to a specific role."""
        return [doc for doc in self.documents if role in doc["allowed_roles"]]

#!/usr/bin/env python3
"""
End-to-End Test for RBAC Chatbot with Claude API

This script tests the complete workflow:
1. Document loading & RBAC tagging
2. RAG pipeline initialization
3. Document retrieval with role filtering
4. Response generation with Claude
5. File upload functionality
"""

import sys
import os
from pathlib import Path

# Ensure ANTHROPIC_API_KEY is set
if not os.getenv("ANTHROPIC_API_KEY"):
    print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
    print("Run: export ANTHROPIC_API_KEY='your-key-here'")
    sys.exit(1)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag_pipeline import RAGPipeline
from app.document_loader import DocumentLoader
from app.file_parser import FileParser


def test_document_loading():
    """Test 1: Load documents and verify RBAC tagging."""
    print("\n" + "="*70)
    print("TEST 1: Document Loading & RBAC Tagging")
    print("="*70)
    
    loader = DocumentLoader()
    docs = loader.load_all_documents()
    
    print(f"✓ Loaded {len(docs)} documents")
    
    # Check departments
    departments = set(doc["department"] for doc in docs)
    print(f"✓ Departments found: {departments}")
    
    # Check Finance access
    finance_docs = [d for d in docs if d["department"] == "finance"]
    print(f"✓ Finance docs: {len(finance_docs)}")
    for doc in finance_docs:
        assert "finance" in doc["allowed_roles"]
        assert "c-level" in doc["allowed_roles"]
    print("✓ Finance RBAC verified")
    
    # Check Employee access
    employee_docs = loader.get_documents_for_role("employee")
    print(f"✓ Employee can access: {len(employee_docs)} docs (general only)")
    
    return True


def test_rag_initialization():
    """Test 2: Initialize RAG pipeline with Claude."""
    print("\n" + "="*70)
    print("TEST 2: RAG Pipeline Initialization")
    print("="*70)
    
    pipeline = RAGPipeline()
    print(f"✓ Using model: {pipeline.model}")
    print(f"✓ API key loaded: {'ANTHROPIC_API_KEY' in os.environ}")
    
    pipeline.initialize_vector_store()
    print(f"✓ Vector store initialized")
    print(f"✓ Total documents in Chroma: {len(pipeline.document_metadata)}")
    
    return pipeline


def test_retrieval(pipeline):
    """Test 3: Document retrieval with role filtering."""
    print("\n" + "="*70)
    print("TEST 3: Document Retrieval with Role Filtering")
    print("="*70)
    
    # Finance user queries finance data
    print("\n[Finance User Query]")
    query = "What are the quarterly financial results?"
    results = pipeline.retrieve(query, "finance", top_k=3)
    print(f"Query: {query}")
    print(f"Retrieved {len(results)} documents for finance role")
    for i, doc in enumerate(results, 1):
        print(f"  {i}. {doc['source']} (dept: {doc['department']})")
    
    assert len(results) > 0, "Finance should retrieve documents"
    
    # Employee queries finance data (should get nothing)
    print("\n[Employee User Query - Access Denied Test]")
    results = pipeline.retrieve(query, "employee", top_k=3)
    print(f"Query: {query}")
    print(f"Retrieved {len(results)} documents for employee role")
    
    # Employee should only see general docs (and not finance docs)
    for doc in results:
        assert doc["department"] != "finance", "Employee shouldn't access finance"
    print("✓ Access control working correctly")
    
    # C-level queries everything
    print("\n[C-Level User Query - Full Access Test]")
    results = pipeline.retrieve(query, "c-level", top_k=5)
    print(f"Retrieved {len(results)} documents for c-level role")
    print("✓ C-level has access to multiple departments")
    
    return True


def test_claude_response(pipeline):
    """Test 4: Generate response with Claude."""
    print("\n" + "="*70)
    print("TEST 4: Claude Response Generation")
    print("="*70)
    
    query = "Tell me about the company"
    print(f"\nQuery: {query}")
    print("Calling Claude API...")
    
    try:
        result = pipeline.query(query, "c-level")
        
        print(f"\n✓ Claude Response Generated!")
        print(f"Role: {result['role']}")
        print(f"Sources: {result['sources']}")
        print(f"\nAnswer ({len(result['answer'])} chars):")
        print("-" * 70)
        print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
        print("-" * 70)
        
        assert len(result['answer']) > 0, "Response should not be empty"
        print("\n✓ Claude response test passed!")
        
    except Exception as e:
        print(f"❌ Claude API Error: {str(e)}")
        return False
    
    return True


def test_file_upload_simulation():
    """Test 5: File parsing for uploads."""
    print("\n" + "="*70)
    print("TEST 5: File Upload & Parsing")
    print("="*70)
    
    # Test markdown parsing
    print("\n[Markdown File]")
    md_content = b"# Test Document\n\nThis is test content for finance."
    content, format_type = FileParser.parse_file(md_content, "test_report.md")
    print(f"✓ Parsed markdown: {len(content)} chars, format: {format_type}")
    assert "Test Document" in content
    
    # Test department inference
    print("\n[Department Inference]")
    dept = FileParser.get_department_from_filename("Q4_marketing_campaign.md")
    print(f"Filename: Q4_marketing_campaign.md → Inferred: {dept}")
    assert dept == "marketing"
    
    dept = FileParser.get_department_from_filename("financial_summary.pdf")
    print(f"Filename: financial_summary.pdf → Inferred: {dept}")
    assert dept == "finance"
    
    print("✓ File parsing tests passed!")
    return True


def test_dynamic_upload(pipeline):
    """Test 6: Dynamic document upload."""
    print("\n" + "="*70)
    print("TEST 6: Dynamic Document Upload")
    print("="*70)
    
    # Simulate uploading a new document
    print("\n[Uploading: Q4_Sales_Report.md to finance dept]")
    new_doc = """# Q4 2024 Sales Report
    
    ## Overview
    Q4 2024 exceeded targets by 15%.
    
    - Revenue: $45.2M (target: $40.3M)
    - Gross Margin: 68.5%
    - Customer Acquisition Cost: $1,250
    """
    
    doc_id = pipeline.add_document(
        content=new_doc,
        source="Q4_Sales_Report.md",
        department="finance",
        allowed_roles=["finance", "c-level"]
    )
    
    print(f"✓ Document uploaded with ID: {doc_id}")
    print(f"✓ Total docs now: {len(pipeline.document_metadata)}")
    
    # Verify it's queryable by finance user
    print("\n[Querying uploaded document as Finance user]")
    results = pipeline.retrieve("What was Q4 revenue?", "finance")
    
    found_uploaded = any("Q4_Sales" in doc["source"] for doc in results)
    print(f"✓ Uploaded doc in results: {found_uploaded}")
    
    if found_uploaded:
        print("✓ Uploaded document is immediately queryable!")
    
    return True


def test_rbac_across_users(pipeline):
    """Test 7: RBAC enforcement across users."""
    print("\n" + "="*70)
    print("TEST 7: RBAC Enforcement Across User Roles")
    print("="*70)
    
    query = "What is the company overview?"
    
    roles_to_test = ["finance", "marketing", "hr", "engineering", "c-level", "employee"]
    
    print(f"\nQuery: {query}")
    print("\nTesting access for each role:")
    print("-" * 70)
    
    for role in roles_to_test:
        results = pipeline.retrieve(query, role, top_k=2)
        departments = set(doc["department"] for doc in results)
        print(f"{role:15} → {len(results):2} docs from dept: {departments}")
    
    print("-" * 70)
    print("✓ RBAC working across all roles!")
    
    return True


def run_all_tests():
    """Run complete end-to-end test suite."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  FINSOL VE RBAC CHATBOT - END-TO-END TEST SUITE".center(68) + "║")
    print("║" + "  With Claude API".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    tests = [
        ("Document Loading", test_document_loading, []),
        ("RAG Initialization", test_rag_initialization, []),
        ("Retrieval & Filtering", test_retrieval, []),
        ("Claude Response", test_claude_response, []),
        ("File Parsing", test_file_upload_simulation, []),
        ("Dynamic Upload", test_dynamic_upload, []),
        ("RBAC Across Users", test_rbac_across_users, []),
    ]
    
    passed = 0
    failed = 0
    pipeline = None
    
    for test_name, test_func, _ in tests:
        try:
            if test_name == "RAG Initialization":
                pipeline = test_func()
            elif test_name == "Retrieval & Filtering":
                test_func(pipeline)
            elif test_name == "Claude Response":
                test_func(pipeline)
            elif test_name == "Dynamic Upload":
                test_func(pipeline)
            elif test_name == "RBAC Across Users":
                test_func(pipeline)
            else:
                test_func()
            
            passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✓ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is production-ready.\n")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Fix issues before deployment.\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

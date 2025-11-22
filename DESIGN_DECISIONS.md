# Design Decisions

This document explains the "why" behind architectural choices. Each decision includes tradeoffs and alternatives considered.

## 1. Vector Database: Chroma vs Alternatives

### Decision: Use Chroma (in-memory vector database)

### Alternatives Considered

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|--------|
| **Chroma** | Local, instant, free, auto-embed | In-memory only, single-machine | ✅ CHOSEN |
| **Pinecone** | Cloud, scalable, managed | Costs $$$, needs API key, overkill | ❌ Too expensive |
| **Weaviate** | Rich features, flexible | Complex setup, Docker required | ❌ Too complex |
| **FAISS** | Fast, local | No auto-embedding, manual setup | ❌ More work |
| **Elasticsearch** | Powerful, mature | Heavy, not for vectors | ❌ Wrong tool |

### Rationale

**For this portfolio project:**
- ✅ Zero setup time (instant local DB)
- ✅ No API keys or authentication needed
- ✅ Automatic embedding generation
- ✅ Fast semantic search (cosine similarity)
- ✅ Perfect for prototyping

**Trade-off:**
- ❌ In-memory only (data lost on restart)
- ❌ Single machine (no distributed search)

**For Production:**
Would migrate to Pinecone/Weaviate when scaling beyond 100k documents or needing multi-region support.

---

## 2. LLM Choice: Claude Haiku vs Alternatives

### Decision: Use Claude Haiku via Anthropic API

### Comparison Table

| Model | Cost | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **Claude Haiku** | $0.25/$1.25 | 2-3s | 9/10 | ✅ CHOSEN |
| **GPT-4o Mini** | $0.15/$0.60 | 1-2s | 8/10 | Cost-focused |
| **Gemini Flash** | $0.075/$0.30 | 1-2s | 7/10 | Speed-focused |
| **Mistral 7B** | FREE (local) | 3-5s | 6/10 | Budget |
| **Llama 2 70B** | FREE (local) | 10-15s | 7/10 | Local-only |

### Rationale

**Why Claude Haiku over alternatives:**

1. **Quality** - Excellent understanding of context, minimal hallucinations
2. **Reliability** - Anthropic's focus on safety
3. **Speed** - 2-3 sec response time (acceptable UX)
4. **Cost** - $0.25-1.25 per 1M tokens (cheap for RAG)
5. **Reasoning** - Excels at document-grounded tasks

**Trade-offs:**

| Pro | Con |
|-----|-----|
| Best quality answers | Not the cheapest (GPT-4o mini is $0.15) |
| Safest (low hallucinations) | Slightly slower than fastest models |
| Great at context understanding | Requires API key (not local) |

**Why not local models (Phi/Mistral)?**
- Phi: Small model = lower quality answers
- Mistral: Requires Ollama = extra setup
- Neither optimized for RAG tasks

**Why not cheaper models?**
- **Gemini Flash** ($0.075): Lower quality, sometimes misses context
- **GPT-4o Mini** ($0.15): Good option, comparable quality
- Claude Haiku: Slightly more expensive but more reliable for business use

### Production Decision
For high-volume usage (10k+ queries/day), would consider:
- OpenAI's batch API (50% discount)
- Multi-model routing (use cheapest appropriate model per query)
- Semantic caching (store similar questions' results)

---

## 3. Authentication: HTTP Basic vs OAuth/JWT

### Decision: Use HTTP Basic Authentication

### Why HTTP Basic?

| Aspect | HTTP Basic | OAuth2 | JWT | API Key |
|--------|-----------|--------|-----|---------|
| Setup | Instant | Complex | Medium | Simple |
| Security | OK (over HTTPS) | Excellent | Good | Good |
| Stateless | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Token Expiry | N/A | ✅ Yes | ✅ Yes | No |
| Token Refresh | N/A | ✅ Yes | ✅ Yes | No |
| Best For | **Demos** | Enterprise | Modern APIs | Service-to-Service |

### Rationale

**For Portfolio Project:**
- ✅ HTTP Basic is **instantly understandable**
- ✅ **Zero setup** (no token servers, no refresh logic)
- ✅ **Works everywhere** (cURL, Python, browsers)
- ✅ **Demonstrates understanding** of basic auth concepts
- ✅ **Focus on RAG, not auth complexity**

**Trade-off:**
- ❌ Not suitable for public APIs
- ❌ Credentials sent with every request
- ❌ No token expiry
- ❌ No refresh mechanism

### For Production

Would implement OAuth2 + JWT because:
- Users can login once, get token
- Token can expire automatically
- Better for mobile apps & SPAs
- Industry standard for web apps

### Code Evidence

```python
# HTTP Basic (current, simple)
@app.get("/protected")
async def protected(credentials: HTTPBasicCredentials = Depends(security)):
    # credentials.username, credentials.password
    
# OAuth2 would be (production)
@app.get("/protected")
async def protected(token: str = Depends(oauth2_scheme)):
    # verify_token(token)
```

---

## 4. RBAC Enforcement: Retrieval-Time vs Storage-Time

### Decision: Enforce RBAC at Retrieval Time

### Two Approaches

#### Approach A: Storage-Time RBAC (Not Chosen)
```
Upload finance doc
    ↓
Encrypt with finance role key
    ↓
Store encrypted in DB
    ↓
Query: decrypt only if user is finance
```

**Pros:**
- Stronger security (encryption)
- Immutable permissions at storage

**Cons:**
- Complex encryption/decryption
- Hard to share general documents
- Difficult to change permissions later
- Performance overhead

#### Approach B: Retrieval-Time RBAC (Chosen) ✅
```
Upload finance doc with metadata: allowed_roles=["finance", "c-level"]
    ↓
Store unencrypted in DB
    ↓
Query: filter by role BEFORE returning
```

**Pros:**
- ✅ Simple metadata tagging
- ✅ Easy to share general docs
- ✅ Easy permission changes (just update metadata)
- ✅ Better performance
- ✅ Easier to audit

**Cons:**
- Weaker security IF database is breached
  - (But encryption also wouldn't help if DB is breached + key is compromised)

### Trade-Off Analysis

| Scenario | Approach A | Approach B |
|----------|-----------|-----------|
| Database fully compromised | Encrypted (safer) | Plaintext (worse) |
| Need to change permissions | Hard (re-encrypt) | Easy (update metadata) |
| Performance | Slower (decrypt each query) | Faster (metadata lookup) |
| Complexity | High (encryption) | Low (simple tagging) |
| Share general docs | Hard (multiple keys) | Easy (everyone has access) |

### Verdict

**For portfolio project:** Retrieval-time makes sense
- Simpler code to explain in interviews
- Focuses on RBAC logic, not encryption
- Better UX (dynamic permissions)

**For sensitive data (healthcare, finance):** Would use storage-time encryption
- Combined with retrieval-time filtering
- Defense in depth

---

## 5. Department Inference from Filename

### Decision: Use Keyword Matching for Department Auto-Detection

### Why Not Alternatives?

| Method | Pros | Cons | Verdict |
|--------|------|------|--------|
| **Keyword Matching** | Fast, simple, explainable | Simple heuristic, false positives | ✅ CHOSEN |
| **ML Classifier** | Accurate, learns patterns | Needs training data, complex | ❌ Overkill |
| **LLM Classification** | Excellent accuracy | Costs $$, slow, overkill | ❌ Overkill |
| **User Manual** | Always correct | Bad UX, requires user input | ❌ Fallback only |

### Implementation

```python
# Simple, explainable keyword matching
keywords = {
    "finance": ["finance", "financial", "quarterly", "revenue", "expense"],
    "marketing": ["marketing", "campaign", "sales", "customer"],
    "hr": ["hr", "employee", "payroll", "attendance"],
}

for dept, words in keywords.items():
    if any(word in filename.lower() for word in words):
        return dept
```

### Examples

| Filename | Inferred | Reason |
|----------|----------|--------|
| `Q4_financial_report.md` | finance | Contains "financial" |
| `marketing_Q4_results.pdf` | marketing | Contains "marketing" |
| `employee_handbook.md` | hr | Contains "employee" |
| `random_document.md` | None (ask user) | No keywords matched |

### Why This Approach?

1. **User-friendly** - Most files have obvious department in name
2. **Explainable** - Can show user why system chose a department
3. **Fallback** - If inference fails, ask user (no bad guess)
4. **Fast** - String matching is instant
5. **Interview-friendly** - Simple logic to explain

---

## 6. Document Chunking Strategy

### Decision: No Chunking (Pass Entire Document to Chroma)

### Why No Chunking?

Current approach:
```python
# Entire document is one record
self.collection.add(
    ids=[doc_id],
    documents=[entire_content],  # Full document
    metadatas=[metadata]
)
```

### Why Not Chunk Documents?

| Approach | Pros | Cons | Current? |
|----------|------|------|----------|
| **No Chunking** | Simple, context-aware | Large docs = slower embedding | ✅ YES |
| **Fixed Size Chunks** | Faster embedding | Breaks context at boundaries | ❌ NO |
| **Semantic Chunks** | Preserves meaning | Complex, needs ML | ❌ NO |
| **Paragraph Chunks** | Good balance | Still might split coherent thought | ❌ NO |

### Rationale

**For portfolio project:**
- Documents are ~3-10KB (small)
- Chroma handles them fine
- Simpler to explain
- Better context preservation

**When to Chunk (Production):**
- Documents > 100KB
- Need faster retrieval time
- Dealing with 100k+ documents

---

## 7. Streamlit vs React/Vue for Frontend

### Decision: Use Streamlit

### Comparison

| Aspect | Streamlit | React | Vue | FastAPI Only |
|--------|-----------|-------|-----|--------------|
| Setup | 1 command | ~1 hour | ~1 hour | Need separate UI |
| Development | Minutes | Hours | Hours | Web dev knowledge |
| Learning Curve | Easy (Python) | Hard (JS/React) | Medium | N/A |
| Customization | Limited | Unlimited | Unlimited | Full control |
| Best For | **Demos** | Production apps | Production apps | Backend-only |

### Rationale

**For portfolio project:**
- ✅ Built in Python (no JS needed)
- ✅ RAD (Rapid Application Development)
- ✅ Session management built-in
- ✅ Shows focus on backend/ML, not frontend
- ✅ Deploym easily (Streamlit Cloud)

**Trade-off:**
- ❌ Limited customization
- ❌ Slower than React
- ❌ Not suitable for complex UIs

**For Production:**
Would use React + TypeScript for:
- Professional UX
- Complex interactions
- Mobile support
- Better performance

---

## 8. Testing Strategy: Coverage and Philosophy

### Decision: 40+ Tests Across 3 Levels

### Testing Pyramid

```
        ▲
       / \
      /   \  End-to-End Tests (7 tests)
     /-----\
    /       \  Integration Tests (6 tests)
   /         \
  /-----------\
 /             \ Unit Tests (25+ tests)
/_____________\
```

### Why This Structure?

| Test Type | Cost | Speed | Value | Quantity |
|-----------|------|-------|-------|----------|
| **Unit** | Low | Fast | High (catch bugs early) | 25+ |
| **Integration** | Medium | Slow | High (catch component issues) | 6 |
| **E2E** | High | Slow | Medium (catch user workflows) | 7 |

### Philosophy

1. **Unit Tests** - Test each function in isolation
2. **Integration Tests** - Test components together
3. **E2E Tests** - Test complete user flows

### Examples

```python
# UNIT TEST - Test retrieval filtering logic
def test_retrieve_respects_role_access():
    pipeline = RAGPipeline()
    results = pipeline.retrieve(query, role="marketing")
    assert all(doc["department"] != "finance" for doc in results)

# INTEGRATION TEST - Test API endpoint with database
def test_query_endpoint_with_valid_auth():
    response = test_client.post(
        "/query",
        json={"question": "..."},
        headers=auth_header
    )
    assert response.status_code == 200

# E2E TEST - Test complete workflow
def test_full_workflow_finance_user():
    # Login
    # Query
    # Verify response
    # Logout
```

---

## 9. Error Handling: Fail-Safe vs Fail-Open

### Decision: Fail-Safe (Deny by Default)

### Two Philosophies

#### Fail-Safe: "Better to deny than leak"
```python
# If RBAC check fails → Deny access
if role not in allowed_roles:
    raise HTTPException(403, "Forbidden")
return document
```

#### Fail-Open: "Better to allow than error"
```python
# If RBAC check fails → Allow access
try:
    if role not in allowed_roles:
        raise HTTPException(403)
except:
    return document  # On error, allow
```

### Rationale

**Chose Fail-Safe because:**
- ✅ Security: Better to deny incorrectly than allow incorrectly
- ✅ Audit: Easy to detect why access was denied
- ✅ Testing: Easier to test security edge cases

**Finance example:**
- Fail-Safe: Finance user can't see Marketing data (safe)
- Fail-Open: Finance user might see Marketing data (risky)

---

## 10. Claude vs Ollama: When to Switch

### Current: Phi/Ollama (Local)
- Cost: FREE
- Quality: 6/10 (good but generic answers)
- Setup: Local server needed
- Speed: Slower

### Alternative: Claude API
- Cost: ~$1/month for portfolio testing
- Quality: 9/10 (excellent, grounded answers)
- Setup: API key only
- Speed: Faster

### Decision Made

**For this project:** Switched to Claude API because:
- ✅ Response quality matters for portfolio
- ✅ Cost is negligible (~$1-2)
- ✅ Interview demonstrates understanding of tradeoffs
- ✅ No local setup headaches

**Matrix:**

| Factor | Ollama (Phi) | Claude API |
|--------|-------------|-----------|
| Cost | FREE | $1-2/month |
| Quality | 6/10 | 9/10 |
| Setup | Local server | API key |
| Interview Value | Good | **Better** |

---

## 11. .env vs Hardcoded vs Config File

### Decision: .env File with Python-Dotenv

### Three Approaches

| Approach | Security | Convenience | Scalability |
|----------|----------|-------------|-------------|
| **Hardcoded** | ❌ Terrible | ✅ Easy | ❌ Bad |
| **.env file** | ✅ Good | ✅ Easy | ✅ Good |
| **Config server** | ✅ Excellent | ❌ Complex | ✅ Excellent |

### Chosen: .env File

```
.env (local, not in git)
.env.example (template in git)
```

**Why:**
- ✅ Secure (secret not committed)
- ✅ Simple (one file)
- ✅ Standard practice
- ✅ Others can copy .env.example

**For production:**
- Use environment variables on deployment
- Or use config management (AWS Secrets Manager, HashiCorp Vault)

---

## Summary Table

| Decision | Choice | Alternative | Why |
|----------|--------|-------------|-----|
| Vector DB | Chroma | Pinecone | Simple, free, local |
| LLM | Claude Haiku | Ollama | Better quality, worth $1 |
| Auth | HTTP Basic | OAuth2 | Simple, understandable |
| RBAC | Retrieval-time | Storage-time | Simpler, more flexible |
| Department | Keyword match | ML classifier | Good enough, faster |
| Chunking | No chunking | Fixed chunks | Documents are small |
| Frontend | Streamlit | React | RAD, Python-focused |
| Testing | 40+ tests | No tests | Shows quality practices |
| Error | Fail-safe | Fail-open | Security > availability |
| Config | .env file | Hardcoded | Secure, simple |

---

## Future Improvements & When to Implement

### Immediate (< 1 hour)
- [ ] Add logging
- [ ] Add more detailed error messages
- [ ] Document deployment options

### Short Term (1-4 hours)
- [ ] Implement caching (Redis)
- [ ] Add rate limiting
- [ ] User preference storage (PostgreSQL)

### Medium Term (4-16 hours)
- [ ] OAuth2 authentication
- [ ] Document versioning
- [ ] Role hierarchy
- [ ] Admin dashboard

### Long Term (16+ hours)
- [ ] Fine-tuned embeddings
- [ ] Knowledge graph integration
- [ ] Multi-turn conversations with memory
- [ ] Full-text search
- [ ] Real-time document sync

---

**These decisions balance simplicity, security, and portfolio impact for a demo project destined for production.**

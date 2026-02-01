# Student Facts System

This document explains how student facts are stored, managed, and used in Nihongo Dojo.

---

## Overview

Student facts are pieces of long-term memory about the student that help the AI tutor personalize lessons. Facts are stored as rows in a SQLite table and can be managed by:

1. **The Listener agent** - via the `manage_student_facts` tool in background after each conversation turn
2. **Memory compaction** - automatically extracts facts from archived conversations
3. **The user** - via the frontend UI (manual CRUD operations)

**Note:** The system uses a two-agent architecture. The Tutor agent (which responds to the user) has no tools - it focuses purely on teaching. The Listener agent runs in the background after each message to extract and manage facts.

---

## Data Model

**Table:** `student_facts`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-incrementing unique identifier |
| `content` | Text | The fact itself (e.g., "Likes anime, especially Naruto") |
| `source` | String(20) | Who created it: `tutor`, `compaction`, or `manual` |
| `created_at` | DateTime | When the fact was created |
| `updated_at` | DateTime | When the fact was last modified |

**File:** `backend/app/db/models.py`

```python
class StudentFact(Base):
    __tablename__ = "student_facts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    source = Column(String(20), default="tutor")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

---

## How Facts Appear in the AI Prompt

Facts are injected into the system prompt with their IDs visible:

```
## About This Student
- [1] Learning Japanese for travel to Tokyo
- [2] Likes anime, especially Naruto (favorite character: Kakashi)
- [3] Works as a software engineer
- [4] Prefers conversational practice over textbook exercises
```

The AI sees the IDs in brackets, allowing it to reference specific facts when editing or deleting.

**File:** `backend/app/core/context_builder.py`

```python
async def fetch_student_facts() -> List[Dict]:
    """Fetch all student facts from the database."""
    # Returns [{"id": 1, "content": "..."}, ...]

def format_student_facts(facts: List[Dict]) -> str:
    """Format student facts as a list with IDs."""
    if not facts:
        return "(No information recorded yet)"
    return "\n".join(f"- [{f['id']}] {f['content']}" for f in facts)
```

---

## AI Tool: `manage_student_facts`

The **Listener agent** uses this tool to add, edit, or delete facts in the background after each conversation turn.

**File:** `backend/app/core/tools.py`

**Used by:** `backend/app/services/listener_service.py`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | `add`, `edit`, or `delete` |
| `content` | string | For add/edit | The fact text (new fact or updated text) |
| `fact_id` | integer | For edit/delete | The ID of the fact to modify |

### Actions

**Add a new fact:**
```json
{
  "action": "add",
  "content": "Enjoys discussing travel experiences"
}
```
→ Returns: `"Added fact [#5]: Enjoys discussing travel experiences"`

**Edit an existing fact:**
```json
{
  "action": "edit",
  "fact_id": 2,
  "content": "Loves anime, especially Naruto and One Piece"
}
```
→ Returns: `"Updated fact [#2]: 'Likes anime, especi...' → 'Loves anime, especi...'"`

**Delete a fact:**
```json
{
  "action": "delete",
  "fact_id": 3
}
```
→ Returns: `"Deleted fact [#3]: Works as a software engineer"`

### Error Handling

| Error | Response |
|-------|----------|
| Missing `fact_id` for edit/delete | `"Error: 'fact_id' is required for edit action"` |
| Fact ID not found | `"Error: No fact found with ID 99"` |
| Duplicate fact (exact match) | `"Fact already exists (duplicate not added)"` |
| Missing content for add/edit | `"Error: 'content' is required for add action"` |

---

## Memory Compaction Integration

When old messages are compacted, the compaction AI may extract new student facts.

**File:** `backend/app/services/memory_service.py`

### Flow

1. Compaction AI analyzes 10 oldest non-archived messages
2. Returns JSON with `new_summary` and optionally `new_student_facts`
3. If facts found, they're parsed (newline/bullet-separated) and inserted:

```python
async def _add_student_facts(self, new_facts: str) -> None:
    """Add extracted facts to the student_facts table."""
    fact_lines = [
        line.strip().lstrip("- ").lstrip("* ").strip()
        for line in new_facts.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]

    for fact_text in fact_lines:
        # Check for duplicate before adding
        if not existing:
            session.add(StudentFact(content=fact_text, source="compaction"))
```

Facts from compaction are tagged with `source="compaction"` for auditing.

---

## REST API Endpoints

The frontend uses these endpoints to display and manage facts.

**File:** `backend/app/api/notes.py`

### GET /api/notes
Returns all facts formatted as a bullet list (backwards compatible with old UI).

**Response:**
```json
{
  "content": "- [1] Likes anime\n- [2] Learning for travel"
}
```

### GET /api/notes/facts
Returns all facts as a structured list.

**Response:**
```json
{
  "facts": [
    {"id": 1, "content": "Likes anime", "source": "tutor", "created_at": "2024-01-15T10:30:00"},
    {"id": 2, "content": "Learning for travel", "source": "compaction", "created_at": "2024-01-15T11:00:00"}
  ]
}
```

### POST /api/notes/facts
Add a new fact manually.

**Request:**
```json
{"content": "Prefers morning study sessions"}
```

**Response:**
```json
{"id": 3, "content": "Prefers morning study sessions", "source": "manual"}
```

### PUT /api/notes/facts/{id}
Update a fact by ID.

**Request:**
```json
{"content": "Updated fact text"}
```

**Response:**
```json
{"message": "Fact 1 updated", "content": "Updated fact text"}
```

### DELETE /api/notes/facts/{id}
Delete a fact by ID.

**Response:**
```json
{"message": "Fact 1 deleted"}
```

### GET /api/notes/token-count
Estimate token count of all facts (for context budget monitoring).

**Response:**
```json
{"token_count": 150}
```

---

## Source Tracking

Facts are tagged by their origin:

| Source | Created By |
|--------|------------|
| `listener` | Listener agent (background task after each conversation turn) |
| `compaction` | Memory compaction extraction |
| `manual` | User via frontend UI or API |

**Note:** Legacy facts may still have `source="tutor"` from before the two-agent architecture was introduced.

This allows for auditing and potentially different handling (e.g., showing source in admin view).

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/db/models.py` | `StudentFact` SQLAlchemy model |
| `backend/app/core/agents.py` | Listener system prompt with fact extraction instructions |
| `backend/app/core/tools.py` | `manage_student_facts` tool definition and execution |
| `backend/app/core/context_builder.py` | Fetches and formats facts for both agent prompts |
| `backend/app/services/listener_service.py` | Background Listener agent for fact extraction |
| `backend/app/services/memory_service.py` | Compaction fact extraction |
| `backend/app/api/notes.py` | REST API endpoints |

---

## Database Queries

**View all facts:**
```sql
SELECT id, content, source, created_at FROM student_facts ORDER BY created_at;
```

**Count by source:**
```sql
SELECT source, COUNT(*) FROM student_facts GROUP BY source;
```

**Find duplicates:**
```sql
SELECT content, COUNT(*) as cnt FROM student_facts
GROUP BY content HAVING cnt > 1;
```

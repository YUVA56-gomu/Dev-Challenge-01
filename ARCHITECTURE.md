# Sathi (साथी) — System Architecture & Technical Specifications

This document outlines the architectural blueprints, data models, retrieval pipelines, and design patterns powering **Sathi (साथी) — Personal AI CA Companion**.

---

## 1. High-Level Architecture Overview

Sathi employs a hybrid local-first architecture prioritizing privacy, low latency, and zero token costs for continuous 10–12 hour daily CA study sessions:

```
                            [React 19 + Vite Frontend]
                                (Port 5173 / Localhost)
                                         │
                         REST / JSON / Streaming Audio
                                         │
                                         ▼
                            [FastAPI Backend Gateway]
                                (Port 8000 / Uvicorn)
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
      [Query Router & RAG]     [AI Provider & Engine]    [Repository & Storage]
                 │                       │                       │
      ┌──────────┴──────────┐            │             ┌─────────┴─────────┐
      │                     │            │             │                   │
  [FTS5 Lexical]     [sqlite-vec Dense]  │        [SQLite RDBMS]   [Audio SHA-256 Cache]
   (BM25 Search)      (FastEmbed 384d)   │         (sathi.db)          (Disk wav/mp3)
      └──────────┬──────────┘            │             │
                 ▼                       ▼             ▼
       [Hybrid RRF Merger]     [Ollama Gemma 2 2B] [Syllabus & Memory Providers]
                 │              (NVIDIA RTX VRAM)  (Local / Backboard.io Adapter)
                 ▼                       │
         [Grounded Prompt] ──────────────┘
```

---

## 2. Phase 2A — Scalable CA Syllabus Data Model

The syllabus model replaces flat mock arrays with an official, relational hierarchy aligned with the ICAI New Scheme of Education and Training (2024–2025):

```
CA Track
  └── CA Stages (`ca_stages`)
       ├── Foundation (4 Papers)
       ├── Intermediate (Group 1 & 2, 6 Papers)
       └── Final (Group 1 & 2, 6 Papers)
            └── Groups (`ca_groups`)
                 └── Papers (`ca_papers`)
                      └── Modules (`ca_modules`)
                           └── Chapters (`ca_chapters`)
                                └── Topics (`ca_topics`)
```

### Relational Schema Entities (`sathi.db`)

1. **`ca_stages`**:
   - `id`: Unique stage identifier (`stage_foundation`, `stage_intermediate`, `stage_final`)
   - `name`: Full stage name
   - `code`: Stage abbreviation (`FOUNDATION`, `INTER`, `FINAL`)
   - `total_papers`: Numeric count of papers in stage
   - `description`: Educational curriculum overview

2. **`ca_groups`**:
   - `id`: Group identifier (`grp_inter_1`, `grp_inter_2`, etc.)
   - `stage_id`: Foreign key reference to `ca_stages`
   - `name`: Formal group title
   - `code`: Group code (`G1`, `G2`)

3. **`ca_papers`**:
   - `id`: Paper identifier
   - `group_id`: Foreign key reference to `ca_groups`
   - `paper_num`: Official paper sequence (1 to 6)
   - `name`: Paper title (e.g., *Advanced Accounting*, *Corporate and Other Laws*, *Taxation*)
   - `code`: Official code (`PAPER_1`, `PAPER_2`, etc.)

4. **`ca_modules`**:
   - `id`: Module identifier
   - `paper_id`: Foreign key reference to `ca_papers`
   - `module_num`: Sequential module number according to ICAI physical study volume
   - `name`: Module theme (e.g., *Company Law*, *GST*, *Standards on Auditing*)

5. **`ca_chapters`**:
   - `id`: Chapter identifier
   - `module_id`: Foreign key reference to `ca_modules`
   - `chapter_num`: Sequential chapter index
   - `title`: Chapter title
   - `statutory_reference`: Statutory provision or Standard (e.g., *Sections 139 to 148, Companies Act 2013*, *AS 10*)
   - `status`: Lifecycle enum (`not_started`, `in_progress`, `completed`, `needs_revision`)
   - `confidence_score`: 1 to 5 integer rating
   - `revision_count`: Cumulative revision cycle count
   - `last_studied` / `last_revised`: Timestamps
   - `notes`: Markdown revision notes
   - `weak_areas`: Specific adjustments or clauses requiring remediation

6. **`ca_topics`**:
   - `id`: Topic identifier
   - `chapter_id`: Foreign key reference to `ca_chapters`
   - `topic_num`: Topic sequence
   - `title`: Topic heading
   - `statutory_section`: Precise section or paragraph (e.g., *Section 17(5) CGST Act 2017*, *SA 200 para 11*)
   - `learning_objective`: Specific pedagogical objective
   - `estimated_minutes`: Recommended time investment
   - `exam_weightage`: Weightage tier (`High`, `Medium`, `Low`)
   - `status` & `confidence_score`: Topic-level granularity

---

## 3. Phase 2B & 2C & 2D — Hybrid Local RAG Engine

Sathi eliminates cloud vector database dependencies (such as Pinecone, Qdrant Cloud, or Weaviate) in favor of a zero-cost, privacy-preserving, embedded local retrieval architecture.

### Directory Structure
```
backend/app/core/rag/
├── document_store.py   # Document ingestion, ICAI source verification & metadata
├── vector_store.py     # sqlite-vec dense index + FTS5 BM25 lexical index + RRF merger
└── query_router.py     # Fast Path vs Deep Path classifier
```

### Retrieval Pipeline

1. **Ingestion & Metadata Preservation:**
   - Every ingested chunk maintains immutable source provenance:
     - `doc_name`: Official publication title (e.g., *ICAI Study Material - Paper 4: Taxation*)
     - `source`: Authoritative issuing body (*ICAI Board of Studies*)
     - `edition`: Curriculum year (e.g., *2024-2025 Edition*)
     - `stage` / `paper` / `chapter`: Curriculum taxonomy
     - `statutory_section`: Section number (e.g., *Section 17(5) CGST Act 2017*)
     - `page_num`: Physical textbook page number (e.g., *Page 142*)

2. **Dual-Index Architecture:**
   - **Lexical Index (SQLite FTS5):** Full-text search with BM25 ranking. Critical for exact legal citations (e.g., `"Section 17(5)"`, `"Section 139"`, `"AS 10"`, `"SA 200"`).
   - **Dense Semantic Index (`sqlite-vec` + `FastEmbed`):**
     - Embedding Model: `BAAI/bge-small-en-v1.5` (quantized ONNX runtime, 384 dimensions).
     - Distance Metric: Cosine / L2 distance.
     - Handles semantic queries (e.g., *"Why can't we claim input tax credit on employee insurance?"*).

3. **Reciprocal Rank Fusion (RRF):**
   Lexical and semantic ranks are merged using standard RRF:
   $$RRF(d) = \sum_{m \in \{lexical, semantic\}} \frac{1}{60 + r_m(d)}$$
   This guarantees that both precise section matches and conceptual synonyms surface at the top of retrieved context.

---

## 4. Phase 2N — Intelligent Query Routing

Not every prompt requires executing vector embeddings and full-text searches. Sathi employs intelligent query routing:

```
                          Incoming Student Message
                                     │
                                     ▼
                      [Intelligent Query Classifier]
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
     [FAST PATH]                                          [DEEP PATH]
  - Greetings ("Hey Sathi")                             - Statutory questions ("Section 17(5)")
  - Emotional check-ins ("Feeling anxious")             - Accounting standards ("AS 10", "SA 200")
  - Casual motivation / scheduling                      - Active chapter context passed from UI
  - General conversational follow-ups                   - "Why can't we claim ITC on this?"
           │                                                   │
           ▼                                                   ▼
  Direct Gemma 2 2B                                    Authoritative Hybrid RAG
   (~150ms latency)                                    + Grounded Gemma Prompt
                                                       + Source Citations
```

---

## 5. Phase 2E & 2F — Grounded Gemma Prompting & Source Citations

When a query is routed to the Deep Path, Sathi composes a multi-part prompt enforcing strict epistemic boundaries:

1. **System Instructions:** Persona, pedagogical style, exam relevance.
2. **Student Progress & Memory Context:** Active stage, recent struggles, personal preferences.
3. **Recent Conversation:** Multi-turn dialogue history.
4. **Retrieved Authoritative Context:** Verbatim excerpts from ICAI study material with exact citations.
5. **Anti-Hallucination Mandate:**
   - Never fabricate section numbers or rule provisions.
   - If retrieved material does not establish the answer, explicitly state: *"The available ICAI study material does not establish the answer to this question."*
   - Never claim unverified generated assumptions are official ICAI rules.

In the user interface, verified responses display an interactive **`Source Verified`** badge. Clicking it reveals the issuing authority, document name, statutory section, page number, and authoritative text quote.

---

## 6. Phase 2J — Semantic Memory Layer & Provider Pattern

Sathi introduces an extensible memory architecture separating deterministic progress from semantic/episodic memory:

### Interface: `MemoryProvider`
```python
class MemoryProvider(ABC):
    def save_memory(self, student_id: str, memory_text: str, memory_type: str = "preference") -> str: ...
    def retrieve_memory(self, student_id: str, query: str = "", limit: int = 5) -> List[Dict]: ...
    def summarize_memory(self, student_id: str) -> str: ...
    def delete_memory(self, memory_id: str) -> bool: ...
```

### Implementations:
1. **`LocalMemoryProvider` (Default):**
   - Stores memories in the `semantic_memories` SQLite table.
   - Zero external network requests; complete on-device privacy.
2. **`BackboardMemoryProvider` (Optional Adapter):**
   - Activates only when `BACKBOARD_API_KEY` is present in the environment.
   - Gracefully falls back to `LocalMemoryProvider` on network failure, timeout, or DNS resolution errors.

### State Separation:
- **Deterministic State (SQLite):** Chapter completion, task status, streaks, confidence scores, revision dates, syllabus hierarchy.
- **Semantic Memory (Provider):** Epistemic preferences (*"Student prefers examples before statutory text"*), historical struggles (*"Student struggled with passenger vehicle capacity limits"*).

---

## 7. Phase 2M — Voice Companion Pipeline

```
  [User Speaks] ──► [Web Speech STT] ──► [FastAPI /api/chat]
                                                  │
                                                  ▼
                                       [Gemma 2 2B Inference]
                                       (content + spoken_reply)
                                                  │
                                                  ▼
                                       [Voice Synthesis Engine]
                                                  │
                     ┌────────────────────────────┴────────────────────────────┐
                     ▼                                                         ▼
            [SHA-256 Cache Hit]                                      [Cache Miss]
        (Instant playback from disk)                                           │
                                                                               ▼
                                                                [ElevenLabs Provider]
                                                               (Optional API Key present)
                                                                               │
                                                         ┌─────────────────────┴─────────────────────┐
                                                         ▼                                           ▼
                                                [MP3 Stream Generated]                     [Fallback to Browser]
                                                (Cached to disk via SHA-256)             (Web Speech SpeechSynthesis)
```

- **`spoken_reply` Optimization:** When Gemma generates a comprehensive multi-paragraph statutory explanation (e.g. 1500 characters), it simultaneously produces an encouraging 1–2 sentence spoken reply (e.g. 130 characters) for natural audio consumption without reading walls of text.

---

## 9. Phase 3 — CA Exam Practice & Answer Evaluation Architecture

### A. Question Model & Source Provenance Architecture
Every question in the system enforces strict provenance separation between verified official ICAI materials and AI-generated practice scenarios:

```sql
CREATE TABLE questions (
    id TEXT PRIMARY KEY,
    stage_id TEXT NOT NULL,
    group_id TEXT,
    paper_id TEXT NOT NULL,
    module_id TEXT,
    chapter_id TEXT NOT NULL,
    topic_id TEXT,
    difficulty TEXT CHECK(difficulty IN ('Easy', 'Medium', 'Hard')),
    question_type TEXT CHECK(question_type IN ('MCQ', 'Short Answer', 'Theory', 'Numerical', 'Practical')),
    marks INTEGER NOT NULL,
    expected_time_minutes INTEGER NOT NULL,
    source TEXT NOT NULL,                -- e.g. 'ICAI RTP — May 2026' vs 'Sathi AI Practice Question'
    source_document TEXT,                -- Verified document name
    source_page INTEGER,                 -- Official textbook page
    question_text TEXT NOT NULL,
    options TEXT,                        -- JSON array for MCQs
    correct_answer TEXT,                 -- Option key or core statutory holding
    solution TEXT NOT NULL,              -- Model step-by-step solution
    marking_scheme TEXT NOT NULL,        -- Step-mark allocation criteria
    explanation TEXT,                    -- Pedagogical insight
    is_official INTEGER DEFAULT 1,       -- 1 = Official ICAI, 0 = AI-generated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### B. Evaluation Pipeline & Step Marking
```
   [Student Submits Answer]
              │
              ▼
   [Question Type Dispatch]
       │              │
       ▼ (MCQ)        ▼ (Theory / Practical / Numerical)
 [Deterministic]  [Hybrid RAG Context Ingestion]
  (Exact Match)               │
       │                      ▼
       │         [Gemma 2 2B Step-Marking Prompt]
       │         (Question + Marking Scheme + ICAI Chunk)
       │                      │
       └──────────────┬───────┘
                      ▼
            [Structured JSON Output]
      - Score / Max Score
      - Sub-scores (Concept, Calculation, Presentation %)
      - Strengths ("What You Did Well")
      - Mistakes ("Where You Lost Marks")
      - Model Solution & Step Feedback
      - Spoken Verbal Summary
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
[SQLite Attempt Log]    [Profile & Spaced Scheduler]
(question_attempts,     (topic_performance,
 answer_evaluations)     revision_schedule)
```

### C. Spaced Revision Scheduling Model
Following any incorrect or sub-threshold attempt ($< 75\%$), Sathi automatically schedules spaced revisions following an expanding interval sequence:
- Interval sequence: `[Day 1, Day 3, Day 7, Day 14, Day 30]`
- Database entity: `revision_schedule` tracking `topic_id`, `scheduled_date`, `interval_days`, `repetition_count`, and `is_completed`.
- Filter query: `scheduled_date <= DATE('now') AND is_completed = 0` surfaces actionable daily revision tasks on the Progress and Practice dashboards.

### D. Companion Attempt Context Transfer ("Ask Sathi")
When the student clicks "Ask Sathi" on any evaluation screen, the frontend transfers the structured attempt state into Sathi's context:
```python
attempt_context = {
    "question": q["question_text"],
    "student_answer": user_answer,
    "score": eval_res["score"],
    "max_score": eval_res["max_score"],
    "mistakes": eval_res["mistakes"],
    "ideal_answer": eval_res["ideal_answer"]
}
```
Sathi's prompt injector (`build_grounded_system_prompt`) formats this into an immediate academic diagnostic context, allowing the student to ask natural questions (*"Why did I lose 2 marks on the mini-bus?"*) without repeating the problem statement.


---

## 9. Phase 4 — Full ICAI Knowledge & Question Corpus Ingestion Architecture

### A. Document Ingestion Pipeline (`backend/app/knowledge/`)
Phase 4 introduces a production ingestion pipeline supporting PDF, TXT, and Markdown files:

```
OFFICIAL DOCUMENT (PDF / TXT / MD)
               │
               ▼
      [Document Parser]
               │  ├── PDF: pypdf page & text extraction
               │  ├── Page Detection (page numbers preserved)
               │  └── Section Detection (statutory sections, headings)
               ▼
     [Semantic Chunker]
               │  ├── Respects clause boundaries (Sections, Provisos)
               │  └── Preserves complete legal provisions
               ▼
    [Metadata & Content Hash]
               │  ├── SHA-256 File Hash (document-level deduplication)
               │  └── SHA-256 Content Hash (chunk-level deduplication)
               ▼
     [Dual-Store Indexing]
         ┌─────┴─────┐
         ▼           ▼
   [SQLite FTS5]  [sqlite-vec]
   (BM25 Search)  (FastEmbed 384d Dense)
```

### B. Duplicate Protection & Provenance Schema
Every document and chunk enforces deterministic deduplication. Re-importing identical files returns `"status": "already_indexed"` and reports 0 duplicate chunk insertion.

```sql
CREATE TABLE ingested_documents (
    document_id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT,
    file_format TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,      -- SHA-256 of raw file bytes
    document_title TEXT NOT NULL,
    source_type TEXT NOT NULL,           -- ICAI_STUDY_MATERIAL, RTP, MTP, PAST_EXAM
    issuing_body TEXT NOT NULL,          -- ICAI
    stage TEXT NOT NULL,
    group_name TEXT,
    paper TEXT NOT NULL,
    module TEXT,
    chapter TEXT,
    total_pages INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    document_version TEXT,
    effective_date TEXT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE knowledge_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES ingested_documents(document_id),
    document_title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    issuing_body TEXT NOT NULL,
    stage TEXT NOT NULL,
    group_name TEXT,
    paper TEXT NOT NULL,
    module TEXT,
    chapter TEXT NOT NULL,
    topic TEXT,
    statutory_reference TEXT,
    page_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT UNIQUE NOT NULL,   -- SHA-256 of normalized text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### C. Advanced Hybrid Knowledge Retriever (`HybridKnowledgeRetriever`)
- **Statutory Query Weighting:** When queries contain explicit statutory sections (`Section 17(5)`, `Section 139`, `AS 10`), lexical search receives a 1.8x weighting multiplier.
- **Reciprocal Rank Fusion (RRF):**
  $$\text{RRF Score} = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{w_m}{k + \text{rank}_m} \quad (k = 60)$$
- **Explicit Provenance Badging:** Every retrieved chunk is tagged with provenance:
  - `🏛️ Official ICAI Source` (`ICAI_STUDY_MATERIAL`, `RTP`, `MTP`, `PAST_EXAM`)
  - `🤖 Sathi AI Generated Practice` (`SATHI_GENERATED`)

### D. Multi-Factor Weak-Area & Priority-Adaptive Spaced Revision
- **Weak-Area Diagnosis:** Evaluates accuracy $< 75\%$, average score $< 60\%$, and repeated recorded mistakes.
- **Adaptive Spaced Revision:** If a topic demonstrates repeated struggle, revision intervals escalate to immediate cycles (Day 1 or Day 3) rather than progressing to distant dates, ensuring memory consolidation on critical exam provisions.



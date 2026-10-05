# Sathi (साथी) — Personal AI CA Companion & Grounding Anchor
### Built for DEV Hacktoberfest 2026 Weekend Challenge 1: *Build for a Friend*

> **"Built for my sister, an aspiring Chartered Accountant (CA)."**
> CA preparation is notorious for rigorous 10–12 hour study days, vast multi-volume syllabi, and severe solitary burnout. Sathi is an AI companion designed not just to explain accounting standards and tax provisions, but to accompany her throughout the preparation journey: tracking progress across Foundation, Intermediate, and Final stages, answering doubts grounded in authoritative ICAI study materials, and maintaining human perspective when examination anxiety hits.

---

## 🌟 The Pillars of Sathi

### 1. 🎤 Voice & Multimodal Conversational Companion
- **Real-Time Speech Interaction:** Integrated Web Speech STT + ElevenLabs TTS voice synthesis with animated companion orb reactions (idle, listening, thinking, speaking).
- **Graceful Local Fallback:** Works 100% offline out-of-the-box using browser Web Speech API if ElevenLabs credentials are not configured.
- **SHA-256 Audio Caching:** Instant zero-cost replay for frequently synthesized academic explanations.
- **Full Conversational Controls:** Listen, Pause, Resume, Replay, Copy, and Save to Notes.

### 2. 🏛️ Authoritative CA Knowledge Engine & Local Hybrid RAG
- **Zero Cloud Vector DB:** Powered by local `FastEmbed` (`BAAI/bge-small-en-v1.5`, 384 dimensions) and `sqlite-vec` dense vector search combined with SQLite FTS5 BM25 keyword matching via Reciprocal Rank Fusion (RRF).
- **Intelligent Query Router:**
  - **Fast Path:** Greetings, casual check-ins, motivation, and wellbeing skip retrieval for zero-latency instant responses.
  - **Deep Path:** Statutory queries (Section numbers, Accounting Standards, Standards on Auditing, ICAI rules) automatically retrieve verified source chunks.
- **Verified Source Citations:** UI displays expandable `Source Verified` cards detailing document name, statutory section, page number, edition, and exact authoritative quotes.
- **Strict Hallucination Fallback:** If retrieved ICAI material does not establish the answer, Sathi explicitly declares the absence rather than fabricating statutory sections or rules.

### 3. 📚 Scalable ICAI Syllabus Hierarchy & Academic Workspace
- **Complete Stage Hierarchy:** Foundation, Intermediate (Group 1 & 2), and Final covering modules, chapters, and topics based on the ICAI 2024–2025 scheme.
- **Pedagogical Progress Tracking:** Track status (`Not Started`, `In Progress`, `Completed`, `Needs Revision`), 5-level confidence ratings, revision counts, and attached personal notes.
- **"Ask Sathi" Context Injection:** Every chapter and topic has a dedicated "Ask Sathi" trigger that seamlessly loads stage, group, paper, module, and topic context into the companion without requiring manual explanation.
- **Focused Study Session (Phase 2K):** 8-step structured learning modal:
  1. What you'll learn
  2. Core conceptual breakdown
  3. Practical CA exam example
  4. Instant Ask Sathi doubt clearance
  5. High-yield practice question with solution reveal
  6. Progress & confidence updates
  7. Revision logging & counter
  8. Personal notes auto-save

### 4. 🧠 Adaptive Memory & Student-Aware Recommender
- **Memory Provider Architecture:** Provider pattern with `LocalMemoryProvider` (SQLite-backed) as the default and `BackboardMemoryProvider` as an optional semantic memory adapter activated via `BACKBOARD_API_KEY`.
- **Student-Aware Recommendations:** Sathi analyzes real SQLite progress state (active chapters, low confidence scores, overdue revisions) to recommend strategic daily study tasks without inventing fake progress.

### 5. 🌿 Sanctuary & Life Beyond Examinations
- **Box Breathing Visualizer (4-4-4-4):** Interactive animated breathing circle to downregulate cortisol before exams.
- **Cognitive Thought Reframing:** Powered by local Gemma 2 2B to reframe catastrophic thoughts (*"I'm going to fail this attempt"*) into empathetic, constructive perspectives.
- **Perspective Anchors:** Reminders that human worth is not defined by a six-digit roll number.

---

## 🛠️ System Architecture

```
               React 19 + Vite Desktop UI (Glassmorphic Design)
       ┌───────────────────────────────┴───────────────────────────────┐
       │                                                               │
Voice Orb (STT / TTS)                                       Study Workspace & Hierarchy
       │                                                               │
       └───────────────────────────────┬───────────────────────────────┘
                                       │ HTTP / REST
                         FastAPI Gateway (:8000)
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        Intelligent Query Router                 Study Repository (SQLite)
       ┌────────────┴────────────┐                        │
       ▼                         ▼                        ▼
   Fast Path                 Deep Path            Syllabus Hierarchy
 (Gemma Direct)                  │                (Stages, Groups, Papers,
                                 ▼                 Modules, Chapters, Topics)
                    Authoritative Hybrid RAG
                    ┌────────────┴────────────┐
                    ▼                         ▼
             FTS5 BM25 Lexical           sqlite-vec Dense
             Keyword Matcher             FastEmbed (bge-small)
                    └────────────┬────────────┘
                                 ▼
                     Reciprocal Rank Fusion
                                 ▼
                     Authoritative ICAI Chunks
                                 │
                                 ▼
                    Grounding Prompt Builder
             (System + Memory + Context + Chunks)
                                 │
                                 ▼
                  Ollama Gemma 2 2B Engine (:11434)
                    (Local NVIDIA GPU VRAM)
                                 │
                                 ▼
              Grounded Response + Verified Citations
```

---

## 🚀 Quickstart Guide

### Prerequisites
1. **Ollama:** Installed with `gemma2:2b` pulled:
   ```bash
   ollama pull gemma2:2b
   ```
2. **Python 3.10+** (tested and verified on Python 3.14 with `fastembed` & `sqlite-vec`)
3. **Node.js 18+**

### 1. Start the Backend API
```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI documentation will be live at: `http://127.0.0.1:8000/docs`

### 2. Start the Frontend Application
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
Open **`http://127.0.0.1:5173/`** in your browser.

---

### 6. ✍️ CA Exam Practice & Answer Evaluation Engine (Phase 3)
- **Interactive Practice Hub:** Dedicated CA preparation environment with Quick Sets (5, 10, 20 questions), Practice by Subject, Practice by Chapter, and Weak Area focus.
- **Strict Source Provenance:** Authoritative ICAI questions (`🏛️ ICAI RTP — May 2026`, Past Exams, MTPs) are strictly segregated from AI-generated questions (`🤖 Sathi AI Practice Question`).
- **RAG-Grounded Question Generator:** Generates high-yield practical case studies and numerical problems grounded in authoritative ICAI Study Material context via Gemma 2 2B.
- **Structured Step-Marking Evaluation:**
  - Deterministic scoring for MCQs (100% precision).
  - Multi-dimensional breakdown for theory/practical problems: Concept Understanding, Calculation & Adjustments, and ICAI Presentation scores.
  - Concrete step feedback: "What You Did Well" (strengths), "Where You Lost Marks" (omissions, wrong sections, calculation errors), and "Ideal Approach" model solutions.
  - Spoken explanation summary ready for single-click ElevenLabs audio playback.
  - Explicit disclaimer designating AI-assisted evaluation estimates to preserve academic safety.
- **Weak Topic Detection:** Dynamically tracks attempts, accuracy percentages, and repeated mistakes per topic in SQLite.
- **Spaced Revision Scheduling:** Automatically schedules spaced revisions at Day 1, 3, 7, 14, and 30 intervals after incorrect answers.
- **Timed Exam Mode Simulation:** Realistic ICAI mock exam with countdown timer, marks tally, question navigation, and post-exam diagnostic performance report.
- **Deep "Ask Sathi" Attempt Transfer:** Single-click transfer of attempt context (question text, student answer, marks lost, mistakes identified) to the conversational companion for natural follow-up doubt clearance.

---

### 7. 📚 Full ICAI Knowledge & Question Corpus Ingestion Engine (Phase 4)
- **Document Ingestion Pipeline (`backend/app/knowledge/`):** Production-grade ingestion pipeline supporting PDF (`pypdf`), Markdown, and TXT files.
- **Page & Section Preservation:** Preserves textbook page numbers, headings, sub-headings, and statutory references (`Section \d+`, `Rule \d+`, `SA \d+`, `AS \d+`).
- **Semantic Clause-Aware Chunking:** Legal clause integrity preservation—never splits mid-sentence, mid-clause, or mid-proviso.
- **Deterministic Deduplication:** Dual SHA-256 hashing at file-level (`file_hash`) and chunk-level (`content_hash`) prevents duplicate chunk insertion.
- **Hybrid Knowledge Retriever:** FTS5 BM25 search with statutory query weighting (1.8x multiplier for exact Section/Standard lookups like `"Section 17(5)"` or `"AS 10"`) + `sqlite-vec` dense vector search (FastEmbed 384d) + Reciprocal Rank Fusion (RRF).
- **Expanded Question Corpus:** Expanded from 6 to 25 verified questions across Foundation, Intermediate (Papers 1–6), and Final.
- **Strict Provenance Separation:** Explicit separation between 🏛️ Official ICAI Source (`ICAI_STUDY_MATERIAL`, `RTP`, `MTP`, `PAST_EXAM`) and 🤖 Sathi AI Generated Practice (`SATHI_GENERATED`).
- **Timed Exam Generator:** Non-repetition selection logic (`exclude_ids`) supporting 5, 10, and 20 question sets.
- **Multi-Factor Weak-Area & Adaptive Spaced Revision:** Multi-factor weak-area diagnosis and priority-adaptive spaced revision escalation to Day 1/Day 3 upon repeated struggle.

---

## 🧪 Comprehensive Verification Suites

All test suites run locally with zero cloud dependencies:

```powershell
cd backend

# 1. MVP Core & Reframer Test Suite (7/7 passing)
python -X utf8 tests/verify_mvp.py

# 2. Voice Companion & Audio Caching Test Suite (6/6 passing)
python -X utf8 tests/verify_voice_companion.py

# 3. Hybrid RAG & Provenance Test Suite (6/6 passing)
python -X utf8 tests/verify_rag.py

# 4. Memory Provider & Backboard Adapter Suite (4/4 passing)
python -X utf8 tests/verify_memory.py

# 5. Scalable Syllabus & Context Injection Suite (5/5 passing)
python -X utf8 tests/verify_study_context.py

# 6. Exam Practice & Answer Evaluation Suite (8/8 passing)
python -X utf8 tests/verify_practice.py

# 7. Phase 4 Knowledge Ingestion & Corpus Suite (15/15 passing)
python -X utf8 tests/verify_phase4.py
```
*(Total: 51/51 tests passing · 100% Pass Rate)*

---

## 🛡️ Privacy & Security Model
- **100% Local Intelligence:** All prompts, academic questions, and emotional thoughts are processed locally on-device by Gemma 2 2B.
- **Zero Third-Party Data Leakage by Default:** The default `LocalMemoryProvider` stores memories entirely in `sathi.db`.
- **Optional Backboard Adapter:** If `BACKBOARD_API_KEY` is provided, semantic memory summaries can optionally sync with Backboard.io. If absent, the system operates seamlessly with zero degradation.
- **No Hardcoded Credentials:** All API keys (`ELEVENLABS_API_KEY`, `BACKBOARD_API_KEY`) are optional environment variables.

---

## 📄 License
Licensed under the Apache 2.0 License.

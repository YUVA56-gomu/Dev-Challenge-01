# Sathi (साथी) — Development Roadmap

---

## 🏆 Completed Milestones

### Phase 0: MVP End-to-End Vertical Slice ✅
- Open-weight **Google Gemma 2 2B** via Ollama on local NVIDIA GPU VRAM.
- Multi-turn conversational memory with pedagogical CA persona.
- SQLite database with basic syllabus papers, daily tasks, study streaks, and progress meters.
- Sanctuary view with interactive Box Breathing visualizer (4-4-4-4) and AI cognitive thought reframing.
- Automated regression suite (`tests/verify_mvp.py`, 7/7 passed).

### Phase 1: Real-Time Voice Conversational Companion ✅
- Web Speech STT for live microphone speech input.
- `ElevenLabsVoiceProvider` integration with seamless browser `SpeechSynthesis` local fallback.
- `spoken_reply` optimization in Gemma prompt preventing lengthy text reading over audio.
- SHA-256 disk audio caching for zero-latency instant replay of common explanations.
- Animated 4-state `VoiceOrb` reacting to speaking, listening, and thinking states.
- Automated voice suite (`tests/verify_voice_companion.py`, 6/6 passed).

### Phase 2: CA Knowledge Engine + Full Syllabus + Local Hybrid RAG + Memory ✅
- **Full Syllabus Hierarchy:** Multi-stage relational schema covering Foundation, Intermediate, and Final (Groups, Papers, Modules, Chapters, Topics) with statutory sections and exam weightages.
- **Authoritative Hybrid RAG:**
  - Ingestion pipeline with strict document provenance (Doc name, issuing authority, edition, section, page).
  - Lexical FTS5 BM25 search + dense `sqlite-vec` search (`FastEmbed` `bge-small-en-v1.5`).
  - Reciprocal Rank Fusion (RRF) combining keyword precision with semantic discovery.
- **Intelligent Query Router:** Fast Path (greetings/emotions) vs Deep Path (statutory/syllabus questions).
- **Grounded Gemma Responses & Provenance Citations:** Anti-hallucination mandate with expandable `Source Verified` UI cards.
- **"Ask Sathi" from Syllabus:** 1-click chapter and topic context injection.
- **Focused Study Session:** 8-step structured learning modal (Objectives, Explain, Example, Practice with reveal, Status, Confidence, Revisions, Notes).
- **Semantic Memory Layer:** `LocalMemoryProvider` default with optional `BackboardMemoryProvider` adapter.
- **Student-Aware Recommender:** Recommendations generated from real SQLite progress and weak areas.
- **Comprehensive Verification:** 5 automated test suites with 28/28 tests passing.

---

### Phase 3: CA Exam Practice & Answer Evaluation Engine ✅
- **Interactive Practice Hub:** Practice workspace with Quick Sets (5, 10, 20 questions), Practice by Subject, Practice by Chapter, and Weak Area targeting.
- **Strict Question Provenance:** Strict segregation between verified ICAI questions (`🏛️ ICAI RTP — May 2026`) and AI-generated practice questions (`🤖 Sathi AI Practice Question`).
- **RAG-Grounded Question Generator:** Creates realistic practical and numerical case studies strictly grounded in retrieved ICAI study material chunks.
- **Structured Step-Marking Evaluation:** Multi-dimensional scoring (Concept, Calculation, Presentation), strengths, mistakes, model answers, and ElevenLabs-ready spoken feedback.
- **Weak Topic Tracking & Spaced Revision:** SQLite performance tracking updating weak topics and scheduling spaced revisions across Day 1, 3, 7, 14, and 30 intervals.
- **Timed Exam Mode Simulation:** Realistic ICAI mock exam with countdown timer, marks tally, question navigation, and post-exam diagnostic performance report.
- **Deep "Ask Sathi" Attempt Transfer:** Seamless 1-click transition from evaluation screen into conversational companion carrying full attempt context for natural review.
- **Automated Verification:** 8-phase practice test suite (`tests/verify_practice.py`) passing with 100% success rate (36/36 tests overall).

---

### Phase 4: Full ICAI Knowledge + Question Corpus Ingestion Engine ✅
- **Document Ingestion Pipeline (`backend/app/knowledge/`):** Production-grade ingestion supporting PDF (`pypdf`), Markdown, and TXT files with page and section preservation.
- **Semantic Clause-Aware Chunking:** Legal clause integrity preservation—never splits mid-sentence, mid-clause, or mid-proviso.
- **Deterministic Deduplication:** Dual SHA-256 hashing at file-level (`file_hash`) and chunk-level (`content_hash`) with duplicate protection.
- **Hybrid Knowledge Retriever:** FTS5 BM25 search with statutory query weighting (1.8x multiplier for exact Section/Standard lookups) + `sqlite-vec` dense vector search (FastEmbed 384d) + Reciprocal Rank Fusion (RRF).
- **Expanded Question Corpus:** Expanded from 6 to 25 verified questions across Foundation, Intermediate (Papers 1–6), and Final.
- **Strict Provenance Separation:** Clear differentiation between 🏛️ Official ICAI Source (`ICAI_STUDY_MATERIAL`, `RTP`, `MTP`, `PAST_EXAM`) and 🤖 Sathi AI Generated Practice (`SATHI_GENERATED`).
- **Timed Exam Generator:** Non-repetition selection logic (`exclude_ids`) supporting 5, 10, and 20 question sets.
- **Multi-Factor Weak-Area & Adaptive Spaced Revision:** Multi-factor weak-area diagnosis and priority-adaptive spaced revision escalation to Day 1/Day 3 upon repeated struggle.
- **Automated Verification:** 15-phase verification suite (`tests/verify_phase4.py`) passing with 100% success rate (51/51 tests passing across 7 suites).

---

## 🚀 Future Milestones

### Phase 5: Packaged Desktop App & Offline Distribution
- **Tauri / Electron Packaging:** Bundle Sathi into a standalone `.exe` installer.
- **Embedded Ollama Manager:** Automated model verification and health monitoring within the desktop runtime.
- **Encrypted Local Storage:** SQLCipher encryption for sensitive revision notes and student journals.

### Phase 6: Fine-Tuning Sathi Companion (Future Experiment)
- **Pedagogical Persona Alignment:** Fine-tuning Gemma 2 on curated CA mentor conversations for empathetic teaching style (keeping RAG as the sole authoritative knowledge source).

---

## 🎯 Current Status

**Phase 3 is COMPLETE and Verified.**
All 6 automated verification suites pass with zero regressions (36/36 tests passing). Full browser walkthrough and UI interactions verified end-to-end.
Awaiting user instruction before commencing Phase 4.


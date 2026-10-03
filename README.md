# Sathi (साथी) — The Personal AI CA Companion & Grounding Anchor
### Built for DEV Hacktoberfest 2026 Weekend Challenge 1: *Build for a Friend*

> **"Built for my sister, an aspiring Chartered Accountant (CA)."**
> CA preparation is notorious for rigorous 10–12 hour study days, vast multi-volume syllabi, and severe solitary burnout. Sathi is an AI companion designed not just to explain accounting standards and tax provisions, but to help her stay consistent, track progress, and remember that her human worth is greater than an examination score.

---

## 🌟 The Three Pillars

### 1. 💬 AI CA Study Companion (Core AI)
- **Open-Weight Core:** Powered locally by **Google Gemma 2 (2B)** via Ollama with NVIDIA GPU acceleration.
- **Multi-Turn Memory:** Context-aware conversations across complex multi-step accounting inquiries.
- **Sathi Persona:** Empathetic, patient, pedagogical, and rigorous. Explains concepts with real-world Indian business examples (GST Input Tax Credit, Standards on Auditing, Companies Act sections) and memory mnemonics.
- **Strict Educational Boundary:** Explicitly distinguishes academic mentoring from practicing CA or financial advice.

### 2. 📚 Study & Progress Tracker
- **Syllabus Hierarchy:** Structured breakdown of CA Papers (Advanced Accounting, Corporate and Other Laws, Taxation, Costing, Auditing).
- **Chapter Status Lifecycle:** Track chapters across `Not Started`, `In Progress`, and `Completed`.
- **Chapter Revision Notes:** In-app personal notes for key formulas, adjustments, and section references stored in SQLite.
- **Study Streak & Daily Tasks:** Streak counter that rewards showing up every day, plus a daily task checklist.

### 3. 🌿 Sanctuary & Life Beyond Examinations
- **Box Breathing Visualizer (4-4-4-4):** Interactive animated breathing circle (Inhale 4s $\rightarrow$ Hold 4s $\rightarrow$ Exhale 4s $\rightarrow$ Hold 4s) to regulate cortisol before mock tests.
- **Negative Thought Reframing (Gemma AI):** When anxiety strikes (e.g., *"I'm going to fail this attempt"*), Gemma reframes the thought into a compassionate, grounded, growth-oriented perspective.
- **Anchors of Perspective:** Curated reflections reminding the student that their identity transcends a 6-digit roll number.

---

## 🛠️ Architecture & Open-Source AI at the Core

```
Browser Client (React 19 + Vite + CSS Design Tokens)
                        ↓ HTTP / REST
         FastAPI API Gateway (:8000)
    ┌───────────────────┴───────────────────┐
    ↓                                       ↓
AIProvider Abstraction             Study Repository
    ↓                                       ↓
OllamaGemmaProvider                    SQLite DB (sathi.db)
    ↓
Ollama Local Runtime (:11434)
    ↓
Google Gemma 2 2B (On-Device GPU VRAM)
```

### Why Open-Source AI Matters for This Project
1. **100% Privacy for Sensitive Thoughts:** Anxious thoughts and study struggles never leave the student's personal machine.
2. **Zero-Latency Offline Study:** Runs completely offline when Wi-Fi drops or during distraction-free study sessions.
3. **Zero Token Cost:** CA preparation demands thousands of queries during grueling 12-hour study days without subscription fatigue.

---

## 🚀 Getting Started

### Prerequisites
1. **Ollama:** Installed with `gemma2:2b` pulled (`ollama pull gemma2:2b`).
2. **Python 3.10+**
3. **Node.js 18+**

### 1. Start the Backend Service
```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: `http://127.0.0.1:8000/docs`

### 2. Start the Frontend Application
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
Open **`http://127.0.0.1:5173/`** in your browser.

### 3. Run the Automated Verification Suite
```powershell
cd backend
python -X utf8 tests/verify_mvp.py
```

---

## 📄 License
Licensed under the Apache 2.0 License.

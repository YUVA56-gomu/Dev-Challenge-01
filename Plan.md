Absolutely. At this point, **don't keep adding random features**. You already have a working MVP, Gemma, multi-turn chat, ElevenLabs voice, study tracker, tasks, sanctuary, etc.

Now we should treat Sathi as a **product-development roadmap** and finish it phase by phase.

Below is a complete `.md` file you can save as something like `SATHI_FINAL_ROADMAP.md`.

```md
# SATHI (साथी)
# Complete Development Roadmap
## Personal AI CA Companion — DEV Hacktoberfest 2026

---

# 0. PRODUCT VISION

Sathi is a personal AI companion designed to support a student throughout the journey of becoming a Chartered Accountant.

Sathi is NOT just:

- a chatbot
- a syllabus tracker
- a voice assistant
- a study planner

It combines:

1. Conversational AI
2. Voice interaction
3. CA knowledge
4. Syllabus navigation
5. Personal study memory
6. Progress tracking
7. Personalized learning
8. Emotional grounding
9. Career guidance
10. A premium, distraction-free study experience

The core principle:

> Sathi should feel like a study companion, not another educational dashboard.

---

# 1. CURRENT STATE

## Already Implemented

### AI

- Google Gemma 2 2B
- Ollama
- Local GPU inference
- NVIDIA RTX 3050
- AIProvider abstraction
- FastAPI AI gateway
- Multi-turn conversation
- Local inference
- Offline AI capability

### Backend

- FastAPI
- SQLite
- Repository architecture
- AI provider abstraction
- Voice provider abstraction
- REST APIs
- Health endpoint
- Chat endpoint
- Voice endpoints

### Frontend

- React
- Vite
- Companion interface
- Study interface
- Progress interface
- Sanctuary interface
- Daily tasks
- Syllabus tracking

### Voice

- ElevenLabs integration
- Voice synthesis
- Audio caching
- SHA-256 cache
- Voice playback
- Replay
- Pause
- Resume
- Stop
- Browser fallback
- Voice Orb
- Listening state
- Thinking state
- Speaking state

### Verification

- Backend MVP verification
- Multi-turn verification
- Voice verification
- Frontend production build
- Browser verification

---

# 2. FINAL DEVELOPMENT ORDER

The remaining development should happen in this order:

PHASE 1
↓
Real-time conversational voice interaction

PHASE 2
↓
Companion UI / Chat UX improvements

PHASE 3
↓
Response rendering + streaming animations

PHASE 4
↓
Dark mode + visual polish

PHASE 5
↓
Complete CA syllabus architecture

PHASE 6
↓
CA Knowledge Base + RAG

PHASE 7
↓
Student memory + personalization

PHASE 8
↓
ElevenLabs sound effects + ambient sounds

PHASE 9
↓
Gemma behavior tuning

PHASE 10
↓
Advanced study intelligence

PHASE 11
↓
Testing + reliability + privacy

PHASE 12
↓
DEV Challenge submission preparation

PHASE 13
↓
Final demo + documentation

---

# PHASE 1 — REAL-TIME VOICE CONVERSATIONAL COMPANION

## Goal

Make Sathi feel like a real voice companion.

The user should be able to:

1. Click the companion
2. Sathi starts listening
3. User speaks
4. User can interrupt when necessary
5. Sathi processes the request
6. Sathi generates an answer
7. ElevenLabs speaks the answer
8. User can interrupt the response
9. Sathi stops speaking
10. Sathi listens again

The interaction should feel natural.

---

## Required States

The Voice Orb must support:

### IDLE

```
Ready
```

### LISTENING

```
I'm listening...
```

### THINKING

```
Thinking...
```

### SPEAKING

```
Speaking...
```

### INTERRUPTED

```
Listening...
```

### ERROR

```
Voice unavailable
```

---

## Conversation Flow

```
User
 ↓
Click Companion
 ↓
Listening
 ↓
Speech Input
 ↓
Transcription
 ↓
Conversation Context
 ↓
Gemma
 ↓
Response
 ↓
ElevenLabs
 ↓
Speech Output
 ↓
User can interrupt
 ↓
Listening again
```

---

## Important Behavior

The user should NOT have to manually press:

Speak → Stop → Generate → Play

Instead:

```
Listen
→ Understand
→ Answer
→ Speak
→ Listen again
```

This is the conversational experience.

---

## Interruption

If Sathi is speaking:

User clicks microphone
OR
user starts speaking

Then:

```
STOP CURRENT AUDIO
CLEAR PLAYBACK
ENTER LISTENING STATE
CAPTURE USER SPEECH
PROCESS NEW REQUEST
```

This is critical for making the companion feel natural.

---

## ElevenLabs

Use ElevenLabs as the voice layer.

Keep credentials exclusively in:

```
backend/.env
```

Never expose the API key to React.

---

## Completion Criteria

- [ ] Voice input works
- [ ] Voice output works
- [ ] ElevenLabs works
- [ ] User can interrupt Sathi
- [ ] Sathi can listen again
- [ ] Multi-turn context survives voice interaction
- [ ] Text and voice share the same conversation
- [ ] Voice errors don't break text chat
- [ ] Loading states are clear

---

# PHASE 2 — COMPANION UI / CHAT EXPERIENCE

## Goal

Make the Companion feel premium.

The Companion should resemble the quality of modern AI products such as ChatGPT / Gemini while maintaining Sathi's own visual identity.

---

## Main Companion Experience

The companion object / orb should remain accessible.

Example:

```
              SATHI

        [ Animated Orb ]

       "How can I help?"

       ───────────────

 Student message

 Sathi response

 [Listen] [Copy] [Save]

       🎤 Speak
```

---

## UI Principles

Avoid:

- crowded screens
- too many buttons
- huge text blocks
- unnecessary cards
- excessive gradients
- distracting animations

Use:

- whitespace
- glass surfaces
- subtle borders
- soft shadows
- smooth transitions
- readable typography
- clear hierarchy

---

## Companion Object

The companion should be visually present throughout the application.

Possible states:

```
Idle
Listening
Thinking
Speaking
Happy / Encouraging
Concerned / Supportive
```

The visual state should change based on the interaction.

---

# PHASE 3 — RESPONSE RENDERING + STREAMING ANIMATION

## Problem

Gemma currently produces responses containing things like:

```
**Important**
**Definition**
**Example**
```

or badly rendered Markdown.

This must be fixed.

---

## Response Rendering

Implement proper Markdown rendering.

Support:

- headings
- bold
- italic
- bullet lists
- numbered lists
- code blocks
- formulas
- tables
- quotes
- highlighted key points

The raw Markdown must NEVER be shown to the user.

Bad:

```
**Section 139**
```

Good:

### Section 139

---

## AI Response Structure

Teach Gemma to produce structured responses.

Example:

```
CONCEPT

Simple explanation.

WHY IT MATTERS

Explanation.

EXAMPLE

Practical example.

EXAM TIP

Important point to remember.

MEMORY TRICK

Mnemonic.
```

The frontend can then render these elegantly.

---

## Streaming

Implement token/word streaming where practical.

Instead of:

```
User sends message

3 seconds silence

FULL RESPONSE APPEARS
```

Use:

```
User sends message

Sathi thinking...

"Okay, let's break this down..."

"First..."

"The important thing is..."
```

---

## Animation

Use subtle response animation.

Possible sequence:

```
Sending
 ↓
Thinking indicator
 ↓
Response container appears
 ↓
Text streams
 ↓
Source badges appear
 ↓
Action buttons appear
```

---

## Important Principle

Animations should reduce perceived waiting time.

They must NOT make the application slower.

Avoid:

- excessive bouncing
- long delays
- unnecessary 3D animation
- animation on every tiny UI element

---

# PHASE 4 — DARK MODE + VISUAL POLISH

## Goal

Create a polished premium visual system.

---

## Theme

Support:

### Light Mode

Clean study environment.

### Dark Mode

Night study environment.

---

## Visual Direction

Use:

- Glassmorphism
- Soft gradients
- Translucent surfaces
- Subtle blur
- Ocean-inspired accents
- Clean typography

Do NOT make everything dark navy.

The interface should remain readable.

---

## Theme Tokens

Create centralized CSS variables.

Example:

```
--background
--surface
--surface-glass
--text-primary
--text-secondary
--border
--accent
--success
--warning
--danger
```

Do not hardcode colors throughout components.

---

# PHASE 5 — COMPLETE CA SYLLABUS SYSTEM

## Goal

Sathi must understand the complete CA journey.

The current limited syllabus seed is NOT enough.

---

# CA Journey

Sathi should understand:

```
CA Journey
│
├── Foundation
│
├── Intermediate
│   ├── Group 1
│   └── Group 2
│
├── Practical Training / Articleship
│
├── Final
│   ├── Group 1
│   └── Group 2
│
├── Self-Paced Modules
│
└── Membership / Qualification
```

The exact rules and current requirements must come from authoritative ICAI sources and be versioned.

---

# Academic Hierarchy

Database structure:

```
Stage
 ↓
Group
 ↓
Paper
 ↓
Module
 ↓
Chapter
 ↓
Topic
 ↓
Learning Objective
```

---

## Student Progress

Track:

- Not Started
- In Progress
- Completed
- Needs Revision

Also:

- Confidence
- Revision count
- Last revised
- Questions attempted
- Questions correct
- Weak areas
- Notes

---

# Study Mode

Every chapter should have:

```
Chapter

Progress
Notes
Ask Sathi
Start Chapter
Mark Complete
Practice Questions
Revision
```

---

## "Add Chapter" Feature

Study Mode should allow the user to add/customize chapters where appropriate.

Example:

```
+ Add Chapter

Subject:
Taxation

Chapter:
GST Input Tax Credit

Estimated Hours:
6

Difficulty:
Medium
```

---

# PHASE 6 — CA KNOWLEDGE BASE + RAG

## Goal

Gemma should NOT be expected to memorize the entire CA curriculum.

Instead:

```
Authoritative Sources
        ↓
Document Processing
        ↓
Chunking
        ↓
Metadata
        ↓
Embeddings
        ↓
Hybrid Retrieval
        ↓
Gemma
        ↓
Verified Answer
```

---

# Knowledge Sources

Prioritize authoritative sources.

Examples:

- ICAI study material
- ICAI BoS material
- ICAI announcements
- ICAI regulations
- official RTPs
- official MTPs
- official statutory material
- Government legislation
- relevant official notifications

Every source must be versioned.

---

# RAG

Use:

### Lexical Retrieval

Useful for:

```
Section 17(5)
Section 139
AS 10
SA 200
```

### Semantic Retrieval

Useful for:

```
Explain the concept behind blocked ITC.
```

---

# Hybrid Retrieval

```
User Question
      ↓
Intent Detection
      ↓
Keyword Search
      +
Vector Search
      ↓
Rank Results
      ↓
Top Relevant Sources
      ↓
Gemma
```

---

# Source Attribution

Every factual answer should be able to show:

```
Source Verified

ICAI
Paper:
Chapter:
Section:
Page:
Edition:
```

The UI should make the source accessible.

---

# Anti-Hallucination Rule

For sensitive factual questions:

```
If authoritative context exists:
    Answer using retrieved context.

If context does not exist:
    Say that verification is required.

Never invent:
- sections
- dates
- tax rates
- exam rules
- ICAI deadlines
- legal requirements
```

---

# PHASE 7 — PERSONAL MEMORY + CONTEXT

## Goal

Make Sathi remember the student without confusing memory with factual knowledge.

There are three separate memory systems.

---

## Layer 1 — Structured Student State

SQLite.

Store:

- syllabus progress
- tasks
- weak topics
- revision history
- confidence
- exam target
- study sessions

---

## Layer 2 — Conversation Memory

Current conversation:

```
Last N turns
```

Used for immediate context.

---

## Layer 3 — Long-Term Personal Memory

Potentially:

- learning preferences
- recurring difficulties
- preferred explanation style
- study habits
- important goals

Use a `MemoryProvider` abstraction.

---

## Local Memory

Default:

```
LocalSQLiteMemoryProvider
```

Benefits:

- private
- offline
- no API dependency

---

## Optional Backboard.io

Backboard can be evaluated for semantic/episodic memory.

Architecture:

```
MemoryProvider
      │
      ├── LocalSQLiteMemoryProvider
      │
      └── BackboardMemoryProvider
```

Backboard should NOT become the source of truth for:

- syllabus completion
- task booleans
- exact progress
- official CA facts

---

# PHASE 8 — SOUNDS + AUDIO EXPERIENCE

## This phase comes AFTER UI improvements.

The goal is not to add random sound effects.

Sathi should have a subtle audio identity.

---

# Sound Categories

## 1. Companion Open

Very short:

```
0.5 – 1.0 sec
```

Soft futuristic / oceanic activation.

Used when opening Companion.

---

## 2. Listening Start

```
0.3 – 0.7 sec
```

Soft confirmation sound.

Used when:

```
Listening...
```

---

## 3. Thinking

Very subtle:

```
1 – 2 sec
```

Can loop quietly.

Used while Gemma is processing.

---

## 4. Response Ready

```
0.4 – 0.8 sec
```

Soft completion chime.

---

## 5. Message Sent

```
0.1 – 0.3 sec
```

Extremely subtle.

---

## 6. Task Completed

```
0.5 – 1.0 sec
```

Positive but not game-like.

---

## 7. Chapter Completed

```
1 – 1.5 sec
```

Slightly more rewarding.

---

## 8. Error

```
0.3 – 0.6 sec
```

Soft notification.

Never harsh.

---

## 9. Sanctuary / Breathing

Long ambient audio:

```
30 sec – several minutes
```

Optional background sound.

---

# Copilot-Style Music

Instead of having constant background music, create optional adaptive "copilot" music.

Characteristics:

- minimal
- calm
- study-friendly
- no distracting vocals
- soft ambient texture
- subtle ocean atmosphere
- low dynamic range

Possible modes:

```
Focus
Deep Study
Revision
Night Study
Breathing
```

Music should be optional and OFF by default if it may distract the student.

---

# ElevenLabs Creation

For short UI effects:

Use:

```
Sound Effects
```

For longer ambient tracks:

Use:

```
Music Generation
```

Always specify duration in the generation prompt.

Example:

```
Create a 0.7-second subtle futuristic oceanic UI activation sound.
Soft, premium, minimal, glassmorphic technology aesthetic.
No melody, no voice, no percussion.
Quick attack and smooth decay.
```

For music:

```
Create a 90-second calm study companion ambient track.
Minimalist electronic ambient music with subtle ocean atmosphere.
No vocals.
No strong percussion.
No dramatic transitions.
Designed for long concentration sessions.
```

---

# PHASE 9 — GEMMA BEHAVIOR TUNING

## Goal

Do NOT immediately fine-tune the model.

First improve:

- system prompts
- RAG
- structured context
- output formatting
- examples
- response policies

---

# Gemma Persona

Sathi should behave like:

```
A patient CA study companion.
```

Not:

```
A generic chatbot.
```

---

# Response Rules

For simple questions:

```
Answer directly.
```

For difficult concepts:

```
Explain
→ Simplify
→ Example
→ Exam perspective
→ Memory trick
```

For practical questions:

```
Concept
→ Formula
→ Steps
→ Worked example
```

For legal questions:

```
Provision
→ Meaning
→ Example
→ Exception
→ Source
```

---

# Response Length

Avoid:

- unnecessary essays
- repetitive explanations
- excessive disclaimers

Prefer:

```
Short answer
+
Useful depth
```

---

# Fine-Tuning

Fine-tuning is OPTIONAL.

Do NOT fine-tune to store CA laws.

RAG should store changing factual knowledge.

If fine-tuning is later required:

```
Gemma
 ↓
QLoRA
 ↓
Pedagogical behavior / tone
```

Potential dataset:

- CA mentor conversations
- explanation examples
- Socratic questioning
- exam-oriented explanations
- Hinglish examples if required

Fine-tuning should change behavior, NOT replace RAG.

---

# PHASE 10 — ADVANCED STUDY INTELLIGENCE

Once the core system is stable, Sathi can become proactive.

---

## Personalized Study Planner

Inputs:

- available hours
- exam date
- syllabus completion
- weak areas
- chapter difficulty
- revision history

Output:

```
Today's Study Plan

1. Taxation — ITC
   60 minutes

2. Audit — SA 500
   45 minutes

3. Practice
   30 minutes

4. Revision
   20 minutes
```

---

# Spaced Revision

Automatically suggest:

```
Day 1
Day 7
Day 30
```

based on completed chapters.

---

# Weak Area Detection

Example:

```
Student attempted:
20 questions

Correct:
11

Accuracy:
55%

Weak Topic:
Blocked ITC
```

Sathi can recommend:

```
Revise Section 17(5)
↓
Read explanation
↓
Solve 5 questions
↓
Re-test
```

---

# Exam Mode

Eventually:

```
Exam Mode
```

Features:

- timed questions
- mock tests
- revision mode
- exam-style answers
- mistakes log
- performance analytics

---

# PHASE 11 — RELIABILITY, SECURITY & PRIVACY

## Backend

Check:

- API validation
- exception handling
- timeouts
- rate limits where required
- logging
- structured errors

---

## Secrets

Never expose:

```
ELEVENLABS_API_KEY
```

Never expose:

```
BACKBOARD_API_KEY
```

Never expose other provider keys.

---

## Frontend

Frontend should communicate with:

```
FastAPI
```

Not directly with:

```
Ollama
ElevenLabs
Backboard
```

---

# Offline Mode

The core AI should continue functioning without internet:

```
React
 ↓
FastAPI
 ↓
Ollama
 ↓
Gemma
```

Voice can gracefully indicate when ElevenLabs is unavailable.

---

# PHASE 12 — COMPLETE TESTING

Create a final verification suite.

---

## AI Tests

- [ ] Simple question
- [ ] Multi-turn question
- [ ] Context continuation
- [ ] Long response
- [ ] Empty prompt
- [ ] Invalid request
- [ ] Offline inference

---

## Voice Tests

- [ ] Microphone
- [ ] Speech recognition
- [ ] ElevenLabs TTS
- [ ] Playback
- [ ] Pause
- [ ] Resume
- [ ] Replay
- [ ] Interrupt
- [ ] Error handling
- [ ] Cache
- [ ] Offline fallback

---

## RAG Tests

- [ ] Exact section search
- [ ] Semantic question
- [ ] Source attribution
- [ ] Incorrect source rejection
- [ ] Missing source handling
- [ ] Versioned document handling

---

## Study Tests

- [ ] Add chapter
- [ ] Complete chapter
- [ ] Revision
- [ ] Notes
- [ ] Tasks
- [ ] Progress
- [ ] Streak
- [ ] Weak areas

---

## UI Tests

- [ ] Light mode
- [ ] Dark mode
- [ ] Responsive layout
- [ ] Companion
- [ ] Voice Orb
- [ ] Animations
- [ ] Loading states
- [ ] Error states

---

# PHASE 13 — PERFORMANCE OPTIMIZATION

## Goal

Make the application feel fast.

---

# Perceived Performance

When Gemma needs time:

Show:

```
Sathi is thinking...
```

with subtle animation.

Never leave the screen frozen.

---

# Optimize

- response streaming
- audio caching
- database queries
- vector retrieval
- frontend rendering
- lazy loading
- unnecessary API calls
- model loading behavior

---

# GPU

Verify:

```
nvidia-smi
```

Gemma should actually use the RTX GPU when configured.

---

# PHASE 14 — DEV CHALLENGE PREPARATION

## Goal

Prepare Sathi specifically for:

# DEV Hacktoberfest 2026
# Weekend Challenge 1 — Build for a Friend

---

# Story

The project should clearly communicate:

> I built Sathi for my sister, who is preparing for the CA examination.

The story is more important than simply listing technologies.

---

# Demo Flow

The demo should NOT show every feature.

Use a strong narrative.

---

## Demo 1 — Progress

Open Sathi.

Show:

```
Today's Progress
```

Show:

- chapters
- study goals
- progress
- tasks

---

## Demo 2 — Companion

Click the companion.

Speak:

```
Explain Section 17(5) to me in simple words.
```

Sathi:

```
Listens
→ Thinks
→ Answers
→ Speaks
```

---

## Demo 3 — Follow-up

Ask:

```
What is the easiest way to remember it?
```

Sathi remembers the previous conversation.

---

## Demo 4 — Study

Open a chapter.

Show:

```
Ask Sathi
Notes
Progress
Revision
```

---

## Demo 5 — RAG

Ask a factual CA question.

Show:

```
Source Verified
```

This demonstrates that Sathi is not simply hallucinating from Gemma.

---

## Demo 6 — Personalization

Show:

```
Weak Area
Revision Due
Study Recommendation
```

---

## Demo 7 — Sanctuary

Show:

```
Breathing
```

or

```
Thought Reframer
```

Keep this short.

---

# PHASE 15 — DOCUMENTATION

Create:

```
README.md
ARCHITECTURE.md
SATHI_FINAL_ROADMAP.md
```

---

# README

Include:

1. What is Sathi?
2. Why was it built?
3. Who is it for?
4. Features
5. Architecture
6. Technology stack
7. Local setup
8. Environment variables
9. Running instructions
10. Screenshots
11. Demo video
12. Privacy model
13. Future roadmap

---

# Architecture Documentation

Explain:

```
React
 ↓
FastAPI
 ↓
Orchestrator
 ├── Gemma
 ├── RAG
 ├── Memory
 ├── SQLite
 └── ElevenLabs
```

---

# PHASE 16 — FINAL DEMO POLISH

Before recording:

Remove:

- console errors
- broken buttons
- placeholder text
- fake data where possible
- unfinished screens
- debug indicators
- unnecessary UI

Check:

- animations
- voice
- typography
- spacing
- mobile/responsive behavior
- loading states
- error states

---

# FINAL FEATURE SET

The final Sathi experience should contain:

## HOME / PROGRESS

- Today's progress
- Study streak
- Upcoming revision
- Weak areas
- Daily tasks
- Current goal
- Study recommendation

---

## COMPANION

- Text chat
- Voice chat
- ElevenLabs
- Interruptible conversation
- Multi-turn context
- Response streaming
- Markdown rendering
- Source citations
- Save to notes

---

## STUDY

- Full CA syllabus
- Foundation
- Intermediate
- Final
- Groups
- Papers
- Modules
- Chapters
- Topics
- Progress
- Notes
- Revision
- Ask Sathi
- Add chapter

---

## PROGRESS

- Overall completion
- Subject completion
- Study streak
- Questions attempted
- Accuracy
- Weak topics
- Revision schedule

---

## SANCTUARY

- Breathing
- Thought reframing
- Calm environment
- Optional ambient sounds

---

## KNOWLEDGE

- RAG
- ICAI sources
- Statutory sources
- Source attribution
- Versioned documents
- Hybrid search

---

## MEMORY

- Conversation context
- Student state
- Personal preferences
- Weak areas
- Revision history

---

## AUDIO

- ElevenLabs voice
- Listening sounds
- Thinking sounds
- Completion sounds
- Task sounds
- Ambient study music
- Breathing audio

---

# FINAL ARCHITECTURE

```text
                         SATHI
                           │
              ┌────────────┴────────────┐
              │                         │
           React UI                 Voice Orb
              │                         │
              └────────────┬────────────┘
                           │
                       FastAPI
                           │
                    Sathi Orchestrator
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
      Gemma               RAG              Memory
        │                  │                  │
      Ollama         Knowledge Store     Student DB
        │                  │                  │
      RTX GPU        ICAI / Official      SQLite
                           │
                    Source Attribution
                           │
                      ElevenLabs
                           │
                         Voice
```

---

# IMPORTANT ARCHITECTURAL PRINCIPLE

Do NOT make Gemma responsible for everything.

Gemma:

- reasoning
- explanation
- conversation
- synthesis
- personalization

RAG:

- factual CA knowledge
- laws
- regulations
- study material
- current authoritative information

SQLite:

- exact student state
- syllabus
- tasks
- progress
- notes

Memory:

- conversational continuity
- personal preferences
- long-term context

ElevenLabs:

- voice

React:

- experience

FastAPI:

- orchestration and security

---

# FINAL ORDER OF EXECUTION

Do not skip ahead.

## STEP 1

Finish real-time voice conversation.

```
Listen
→ Understand
→ Think
→ Speak
→ Interrupt
→ Listen
```

## STEP 2

Finish Companion UI.

## STEP 3

Implement response rendering.

## STEP 4

Implement response streaming + animations.

## STEP 5

Implement dark mode and final visual system.

## STEP 6

Expand the complete CA syllabus.

## STEP 7

Implement RAG.

## STEP 8

Implement source attribution.

## STEP 9

Implement structured student memory.

## STEP 10

Evaluate Backboard.io integration.

## STEP 11

Add ElevenLabs sound effects.

## STEP 12

Add optional Copilot-style study music.

## STEP 13

Tune Gemma prompts and response behavior.

## STEP 14

Add advanced personalized study intelligence.

## STEP 15

Run complete test suite.

## STEP 16

Optimize performance.

## STEP 17

Clean UI and remove unfinished elements.

## STEP 18

Prepare DEV Challenge demo.

## STEP 19

Write README and architecture documentation.

## STEP 20

Record final demo.

## STEP 21

Submit.

---

# DEFINITION OF DONE

Sathi is considered complete for the DEV Challenge when:

- [ ] The application feels like a real product.
- [ ] The Companion can have natural voice conversations.
- [ ] ElevenLabs voice works reliably.
- [ ] The user can interrupt Sathi.
- [ ] Gemma maintains conversation context.
- [ ] Responses are beautifully rendered.
- [ ] Responses stream naturally.
- [ ] UI has polished animations.
- [ ] Light and dark themes work.
- [ ] Complete CA syllabus structure exists.
- [ ] Sathi can navigate the CA journey.
- [ ] RAG provides authoritative CA knowledge.
- [ ] Answers can show their sources.
- [ ] Student progress is persisted.
- [ ] Student memory is separated from factual knowledge.
- [ ] Study recommendations use actual student progress.
- [ ] Sounds enhance the experience without becoming distracting.
- [ ] The application works gracefully when external services fail.
- [ ] API keys are secure.
- [ ] No major console/backend errors remain.
- [ ] Demo flow is polished.
- [ ] README is complete.
- [ ] Architecture is documented.
- [ ] DEV Challenge requirements are satisfied.

---

# THE FINAL EXPERIENCE

The student should be able to open Sathi and see:

"Good evening.
You have 2h 40m planned today."

Then:

```
Today's Focus

Taxation
GST — Input Tax Credit
45 min

Auditing
SA 500 — Audit Evidence
40 min

Revision
Corporate Law
20 min
```

The student clicks the Companion.

The orb appears.

She says:

> "Sathi, explain blocked ITC again."

Sathi listens.

Gemma reasons using the conversation context + RAG.

The answer appears beautifully on screen.

ElevenLabs speaks the answer.

She interrupts:

> "Wait, what about food and beverages?"

Sathi stops speaking.

Sathi listens.

The conversation continues naturally.

Later:

```
Chapter Completed ✓

Next Revision:
7 days
```

That is the experience we are building.

---

# CORE PRINCIPLE

Do not build Sathi as:

"Gemma + some buttons."

Build it as:

> A complete personal environment for becoming a CA.

The AI is the brain.

The RAG is the knowledge.

The database is the memory.

The Companion is the personality.

The voice is the interaction.

The UI is the experience.

The study system is the structure.

And the student remains at the center.
```

### One important change from the earlier plan

I would **not make fine-tuning a required phase before submission**. Get the full experience working first. Your biggest gains now will come from **RAG + better prompts + structured context + response rendering**, not from trying to teach the 2B model the entire CA syllabus through fine-tuning.

And the order you just described is right:

**Voice → UI polish → response animations → dark mode → full syllabus → RAG → memory → sounds/music → Gemma tuning → testing → DEV submission.**
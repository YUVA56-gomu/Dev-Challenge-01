export const API_BASE = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function sendChatMessage(message, history = [], studyContext = null) {
  const payload = { message, history };
  if (studyContext) {
    payload.study_context = studyContext;
  }
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }
  return res.json();
}

export async function sendChatMessageStream(message, history = [], studyContext = null, onChunk, onMetadata, onDone, onError) {
  const payload = { message, history };
  if (studyContext) {
    payload.study_context = studyContext;
  }
  try {
    const res = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }
    
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6);
          try {
            const data = JSON.parse(dataStr);
            if (data.type === 'metadata' && onMetadata) onMetadata(data);
            else if (data.type === 'chunk' && onChunk) onChunk(data.content);
            else if (data.type === 'error' && onError) onError(new Error(data.content));
            else if (data.type === 'done' && onDone) onDone(data.spoken_reply);
          } catch (e) {}
        }
      }
    }
    if (buffer.startsWith('data: ')) {
      try {
        const data = JSON.parse(buffer.slice(6));
        if (data.type === 'chunk' && onChunk) onChunk(data.content);
        else if (data.type === 'done' && onDone) onDone(data.spoken_reply);
      } catch(e) {}
    }
  } catch (err) {
    if (onError) onError(err);
  }
}


export async function synthesizeVoice(text, voiceId = null) {
  try {
    const res = await fetch(`${API_BASE}/api/voice/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice_id: voiceId }),
    });

    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('audio/')) {
      const blob = await res.blob();
      return { type: 'audio', blob };
    } else {
      const data = await res.json();
      return { type: 'fallback', data };
    }
  } catch (err) {
    return { type: 'fallback', error: err.message };
  }
}

export async function fetchVoiceStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/voice/status`);
    return await res.json();
  } catch (err) {
    return { provider: 'unavailable', error: err.message };
  }
}


export async function reframeThought(thought) {
  const res = await fetch(`${API_BASE}/api/wellness/reframe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ thought }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }
  return res.json();
}

export async function fetchSubjects() {
  const res = await fetch(`${API_BASE}/api/study/subjects`);
  return res.json();
}

export async function updateChapterStatus(chapterId, status, notes = null) {
  const body = {};
  if (status !== null) body.status = status;
  if (notes !== null) body.notes = notes;
  
  const res = await fetch(`${API_BASE}/api/study/chapters/${chapterId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function fetchTasks() {
  const res = await fetch(`${API_BASE}/api/study/tasks`);
  return res.json();
}

export async function createTask(title, subjectId = null) {
  const res = await fetch(`${API_BASE}/api/study/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, subject_id: subjectId }),
  });
  return res.json();
}

export async function toggleTask(taskId) {
  const res = await fetch(`${API_BASE}/api/study/tasks/${taskId}/toggle`, {
    method: 'PATCH',
  });
  return res.json();
}

export async function deleteTask(taskId) {
  const res = await fetch(`${API_BASE}/api/study/tasks/${taskId}`, {
    method: 'DELETE',
  });
  return res.json();
}

export async function fetchProgress() {
  const res = await fetch(`${API_BASE}/api/study/progress`);
  return res.json();
}

// --- Phase 2: Full CA Syllabus & Recommendations ---

export async function fetchStages() {
  const res = await fetch(`${API_BASE}/api/study/stages`);
  return res.json();
}

export async function fetchHierarchy(stageId = 'stage_intermediate') {
  const res = await fetch(`${API_BASE}/api/study/hierarchy?stage_id=${stageId}`);
  return res.json();
}

export async function updateCAChapter(chapterId, updates) {
  const res = await fetch(`${API_BASE}/api/study/ca-chapters/${chapterId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  return res.json();
}

export async function updateCATopic(topicId, updates) {
  const res = await fetch(`${API_BASE}/api/study/ca-topics/${topicId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  return res.json();
}

export async function addCustomChapter(paperId, title, estimatedHours = 6, difficulty = 'Medium', learningObjective = '') {
  const res = await fetch(`${API_BASE}/api/study/custom-chapter`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      paper_id: paperId,
      title,
      estimated_hours: estimatedHours,
      difficulty,
      learning_objective: learningObjective,
    }),
  });
  return res.json();
}

export async function fetchStudyRecommendations(studentId = 'pooja') {
  const res = await fetch(`${API_BASE}/api/study/recommendations?student_id=${studentId}`);
  return res.json();
}

export async function fetchMemoryProfile(studentId = 'pooja') {
  const res = await fetch(`${API_BASE}/api/memory/profile?student_id=${studentId}`);
  return res.json();
}

// --- Phase 3: Practice & Answer Evaluation Endpoints ---

export async function fetchPracticeQuestions(filters = {}) {
  const params = new URLSearchParams();
  if (filters.stage_id) params.append('stage_id', filters.stage_id);
  if (filters.paper_id) params.append('paper_id', filters.paper_id);
  if (filters.chapter_id) params.append('chapter_id', filters.chapter_id);
  if (filters.topic_id) params.append('topic_id', filters.topic_id);
  if (filters.difficulty) params.append('difficulty', filters.difficulty);
  if (filters.question_type) params.append('question_type', filters.question_type);
  if (filters.source_type) params.append('source_type', filters.source_type);
  if (filters.is_official !== undefined) params.append('is_official', filters.is_official);
  if (filters.limit) params.append('limit', filters.limit);

  const res = await fetch(`${API_BASE}/api/practice/questions?${params.toString()}`);
  return res.json();
}

export async function fetchQuestionById(questionId) {
  const res = await fetch(`${API_BASE}/api/practice/questions/${questionId}`);
  return res.json();
}

export async function generatePracticeQuestion(payload) {
  const res = await fetch(`${API_BASE}/api/practice/questions/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function submitPracticeAnswer(payload) {
  const res = await fetch(`${API_BASE}/api/practice/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function fetchPracticeStats(studentId = 'pooja') {
  const res = await fetch(`${API_BASE}/api/practice/stats?student_id=${studentId}`);
  return res.json();
}

export async function fetchWeakAreas(studentId = 'pooja') {
  const res = await fetch(`${API_BASE}/api/practice/weak-areas?student_id=${studentId}`);
  return res.json();
}

export async function fetchDueRevisions(studentId = 'pooja') {
  const res = await fetch(`${API_BASE}/api/practice/revisions?student_id=${studentId}`);
  return res.json();
}

export async function completeRevision(revisionId) {
  const res = await fetch(`${API_BASE}/api/practice/revisions/${revisionId}/complete`, {
    method: 'POST',
  });
  return res.json();
}

export async function startExamSession(payload) {
  const res = await fetch(`${API_BASE}/api/practice/exam/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function fetchExamSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/practice/exam/${sessionId}`);
  return res.json();
}

export async function submitExamSession(sessionId, payload) {
  const res = await fetch(`${API_BASE}/api/practice/exam/${sessionId}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

// --- Phase 4: Full ICAI Knowledge & Corpus API ---

export async function fetchCorpusStats() {
  const res = await fetch(`${API_BASE}/api/practice/corpus/stats`);
  return res.json();
}

export async function fetchKnowledgeDocs() {
  const res = await fetch(`${API_BASE}/api/knowledge/documents`);
  return res.json();
}

export async function fetchKnowledgeStats() {
  const res = await fetch(`${API_BASE}/api/knowledge/stats`);
  return res.json();
}

export async function searchKnowledge(payload) {
  const res = await fetch(`${API_BASE}/api/knowledge/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function ingestDocument(payload) {
  const res = await fetch(`${API_BASE}/api/knowledge/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}



// --- Sanctuary: Reflections, Check-ins, Focus Sessions ---

export async function saveSanctuaryReflection(reflectionText, studentId = 'pooja') {
  const res = await fetch(`${API_BASE}/api/sanctuary/reflections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reflection_text: reflectionText, student_id: studentId }),
  });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function fetchSanctuaryReflections(studentId = 'pooja', limit = 10) {
  const res = await fetch(`${API_BASE}/api/sanctuary/reflections?student_id=${studentId}&limit=${limit}`);
  return res.json();
}

export async function saveSanctuaryCheckin(mood, studentId = 'pooja') {
  const res = await fetch(`${API_BASE}/api/sanctuary/checkin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mood, student_id: studentId }),
  });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function fetchLatestCheckin(studentId = 'pooja') {
  try {
    const res = await fetch(`${API_BASE}/api/sanctuary/checkin/latest?student_id=${studentId}`);
    return res.json();
  } catch {
    return { mood: null };
  }
}

export async function saveFocusSession(durationMinutes, completed = false, studentId = 'pooja') {
  const res = await fetch(`${API_BASE}/api/sanctuary/focus-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ duration_minutes: durationMinutes, completed, student_id: studentId }),
  });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function fetchFocusSessions(studentId = 'pooja', limit = 20) {
  const res = await fetch(`${API_BASE}/api/sanctuary/focus-sessions?student_id=${studentId}&limit=${limit}`);
  return res.json();
}

// --- ElevenLabs configuration ---

export async function configureElevenLabs(apiKey, voiceId = null) {
  const res = await fetch(`${API_BASE}/api/settings/elevenlabs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey, voice_id: voiceId }),
  });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function fetchVoiceConfigStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/settings/voice-status`);
    return res.json();
  } catch {
    return { elevenlabs_configured: false, provider: 'unavailable' };
  }
}

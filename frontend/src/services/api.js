export const API_BASE = 'http://localhost:8000';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function sendChatMessage(message, history = []) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }
  return res.json();
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

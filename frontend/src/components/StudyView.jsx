import React, { useState, useEffect } from 'react';
import { fetchSubjects, updateChapterStatus } from '../services/api';

export default function StudyView({ onAskInChat }) {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeNotesChapter, setActiveNotesChapter] = useState(null);
  const [noteText, setNoteText] = useState('');
  const [savingNote, setSavingNote] = useState(false);

  const loadData = async () => {
    try {
      const data = await fetchSubjects();
      setSubjects(data);
      if (data.length > 0 && !selectedSubjectId) {
        setSelectedSubjectId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load subjects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleStatusChange = async (chapterId, newStatus) => {
    try {
      await updateChapterStatus(chapterId, newStatus);
      await loadData();
    } catch (err) {
      alert('Could not update chapter status');
    }
  };

  const openNotesModal = (chapter) => {
    setActiveNotesChapter(chapter);
    setNoteText(chapter.notes || '');
  };

  const saveNotes = async () => {
    if (!activeNotesChapter) return;
    setSavingNote(true);
    try {
      await updateChapterStatus(activeNotesChapter.id, null, noteText);
      setActiveNotesChapter(null);
      await loadData();
    } catch (err) {
      alert('Failed to save notes');
    } finally {
      setSavingNote(false);
    }
  };

  const selectedSubject = subjects.find((s) => s.id === selectedSubjectId);

  if (loading) {
    return (
      <div className="view-container loading-center">
        <div className="pulsing-spinner"></div>
        <p>Loading CA Syllabus modules...</p>
      </div>
    );
  }

  return (
    <div className="view-container study-view">
      <div className="view-header">
        <div>
          <h2>CA Syllabus & Study Tracker</h2>
          <p className="view-subtitle">
            Track your chapters, review notes, and monitor completion progress across CA papers.
          </p>
        </div>
      </div>

      <div className="study-layout">
        {/* Left Column: Subjects List */}
        <aside className="subjects-sidebar">
          <div className="sidebar-heading">Papers / Subjects</div>
          <div className="subjects-nav-list">
            {subjects.map((sub) => (
              <button
                key={sub.id}
                className={`subject-nav-card ${selectedSubjectId === sub.id ? 'active' : ''}`}
                onClick={() => setSelectedSubjectId(sub.id)}
              >
                <div className="subject-card-header">
                  <span className="subject-code-tag">{sub.code}</span>
                  <span className="subject-pct">{sub.progress_percentage}%</span>
                </div>
                <div className="subject-name">{sub.name}</div>
                <div className="mini-progress-bar">
                  <div
                    className="mini-progress-fill"
                    style={{ width: `${sub.progress_percentage}%` }}
                  ></div>
                </div>
                <div className="subject-meta-count">
                  {sub.completed_chapters} of {sub.total_chapters} chapters completed
                </div>
              </button>
            ))}
          </div>
        </aside>

        {/* Right Column: Chapters Detail */}
        <main className="chapters-main">
          {selectedSubject && (
            <div className="subject-detail-card">
              <div className="subject-detail-header">
                <div>
                  <span className="badge-tag">{selectedSubject.group_name}</span>
                  <h3>{selectedSubject.code}: {selectedSubject.name}</h3>
                </div>
                <div className="overall-subject-pct">
                  <span className="pct-num">{selectedSubject.progress_percentage}%</span>
                  <span className="pct-label">Completed</span>
                </div>
              </div>

              <div className="chapters-list">
                {selectedSubject.chapters.map((ch) => (
                  <div key={ch.id} className={`chapter-item-card status-${ch.status}`}>
                    <div className="chapter-info">
                      <div className="chapter-title-row">
                        <span className="ch-num">Ch {ch.chapter_num}</span>
                        <h4 className="ch-title">{ch.title}</h4>
                      </div>
                      {ch.notes && (
                        <div className="ch-notes-preview">
                          <span className="notes-icon">📝</span> {ch.notes}
                        </div>
                      )}
                    </div>

                    <div className="chapter-actions">
                      {/* Status selector */}
                      <select
                        className={`status-select ${ch.status}`}
                        value={ch.status}
                        onChange={(e) => handleStatusChange(ch.id, e.target.value)}
                      >
                        <option value="not_started">⏳ Not Started</option>
                        <option value="in_progress">🔄 In Progress</option>
                        <option value="completed">✅ Completed</option>
                      </select>

                      {/* Notes button */}
                      <button
                        className="action-icon-btn"
                        onClick={() => openNotesModal(ch)}
                        title="Add/Edit chapter revision notes"
                      >
                        📝 Notes
                      </button>

                      {/* Ask Sathi in chat button */}
                      {onAskInChat && (
                        <button
                          className="action-icon-btn ask-btn"
                          onClick={() => onAskInChat(`Explain key concepts from Chapter ${ch.chapter_num}: ${ch.title} in ${selectedSubject.name}.`)}
                          title="Ask Gemma about this chapter"
                        >
                          💬 Ask Sathi
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Notes Modal */}
      {activeNotesChapter && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3>Chapter Revision Notes</h3>
            <p className="modal-sub">
              Ch {activeNotesChapter.chapter_num}: {activeNotesChapter.title}
            </p>
            <textarea
              className="notes-textarea"
              rows={6}
              placeholder="Write formulas, section numbers, key exam adjustments, or mnemonics..."
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
            />
            <div className="modal-actions">
              <button
                className="secondary-button"
                onClick={() => setActiveNotesChapter(null)}
                disabled={savingNote}
              >
                Cancel
              </button>
              <button
                className="primary-button"
                onClick={saveNotes}
                disabled={savingNote}
              >
                {savingNote ? 'Saving...' : 'Save Notes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

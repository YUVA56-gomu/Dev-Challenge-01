import React, { useState, useEffect } from 'react';

/**
 * NotesView Component
 * Dedicated revision notes bank for CA concepts, summaries, and key formula sheets.
 */
export default function NotesView({ onAskInChat }) {
  const [notes, setNotes] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [newNoteText, setNewNoteText] = useState('');
  const [newNoteSubject, setNewNoteSubject] = useState('Accounting');

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('sathi_saved_notes') || '[]');
      if (saved.length === 0) {
        // Seed default high-yield revision notes
        const defaultNotes = [
          {
            id: '1',
            subject: 'Taxation',
            text: 'Section 17(5) - Ineligible / Blocked ITC: Motor vehicles for transport of persons having seating capacity <= 13 persons (including driver), except when used for transportation of goods, making taxable supply of vehicles, or imparting training.',
            savedAt: 'Today at 08:30',
          },
          {
            id: '2',
            subject: 'Auditing',
            text: 'SA 200 - Inherent Limitations of an Audit: Nature of financial reporting, nature of audit procedures (management may not provide full info), timeliness of financial reporting, balance between benefit and cost.',
            savedAt: 'Yesterday at 17:15',
          },
          {
            id: '3',
            subject: 'Accounting',
            text: 'AS 10 (Property, Plant and Equipment): Initial measurement at cost. Subsequent expenditure recognized only if future economic benefits flow to enterprise. Component accounting is mandatory for significant parts.',
            savedAt: '2 days ago',
          },
        ];
        localStorage.setItem('sathi_saved_notes', JSON.stringify(defaultNotes));
        setNotes(defaultNotes);
      } else {
        setNotes(saved);
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  const handleAddNote = (e) => {
    e.preventDefault();
    if (!newNoteText.trim()) return;

    const newNote = {
      id: Date.now().toString(),
      subject: newNoteSubject,
      text: newNoteText.trim(),
      savedAt: 'Just now',
    };

    const updated = [newNote, ...notes];
    setNotes(updated);
    localStorage.setItem('sathi_saved_notes', JSON.stringify(updated));
    setNewNoteText('');
  };

  const handleDelete = (id) => {
    const updated = notes.filter((n) => n.id !== id);
    setNotes(updated);
    localStorage.setItem('sathi_saved_notes', JSON.stringify(updated));
  };

  const filtered = notes.filter(
    (n) =>
      n.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (n.subject && n.subject.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="view-container notes-view">
      <div className="view-header">
        <div>
          <h2>Revision Notes & Formula Bank</h2>
          <p className="view-subtitle">
            Saved CA concepts, statutory provisions, and high-yield exam takeaways.
          </p>
        </div>
      </div>

      {/* Add New Note Bar */}
      <div className="add-note-card">
        <form onSubmit={handleAddNote} className="add-note-form">
          <div className="note-form-top">
            <select
              value={newNoteSubject}
              onChange={(e) => setNewNoteSubject(e.target.value)}
              className="note-subject-select"
            >
              <option value="Accounting">Accounting (AS / Ind AS)</option>
              <option value="Corporate Law">Corporate & Other Laws</option>
              <option value="Costing">Cost & Management Accounting</option>
              <option value="Taxation">Taxation (Income Tax & GST)</option>
              <option value="Auditing">Auditing & Ethics</option>
            </select>
            <input
              type="text"
              placeholder="Search existing notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="notes-search-input"
            />
          </div>

          <textarea
            placeholder="Write a quick revision note or statutory section summary..."
            value={newNoteText}
            onChange={(e) => setNewNoteText(e.target.value)}
            rows={2}
            className="notes-textarea"
          />

          <div className="note-form-bottom">
            <button type="submit" className="primary-button" disabled={!newNoteText.trim()}>
              + Save Note
            </button>
          </div>
        </form>
      </div>

      {/* Notes Grid */}
      <div className="notes-cards-grid">
        {filtered.length === 0 ? (
          <div className="empty-tasks-state">No notes found matching your search.</div>
        ) : (
          filtered.map((note) => (
            <div key={note.id} className="note-card">
              <div className="note-card-header">
                <span className="note-subject-badge">{note.subject || 'General'}</span>
                <span className="note-date">{note.savedAt}</span>
              </div>
              <p className="note-body-text">{note.text}</p>
              <div className="note-card-actions">
                <button
                  className="action-pill-btn"
                  onClick={() => {
                    navigator.clipboard.writeText(note.text);
                    alert('Note copied to clipboard!');
                  }}
                  title="Copy to clipboard"
                >
                  📋 Copy
                </button>
                <button
                  className="action-pill-btn"
                  onClick={() => {
                    if (onAskInChat) onAskInChat(`Can you explain and test me on this note:\n"${note.text}"`);
                  }}
                  title="Ask Sathi to quiz me on this"
                >
                  🤖 Quiz me
                </button>
                <button
                  className="action-pill-btn danger"
                  onClick={() => handleDelete(note.id)}
                  title="Delete note"
                >
                  ✕ Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import {
  fetchStages,
  fetchHierarchy,
  updateCAChapter,
  updateCATopic,
  addCustomChapter,
} from '../services/api';
import { soundService } from '../services/soundService';

/**
 * Phase 5 StudyView Component - Complete CA Knowledge & Academic Workspace
 */
export default function StudyView({ onAskInChat, onNavigateToPractice }) {
  const [stages, setStages] = useState([]);
  const [selectedStageId, setSelectedStageId] = useState('stage_intermediate');
  const [hierarchy, setHierarchy] = useState(null);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [selectedPaperId, setSelectedPaperId] = useState(null);
  const [expandedModules, setExpandedModules] = useState({});
  const [expandedTopics, setExpandedTopics] = useState({});
  const [loading, setLoading] = useState(true);

  // Add Chapter Modal State
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [newChapTitle, setNewChapTitle] = useState('');
  const [newChapHours, setNewChapHours] = useState(6);
  const [newChapDifficulty, setNewChapDifficulty] = useState('Medium');
  const [submittingChap, setSubmittingChap] = useState(false);

  // Focused Study Session Drawer
  const [focusedChapter, setFocusedChapter] = useState(null);
  const [focusedContext, setFocusedContext] = useState(null);
  const [practiceAnswerVisible, setPracticeAnswerVisible] = useState(false);

  // Notes Modal state
  const [activeNotesItem, setActiveNotesItem] = useState(null); // { type: 'chapter'|'topic', item, context }
  const [noteContent, setNoteContent] = useState('');
  const [savingNote, setSavingNote] = useState(false);

  // Load stages on mount
  useEffect(() => {
    async function initStages() {
      try {
        const stageList = await fetchStages();
        if (Array.isArray(stageList) && stageList.length > 0) {
          setStages(stageList);
          // Default to intermediate if available, else first
          const inter = stageList.find((s) => s.code === 'INTER');
          setSelectedStageId(inter ? inter.id : stageList[0].id);
        }
      } catch (err) {
        console.error('Failed to load stages:', err);
      }
    }
    initStages();
  }, []);

  // Load hierarchy when stage changes
  const loadHierarchyData = async (stageId) => {
    setLoading(true);
    try {
      const data = await fetchHierarchy(stageId);
      setHierarchy(data);

      if (data && data.groups && data.groups.length > 0) {
        setSelectedGroupId(data.groups[0].id);
        if (data.groups[0].papers && data.groups[0].papers.length > 0) {
          setSelectedPaperId(data.groups[0].papers[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load hierarchy for stage:', stageId, err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedStageId) {
      loadHierarchyData(selectedStageId);
    }
  }, [selectedStageId]);

  // When group changes, auto-select first paper of that group
  const handleGroupSelect = (groupId) => {
    setSelectedGroupId(groupId);
    const grp = hierarchy?.groups?.find((g) => g.id === groupId);
    if (grp && grp.papers && grp.papers.length > 0) {
      setSelectedPaperId(grp.papers[0].id);
    } else {
      setSelectedPaperId(null);
    }
  };

  // Toggle module accordion
  const toggleModule = (modId) => {
    setExpandedModules((prev) => ({
      ...prev,
      [modId]: prev[modId] === undefined ? true : !prev[modId],
    }));
  };

  // Toggle chapter topics accordion
  const toggleTopics = (chapId) => {
    setExpandedTopics((prev) => ({
      ...prev,
      [chapId]: !prev[chapId],
    }));
  };

  // Update chapter status or confidence
  const handleChapterUpdate = async (chapterId, updates) => {
    try {
      if (updates.status === 'completed') {
        soundService.playSound('chapter_complete');
      }
      await updateCAChapter(chapterId, updates);
      await loadHierarchyData(selectedStageId);
      if (focusedChapter && focusedChapter.id === chapterId) {
        setFocusedChapter((prev) => ({ ...prev, ...updates }));
      }
    } catch (err) {
      console.error('Failed to update chapter:', err);
      alert('Could not update chapter');
    }
  };

  // Increment revision count
  const handleIncrementRevision = async (chapterId) => {
    try {
      await updateCAChapter(chapterId, { increment_revision: true });
      await loadHierarchyData(selectedStageId);
      if (focusedChapter && focusedChapter.id === chapterId) {
        setFocusedChapter((prev) => ({
          ...prev,
          revision_count: (prev.revision_count || 0) + 1,
          last_revised: 'Just now',
        }));
      }
    } catch (err) {
      console.error('Failed to increment revision:', err);
    }
  };

  // Add Custom Chapter submit handler
  const handleAddCustomChapterSubmit = async (e) => {
    e.preventDefault();
    if (!newChapTitle.trim() || !selectedPaperId) return;
    setSubmittingChap(true);
    try {
      await addCustomChapter(
        selectedPaperId,
        newChapTitle.trim(),
        Number(newChapHours) || 6,
        newChapDifficulty
      );
      setAddModalOpen(false);
      setNewChapTitle('');
      setNewChapHours(6);
      await loadHierarchyData(selectedStageId);
    } catch (err) {
      console.error('Failed to create custom chapter:', err);
      alert('Could not add custom chapter');
    } finally {
      setSubmittingChap(false);
    }
  };

  // Update topic status or confidence
  const handleTopicUpdate = async (topicId, updates) => {
    try {
      await updateCATopic(topicId, updates);
      await loadHierarchyData(selectedStageId);
    } catch (err) {
      console.error('Failed to update topic:', err);
    }
  };

  // Open Notes Modal
  const openNotes = (type, item, context) => {
    setActiveNotesItem({ type, item, context });
    setNoteContent(item.notes || '');
  };

  const saveNotes = async () => {
    if (!activeNotesItem) return;
    setSavingNote(true);
    try {
      if (activeNotesItem.type === 'chapter') {
        await handleChapterUpdate(activeNotesItem.item.id, { notes: noteContent });
      } else {
        await handleTopicUpdate(activeNotesItem.item.id, { notes: noteContent });
      }
      setActiveNotesItem(null);
    } catch (err) {
      alert('Failed to save notes');
    } finally {
      setSavingNote(false);
    }
  };

  // Launch Ask Sathi with rich syllabus context
  const handleAskSathi = (contextData) => {
    const { stage, group, paper, module, chapter, topic } = contextData;
    const target = topic || chapter || paper || 'this syllabus topic';
    const promptText = `Can you guide me through ${target} with conceptual clarity, practical examples, and high-yield exam tips?`;

    if (onAskInChat) {
      onAskInChat(promptText, {
        stage,
        group,
        paper,
        module,
        chapter,
        topic,
      });
    }
  };

  // Launch focused study session
  const openFocusedStudySession = (chapter, context) => {
    setFocusedChapter(chapter);
    setFocusedContext(context);
    setPracticeAnswerVisible(false);
  };

  // Helpers to resolve selected objects
  const currentGroup = hierarchy?.groups?.find((g) => g.id === selectedGroupId) || hierarchy?.groups?.[0];
  const currentPaper = currentGroup?.papers?.find((p) => p.id === selectedPaperId) || currentGroup?.papers?.[0];

  return (
    <div className="study-workspace">
      {/* Stage Selector Header */}
      <header className="workspace-header">
        <div className="workspace-title-group">
          <span className="workspace-eyebrow">ICAI Syllabus 2024–2025 · New Scheme</span>
          <h1 className="workspace-title">CA Knowledge Engine & Syllabus</h1>
        </div>

        {/* Stage Selection Pills */}
        <div className="stage-selector-pills">
          {stages.map((stg) => (
            <button
              key={stg.id}
              className={`stage-pill-btn ${selectedStageId === stg.id ? 'active' : ''}`}
              onClick={() => setSelectedStageId(stg.id)}
            >
              <span className="stage-pill-code">{stg.code}</span>
              <span className="stage-pill-name">{stg.name}</span>
            </button>
          ))}
        </div>
      </header>

      {/* Group Navigation Tabs */}
      {hierarchy?.groups && hierarchy.groups.length > 0 && (
        <div className="groups-nav-bar">
          <span className="groups-bar-label">Curriculum Track:</span>
          <div className="groups-tab-list">
            {hierarchy.groups.map((grp) => (
              <button
                key={grp.id}
                className={`group-tab-button ${selectedGroupId === grp.id ? 'active' : ''}`}
                onClick={() => handleGroupSelect(grp.id)}
              >
                {grp.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <div className="view-container loading-center">
          <div className="pulsing-spinner-soft"></div>
          <p>Loading authoritative CA curriculum tree...</p>
        </div>
      ) : (
        <div className="study-two-column-layout">
          {/* Left Rail: Papers List */}
          <aside className="papers-selector-rail">
            <div className="rail-header-row">
              <span className="rail-heading">Papers</span>
              <span className="rail-badge">{currentGroup?.papers?.length || 0} Papers</span>
            </div>
            <div className="papers-menu">
              {currentGroup?.papers?.map((paper) => {
                const isSelected = paper.id === (currentPaper?.id || selectedPaperId);
                const allChapters = paper.modules?.flatMap((m) => m.chapters || []) || [];
                const completedCount = allChapters.filter((c) => c.status === 'completed').length;
                const progressPct = allChapters.length > 0 ? Math.round((completedCount / allChapters.length) * 100) : 0;

                return (
                  <button
                    key={paper.id}
                    className={`paper-tab-row ${isSelected ? 'active' : ''}`}
                    onClick={() => setSelectedPaperId(paper.id)}
                  >
                    <div className="paper-tab-main">
                      <span className="paper-tab-code">Paper {paper.paper_num}</span>
                      <span className="paper-tab-name">{paper.name}</span>
                    </div>
                    <span className="paper-tab-pct">{progressPct}%</span>
                  </button>
                );
              })}
            </div>
          </aside>

          {/* Right Main Pane: Modules -> Chapters -> Topics */}
          <main className="paper-chapters-pane">
            {currentPaper ? (
              <div className="paper-sheet">
                {/* Paper Summary Card */}
                <div className="paper-header-strip">
                  <div>
                    <span className="group-badge">{currentGroup?.name}</span>
                    <h2 className="paper-display-title">
                      Paper {currentPaper.paper_num}: {currentPaper.name}
                    </h2>
                    <p className="paper-sub-desc">
                      Authoritative ICAI Study Material Modules · Statutory References · Exam Weightage
                    </p>
                  </div>

                  <div className="paper-header-actions">
                    <button
                      className="add-custom-chapter-btn"
                      onClick={() => setAddModalOpen(true)}
                    >
                      ➕ Add Chapter
                    </button>

                    <button
                      className="ask-sathi-pill-btn"
                      onClick={() =>
                        handleAskSathi({
                          stage: hierarchy?.name,
                          group: currentGroup?.name,
                          paper: currentPaper.name,
                        })
                      }
                      title="Ask Sathi about this entire paper"
                    >
                      💬 Ask Sathi on Paper
                    </button>
                  </div>
                </div>

                {/* Modules Accordion */}
                <div className="modules-stack">
                  {currentPaper.modules?.map((mod) => {
                    const isExpanded = expandedModules[mod.id] !== false; // Default open
                    const totalChaps = mod.chapters?.length || 0;
                    const doneChaps = mod.chapters?.filter((c) => c.status === 'completed').length || 0;

                    return (
                      <section key={mod.id} className="module-card-section">
                        <div
                          className="module-card-header"
                          onClick={() => toggleModule(mod.id)}
                        >
                          <div className="module-title-box">
                            <span className="module-expand-icon">{isExpanded ? '▼' : '►'}</span>
                            <span className="module-pill-tag">Module {mod.module_num}</span>
                            <h3 className="module-heading">{mod.name}</h3>
                          </div>
                          <div className="module-meta-box">
                            <span className="module-progress-chip">
                              {doneChaps}/{totalChaps} Chapters
                            </span>
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="module-chapters-body">
                            {mod.chapters?.map((ch) => {
                              const topicsOpen = expandedTopics[ch.id];
                              const contextObj = {
                                stage: hierarchy?.name,
                                group: currentGroup?.name,
                                paper: currentPaper.name,
                                module: mod.name,
                                chapter: ch.title,
                              };

                              return (
                                <article key={ch.id} className={`chapter-scalable-card ${ch.status}`}>
                                  {/* Chapter Top Bar */}
                                  <div className="chapter-main-row">
                                    <div className="chapter-info-col">
                                      <div className="ch-eyebrow-row">
                                        <span className="ch-num-badge">CH {ch.chapter_num}</span>
                                        {ch.statutory_reference && (
                                          <span className="statutory-pill" title="Official statutory provision or standard">
                                            📜 {ch.statutory_reference}
                                          </span>
                                        )}
                                        {ch.revision_count > 0 && (
                                          <span className="revision-pill">
                                            🔁 Rev {ch.revision_count}
                                          </span>
                                        )}
                                      </div>
                                      <h4 className="ch-headline">{ch.title}</h4>

                                      {ch.notes && (
                                        <div
                                          className="ch-attached-note-banner"
                                          onClick={() => openNotes('chapter', ch, contextObj)}
                                        >
                                          <span className="note-icon">📝</span>
                                          <span className="note-preview">{ch.notes}</span>
                                        </div>
                                      )}
                                    </div>

                                    {/* Chapter Controls & Actions */}
                                    <div className="chapter-controls-col">
                                      {/* Status Selector */}
                                      <select
                                        className={`ca-status-dropdown ${ch.status}`}
                                        value={ch.status}
                                        onChange={(e) =>
                                          handleChapterUpdate(ch.id, { status: e.target.value })
                                        }
                                      >
                                        <option value="not_started">○ Not Started</option>
                                        <option value="in_progress">→ In Progress</option>
                                        <option value="completed">✓ Completed</option>
                                        <option value="needs_revision">⚠ Needs Revision</option>
                                      </select>

                                      {/* Confidence Rating (1-5) */}
                                      <div className="confidence-meter" title="Self-assessed confidence (1-5)">
                                        <span className="confidence-label">Conf:</span>
                                        {[1, 2, 3, 4, 5].map((lvl) => (
                                          <button
                                            key={lvl}
                                            type="button"
                                            className={`conf-dot-btn ${lvl <= (ch.confidence_score || 0) ? 'filled' : ''}`}
                                            onClick={() =>
                                              handleChapterUpdate(ch.id, { confidence_score: lvl })
                                            }
                                          >
                                            ★
                                          </button>
                                        ))}
                                      </div>

                                      {/* Primary Actions Group */}
                                      <div className="ch-actions-bar">
                                        <button
                                          className="action-link-btn"
                                          onClick={() => openNotes('chapter', ch, contextObj)}
                                          title="Personal chapter notes"
                                        >
                                          📝 Notes
                                        </button>

                                        <button
                                          className="action-link-btn focus-study-btn"
                                          onClick={() => openFocusedStudySession(ch, contextObj)}
                                          title="Open focused study session"
                                        >
                                          📖 Study Chapter
                                        </button>

                                        {onNavigateToPractice && (
                                          <button
                                            className="action-link-btn practice-action-btn"
                                            onClick={() => onNavigateToPractice(currentPaper?.id, ch.id)}
                                            title="Practice questions for this chapter"
                                          >
                                            ✍️ Practice
                                          </button>
                                        )}

                                        <button
                                          className="action-link-btn ask-sathi-btn"
                                          onClick={() => handleAskSathi(contextObj)}
                                          title="Ask Sathi with chapter context"
                                        >
                                          💬 Ask Sathi
                                        </button>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Topics Toggle Footer */}
                                  {ch.topics && ch.topics.length > 0 && (
                                    <div className="topics-toggle-strip">
                                      <button
                                        className="topics-accordion-btn"
                                        onClick={() => toggleTopics(ch.id)}
                                      >
                                        {topicsOpen ? '▲ Hide Topics' : `▼ View Topics (${ch.topics.length})`}
                                      </button>
                                      <span className="topics-subtext">
                                        Sub-sections, statutory clauses & exam weightage
                                      </span>
                                    </div>
                                  )}

                                  {/* Detailed Topics List */}
                                  {topicsOpen && ch.topics && (
                                    <div className="topics-sub-container">
                                      {ch.topics.map((top) => {
                                        const topicContext = {
                                          ...contextObj,
                                          topic: top.title,
                                        };

                                        return (
                                          <div key={top.id} className={`topic-row-item ${top.status}`}>
                                            <div className="topic-left-details">
                                              <div className="topic-header-line">
                                                <span className="topic-tag">Topic {top.topic_num}</span>
                                                <h5 className="topic-title-text">{top.title}</h5>
                                                {top.statutory_section && (
                                                  <span className="topic-statute-badge">
                                                    {top.statutory_section}
                                                  </span>
                                                )}
                                                {top.exam_weightage && (
                                                  <span className={`exam-weightage-badge ${top.exam_weightage.toLowerCase()}`}>
                                                    {top.exam_weightage} Weight
                                                  </span>
                                                )}
                                              </div>

                                              {top.learning_objective && (
                                                <p className="topic-objective-text">
                                                  <strong>Objective:</strong> {top.learning_objective}
                                                </p>
                                              )}
                                            </div>

                                            <div className="topic-right-actions">
                                              {/* Topic Status */}
                                              <select
                                                className={`topic-status-select ${top.status}`}
                                                value={top.status}
                                                onChange={(e) =>
                                                  handleTopicUpdate(top.id, { status: e.target.value })
                                                }
                                              >
                                                <option value="not_started">○ Not Started</option>
                                                <option value="in_progress">→ In Progress</option>
                                                <option value="completed">✓ Completed</option>
                                                <option value="needs_revision">⚠ Revise</option>
                                              </select>

                                              <button
                                                className="topic-action-btn"
                                                onClick={() => openNotes('topic', top, topicContext)}
                                                title="Topic Notes"
                                              >
                                                📝
                                              </button>

                                              {onNavigateToPractice && (
                                                <button
                                                  className="topic-action-btn practice"
                                                  onClick={() => onNavigateToPractice(currentPaper?.id, ch.id)}
                                                  title="Practice questions for this topic"
                                                >
                                                  ✍️ Practice
                                                </button>
                                              )}

                                              <button
                                                className="topic-ask-btn"
                                                onClick={() => handleAskSathi(topicContext)}
                                                title="Ask Sathi on this exact topic"
                                              >
                                                💬 Ask Sathi
                                              </button>
                                            </div>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  )}
                                </article>
                              );
                            })}
                          </div>
                        )}
                      </section>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="paper-sheet empty-selection">
                <p>Select a paper from the left rail to view syllabus modules and chapters.</p>
              </div>
            )}
          </main>
        </div>
      )}

      {/* ========================================================
          FOCUSED STUDY SESSION DRAWER / MODAL (Phase 2K)
          1. What you'll learn
          2. Explain
          3. Example
          4. Ask Sathi
          5. Practice
          6. Mark complete
          7. Add notes
          8. Schedule revision
         ======================================================== */}
      {focusedChapter && (
        <div className="modal-backdrop" onClick={() => setFocusedChapter(null)}>
          <div
            className="modal-card focused-study-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="focused-study-header">
              <div className="focused-header-info">
                <span className="focused-eyebrow">
                  {focusedContext?.paper} · CH {focusedChapter.chapter_num}
                </span>
                <h2 className="focused-title">{focusedChapter.title}</h2>
                {focusedChapter.statutory_reference && (
                  <span className="focused-statutory-tag">
                    📜 {focusedChapter.statutory_reference}
                  </span>
                )}
              </div>
              <button
                className="modal-close-btn"
                onClick={() => setFocusedChapter(null)}
                aria-label="Close study session"
              >
                ✕
              </button>
            </div>

            <div className="focused-study-body">
              {/* 1. What You'll Learn */}
              <section className="focused-section-card">
                <h4 className="section-step-label">1. What You'll Learn</h4>
                <ul className="learning-points-list">
                  <li>Understand the statutory basis under {focusedChapter.statutory_reference || 'ICAI standards'}.</li>
                  <li>Master high-yield practical exam adjustments and disclosure requirements.</li>
                  <li>Identify common student exam traps, disqualified provisions, and presentation caveats.</li>
                </ul>
              </section>

              {/* 2. Conceptual Explanation */}
              <section className="focused-section-card">
                <h4 className="section-step-label">2. Core Conceptual Breakdown</h4>
                <p className="concept-explanation-text">
                  This chapter covers essential statutory frameworks under ICAI curriculum. Pay close attention to eligibility conditions, negative lists, and timing rules. Where applicable, distinguish between mandatory legal provisions and standard audit or accounting practice.
                </p>
                <div className="statutory-callout-box">
                  <strong>Key Statutory Reference:</strong> {focusedChapter.statutory_reference || 'ICAI Study Material'}
                  <p className="callout-small">
                    Always reference exact section numbers or Standard paragraphs in exam answers to secure full presentation marks.
                  </p>
                </div>
              </section>

              {/* 3. Practical CA Exam Example */}
              <section className="focused-section-card">
                <h4 className="section-step-label">3. Illustrative Exam Example</h4>
                <div className="example-box">
                  <p className="example-scenario">
                    <strong>Scenario:</strong> A registered enterprise incurs expenditure on qualifying items and seeks advice on statutory compliance and credit eligibility under {focusedChapter.statutory_reference || 'the relevant provisions'}.
                  </p>
                  <p className="example-solution">
                    <strong>Analysis:</strong> Cross-check whether any statutory negative list or restriction applies. If the statutory test is satisfied and supported by valid documentation, full benefit or compliance is established.
                  </p>
                </div>
              </section>

              {/* 4. Ask Sathi Instant Action */}
              <section className="focused-section-card highlight-card">
                <div className="ask-companion-strip">
                  <div>
                    <h4 className="section-step-label">4. Have a Doubt on This Chapter?</h4>
                    <p className="companion-subtext">
                      Sathi is ready with grounded ICAI study material and instant conversational answers.
                    </p>
                  </div>
                  <button
                    className="launch-sathi-btn"
                    onClick={() => {
                      const ctx = focusedContext;
                      setFocusedChapter(null);
                      handleAskSathi(ctx);
                    }}
                  >
                    💬 Ask Sathi Now
                  </button>
                </div>
              </section>

              {/* 5. Practice Exam Question */}
              <section className="focused-section-card">
                <div className="practice-header-line">
                  <h4 className="section-step-label">5. High-Yield Practice Question</h4>
                  <button
                    className="toggle-answer-btn"
                    onClick={() => setPracticeAnswerVisible(!practiceAnswerVisible)}
                  >
                    {practiceAnswerVisible ? 'Hide Solution' : 'Reveal Suggested Solution'}
                  </button>
                </div>

                <div className="practice-question-box">
                  <p className="question-text">
                    <strong>Question:</strong> State the statutory conditions or standard audit requirements applicable to {focusedChapter.title}, and discuss the implications of non-compliance.
                  </p>

                  {practiceAnswerVisible && (
                    <div className="practice-solution-box">
                      <p className="solution-title">✓ ICAI Suggested Answer Outline:</p>
                      <ol className="solution-steps">
                        <li>Cite the exact statutory section / Standard reference: {focusedChapter.statutory_reference}.</li>
                        <li>Enumerate the primary eligibility or procedure criteria step-by-step.</li>
                        <li>Address specific exceptions or penal/reporting consequences.</li>
                        <li>Conclude with a clear, reasoned recommendation.</li>
                      </ol>
                    </div>
                  )}
                </div>
              </section>

              {/* 6. Mark Progress & Confidence */}
              <section className="focused-section-card controls-card">
                <h4 className="section-step-label">6. Mark Progress & Confidence</h4>
                <div className="study-controls-row">
                  <div className="control-group">
                    <label>Status:</label>
                    <select
                      className={`ca-status-dropdown ${focusedChapter.status}`}
                      value={focusedChapter.status}
                      onChange={(e) =>
                        handleChapterUpdate(focusedChapter.id, { status: e.target.value })
                      }
                    >
                      <option value="not_started">○ Not Started</option>
                      <option value="in_progress">→ In Progress</option>
                      <option value="completed">✓ Completed</option>
                      <option value="needs_revision">⚠ Needs Revision</option>
                    </select>
                  </div>

                  <div className="control-group">
                    <label>Confidence (1-5):</label>
                    <div className="confidence-meter">
                      {[1, 2, 3, 4, 5].map((lvl) => (
                        <button
                          key={lvl}
                          type="button"
                          className={`conf-dot-btn ${lvl <= (focusedChapter.confidence_score || 0) ? 'filled' : ''}`}
                          onClick={() =>
                            handleChapterUpdate(focusedChapter.id, { confidence_score: lvl })
                          }
                        >
                          ★
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </section>

              {/* 7 & 8. Revision Tracker & Notes */}
              <section className="focused-section-card">
                <div className="revision-section-row">
                  <div>
                    <h4 className="section-step-label">7 & 8. Revision & Notes</h4>
                    <p className="revision-stat">
                      Completed Revisions: <strong>{focusedChapter.revision_count || 0}</strong>
                      {focusedChapter.last_revised && (
                        <span> · Last revised: {focusedChapter.last_revised}</span>
                      )}
                    </p>
                  </div>
                  <button
                    className="increment-revision-btn"
                    onClick={() => handleIncrementRevision(focusedChapter.id)}
                  >
                    🔁 Log Revision Completed
                  </button>
                </div>

                <div className="focused-notes-editor-box">
                  <label className="notes-label">Chapter Summary & Exam Traps:</label>
                  <textarea
                    className="focused-notes-textarea"
                    rows={4}
                    placeholder="Capture tricky adjustments, limits, mnemonics, or Section cross-references..."
                    defaultValue={focusedChapter.notes || ''}
                    onBlur={(e) =>
                      handleChapterUpdate(focusedChapter.id, { notes: e.target.value })
                    }
                  />
                  <span className="notes-auto-save-hint">Auto-saves when you click outside the box.</span>
                </div>
              </section>
            </div>

            <div className="focused-study-footer">
              <button
                className="study-done-btn"
                onClick={() => setFocusedChapter(null)}
              >
                Close Session
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================
          GENERAL REVISION NOTES MODAL
         ======================================================== */}
      {activeNotesItem && (
        <div className="modal-backdrop" onClick={() => setActiveNotesItem(null)}>
          <div className="modal-card calm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-strip">
              <div>
                <span className="modal-eyebrow">
                  {activeNotesItem.type === 'chapter' ? 'Chapter Revision Notes' : 'Topic Notes'}
                </span>
                <h3>{activeNotesItem.item.title}</h3>
              </div>
              <button className="modal-close-btn" onClick={() => setActiveNotesItem(null)}>
                ✕
              </button>
            </div>

            <textarea
              className="calm-notes-editor"
              rows={8}
              placeholder="Record section numbers, high-yield adjustments, formula tips, or exam pitfalls..."
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
              autoFocus
            />

            <div className="modal-footer-row">
              <button
                className="calm-cancel-btn"
                onClick={() => setActiveNotesItem(null)}
                disabled={savingNote}
              >
                Cancel
              </button>
              <button
                className="calm-save-btn"
                onClick={saveNotes}
                disabled={savingNote}
              >
                {savingNote ? 'Saving...' : 'Save Notes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Custom Chapter Modal */}
      {addModalOpen && (
        <div className="notes-modal-overlay" onClick={() => setAddModalOpen(false)}>
          <div className="notes-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-row">
              <h3>➕ Add Chapter</h3>
              <button className="modal-close-icon" onClick={() => setAddModalOpen(false)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleAddCustomChapterSubmit} className="add-chapter-form">
              <div className="form-group-item" style={{ marginBottom: '12px' }}>
                <label className="form-label" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-muted)' }}>Subject / Paper</label>
                <input
                  type="text"
                  className="timeline-input"
                  value={currentPaper ? `Paper ${currentPaper.paper_num}: ${currentPaper.name}` : ''}
                  disabled
                  style={{ width: '100%', opacity: 0.8 }}
                />
              </div>

              <div className="form-group-item" style={{ marginBottom: '12px' }}>
                <label className="form-label" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-muted)' }}>Chapter Title</label>
                <input
                  type="text"
                  className="timeline-input"
                  placeholder="e.g., GST Input Tax Credit or Audit of Banks"
                  value={newChapTitle}
                  onChange={(e) => setNewChapTitle(e.target.value)}
                  required
                  autoFocus
                  style={{ width: '100%' }}
                />
              </div>

              <div className="form-row-two-col" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div className="form-group-item">
                  <label className="form-label" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-muted)' }}>Estimated Hours</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    className="timeline-input"
                    value={newChapHours}
                    onChange={(e) => setNewChapHours(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>

                <div className="form-group-item">
                  <label className="form-label" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-muted)' }}>Difficulty</label>
                  <select
                    className="filter-select"
                    value={newChapDifficulty}
                    onChange={(e) => setNewChapDifficulty(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
              </div>

              <div className="modal-footer-row">
                <button
                  type="button"
                  className="calm-cancel-btn"
                  onClick={() => setAddModalOpen(false)}
                  disabled={submittingChap}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="calm-save-btn"
                  disabled={submittingChap || !newChapTitle.trim()}
                >
                  {submittingChap ? 'Adding...' : 'Create Chapter'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

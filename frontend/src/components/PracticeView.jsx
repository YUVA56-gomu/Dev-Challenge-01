import React, { useState, useEffect } from 'react';
import {
  fetchPracticeQuestions,
  fetchQuestionById,
  submitPracticeAnswer,
  fetchPracticeStats,
  fetchWeakAreas,
  fetchDueRevisions,
  completeRevision,
  startExamSession,
  fetchExamSession,
  submitExamSession,
  fetchCorpusStats
} from '../services/api';
import { voiceService } from '../services/voice';

/**
 * PracticeView Component - Phase 3 CA Exam Practice & Answer Evaluation Engine
 * 
 * Features:
 * - Practice Hub: Continue Practice, Practice by Subject/Chapter, Weak Areas, Revisions Due
 * - Question Engine: Official ICAI (RTP/MTP/Past Exams) vs AI-Generated Practice Questions
 * - Evaluation Engine: Step-marking, Strengths, Mistakes, Concept/Calculation/Presentation bars
 * - Spaced Revision Tracker: Automatic intervals (Day 1, 3, 7, 14, 30) on mistakes
 * - Timed Exam Simulation: Live countdown timer, multi-question navigation, post-exam diagnosis
 * - Companion Integration: One-click "Ask Sathi" transferring full attempt context
 * - Voice Integration: "Listen to Explanation" using cached ElevenLabs synthesis
 */
export default function PracticeView({ onAskInChat, initialSubject = null, initialChapter = null }) {
  // Modes: 'dashboard' | 'question' | 'evaluation' | 'exam' | 'exam_result'
  const [mode, setMode] = useState('dashboard');
  
  // Dashboard state
  const [stats, setStats] = useState(null);
  const [weakAreas, setWeakAreas] = useState([]);
  const [revisions, setDueRevisions] = useState([]);
  const [questionsPool, setQuestionsPool] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedPaper, setSelectedPaper] = useState(initialSubject || '');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [selectedStage, setSelectedStage] = useState('');
  const [selectedSourceType, setSelectedSourceType] = useState('');
  const [examQuestionCount, setExamQuestionCount] = useState(5);
  const [corpusStats, setCorpusStats] = useState(null);

  // Active Single Question Practice state
  const [activeQuestion, setActiveQuestion] = useState(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const [questionTimer, setQuestionTimer] = useState(0);

  // Audio Playback state
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);

  // Exam Mode state
  const [activeExamSession, setActiveExamSession] = useState(null);
  const [currentExamIndex, setCurrentExamIndex] = useState(0);
  const [examAnswers, setExamAnswers] = useState({});
  const [examSecondsLeft, setExamSecondsLeft] = useState(1800);
  const [examResult, setExamResult] = useState(null);

  // Papers list for filter tabs
  const papersList = [
    { id: 'paper_tax', name: 'Taxation (GST & Income Tax)', code: 'Paper 4' },
    { id: 'paper_law', name: 'Corporate & Other Laws', code: 'Paper 2' },
    { id: 'paper_audit', name: 'Auditing & Ethics', code: 'Paper 5' },
    { id: 'paper_adv_acc', name: 'Advanced Accounting', code: 'Paper 1' },
  ];

  // Load dashboard data on mount
  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, weakData, revData, qList, cStats] = await Promise.all([
        fetchPracticeStats('pooja'),
        fetchWeakAreas('pooja', 5),
        fetchDueRevisions('pooja'),
        fetchPracticeQuestions({
          paper_id: selectedPaper || undefined,
          stage_id: selectedStage || undefined,
          source_type: selectedSourceType || undefined,
          difficulty: selectedDifficulty || undefined,
          limit: 20
        }),
        fetchCorpusStats().catch(() => null),
      ]);
      setStats(statsData);
      setWeakAreas(weakData || []);
      setDueRevisions(revData || []);
      setQuestionsPool(qList || []);
      if (cStats) setCorpusStats(cStats);
    } catch (err) {
      console.error('Failed to load practice data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [selectedPaper, selectedStage, selectedSourceType, selectedDifficulty]);

  // Question solving timer
  useEffect(() => {
    let interval = null;
    if (mode === 'question') {
      interval = setInterval(() => setQuestionTimer((prev) => prev + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [mode]);

  // Exam countdown timer
  useEffect(() => {
    let interval = null;
    if (mode === 'exam' && examSecondsLeft > 0) {
      interval = setInterval(() => {
        setExamSecondsLeft((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            handleAutoSubmitExam();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [mode, examSecondsLeft]);

  // Clean voice when leaving evaluation
  useEffect(() => {
    return () => {
      voiceService.stop();
    };
  }, [mode]);

  // -------------------------------------------------------------
  // Question & Attempt Handlers
  // -------------------------------------------------------------

  const handleStartQuestion = (q) => {
    setActiveQuestion(q);
    setUserAnswer('');
    setEvaluation(null);
    setQuestionTimer(0);
    setIsPlayingAudio(false);
    setMode('question');
  };

  const handleSubmitAnswer = async () => {
    if (!userAnswer.trim()) {
      alert('Please enter or select an answer before submitting.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitPracticeAnswer({
        question_id: activeQuestion.id,
        student_id: 'pooja',
        user_answer: userAnswer,
        time_spent_seconds: questionTimer,
      });

      setEvaluation(res.evaluation);
      setMode('evaluation');
      // Refresh stats in background
      loadDashboardData();
    } catch (err) {
      console.error('Failed to submit answer:', err);
      alert('Could not evaluate answer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCompleteRevision = async (revId) => {
    try {
      await completeRevision(revId);
      setDueRevisions((prev) => prev.filter((r) => r.id !== revId));
    } catch (err) {
      console.error('Failed to mark revision complete:', err);
    }
  };

  // -------------------------------------------------------------
  // Voice & Audio Handlers
  // -------------------------------------------------------------

  const handleListenExplanation = async () => {
    if (isPlayingAudio) {
      voiceService.stop();
      setIsPlayingAudio(false);
      return;
    }

    const textToSpeak =
      evaluation?.spoken_explanation ||
      `You scored ${evaluation?.score} out of ${evaluation?.max_score}. Review the ideal approach for full marks.`;

    setAudioLoading(true);
    try {
      await voiceService.speak(
        textToSpeak,
        () => {
          setIsPlayingAudio(true);
          setAudioLoading(false);
        },
        () => {
          setIsPlayingAudio(false);
          setAudioLoading(false);
        },
        () => {
          setIsPlayingAudio(true);
          setAudioLoading(false);
        }
      );
    } catch (err) {
      console.error('Voice playback error:', err);
      setIsPlayingAudio(false);
      setAudioLoading(false);
    }
  };

  // -------------------------------------------------------------
  // Companion Deep Integration
  // -------------------------------------------------------------

  const handleAskSathiAboutAttempt = () => {
    if (!onAskInChat) return;

    const promptText = `Can you explain where I lost marks on this question and how to frame the statutory answer for full marks?`;
    const attemptContext = {
      question_id: activeQuestion.id,
      question_text: activeQuestion.question_text,
      question_type: activeQuestion.question_type,
      user_answer: userAnswer,
      score: evaluation?.score,
      max_score: evaluation?.max_score,
      mistakes: evaluation?.mistakes || [],
      missing_concepts: evaluation?.missing_concepts || [],
      ideal_answer: evaluation?.ideal_answer || activeQuestion.solution,
      source: activeQuestion.source,
    };

    onAskInChat(promptText, {
      paper: activeQuestion.paper_id,
      chapter: activeQuestion.chapter_id,
      topic: activeQuestion.topic_id,
      attempt_context: attemptContext,
    });
  };

  // -------------------------------------------------------------
  // Exam Mode Handlers
  // -------------------------------------------------------------

  const handleStartExam = async (paperId = null, count = null) => {
    const qCount = count || examQuestionCount;
    setLoading(true);
    try {
      const session = await startExamSession({
        student_id: 'pooja',
        paper_id: paperId || (selectedPaper || undefined),
        stage_id: selectedStage || undefined,
        num_questions: qCount,
        time_limit_minutes: qCount === 20 ? 60 : (qCount === 10 ? 45 : 25),
      });
      setActiveExamSession(session);
      setCurrentExamIndex(0);
      setExamAnswers({});
      setExamSecondsLeft(session.time_limit_minutes * 60);
      setMode('exam');
    } catch (err) {
      console.error('Failed to start exam session:', err);
      alert('Could not start exam mode.');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSubmitExam = async () => {
    if (!activeExamSession) return;
    await submitCurrentExam();
  };

  const submitCurrentExam = async () => {
    setSubmitting(true);
    try {
      const timeSpent = (activeExamSession.time_limit_minutes * 60) - examSecondsLeft;
      const res = await submitExamSession(activeExamSession.session_id, {
        answers: examAnswers,
        time_spent_seconds: timeSpent,
      });
      setExamResult(res);
      setMode('exam_result');
      loadDashboardData();
    } catch (err) {
      console.error('Failed to submit exam:', err);
      alert('Could not submit exam. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Helpers
  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins}:${rem < 10 ? '0' : ''}${rem}`;
  };

  return (
    <div className="practice-screen">
      {/* ========================================================
          1. PRACTICE DASHBOARD MODE
         ======================================================== */}
      {mode === 'dashboard' && (
        <div className="practice-dashboard-sheet">
          {/* Header */}
          <header className="practice-header">
            <div className="practice-title-group">
              <span className="practice-eyebrow">CA Exam Practice & Self-Evaluation</span>
              <h1 className="practice-title">Mastery Through Practice</h1>
              <p className="practice-sub">
                Attempt exam-standard questions, receive instant step-marking evaluations, and turn mistakes into exam confidence.
              </p>
            </div>

            <div className="practice-header-actions" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div style={{ display: 'flex', background: 'rgba(255,255,255,0.08)', borderRadius: '8px', padding: '2px' }}>
                {[5, 10, 20].map((cnt) => (
                  <button
                    key={cnt}
                    onClick={() => setExamQuestionCount(cnt)}
                    style={{
                      padding: '4px 10px',
                      fontSize: '12px',
                      fontWeight: examQuestionCount === cnt ? '700' : '400',
                      background: examQuestionCount === cnt ? '#3b82f6' : 'transparent',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer'
                    }}
                  >
                    {cnt} Qs
                  </button>
                ))}
              </div>
              <button
                className="start-exam-banner-btn"
                onClick={() => handleStartExam(selectedPaper || null, examQuestionCount)}
              >
                ⏱️ Start Timed Exam ({examQuestionCount} Qs)
              </button>
            </div>
          </header>

          {/* Phase 4: ICAI Knowledge & Question Corpus Provenance Banner */}
          {corpusStats && (
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              padding: '12px 18px',
              marginBottom: '16px',
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              fontSize: '13px',
              color: '#cbd5e1'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '16px' }}>🏛️</span>
                <span style={{ fontWeight: 600, color: '#f8fafc' }}>ICAI Knowledge Corpus</span>
                <span style={{ color: '#94a3b8' }}>· Verified Provenance Separated</span>
              </div>
              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                <span>Total: <strong style={{ color: '#f8fafc' }}>{corpusStats.total_questions}</strong></span>
                <span>🏛️ Official ICAI: <strong style={{ color: '#60a5fa' }}>{corpusStats.official_questions}</strong></span>
                <span>🤖 Sathi AI: <strong style={{ color: '#a78bfa' }}>{corpusStats.ai_generated_questions}</strong></span>
                <span>📚 Ingested Chunks: <strong style={{ color: '#34d399' }}>{corpusStats.total_knowledge_chunks}</strong></span>
              </div>
            </div>
          )}

          {/* Practice Performance Metrics Strip */}
          <div className="practice-stats-strip">
            <div className="practice-stat-box">
              <span className="p-stat-number">{stats?.questions_attempted || 0}</span>
              <span className="p-stat-label">Questions Attempted</span>
            </div>
            <div className="practice-stat-box">
              <span className="p-stat-number">{stats?.questions_correct || 0}</span>
              <span className="p-stat-label">Questions Correct</span>
            </div>
            <div className="practice-stat-box">
              <span className="p-stat-number highlight-blue">{stats?.accuracy_pct || 0}%</span>
              <span className="p-stat-label">Overall Accuracy</span>
            </div>
            <div className="practice-stat-box">
              <span className="p-stat-number highlight-orange">{(stats?.practice_streak ?? 0) > 0 ? `🔥 ${stats.practice_streak}` : '—'}</span>
              <span className="p-stat-label">Practice Day Streak</span>
            </div>
            <div className="practice-stat-box">
              <span className="p-stat-number highlight-purple">{revisions?.length || 0}</span>
              <span className="p-stat-label">Revisions Due</span>
            </div>
          </div>

          {/* Quick Practice & Subject Tabs */}
          <div className="practice-filter-row">
            <div className="subject-filter-tabs">
              <button
                className={`subject-tab-btn ${selectedPaper === '' ? 'active' : ''}`}
                onClick={() => setSelectedPaper('')}
              >
                All Subjects
              </button>
              {papersList.map((p) => (
                <button
                  key={p.id}
                  className={`subject-tab-btn ${selectedPaper === p.id ? 'active' : ''}`}
                  onClick={() => setSelectedPaper(p.id)}
                >
                  {p.code}: {p.name.split(' ')[0]}
                </button>
              ))}
            </div>

            <div className="quick-practice-pills">
              <span className="quick-label">Quick Sets:</span>
              <button
                className="quick-pill-btn"
                onClick={() => {
                  if (questionsPool.length > 0) handleStartQuestion(questionsPool[0]);
                }}
              >
                ⚡ 5 Questions
              </button>
            </div>
          </div>

          <div className="practice-main-grid">
            {/* Left Column: Questions List */}
            <div className="practice-questions-column">
              <div className="column-title-row">
                <h3 className="column-title">Available Practice Questions</h3>
                <span className="pool-count">{questionsPool.length} Questions Ready</span>
              </div>

              {loading ? (
                <div className="loading-card-soft">
                  <div className="pulsing-spinner-soft"></div>
                  <p>Loading authoritative practice questions...</p>
                </div>
              ) : questionsPool.length === 0 ? (
                <div className="empty-practice-card">
                  <p>No questions found for this subject filter. Select another subject above.</p>
                </div>
              ) : (
                <div className="questions-card-list">
                  {questionsPool.map((q) => {
                    const isOfficial = q.is_official !== undefined ? Boolean(q.is_official) : (q.source && q.source.includes('ICAI'));
                    return (
                      <div key={q.id} className="practice-question-item-card">
                        <div className="q-card-top-row">
                          <span className={`q-source-pill ${isOfficial ? 'official' : 'ai'}`}>
                            {isOfficial ? '🏛️ Official ICAI' : '🤖 Sathi AI Practice'}
                            {q.source_document ? ` · ${q.source_document}` : (q.source ? ` · ${q.source}` : '')}
                            {q.source_year ? ` (${q.source_year})` : ''}
                          </span>
                          <div className="q-badges-stack">
                            <span className={`q-diff-badge ${q.difficulty.toLowerCase()}`}>
                              {q.difficulty}
                            </span>
                            <span className="q-type-badge">{q.question_type}</span>
                            <span className="q-marks-badge">{q.marks} Marks</span>
                          </div>
                        </div>

                        <p className="q-preview-text">{q.question_text}</p>

                        <div className="q-card-footer-row">
                          <span className="q-expected-time">⏱️ {q.expected_time_minutes || 10} mins</span>
                          <button
                            className="attempt-q-btn"
                            onClick={() => handleStartQuestion(q)}
                          >
                            Solve Question ➜
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Right Column: Weak Areas & Due Spaced Revisions */}
            <aside className="practice-sidebar-column">
              {/* Spaced Revisions Due Alert Card */}
              {revisions.length > 0 && (
                <div className="practice-side-card revisions-card">
                  <div className="side-card-header">
                    <span className="side-card-icon">🔁</span>
                    <h4 className="side-card-title">Due Spaced Revisions</h4>
                  </div>
                  <p className="side-card-sub">
                    Scheduled intervals based on your past answer evaluations.
                  </p>

                  <div className="revisions-tray-list">
                    {revisions.map((rev) => (
                      <div key={rev.id} className="revision-tray-item">
                        <div className="rev-info">
                          <span className="rev-topic-name">{rev.topic_title || rev.chapter_title}</span>
                          <span className="rev-meta">
                            Interval: Day {rev.interval_day} · Due: {rev.scheduled_date}
                          </span>
                        </div>
                        <button
                          className="rev-done-action-btn"
                          onClick={() => handleCompleteRevision(rev.id)}
                          title="Mark this revision completed"
                        >
                          ✓ Done
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Weak Areas Card */}
              <div className="practice-side-card weak-areas-card">
                <div className="side-card-header">
                  <span className="side-card-icon">🎯</span>
                  <h4 className="side-card-title">Priority Focus Areas</h4>
                </div>
                <p className="side-card-sub">
                  Calculated from your accuracy and repeated mistakes in SQLite.
                </p>

                <div className="weak-topics-list">
                  {weakAreas.length === 0 ? (
                    <p className="empty-sub">No critical weak areas detected! Keep practicing.</p>
                  ) : (
                    weakAreas.map((w, idx) => (
                      <div key={idx} className="weak-topic-row">
                        <div className="weak-topic-info">
                          <span className="weak-name">{w.topic_title || w.chapter_title}</span>
                          <span className="weak-stat">
                            Accuracy: {w.accuracy_pct}% ({w.questions_attempted} attempts)
                          </span>
                        </div>
                        <button
                          className="weak-practice-btn"
                          onClick={() => {
                            const matched = questionsPool.find(
                              (q) => q.topic_id === w.topic_id || q.chapter_id === w.chapter_id
                            );
                            if (matched) handleStartQuestion(matched);
                            else alert('Please filter by this subject to practice this topic.');
                          }}
                        >
                          Practice
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Recent Attempts History */}
              {stats?.recent_attempts && stats.recent_attempts.length > 0 && (
                <div className="practice-side-card history-card">
                  <div className="side-card-header">
                    <span className="side-card-icon">📋</span>
                    <h4 className="side-card-title">Recent Attempts</h4>
                  </div>
                  <div className="attempts-history-list">
                    {stats.recent_attempts.slice(0, 4).map((att) => (
                      <div key={att.id} className="history-attempt-item">
                        <span className="att-title">{att.chapter_title || 'Practice Attempt'}</span>
                        <div className="att-meta">
                          <span className={`att-score-badge ${att.is_correct ? 'pass' : 'fail'}`}>
                            {att.score} / {att.max_score} M
                          </span>
                          <span className="att-time">{att.created_at?.slice(0, 10)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </aside>
          </div>
        </div>
      )}

      {/* ========================================================
          2. SINGLE QUESTION PRACTICE MODE
         ======================================================== */}
      {mode === 'question' && activeQuestion && (
        <div className="question-solving-sheet">
          <div className="solving-top-bar">
            <button className="back-link-btn" onClick={() => setMode('dashboard')}>
              ← Back to Practice Hub
            </button>
            <div className="solving-timer-pill">
              <span>⏱️ Time: {formatTime(questionTimer)}</span>
            </div>
          </div>

          <div className="solving-question-card">
            <div className="q-card-top-row">
              {(() => {
                const isOfficial = activeQuestion.is_official !== undefined ? Boolean(activeQuestion.is_official) : (activeQuestion.source && activeQuestion.source.includes('ICAI'));
                return (
                  <span className={`q-source-pill ${isOfficial ? 'official' : 'ai'}`}>
                    {isOfficial ? '🏛️ Official ICAI Source' : '🤖 Sathi AI Practice'}
                    {activeQuestion.source_document ? ` · ${activeQuestion.source_document}` : (activeQuestion.source ? ` · ${activeQuestion.source}` : '')}
                    {activeQuestion.source_year ? ` (${activeQuestion.source_year})` : ''}
                  </span>
                );
              })()}
              <div className="q-badges-stack">
                <span className={`q-diff-badge ${activeQuestion.difficulty?.toLowerCase()}`}>
                  {activeQuestion.difficulty}
                </span>
                <span className="q-type-badge">{activeQuestion.question_type}</span>
                <span className="q-marks-badge">{activeQuestion.marks} Marks</span>
              </div>
            </div>

            <h2 className="solving-question-text">{activeQuestion.question_text}</h2>

            {/* Answer Input: MCQ Options or Textarea */}
            {activeQuestion.question_type === 'MCQ' && activeQuestion.options ? (
              <div className="mcq-options-container">
                <span className="mcq-choose-label">Select the correct statutory option:</span>
                <div className="mcq-options-grid">
                  {activeQuestion.options.map((opt, idx) => (
                    <button
                      key={idx}
                      className={`mcq-option-card ${userAnswer === opt ? 'selected' : ''}`}
                      onClick={() => setUserAnswer(opt)}
                    >
                      <span className="mcq-letter">{String.fromCharCode(65 + idx)}</span>
                      <span className="mcq-opt-text">{opt}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="theory-answer-container">
                <label className="answer-label">
                  Your Answer & Working Notes (Structure with Sections, Criteria, and Conclusion):
                </label>
                <textarea
                  className="answer-textarea"
                  rows={10}
                  placeholder="Type your exam solution here. Mention specific section numbers, statutory criteria, and your final recommendation..."
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  autoFocus
                />
                <span className="word-count-note">
                  {userAnswer.trim().split(/\s+/).filter(Boolean).length} words typed
                </span>
              </div>
            )}

            <div className="solving-footer-row">
              <button
                className="cancel-solving-btn"
                onClick={() => setMode('dashboard')}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                className="submit-answer-primary-btn"
                onClick={handleSubmitAnswer}
                disabled={submitting}
              >
                {submitting ? 'Evaluating with Sathi...' : 'Submit Answer for AI Evaluation ➜'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================
          3. EVALUATION RESULT MODE
         ======================================================== */}
      {mode === 'evaluation' && evaluation && (
        <div className="evaluation-result-sheet">
          <div className="evaluation-top-bar">
            <button className="back-link-btn" onClick={() => setMode('dashboard')}>
              ← Return to Practice Hub
            </button>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className={`q-source-pill ${activeQuestion.is_official ? 'official' : 'ai'}`} style={{ margin: 0, padding: '4px 10px' }}>
                {activeQuestion.is_official ? '🏛️ Official ICAI' : '🤖 Sathi AI Practice'}
              </span>
              <span className="eval-disclaimer-tag">
                {evaluation.is_ai_assisted ? 'ℹ️ AI-Assisted Evaluation (Estimate)' : '✓ Verified Standard Evaluation'}
              </span>
            </div>
          </div>

          {/* Hero Score Banner */}
          <div className={`eval-score-banner ${evaluation.correct ? 'pass' : 'needs-work'}`}>
            <div className="eval-score-main">
              <span className="eval-score-label">EVALUATION SCORE</span>
              <h2 className="eval-score-digits">
                {evaluation.score} <span className="max-score-denom">/ {evaluation.max_score} Marks</span>
              </h2>
              <p className="eval-status-message">
                {evaluation.correct
                  ? '✓ Excellent demonstration of statutory and analytical principles!'
                  : '⚠ Good attempt, but key statutory conditions or adjustments were missed.'}
              </p>
            </div>

            {/* 3 Component Progress Bars */}
            <div className="eval-bars-group">
              <div className="component-bar-row">
                <span className="bar-label">Concept Understanding</span>
                <div className="bar-track">
                  <div className="bar-fill blue" style={{ width: `${evaluation.concept_score_pct || 70}%` }}></div>
                </div>
                <span className="bar-pct">{evaluation.concept_score_pct || 70}%</span>
              </div>

              <div className="component-bar-row">
                <span className="bar-label">Calculation & Adjustments</span>
                <div className="bar-track">
                  <div className="bar-fill green" style={{ width: `${evaluation.calculation_score_pct || 65}%` }}></div>
                </div>
                <span className="bar-pct">{evaluation.calculation_score_pct || 65}%</span>
              </div>

              <div className="component-bar-row">
                <span className="bar-label">ICAI Presentation</span>
                <div className="bar-track">
                  <div className="bar-fill purple" style={{ width: `${evaluation.presentation_score_pct || 75}%` }}></div>
                </div>
                <span className="bar-pct">{evaluation.presentation_score_pct || 75}%</span>
              </div>
            </div>
          </div>

          {/* Action Bar: Listen (ElevenLabs) + Ask Sathi */}
          <div className="eval-action-strip">
            <button
              className="eval-voice-btn"
              onClick={handleListenExplanation}
              disabled={audioLoading}
            >
              {isPlayingAudio ? '⏸ Pause Explanation' : '🔊 Listen to Sathi Breakdown'}
            </button>

            <button
              className="eval-ask-sathi-btn"
              onClick={handleAskSathiAboutAttempt}
            >
              💬 Ask Sathi: Why did I lose marks here?
            </button>
          </div>

          {/* Strengths & Mistakes Two-Column Breakdown */}
          <div className="eval-feedback-grid">
            <div className="eval-column-card strengths-card">
              <h4 className="column-card-title">✓ What You Did Well</h4>
              {evaluation.strengths?.length > 0 ? (
                <ul className="feedback-list strengths">
                  {evaluation.strengths.map((str, idx) => (
                    <li key={idx}>{str}</li>
                  ))}
                </ul>
              ) : (
                <p className="neutral-sub">Attempt captured; continue reviewing the core principle.</p>
              )}
            </div>

            <div className="eval-column-card mistakes-card">
              <h4 className="column-card-title">✗ Where You Lost Marks</h4>
              {evaluation.mistakes?.length > 0 ? (
                <ul className="feedback-list mistakes">
                  {evaluation.mistakes.map((mst, idx) => (
                    <li key={idx}>{mst}</li>
                  ))}
                </ul>
              ) : (
                <p className="neutral-sub">No major errors identified.</p>
              )}

              {evaluation.missing_concepts?.length > 0 && (
                <div className="missing-concepts-box">
                  <span className="missing-label">Missing Statutory Provisions:</span>
                  <div className="missing-chips">
                    {evaluation.missing_concepts.map((mc, idx) => (
                      <span key={idx} className="missing-chip">{mc}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Ideal Solution & Model Outline */}
          {evaluation.ideal_answer && (
            <div className="ideal-solution-card">
              <h4 className="ideal-title">✓ ICAI Model Approach & Suggested Solution</h4>
              <div className="ideal-content-text">
                <pre>{evaluation.ideal_answer}</pre>
              </div>
            </div>
          )}

          <div className="evaluation-footer-buttons">
            <button
              className="try-again-btn"
              onClick={() => handleStartQuestion(activeQuestion)}
            >
              🔁 Re-attempt This Question
            </button>
            <button
              className="next-q-btn"
              onClick={() => setMode('dashboard')}
            >
              Next Practice Question ➜
            </button>
          </div>
        </div>
      )}

      {/* ========================================================
          4. TIMED EXAM SIMULATION MODE
         ======================================================== */}
      {mode === 'exam' && activeExamSession && (
        <div className="exam-simulation-sheet">
          <header className="exam-sticky-header">
            <div className="exam-meta-left">
              <span className="exam-badge">EXAM MODE</span>
              <h3 className="exam-header-title">{activeExamSession.title}</h3>
            </div>

            <div className="exam-timer-center">
              <span className={`countdown-clock ${examSecondsLeft < 300 ? 'urgent' : ''}`}>
                ⏱️ {formatTime(examSecondsLeft)}
              </span>
              <span className="clock-sub">Time Remaining</span>
            </div>

            <div className="exam-meta-right">
              <button
                className="submit-exam-danger-btn"
                onClick={submitCurrentExam}
                disabled={submitting}
              >
                {submitting ? 'Submitting Exam...' : 'Submit Complete Exam ➜'}
              </button>
            </div>
          </header>

          <div className="exam-content-layout">
            {/* Left Question Navigation Palette */}
            <aside className="exam-nav-palette">
              <span className="palette-label">Question Palette</span>
              <div className="palette-grid">
                {activeExamSession.questions?.map((item, idx) => {
                  const qid = item.id || item.question_id;
                  const answered = Boolean(examAnswers[qid]?.trim());
                  const isCurrent = idx === currentExamIndex;

                  return (
                    <button
                      key={qid}
                      className={`palette-num-btn ${isCurrent ? 'current' : ''} ${answered ? 'answered' : ''}`}
                      onClick={() => setCurrentExamIndex(idx)}
                    >
                      {idx + 1}
                    </button>
                  );
                })}
              </div>

              <div className="palette-legend">
                <div className="legend-item"><span className="dot answered"></span> Answered</div>
                <div className="legend-item"><span className="dot"></span> Unanswered</div>
              </div>
            </aside>

            {/* Main Exam Question Workspace */}
            <main className="exam-active-question-pane">
              {activeExamSession.questions?.[currentExamIndex] && (() => {
                const q = activeExamSession.questions[currentExamIndex];
                const qid = q.id || q.question_id;
                const currentAns = examAnswers[qid] || '';

                return (
                  <div className="exam-question-box">
                    <div className="exam-q-info-strip">
                      <span className="exam-q-index">Question {currentExamIndex + 1} of {activeExamSession.total_questions}</span>
                      <span className="exam-q-marks">{q.marks} Marks</span>
                    </div>

                    <h3 className="exam-q-text">{q.question_text}</h3>

                    {q.options ? (
                      <div className="mcq-options-grid">
                        {q.options.map((opt, idx) => (
                          <button
                            key={idx}
                            className={`mcq-option-card ${currentAns === opt ? 'selected' : ''}`}
                            onClick={() => setExamAnswers((prev) => ({ ...prev, [qid]: opt }))}
                          >
                            <span className="mcq-letter">{String.fromCharCode(65 + idx)}</span>
                            <span className="mcq-opt-text">{opt}</span>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <textarea
                        className="exam-writing-area"
                        rows={12}
                        placeholder="Write your complete examination answer here..."
                        value={currentAns}
                        onChange={(e) =>
                          setExamAnswers((prev) => ({ ...prev, [qid]: e.target.value }))
                        }
                      />
                    )}

                    <div className="exam-nav-footer">
                      <button
                        className="exam-prev-btn"
                        disabled={currentExamIndex === 0}
                        onClick={() => setCurrentExamIndex((prev) => prev - 1)}
                      >
                        ← Previous
                      </button>

                      {currentExamIndex < activeExamSession.total_questions - 1 ? (
                        <button
                          className="exam-next-btn"
                          onClick={() => setCurrentExamIndex((prev) => prev + 1)}
                        >
                          Next Question →
                        </button>
                      ) : (
                        <button
                          className="submit-exam-primary-btn"
                          onClick={submitCurrentExam}
                          disabled={submitting}
                        >
                          Finish & Submit Exam
                        </button>
                      )}
                    </div>
                  </div>
                );
              })()}
            </main>
          </div>
        </div>
      )}

      {/* ========================================================
          5. POST-EXAM ANALYSIS MODE
         ======================================================== */}
      {mode === 'exam_result' && examResult && (
        <div className="exam-result-sheet">
          <header className="result-header">
            <span className="result-eyebrow">POST-EXAM DIAGNOSIS</span>
            <h1 className="result-title">Exam Performance Analysis</h1>
          </header>

          <div className="result-hero-card">
            <div className="result-score-ring">
              <span className="ring-score">{examResult.score_obtained}</span>
              <span className="ring-max">/ {examResult.total_marks}</span>
            </div>

            <div className="result-metrics-grid">
              <div className="r-metric-box">
                <span className="r-num">{examResult.accuracy_pct}%</span>
                <span className="r-label">Accuracy</span>
              </div>
              <div className="r-metric-box">
                <span className="r-num">{formatTime(examResult.time_spent_seconds || 0)}</span>
                <span className="r-label">Time Spent</span>
              </div>
            </div>
          </div>

          <div className="result-analysis-grid">
            <div className="analysis-card strong">
              <h4>✓ Strong Areas</h4>
              <ul>
                {examResult.strong_areas?.length > 0 ? (
                  examResult.strong_areas.map((sa, idx) => <li key={idx}>{sa}</li>)
                ) : (
                  <li>Keep practicing across all syllabus modules.</li>
                )}
              </ul>
            </div>

            <div className="analysis-card weak">
              <h4>⚠ Needs Attention</h4>
              <ul>
                {examResult.weak_areas?.length > 0 ? (
                  examResult.weak_areas.map((wa, idx) => <li key={idx}>{wa}</li>)
                ) : (
                  <li>No recurring errors detected.</li>
                )}
              </ul>
            </div>

            <div className="analysis-card recommended">
              <h4>🎯 Recommended Next Steps</h4>
              <ol>
                {examResult.recommended_steps?.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          </div>

          <div className="result-footer-row">
            <button
              className="return-hub-btn"
              onClick={() => setMode('dashboard')}
            >
              Return to Practice Dashboard ➜
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

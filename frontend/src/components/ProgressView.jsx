import React, { useState, useEffect } from 'react';
import {
  fetchProgress,
  fetchSubjects,
  fetchStudyRecommendations,
  fetchPracticeStats,
  fetchDueRevisions
} from '../services/api';

export default function ProgressView({ onNavigate, onAskInChat, onNavigateToPractice }) {
  const [progress, setProgress] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const [practiceStats, setPracticeStats] = useState(null);
  const [dueRevisions, setDueRevisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [planAdjusted, setPlanAdjusted] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [progData, subData, recData, pStats, revs] = await Promise.all([
          fetchProgress(),
          fetchSubjects(),
          fetchStudyRecommendations('pooja'),
          fetchPracticeStats('pooja'),
          fetchDueRevisions('pooja'),
        ]);
        setProgress(progData);
        setSubjects(subData || []);
        setRecommendations(recData);
        setPracticeStats(pStats);
        setDueRevisions(revs || []);
      } catch (err) {
        setError('Could not load progress data.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleAdjustPlan = () => {
    setPlanAdjusted(true);
    onAskInChat?.('What should I study today based on my current CA progress, weak areas, and revision status?');
  };

  const handleStudyItem = (topicTitle, chapterTitle, paperName) => {
    onAskInChat?.(
      `Let's focus on ${topicTitle} from ${chapterTitle}. Can we review the key rules and an exam example?`,
      { paper: paperName, chapter: chapterTitle, topic: topicTitle }
    );
  };

  if (loading) {
    return (
      <div className="view-container loading-center">
        <div className="pulsing-spinner-soft" />
        <p>Loading your progress...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="view-container loading-center">
        <p className="empty-state-text">{error}</p>
        <button className="primary-action-btn" onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  const overallPercent = progress?.overall_progress_percentage ?? 0;
  const completedChapters = progress?.completed_chapters ?? 0;
  const totalChapters = progress?.total_chapters ?? 0;
  const streakDays = progress?.current_streak_days ?? 0;
  const focusMinutes = progress?.total_focus_minutes ?? 0;
  const tasksCompleted = progress?.tasks_completed ?? 0;

  const hasAnyActivity = completedChapters > 0 || (practiceStats?.questions_attempted ?? 0) > 0;

  const formatFocus = (mins) => {
    if (!mins) return '0m';
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    if (h > 0 && m > 0) return `${h}h ${m}m`;
    if (h > 0) return `${h}h`;
    return `${m}m`;
  };

  return (
    <div className="progress-screen">
      <header className="progress-header">
        <span className="progress-eyebrow">Academic Progress</span>
        <h1 className="progress-title">Your CA journey.</h1>
        <p className="progress-sub">Track where you are and what to focus on next.</p>
      </header>

      {/* Empty state */}
      {!hasAnyActivity && (
        <div className="progress-empty-state">
          <div className="empty-state-icon">📊</div>
          <h3 className="empty-state-title">No activity recorded yet</h3>
          <p className="empty-state-text">
            Your progress will appear here once you start studying chapters and attempting practice questions.
          </p>
          <div className="empty-state-actions">
            <button className="primary-action-btn" onClick={() => onNavigate?.('study')}>
              Start Studying
            </button>
            <button className="secondary-action-btn" onClick={() => onNavigate?.('practice')}>
              Take Practice
            </button>
          </div>
        </div>
      )}

      {hasAnyActivity && (
        <div className="progress-sheet">
          {/* Sathi Recommendation */}
          {recommendations?.recommended_action && (
            <>
              <section className="progress-section recommendation-highlight-section">
                <div className="insight-badge-row">
                  <span className="sathi-badge-small">Sathi Recommendation</span>
                  {streakDays > 0 && (
                    <span className="streak-badge">🔥 {streakDays}-day streak</span>
                  )}
                </div>
                <div className="recommendation-content-box">
                  <p className="recommendation-hero-text">{recommendations.recommended_action}</p>
                  {recommendations.struggling_topics?.length > 0 && (
                    <div className="struggling-topics-tray">
                      <span className="tray-label">Focus Areas:</span>
                      <div className="struggle-chips-row">
                        {recommendations.struggling_topics.map((item, idx) => (
                          <div key={idx} className="struggle-chip-card">
                            <div className="struggle-chip-info">
                              <span className="struggle-chip-title">{item.title}</span>
                              <span className="struggle-chip-meta">
                                {item.chapter_title} · Confidence {item.confidence_score}/5
                              </span>
                            </div>
                            <button
                              className="struggle-chip-action-btn"
                              onClick={() => handleStudyItem(item.title, item.chapter_title, item.paper_name)}
                            >
                              Study with Sathi
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </section>
              <div className="sheet-divider" />
            </>
          )}

          {/* Practice Metrics */}
          <section className="progress-section practice-analytics-section">
            <div className="section-header-flex">
              <h2 className="progress-section-label">EXAM PRACTICE</h2>
              {onNavigateToPractice && (
                <button className="practice-hub-jump-btn" onClick={() => onNavigateToPractice()}>
                  Practice Hub →
                </button>
              )}
            </div>
            <div className="practice-metrics-grid">
              <div className="p-metric-card">
                <span className="p-metric-val">{practiceStats?.questions_attempted ?? 0}</span>
                <span className="p-metric-desc">Questions Attempted</span>
              </div>
              <div className="p-metric-card">
                <span className="p-metric-val positive">{practiceStats?.accuracy_pct ?? 0}%</span>
                <span className="p-metric-desc">Accuracy</span>
              </div>
              <div className="p-metric-card">
                <span className="p-metric-val streak">
                  {(practiceStats?.practice_streak ?? 0) > 0 ? `${practiceStats.practice_streak}d` : '—'}
                </span>
                <span className="p-metric-desc">Practice Streak</span>
              </div>
              <div className="p-metric-card">
                <span className="p-metric-val revision">{dueRevisions.length}</span>
                <span className="p-metric-desc">Revisions Due</span>
              </div>
            </div>
          </section>

          <div className="sheet-divider" />

          {/* Syllabus Progress */}
          <section className="progress-section">
            <h2 className="progress-section-label">SYLLABUS PROGRESS</h2>
            <div className="journey-main-bar-block">
              <div className="journey-overall-track">
                <div className="journey-overall-fill" style={{ width: `${overallPercent}%` }} />
              </div>
              <div className="journey-stat-row">
                <span className="journey-stat-pct">{overallPercent}% complete</span>
                <span className="journey-stat-chapters">
                  {completedChapters} of {totalChapters} chapters
                </span>
              </div>
            </div>
          </section>

          {/* Paper breakdown */}
          {subjects.length > 0 && (
            <>
              <div className="sheet-divider" />
              <section className="progress-section">
                <h2 className="progress-section-label">BY PAPER</h2>
                <div className="paper-meters-list">
                  {subjects.map((sub) => {
                    const completed = sub.chapters?.filter((c) => c.status === 'completed').length || 0;
                    const total = sub.chapters?.length || 1;
                    const pct = sub.progress_percentage ?? Math.round((completed / total) * 100);
                    return (
                      <div key={sub.id} className="paper-meter-row">
                        <div className="paper-meter-meta">
                          <span className="meter-paper-name">{sub.name}</span>
                          <span className="meter-paper-pct">{pct}%</span>
                        </div>
                        <div className="meter-track">
                          <div className="meter-fill" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            </>
          )}

          {/* Focus time */}
          {(focusMinutes > 0 || streakDays > 0 || tasksCompleted > 0) && (
            <>
              <div className="sheet-divider" />
              <section className="progress-section">
                <h2 className="progress-section-label">STUDY ACTIVITY</h2>
                <div className="this-week-strip">
                  <div className="week-stat-card">
                    <span className="stat-big-val">{formatFocus(focusMinutes)}</span>
                    <span className="stat-meta-note">Total focus time</span>
                  </div>
                  <div className="week-stat-card">
                    <span className="stat-big-val">{streakDays}</span>
                    <span className="stat-meta-note">Day streak</span>
                  </div>
                  <div className="week-stat-card">
                    <span className="stat-big-val">{tasksCompleted}</span>
                    <span className="stat-meta-note">Tasks completed</span>
                  </div>
                </div>
              </section>
            </>
          )}

          <div className="sheet-divider" />

          {/* Ask Sathi */}
          <section className="sathi-insight-section">
            <div className="insight-badge-row">
              <span className="sathi-badge-small">Sathi Study Advisor</span>
            </div>
            <blockquote className="insight-ai-text">
              "Ask Sathi about any chapter you're unsure about and schedule spaced revisions for topics you've answered incorrectly."
            </blockquote>
            <div className="insight-action-row">
              <button
                className="insight-rebalance-btn"
                onClick={handleAdjustPlan}
                disabled={planAdjusted}
              >
                {planAdjusted ? 'Opening Companion...' : 'Ask Sathi: What to study today?'}
              </button>
              <button className="insight-talk-btn" onClick={() => onNavigate?.('companion')}>
                Discuss with Sathi →
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

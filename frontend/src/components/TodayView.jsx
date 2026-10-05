import React, { useState, useEffect, useCallback } from 'react';
import { fetchProgress, fetchTasks, toggleTask, createTask, deleteTask, fetchDueRevisions } from '../services/api';
import { soundService } from '../services/soundService';

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function formatFocusTime(minutes) {
  if (!minutes) return null;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h > 0 && m > 0) return `${h}h ${m}m`;
  if (h > 0) return `${h}h`;
  return `${m}m`;
}

export default function TodayView({ onNavigate, onAskInChat }) {
  const [progress, setProgress] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [dueRevisions, setDueRevisions] = useState([]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [progData, tasksData, revData] = await Promise.all([
        fetchProgress(),
        fetchTasks(),
        fetchDueRevisions('pooja'),
      ]);
      setProgress(progData);
      setTasks(tasksData || []);
      setDueRevisions(revData || []);
    } catch (err) {
      setError('Could not load dashboard data. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleToggleTask = async (taskId) => {
    try {
      soundService.playSound('task_complete');
      await toggleTask(taskId);
      await loadData();
    } catch {
      // silent — task toggle failure shouldn't break the page
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    const title = newTaskTitle.trim();
    if (!title) return;
    try {
      await createTask(title);
      setNewTaskTitle('');
      await loadData();
    } catch {
      alert('Could not add task. Please try again.');
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      await deleteTask(taskId);
      await loadData();
    } catch {
      // silent
    }
  };

  if (loading) {
    return (
      <div className="view-container loading-center">
        <div className="pulsing-spinner-soft" />
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="view-container loading-center">
        <div className="empty-state-icon">⚠️</div>
        <p className="empty-state-text">{error}</p>
        <button className="primary-action-btn" onClick={loadData}>Retry</button>
      </div>
    );
  }

  const overallPct = progress?.overall_progress_percentage ?? 0;
  const completedChapters = progress?.completed_chapters ?? 0;
  const totalChapters = progress?.total_chapters ?? 0;
  const inProgressChapters = progress?.in_progress_chapters ?? 0;
  const streakDays = progress?.current_streak_days ?? 0;
  const focusMinutes = progress?.total_focus_minutes ?? 0;
  const focusLabel = formatFocusTime(focusMinutes);

  const pendingTasks = tasks.filter((t) => !t.completed);
  const completedTasksCount = tasks.filter((t) => t.completed).length;
  const hasAnyActivity = completedChapters > 0 || tasks.length > 0 || inProgressChapters > 0;

  return (
    <div className="today-dashboard-shell">
      {/* Greeting */}
      <header className="dashboard-top-banner">
        <div className="banner-titles-col">
          <h1 className="greeting-main">{getGreeting()} 👋</h1>
          <p className="greeting-sub">
            {hasAnyActivity
              ? `${completedChapters} of ${totalChapters} chapters done · ${inProgressChapters > 0 ? `${inProgressChapters} in progress` : 'keep going'}`
              : 'Your study day starts here. Choose where to begin.'}
          </p>
        </div>
        {streakDays > 0 && (
          <div className="banner-badge-col">
            <span className="efficiency-chip">
              <span className="dot-active" />
              {streakDays}-day streak
              {focusLabel ? ` · ${focusLabel} total` : ''}
            </span>
          </div>
        )}
      </header>

      {/* Sathi Quick Action Card */}
      <section className="sathi-hero-card">
        <div className="hero-top-meta">
          <span className="sathi-hero-tag">SATHI AI</span>
        </div>
        <p className="hero-prompt-text">
          {hasAnyActivity
            ? 'Ask Sathi about any chapter, section, or standard — or get a study plan for today.'
            : 'New here? Tell Sathi what you want to study and get started right away.'}
        </p>
        <div className="hero-actions-row">
          <button
            className="hero-talk-btn"
            onClick={() => onNavigate?.('companion')}
          >
            <span className="btn-icon">💬</span> Talk to Sathi
          </button>
          <button
            className="hero-quick-btn"
            onClick={() => onAskInChat?.('What should I study today based on my current CA progress and weak areas?')}
          >
            Get Today's Plan →
          </button>
        </div>
      </section>

      {/* Dashboard Grid */}
      <div className="dashboard-main-grid">
        {/* Left: Tasks + Revisions */}
        <div className="dashboard-left-col">
          {/* Due Revisions */}
          {dueRevisions.length > 0 && (
            <div className="today-revisions-card">
              <div className="revisions-header-row">
                <span className="revisions-label">Revisions Due Today</span>
                <span className="revisions-count-badge">{dueRevisions.length}</span>
              </div>
              <div className="revisions-list">
                {dueRevisions.slice(0, 4).map((rev) => (
                  <div key={rev.id} className="revision-due-row">
                    <span className="revision-due-topic">{rev.topic_id?.replace(/_/g, ' ') || 'Topic'}</span>
                    <button
                      className="revision-due-btn"
                      onClick={() => onNavigate?.('practice')}
                    >
                      Practise
                    </button>
                  </div>
                ))}
                {dueRevisions.length > 4 && (
                  <button className="view-all-link" onClick={() => onNavigate?.('practice')}>
                    +{dueRevisions.length - 4} more → Practice hub
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Study Targets */}
          <div className="today-tasks-checklist">
            <div className="tasks-header-row">
              <span className="tasks-eyebrow">
                Study Targets
                {tasks.length > 0 && ` (${completedTasksCount}/${tasks.length})`}
              </span>
            </div>

            {tasks.length === 0 ? (
              <div className="tasks-empty-state">
                <p>No targets yet. Add something to focus on today.</p>
              </div>
            ) : (
              <div className="checklist-items">
                {tasks.map((t) => (
                  <div key={t.id} className="checklist-row-item">
                    <label className="checklist-row">
                      <input
                        type="checkbox"
                        checked={t.completed}
                        onChange={() => handleToggleTask(t.id)}
                        aria-label={`Mark "${t.title}" as ${t.completed ? 'incomplete' : 'complete'}`}
                      />
                      <span className={t.completed ? 'task-done' : ''}>{t.title}</span>
                    </label>
                    <button
                      className="task-delete-btn"
                      onClick={() => handleDeleteTask(t.id)}
                      aria-label={`Delete task: ${t.title}`}
                      title="Remove"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}

            <form className="timeline-quick-add" onSubmit={handleAddTask}>
              <input
                type="text"
                placeholder="Add a study target for today..."
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                className="timeline-input"
                aria-label="New study target"
              />
              {newTaskTitle.trim() && (
                <button type="submit" className="timeline-add-submit">
                  Add
                </button>
              )}
            </form>
          </div>
        </div>

        {/* Right: Progress + Quick Actions */}
        <div className="dashboard-right-col">
          {/* Syllabus Progress */}
          <div className="dash-widget-card syllabus-widget">
            <div className="widget-top-line">
              <span className="widget-eyebrow">Syllabus Progress</span>
              <button className="widget-link-btn" onClick={() => onNavigate?.('progress')}>
                Details →
              </button>
            </div>

            {totalChapters === 0 ? (
              <div className="widget-empty">
                <p>No syllabus data yet.</p>
                <button className="widget-action-btn" onClick={() => onNavigate?.('study')}>
                  Open Study →
                </button>
              </div>
            ) : (
              <>
                <div className="syllabus-big-metric">
                  <span className="pct-num">{overallPct}%</span>
                  <span className="pct-label">covered</span>
                </div>
                <div className="bar-track" style={{ margin: '8px 0' }}>
                  <div className="bar-fill" style={{ width: `${overallPct}%` }} />
                </div>
                <p className="syllabus-stats-line">
                  {completedChapters} of {totalChapters} chapters completed
                  {inProgressChapters > 0 && ` · ${inProgressChapters} in progress`}
                </p>
              </>
            )}
          </div>

          {/* Focus Time */}
          {focusMinutes > 0 && (
            <div className="dash-widget-card focus-widget">
              <div className="widget-top-line">
                <span className="widget-eyebrow">Total Focus Time</span>
              </div>
              <div className="focus-big-num">
                {focusLabel}
                <span className="focus-total"> recorded</span>
              </div>
              <button
                className="widget-action-btn"
                style={{ marginTop: '10px' }}
                onClick={() => onNavigate?.('sanctuary')}
              >
                Start Focus Timer →
              </button>
            </div>
          )}

          {/* Quick Navigation */}
          <div className="dash-widget-card drill-widget">
            <div className="widget-top-line">
              <span className="widget-eyebrow">Quick Actions</span>
            </div>
            <div className="drill-cards-grid">
              <button className="drill-item-box" onClick={() => onNavigate?.('study')}>
                <span className="drill-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                  </svg>
                </span>
                <span className="drill-name">Study</span>
                <span className="drill-sub-badge">Syllabus</span>
              </button>

              <button className="drill-item-box" onClick={() => onNavigate?.('practice')}>
                <span className="drill-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /><path d="M9 14l2 2 4-4" />
                  </svg>
                </span>
                <span className="drill-name">Practice</span>
                <span className="drill-sub-badge">
                  {dueRevisions.length > 0 ? `${dueRevisions.length} due` : 'Questions'}
                </span>
              </button>

              <button className="drill-item-box" onClick={() => onNavigate?.('sanctuary')}>
                <span className="drill-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                  </svg>
                </span>
                <span className="drill-name">Focus</span>
                <span className="drill-sub-badge">Timer</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

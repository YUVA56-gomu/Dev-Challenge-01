import React, { useState, useEffect } from 'react';
import { fetchProgress, fetchTasks, createTask, toggleTask, deleteTask } from '../services/api';

export default function ProgressView() {
  const [progress, setProgress] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [loading, setLoading] = useState(true);

  const loadAll = async () => {
    try {
      const [progData, tasksData] = await Promise.all([fetchProgress(), fetchTasks()]);
      setProgress(progData);
      setTasks(tasksData);
    } catch (err) {
      console.error('Error loading progress/tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;
    try {
      await createTask(newTaskTitle.trim());
      setNewTaskTitle('');
      await loadAll();
    } catch (err) {
      alert('Failed to add task');
    }
  };

  const handleToggleTask = async (taskId) => {
    try {
      await toggleTask(taskId);
      await loadAll();
    } catch (err) {
      alert('Failed to toggle task');
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      await deleteTask(taskId);
      await loadAll();
    } catch (err) {
      alert('Failed to delete task');
    }
  };

  if (loading) {
    return (
      <div className="view-container loading-center">
        <div className="pulsing-spinner"></div>
        <p>Loading study progress metrics...</p>
      </div>
    );
  }

  return (
    <div className="view-container progress-view">
      <div className="view-header">
        <div>
          <h2>Study Progress & Daily Tasks</h2>
          <p className="view-subtitle">
            Consistency over intensity. Track your daily habits, study streak, and milestones.
          </p>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card highlight-metric">
          <div className="metric-icon">🔥</div>
          <div className="metric-content">
            <span className="metric-value">{progress?.current_streak_days || 1} Day</span>
            <span className="metric-label">Current Study Streak</span>
          </div>
          <div className="metric-subtext">Last active: {progress?.last_active_date || 'Today'}</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">📈</div>
          <div className="metric-content">
            <span className="metric-value">{progress?.overall_progress_percentage || 0}%</span>
            <span className="metric-label">Overall CA Syllabus</span>
          </div>
          <div className="metric-subtext">
            {progress?.completed_chapters} of {progress?.total_chapters} chapters mastered
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🎯</div>
          <div className="metric-content">
            <span className="metric-value">
              {progress?.tasks_completed} / {progress?.tasks_total}
            </span>
            <span className="metric-label">Today's Tasks Completed</span>
          </div>
          <div className="metric-subtext">
            {progress?.tasks_total - progress?.tasks_completed} remaining for today
          </div>
        </div>
      </div>

      {/* Chapter Distribution Breakdown */}
      <div className="distribution-card">
        <h3>Syllabus Distribution</h3>
        <div className="distribution-bar-wrapper">
          <div className="distribution-bar">
            <div
              className="dist-segment completed"
              style={{
                width: `${(progress?.completed_chapters / progress?.total_chapters) * 100}%`,
              }}
              title={`Completed: ${progress?.completed_chapters}`}
            ></div>
            <div
              className="dist-segment in-progress"
              style={{
                width: `${(progress?.in_progress_chapters / progress?.total_chapters) * 100}%`,
              }}
              title={`In Progress: ${progress?.in_progress_chapters}`}
            ></div>
            <div
              className="dist-segment not-started"
              style={{
                width: `${(progress?.not_started_chapters / progress?.total_chapters) * 100}%`,
              }}
              title={`Not Started: ${progress?.not_started_chapters}`}
            ></div>
          </div>
        </div>
        <div className="distribution-legend">
          <span className="legend-item">
            <span className="legend-dot completed"></span>
            Completed: {progress?.completed_chapters}
          </span>
          <span className="legend-item">
            <span className="legend-dot in-progress"></span>
            In Progress: {progress?.in_progress_chapters}
          </span>
          <span className="legend-item">
            <span className="legend-dot not-started"></span>
            Not Started: {progress?.not_started_chapters}
          </span>
        </div>
      </div>

      {/* Daily Tasks Board */}
      <div className="tasks-board-card">
        <div className="tasks-header">
          <div>
            <h3>Daily Study Tasks</h3>
            <p className="tasks-sub">Small consistent daily targets lead to clearing the group.</p>
          </div>
        </div>

        <form className="add-task-form" onSubmit={handleAddTask}>
          <input
            type="text"
            className="task-input"
            placeholder="Add a new task (e.g. Solve 3 practical sums of AS 10, revise Section 17(5))..."
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
          />
          <button type="submit" className="primary-button add-task-btn" disabled={!newTaskTitle.trim()}>
            + Add Task
          </button>
        </form>

        <div className="tasks-list">
          {tasks.length === 0 ? (
            <div className="empty-tasks-state">
              <span>☕</span> No tasks for today. Add one above!
            </div>
          ) : (
            tasks.map((task) => (
              <div key={task.id} className={`task-item ${task.completed ? 'completed' : ''}`}>
                <label className="task-checkbox-label">
                  <input
                    type="checkbox"
                    checked={task.completed}
                    onChange={() => handleToggleTask(task.id)}
                  />
                  <span className="checkmark"></span>
                  <span className="task-title-text">{task.title}</span>
                </label>
                <div className="task-item-meta">
                  <span className="task-subject-tag">{task.subject_name}</span>
                  <button
                    className="delete-task-btn"
                    onClick={() => handleDeleteTask(task.id)}
                    title="Delete task"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

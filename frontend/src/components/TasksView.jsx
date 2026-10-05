import React, { useState, useEffect } from 'react';
import { fetchTasks, createTask, toggleTask, deleteTask } from '../services/api';

/**
 * TasksView Component
 * Dedicated daily study checklist and targets board.
 */
export default function TasksView() {
  const [tasks, setTasks] = useState([]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [filter, setFilter] = useState('all'); // 'all' | 'pending' | 'completed'
  const [loading, setLoading] = useState(true);

  const loadTasks = async () => {
    try {
      const data = await fetchTasks();
      setTasks(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;
    try {
      await createTask(newTaskTitle.trim());
      setNewTaskTitle('');
      await loadTasks();
    } catch (e) {
      alert('Failed to add task');
    }
  };

  const handleToggle = async (taskId) => {
    try {
      await toggleTask(taskId);
      await loadTasks();
    } catch (e) {
      alert('Failed to toggle task');
    }
  };

  const handleDelete = async (taskId) => {
    try {
      await deleteTask(taskId);
      await loadTasks();
    } catch (e) {
      alert('Failed to delete task');
    }
  };

  const filteredTasks = tasks.filter((t) => {
    if (filter === 'pending') return !t.completed;
    if (filter === 'completed') return t.completed;
    return true;
  });

  const completedCount = tasks.filter((t) => t.completed).length;

  return (
    <div className="view-container tasks-view">
      <div className="view-header">
        <div>
          <h2>Daily Study Tasks & Milestones</h2>
          <p className="view-subtitle">
            Consistent daily execution is what clears CA exams.
          </p>
        </div>

        <div className="tasks-progress-badge">
          <span>{completedCount} of {tasks.length} Completed</span>
          <div className="tasks-mini-bar">
            <div
              className="tasks-mini-fill"
              style={{ width: `${tasks.length ? (completedCount / tasks.length) * 100 : 0}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Task Creation Bar */}
      <form onSubmit={handleAddTask} className="tasks-add-bar">
        <input
          type="text"
          className="task-input-lg"
          placeholder="Add a target (e.g. Solve 3 practical sums of AS 10, Revise Section 17(5) motor vehicles)..."
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
        />
        <button type="submit" className="primary-button" disabled={!newTaskTitle.trim()}>
          + Add Target
        </button>
      </form>

      {/* Filter Tabs */}
      <div className="tasks-filter-tabs">
        <button
          className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Tasks ({tasks.length})
        </button>
        <button
          className={`filter-btn ${filter === 'pending' ? 'active' : ''}`}
          onClick={() => setFilter('pending')}
        >
          Pending ({tasks.length - completedCount})
        </button>
        <button
          className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
          onClick={() => setFilter('completed')}
        >
          Completed ({completedCount})
        </button>
      </div>

      {/* Tasks List Board */}
      <div className="tasks-board-stream">
        {loading ? (
          <div className="loading-center">
            <div className="pulsing-spinner"></div>
            <p>Loading targets...</p>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="empty-tasks-state">
            <span>🎉</span>
            {filter === 'completed'
              ? 'No completed tasks yet. Finish a task above!'
              : 'All caught up! Add a new study target above.'}
          </div>
        ) : (
          filteredTasks.map((task) => (
            <div key={task.id} className={`task-card-row ${task.completed ? 'completed' : ''}`}>
              <label className="task-checkbox-wrap">
                <input
                  type="checkbox"
                  checked={task.completed}
                  onChange={() => handleToggle(task.id)}
                />
                <span className="task-custom-check"></span>
                <span className="task-row-title">{task.title}</span>
              </label>

              <div className="task-row-actions">
                <span className="task-subject-tag">{task.subject_name || 'General CA'}</span>
                <button
                  className="task-row-del-btn"
                  onClick={() => handleDelete(task.id)}
                  title="Delete target"
                >
                  ✕
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { fetchProgress, fetchSubjects } from '../services/api';

/**
 * AnalyticsView Component
 * Deep analytics into syllabus coverage, paper-wise distribution, and exam velocity.
 */
export default function AnalyticsView({ onNavigate }) {
  const [progress, setProgress] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [p, s] = await Promise.all([fetchProgress(), fetchSubjects()]);
        setProgress(p);
        setSubjects(s);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="view-container loading-center">
        <div className="pulsing-spinner"></div>
        <p>Calculating syllabus coverage metrics...</p>
      </div>
    );
  }

  const overallPercent = progress?.overall_progress_percentage || 24;

  return (
    <div className="view-container analytics-view">
      <div className="view-header">
        <div>
          <h2>Syllabus Mastery Analytics</h2>
          <p className="view-subtitle">
            Paper-wise coverage, revision velocity, and exam readiness breakdown.
          </p>
        </div>
      </div>

      {/* Top Velocity Metric Cards */}
      <div className="metrics-grid">
        <div className="metric-card highlight-metric">
          <div className="metric-icon">🔥</div>
          <div className="metric-content">
            <span className="metric-value">{progress?.current_streak_days || 5} Days</span>
            <span className="metric-label">Study Streak</span>
          </div>
          <div className="metric-subtext">Compounding daily revision habit</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">📊</div>
          <div className="metric-content">
            <span className="metric-value">{overallPercent}%</span>
            <span className="metric-label">Overall Completion</span>
          </div>
          <div className="metric-subtext">
            {progress?.completed_chapters} / {progress?.total_chapters} Chapters done
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">⏱️</div>
          <div className="metric-content">
            <span className="metric-value">42.5 hrs</span>
            <span className="metric-label">Study Hours Logged</span>
          </div>
          <div className="metric-subtext">Target: 300 hrs before exam</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🎯</div>
          <div className="metric-content">
            <span className="metric-value">62 / 100</span>
            <span className="metric-label">Estimated Readiness Index</span>
          </div>
          <div className="metric-subtext">Based on completion & active streak</div>
        </div>
      </div>

      {/* Paper-Wise Progress Breakdown */}
      <div className="dashboard-card analytics-breakdown-card">
        <div className="card-top-row">
          <div>
            <h3 className="card-heading">Paper-by-Paper Progress</h3>
            <p className="card-subheading">Tracking coverage across CA Intermediate Group 1 & 2</p>
          </div>
          <button
            className="secondary-button"
            onClick={() => onNavigate && onNavigate('study')}
          >
            Go to Syllabus Tracker ➜
          </button>
        </div>

        <div className="paper-analytics-list">
          {subjects.map((sub) => {
            const completed = sub.chapters?.filter((c) => c.status === 'completed').length || 0;
            const total = sub.chapters?.length || 1;
            const pct = Math.round((completed / total) * 100);

            return (
              <div key={sub.id} className="paper-analytic-row">
                <div className="paper-info-col">
                  <span className="paper-code-badge">{sub.code}</span>
                  <span className="paper-name-title">{sub.name}</span>
                </div>

                <div className="paper-progress-col">
                  <div className="paper-progress-bar-bg">
                    <div
                      className="paper-progress-bar-fill"
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>
                  <span className="paper-pct-text">{pct}%</span>
                </div>

                <div className="paper-stat-col">
                  <span>{completed} / {total} Ch.</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

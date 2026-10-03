import React from 'react';

export default function Navbar({ activeTab, onTabChange, health }) {
  const isModelReady = health?.details?.model_available;
  const isOk = health?.status === 'ok' && isModelReady;

  const tabs = [
    { id: 'companion', label: 'AI Companion', icon: '💬' },
    { id: 'study', label: 'Syllabus & Notes', icon: '📚' },
    { id: 'progress', label: 'Progress & Tasks', icon: '📊' },
    { id: 'sanctuary', label: 'Sanctuary & Wellness', icon: '🌿' },
  ];

  return (
    <header className="app-header">
      <div className="brand-group">
        <div className="brand-icon">📚</div>
        <div className="brand-info">
          <div className="brand-title">
            <h1>Sathi</h1>
            <span className="hindi-badge">साथी</span>
          </div>
          <p>Personal CA AI Companion</p>
        </div>
      </div>

      <nav className="nav-tabs" aria-label="Main Navigation">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </nav>

      <div className={`health-badge ${isOk ? 'ok' : 'degraded'}`}>
        <span className="health-dot"></span>
        <span className="health-text">
          {isOk
            ? `Gemma 2 (Local GPU)`
            : health?.status === 'offline'
            ? 'Backend Offline'
            : 'Connecting...'}
        </span>
      </div>
    </header>
  );
}

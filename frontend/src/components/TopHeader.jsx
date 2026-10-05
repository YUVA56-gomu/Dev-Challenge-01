import React, { useMemo } from 'react';

const PAGE_TITLES = {
  today:     'Today',
  study:     'Study',
  practice:  'Practice',
  companion: 'Sathi AI',
  progress:  'Progress',
  sanctuary: 'Sanctuary',
  settings:  'Settings',
};

export default function TopHeader({ activeTab, theme = 'light', onToggleTheme, onToggleSidebar, onTabChange, streak, totalFocusMinutes }) {
  const title = PAGE_TITLES[activeTab] || 'Sathi';

  const dateLabel = useMemo(() => {
    return new Date().toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });
  }, []);

  const focusLabel = useMemo(() => {
    if (!totalFocusMinutes) return null;
    const h = Math.floor(totalFocusMinutes / 60);
    const m = totalFocusMinutes % 60;
    if (h > 0 && m > 0) return `${h}h ${m}m`;
    if (h > 0) return `${h}h`;
    return `${m}m`;
  }, [totalFocusMinutes]);

  return (
    <header className="calm-top-header" role="banner">
      {/* Left */}
      <div className="top-header-left">
        <button
          className="mobile-sidebar-toggle"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <span className="crumb-page-title">{title}</span>
      </div>

      {/* Center search */}
      <div className="top-header-center" role="search">
        <div
          className="global-search-wrapper"
          onClick={() => onTabChange('study')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onTabChange('study')}
          aria-label="Search topics and sections"
        >
          <svg className="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            className="global-search-input"
            placeholder="Search topics, sections, standards..."
            readOnly
            tabIndex={-1}
            aria-label="Search"
          />
          <span className="search-kbd-badge" aria-hidden="true">⌘K</span>
        </div>
      </div>

      {/* Right */}
      <div className="top-header-right">
        <div className="header-meta-chip date-chip" aria-label={`Today is ${dateLabel}`}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span>{dateLabel}</span>
        </div>

        {streak > 0 && (
          <div className="header-meta-chip streak-chip" aria-label={`${streak}-day study streak`}>
            <span className="chip-icon" aria-hidden="true">🔥</span>
            <span>{streak}d streak{focusLabel ? ` · ${focusLabel}` : ''}</span>
          </div>
        )}

        <button
          className="theme-toggle-btn"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
        </button>

        <button
          className="student-profile-chip"
          onClick={() => onTabChange('settings')}
          aria-label="Open settings"
        >
          <div className="student-avatar-orb" aria-hidden="true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <div className="student-info-col">
            <span className="student-name-text">CA Student</span>
            <span className="student-role-text">Intermediate</span>
          </div>
        </button>
      </div>
    </header>
  );
}

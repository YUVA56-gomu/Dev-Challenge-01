import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import TodayView from './components/TodayView';
import StudyView from './components/StudyView';
import PracticeView from './components/PracticeView';
import CompanionView from './components/CompanionView';
import ProgressView from './components/ProgressView';
import SanctuaryView from './components/SanctuaryView';
import SettingsView from './components/SettingsView';
import { fetchHealth, fetchProgress } from './services/api';
import './App.css';

export default function App() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('sathi-theme');
    if (saved) return saved;
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sathi-theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme((p) => (p === 'dark' ? 'light' : 'dark'));

  const [activeTab, setActiveTab] = useState('today');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [health, setHealth] = useState({ status: 'checking', details: null });

  // Real streak / focus time for TopHeader
  const [streak, setStreak] = useState(0);
  const [totalFocusMinutes, setTotalFocusMinutes] = useState(0);

  useEffect(() => {
    const check = async () => {
      try {
        const data = await fetchHealth();
        setHealth({ status: data.status, details: data.ai_provider });
      } catch {
        setHealth({ status: 'offline', details: null });
      }
    };
    check();
    const iv = setInterval(check, 15000);
    return () => clearInterval(iv);
  }, []);

  // Load real streak from progress API
  useEffect(() => {
    fetchProgress()
      .then((d) => {
        if (d?.current_streak_days) setStreak(d.current_streak_days);
        if (d?.total_focus_minutes) setTotalFocusMinutes(d.total_focus_minutes);
      })
      .catch(() => {});
  }, [activeTab]); // refresh when navigating

  const [pendingStudyContext, setPendingStudyContext] = useState(null);
  const [pendingPracticeContext, setPendingPracticeContext] = useState(null);

  const handleAskInChat = (promptText, studyContext = null) => {
    if (studyContext) setPendingStudyContext(studyContext);
    setActiveTab('companion');
    if (promptText) {
      setTimeout(() => {
        const ta = document.querySelector('.companion-textarea');
        if (ta) {
          ta.value = promptText;
          ta.dispatchEvent(new Event('input', { bubbles: true }));
          ta.focus();
        }
      }, 150);
    }
  };

  const handleNavigateToPractice = (paperId = null, chapterId = null) => {
    if (paperId || chapterId) setPendingPracticeContext({ paperId, chapterId });
    setActiveTab('practice');
  };

  return (
    <div className="sathi-desktop-app">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="main-viewport-shell">
        <TopHeader
          activeTab={activeTab}
          theme={theme}
          onToggleTheme={toggleTheme}
          onToggleSidebar={() => setSidebarOpen((p) => !p)}
          onTabChange={setActiveTab}
          streak={streak}
          totalFocusMinutes={totalFocusMinutes}
        />

        <main className={`content-scroll-container${activeTab === 'companion' ? ' companion-container' : ''}`}>
          {activeTab === 'today' && (
            <TodayView onNavigate={setActiveTab} onAskInChat={handleAskInChat} />
          )}
          {activeTab === 'study' && (
            <StudyView onAskInChat={handleAskInChat} onNavigateToPractice={handleNavigateToPractice} />
          )}
          {activeTab === 'practice' && (
            <PracticeView
              onAskInChat={handleAskInChat}
              initialSubject={pendingPracticeContext?.paperId}
              initialChapter={pendingPracticeContext?.chapterId}
            />
          )}
          {activeTab === 'companion' && (
            <CompanionView
              initialContext={pendingStudyContext}
              onClearContext={() => setPendingStudyContext(null)}
            />
          )}
          {activeTab === 'progress' && (
            <ProgressView
              onNavigate={setActiveTab}
              onAskInChat={handleAskInChat}
              onNavigateToPractice={handleNavigateToPractice}
            />
          )}
          {activeTab === 'sanctuary' && (
            <SanctuaryView onReturnToStudy={setActiveTab} />
          )}
          {activeTab === 'settings' && (
            <SettingsView health={health} theme={theme} onToggleTheme={toggleTheme} />
          )}
        </main>
      </div>
    </div>
  );
}

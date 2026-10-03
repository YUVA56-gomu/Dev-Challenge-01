import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import CompanionView from './components/CompanionView';
import StudyView from './components/StudyView';
import ProgressView from './components/ProgressView';
import SanctuaryView from './components/SanctuaryView';
import { fetchHealth } from './services/api';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('companion');
  const [health, setHealth] = useState({ status: 'checking', details: null });

  // Check backend health periodically
  useEffect(() => {
    const check = async () => {
      try {
        const data = await fetchHealth();
        setHealth({ status: data.status, details: data.ai_provider });
      } catch (err) {
        setHealth({ status: 'offline', details: null });
      }
    };

    check();
    const interval = setInterval(check, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleAskInChat = (promptText) => {
    setActiveTab('companion');
    // Pre-fill prompt via custom event or let companion receive it
    setTimeout(() => {
      const textarea = document.querySelector('.input-textarea');
      if (textarea) {
        textarea.value = promptText;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.focus();
      }
    }, 100);
  };

  return (
    <div className="app-shell">
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} health={health} />

      <main className="content-area">
        {activeTab === 'companion' && <CompanionView health={health} />}
        {activeTab === 'study' && <StudyView onAskInChat={handleAskInChat} />}
        {activeTab === 'progress' && <ProgressView />}
        {activeTab === 'sanctuary' && <SanctuaryView />}
      </main>
    </div>
  );
}

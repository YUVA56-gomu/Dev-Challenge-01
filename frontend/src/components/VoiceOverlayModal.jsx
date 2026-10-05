import React, { useState } from 'react';
import { soundService } from '../services/soundService';

/**
 * VoiceOverlayModal — Full-screen immersive voice companion.
 * Shows animated background, live transcript, audio wave, control dock.
 */
export default function VoiceOverlayModal({
  isOpen,
  onClose,
  state = 'idle',
  statusHint = '',
  transcript = '',
  latestSpokenText = '',
  onToggleListening,
  autoSpeak,
  onToggleAutoSpeak,
  activeContext,
}) {
  const [showSettings, setShowSettings] = useState(false);
  const [ambientMusic, setAmbientMusic] = useState(false);

  if (!isOpen) return null;

  const getHeadline = () => {
    switch (state) {
      case 'listening': return "I'm listening...";
      case 'thinking':  return 'Sathi is thinking...';
      case 'speaking':  return 'Sathi is speaking...';
      case 'error':     return statusHint || 'Voice notice';
      default:          return 'Tap the mic to speak';
    }
  };

  const getSubline = () => {
    switch (state) {
      case 'listening': return "Speak clearly — I'll understand CA terms and section numbers";
      case 'thinking':  return 'Formulating an answer based on your syllabus...';
      case 'speaking':  return 'Tap the mic to interrupt and ask something new';
      case 'error':     return 'Using browser speech as fallback';
      default:          return 'Real-time voice conversation with your CA companion';
    }
  };

  const handleMicClick = () => {
    soundService.playSound('listening');
    onToggleListening();
  };

  const handleClose = () => {
    soundService.stopMusic();
    setAmbientMusic(false);
    onClose();
  };

  const toggleAmbient = () => {
    if (ambientMusic) {
      soundService.stopMusic();
      setAmbientMusic(false);
    } else {
      soundService.playMusic('companion_atmosphere', 0.15, true);
      setAmbientMusic(true);
    }
  };

  const isListening = state === 'listening';
  const isActive = state === 'listening' || state === 'speaking';

  return (
    <div className="voice-overlay-backdrop" role="dialog" aria-modal="true" aria-label="Voice companion">
      {/* Animated dark water background */}
      <div className="dark-water-bg" aria-hidden="true">
        <div className="water-layer-1" />
        <div className="water-layer-2" />
        <div className="ambient-radial-glow" />
      </div>

      {/* Main content */}
      <div className="voice-overlay-content">
        {/* Context chip */}
        {activeContext && (
          <div className="voice-context-chip">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            {activeContext.topic || activeContext.chapter || activeContext.paper}
          </div>
        )}

        {/* Headline */}
        <div className="voice-headline-container">
          <h1 className="voice-headline-text">{getHeadline()}</h1>
          <p className="voice-headline-sub">{getSubline()}</p>
        </div>

        {/* Live transcript */}
        {transcript && isListening && (
          <div className="live-transcript-panel" role="status" aria-live="polite">
            "{transcript}"
          </div>
        )}

        {latestSpokenText && state === 'speaking' && (
          <div className="live-transcript-panel spoken-panel" role="status" aria-live="polite">
            "{latestSpokenText}"
          </div>
        )}

        {/* Audio wave — visible when active */}
        {isActive && (
          <div className="audio-wave-bars" aria-hidden="true">
            <span className="bar bar-1" />
            <span className="bar bar-2" />
            <span className="bar bar-3" />
            <span className="bar bar-4" />
            <span className="bar bar-5" />
          </div>
        )}

        {/* Thinking dots */}
        {state === 'thinking' && (
          <div className="voice-thinking-dots" aria-hidden="true">
            <span /><span /><span />
          </div>
        )}
      </div>

      {/* Settings popover */}
      {showSettings && (
        <div className="voice-settings-popover" role="menu">
          <h4>Voice Settings</h4>
          <label className="popover-row" role="menuitem">
            <span>Auto-speak responses</span>
            <input
              type="checkbox"
              checked={autoSpeak}
              onChange={(e) => onToggleAutoSpeak(e.target.checked)}
              aria-label="Auto-speak toggle"
            />
          </label>
          <label className="popover-row" role="menuitem">
            <span>Ambient atmosphere</span>
            <input
              type="checkbox"
              checked={ambientMusic}
              onChange={toggleAmbient}
              aria-label="Ambient music toggle"
            />
          </label>
        </div>
      )}

      {/* Control dock */}
      <div className="voice-pill-dock" role="toolbar" aria-label="Voice controls">
        {/* Close */}
        <button
          className="dock-btn"
          onClick={handleClose}
          aria-label="Exit voice mode"
          title="Exit voice mode"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>

        {/* Context info */}
        <button
          className="dock-btn"
          onClick={() => {
            soundService.playSound('ident');
          }}
          aria-label="View active context"
          title={activeContext ? `Context: ${activeContext.paper || 'CA Studies'}` : 'All CA subjects ready'}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="6" cy="12" r="4"/><circle cx="18" cy="12" r="4"/><line x1="10" y1="12" x2="14" y2="12"/>
          </svg>
        </button>

        {/* Main mic */}
        <button
          className={`dock-btn central-mic ${isListening ? 'active-listening' : ''}`}
          onClick={handleMicClick}
          aria-label={isListening ? 'Stop listening' : 'Start speaking'}
          title={isListening ? 'Stop listening' : 'Speak to Sathi'}
        >
          {isListening ? (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
            </svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
          )}
        </button>

        {/* Settings */}
        <button
          className={`dock-btn ${showSettings ? 'active' : ''}`}
          onClick={() => setShowSettings((v) => !v)}
          aria-label="Voice settings"
          aria-expanded={showSettings}
          title="Settings"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
      </div>
    </div>
  );
}

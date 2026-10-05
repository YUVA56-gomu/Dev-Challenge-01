import React from 'react';

/**
 * VoiceOrb Component — Sathi's Living Companion Orb
 * States: 'idle' | 'listening' | 'thinking' | 'speaking' | 'error'
 * Uses SVG icons for consistent cross-platform rendering.
 */
export default function VoiceOrb({ state = 'idle', statusHint = '', onOrbClick }) {
  const getStatusText = () => {
    switch (state) {
      case 'listening': return 'Listening...';
      case 'thinking':  return 'Thinking...';
      case 'speaking':  return 'Speaking...';
      case 'error':     return 'Notice';
      default:          return 'Ready';
    }
  };

  const getSubStatusText = () => {
    if (statusHint) return statusHint;
    switch (state) {
      case 'listening': return 'Speak clearly, I'm listening';
      case 'thinking':  return 'Formulating your answer...';
      case 'speaking':  return 'Tap to pause';
      case 'error':     return 'Falling back to device voice';
      default:          return 'Tap to start speaking';
    }
  };

  const OrbIcon = () => {
    switch (state) {
      case 'listening':
        return (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
        );
      case 'thinking':
        return (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        );
      case 'speaking':
        return (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
          </svg>
        );
      case 'error':
        return (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        );
      default: // idle
        return (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
        );
    }
  };

  return (
    <div
      className={`voice-orb-container ${state}`}
      onClick={onOrbClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onOrbClick?.()}
      aria-label={`Sathi voice orb — ${getStatusText()}. ${getSubStatusText()}`}
      aria-live="polite"
    >
      <div className="voice-orb-stage" aria-hidden="true">
        {/* Ripple rings — visible during listening/speaking */}
        <div className="orb-ripple ring-1"></div>
        <div className="orb-ripple ring-2"></div>
        <div className="orb-ripple ring-3"></div>

        {/* Orbit ring — visible during thinking */}
        <div className="orb-orbit-ring">
          <div className="orbit-particle"></div>
        </div>

        {/* Core orb */}
        <div className="orb-core">
          <div className="orb-inner-glow"></div>
          <div className="orb-icon">
            <OrbIcon />
          </div>
        </div>
      </div>

      <div className="orb-status-text">
        <span className="orb-status-label">{getStatusText()}</span>
        <span className="orb-status-hint">{getSubStatusText()}</span>
      </div>
    </div>
  );
}

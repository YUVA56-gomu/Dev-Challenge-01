import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  saveSanctuaryReflection,
  fetchSanctuaryReflections,
  saveSanctuaryCheckin,
  fetchLatestCheckin,
  saveFocusSession,
} from '../services/api';
import { soundService } from '../services/soundService';

// ─── Timer presets ────────────────────────────────────────────────────────────
const FOCUS_PRESETS = [
  { label: '25 min', minutes: 25 },
  { label: '45 min', minutes: 45 },
  { label: '60 min', minutes: 60 },
];

const BREATHING_PRESETS = [
  { label: '1 min', cycles: 4 },   // ~4 cycles × ~16s
  { label: '3 min', cycles: 11 },
  { label: '5 min', cycles: 19 },
];

// 4-4-4-4 box breathing phases
const BOX_PHASES = ['Inhale', 'Hold', 'Exhale', 'Rest'];

const MOOD_OPTIONS = [
  { id: 'focused',     label: 'Focused',     emoji: '🎯' },
  { id: 'okay',        label: 'Okay',        emoji: '😌' },
  { id: 'tired',       label: 'Tired',       emoji: '😴' },
  { id: 'overwhelmed', label: 'Overwhelmed', emoji: '😤' },
  { id: 'break',       label: 'Need a break', emoji: '🌿' },
];

function fmt(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function SanctuaryView({ onReturnToStudy }) {
  const [activeSection, setActiveSection] = useState('home'); // home | breathing | focus | reflect | checkin
  const [musicPlaying, setMusicPlaying] = useState(false);

  // ── Breathing ──────────────────────────────────────────────────────────────
  const [breathRunning, setBreathRunning] = useState(false);
  const [breathPhaseIdx, setBreathPhaseIdx] = useState(0);
  const [breathPhaseSeconds, setBreathPhaseSeconds] = useState(4);
  const [breathCycles, setBreathCycles] = useState(0);
  const [breathPreset, setBreathPreset] = useState(BREATHING_PRESETS[0]);
  const breathTimerRef = useRef(null);

  const stopBreathing = useCallback(() => {
    clearInterval(breathTimerRef.current);
    setBreathRunning(false);
    setBreathPhaseIdx(0);
    setBreathPhaseSeconds(4);
  }, []);

  const startBreathing = useCallback(() => {
    setBreathCycles(0);
    setBreathPhaseIdx(0);
    setBreathPhaseSeconds(4);
    setBreathRunning(true);
  }, []);

  useEffect(() => {
    if (!breathRunning) {
      clearInterval(breathTimerRef.current);
      return;
    }
    breathTimerRef.current = setInterval(() => {
      setBreathPhaseSeconds((prev) => {
        if (prev > 1) return prev - 1;
        // Advance phase
        setBreathPhaseIdx((pi) => {
          const next = (pi + 1) % BOX_PHASES.length;
          if (next === 0) {
            setBreathCycles((c) => {
              const newC = c + 1;
              if (newC >= breathPreset.cycles) {
                stopBreathing();
              }
              return newC;
            });
          }
          return next;
        });
        return 4;
      });
    }, 1000);
    return () => clearInterval(breathTimerRef.current);
  }, [breathRunning, breathPreset.cycles, stopBreathing]);

  // ── Focus Timer ─────────────────────────────────────────────────────────────
  const [focusPreset, setFocusPreset] = useState(FOCUS_PRESETS[0]);
  const [customMinutes, setCustomMinutes] = useState('');
  const [focusSecondsLeft, setFocusSecondsLeft] = useState(FOCUS_PRESETS[0].minutes * 60);
  const [focusRunning, setFocusRunning] = useState(false);
  const [focusPaused, setFocusPaused] = useState(false);
  const [focusDone, setFocusDone] = useState(false);
  const [focusSaving, setFocusSaving] = useState(false);
  const focusTimerRef = useRef(null);
  const focusStartedMinutes = useRef(0);

  const resetFocusTimer = useCallback((minutes) => {
    clearInterval(focusTimerRef.current);
    setFocusSecondsLeft(minutes * 60);
    setFocusRunning(false);
    setFocusPaused(false);
    setFocusDone(false);
  }, []);

  const startFocusTimer = useCallback(() => {
    const mins = customMinutes ? parseInt(customMinutes, 10) : focusPreset.minutes;
    if (!mins || mins < 1) return;
    focusStartedMinutes.current = mins;
    setFocusSecondsLeft(mins * 60);
    setFocusRunning(true);
    setFocusPaused(false);
    setFocusDone(false);
  }, [customMinutes, focusPreset.minutes]);

  useEffect(() => {
    if (!focusRunning || focusPaused) {
      clearInterval(focusTimerRef.current);
      return;
    }
    focusTimerRef.current = setInterval(() => {
      setFocusSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(focusTimerRef.current);
          setFocusRunning(false);
          setFocusDone(true);
          soundService.playSound('meditation_complete');
          // Persist completed session
          const mins = focusStartedMinutes.current;
          setFocusSaving(true);
          saveFocusSession(mins, true).finally(() => setFocusSaving(false));
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(focusTimerRef.current);
  }, [focusRunning, focusPaused]);

  // ── Reflection ──────────────────────────────────────────────────────────────
  const [reflectionText, setReflectionText] = useState('');
  const [reflectionSaving, setReflectionSaving] = useState(false);
  const [reflectionSaved, setReflectionSaved] = useState(false);
  const [reflections, setReflections] = useState([]);
  const [reflectionsLoading, setReflectionsLoading] = useState(false);

  const loadReflections = useCallback(async () => {
    setReflectionsLoading(true);
    try {
      const data = await fetchSanctuaryReflections();
      setReflections(data || []);
    } catch { /* silent */ } finally {
      setReflectionsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeSection === 'reflect') loadReflections();
  }, [activeSection, loadReflections]);

  const handleSaveReflection = async (e) => {
    e.preventDefault();
    if (!reflectionText.trim() || reflectionSaving) return;
    setReflectionSaving(true);
    try {
      await saveSanctuaryReflection(reflectionText.trim());
      setReflectionText('');
      setReflectionSaved(true);
      setTimeout(() => setReflectionSaved(false), 3000);
      loadReflections();
    } catch {
      alert('Could not save reflection. Please try again.');
    } finally {
      setReflectionSaving(false);
    }
  };

  // ── Check-in ────────────────────────────────────────────────────────────────
  const [selectedMood, setSelectedMood] = useState(null);
  const [checkinSaving, setCheckinSaving] = useState(false);
  const [checkinSaved, setCheckinSaved] = useState(false);
  const [latestCheckin, setLatestCheckin] = useState(null);

  useEffect(() => {
    if (activeSection === 'checkin') {
      fetchLatestCheckin().then((d) => setLatestCheckin(d)).catch(() => {});
    }
  }, [activeSection]);

  const handleSaveCheckin = async (mood) => {
    setSelectedMood(mood);
    setCheckinSaving(true);
    try {
      await saveSanctuaryCheckin(mood);
      setCheckinSaved(true);
      setLatestCheckin({ mood, created_at: new Date().toISOString() });
      setTimeout(() => setCheckinSaved(false), 3000);
    } catch { /* silent */ } finally {
      setCheckinSaving(false);
    }
  };

  // ── Ambient music ────────────────────────────────────────────────────────────
  const toggleMusic = () => {
    if (musicPlaying) {
      soundService.stopMusic();
      setMusicPlaying(false);
    } else {
      soundService.playMusic('sanctuary_1', 0.18, true);
      setMusicPlaying(true);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearInterval(breathTimerRef.current);
      clearInterval(focusTimerRef.current);
      soundService.stopMusic();
    };
  }, []);

  const handleReturn = () => {
    soundService.stopMusic();
    setMusicPlaying(false);
    onReturnToStudy?.('today');
  };

  // ─── Section renderers ────────────────────────────────────────────────────

  const renderHome = () => (
    <div className="sanctuary-home-grid">
      <button className="sanctuary-feature-card" onClick={() => setActiveSection('breathing')}>
        <div className="sanctuary-feature-icon">🫁</div>
        <h3 className="sanctuary-feature-title">Breathing</h3>
        <p className="sanctuary-feature-desc">4-4-4-4 box breathing to calm your nervous system before studying.</p>
      </button>

      <button className="sanctuary-feature-card" onClick={() => setActiveSection('focus')}>
        <div className="sanctuary-feature-icon">⏱</div>
        <h3 className="sanctuary-feature-title">Focus Timer</h3>
        <p className="sanctuary-feature-desc">Timed study sessions that record your focus time automatically.</p>
      </button>

      <button className="sanctuary-feature-card" onClick={() => setActiveSection('reflect')}>
        <div className="sanctuary-feature-icon">📝</div>
        <h3 className="sanctuary-feature-title">Reflection</h3>
        <p className="sanctuary-feature-desc">Write a private note about what went well or what feels difficult.</p>
      </button>

      <button className="sanctuary-feature-card" onClick={() => setActiveSection('checkin')}>
        <div className="sanctuary-feature-icon">💬</div>
        <h3 className="sanctuary-feature-title">Check-in</h3>
        <p className="sanctuary-feature-desc">A quick moment to note how you're feeling about today's study.</p>
      </button>
    </div>
  );

  const renderBreathing = () => {
    const phaseName = BOX_PHASES[breathPhaseIdx];
    const isInhale = phaseName === 'Inhale';
    const isExhale = phaseName === 'Exhale';
    const orbClass = breathRunning
      ? isInhale ? 'inhale' : isExhale ? 'exhale' : ''
      : '';

    return (
      <div className="sanctuary-section-panel">
        <h2 className="sanctuary-section-title">Box Breathing</h2>
        <p className="sanctuary-section-sub">4 counts each: Inhale · Hold · Exhale · Rest. Repeat to settle before studying.</p>

        {/* Preset selector */}
        {!breathRunning && (
          <div className="sanctuary-preset-row">
            {BREATHING_PRESETS.map((p) => (
              <button
                key={p.label}
                className={`sanctuary-preset-btn ${breathPreset.label === p.label ? 'active' : ''}`}
                onClick={() => setBreathPreset(p)}
              >
                {p.label}
              </button>
            ))}
          </div>
        )}

        {/* Orb */}
        <div className="breathing-orb-container">
          <div className={`calm-breathing-orb ${orbClass}`}>
            <div className="orb-center-label">
              {breathRunning ? (
                <>
                  <span className="orb-phase-name">{phaseName}</span>
                  <span className="orb-seconds-num">{breathPhaseSeconds}s</span>
                </>
              ) : (
                <span className="orb-phase-name">Ready</span>
              )}
            </div>
          </div>
        </div>

        {breathCycles > 0 && (
          <p className="cycle-count-tag">
            {breathCycles} / {breathPreset.cycles} cycles
            {breathCycles >= breathPreset.cycles && ' — Complete ✓'}
          </p>
        )}

        <div className="sanctuary-controls-row">
          {!breathRunning ? (
            <button className="sanctuary-primary-btn" onClick={startBreathing}>
              Start
            </button>
          ) : (
            <button className="sanctuary-danger-btn" onClick={stopBreathing}>
              Stop
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderFocus = () => {
    const effectiveMinutes = customMinutes ? parseInt(customMinutes, 10) : focusPreset.minutes;
    const totalSeconds = (effectiveMinutes || focusPreset.minutes) * 60;
    const elapsed = totalSeconds - focusSecondsLeft;
    const progressPct = totalSeconds > 0 ? Math.round((elapsed / totalSeconds) * 100) : 0;

    return (
      <div className="sanctuary-section-panel">
        <h2 className="sanctuary-section-title">Focus Timer</h2>
        <p className="sanctuary-section-sub">
          Set a timer for your study session. Completed sessions are saved to your focus time total.
        </p>

        {!focusRunning && !focusDone && (
          <>
            <div className="sanctuary-preset-row">
              {FOCUS_PRESETS.map((p) => (
                <button
                  key={p.label}
                  className={`sanctuary-preset-btn ${!customMinutes && focusPreset.label === p.label ? 'active' : ''}`}
                  onClick={() => {
                    setFocusPreset(p);
                    setCustomMinutes('');
                    setFocusSecondsLeft(p.minutes * 60);
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div className="sanctuary-custom-row">
              <input
                type="number"
                min="1"
                max="180"
                placeholder="Custom minutes"
                value={customMinutes}
                onChange={(e) => {
                  setCustomMinutes(e.target.value);
                  const v = parseInt(e.target.value, 10);
                  if (v > 0) setFocusSecondsLeft(v * 60);
                }}
                className="sanctuary-custom-input"
                aria-label="Custom focus duration in minutes"
              />
            </div>
          </>
        )}

        {/* Timer display */}
        <div className="focus-timer-display">
          <span className={`focus-timer-num ${focusSecondsLeft < 60 && focusRunning ? 'warning' : ''}`}>
            {fmt(focusSecondsLeft)}
          </span>
          {focusRunning && (
            <p className="focus-timer-label">
              {focusPaused ? 'Paused' : 'Focusing...'}
            </p>
          )}
        </div>

        {/* Progress bar */}
        {focusRunning && (
          <div className="focus-progress-track">
            <div className="focus-progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
        )}

        {focusDone && (
          <div className="focus-done-banner">
            <span>Session complete {focusSaving ? '— saving...' : '✓ saved to your focus time'}</span>
          </div>
        )}

        <div className="sanctuary-controls-row">
          {!focusRunning && !focusDone && (
            <button className="sanctuary-primary-btn" onClick={startFocusTimer}>
              Start Session
            </button>
          )}
          {focusRunning && !focusPaused && (
            <button className="sanctuary-secondary-btn" onClick={() => setFocusPaused(true)}>
              Pause
            </button>
          )}
          {focusRunning && focusPaused && (
            <button className="sanctuary-primary-btn" onClick={() => setFocusPaused(false)}>
              Resume
            </button>
          )}
          {(focusRunning || focusDone) && (
            <button
              className="sanctuary-danger-btn"
              onClick={() => {
                if (focusRunning && focusStartedMinutes.current > 0) {
                  const elapsedMins = Math.floor(elapsed / 60);
                  if (elapsedMins >= 1) saveFocusSession(elapsedMins, false);
                }
                resetFocusTimer(focusPreset.minutes);
              }}
            >
              Stop
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderReflect = () => (
    <div className="sanctuary-section-panel">
      <h2 className="sanctuary-section-title">Private Reflection</h2>
      <p className="sanctuary-section-sub">
        Write a short note for yourself. Reflections are stored privately and never shared.
      </p>

      <form onSubmit={handleSaveReflection} className="sanctuary-reflect-form">
        <div className="reflect-prompts">
          {['What went well today?', 'What felt difficult?', 'What will I focus on next?'].map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="reflect-prompt-btn"
              onClick={() => setReflectionText((prev) => prev ? `${prev}\n${prompt} ` : `${prompt} `)}
            >
              {prompt}
            </button>
          ))}
        </div>

        <textarea
          className="sanctuary-reflect-textarea"
          rows={4}
          placeholder="Write your reflection here..."
          value={reflectionText}
          onChange={(e) => setReflectionText(e.target.value)}
          disabled={reflectionSaving}
          aria-label="Reflection note"
        />

        <div className="sanctuary-controls-row">
          <button
            type="submit"
            className="sanctuary-primary-btn"
            disabled={!reflectionText.trim() || reflectionSaving}
          >
            {reflectionSaving ? 'Saving...' : 'Save Reflection'}
          </button>
          {reflectionSaved && <span className="sanctuary-saved-note">Saved ✓</span>}
        </div>
      </form>

      {reflectionsLoading ? (
        <p className="sanctuary-loading-note">Loading past reflections...</p>
      ) : reflections.length > 0 ? (
        <div className="reflections-history">
          <h3 className="reflections-history-label">Past Reflections</h3>
          {reflections.slice(0, 5).map((r) => (
            <div key={r.id} className="reflection-history-item">
              <p className="reflection-history-text">{r.text}</p>
              <span className="reflection-history-date">
                {new Date(r.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );

  const renderCheckin = () => (
    <div className="sanctuary-section-panel">
      <h2 className="sanctuary-section-title">How are you feeling?</h2>
      <p className="sanctuary-section-sub">
        A quick check-in before or after studying. This helps Sathi understand your study state.
      </p>

      {latestCheckin?.mood && (
        <div className="checkin-latest">
          <span>Last check-in: </span>
          <strong>{MOOD_OPTIONS.find((m) => m.id === latestCheckin.mood)?.emoji} {MOOD_OPTIONS.find((m) => m.id === latestCheckin.mood)?.label || latestCheckin.mood}</strong>
        </div>
      )}

      <div className="checkin-mood-grid">
        {MOOD_OPTIONS.map((m) => (
          <button
            key={m.id}
            className={`checkin-mood-btn ${selectedMood === m.id ? 'selected' : ''}`}
            onClick={() => handleSaveCheckin(m.id)}
            disabled={checkinSaving}
            aria-label={m.label}
          >
            <span className="mood-emoji">{m.emoji}</span>
            <span className="mood-label">{m.label}</span>
          </button>
        ))}
      </div>

      {checkinSaved && (
        <p className="sanctuary-saved-note">Check-in saved ✓</p>
      )}
    </div>
  );

  // ─── Main render ─────────────────────────────────────────────────────────

  return (
    <div className="sanctuary-shell">
      {/* Top bar */}
      <div className="sanctuary-top-bar">
        <div className="sanctuary-breadcrumb">
          {activeSection !== 'home' && (
            <button
              className="sanctuary-back-btn"
              onClick={() => setActiveSection('home')}
              aria-label="Back to Sanctuary home"
            >
              ← Back
            </button>
          )}
          <span className="sanctuary-title-text">Sanctuary</span>
        </div>

        <div className="sanctuary-top-actions">
          <button
            className={`sanctuary-music-btn ${musicPlaying ? 'active' : ''}`}
            onClick={toggleMusic}
            aria-label={musicPlaying ? 'Stop ambient music' : 'Play ambient music'}
            title={musicPlaying ? 'Stop music' : 'Play ambient music'}
          >
            {musicPlaying ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" /><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
              </svg>
            )}
            <span>{musicPlaying ? 'Music on' : 'Ambient music'}</span>
          </button>

          <button className="exit-sanctuary-btn" onClick={handleReturn}>
            Return to Study →
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="sanctuary-content">
        {activeSection === 'home' && renderHome()}
        {activeSection === 'breathing' && renderBreathing()}
        {activeSection === 'focus' && renderFocus()}
        {activeSection === 'reflect' && renderReflect()}
        {activeSection === 'checkin' && renderCheckin()}
      </div>
    </div>
  );
}

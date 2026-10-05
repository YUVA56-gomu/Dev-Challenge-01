import React, { useState, useEffect } from 'react';
import { configureElevenLabs, fetchVoiceConfigStatus } from '../services/api';

export default function SettingsView({ health, theme = 'light', onToggleTheme }) {
  const isModelReady = health?.details?.model_available;
  const backendStatus = health?.status;

  // Profile
  const [studentName, setStudentName] = useState(() => localStorage.getItem('sathi-student-name') || '');
  const [nameEditing, setNameEditing] = useState(false);
  const [nameInput, setNameInput] = useState(studentName);
  const [nameSaved, setNameSaved] = useState(false);

  // ElevenLabs
  const [elevenLabsKey, setElevenLabsKey] = useState('');
  const [elevenLabsVoiceId, setElevenLabsVoiceId] = useState('21m00Tcm4TlvDq8ikWAM');
  const [voiceStatus, setVoiceStatus] = useState(null);
  const [voiceSaving, setVoiceSaving] = useState(false);
  const [voiceSaved, setVoiceSaved] = useState(false);
  const [voiceError, setVoiceError] = useState('');
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    fetchVoiceConfigStatus().then(setVoiceStatus).catch(() => {});
  }, []);

  const handleSaveName = (e) => {
    e.preventDefault();
    const n = nameInput.trim();
    localStorage.setItem('sathi-student-name', n);
    setStudentName(n);
    setNameEditing(false);
    setNameSaved(true);
    setTimeout(() => setNameSaved(false), 2000);
  };

  const handleSaveElevenLabs = async (e) => {
    e.preventDefault();
    const key = elevenLabsKey.trim();
    if (!key) { setVoiceError('Please enter your ElevenLabs API key.'); return; }
    setVoiceSaving(true);
    setVoiceError('');
    try {
      const result = await configureElevenLabs(key, elevenLabsVoiceId.trim() || undefined);
      setVoiceStatus({ elevenlabs_configured: result.elevenlabs_active, voice_id: result.voice_id, provider: 'ElevenLabsVoiceProvider' });
      setVoiceSaved(true);
      setElevenLabsKey(''); // clear for security
      setTimeout(() => setVoiceSaved(false), 3000);
    } catch (err) {
      setVoiceError('Could not save — is the backend running?');
    } finally {
      setVoiceSaving(false);
    }
  };

  const aiStatusColor = backendStatus === 'ok' && isModelReady ? 'success' : backendStatus === 'checking' ? '' : 'error';
  const aiStatusText = backendStatus === 'ok' && isModelReady
    ? 'Connected — running locally'
    : backendStatus === 'checking' ? 'Checking...' : 'Offline — start the backend server';

  // Popular ElevenLabs voices
  const VOICE_PRESETS = [
    { id: '21m00Tcm4TlvDq8ikWAM', name: 'Rachel (Default, calm)' },
    { id: 'AZnzlk1XvdvUeBnXmlld', name: 'Domi (confident)' },
    { id: 'EXAVITQu4vr4xnSDxMaL', name: 'Bella (warm)' },
    { id: 'VR6AewLTigWG4xSOukaG', name: 'Arnold (deep)' },
    { id: 'pNInz6obpgDQGcFmaJgB', name: 'Adam (professional)' },
  ];

  return (
    <div className="settings-screen">
      <header className="settings-header">
        <span className="settings-eyebrow">Preferences</span>
        <h1 className="settings-title">Settings</h1>
        <p className="settings-sub">Configure your Sathi experience.</p>
      </header>

      <div className="settings-sheet">

        {/* ── Appearance ───────────────────────────── */}
        <section className="settings-card-group">
          <h2 className="settings-group-title">Appearance</h2>
          <div className="settings-row-item">
            <div className="row-text-block">
              <span className="row-label">Theme</span>
              <span className="row-desc">Light or dark mode for long study sessions.</span>
            </div>
            <button className="settings-theme-toggle-btn" onClick={onToggleTheme}>
              {theme === 'dark' ? (
                <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg> Light Mode</>
              ) : (
                <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg> Dark Mode</>
              )}
            </button>
          </div>
        </section>

        {/* ── Profile ──────────────────────────────── */}
        <section className="settings-card-group">
          <h2 className="settings-group-title">Profile</h2>
          <div className="settings-row-item">
            <div className="row-text-block">
              <span className="row-label">Your Name</span>
              <span className="row-desc">Used in greetings. Stored locally only.</span>
            </div>
            {nameEditing ? (
              <form onSubmit={handleSaveName} className="settings-name-form">
                <input
                  type="text"
                  className="settings-name-input"
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  placeholder="Your name"
                  autoFocus
                  maxLength={40}
                />
                <button type="submit" className="settings-save-btn">Save</button>
                <button type="button" className="settings-cancel-btn" onClick={() => { setNameEditing(false); setNameInput(studentName); }}>Cancel</button>
              </form>
            ) : (
              <div className="settings-name-display">
                <span className="row-value-pill">{studentName || 'Not set'}</span>
                <button className="settings-edit-btn" onClick={() => { setNameEditing(true); setNameInput(studentName); }}>Edit</button>
                {nameSaved && <span className="settings-saved-note">Saved ✓</span>}
              </div>
            )}
          </div>
          <div className="row-divider" />
          <div className="settings-row-item">
            <div className="row-text-block">
              <span className="row-label">Examination Level</span>
              <span className="row-desc">CA Intermediate — New Scheme (2024–25)</span>
            </div>
            <span className="row-value-pill">CA Intermediate</span>
          </div>
        </section>

        {/* ── ElevenLabs Voice ─────────────────────── */}
        <section className="settings-card-group">
          <h2 className="settings-group-title">Voice Synthesis (ElevenLabs)</h2>

          {/* Current status */}
          <div className="settings-row-item">
            <div className="row-text-block">
              <span className="row-label">Voice Status</span>
              <span className="row-desc">
                {voiceStatus?.elevenlabs_configured
                  ? `ElevenLabs active · Voice: ${voiceStatus.voice_id}`
                  : 'Using browser Web Speech API (free fallback). Add your ElevenLabs key for premium voice.'}
              </span>
            </div>
            <span className={`row-value-pill ${voiceStatus?.elevenlabs_configured ? 'success' : ''}`}>
              {voiceStatus?.elevenlabs_configured ? 'ElevenLabs Active' : voiceStatus === null ? 'Checking...' : 'Browser Fallback'}
            </span>
          </div>

          <div className="row-divider" />

          {/* Key input */}
          <div className="settings-elevenlabs-block">
            <p className="settings-elevenlabs-help">
              Get your free API key at <strong>elevenlabs.io</strong> → Profile → API Keys. The key is saved to your backend <code>.env</code> file and persists across restarts.
            </p>

            <form onSubmit={handleSaveElevenLabs} className="settings-elevenlabs-form">
              <div className="settings-input-row">
                <label className="settings-field-label">API Key</label>
                <div className="settings-password-wrapper">
                  <input
                    type={showKey ? 'text' : 'password'}
                    className="settings-api-input"
                    value={elevenLabsKey}
                    onChange={(e) => setElevenLabsKey(e.target.value)}
                    placeholder="sk_..."
                    autoComplete="off"
                    spellCheck={false}
                    aria-label="ElevenLabs API key"
                  />
                  <button
                    type="button"
                    className="settings-show-key-btn"
                    onClick={() => setShowKey((v) => !v)}
                    aria-label={showKey ? 'Hide key' : 'Show key'}
                  >
                    {showKey ? (
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                    ) : (
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    )}
                  </button>
                </div>
              </div>

              <div className="settings-input-row">
                <label className="settings-field-label">Voice</label>
                <select
                  className="settings-voice-select"
                  value={elevenLabsVoiceId}
                  onChange={(e) => setElevenLabsVoiceId(e.target.value)}
                  aria-label="ElevenLabs voice"
                >
                  {VOICE_PRESETS.map((v) => (
                    <option key={v.id} value={v.id}>{v.name}</option>
                  ))}
                  <option value="custom">Custom voice ID...</option>
                </select>
                {elevenLabsVoiceId === 'custom' && (
                  <input
                    type="text"
                    className="settings-api-input"
                    placeholder="Paste custom voice ID"
                    onChange={(e) => setElevenLabsVoiceId(e.target.value)}
                    style={{ marginTop: '6px' }}
                  />
                )}
              </div>

              {voiceError && <p className="settings-error-note">{voiceError}</p>}

              <div className="settings-form-actions">
                <button
                  type="submit"
                  className="settings-save-btn"
                  disabled={voiceSaving || !elevenLabsKey.trim()}
                >
                  {voiceSaving ? 'Saving...' : 'Save & Activate'}
                </button>
                {voiceSaved && <span className="settings-saved-note">Activated ✓ — restart not required</span>}
              </div>
            </form>
          </div>
        </section>

        {/* ── AI System ────────────────────────────── */}
        <section className="settings-card-group">
          <h2 className="settings-group-title">AI System</h2>
          <div className="settings-row-item">
            <div className="row-text-block">
              <span className="row-label">AI Model</span>
              <span className="row-desc">Local Gemma via Ollama — all inference runs on your device.</span>
            </div>
            <span className="row-value-pill">Gemma 2</span>
          </div>
          <div className="row-divider" />
          <div className="settings-row-item">
            <div className="row-text-block">
              <span className="row-label">Backend Status</span>
              <span className="row-desc">FastAPI server + Ollama connection.</span>
            </div>
            <span className={`row-value-pill ${aiStatusColor}`}>{aiStatusText}</span>
          </div>
        </section>

        {/* ── Privacy ──────────────────────────────── */}
        <section className="settings-card-group">
          <h2 className="settings-group-title">Privacy</h2>
          <div className="settings-row-item">
            <div className="row-text-block">
              <span className="row-label">Data Storage</span>
              <span className="row-desc">All study data, attempts, and reflections are stored in SQLite on your device. Nothing leaves your machine except ElevenLabs TTS requests (text only, no study content).</span>
            </div>
            <span className="row-value-pill success">Local only</span>
          </div>
          <div className="row-divider" />
          <div className="settings-row-item">
            <div className="row-text-block">
              <span className="row-label">Reflections</span>
              <span className="row-desc">Private notes in Sanctuary are never sent to any external service.</span>
            </div>
            <span className="row-value-pill success">Private</span>
          </div>
        </section>

      </div>
    </div>
  );
}

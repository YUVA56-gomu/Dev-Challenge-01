import React, { useState, useEffect, useRef } from 'react';
import { reframeThought } from '../services/api';

export default function SanctuaryView() {
  // --- Breathing State ---
  const [breathingActive, setBreathingActive] = useState(false);
  const [phase, setPhase] = useState('Inhale'); // Inhale, Hold-In, Exhale, Hold-Out
  const [secondsLeft, setSecondsLeft] = useState(4);
  const [completedCycles, setCompletedCycles] = useState(0);

  // --- Thought Reframing State ---
  const [thoughtInput, setThoughtInput] = useState('');
  const [reframedOutput, setReframedOutput] = useState('');
  const [isReframing, setIsReframing] = useState(false);

  // --- Perspective Card State ---
  const [expandedCard, setExpandedCard] = useState(0);

  // Breathing Box Timer: 4-4-4-4 cycle
  useEffect(() => {
    let timer = null;
    if (breathingActive) {
      timer = setInterval(() => {
        setSecondsLeft((prev) => {
          if (prev > 1) return prev - 1;

          // Transition phase
          setPhase((currentPhase) => {
            if (currentPhase === 'Inhale') return 'Hold-In';
            if (currentPhase === 'Hold-In') return 'Exhale';
            if (currentPhase === 'Hold-Exhale') return 'Hold-Out';
            if (currentPhase === 'Exhale') return 'Hold-Out';
            if (currentPhase === 'Hold-Out') {
              setCompletedCycles((c) => c + 1);
              return 'Inhale';
            }
            return 'Inhale';
          });
          return 4;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [breathingActive]);

  const resetBreathing = () => {
    setBreathingActive(false);
    setPhase('Inhale');
    setSecondsLeft(4);
  };

  const handleReframe = async (e) => {
    e.preventDefault();
    if (!thoughtInput.trim() || isReframing) return;

    setIsReframing(true);
    setReframedOutput('');

    try {
      const data = await reframeThought(thoughtInput.trim());
      setReframedOutput(data.reframed);
    } catch (err) {
      setReframedOutput('⚠️ Could not connect to Gemma for reframing. Please check local server.');
    } finally {
      setIsReframing(false);
    }
  };

  const perspectives = [
    {
      title: 'Identity Beyond an ICAI Roll Number',
      icon: '🌿',
      summary: 'You are a multi-dimensional human being, not defined by a pass list.',
      content:
        'The intense culture of CA preparation can make it feel like your entire worth hangs on a single marksheet. Remember: clearing or not clearing does not diminish your kindness, intellect, resilience, or future potential. The exam is something you are doing, not who you are.',
    },
    {
      title: 'The Reality of Pass Percentages',
      icon: '📊',
      summary: 'Low pass rates measure institutional quotas, not individual intelligence.',
      content:
        'A 10%–15% pass rate simply means that ICAI controls supply and demand in the profession. Missing a mark or needing an extra attempt is extraordinarily common among even top partners and CFOs. Persistence, not perfection, is the defining trait of successful professionals.',
    },
    {
      title: 'Rest is Part of the Syllabus',
      icon: '🌙',
      summary: 'A chronically sleep-deprived brain cannot retain Section 17(5) or AS 10.',
      content:
        'Studying 14 hours a day on 4 hours of sleep produces diminishing cognitive returns. Memory consolidation happens during deep sleep. Giving yourself permission to sleep 7–8 hours and take walks is a tactical study strategy, not laziness.',
    },
    {
      title: 'Attempts are Iterations, Not Failures',
      icon: '🧭',
      summary: 'Each preparation cycle builds compound knowledge.',
      content:
        'In software engineering, we debug and iterate. In CA exams, an attempt that did not clear provides diagnostic data on what needs sharpening. Give yourself the grace you would give your best friend.',
    },
  ];

  return (
    <div className="view-container sanctuary-view">
      <div className="view-header">
        <div>
          <h2>Sanctuary & Life Beyond Exams</h2>
          <p className="view-subtitle">
            Take a deep breath. Ground yourself. Examination performance is only one chapter of your story.
          </p>
        </div>
      </div>

      {/* Grid: Left = Breathing Exercise, Right = Negative Thought Reframing */}
      <div className="sanctuary-grid">
        {/* Section 1: Box Breathing Visualizer */}
        <section className="sanctuary-card breathing-card">
          <div className="card-badge">Pranayama / Box Breathing (4-4-4-4)</div>
          <h3>Regulate Your Nervous System</h3>
          <p className="sanctuary-desc">
            Use box breathing before starting an intense revision block or when exam anxiety spikes.
          </p>

          <div className="breathing-stage">
            <div className={`breathing-circle-wrapper ${breathingActive ? phase.toLowerCase() : 'idle'}`}>
              <div className="breathing-circle">
                <div className="breathing-phase-label">{breathingActive ? phase : 'Ready'}</div>
                <div className="breathing-timer">{breathingActive ? `${secondsLeft}s` : '4s'}</div>
              </div>
            </div>
            <div className="breathing-instruction">
              {phase === 'Inhale' && 'Inhale slowly and deeply through your nose...'}
              {phase === 'Hold-In' && 'Gently hold your breath with relaxed shoulders...'}
              {phase === 'Exhale' && 'Exhale smoothly and completely through your mouth...'}
              {phase === 'Hold-Out' && 'Rest in emptiness before the next inhale...'}
            </div>
          </div>

          <div className="breathing-controls">
            <button
              className={`primary-button ${breathingActive ? 'pause-btn' : 'start-btn'}`}
              onClick={() => setBreathingActive(!breathingActive)}
            >
              {breathingActive ? '⏸️ Pause Breathing' : '▶️ Begin Breathing Exercise'}
            </button>
            <button className="secondary-button" onClick={resetBreathing}>
              ↺ Reset
            </button>
          </div>

          {completedCycles > 0 && (
            <div className="cycle-badge">
              ✨ Completed {completedCycles} full breathing cycle{completedCycles > 1 ? 's' : ''}
            </div>
          )}
        </section>

        {/* Section 2: Negative Thought Reframing (Gemma AI) */}
        <section className="sanctuary-card reframing-card">
          <div className="card-badge">Powered by Gemma 2 AI</div>
          <h3>Negative Thought Reframer</h3>
          <p className="sanctuary-desc">
            Caught in an anxiety spiral? Share the thought that is troubling you, and Sathi will help
            you reframe it with compassionate perspective.
          </p>

          <form className="reframe-form" onSubmit={handleReframe}>
            <textarea
              className="reframe-input"
              rows={3}
              placeholder="e.g. 'I am so far behind everyone else, I feel like I am definitely going to fail this attempt...'"
              value={thoughtInput}
              onChange={(e) => setThoughtInput(e.target.value)}
              disabled={isReframing}
            />
            <div className="reframe-btn-row">
              <button
                type="submit"
                className="primary-button reframe-btn"
                disabled={isReframing || !thoughtInput.trim()}
              >
                {isReframing ? 'Reframing with Gemma...' : '✨ Reframe Thought'}
              </button>
            </div>
          </form>

          {isReframing && (
            <div className="loading-card">
              <div className="pulsing-spinner"></div>
              <span>Gemma is generating a supportive perspective...</span>
            </div>
          )}

          {reframedOutput && (
            <div className="reframed-result-box">
              <div className="result-header">
                <span className="result-icon">🌱</span>
                <strong>Reframed Perspective:</strong>
              </div>
              <div className="result-content">{reframedOutput}</div>
            </div>
          )}

          <div className="non-clinical-notice">
            ℹ️ Sathi provides supportive reflection and grounding for study-related stress. Not a substitute for professional therapy or medical care.
          </div>
        </section>
      </div>

      {/* Section 3: Beyond the Examination Perspectives */}
      <section className="perspectives-section">
        <h3>Anchors of Perspective</h3>
        <p className="section-sub">Click a perspective to reflect on what truly matters.</p>

        <div className="perspectives-grid">
          {perspectives.map((p, idx) => (
            <div
              key={idx}
              className={`perspective-card ${expandedCard === idx ? 'expanded' : ''}`}
              onClick={() => setExpandedCard(expandedCard === idx ? -1 : idx)}
            >
              <div className="card-top">
                <span className="p-icon">{p.icon}</span>
                <h4>{p.title}</h4>
              </div>
              <p className="p-summary">{p.summary}</p>
              {expandedCard === idx && <p className="p-detail">{p.content}</p>}
              <span className="expand-indicator">
                {expandedCard === idx ? 'Show less ▲' : 'Read reflection ▼'}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

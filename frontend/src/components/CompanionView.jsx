import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChatMessageStream } from '../services/api';
import { voiceService } from '../services/voice';
import { soundService } from '../services/soundService';
import VoiceOverlayModal from './VoiceOverlayModal';

/**
 * CompanionView Component - The Living AI CA Companion
 * 
 * Calm, human, encouraging, unified voice & text interaction.
 * Chat-focused main view with an image-style Voice Companion Overlay popup.
 */
export default function CompanionView({ initialContext = null, onClearContext = () => {} }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [orbState, setOrbState] = useState('idle'); // 'idle' | 'listening' | 'thinking' | 'speaking' | 'error'
  const [orbHint, setOrbHint] = useState('');
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [isVoiceOverlayOpen, setIsVoiceOverlayOpen] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [latestSpokenText, setLatestSpokenText] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [savedNoteId, setSavedNoteId] = useState(null);
  const [fallbackNotice, setFallbackNotice] = useState(null);
  const [activeStudyContext, setActiveStudyContext] = useState(initialContext);
  const [expandedCitationId, setExpandedCitationId] = useState(null);

  // Playback state: tracks active message, speaking status, and paused state
  const [playback, setPlayback] = useState({
    messageId: null,
    isSpeaking: false,
    isPaused: false,
  });

  const messagesEndRef = useRef(null);
  const recognizerRef = useRef(null);
  const isListeningRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, orbState, playback, expandedCitationId]);

  // Synchronize when initialContext changes from "Ask Sathi" or Practice View
  useEffect(() => {
    if (initialContext) {
      setActiveStudyContext(initialContext);
      if (messages.length === 0) {
        if (initialContext.attempt_context) {
          const att = initialContext.attempt_context;
          const targetName = initialContext.topic || initialContext.chapter || 'this practice question';
          setMessages([
            {
              id: 'attempt_intro',
              role: 'assistant',
              content: `I reviewed your practice attempt on **${targetName}** (Score: **${att.score} / ${att.max_score} Marks**).\n\n${
                att.mistakes && att.mistakes.length > 0
                  ? `Identified adjustments to examine: *${att.mistakes.join('; ')}*.\n\n`
                  : ''
              }What would you like to explore — why marks were lost, how to frame the statutory answer for full marks, or an exam memory tip?`,
              spoken_reply: `I reviewed your practice attempt on ${targetName} where you scored ${att.score} out of ${att.max_score}. What would you like to explore — why marks were lost, the ideal approach, or an exam tip?`,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              is_rag_grounded: false,
            },
          ]);
        } else {
          const targetName = initialContext.topic || initialContext.chapter || 'this topic';
          setMessages([
            {
              id: 'context_intro',
              role: 'assistant',
              content: `Let's study **${targetName}** together.\n\nWhat would you like to explore first — the core conceptual explanation, the relevant statutory section, an illustrative exam example, or a quick practice question?`,
              spoken_reply: `Let's study ${targetName} together. What would you like to explore first — the concept, the relevant section, an exam example, or a practice question?`,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              is_rag_grounded: false,
            },
          ]);
        }
      }
    }
  }, [initialContext]);

  // Clean up voice/speech on unmount
  useEffect(() => {
    return () => {
      voiceService.stop();
      soundService.stopMusic();
      if (recognizerRef.current) {
        recognizerRef.current.stop();
      }
    };
  }, []);

  /**
   * Play speech for a specific message using concise spoken_reply when available
   */
  const playMessageVoice = useCallback((messageId, textToSpeak) => {
    if (playback.messageId === messageId) {
      if (playback.isSpeaking && !playback.isPaused) {
        voiceService.pause();
        setPlayback((prev) => ({ ...prev, isPaused: true }));
        return;
      } else if (playback.isPaused) {
        voiceService.resume();
        setPlayback((prev) => ({ ...prev, isPaused: false }));
        return;
      }
    }

    voiceService.stop();
    soundService.playSound('response');
    setLatestSpokenText(textToSpeak);
    setPlayback({ messageId, isSpeaking: true, isPaused: false });
    setOrbState('speaking');
    setOrbHint('Sathi is speaking...');

    voiceService.speak(
      textToSpeak,
      () => {
        setPlayback({ messageId, isSpeaking: true, isPaused: false });
        setOrbState('speaking');
        setOrbHint('Sathi is speaking...');
      },
      () => {
        setPlayback({ messageId: null, isSpeaking: false, isPaused: false });
        setOrbState('idle');
        setOrbHint('');
      },
      (fallbackMsg) => {
        setFallbackNotice(fallbackMsg);
        setTimeout(() => setFallbackNotice(null), 5000);
      }
    );
  }, [playback]);

  const pausePlayback = useCallback(() => {
    voiceService.pause();
    setPlayback((prev) => ({ ...prev, isPaused: true }));
  }, []);

  const resumePlayback = useCallback(() => {
    voiceService.resume();
    setPlayback((prev) => ({ ...prev, isPaused: false }));
  }, []);

  const replayMessageVoice = useCallback((messageId, textToSpeak) => {
    voiceService.stop();
    playMessageVoice(messageId, textToSpeak);
  }, [playMessageVoice]);

  /**
   * Open the Real Voice Companion Overlay Modal
   */
  const openVoiceOverlay = useCallback(() => {
    soundService.playSound('wake');
    soundService.playMusic('companion_atmosphere', 0.15, true);
    setIsVoiceOverlayOpen(true);
    startListening();
  }, []);

  /**
   * Multi-turn send handler with RAG syllabus context
   */
  const handleSend = useCallback(
    async (textToSend) => {
      const promptText = (typeof textToSend === 'string' ? textToSend : input).trim();
      if (!promptText || isLoading) return;

      // Stop any current voice activity
      voiceService.stop();
      setPlayback({ messageId: null, isSpeaking: false, isPaused: false });

      if (isListeningRef.current && recognizerRef.current) {
        recognizerRef.current.stop();
        isListeningRef.current = false;
      }

      const userMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: promptText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      const historyPayload = messages
        .filter((m) => !m.isError && m.id !== 'context_intro')
        .map((m) => ({ role: m.role, content: m.content }));

      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setIsLoading(true);
      setOrbState('thinking');
      setOrbHint('Formulating a response...');

      try {
        let currentMessageId = (Date.now() + 1).toString();
        let assistantMessage = {
          id: currentMessageId,
          role: 'assistant',
          content: '',
          spoken_reply: '',
          is_rag_grounded: false,
          citations: [],
          routing: null,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isStreaming: true
        };
        
        setMessages((prev) => [...prev, assistantMessage]);

        await sendChatMessageStream(
          promptText, 
          historyPayload, 
          activeStudyContext,
          (chunkText) => {
            setIsLoading(false);
            setOrbState('thinking');
            setOrbHint('Sathi is typing...');
            assistantMessage.content += chunkText;
            setMessages(prev => prev.map(m => m.id === currentMessageId ? { ...assistantMessage } : m));
          },
          (metadata) => {
            assistantMessage.is_rag_grounded = metadata.is_rag_grounded;
            assistantMessage.citations = metadata.citations || [];
            assistantMessage.routing = metadata.routing || null;
            setMessages(prev => prev.map(m => m.id === currentMessageId ? { ...assistantMessage } : m));
          },
          (spoken_reply) => {
            assistantMessage.spoken_reply = spoken_reply || assistantMessage.content;
            assistantMessage.isStreaming = false;
            setMessages(prev => prev.map(m => m.id === currentMessageId ? { ...assistantMessage } : m));
            setIsLoading(false);
            if (autoSpeak) {
              playMessageVoice(assistantMessage.id, assistantMessage.spoken_reply);
            } else {
              setOrbState('idle');
              setOrbHint('');
            }
          },
          (error) => {
            throw error;
          }
        );
      } catch (err) {
        setMessages((prev) => prev.filter(m => m.id !== prev[prev.length - 1].id));
        const errorMessage = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `I'm having trouble connecting to my local memory right now. Please ensure your local assistant server is running.`,
          isError: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, errorMessage]);
        setOrbState('error');
        setOrbHint('Assistant offline');
        setIsLoading(false);
        setTimeout(() => {
          setOrbState('idle');
          setOrbHint('');
        }, 4000);
      }
    },
    [input, isLoading, messages, autoSpeak, playMessageVoice, activeStudyContext]
  );

  /**
   * Helper to initialize and start speech recognizer
   */
  const startListening = () => {
    soundService.playSound('listening');
    const recognizer = voiceService.createSpeechRecognizer(
      (transcript, isFinal) => {
        setInput(transcript);
        setLiveTranscript(transcript);
        if (isFinal && transcript.trim() && isVoiceOverlayOpen) {
          handleSend(transcript);
        }
      },
      (errorMessage) => {
        console.warn('Speech recognition notice:', errorMessage);
        isListeningRef.current = false;
        setOrbState('error');
        setOrbHint(errorMessage);
        setTimeout(() => {
          setOrbState('idle');
          setOrbHint('');
        }, 4000);
      },
      () => {
        isListeningRef.current = false;
        if (orbState === 'listening') {
          setOrbState('idle');
          setOrbHint('');
        }
      }
    );

    if (!recognizer.isSupported) {
      setOrbState('error');
      setOrbHint('Speech recognition unsupported in this browser.');
      setTimeout(() => {
        setOrbState('idle');
        setOrbHint('');
      }, 4000);
      return;
    }

    recognizerRef.current = recognizer;
    isListeningRef.current = true;
    setOrbState('listening');
    setOrbHint('Listening to you... Speak clearly');
    recognizer.start();
  };

  const toggleListening = () => {
    if (playback.isSpeaking) {
      voiceService.stop();
      setPlayback({ messageId: null, isSpeaking: false, isPaused: false });
      startListening();
      return;
    }

    if (isListeningRef.current) {
      if (recognizerRef.current) {
        recognizerRef.current.stop();
      }
      isListeningRef.current = false;
      setOrbState('idle');
      setOrbHint('');
      return;
    }

    startListening();
  };

  const copyToClipboard = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const saveToNotes = (id, text) => {
    try {
      const existing = JSON.parse(localStorage.getItem('sathi_saved_notes') || '[]');
      const newNote = {
        id: Date.now().toString(),
        subject: activeStudyContext?.paper || 'CA Revision',
        text: text.slice(0, 300) + (text.length > 300 ? '...' : ''),
        savedAt: 'Today',
      };
      localStorage.setItem('sathi_saved_notes', JSON.stringify([newNote, ...existing]));
      setSavedNoteId(id);
      setTimeout(() => setSavedNoteId(null), 2000);
    } catch (e) {
      console.error(e);
    }
  };

  const toggleCitation = (messageId) => {
    setExpandedCitationId((prev) => (prev === messageId ? null : messageId));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const starterPrompts = [
    { label: 'Explain Section 17(5) blocked credits', prompt: 'What are the blocked credits under Section 17(5) of the CGST Act? Explain with simple examples.' },
    { label: 'First auditor appointment rules', prompt: 'Who appoints the first auditor in a non-government company under Section 139, and what is the time limit?' },
    { label: 'Depreciation under AS 10', prompt: 'Explain component depreciation and disposal of asset before useful life under AS 10.' },
    { label: 'SA 200 audit limitations', prompt: 'What are the inherent limitations of an audit according to Standard on Auditing 200?' },
    { label: 'What should I study today?', prompt: 'What should I study today based on my current CA preparation progress and weak areas?' },
    { label: "Quiz me on Section 141 disqualifications", prompt: 'Can you quiz me on auditor disqualifications under Section 141 with a realistic practical question?' },
  ];

  return (
    <div className="companion-screen">
      {/* Top Header Controls */}
      <div className="companion-top-bar">
        <div className="companion-header-identity">
          <span className="companion-identity-badge">Sathi · Personal AI Companion</span>
          {messages.length > 0 && (
            <span className={`companion-status-tag ${orbState}`}>
              {orbState === 'listening' && '🔵 Listening...'}
              {orbState === 'thinking' && '🧠 Processing...'}
              {orbState === 'speaking' && '🔊 Speaking...'}
              {orbState === 'error' && '⚠️ Voice Notice'}
              {orbState === 'idle' && '💬 Active Chat'}
            </span>
          )}
        </div>
        
        <div className="companion-audio-controls">
          {/* Prominent Voice Mode Trigger Button */}
          <button
            className="voice-mode-launcher-btn"
            onClick={openVoiceOverlay}
            title="Start Voice Conversation"
            aria-label="Open voice mode"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
            <span>Voice Mode</span>
          </button>

          <label className="calm-toggle-label" title="Read Sathi replies out loud">
            <input
              type="checkbox"
              checked={autoSpeak}
              onChange={(e) => setAutoSpeak(e.target.checked)}
              className="calm-checkbox"
            />
            <span className="calm-toggle-text">🔊 Auto-Speak</span>
          </label>

          {messages.length > 0 && (
            <button
              className="calm-text-btn"
              onClick={() => {
                if (window.confirm('Start a fresh conversation?')) {
                  voiceService.stop();
                  setPlayback({ messageId: null, isSpeaking: false, isPaused: false });
                  setMessages([]);
                  setOrbState('idle');
                  setOrbHint('');
                }
              }}
            >
              New Conversation
            </button>
          )}
        </div>
      </div>

      {/* Active Study Context Banner */}
      {activeStudyContext && (
        <div className="active-context-banner">
          <div className="context-banner-info">
            <span className="context-icon">
              {activeStudyContext.attempt_context ? '✍️' : '📖'}
            </span>
            <span className="context-label">
              {activeStudyContext.attempt_context
                ? `PRACTICE ATTEMPT REVIEW (${activeStudyContext.attempt_context.score}/${activeStudyContext.attempt_context.max_score} M):`
                : 'FOCUSED STUDY:'}
            </span>
            <span className="context-text">
              {activeStudyContext.paper} ❯ {activeStudyContext.chapter}
              {activeStudyContext.topic && ` ❯ ${activeStudyContext.topic}`}
              {activeStudyContext.statutory_section && ` (${activeStudyContext.statutory_section})`}
            </span>
          </div>
          <button
            className="context-clear-btn"
            onClick={() => {
              setActiveStudyContext(null);
              onClearContext();
            }}
            title="Clear topic context"
          >
            ✕ Clear Context
          </button>
        </div>
      )}

      {/* Device Voice Notice when offline or ElevenLabs unavailable */}
      {fallbackNotice && (
        <div className="device-voice-notice" role="alert">
          <span>🔊</span>
          <span>{fallbackNotice}</span>
        </div>
      )}

      {/* Main Conversational Area */}
      <div className="companion-scroll-stage">
        {messages.length === 0 ? (
          /* Premium Chat-Focused Welcome Stage */
          <div className="companion-welcome-stage">
            <div className="welcome-greeting-block">
              <h2 className="welcome-salutation">Hello. I'm Sathi.</h2>
              <p className="welcome-lead">Your CA AI companion. Ask me anything about your syllabus, sections, or standards.</p>
            </div>

            {/* Voice Conversation Launch Banner */}
            <div className="voice-banner-hero" onClick={openVoiceOverlay} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && openVoiceOverlay()} aria-label="Launch voice mode">
              <div className="voice-hero-icon" aria-hidden="true">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="23"/>
                  <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
              </div>
              <div className="voice-hero-text">
                <h3>Start Voice Conversation</h3>
                <p>Real-time speech with your CA companion — ElevenLabs or browser voice</p>
              </div>
              <button className="voice-hero-action-btn" tabIndex={-1} aria-hidden="true">Launch →</button>
            </div>

            {/* Compact Starter Actions */}
            <div className="compact-starters-zone">
              <span className="starters-subtle-title">CHOOSE A STUDY TOPIC</span>
              <div className="starters-pill-flow">
                {starterPrompts.map((s, idx) => (
                  <button
                    key={idx}
                    className="compact-starter-pill"
                    onClick={() => handleSend(s.prompt)}
                    disabled={isLoading}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Active Conversational Flow */
          <div className="active-messages-stream">
            {messages.map((msg) => {
              const isCurrentPlaying = playback.messageId === msg.id && playback.isSpeaking && !playback.isPaused;
              const isCurrentPaused = playback.messageId === msg.id && playback.isPaused;
              const hasCitations = msg.citations && msg.citations.length > 0;
              const isExpanded = expandedCitationId === msg.id;

              return (
                <div key={msg.id} className={`chat-message-row ${msg.role}`}>
                  <div className="chat-bubble">
                    {msg.role === 'assistant' && (
                      <div className="assistant-header-meta">
                        <div className="assistant-tag-group">
                          <span className="sathi-badge-tag">Sathi</span>
                          {msg.is_rag_grounded && (
                            <span className="rag-grounded-pill">🛡️ RAG Grounded</span>
                          )}
                        </div>
                        <span className="msg-timestamp">{msg.timestamp}</span>
                      </div>
                    )}

                    <div className="chat-content-text markdown-body">
                      {msg.role === 'assistant' ? (
                        <>
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                          {msg.isStreaming && <span className="streaming-cursor"></span>}
                        </>
                      ) : (
                        msg.content
                      )}
                    </div>

                    {/* Verified Source Citations */}
                    {hasCitations && (
                      <div className="verified-source-container">
                        <button
                          type="button"
                          className={`source-verified-button ${isExpanded ? 'open' : ''}`}
                          onClick={() => toggleCitation(msg.id)}
                          title="Click to view verified study material provenance"
                        >
                          <span className="source-verified-badge">🛡️ Source Verified</span>
                          <span className="source-highlight-text">
                            {msg.citations[0].document_name} · {msg.citations[0].statutory_reference} (P. {msg.citations[0].page_number})
                          </span>
                          <span className="source-chevron">{isExpanded ? '▲' : '▼'}</span>
                        </button>

                        {isExpanded && (
                          <div className="citations-dropdown-card">
                            <div className="citations-list-title">OFFICIAL STUDY MATERIAL CITATIONS</div>
                            {msg.citations.map((c, idx) => (
                              <div key={idx} className="citation-item-card">
                                <div className="citation-header-row">
                                  <span className="citation-doc-name">📖 {c.document_name}</span>
                                  <span className="citation-page-badge">Page {c.page_number}</span>
                                </div>
                                <div className="citation-meta-tags">
                                  <span className="c-tag paper">{c.paper}</span>
                                  <span className="c-tag chapter">{c.chapter}</span>
                                  <span className="c-tag section">{c.statutory_reference}</span>
                                </div>
                                <div className="citation-snippet-text">{c.snippet}</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {msg.role === 'assistant' && !msg.isError && (
                      <div className="assistant-footer-meta">
                        <div className="subtle-source-hint">
                          <span>📚 ICAI Study Guidance</span>
                        </div>

                        <div className="chat-action-pills">
                          {isCurrentPlaying ? (
                            <button
                              className="msg-action-btn active"
                              onClick={pausePlayback}
                              title="Pause voice"
                            >
                              ⏸ Pause
                            </button>
                          ) : isCurrentPaused ? (
                            <button
                              className="msg-action-btn active"
                              onClick={resumePlayback}
                              title="Resume voice"
                            >
                              ▶ Resume
                            </button>
                          ) : (
                            <button
                              className="msg-action-btn"
                              onClick={() => playMessageVoice(msg.id, msg.spoken_reply || msg.content)}
                              title="Listen to Sathi"
                            >
                              🔊 Listen
                            </button>
                          )}

                          <button
                            className="msg-action-btn"
                            onClick={() => replayMessageVoice(msg.id, msg.spoken_reply || msg.content)}
                            title="Replay from beginning"
                          >
                            🔁 Replay
                          </button>

                          <button
                            className="msg-action-btn"
                            onClick={() => copyToClipboard(msg.id, msg.content)}
                            title="Copy response"
                          >
                            {copiedId === msg.id ? '✓ Copied' : '📋 Copy'}
                          </button>

                          <button
                            className="msg-action-btn"
                            onClick={() => saveToNotes(msg.id, msg.content)}
                            title="Save note"
                          >
                            {savedNoteId === msg.id ? '✓ Saved' : '📝 Save'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="thinking-row">
                <div className="pulsing-spinner-soft"></div>
                <span className="thinking-hint">Sathi is thinking...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Large Conversational Input Bar at Bottom */}
      <div className="companion-input-container">
        <form
          className="companion-input-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <button
            type="button"
            className="input-mic-btn"
            onClick={openVoiceOverlay}
            title="Open Voice Mode"
            aria-label="Open voice conversation"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
          </button>

          <textarea
            className="companion-textarea"
            rows={1}
            placeholder={
              activeStudyContext
                ? `Ask Sathi about ${activeStudyContext.topic || activeStudyContext.chapter}...`
                : "Ask Sathi about sections, accounting standards, or your CA studies..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />

          <button
            type="submit"
            className="input-send-circle"
            disabled={isLoading || !input.trim()}
            title="Send"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>
        </form>
      </div>

      {/* Real Voice Companion Overlay Modal */}
      <VoiceOverlayModal
        isOpen={isVoiceOverlayOpen}
        onClose={() => {
          setIsVoiceOverlayOpen(false);
          if (isListeningRef.current && recognizerRef.current) {
            recognizerRef.current.stop();
          }
          setOrbState('idle');
        }}
        state={orbState}
        statusHint={orbHint}
        transcript={liveTranscript}
        latestSpokenText={latestSpokenText}
        onToggleListening={toggleListening}
        autoSpeak={autoSpeak}
        onToggleAutoSpeak={setAutoSpeak}
        activeContext={activeStudyContext}
      />
    </div>
  );
}

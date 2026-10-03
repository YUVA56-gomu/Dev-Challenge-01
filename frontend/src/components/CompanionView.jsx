import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../services/api';

export default function CompanionView({ health }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (textToSend) => {
    const promptText = (typeof textToSend === 'string' ? textToSend : input).trim();
    if (!promptText || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: promptText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    // Format previous history for backend
    const historyPayload = messages
      .filter((m) => !m.isError)
      .map((m) => ({ role: m.role, content: m.content }));

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const data = await sendChatMessage(promptText, historyPayload);
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.reply,
        model: data.model,
        provider: data.provider,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ Error: ${err.message}\n\nPlease ensure your local backend and Ollama are running.`,
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    if (messages.length > 0 && window.confirm('Clear conversation history?')) {
      setMessages([]);
    }
  };

  const suggestions = [
    'Explain depreciation like I am a CA Foundation student.',
    'What are the conditions for claiming Input Tax Credit (ITC) under Section 16 of CGST Act?',
    'What are the inherent limitations of an audit according to SA 200?',
    'How do I calculate Break-Even Point and Margin of Safety in Costing?',
  ];

  return (
    <div className="view-container companion-view">
      <div className="view-header">
        <div>
          <h2>AI CA Companion</h2>
          <p className="view-subtitle">
            Study mentor powered by local Google Gemma 2 (2B) running on your RTX 3050 GPU.
          </p>
        </div>
        {messages.length > 0 && (
          <button className="secondary-button" onClick={clearChat} title="Clear conversation">
            🗑️ Clear Chat
          </button>
        )}
      </div>

      <div className="chat-messages-card">
        {messages.length === 0 ? (
          <div className="welcome-card">
            <div className="welcome-icon">🎓</div>
            <h3>Namaste! I am Sathi, your personal CA study companion.</h3>
            <p>
              I am here to guide you through tough syllabus concepts, explain accounting standards,
              walk through tax calculations, and keep your spirits up through the long study hours.
            </p>

            <div className="suggestions-box">
              <span className="suggestions-heading">Try asking a CA question:</span>
              <div className="suggestions-grid">
                {suggestions.map((s, idx) => (
                  <button
                    key={idx}
                    className="suggestion-card"
                    onClick={() => handleSend(s)}
                    disabled={isLoading}
                  >
                    "{s}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="messages-stream">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👩‍🎓' : '📚'}
                </div>
                <div className="message-bubble">
                  <div className="message-meta">
                    <span className="sender-name">
                      {msg.role === 'user' ? 'Student' : 'Sathi Mentor'}
                    </span>
                    {msg.model && <span className="model-badge">{msg.model}</span>}
                    <span className="message-time">{msg.timestamp}</span>
                  </div>
                  <div className="message-body">{msg.content}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {isLoading && (
          <div className="loading-card">
            <div className="pulsing-spinner"></div>
            <span>Gemma 2 is formulating an explanation...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-bar">
        <form
          className="chat-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <textarea
            className="input-textarea"
            rows={1}
            placeholder="Ask a question on Accounting, Law, Tax, Costing, or Auditing..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="primary-button send-btn"
            disabled={isLoading || !input.trim()}
          >
            Ask Sathi ➜
          </button>
        </form>
        <div className="disclaimer-footer">
          <span>🔒 100% Private local inference on your GPU</span>
          <span>• Educational study mentor (Not a practicing CA / financial advisor)</span>
        </div>
      </div>
    </div>
  );
}

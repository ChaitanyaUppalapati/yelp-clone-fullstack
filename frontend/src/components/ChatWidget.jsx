// components/ChatWidget.jsx — Floating AI chatbot
import { useState, useRef, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function ChatWidget() {
  const { isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    const userMsg = { role: 'user', content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/ai/chat', { message: text.trim() });
      const aiMsg = { role: 'assistant', content: res.data.message || res.data.response || 'I received your message!' };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const quickActions = [
    'Find dinner tonight',
    'Best rated near me',
    'Vegan options',
    'Cheap eats',
  ];

  return (
    <>
      {/* Chat Panel */}
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <h4>🤖 AI Assistant</h4>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setMessages([])}
                title="New chat"
              >
                🗑️
              </button>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setOpen(false)}
              >
                ✕
              </button>
            </div>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '24px', color: 'var(--clr-text-muted)' }}>
                <p style={{ fontSize: '1.5rem', marginBottom: '8px' }}>🍽️</p>
                <p style={{ fontSize: '0.875rem' }}>
                  Hi! I'm your restaurant assistant. Ask me anything about dining!
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {loading && (
              <div className="chat-bubble assistant" style={{ opacity: 0.6 }}>
                <span className="typing-dots">Thinking…</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          {messages.length === 0 && (
            <div className="chat-quick-actions">
              {quickActions.map((action) => (
                <button
                  key={action}
                  className="chat-quick-btn"
                  onClick={() => sendMessage(action)}
                >
                  {action}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <form className="chat-input-area" onSubmit={handleSubmit}>
            <input
              type="text"
              className="form-input"
              placeholder={isAuthenticated ? 'Ask me anything…' : 'Log in to chat…'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading || !isAuthenticated}
              id="chat-input"
            />
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={loading || !input.trim() || !isAuthenticated}
              id="chat-send"
            >
              ➤
            </button>
          </form>
        </div>
      )}

      {/* FAB */}
      <button
        className="chat-fab"
        onClick={() => setOpen(!open)}
        title="AI Assistant"
        id="chat-fab"
      >
        {open ? '✕' : '💬'}
      </button>
    </>
  );
}

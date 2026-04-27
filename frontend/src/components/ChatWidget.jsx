// components/ChatWidget.jsx — Floating AI chatbot with session + restaurant cards
import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { MessageCircle, Bot, Trash2, X, UtensilsCrossed, Send, MapPin } from 'lucide-react';

const PRICE_LABELS = ['', '$', '$$', '$$$', '$$$$'];

function RestaurantRecommendation({ restaurant }) {
  return (
    <Link
      to={`/restaurants/${restaurant.id}`}
      style={{
        display: 'block',
        background: 'var(--clr-bg-elevated)',
        border: '1px solid var(--clr-border)',
        borderRadius: '8px',
        padding: '10px 12px',
        marginTop: '8px',
        textDecoration: 'none',
        color: 'inherit',
        transition: 'border-color 0.2s',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--clr-primary)')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--clr-border)')}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{restaurant.name}</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--clr-gold, #f5a623)', whiteSpace: 'nowrap', marginLeft: '8px' }}>
          ★ {restaurant.avg_rating?.toFixed(1)}
        </span>
      </div>
      <div style={{ display: 'flex', gap: '8px', marginTop: '4px', flexWrap: 'wrap' }}>
        {restaurant.cuisine_type && (
          <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>{restaurant.cuisine_type}</span>
        )}
        {restaurant.pricing_tier && (
          <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>{PRICE_LABELS[restaurant.pricing_tier]}</span>
        )}
        {restaurant.city && (
          <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', display: 'flex', alignItems: 'center', gap: '2px' }}><MapPin size={11} /> {restaurant.city}</span>
        )}
      </div>
    </Link>
  );
}

export default function ChatWidget() {
  const { isAuthenticated } = useAuth(); // kept for future use
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  // Persist session_id for the lifetime of the chat (reset on "new chat")
  const sessionIdRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    // Generate session_id on first message (crypto.randomUUID requires HTTPS; use fallback for HTTP)
    if (!sessionIdRef.current) {
      sessionIdRef.current =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
              const r = (Math.random() * 16) | 0;
              return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
            });
    }

    const userMsg = { role: 'user', content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/ai/chat', {
        message: text.trim(),
        session_id: sessionIdRef.current,
      });

      const data = res.data;
      const aiMsg = {
        role: 'assistant',
        content: data.response || 'I received your message!',
        restaurants: data.restaurants || [],
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', restaurants: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleNewChat = () => {
    setMessages([]);
    sessionIdRef.current = null;
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
            <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Bot size={18} /> AI Assistant</h4>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn btn-ghost btn-sm"
                onClick={handleNewChat}
                title="New chat"
              >
                <Trash2 size={15} />
              </button>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setOpen(false)}
              >
                <X size={15} />
              </button>
            </div>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '24px', color: 'var(--clr-text-muted)' }}>
                <p style={{ marginBottom: '8px', color: 'var(--clr-text-muted)' }}><UtensilsCrossed size={36} /></p>
                <p style={{ fontSize: '0.875rem' }}>
                  Hi! I&apos;m your restaurant assistant. Ask me anything about dining!
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i}>
                <div className={`chat-bubble ${msg.role}`}>
                  {msg.content}
                </div>
                {msg.role === 'assistant' && msg.restaurants?.length > 0 && (
                  <div style={{ paddingLeft: '8px' }}>
                    {msg.restaurants.map((r) => (
                      <RestaurantRecommendation key={r.id} restaurant={r} />
                    ))}
                  </div>
                )}
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
                  disabled={loading}
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
              placeholder="Ask me anything…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              id="chat-input"
            />
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={loading || !input.trim()}
              id="chat-send"
            >
              <Send size={15} />
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
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </>
  );
}

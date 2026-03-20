// pages/HistoryPage.jsx — User activity history: reviews written + restaurants added
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import StarRating from '../components/StarRating';
import { ClipboardList, PenLine, MapPin, Store } from 'lucide-react';

const PRICE_LABELS = ['', '$', '$$', '$$$', '$$$$'];

export default function HistoryPage() {
  const [tab, setTab] = useState('reviews');
  const [history, setHistory] = useState({ reviews: [], restaurants_added: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/users/me/history')
      .then((res) => setHistory(res.data))
      .catch(() => setError('Failed to load history.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: '760px' }}>
        <h1 style={{ marginBottom: 'var(--sp-xs)', display: 'flex', alignItems: 'center', gap: '10px' }}><ClipboardList size={26} /> My History</h1>
        <p className="text-secondary" style={{ marginBottom: 'var(--sp-lg)' }}>
          Your reviews and restaurants you&apos;ve added
        </p>

        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${tab === 'reviews' ? 'active' : ''}`}
            onClick={() => setTab('reviews')}
          >
            Reviews ({history.reviews.length})
          </button>
          <button
            className={`tab ${tab === 'restaurants' ? 'active' : ''}`}
            onClick={() => setTab('restaurants')}
          >
            Added Restaurants ({history.restaurants_added.length})
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="loading-center"><div className="spinner"></div></div>
        ) : (
          <>
            {/* Reviews Tab */}
            {tab === 'reviews' && (
              <div className="fade-in">
                {history.reviews.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon"><PenLine size={48} /></div>
                    <h3>No reviews yet</h3>
                    <p>Start reviewing restaurants you&apos;ve visited!</p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                    {history.reviews.map((rev) => (
                      <div key={rev.id} className="card">
                        <div className="card-body">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                            <Link
                              to={`/restaurants/${rev.restaurant_id}`}
                              style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--clr-text-primary)' }}
                            >
                              {rev.restaurant_name}
                            </Link>
                            <StarRating rating={rev.rating} size="0.875rem" />
                          </div>
                          {rev.comment && (
                            <p style={{ color: 'var(--clr-text-secondary)', fontSize: '0.9375rem', lineHeight: 1.6 }}>
                              {rev.comment}
                            </p>
                          )}
                          <p style={{ fontSize: '0.8125rem', color: 'var(--clr-text-muted)', marginTop: '8px' }}>
                            {rev.created_at ? new Date(rev.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : ''}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Restaurants Added Tab */}
            {tab === 'restaurants' && (
              <div className="fade-in">
                {history.restaurants_added.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon"><Store size={48} /></div>
                    <h3>No restaurants added yet</h3>
                    <p>Add a restaurant to the platform!</p>
                    <Link to="/add-restaurant" className="btn btn-primary" style={{ marginTop: '16px' }}>
                      + Add Restaurant
                    </Link>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                    {history.restaurants_added.map((r) => (
                      <div key={r.id} className="card">
                        <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <Link
                              to={`/restaurants/${r.id}`}
                              style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--clr-text-primary)' }}
                            >
                              {r.name}
                            </Link>
                            <div style={{ display: 'flex', gap: '12px', marginTop: '6px', flexWrap: 'wrap' }}>
                              {r.cuisine_type && (
                                <span className="badge badge-primary">{r.cuisine_type}</span>
                              )}
                              {r.pricing_tier && (
                                <span style={{ fontSize: '0.8125rem', color: 'var(--clr-text-muted)' }}>
                                  {PRICE_LABELS[r.pricing_tier]}
                                </span>
                              )}
                              {r.city && (
                                <span style={{ fontSize: '0.8125rem', color: 'var(--clr-text-muted)' }}>
                                  <MapPin size={12} /> {r.city}
                                </span>
                              )}
                              <StarRating rating={r.avg_rating} size="0.8125rem" />
                              <span style={{ fontSize: '0.8125rem', color: 'var(--clr-text-muted)' }}>
                                {r.review_count} review{r.review_count !== 1 ? 's' : ''}
                              </span>
                            </div>
                          </div>
                          <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                            <Link to={`/restaurants/${r.id}`} className="btn btn-ghost btn-sm">View</Link>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

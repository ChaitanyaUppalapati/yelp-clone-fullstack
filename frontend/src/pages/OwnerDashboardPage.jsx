// pages/OwnerDashboardPage.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import StarRating from '../components/StarRating';
import { BarChart2, Store, MapPin } from 'lucide-react';

export default function OwnerDashboardPage() {
  const [restaurants, setRestaurants] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/owner/restaurants'),
      api.get('/owner/analytics'),
    ])
      .then(([restRes, analyticsRes]) => {
        setRestaurants(restRes.data);
        setAnalytics(analyticsRes.data);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const maxDistCount = analytics
    ? Math.max(...Object.values(analytics.ratings_distribution), 1)
    : 1;

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 'var(--sp-xs)', display: 'flex', alignItems: 'center', gap: '10px' }}><BarChart2 size={26} /> Owner Dashboard</h1>
        <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)' }}>
          Manage your restaurant listings and track performance
        </p>

        {loading ? (
          <div className="loading-center"><div className="spinner"></div></div>
        ) : (
          <>
            {/* ── Summary Stats ── */}
            <div className="stat-cards fade-in" style={{ marginBottom: 'var(--sp-xl)' }}>
              <div className="stat-card">
                <div className="stat-value">{analytics?.total_restaurants ?? restaurants.length}</div>
                <div className="stat-label">Restaurants</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{(analytics?.total_reviews ?? 0).toLocaleString()}</div>
                <div className="stat-label">Total Reviews</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{analytics?.avg_rating?.toFixed(1) ?? '0.0'}</div>
                <div className="stat-label">Avg Rating</div>
              </div>
            </div>

            {/* ── Ratings Distribution ── */}
            {analytics && analytics.total_reviews > 0 && (
              <div className="card fade-in" style={{ marginBottom: 'var(--sp-xl)' }}>
                <div className="card-body">
                  <h2 style={{ fontSize: '1.125rem', marginBottom: 'var(--sp-md)' }}>Ratings Distribution</h2>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {[5, 4, 3, 2, 1].map((star) => {
                      const count = analytics.ratings_distribution[star] || 0;
                      const pct = Math.round((count / maxDistCount) * 100);
                      return (
                        <div key={star} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <span style={{ width: '24px', textAlign: 'right', fontSize: '0.875rem', fontWeight: 600 }}>{star}★</span>
                          <div style={{ flex: 1, background: 'var(--clr-bg)', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                            <div style={{ width: `${pct}%`, height: '100%', background: 'var(--clr-gold, #f5a623)', borderRadius: '4px', transition: 'width 0.4s ease' }} />
                          </div>
                          <span style={{ width: '28px', fontSize: '0.8125rem', color: 'var(--clr-text-muted)' }}>{count}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* ── Recent Reviews ── */}
            {analytics && analytics.recent_reviews?.length > 0 && (
              <div className="card fade-in" style={{ marginBottom: 'var(--sp-xl)' }}>
                <div className="card-body">
                  <h2 style={{ fontSize: '1.125rem', marginBottom: 'var(--sp-md)' }}>Recent Reviews</h2>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                    {analytics.recent_reviews.map((rev) => (
                      <div key={rev.id} style={{ borderBottom: '1px solid var(--clr-border)', paddingBottom: 'var(--sp-md)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <Link to={`/restaurants/${rev.restaurant_id}`} style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
                            {rev.restaurant_name}
                          </Link>
                          <StarRating rating={rev.rating} size="0.8125rem" />
                        </div>
                        {rev.comment && (
                          <p style={{ color: 'var(--clr-text-secondary)', fontSize: '0.875rem', lineHeight: 1.5, margin: 0 }}>
                            {rev.comment.length > 140 ? rev.comment.slice(0, 140) + '…' : rev.comment}
                          </p>
                        )}
                        <p style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', marginTop: '4px' }}>
                          {rev.created_at ? new Date(rev.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : ''}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── Restaurant List ── */}
            <h2 style={{ fontSize: '1.25rem', marginBottom: 'var(--sp-md)' }}>Your Restaurants</h2>
            {restaurants.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon"><Store size={48} /></div>
                <h3>No restaurants yet</h3>
                <p>Add a restaurant to get started</p>
                <Link to="/add-restaurant" className="btn btn-primary" style={{ marginTop: '16px' }}>+ Add Restaurant</Link>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                {restaurants.map((r) => (
                  <div key={r.id} className="card fade-in" style={{ cursor: 'default' }}>
                    <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h4 style={{ marginBottom: '4px' }}>{r.name}</h4>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <StarRating rating={parseFloat(r.avg_rating)} size="0.875rem" />
                          <span className="text-muted" style={{ fontSize: '0.8125rem' }}>
                            {r.review_count} reviews
                          </span>
                          {r.city && <span className="text-secondary" style={{ fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '3px' }}><MapPin size={12} /> {r.city}</span>}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <Link to={`/owner/manage/${r.id}`} className="btn btn-secondary btn-sm">Manage</Link>
                        <Link to={`/restaurants/${r.id}`} className="btn btn-ghost btn-sm">View</Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

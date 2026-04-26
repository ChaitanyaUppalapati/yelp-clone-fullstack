import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import StarRating from '../components/StarRating';
import {
  BarChart2,
  Store,
  MapPin,
  MessageSquareText,
  Smile,
  Meh,
  Frown,
} from 'lucide-react';

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
  const sentiment = analytics?.sentiment_analysis;
  const sentimentDistMax = sentiment
    ? Math.max(...Object.values(sentiment.distribution || { positive: 0, neutral: 0, negative: 0 }), 1)
    : 1;
  const sentimentToneMeta = {
    positive: { icon: Smile, color: 'var(--clr-success)', background: 'rgba(46, 204, 113, 0.14)' },
    neutral: { icon: Meh, color: 'var(--clr-warning)', background: 'rgba(243, 156, 18, 0.14)' },
    negative: { icon: Frown, color: 'var(--clr-error)', background: 'rgba(231, 76, 60, 0.14)' },
  };

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 'var(--sp-xs)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <BarChart2 size={26} /> Owner Dashboard
        </h1>
        <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)' }}>
          Manage your restaurant listings and track performance
        </p>

        {loading ? (
          <div className="loading-center"><div className="spinner"></div></div>
        ) : (
          <>
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

            {sentiment && (
              <div className="card fade-in" style={{ marginBottom: 'var(--sp-xl)' }}>
                <div className="card-body">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap', marginBottom: 'var(--sp-md)' }}>
                    <div>
                      <h2 style={{ fontSize: '1.125rem', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <MessageSquareText size={18} /> Review Sentiment
                      </h2>
                      <p className="text-secondary" style={{ fontSize: '0.875rem' }}>
                        Overall tone across customer feedback
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div
                        className="badge"
                        style={{
                          background: sentimentToneMeta[sentiment.overall_label]?.background || 'rgba(52, 152, 219, 0.14)',
                          color: sentimentToneMeta[sentiment.overall_label]?.color || 'var(--clr-info)',
                          marginBottom: '6px',
                          textTransform: 'capitalize',
                        }}
                      >
                        {sentiment.overall_label}
                      </div>
                      <div className="text-secondary" style={{ fontSize: '0.8125rem' }}>
                        Avg score: {sentiment.average_score.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  {sentiment.total_reviews_analyzed > 0 ? (
                    <>
                      <div className="stat-cards" style={{ marginBottom: 'var(--sp-lg)' }}>
                        {['positive', 'neutral', 'negative'].map((label) => {
                          const Icon = sentimentToneMeta[label].icon;
                          const count = sentiment.distribution[label] || 0;
                          return (
                            <div key={label} className="stat-card">
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                                <span style={{ color: sentimentToneMeta[label].color, display: 'inline-flex', alignItems: 'center', gap: '6px', textTransform: 'capitalize', fontWeight: 600 }}>
                                  <Icon size={16} /> {label}
                                </span>
                                <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>{count}</span>
                              </div>
                              <div style={{ background: 'var(--clr-bg)', borderRadius: '999px', height: '8px', overflow: 'hidden' }}>
                                <div
                                  style={{
                                    width: `${Math.round((count / sentimentDistMax) * 100)}%`,
                                    height: '100%',
                                    background: sentimentToneMeta[label].color,
                                    borderRadius: '999px',
                                  }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: 'var(--sp-lg)' }}>
                        <div>
                          <h3 style={{ fontSize: '0.9375rem', marginBottom: '10px' }}>Top Praised Themes</h3>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {sentiment.top_positive_themes.length > 0 ? (
                              sentiment.top_positive_themes.map((theme) => (
                                <span key={theme.term} className="badge badge-success">
                                  {theme.term} ({theme.count})
                                </span>
                              ))
                            ) : (
                              <span className="text-muted" style={{ fontSize: '0.875rem' }}>Not enough written praise yet.</span>
                            )}
                          </div>
                        </div>

                        <div>
                          <h3 style={{ fontSize: '0.9375rem', marginBottom: '10px' }}>Top Criticized Themes</h3>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {sentiment.top_negative_themes.length > 0 ? (
                              sentiment.top_negative_themes.map((theme) => (
                                <span
                                  key={theme.term}
                                  className="badge"
                                  style={{ background: 'rgba(231, 76, 60, 0.15)', color: 'var(--clr-error)' }}
                                >
                                  {theme.term} ({theme.count})
                                </span>
                              ))
                            ) : (
                              <span className="text-muted" style={{ fontSize: '0.875rem' }}>No recurring complaints detected.</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {sentiment.restaurant_breakdown?.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '0.9375rem', marginBottom: '10px' }}>Per-Restaurant Mood</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {sentiment.restaurant_breakdown.map((entry) => (
                              <div key={entry.restaurant_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', padding: '10px 12px', background: 'var(--clr-bg-elevated)', borderRadius: '8px', border: '1px solid var(--clr-border)' }}>
                                <div>
                                  <Link to={`/restaurants/${entry.restaurant_id}`} style={{ fontWeight: 600 }}>
                                    {entry.restaurant_name}
                                  </Link>
                                  <div className="text-muted" style={{ fontSize: '0.8125rem' }}>
                                    {entry.review_count} review{entry.review_count !== 1 ? 's' : ''} analyzed
                                  </div>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                  <div style={{ textTransform: 'capitalize', color: sentimentToneMeta[entry.label]?.color || 'var(--clr-text-secondary)', fontWeight: 600 }}>
                                    {entry.label}
                                  </div>
                                  <div className="text-secondary" style={{ fontSize: '0.8125rem' }}>
                                    Score {entry.average_score.toFixed(2)}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                      Reviews are coming in, but there isn&apos;t enough feedback text yet to summarize the tone.
                    </p>
                  )}
                </div>
              </div>
            )}

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
                          <span style={{ width: '24px', textAlign: 'right', fontSize: '0.875rem', fontWeight: 600 }}>{star}/5</span>
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
                            {rev.comment.length > 140 ? rev.comment.slice(0, 140) + '...' : rev.comment}
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
                {restaurants.map((restaurant) => (
                  <div key={restaurant.id} className="card fade-in" style={{ cursor: 'default' }}>
                    <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h4 style={{ marginBottom: '4px' }}>{restaurant.name}</h4>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <StarRating rating={parseFloat(restaurant.avg_rating)} size="0.875rem" />
                          <span className="text-muted" style={{ fontSize: '0.8125rem' }}>
                            {restaurant.review_count} reviews
                          </span>
                          {restaurant.city && (
                            <span className="text-secondary" style={{ fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '3px' }}>
                              <MapPin size={12} /> {restaurant.city}
                            </span>
                          )}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <Link to={`/owner/manage/${restaurant.id}`} className="btn btn-secondary btn-sm">Manage</Link>
                        <Link to={`/restaurants/${restaurant.id}`} className="btn btn-ghost btn-sm">View</Link>
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

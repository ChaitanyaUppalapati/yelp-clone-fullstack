// pages/OwnerDashboardPage.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import StarRating from '../components/StarRating';

export default function OwnerDashboardPage() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/owner/restaurants')
      .then((res) => setRestaurants(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const totalReviews = restaurants.reduce((sum, r) => sum + (r.review_count || 0), 0);
  const avgRating = restaurants.length
    ? (restaurants.reduce((sum, r) => sum + parseFloat(r.avg_rating || 0), 0) / restaurants.length).toFixed(1)
    : '0.0';

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 'var(--sp-xs)' }}>📊 Owner Dashboard</h1>
        <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)' }}>
          Manage your restaurant listings and track performance
        </p>

        {loading ? (
          <div className="loading-center"><div className="spinner"></div></div>
        ) : (
          <>
            {/* Stats */}
            <div className="stat-cards fade-in">
              <div className="stat-card">
                <div className="stat-value">{restaurants.length}</div>
                <div className="stat-label">Restaurants</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{totalReviews.toLocaleString()}</div>
                <div className="stat-label">Total Reviews</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{avgRating}</div>
                <div className="stat-label">Avg Rating</div>
              </div>
            </div>

            {/* Restaurant List */}
            <h2 style={{ fontSize: '1.25rem', marginBottom: 'var(--sp-md)' }}>Your Restaurants</h2>
            {restaurants.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🏪</div>
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
                          {r.city && <span className="text-secondary" style={{ fontSize: '0.8125rem' }}>📍 {r.city}</span>}
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

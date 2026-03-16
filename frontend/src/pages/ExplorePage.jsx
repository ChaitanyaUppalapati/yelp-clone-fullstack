// pages/ExplorePage.jsx — Landing page with search and restaurant grid
import { useState, useEffect } from 'react';
import api from '../services/api';
import SearchBar from '../components/SearchBar';
import RestaurantCard from '../components/RestaurantCard';

export default function ExplorePage() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchRestaurants = async (filters = {}) => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (filters.cuisine) params.cuisine = filters.cuisine;
      if (filters.city) params.city = filters.city;
      if (filters.pricing_tier) params.pricing_tier = filters.pricing_tier;

      const res = await api.get('/restaurants/', { params });
      setRestaurants(res.data);
    } catch (err) {
      setError('Failed to load restaurants. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRestaurants();
  }, []);

  return (
    <div className="page">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <h1>Discover Great Restaurants</h1>
          <p>Find the perfect spot for any occasion. Read reviews, explore menus, and make reservations.</p>
          <SearchBar onSearch={fetchRestaurants} />
        </div>
      </section>

      {/* Restaurant Grid */}
      <section className="container" style={{ marginTop: 'var(--sp-xl)' }}>
        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="loading-center">
            <div className="spinner"></div>
          </div>
        ) : restaurants.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🍽️</div>
            <h3>No restaurants found</h3>
            <p>Try adjusting your search filters</p>
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-lg)' }}>
              <h2 style={{ fontSize: '1.25rem' }}>
                {restaurants.length} restaurant{restaurants.length !== 1 ? 's' : ''} found
              </h2>
            </div>
            <div className="grid grid-3">
              {restaurants.map((r) => (
                <RestaurantCard key={r.id} restaurant={r} />
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}

// pages/FavoritesPage.jsx
import { useState, useEffect } from 'react';
import api from '../services/api';
import RestaurantCard from '../components/RestaurantCard';

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFavorites = async () => {
      try {
        const favRes = await api.get('/favorites/');
        setFavorites(favRes.data);

        // Fetch each favorited restaurant's details
        const restaurantPromises = favRes.data.map((fav) =>
          api.get(`/restaurants/${fav.restaurant_id}`).then((r) => r.data).catch(() => null)
        );
        const results = await Promise.all(restaurantPromises);
        setRestaurants(results.filter(Boolean));
      } catch (err) {
        console.error('Failed to load favorites', err);
      } finally {
        setLoading(false);
      }
    };
    fetchFavorites();
  }, []);

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 'var(--sp-xs)' }}>♥ Your Favorites</h1>
        <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)' }}>
          Restaurants you've saved for later
        </p>

        {loading ? (
          <div className="loading-center"><div className="spinner"></div></div>
        ) : restaurants.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">💔</div>
            <h3>No favorites yet</h3>
            <p>Click the heart on any restaurant to save it here</p>
          </div>
        ) : (
          <div className="grid grid-3 fade-in-up">
            {restaurants.map((r) => (
              <RestaurantCard key={r.id} restaurant={r} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

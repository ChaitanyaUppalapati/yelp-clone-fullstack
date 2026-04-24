// pages/FavoritesPage.jsx
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import api from '../services/api';
import RestaurantCard from '../components/RestaurantCard';
import { fetchFavorites } from '../store/favoritesSlice';
import { Heart, HeartOff } from 'lucide-react';

export default function FavoritesPage() {
  const dispatch = useDispatch();
  const { favorites, loading: favLoading } = useSelector((state) => state.favorites);
  const [restaurants, setRestaurants] = useState([]);
  const [restaurantsLoading, setRestaurantsLoading] = useState(true);

  useEffect(() => {
    dispatch(fetchFavorites());
  }, [dispatch]);

  // Hydrate full restaurant details for each favorited id.
  useEffect(() => {
    if (favLoading) return;
    let cancelled = false;
    (async () => {
      setRestaurantsLoading(true);
      try {
        const results = await Promise.all(
          favorites.map((fav) =>
            api.get(`/restaurants/${fav.restaurant_id}`).then((r) => r.data).catch(() => null)
          )
        );
        if (!cancelled) setRestaurants(results.filter(Boolean));
      } finally {
        if (!cancelled) setRestaurantsLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [favorites, favLoading]);

  const loading = favLoading || restaurantsLoading;

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 'var(--sp-xs)', display: 'flex', alignItems: 'center', gap: '10px' }}><Heart size={26} /> Your Favorites</h1>
        <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)' }}>
          Restaurants you've saved for later
        </p>

        {loading ? (
          <div className="loading-center"><div className="spinner"></div></div>
        ) : restaurants.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><HeartOff size={48} /></div>
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

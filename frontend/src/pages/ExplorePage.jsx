// pages/ExplorePage.jsx — Landing page with search and restaurant grid
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import SearchBar from '../components/SearchBar';
import RestaurantCard from '../components/RestaurantCard';
import { fetchRestaurants } from '../store/restaurantSlice';
import { UtensilsCrossed } from 'lucide-react';

export default function ExplorePage() {
  const dispatch = useDispatch();
  const { restaurants, loading, error } = useSelector((state) => state.restaurants);

  useEffect(() => {
    dispatch(fetchRestaurants({}));
  }, [dispatch]);

  const handleSearch = (filters) => {
    dispatch(fetchRestaurants(filters));
  };

  return (
    <div className="page">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <h1>Discover Great Restaurants</h1>
          <p>Find the perfect spot for any occasion. Read reviews, explore menus, and make reservations.</p>
          <SearchBar onSearch={handleSearch} />
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
            <div className="empty-state-icon"><UtensilsCrossed size={48} /></div>
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

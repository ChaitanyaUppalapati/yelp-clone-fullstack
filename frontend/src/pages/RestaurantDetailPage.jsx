// pages/RestaurantDetailPage.jsx
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import StarRating from '../components/StarRating';
import ReviewCard from '../components/ReviewCard';
import { Heart, Store, PenLine, UtensilsCrossed, ArrowLeft, Search } from 'lucide-react';

const PRICE_LABELS = ['', '$', '$$', '$$$', '$$$$'];
const DAY_ORDER = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
const DAY_NAMES = { mon: 'Monday', tue: 'Tuesday', wed: 'Wednesday', thu: 'Thursday', fri: 'Friday', sat: 'Saturday', sun: 'Sunday' };

const PLACEHOLDER_IMAGES = [
  'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&h=400&fit=crop',
  'https://images.unsplash.com/photo-1552566626-52f8b828add9?w=800&h=400&fit=crop',
];

export default function RestaurantDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, isOwner, user } = useAuth();

  const [restaurant, setRestaurant] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [isFavorited, setIsFavorited] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [claiming, setClaiming] = useState(false);
  const [claimMsg, setClaimMsg] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [restRes, revRes] = await Promise.all([
          api.get(`/restaurants/${id}`),
          api.get(`/reviews/restaurant/${id}`),
        ]);
        setRestaurant(restRes.data);
        setReviews(revRes.data);

        // Check if user has favorited (only if authenticated)
        if (isAuthenticated) {
          try {
            const favRes = await api.get('/favorites/');
            setIsFavorited(favRes.data.some((f) => f.restaurant_id === parseInt(id)));
          } catch { /* ignore if not auth */ }
        }
      } catch (err) {
        setError('Restaurant not found.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, isAuthenticated]);

  const claimRestaurant = async () => {
    setClaiming(true);
    setClaimMsg('');
    try {
      await api.put(`/owner/claim/${id}`);
      setClaimMsg('Restaurant claimed! You can now manage it from your dashboard.');
      setRestaurant((r) => ({ ...r, owner_id: user?.id }));
    } catch (err) {
      setClaimMsg(err.response?.data?.detail || 'Failed to claim restaurant.');
    } finally {
      setClaiming(false);
    }
  };

  const toggleFavorite = async () => {
    if (!isAuthenticated) { navigate('/login'); return; }
    try {
      if (isFavorited) {
        await api.delete(`/favorites/${id}`);
      } else {
        await api.post(`/favorites/${id}`);
      }
      setIsFavorited(!isFavorited);
    } catch (err) {
      console.error('Favorite toggle failed', err);
    }
  };

  if (loading) return <div className="page loading-center"><div className="spinner"></div></div>;
  if (error || !restaurant) return (
    <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '70vh' }}>
      <div style={{ textAlign: 'center', maxWidth: '480px', padding: '0 var(--sp-lg)' }}>
        <div style={{ marginBottom: 'var(--sp-lg)', color: 'var(--clr-text-muted)' }}>
          <UtensilsCrossed size={72} strokeWidth={1.25} />
        </div>
        <h2 style={{ fontSize: '1.75rem', marginBottom: 'var(--sp-sm)' }}>Restaurant Not Found</h2>
        <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)', lineHeight: 1.6 }}>
          We couldn&apos;t find this restaurant. It may have been removed or the link might be incorrect.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button className="btn btn-ghost" onClick={() => navigate(-1)}>
            <ArrowLeft size={15} /> Go Back
          </button>
          <Link to="/" className="btn btn-primary">
            <Search size={15} /> Browse Restaurants
          </Link>
        </div>
      </div>
    </div>
  );

  const imgSrc = restaurant.photos?.[0] || PLACEHOLDER_IMAGES[restaurant.id % PLACEHOLDER_IMAGES.length];

  return (
    <div className="page fade-in">
      {/* Hero Image */}
      <div className="detail-hero">
        <img src={imgSrc} alt={restaurant.name} onError={(e) => { e.target.src = PLACEHOLDER_IMAGES[0]; }} />
        <div className="detail-hero-overlay" />
      </div>

      <div className="container" style={{ marginTop: '-60px', position: 'relative', zIndex: 1 }}>
        <div className="detail-info">
          {/* Main Content */}
          <div className="detail-main">
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
              <h1>{restaurant.name}</h1>
              <button
                className={`fav-btn ${isFavorited ? 'favorited' : ''}`}
                onClick={toggleFavorite}
                title={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
                id="fav-toggle"
              >
                {isFavorited ? <Heart size={20} fill="currentColor" /> : <Heart size={20} />}
              </button>
            </div>

            <div className="detail-meta">
              <span><StarRating rating={parseFloat(restaurant.avg_rating)} /> {parseFloat(restaurant.avg_rating).toFixed(1)}</span>
              <span>({restaurant.review_count} reviews)</span>
              {restaurant.cuisine_type && <span className="badge badge-primary">{restaurant.cuisine_type}</span>}
              {restaurant.pricing_tier && <span className="price-tier">{PRICE_LABELS[restaurant.pricing_tier]}</span>}
            </div>

            {/* Claim banner for owners */}
            {isOwner && restaurant.owner_id !== user?.id && (
              <div style={{ background: 'var(--clr-bg-elevated)', border: '1px solid var(--clr-border)', borderRadius: '8px', padding: '12px 16px', marginBottom: 'var(--sp-lg)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                <span style={{ fontSize: '0.9375rem', color: 'var(--clr-text-secondary)' }}>
                  Is this your restaurant? Claim it to manage its profile.
                </span>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={claimRestaurant}
                  disabled={claiming}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  {claiming ? 'Claiming…' : <><Store size={14} /> Claim Restaurant</>}
                </button>
              </div>
            )}
            {claimMsg && (
              <div className={`alert ${claimMsg.includes('Failed') ? 'alert-error' : 'alert-success'}`} style={{ marginBottom: 'var(--sp-md)' }}>
                {claimMsg}
              </div>
            )}

            {restaurant.description && (
              <p style={{ color: 'var(--clr-text-secondary)', marginBottom: 'var(--sp-xl)', lineHeight: 1.7 }}>
                {restaurant.description}
              </p>
            )}

            {/* Amenities */}
            {restaurant.amenities?.length > 0 && (
              <div style={{ marginBottom: 'var(--sp-xl)' }}>
                <h3 style={{ marginBottom: 'var(--sp-sm)', fontSize: '1rem' }}>Amenities</h3>
                <div className="tags">
                  {restaurant.amenities.map((a) => (
                    <span className="tag" key={a}>{a.replace(/_/g, ' ')}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Reviews Section */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-md)' }}>
                <h2 style={{ fontSize: '1.25rem' }}>Reviews ({reviews.length})</h2>
                <Link to={`/restaurants/${id}/review`} className="btn btn-primary btn-sm">
                  <PenLine size={14} /> Write a Review
                </Link>
              </div>

              {reviews.length === 0 ? (
                <div className="empty-state" style={{ padding: 'var(--sp-xl)' }}>
                  <p>No reviews yet. Be the first!</p>
                </div>
              ) : (
                reviews.map((rev) => (
                  <ReviewCard key={rev.id} review={rev} />
                ))
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="detail-sidebar">
            <div className="card">
              <div className="card-body">
                {/* Contact */}
                {restaurant.address_line && (
                  <div style={{ marginBottom: 'var(--sp-md)' }}>
                    <h5 style={{ marginBottom: '4px', color: 'var(--clr-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Address</h5>
                    <p style={{ fontSize: '0.9375rem' }}>
                      {restaurant.address_line}<br />
                      {restaurant.city}, {restaurant.state} {restaurant.zip_code}
                    </p>
                  </div>
                )}

                {restaurant.phone && (
                  <div style={{ marginBottom: 'var(--sp-md)' }}>
                    <h5 style={{ marginBottom: '4px', color: 'var(--clr-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Phone</h5>
                    <p style={{ fontSize: '0.9375rem' }}>{restaurant.phone}</p>
                  </div>
                )}

                {restaurant.website && (
                  <div style={{ marginBottom: 'var(--sp-md)' }}>
                    <h5 style={{ marginBottom: '4px', color: 'var(--clr-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Website</h5>
                    <a href={restaurant.website} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.9375rem' }}>
                      {restaurant.website.replace(/^https?:\/\//, '')}
                    </a>
                  </div>
                )}

                {/* Hours */}
                {restaurant.hours_of_operation && (
                  <div>
                    <h5 style={{ marginBottom: '8px', color: 'var(--clr-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Hours</h5>
                    <table className="hours-table">
                      <tbody>
                        {DAY_ORDER.map((day) => (
                          <tr key={day}>
                            <td>{DAY_NAMES[day]}</td>
                            <td>{restaurant.hours_of_operation[day] || 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

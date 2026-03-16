// components/RestaurantCard.jsx
import { useNavigate } from 'react-router-dom';
import StarRating from './StarRating';

const PRICE_LABELS = ['', '$', '$$', '$$$', '$$$$'];

const PLACEHOLDER_IMAGES = [
  'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1552566626-52f8b828add9?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=400&h=300&fit=crop',
];

export default function RestaurantCard({ restaurant }) {
  const navigate = useNavigate();
  const {
    id,
    name,
    cuisine_type,
    city,
    state,
    pricing_tier,
    avg_rating,
    review_count,
    photos,
  } = restaurant;

  const imgSrc = photos?.[0] || PLACEHOLDER_IMAGES[id % PLACEHOLDER_IMAGES.length];

  return (
    <div
      className="card fade-in-up"
      onClick={() => navigate(`/restaurants/${id}`)}
      style={{ cursor: 'pointer' }}
      id={`restaurant-card-${id}`}
    >
      <img
        src={imgSrc}
        alt={name}
        className="card-img"
        loading="lazy"
        onError={(e) => {
          e.target.src = PLACEHOLDER_IMAGES[0];
        }}
      />
      <div className="card-body">
        <h4 style={{ marginBottom: '6px' }}>{name}</h4>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <StarRating rating={parseFloat(avg_rating)} size="0.9375rem" />
          <span className="text-muted" style={{ fontSize: '0.8125rem' }}>
            ({review_count})
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.875rem' }}>
          {cuisine_type && <span className="badge badge-primary">{cuisine_type}</span>}
          {pricing_tier && (
            <span className="price-tier">{PRICE_LABELS[pricing_tier]}</span>
          )}
          {city && (
            <span className="text-secondary">
              📍 {city}{state ? `, ${state}` : ''}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

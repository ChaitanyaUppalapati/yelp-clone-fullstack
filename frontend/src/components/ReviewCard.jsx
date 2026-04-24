// components/ReviewCard.jsx
import StarRating from './StarRating';

const API_BASE = 'http://localhost:8000';

export default function ReviewCard({ review }) {
  const displayName = review.user_name || `User #${review.user_id}`;
  const initial = displayName.charAt(0).toUpperCase();
  const date = new Date(review.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  return (
    <div className="review-card fade-in">
      <div className="review-header">
        <div className="review-avatar">{initial}</div>
        <div className="review-meta">
          <span className="review-author">{displayName}</span>
          <span className="review-date">{date}</span>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <StarRating rating={review.rating} size="0.875rem" />
        </div>
      </div>
      {review.comment && <p className="review-text">{review.comment}</p>}
      {review.photos?.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '10px' }}>
          {review.photos.map((photo, i) => (
            <img
              key={i}
              src={photo.startsWith('/uploads') ? `${API_BASE}${photo}` : photo}
              alt={`Review photo ${i + 1}`}
              style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '8px' }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// components/ReviewCard.jsx
import StarRating from './StarRating';
import { MEDIA_BASE_URL } from '../services/api';
import { Trash2 } from 'lucide-react';

export default function ReviewCard({ review, canDelete = false, onDelete, deleting = false }) {
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
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <StarRating rating={review.rating} size="0.875rem" />
          {canDelete && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={onDelete}
              disabled={deleting}
              aria-label="Delete review"
            >
              <Trash2 size={14} />
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          )}
        </div>
      </div>
      {review.comment && <p className="review-text">{review.comment}</p>}
      {review.photos?.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '10px' }}>
          {review.photos.map((photo, i) => (
            <img
              key={i}
              src={photo.startsWith('/uploads') ? `${MEDIA_BASE_URL}${photo}` : photo}
              alt={`Review photo ${i + 1}`}
              style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '8px' }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// components/ReviewCard.jsx
import StarRating from './StarRating';

export default function ReviewCard({ review, userName }) {
  const initial = (userName || 'U').charAt(0).toUpperCase();
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
          <span className="review-author">{userName || `User #${review.user_id}`}</span>
          <span className="review-date">{date}</span>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <StarRating rating={review.rating} size="0.875rem" />
        </div>
      </div>
      {review.comment && <p className="review-text">{review.comment}</p>}
    </div>
  );
}

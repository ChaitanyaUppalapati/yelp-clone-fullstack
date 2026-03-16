// pages/WriteReviewPage.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import StarRating from '../components/StarRating';

export default function WriteReviewPage() {
  const { id: restaurantId } = useParams();
  const navigate = useNavigate();

  const [restaurant, setRestaurant] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get(`/restaurants/${restaurantId}`)
      .then((res) => setRestaurant(res.data))
      .catch(() => setError('Restaurant not found'));
  }, [restaurantId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (rating === 0) { setError('Please select a rating.'); return; }

    setLoading(true);
    setError('');
    try {
      await api.post('/reviews/', {
        restaurant_id: parseInt(restaurantId),
        rating,
        comment: comment.trim() || null,
      });
      navigate(`/restaurants/${restaurantId}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit review.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: '640px' }}>
        <div className="fade-in-up">
          <h1 style={{ marginBottom: 'var(--sp-sm)' }}>Write a Review</h1>
          {restaurant && (
            <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)', fontSize: '1.125rem' }}>
              for <strong style={{ color: 'var(--clr-text)' }}>{restaurant.name}</strong>
            </p>
          )}

          {error && <div className="alert alert-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group" style={{ marginBottom: 'var(--sp-xl)' }}>
              <label className="form-label">Your Rating</label>
              <StarRating
                rating={rating}
                interactive
                onChange={setRating}
                size="2rem"
              />
              {rating > 0 && (
                <span className="text-muted" style={{ fontSize: '0.875rem', marginTop: '4px' }}>
                  {['', 'Not good', 'Could be better', 'OK', 'Great', 'Outstanding'][rating]}
                </span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="review-comment">Your Review</label>
              <textarea
                id="review-comment"
                className="form-textarea"
                placeholder="Share your experience — What did you order? How was the service and atmosphere?"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={6}
              />
            </div>

            <div style={{ display: 'flex', gap: 'var(--sp-md)', marginTop: 'var(--sp-lg)' }}>
              <button type="submit" className="btn btn-primary btn-lg" disabled={loading} id="review-submit">
                {loading ? 'Submitting…' : '✍️ Submit Review'}
              </button>
              <button type="button" className="btn btn-ghost btn-lg" onClick={() => navigate(-1)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import api from '../services/api';
import StarRating from '../components/StarRating';
import { createReview, clearReviewStatus, clearReviewError } from '../store/reviewSlice';
import { Camera, X, PenLine } from 'lucide-react';

export default function WriteReviewPage() {
  const { id: restaurantId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { loading: submitting, error: submitError, reviewStatus } = useSelector((s) => s.reviews);
  const { user } = useSelector((s) => s.auth);
  const isOwner = user?.role === 'owner';

  const [restaurant, setRestaurant] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [photos, setPhotos] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [error, setError] = useState('');
  const photoInputRef = useRef(null);
  const navTimeoutRef = useRef(null);

  useEffect(() => {
    api.get(`/restaurants/${restaurantId}`)
      .then((res) => setRestaurant(res.data))
      .catch(() => setError('Restaurant not found'));
  }, [restaurantId]);

  useEffect(() => {
    dispatch(clearReviewStatus());
    dispatch(clearReviewError());
    return () => {
      dispatch(clearReviewStatus());
      dispatch(clearReviewError());
    };
  }, [dispatch]);

  useEffect(() => () => {
    if (navTimeoutRef.current) clearTimeout(navTimeoutRef.current);
  }, []);

  useEffect(() => {
    return () => previews.forEach((url) => URL.revokeObjectURL(url));
  }, [previews]);

  const handlePhotoSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (photos.length + files.length > 5) {
      setError('Maximum 5 photos allowed.');
      return;
    }
    setPhotos((prev) => [...prev, ...files]);
    setPreviews((prev) => [...prev, ...files.map((file) => URL.createObjectURL(file))]);
    e.target.value = '';
  };

  const removePhoto = (index) => {
    URL.revokeObjectURL(previews[index]);
    setPhotos((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isOwner) {
      setError('Owner accounts cannot submit reviews.');
      return;
    }
    if (rating === 0) {
      setError('Please select a rating.');
      return;
    }
    setError('');

    const result = await dispatch(createReview({
      restaurant_id: parseInt(restaurantId),
      rating,
      comment: comment.trim() || null,
    }));

    if (!createReview.fulfilled.match(result)) return;

    const { status, data } = result.payload;

    if (status === 202) {
      navTimeoutRef.current = setTimeout(
        () => navigate(`/restaurants/${restaurantId}`),
        1500,
      );
      return;
    }

    if (photos.length > 0 && data?.id) {
      try {
        const formData = new FormData();
        photos.forEach((photo) => formData.append('files', photo));
        await api.post(`/reviews/${data.id}/photos`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } catch (err) {
        setError(err.response?.data?.detail || 'Review saved but photo upload failed.');
        return;
      }
    }

    navigate(`/restaurants/${restaurantId}`);
  };

  const displayError = error || submitError;

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

          {displayError && <div className="alert alert-error">{displayError}</div>}
          {reviewStatus === 'accepted' && (
            <div className="alert alert-success">
              Your review was submitted - it&apos;ll appear shortly.
            </div>
          )}

          {isOwner ? (
            <div className="card">
              <div className="card-body">
                <div className="alert alert-info" style={{ marginBottom: 'var(--sp-lg)' }}>
                  Owner accounts can&apos;t submit restaurant reviews.
                </div>
                <p className="text-secondary" style={{ marginBottom: 'var(--sp-lg)' }}>
                  You can still manage listings and track feedback from the owner dashboard.
                </p>
                <button type="button" className="btn btn-ghost btn-lg" onClick={() => navigate(`/restaurants/${restaurantId}`)}>
                  Back to Restaurant
                </button>
              </div>
            </div>
          ) : (
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
                  placeholder="Share your experience - What did you order? How was the service and atmosphere?"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={6}
                />
              </div>

              <div className="form-group" style={{ marginTop: 'var(--sp-md)' }}>
                <label className="form-label">Photos (optional, max 5)</label>
                {previews.length > 0 && (
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
                    {previews.map((src, i) => (
                      <div key={i} style={{ position: 'relative' }}>
                        <img
                          src={src}
                          alt={`preview ${i + 1}`}
                          style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--clr-border)' }}
                        />
                        <button
                          type="button"
                          onClick={() => removePhoto(i)}
                          style={{ position: 'absolute', top: '-6px', right: '-6px', background: 'var(--clr-primary)', color: '#fff', border: 'none', borderRadius: '50%', width: '20px', height: '20px', cursor: 'pointer', fontSize: '0.75rem', lineHeight: 1 }}
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                {photos.length < 5 && (
                  <>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={() => photoInputRef.current?.click()}
                    >
                      <Camera size={15} /> Add Photos
                    </button>
                    <input
                      ref={photoInputRef}
                      type="file"
                      accept="image/*"
                      multiple
                      style={{ display: 'none' }}
                      onChange={handlePhotoSelect}
                    />
                  </>
                )}
              </div>

              <div style={{ display: 'flex', gap: 'var(--sp-md)', marginTop: 'var(--sp-lg)' }}>
                <button type="submit" className="btn btn-primary btn-lg" disabled={submitting} id="review-submit">
                  {submitting ? 'Submitting...' : <><PenLine size={15} /> Submit Review</>}
                </button>
                <button type="button" className="btn btn-ghost btn-lg" onClick={() => navigate(-1)}>
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

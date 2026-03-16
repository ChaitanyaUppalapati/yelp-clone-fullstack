// components/StarRating.jsx — Dual-mode star rating component
import { useState } from 'react';

export default function StarRating({
  rating = 0,
  maxStars = 5,
  interactive = false,
  onChange,
  size = '1.125rem',
}) {
  const [hoverRating, setHoverRating] = useState(0);

  const displayRating = interactive && hoverRating ? hoverRating : rating;

  return (
    <div className="stars" style={{ fontSize: size }}>
      {Array.from({ length: maxStars }, (_, i) => {
        const starValue = i + 1;
        const isFilled = starValue <= Math.round(displayRating);

        return (
          <span
            key={i}
            className={`star ${isFilled ? 'filled' : ''} ${interactive ? 'interactive' : ''}`}
            onClick={interactive ? () => onChange?.(starValue) : undefined}
            onMouseEnter={interactive ? () => setHoverRating(starValue) : undefined}
            onMouseLeave={interactive ? () => setHoverRating(0) : undefined}
            role={interactive ? 'button' : undefined}
            aria-label={interactive ? `Rate ${starValue} stars` : `${starValue} star`}
          >
            ★
          </span>
        );
      })}
    </div>
  );
}

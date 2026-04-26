import re
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import require_owner, get_current_user
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.restaurant import RestaurantOut, RestaurantUpdate, RestaurantListOut
from app.schemas.review import ReviewOut

router = APIRouter()

POSITIVE_SENTIMENT_TERMS = {
    "amazing", "awesome", "attentive", "best", "clean", "cozy", "delicious",
    "excellent", "exceptional", "fantastic", "favorite", "flavorful", "fresh",
    "friendly", "great", "impeccable", "impressed", "incredible", "love",
    "loved", "lovely", "perfect", "phenomenal", "quick", "recommend",
    "satisfying", "stellar", "superb", "tasty", "warm", "wonderful",
}
NEGATIVE_SENTIMENT_TERMS = {
    "awful", "bad", "bland", "cold", "confusing", "crowded", "disappointing",
    "dirty", "dry", "expensive", "forgetful", "greasy", "hate", "horrible",
    "mediocre", "noisy", "overpriced", "rude", "salty", "slow", "stale",
    "terrible", "tough", "underwhelming", "unfriendly", "worst",
}
THEME_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "had", "has", "have", "i", "if", "in", "is", "it", "its", "my", "of",
    "on", "or", "our", "so", "that", "the", "their", "them", "there", "this",
    "to", "too", "very", "was", "we", "were", "with", "you", "your",
}


def _tokenize_review_text(text: str) -> list[str]:
    return re.findall(r"[a-z']+", (text or "").lower())


def _sentiment_label(score: float) -> str:
    if score >= 0.2:
        return "positive"
    if score <= -0.2:
        return "negative"
    return "neutral"


def _analyze_review_sentiment(review: Review) -> tuple[float, str, list[str], list[str]]:
    tokens = _tokenize_review_text(review.comment or "")
    positive_hits = [token for token in tokens if token in POSITIVE_SENTIMENT_TERMS]
    negative_hits = [token for token in tokens if token in NEGATIVE_SENTIMENT_TERMS]

    matched_terms = len(positive_hits) + len(negative_hits)
    lexical_score = (
        (len(positive_hits) - len(negative_hits)) / matched_terms
        if matched_terms
        else 0.0
    )
    rating_score = ((review.rating or 3) - 3) / 2
    score = round((lexical_score * 0.7) + (rating_score * 0.3), 2)
    return score, _sentiment_label(score), positive_hits, negative_hits


def _summarize_sentiment(reviews: list[Review], restaurant_name_map: dict[int, str]) -> dict:
    distribution = {"positive": 0, "neutral": 0, "negative": 0}
    positive_terms = Counter()
    negative_terms = Counter()
    scores: list[float] = []
    per_restaurant: dict[int, dict] = {}

    for review in reviews:
        score, label, positive_hits, negative_hits = _analyze_review_sentiment(review)
        distribution[label] += 1
        scores.append(score)
        positive_terms.update(
            token for token in positive_hits if token not in THEME_STOPWORDS and len(token) > 2
        )
        negative_terms.update(
            token for token in negative_hits if token not in THEME_STOPWORDS and len(token) > 2
        )

        restaurant_summary = per_restaurant.setdefault(
            review.restaurant_id,
            {
                "restaurant_id": review.restaurant_id,
                "restaurant_name": restaurant_name_map.get(review.restaurant_id, "Unknown"),
                "review_count": 0,
                "scores": [],
            },
        )
        restaurant_summary["review_count"] += 1
        restaurant_summary["scores"].append(score)

    average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    restaurant_breakdown = []
    for summary in per_restaurant.values():
        avg_score = round(sum(summary["scores"]) / len(summary["scores"]), 2)
        restaurant_breakdown.append({
            "restaurant_id": summary["restaurant_id"],
            "restaurant_name": summary["restaurant_name"],
            "review_count": summary["review_count"],
            "average_score": avg_score,
            "label": _sentiment_label(avg_score),
        })

    restaurant_breakdown.sort(key=lambda item: (-item["review_count"], item["restaurant_name"]))

    return {
        "overall_label": _sentiment_label(average_score),
        "average_score": average_score,
        "distribution": distribution,
        "total_reviews_analyzed": len(scores),
        "top_positive_themes": [
            {"term": term, "count": count}
            for term, count in positive_terms.most_common(5)
        ],
        "top_negative_themes": [
            {"term": term, "count": count}
            for term, count in negative_terms.most_common(5)
        ],
        "restaurant_breakdown": restaurant_breakdown,
    }


@router.put("/claim/{restaurant_id}", response_model=RestaurantOut, summary="Claim an existing restaurant listing")
def claim_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Claim an existing restaurant listing as the owner."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only restaurant owners can claim listings")
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id, Restaurant.is_active == True).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You already own this restaurant")
    r.owner_id = current_user.id
    db.commit()
    db.refresh(r)
    return r


@router.get("/analytics", summary="Get analytics for all owned restaurants")
def owner_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return analytics for all restaurants owned by the current user."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")

    restaurants = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    if not restaurants:
        return {"total_restaurants": 0, "total_reviews": 0, "avg_rating": 0.0,
                "ratings_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                "recent_reviews": [],
                "sentiment_analysis": {
                    "overall_label": "neutral",
                    "average_score": 0.0,
                    "distribution": {"positive": 0, "neutral": 0, "negative": 0},
                    "total_reviews_analyzed": 0,
                    "top_positive_themes": [],
                    "top_negative_themes": [],
                    "restaurant_breakdown": [],
                }}

    rest_ids = [r.id for r in restaurants]

    # Ratings distribution across all owned restaurants
    all_reviews = (
        db.query(Review)
        .filter(Review.restaurant_id.in_(rest_ids))
        .order_by(Review.created_at.desc())
        .all()
    )

    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rev in all_reviews:
        distribution[rev.rating] = distribution.get(rev.rating, 0) + 1

    total_reviews = len(all_reviews)
    avg_rating = (
        round(sum(r.rating for r in all_reviews) / total_reviews, 2) if total_reviews else 0.0
    )

    # Recent reviews (last 10 across all owned restaurants)
    recent = []
    rest_name_map = {r.id: r.name for r in restaurants}
    for rev in all_reviews[:10]:
        recent.append({
            "id": rev.id,
            "restaurant_id": rev.restaurant_id,
            "restaurant_name": rest_name_map.get(rev.restaurant_id, "Unknown"),
            "rating": rev.rating,
            "comment": rev.comment,
            "created_at": rev.created_at.isoformat() if rev.created_at else None,
        })

    return {
        "total_restaurants": len(restaurants),
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
        "ratings_distribution": distribution,
        "recent_reviews": recent,
        "sentiment_analysis": _summarize_sentiment(all_reviews, rest_name_map),
    }


@router.get("/restaurants", response_model=list[RestaurantListOut], summary="List restaurants you own")
def owner_restaurants(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """List all restaurants owned by the authenticated user."""
    return (
        db.query(Restaurant)
        .filter(Restaurant.owner_id == current_user.id)
        .all()
    )


@router.put("/restaurants/{restaurant_id}", response_model=RestaurantOut, summary="Update a restaurant you own")
def update_restaurant(
    restaurant_id: int,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """Update a restaurant you own."""
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the owner of this restaurant")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(r, field, value)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate (soft-delete) a restaurant you own")
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """Soft-delete (deactivate) a restaurant you own."""
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the owner of this restaurant")
    r.is_active = False
    db.commit()


@router.get("/dashboard", summary="Owner analytics dashboard")
def owner_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """Analytics dashboard for the owner's restaurants."""
    restaurants = (
        db.query(Restaurant)
        .filter(Restaurant.owner_id == current_user.id)
        .all()
    )
    restaurant_ids = [r.id for r in restaurants]

    if not restaurant_ids:
        return {
            "restaurant_count": 0,
            "total_reviews": 0,
            "overall_avg_rating": 0.0,
            "rating_distribution": {str(i): 0 for i in range(1, 6)},
            "restaurants": [],
            "recent_reviews": [],
        }

    # Total reviews + overall avg across all owned restaurants
    stats = (
        db.query(
            func.count(Review.id).label("total_reviews"),
            func.avg(Review.rating).label("overall_avg"),
        )
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .one()
    )

    # Rating distribution (1-5 star counts)
    dist_rows = (
        db.query(Review.rating, func.count(Review.id).label("cnt"))
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .group_by(Review.rating)
        .all()
    )
    distribution = {str(i): 0 for i in range(1, 6)}
    for row in dist_rows:
        distribution[str(row.rating)] = row.cnt

    # 5 most recent reviews
    recent = (
        db.query(Review)
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )

    # Per-restaurant summary
    restaurant_summaries = [
        {
            "id": r.id,
            "name": r.name,
            "avg_rating": float(r.avg_rating),
            "review_count": r.review_count,
            "is_active": r.is_active,
        }
        for r in restaurants
    ]

    return {
        "restaurant_count": len(restaurants),
        "total_reviews": stats.total_reviews or 0,
        "overall_avg_rating": round(float(stats.overall_avg or 0), 2),
        "rating_distribution": distribution,
        "restaurants": restaurant_summaries,
        "recent_reviews": [
            {
                "id": rv.id,
                "restaurant_id": rv.restaurant_id,
                "user_id": rv.user_id,
                "rating": rv.rating,
                "comment": rv.comment,
                "created_at": rv.created_at,
            }
            for rv in recent
        ],
    }


@router.get("/reviews", response_model=list[ReviewOut], summary="List all reviews for your restaurants")
def owner_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """Paginated list of all reviews for the owner's restaurants."""
    restaurant_ids = [
        r.id
        for r in db.query(Restaurant.id)
        .filter(Restaurant.owner_id == current_user.id)
        .all()
    ]
    if not restaurant_ids:
        return []
    return (
        db.query(Review)
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

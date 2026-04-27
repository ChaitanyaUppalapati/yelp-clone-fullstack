import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.auth import get_token_user_id
from shared.database import get_db
from shared.kafka_producer import publish

router = APIRouter()


async def _require_owner(user_id: str = Depends(get_token_user_id)) -> str:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or user.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")
    return user_id


@router.put("/claim/{restaurant_id}")
async def claim_restaurant(restaurant_id: str, user_id: str = Depends(_require_owner)):
    db = get_db()
    r = await db.restaurants.find_one({"_id": ObjectId(restaurant_id), "is_active": True})
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.get("owner_id") == user_id:
        raise HTTPException(status_code=400, detail="You already own this restaurant")

    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$set": {"owner_id": user_id}},
    )
    publish("restaurant.claimed", {"restaurant_id": restaurant_id, "new_owner_id": user_id})
    updated = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    updated["id"] = str(updated.pop("_id"))
    return updated


@router.get("/restaurants")
async def owner_restaurants(user_id: str = Depends(_require_owner)):
    db = get_db()
    cursor = db.restaurants.find({"owner_id": user_id})
    results = []
    async for r in cursor:
        r["id"] = str(r.pop("_id"))
        results.append(r)
    return results


@router.put("/restaurants/{restaurant_id}")
async def update_restaurant(
    restaurant_id: str,
    payload: dict,
    user_id: str = Depends(_require_owner),
):
    db = get_db()
    r = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.get("owner_id") != user_id:
        raise HTTPException(status_code=403, detail="Not the owner of this restaurant")

    # Strip protected fields
    payload.pop("_id", None)
    payload.pop("id", None)
    payload.pop("owner_id", None)
    payload.pop("added_by", None)

    await db.restaurants.update_one({"_id": ObjectId(restaurant_id)}, {"$set": payload})
    publish("restaurant.updated", {"restaurant_id": restaurant_id, "owner_id": user_id})
    updated = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    updated["id"] = str(updated.pop("_id"))
    return updated


@router.delete("/restaurants/{restaurant_id}", status_code=204)
async def delete_restaurant(restaurant_id: str, user_id: str = Depends(_require_owner)):
    db = get_db()
    r = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.get("owner_id") != user_id:
        raise HTTPException(status_code=403, detail="Not the owner of this restaurant")
    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$set": {"is_active": False}},
    )


STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","was","it","i","we","they","this","that","my","our","very","so",
    "be","have","had","not","by","from","are","were","its","been","their",
    "as","if","up","out","no","just","he","she","me","him","her","would",
    "could","did","do","get","got","all","one","more","also","too","than",
    "there","has","will","went","even","really","then","about","can","us",
}

def _rating_to_score(rating: int) -> float:
    return {1: -1.0, 2: -0.5, 3: 0.0, 4: 0.5, 5: 1.0}.get(rating, 0.0)

def _rating_to_label(rating: int) -> str:
    if rating >= 4: return "positive"
    if rating <= 2: return "negative"
    return "neutral"

def _top_words(comments: list[str], n: int = 6) -> list[dict]:
    freq: dict[str, int] = {}
    for text in comments:
        for word in text.lower().split():
            w = "".join(c for c in word if c.isalpha())
            if len(w) > 3 and w not in STOPWORDS:
                freq[w] = freq.get(w, 0) + 1
    return [{"term": t, "count": c} for t, c in sorted(freq.items(), key=lambda x: -x[1])[:n]]


@router.get("/analytics")
async def owner_analytics(user_id: str = Depends(_require_owner)):
    db = get_db()
    restaurants = await db.restaurants.find({"owner_id": user_id}).to_list(None)
    if not restaurants:
        return {
            "total_restaurants": 0, "total_reviews": 0, "avg_rating": 0.0,
            "ratings_distribution": {str(i): 0 for i in range(1, 6)},
            "recent_reviews": [], "sentiment_analysis": None,
        }

    rest_ids = [str(r["_id"]) for r in restaurants]
    rest_name_map = {str(r["_id"]): r["name"] for r in restaurants}

    all_reviews = await db.reviews.find(
        {"restaurant_id": {"$in": rest_ids}}
    ).sort("created_at", -1).to_list(None)

    distribution = {str(i): 0 for i in range(1, 6)}
    for rev in all_reviews:
        key = str(int(rev.get("rating", 0)))
        if key in distribution:
            distribution[key] += 1

    total = len(all_reviews)
    avg = round(sum(r.get("rating", 0) for r in all_reviews) / total, 2) if total else 0.0

    recent = []
    for rev in all_reviews[:10]:
        recent.append({
            "id": str(rev["_id"]),
            "restaurant_id": rev["restaurant_id"],
            "restaurant_name": rest_name_map.get(rev["restaurant_id"], "Unknown"),
            "rating": rev.get("rating"),
            "comment": rev.get("comment"),
            "created_at": rev.get("created_at"),
        })

    # Sentiment analysis
    pos_comments, neg_comments = [], []
    sentiment_dist = {"positive": 0, "neutral": 0, "negative": 0}
    scores = []
    per_restaurant: dict[str, dict] = {rid: {"scores": [], "comments_pos": [], "comments_neg": []} for rid in rest_ids}

    for rev in all_reviews:
        rating = int(rev.get("rating", 3))
        score = _rating_to_score(rating)
        label = _rating_to_label(rating)
        comment = rev.get("comment") or ""
        rid = rev.get("restaurant_id", "")

        scores.append(score)
        sentiment_dist[label] += 1
        if label == "positive" and comment:
            pos_comments.append(comment)
        elif label == "negative" and comment:
            neg_comments.append(comment)

        if rid in per_restaurant:
            per_restaurant[rid]["scores"].append(score)
            if label == "positive" and comment:
                per_restaurant[rid]["comments_pos"].append(comment)
            elif label == "negative" and comment:
                per_restaurant[rid]["comments_neg"].append(comment)

    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    if avg_score >= 0.2:
        overall_label = "positive"
    elif avg_score <= -0.2:
        overall_label = "negative"
    else:
        overall_label = "neutral"

    restaurant_breakdown = []
    for rid, data in per_restaurant.items():
        if not data["scores"]:
            continue
        rs = round(sum(data["scores"]) / len(data["scores"]), 2)
        restaurant_breakdown.append({
            "restaurant_id": rid,
            "restaurant_name": rest_name_map.get(rid, "Unknown"),
            "label": "positive" if rs >= 0.2 else ("negative" if rs <= -0.2 else "neutral"),
            "average_score": rs,
            "review_count": len(data["scores"]),
        })

    sentiment_analysis = {
        "overall_label": overall_label,
        "average_score": avg_score,
        "total_reviews_analyzed": total,
        "distribution": sentiment_dist,
        "top_positive_themes": _top_words(pos_comments),
        "top_negative_themes": _top_words(neg_comments),
        "restaurant_breakdown": sorted(restaurant_breakdown, key=lambda x: -x["average_score"]),
    }

    return {
        "total_restaurants": len(restaurants),
        "total_reviews": total,
        "avg_rating": avg,
        "ratings_distribution": distribution,
        "recent_reviews": recent,
        "sentiment_analysis": sentiment_analysis,
    }


@router.get("/dashboard")
async def owner_dashboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    user_id: str = Depends(_require_owner),
):
    db = get_db()
    restaurants = await db.restaurants.find({"owner_id": user_id}).to_list(None)
    rest_ids = [str(r["_id"]) for r in restaurants]

    if not rest_ids:
        return {
            "restaurant_count": 0,
            "total_reviews": 0,
            "overall_avg_rating": 0.0,
            "rating_distribution": {str(i): 0 for i in range(1, 6)},
            "restaurants": [],
            "recent_reviews": [],
        }

    all_reviews = await db.reviews.find(
        {"restaurant_id": {"$in": rest_ids}}
    ).sort("created_at", -1).to_list(None)

    distribution = {str(i): 0 for i in range(1, 6)}
    for rev in all_reviews:
        key = str(int(rev.get("rating", 0)))
        if key in distribution:
            distribution[key] += 1

    total = len(all_reviews)
    overall_avg = round(sum(r.get("rating", 0) for r in all_reviews) / total, 2) if total else 0.0

    restaurant_summaries = [
        {
            "id": str(r["_id"]),
            "name": r["name"],
            "avg_rating": float(r.get("avg_rating") or 0),
            "review_count": r.get("review_count") or 0,
            "is_active": r.get("is_active", True),
        }
        for r in restaurants
    ]

    recent_reviews = [
        {
            "id": str(rv["_id"]),
            "restaurant_id": rv["restaurant_id"],
            "user_id": rv.get("user_id"),
            "rating": rv.get("rating"),
            "comment": rv.get("comment"),
            "created_at": rv.get("created_at"),
        }
        for rv in all_reviews[:5]
    ]

    return {
        "restaurant_count": len(restaurants),
        "total_reviews": total,
        "overall_avg_rating": overall_avg,
        "rating_distribution": distribution,
        "restaurants": restaurant_summaries,
        "recent_reviews": recent_reviews,
    }


@router.get("/reviews")
async def owner_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    user_id: str = Depends(_require_owner),
):
    db = get_db()
    rest_ids = [
        str(r["_id"])
        async for r in db.restaurants.find({"owner_id": user_id}, {"_id": 1})
    ]
    if not rest_ids:
        return []

    cursor = db.reviews.find(
        {"restaurant_id": {"$in": rest_ids}}
    ).sort("created_at", -1).skip(skip).limit(limit)

    results = []
    async for rev in cursor:
        rev["id"] = str(rev.pop("_id"))
        results.append(rev)
    return results

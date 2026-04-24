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


@router.get("/analytics")
async def owner_analytics(user_id: str = Depends(_require_owner)):
    db = get_db()
    restaurants = await db.restaurants.find({"owner_id": user_id}).to_list(None)
    if not restaurants:
        return {
            "total_restaurants": 0, "total_reviews": 0, "avg_rating": 0.0,
            "ratings_distribution": {str(i): 0 for i in range(1, 6)},
            "recent_reviews": [],
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

    return {
        "total_restaurants": len(restaurants),
        "total_reviews": total,
        "avg_rating": avg,
        "ratings_distribution": distribution,
        "recent_reviews": recent,
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

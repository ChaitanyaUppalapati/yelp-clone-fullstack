import asyncio, bcrypt, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

PW_HASH = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()

async def seed():
    client = AsyncIOMotorClient("mongodb://localhost:27017/yelp_db")
    db = client.yelp_db

    await db.users.delete_many({"email": {"$regex": "^jmeter_user_"}})
    await db.restaurants.delete_many({"name": {"$regex": "^JMeter Restaurant "}})
    await db.reviews.delete_many({"comment": "Load test review"})

    users = []
    for i in range(1, 501):
        users.append({
            "name": f"JMeter User {i}",
            "email": f"jmeter_user_{i}@test.com",
            "password_hash": PW_HASH,
            "role": "user",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "profile_picture": None, "about_me": None,
            "languages": None, "gender": None,
        })
    result = await db.users.insert_many(users)
    user_ids = [str(i) for i in result.inserted_ids]
    print(f"Seeded {len(user_ids)} users")

    restaurants = []
    for i in range(1, 501):
        restaurants.append({
            "name": f"JMeter Restaurant {i}",
            "cuisine_type": "American",
            "city": "San Jose", "state": "CA",
            "zip_code": "95101", "address": f"{i} Test St",
            "description": "Load test restaurant",
            "pricing_tier": 2, "avg_rating": 0.0, "review_count": 0,
            "is_active": True, "photos": [],
            "owner_id": user_ids[i - 1],
            "added_by": user_ids[i - 1],
            "created_at": datetime.now(timezone.utc),
        })
    r_result = await db.restaurants.insert_many(restaurants)
    rest_ids = [str(i) for i in r_result.inserted_ids]
    print(f"Seeded {len(rest_ids)} restaurants")

    with open(os.path.join(os.path.dirname(__file__), "users.csv"), "w") as f:
        f.write("email,password,restaurant_id\n")
        for i in range(500):
            f.write(f"jmeter_user_{i+1}@test.com,password123,{rest_ids[i]}\n")
    print("Written jmeter/users.csv")
    client.close()

asyncio.run(seed())

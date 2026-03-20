"""
seed_reviews.py — Populate reviews table with realistic fake data,
then recompute avg_rating and review_count for every restaurant.

Run from the backend/ directory:
    python seed_reviews.py
"""

import random
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

# ---------------------------------------------------------------------------
# Comments keyed by rating (1-5)
# ---------------------------------------------------------------------------
COMMENTS = {
    1: [
        "Extremely disappointed. The food was cold and the service was rude.",
        "Worst dining experience I've had in years. Will not be returning.",
        "Waited over an hour for mediocre food. Completely unacceptable.",
        "The place looks nice but the quality is far below expectations.",
        "Overpriced and underwhelming. The kitchen clearly needs work.",
    ],
    2: [
        "Food was okay but nothing special. Service could be a lot better.",
        "Average at best. I've had much better for a similar price.",
        "Decent enough but I wouldn't rush back. Too many small issues.",
        "The appetizers were okay; main course was bland and forgettable.",
        "Not terrible, but not worth the trip or the price either.",
    ],
    3: [
        "Solid spot with good flavors. Service was friendly but slow.",
        "Pretty good overall — a reliable choice for a casual meal.",
        "Enjoyable experience. Nothing blew me away but I'd come back.",
        "Good food and a pleasant atmosphere. A bit pricey for what it is.",
        "Tasty dishes and attentive staff. Worth trying at least once.",
    ],
    4: [
        "Really enjoyed our evening here. Great food and warm service.",
        "Excellent flavors and a beautiful presentation. Highly recommend.",
        "One of my favorite spots in the area. Always consistent.",
        "The portions are generous and everything we ordered was delicious.",
        "Fantastic ambiance and top-notch cuisine. Will definitely return.",
    ],
    5: [
        "Absolutely phenomenal. Every dish was perfectly executed — a must-visit!",
        "Best meal I've had all year. The chef clearly knows their craft.",
        "Flawless from start to finish. Impeccable service and stunning food.",
        "A hidden gem that deserves far more attention. We'll be back weekly.",
        "Outstanding in every way. This is what fine dining should feel like.",
    ],
}

FIRST_NAMES = [
    "Alex", "Jordan", "Morgan", "Taylor", "Casey", "Riley", "Quinn", "Avery",
    "Blake", "Cameron", "Drew", "Emerson", "Finley", "Harper", "Hayden",
    "Jamie", "Kendall", "Logan", "Madison", "Peyton", "Reese", "Rowan",
    "Sage", "Skylar", "Spencer", "Sydney", "Tatum", "Tyler", "Whitney", "Zara",
]
LAST_NAMES = [
    "Anderson", "Brown", "Clark", "Davis", "Evans", "Foster", "Garcia",
    "Hall", "Harris", "Jackson", "Johnson", "Jones", "King", "Lee", "Lewis",
    "Martin", "Martinez", "Miller", "Moore", "Nelson", "Parker", "Patel",
    "Robinson", "Rodriguez", "Smith", "Taylor", "Thomas", "Thompson", "White", "Wilson",
]


def ratings_for_target(target_avg: float, n: int) -> list[int]:
    """Return n integer ratings (1-5) whose mean is close to target_avg."""
    ratings = []
    current_sum = 0
    for i in range(n):
        remaining = n - i
        needed = target_avg * (remaining + len(ratings)) - current_sum
        ideal = needed / remaining
        low = max(1, round(ideal) - 1)
        high = min(5, round(ideal) + 1)
        r = int(round(min(5, max(1, random.uniform(low, high)))))
        ratings.append(r)
        current_sum += r
    random.shuffle(ratings)
    return ratings


def main():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # ------------------------------------------------------------------ #
        # 1. Fetch all restaurants                                            #
        # ------------------------------------------------------------------ #
        restaurants = db.execute(text("SELECT id, name, avg_rating FROM restaurants")).fetchall()
        if not restaurants:
            print("No restaurants found — run schema.sql first.")
            return
        print(f"Found {len(restaurants)} restaurants.")

        # ------------------------------------------------------------------ #
        # 2. Create seed reviewer accounts (skip if email already exists)     #
        # ------------------------------------------------------------------ #
        NUM_REVIEWERS = 40
        reviewer_ids = []
        hashed_pw = bcrypt.hashpw(b"Password123!", bcrypt.gensalt()).decode()

        for i in range(NUM_REVIEWERS):
            first = random.choice(FIRST_NAMES)
            last  = random.choice(LAST_NAMES)
            email = f"reviewer{i+1}@seed.local"
            name  = f"{first} {last}"

            existing = db.execute(
                text("SELECT id FROM users WHERE email = :e"), {"e": email}
            ).fetchone()

            if existing:
                reviewer_ids.append(existing.id)
            else:
                db.execute(text(
                    "INSERT INTO users (email, password_hash, name, role) "
                    "VALUES (:email, :pw, :name, 'user')"
                ), {"email": email, "pw": hashed_pw, "name": name})
                db.flush()
                row = db.execute(
                    text("SELECT id FROM users WHERE email = :e"), {"e": email}
                ).fetchone()
                reviewer_ids.append(row.id)

        db.commit()
        print(f"Seeded / verified {len(reviewer_ids)} reviewer accounts.")

        # ------------------------------------------------------------------ #
        # 3. Insert reviews for each restaurant                               #
        # ------------------------------------------------------------------ #
        reviews_per_restaurant = min(len(reviewer_ids), 30)

        for rest in restaurants:
            rest_id     = rest.id
            target_avg  = float(rest.avg_rating or 4.0)

            # Pick a fresh set of reviewers for this restaurant
            chosen_ids = random.sample(reviewer_ids, reviews_per_restaurant)
            ratings    = ratings_for_target(target_avg, reviews_per_restaurant)

            inserted = 0
            for user_id, rating in zip(chosen_ids, ratings):
                # Enforce unique constraint — skip if already reviewed
                exists = db.execute(text(
                    "SELECT 1 FROM reviews WHERE user_id=:u AND restaurant_id=:r"
                ), {"u": user_id, "r": rest_id}).fetchone()
                if exists:
                    continue

                comment = random.choice(COMMENTS[rating])
                days_ago = random.randint(1, 700)

                db.execute(text(
                    "INSERT INTO reviews (user_id, restaurant_id, rating, comment, created_at, updated_at) "
                    "VALUES (:u, :r, :rating, :comment, "
                    "DATE_SUB(NOW(), INTERVAL :days DAY), "
                    "DATE_SUB(NOW(), INTERVAL :days DAY))"
                ), {
                    "u": user_id, "r": rest_id,
                    "rating": rating, "comment": comment, "days": days_ago,
                })
                inserted += 1

            db.flush()
            print(f"  {rest.name}: inserted {inserted} reviews (target avg {target_avg})")

        db.commit()

        # ------------------------------------------------------------------ #
        # 4. Recompute avg_rating and review_count from actual data           #
        # ------------------------------------------------------------------ #
        print("\nRecomputing aggregates from actual review data...")
        db.execute(text("""
            UPDATE restaurants r
            JOIN (
                SELECT restaurant_id,
                       COUNT(*)        AS cnt,
                       ROUND(AVG(rating), 2) AS avg
                FROM reviews
                GROUP BY restaurant_id
            ) agg ON agg.restaurant_id = r.id
            SET r.review_count = agg.cnt,
                r.avg_rating   = agg.avg
        """))
        db.commit()

        # Print final state
        rows = db.execute(text(
            "SELECT name, review_count, avg_rating FROM restaurants ORDER BY avg_rating DESC"
        )).fetchall()
        print("\nFinal state:")
        print(f"{'Restaurant':<35} {'Reviews':>8} {'Avg':>6}")
        print("-" * 52)
        for row in rows:
            print(f"{row.name:<35} {row.review_count:>8} {float(row.avg_rating):>6.2f}")

        print("\nDone!")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    main()

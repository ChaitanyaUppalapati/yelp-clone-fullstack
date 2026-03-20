"""
seed_restaurants.py — Insert diverse restaurants from across the US,
then seed reviews for any restaurant that has none.

Run from backend/:
    python seed_restaurants.py
"""

import random
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

NEW_RESTAURANTS = [
    # ── New York, NY ────────────────────────────────────────────────────────
    {
        "name": "Carbone",
        "cuisine_type": "Italian",
        "description": "Old-school Italian-American red-sauce joint with a modern fine-dining twist in Greenwich Village.",
        "address_line": "181 Thompson St",
        "city": "New York", "state": "NY", "zip_code": "10012",
        "lat": 40.7275, "lon": -74.0005,
        "phone": "(212) 254-3000", "website": "https://carbonenewyork.com",
        "hours": '{"mon":"17:30-23:00","tue":"17:30-23:00","wed":"17:30-23:00","thu":"17:30-23:00","fri":"17:30-23:30","sat":"17:30-23:30","sun":"17:30-22:00"}',
        "pricing_tier": 4, "amenities": '["reservations","bar","wheelchair_accessible"]',
        "avg_rating": 4.6,
    },
    {
        "name": "Katz's Delicatessen",
        "cuisine_type": "American",
        "description": "Legendary Lower East Side deli serving pastrami and corned beef sandwiches since 1888.",
        "address_line": "205 E Houston St",
        "city": "New York", "state": "NY", "zip_code": "10002",
        "lat": 40.7223, "lon": -73.9873,
        "phone": "(212) 254-2246", "website": "https://katzsdelicatessen.com",
        "hours": '{"mon":"08:00-22:45","tue":"08:00-22:45","wed":"08:00-22:45","thu":"08:00-22:45","fri":"08:00-02:45","sat":"08:00-02:45","sun":"08:00-22:45"}',
        "pricing_tier": 2, "amenities": '["takeout","wheelchair_accessible"]',
        "avg_rating": 4.5,
    },
    {
        "name": "Le Bernardin",
        "cuisine_type": "French",
        "description": "Michelin three-star seafood temple from chef Éric Ripert in Midtown Manhattan.",
        "address_line": "155 W 51st St",
        "city": "New York", "state": "NY", "zip_code": "10019",
        "lat": 40.7617, "lon": -73.9814,
        "phone": "(212) 554-1515", "website": "https://le-bernardin.com",
        "hours": '{"mon":"12:00-14:30","tue":"12:00-14:30","wed":"12:00-14:30","thu":"12:00-14:30","fri":"12:00-14:30","sat":"17:00-22:30","sun":"closed"}',
        "pricing_tier": 4, "amenities": '["reservations","bar","private_dining"]',
        "avg_rating": 4.8,
    },
    {
        "name": "Joe's Pizza",
        "cuisine_type": "American",
        "description": "Iconic Greenwich Village slice shop serving classic New York thin-crust pizza since 1975.",
        "address_line": "7 Carmine St",
        "city": "New York", "state": "NY", "zip_code": "10014",
        "lat": 40.7303, "lon": -74.0025,
        "phone": "(212) 366-1182", "website": "https://joespizzanyc.com",
        "hours": '{"mon":"10:00-04:00","tue":"10:00-04:00","wed":"10:00-04:00","thu":"10:00-04:00","fri":"10:00-05:00","sat":"10:00-05:00","sun":"10:00-04:00"}',
        "pricing_tier": 1, "amenities": '["takeout","wheelchair_accessible"]',
        "avg_rating": 4.4,
    },

    # ── Chicago, IL ─────────────────────────────────────────────────────────
    {
        "name": "Alinea",
        "cuisine_type": "American",
        "description": "Grant Achatz's avant-garde tasting menu experience — consistently rated among the world's best.",
        "address_line": "1723 N Halsted St",
        "city": "Chicago", "state": "IL", "zip_code": "60614",
        "lat": 41.9148, "lon": -87.6487,
        "phone": "(312) 867-0110", "website": "https://alinearestaurant.com",
        "hours": '{"mon":"closed","tue":"closed","wed":"17:00-21:00","thu":"17:00-21:00","fri":"17:00-21:00","sat":"17:00-21:00","sun":"closed"}',
        "pricing_tier": 4, "amenities": '["reservations"]',
        "avg_rating": 4.9,
    },
    {
        "name": "Lou Malnati's Pizzeria",
        "cuisine_type": "American",
        "description": "Chicago's beloved deep-dish institution, serving buttery crusts and chunky tomato sauce since 1971.",
        "address_line": "439 N Wells St",
        "city": "Chicago", "state": "IL", "zip_code": "60654",
        "lat": 41.8899, "lon": -87.6340,
        "phone": "(312) 828-9800", "website": "https://loumalnatis.com",
        "hours": '{"mon":"11:00-22:00","tue":"11:00-22:00","wed":"11:00-22:00","thu":"11:00-22:00","fri":"11:00-23:00","sat":"11:00-23:00","sun":"12:00-22:00"}',
        "pricing_tier": 2, "amenities": '["takeout","delivery","wheelchair_accessible"]',
        "avg_rating": 4.5,
    },
    {
        "name": "Girl & the Goat",
        "cuisine_type": "American",
        "description": "Stephanie Izard's West Loop flagship with bold shared plates and wood-fired flavors.",
        "address_line": "800 W Randolph St",
        "city": "Chicago", "state": "IL", "zip_code": "60607",
        "lat": 41.8843, "lon": -87.6477,
        "phone": "(312) 492-6262", "website": "https://girlandthegoat.com",
        "hours": '{"mon":"16:00-22:00","tue":"16:00-22:00","wed":"16:00-22:00","thu":"16:00-22:00","fri":"16:00-23:00","sat":"16:00-23:00","sun":"closed"}',
        "pricing_tier": 3, "amenities": '["reservations","bar","outdoor_seating"]',
        "avg_rating": 4.5,
    },

    # ── Austin, TX ──────────────────────────────────────────────────────────
    {
        "name": "Franklin Barbecue",
        "cuisine_type": "American",
        "description": "James Beard Award-winning pitmaster Aaron Franklin's legendary smoked brisket — worth every minute of the line.",
        "address_line": "900 E 11th St",
        "city": "Austin", "state": "TX", "zip_code": "78702",
        "lat": 30.2678, "lon": -97.7298,
        "phone": "(512) 653-1187", "website": "https://franklinbbq.com",
        "hours": '{"mon":"closed","tue":"11:00-15:00","wed":"11:00-15:00","thu":"11:00-15:00","fri":"11:00-15:00","sat":"11:00-15:00","sun":"11:00-15:00"}',
        "pricing_tier": 2, "amenities": '["outdoor_seating","takeout"]',
        "avg_rating": 4.8,
    },
    {
        "name": "Uchi",
        "cuisine_type": "Japanese",
        "description": "James Beard-winning sushi and Japanese small plates with creative Austin flair.",
        "address_line": "801 S Lamar Blvd",
        "city": "Austin", "state": "TX", "zip_code": "78704",
        "lat": 30.2537, "lon": -97.7682,
        "phone": "(512) 916-4808", "website": "https://uchiaustin.com",
        "hours": '{"mon":"17:00-22:00","tue":"17:00-22:00","wed":"17:00-22:00","thu":"17:00-22:00","fri":"17:00-23:00","sat":"17:00-23:00","sun":"17:00-22:00"}',
        "pricing_tier": 3, "amenities": '["reservations","bar"]',
        "avg_rating": 4.6,
    },

    # ── Seattle, WA ─────────────────────────────────────────────────────────
    {
        "name": "Canlis",
        "cuisine_type": "American",
        "description": "Seattle's storied fine-dining landmark with sweeping Lake Union views since 1950.",
        "address_line": "2576 Aurora Ave N",
        "city": "Seattle", "state": "WA", "zip_code": "98109",
        "lat": 47.6418, "lon": -122.3466,
        "phone": "(206) 283-3313", "website": "https://canlis.com",
        "hours": '{"mon":"closed","tue":"17:30-22:00","wed":"17:30-22:00","thu":"17:30-22:00","fri":"17:30-22:00","sat":"17:00-22:00","sun":"closed"}',
        "pricing_tier": 4, "amenities": '["reservations","bar","valet_parking"]',
        "avg_rating": 4.7,
    },
    {
        "name": "Pike Place Chowder",
        "cuisine_type": "American",
        "description": "Award-winning chowders steps from the famous Pike Place Market — the New England clam chowder is a must.",
        "address_line": "1530 Post Alley",
        "city": "Seattle", "state": "WA", "zip_code": "98101",
        "lat": 47.6093, "lon": -122.3421,
        "phone": "(206) 267-2537", "website": "https://pikeplacebowl.com",
        "hours": '{"mon":"10:00-17:00","tue":"10:00-17:00","wed":"10:00-17:00","thu":"10:00-17:00","fri":"10:00-17:00","sat":"09:00-17:00","sun":"09:00-17:00"}',
        "pricing_tier": 1, "amenities": '["takeout","outdoor_seating"]',
        "avg_rating": 4.5,
    },
    {
        "name": "Nue",
        "cuisine_type": "Mediterranean",
        "description": "Globally inspired small plates highlighting street foods from over 100 countries.",
        "address_line": "1519 14th Ave",
        "city": "Seattle", "state": "WA", "zip_code": "98122",
        "lat": 47.6136, "lon": -122.3175,
        "phone": "(206) 257-0312", "website": "https://nueseattle.com",
        "hours": '{"mon":"16:00-22:00","tue":"16:00-22:00","wed":"16:00-22:00","thu":"16:00-22:00","fri":"16:00-23:00","sat":"16:00-23:00","sun":"16:00-21:00"}',
        "pricing_tier": 2, "amenities": '["bar","outdoor_seating","reservations"]',
        "avg_rating": 4.3,
    },

    # ── Miami, FL ───────────────────────────────────────────────────────────
    {
        "name": "Versailles Restaurant",
        "cuisine_type": "Cuban",
        "description": "Miami's most famous Cuban restaurant, a Little Havana institution since 1971.",
        "address_line": "3555 SW 8th St",
        "city": "Miami", "state": "FL", "zip_code": "33135",
        "lat": 25.7653, "lon": -80.2499,
        "phone": "(305) 444-0240", "website": "https://versaillesrestaurant.com",
        "hours": '{"mon":"08:00-01:00","tue":"08:00-01:00","wed":"08:00-01:00","thu":"08:00-01:00","fri":"08:00-02:30","sat":"08:00-02:30","sun":"09:00-01:00"}',
        "pricing_tier": 2, "amenities": '["outdoor_seating","takeout","wheelchair_accessible"]',
        "avg_rating": 4.4,
    },
    {
        "name": "Zuma Miami",
        "cuisine_type": "Japanese",
        "description": "Sleek izakaya-inspired rooftop dining with panoramic Brickell skyline views.",
        "address_line": "270 Biscayne Blvd Way",
        "city": "Miami", "state": "FL", "zip_code": "33131",
        "lat": 25.7677, "lon": -80.1884,
        "phone": "(305) 577-0277", "website": "https://zumarestaurant.com",
        "hours": '{"mon":"12:00-15:00","tue":"12:00-15:00","wed":"12:00-15:00","thu":"12:00-15:00","fri":"12:00-16:00","sat":"12:30-16:00","sun":"12:30-15:30"}',
        "pricing_tier": 4, "amenities": '["reservations","bar","outdoor_seating","valet_parking"]',
        "avg_rating": 4.5,
    },

    # ── New Orleans, LA ─────────────────────────────────────────────────────
    {
        "name": "Dooky Chase's Restaurant",
        "cuisine_type": "American",
        "description": "Historic Creole institution in the Tremé neighborhood, a civil rights landmark since 1941.",
        "address_line": "2301 Orleans Ave",
        "city": "New Orleans", "state": "LA", "zip_code": "70119",
        "lat": 29.9727, "lon": -90.0791,
        "phone": "(504) 821-0600", "website": "https://dookychaserestaurant.com",
        "hours": '{"mon":"closed","tue":"11:00-15:00","wed":"11:00-15:00","thu":"11:00-15:00","fri":"11:00-15:00","sat":"closed","sun":"closed"}',
        "pricing_tier": 2, "amenities": '["reservations","wheelchair_accessible"]',
        "avg_rating": 4.5,
    },
    {
        "name": "Commander's Palace",
        "cuisine_type": "American",
        "description": "Iconic Garden District Creole landmark celebrated for jazz brunch and Creole classics.",
        "address_line": "1403 Washington Ave",
        "city": "New Orleans", "state": "LA", "zip_code": "70130",
        "lat": 29.9285, "lon": -90.0847,
        "phone": "(504) 899-8221", "website": "https://commanderspalace.com",
        "hours": '{"mon":"11:30-21:00","tue":"11:30-21:00","wed":"11:30-21:00","thu":"11:30-21:00","fri":"11:30-22:00","sat":"10:00-22:00","sun":"10:00-21:00"}',
        "pricing_tier": 4, "amenities": '["reservations","bar","outdoor_seating","private_dining"]',
        "avg_rating": 4.6,
    },

    # ── Boston, MA ──────────────────────────────────────────────────────────
    {
        "name": "Neptune Oyster",
        "cuisine_type": "American",
        "description": "Tiny North End seafood bar famous for buttery lobster rolls and impeccably fresh oysters.",
        "address_line": "63 Salem St",
        "city": "Boston", "state": "MA", "zip_code": "02113",
        "lat": 42.3639, "lon": -71.0554,
        "phone": "(617) 742-3474", "website": "https://neptuneoyster.com",
        "hours": '{"mon":"11:30-22:00","tue":"11:30-22:00","wed":"11:30-22:00","thu":"11:30-22:00","fri":"11:30-23:00","sat":"11:30-23:00","sun":"11:30-22:00"}',
        "pricing_tier": 3, "amenities": '["bar","outdoor_seating"]',
        "avg_rating": 4.6,
    },
    {
        "name": "O Ya",
        "cuisine_type": "Japanese",
        "description": "Intimate omakase with Japanese minimalism and New England ingredients in Downtown Boston.",
        "address_line": "9 East St",
        "city": "Boston", "state": "MA", "zip_code": "02111",
        "lat": 42.3524, "lon": -71.0567,
        "phone": "(617) 654-9900", "website": "https://oyarestaurantboston.com",
        "hours": '{"mon":"closed","tue":"17:30-21:30","wed":"17:30-21:30","thu":"17:30-21:30","fri":"17:30-22:00","sat":"17:30-22:00","sun":"closed"}',
        "pricing_tier": 4, "amenities": '["reservations","bar"]',
        "avg_rating": 4.7,
    },

    # ── Portland, OR ────────────────────────────────────────────────────────
    {
        "name": "Le Pigeon",
        "cuisine_type": "French",
        "description": "Gabriel Rucker's James Beard-winning bistro with inventive French-American cooking.",
        "address_line": "738 E Burnside St",
        "city": "Portland", "state": "OR", "zip_code": "97214",
        "lat": 45.5233, "lon": -122.6528,
        "phone": "(503) 546-8796", "website": "https://lepigeon.com",
        "hours": '{"mon":"closed","tue":"17:00-22:00","wed":"17:00-22:00","thu":"17:00-22:00","fri":"17:00-22:00","sat":"17:00-22:00","sun":"17:00-22:00"}',
        "pricing_tier": 3, "amenities": '["bar","reservations"]',
        "avg_rating": 4.6,
    },
    {
        "name": "Pok Pok",
        "cuisine_type": "Thai",
        "description": "Andy Ricker's Northern Thai street-food landmark that sparked a national obsession with Thai cooking.",
        "address_line": "3226 SE Division St",
        "city": "Portland", "state": "OR", "zip_code": "97202",
        "lat": 45.5043, "lon": -122.6320,
        "phone": "(503) 232-1387", "website": "https://pokpokpdx.com",
        "hours": '{"mon":"closed","tue":"17:00-22:00","wed":"17:00-22:00","thu":"17:00-22:00","fri":"17:00-22:00","sat":"17:00-22:00","sun":"17:00-22:00"}',
        "pricing_tier": 2, "amenities": '["outdoor_seating","bar"]',
        "avg_rating": 4.4,
    },

    # ── Nashville, TN ───────────────────────────────────────────────────────
    {
        "name": "Husk Nashville",
        "cuisine_type": "American",
        "description": "Sean Brock's temple to Southern cooking housed in a stunning Victorian mansion.",
        "address_line": "37 Rutledge St",
        "city": "Nashville", "state": "TN", "zip_code": "37210",
        "lat": 36.1544, "lon": -86.7743,
        "phone": "(615) 256-6565", "website": "https://husknashville.com",
        "hours": '{"mon":"17:00-22:00","tue":"17:00-22:00","wed":"17:00-22:00","thu":"17:00-22:00","fri":"11:30-22:30","sat":"10:00-22:30","sun":"10:00-21:00"}',
        "pricing_tier": 3, "amenities": '["reservations","bar","outdoor_seating","wheelchair_accessible"]',
        "avg_rating": 4.5,
    },
    {
        "name": "Prince's Hot Chicken",
        "cuisine_type": "American",
        "description": "The birthplace of Nashville hot chicken — fiery, crispy, iconic since the 1930s.",
        "address_line": "123 Ewing Dr",
        "city": "Nashville", "state": "TN", "zip_code": "37207",
        "lat": 36.2009, "lon": -86.7621,
        "phone": "(615) 226-9442", "website": "https://princeshotchicken.com",
        "hours": '{"mon":"closed","tue":"closed","wed":"12:00-22:00","thu":"12:00-22:00","fri":"12:00-04:00","sat":"12:00-04:00","sun":"12:00-22:00"}',
        "pricing_tier": 1, "amenities": '["takeout"]',
        "avg_rating": 4.4,
    },

    # ── Denver, CO ──────────────────────────────────────────────────────────
    {
        "name": "Snooze, an A.M. Eatery",
        "cuisine_type": "American",
        "description": "Wildly creative pancake flights and inventive breakfast cocktails at this beloved Denver brunch chain.",
        "address_line": "2262 Larimer St",
        "city": "Denver", "state": "CO", "zip_code": "80205",
        "lat": 39.7545, "lon": -104.9836,
        "phone": "(303) 297-0700", "website": "https://snoozeeatery.com",
        "hours": '{"mon":"06:30-14:30","tue":"06:30-14:30","wed":"06:30-14:30","thu":"06:30-14:30","fri":"06:30-14:30","sat":"06:30-14:30","sun":"06:30-14:30"}',
        "pricing_tier": 2, "amenities": '["outdoor_seating","wheelchair_accessible"]',
        "avg_rating": 4.3,
    },
    {
        "name": "Fruition Restaurant",
        "cuisine_type": "American",
        "description": "Chef Alex Seidel's intimate farm-to-table gem in Denver's Cherry Creek neighborhood.",
        "address_line": "1313 E 6th Ave",
        "city": "Denver", "state": "CO", "zip_code": "80218",
        "lat": 39.7268, "lon": -104.9697,
        "phone": "(303) 831-1962", "website": "https://fruitionrestaurant.com",
        "hours": '{"mon":"closed","tue":"17:00-21:30","wed":"17:00-21:30","thu":"17:00-21:30","fri":"17:00-22:00","sat":"17:00-22:00","sun":"closed"}',
        "pricing_tier": 3, "amenities": '["reservations","bar"]',
        "avg_rating": 4.5,
    },

    # ── Los Angeles, CA (not Bay Area) ──────────────────────────────────────
    {
        "name": "Nobu Los Angeles",
        "cuisine_type": "Japanese",
        "description": "Nobu Matsuhisa's flagship Japanese-Peruvian fusion — the restaurant that started a global empire.",
        "address_line": "903 N La Cienega Blvd",
        "city": "Los Angeles", "state": "CA", "zip_code": "90069",
        "lat": 34.0803, "lon": -118.3726,
        "phone": "(310) 657-5711", "website": "https://nobumatsuhisa.com",
        "hours": '{"mon":"17:45-22:15","tue":"17:45-22:15","wed":"17:45-22:15","thu":"17:45-22:15","fri":"17:45-23:00","sat":"17:45-23:00","sun":"17:45-22:15"}',
        "pricing_tier": 4, "amenities": '["reservations","bar"]',
        "avg_rating": 4.5,
    },
    {
        "name": "Bestia",
        "cuisine_type": "Italian",
        "description": "Rustic Italian charcuterie, hand-rolled pasta, and wood-roasted meats in the Arts District.",
        "address_line": "2121 E 7th Pl",
        "city": "Los Angeles", "state": "CA", "zip_code": "90021",
        "lat": 34.0361, "lon": -118.2258,
        "phone": "(213) 514-5724", "website": "https://bestiala.com",
        "hours": '{"mon":"17:30-23:00","tue":"17:30-23:00","wed":"17:30-23:00","thu":"17:30-23:00","fri":"17:30-00:00","sat":"17:30-00:00","sun":"17:30-23:00"}',
        "pricing_tier": 3, "amenities": '["reservations","bar","outdoor_seating"]',
        "avg_rating": 4.6,
    },
    {
        "name": "Gjusta",
        "cuisine_type": "Mediterranean",
        "description": "All-day Venice Beach deli and bakery with extraordinary house-cured meats and pastries.",
        "address_line": "320 Sunset Ave",
        "city": "Los Angeles", "state": "CA", "zip_code": "90291",
        "lat": 33.9974, "lon": -118.4716,
        "phone": "(310) 314-0320", "website": "https://gjusta.com",
        "hours": '{"mon":"07:00-21:00","tue":"07:00-21:00","wed":"07:00-21:00","thu":"07:00-21:00","fri":"07:00-21:00","sat":"07:00-21:00","sun":"07:00-21:00"}',
        "pricing_tier": 2, "amenities": '["outdoor_seating","takeout"]',
        "avg_rating": 4.5,
    },

    # ── Atlanta, GA ─────────────────────────────────────────────────────────
    {
        "name": "Bacchanalia",
        "cuisine_type": "American",
        "description": "Atlanta's most celebrated fine-dining destination — contemporary American cuisine in a converted warehouse.",
        "address_line": "1198 Howell Mill Rd NW",
        "city": "Atlanta", "state": "GA", "zip_code": "30318",
        "lat": 33.7876, "lon": -84.4138,
        "phone": "(404) 365-0410", "website": "https://starprovisions.com",
        "hours": '{"mon":"closed","tue":"closed","wed":"18:00-21:00","thu":"18:00-21:00","fri":"18:00-22:00","sat":"18:00-22:00","sun":"closed"}',
        "pricing_tier": 4, "amenities": '["reservations","bar"]',
        "avg_rating": 4.7,
    },
    {
        "name": "Slutty Vegan",
        "cuisine_type": "American",
        "description": "Atlanta's viral plant-based burger joint with outrageous names and phenomenal flavors.",
        "address_line": "1542 Ralph David Abernathy Blvd SW",
        "city": "Atlanta", "state": "GA", "zip_code": "30310",
        "lat": 33.7435, "lon": -84.4178,
        "phone": "(678) 500-6002", "website": "https://sluttyveganatl.com",
        "hours": '{"mon":"12:00-20:00","tue":"12:00-20:00","wed":"12:00-20:00","thu":"12:00-20:00","fri":"12:00-22:00","sat":"12:00-22:00","sun":"12:00-20:00"}',
        "pricing_tier": 1, "amenities": '["takeout","outdoor_seating"]',
        "avg_rating": 4.3,
    },
]

COMMENTS = {
    1: ["Extremely disappointed. Cold food and rude service.", "Worst dining experience I've had in years."],
    2: ["Average at best. Nothing special here.", "Decent enough but I wouldn't rush back."],
    3: ["Solid spot with good flavors. Service was friendly.", "Pretty good overall — a reliable choice."],
    4: ["Really enjoyed our evening here. Great food!", "Excellent flavors and beautiful presentation."],
    5: ["Absolutely phenomenal — a must-visit!", "Best meal I've had all year. Flawless from start to finish."],
}


def main():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. Fetch seed owner id
        owner = db.execute(text("SELECT id FROM users WHERE email='seed@yelp-clone.local'")).fetchone()
        if not owner:
            print("Seed owner not found. Run schema.sql first.")
            sys.exit(1)
        owner_id = owner.id

        # 2. Fetch all existing reviewer accounts
        reviewer_rows = db.execute(text("SELECT id FROM users WHERE email LIKE 'reviewer%@seed.local'")).fetchall()
        reviewer_ids = [r.id for r in reviewer_rows]
        if not reviewer_ids:
            print("No reviewer accounts found. Run seed_reviews.py first.")
            sys.exit(1)
        print(f"Using {len(reviewer_ids)} existing reviewer accounts.")

        # 3. Insert restaurants
        inserted_ids = []
        for r in NEW_RESTAURANTS:
            exists = db.execute(
                text("SELECT id FROM restaurants WHERE name=:n AND city=:c"),
                {"n": r["name"], "c": r["city"]}
            ).fetchone()
            if exists:
                print(f"  SKIP (already exists): {r['name']} — {r['city']}")
                continue

            db.execute(text("""
                INSERT INTO restaurants
                    (owner_id, added_by, name, cuisine_type, description,
                     address_line, city, state, zip_code, latitude, longitude,
                     phone, website, hours_of_operation, pricing_tier, amenities,
                     avg_rating, review_count)
                VALUES
                    (:owner, :owner, :name, :cuisine, :desc,
                     :addr, :city, :state, :zip, :lat, :lon,
                     :phone, :website, :hours, :pricing, :amenities,
                     :avg_rating, 0)
            """), {
                "owner": owner_id,
                "name": r["name"], "cuisine": r["cuisine_type"], "desc": r["description"],
                "addr": r["address_line"], "city": r["city"], "state": r["state"],
                "zip": r["zip_code"], "lat": r["lat"], "lon": r["lon"],
                "phone": r["phone"], "website": r["website"],
                "hours": r["hours"], "pricing": r["pricing_tier"],
                "amenities": r["amenities"], "avg_rating": r["avg_rating"],
            })
            db.flush()
            row = db.execute(
                text("SELECT id FROM restaurants WHERE name=:n AND city=:c"),
                {"n": r["name"], "c": r["city"]}
            ).fetchone()
            inserted_ids.append((row.id, r["name"], float(r["avg_rating"])))
            print(f"  Inserted: {r['name']} — {r['city']}, {r['state']}")

        db.commit()
        print(f"\nInserted {len(inserted_ids)} new restaurants.")

        # 4. Seed reviews for each new restaurant
        reviews_per = min(len(reviewer_ids), 25)
        for rest_id, rest_name, target_avg in inserted_ids:
            chosen = random.sample(reviewer_ids, reviews_per)
            inserted_reviews = 0
            for user_id in chosen:
                # Pick rating close to target avg
                base = round(target_avg)
                rating = min(5, max(1, base + random.choice([-1, 0, 0, 0, 1])))
                comment = random.choice(COMMENTS[rating])
                days_ago = random.randint(1, 700)

                exists = db.execute(text(
                    "SELECT 1 FROM reviews WHERE user_id=:u AND restaurant_id=:r"
                ), {"u": user_id, "r": rest_id}).fetchone()
                if exists:
                    continue

                db.execute(text("""
                    INSERT INTO reviews (user_id, restaurant_id, rating, comment, created_at, updated_at)
                    VALUES (:u, :r, :rating, :comment,
                            DATE_SUB(NOW(), INTERVAL :days DAY),
                            DATE_SUB(NOW(), INTERVAL :days DAY))
                """), {"u": user_id, "r": rest_id, "rating": rating,
                       "comment": comment, "days": days_ago})
                inserted_reviews += 1

            db.flush()
            print(f"  {rest_name}: {inserted_reviews} reviews seeded")

        db.commit()

        # 5. Recompute aggregates for new restaurants only
        if inserted_ids:
            id_list = ",".join(str(i[0]) for i in inserted_ids)
            db.execute(text(f"""
                UPDATE restaurants r
                JOIN (
                    SELECT restaurant_id,
                           COUNT(*) AS cnt,
                           ROUND(AVG(rating), 2) AS avg
                    FROM reviews
                    WHERE restaurant_id IN ({id_list})
                    GROUP BY restaurant_id
                ) agg ON agg.restaurant_id = r.id
                SET r.review_count = agg.cnt,
                    r.avg_rating   = agg.avg
            """))
            db.commit()

        # 6. Summary
        rows = db.execute(text(
            "SELECT city, state, COUNT(*) AS cnt FROM restaurants GROUP BY city, state ORDER BY cnt DESC"
        )).fetchall()
        print("\nRestaurants per city:")
        for row in rows:
            print(f"  {row.city}, {row.state}: {row.cnt}")

        total = db.execute(text("SELECT COUNT(*) FROM restaurants")).fetchone()[0]
        print(f"\nTotal restaurants: {total}")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    main()

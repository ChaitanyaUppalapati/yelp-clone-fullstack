"""
Quick API smoke test — run with:
    python test_api.py
"""
import requests

BASE = "http://localhost:8000"
PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"


def check(label, response, expected_status):
    ok = response.status_code == expected_status
    icon = PASS if ok else FAIL
    print(f"{icon}  [{response.status_code}] {label}")
    if not ok:
        print(f"       → {response.text[:200]}")
    return response


def run():
    token = None
    owner_token = None
    review_id = None

    print("\n── Auth ──────────────────────────────────────────")

    # Register (fresh email each run to avoid conflicts)
    import time
    ts = int(time.time())
    email = f"test_{ts}@example.com"
    owner_email = f"owner_{ts}@example.com"

    r = check("Register user", requests.post(f"{BASE}/auth/register", json={
        "name": "Test User", "email": email,
        "password": "testpass123", "role": "user"
    }), 201)

    check("Register duplicate → 400", requests.post(f"{BASE}/auth/register", json={
        "name": "Test User", "email": email,
        "password": "testpass123", "role": "user"
    }), 400)

    r = check("Login", requests.post(f"{BASE}/auth/login",
        data={"username": email, "password": "testpass123"}
    ), 200)
    token = r.json().get("access_token")
    auth = {"Authorization": f"Bearer {token}"}

    check("Login wrong password → 401", requests.post(f"{BASE}/auth/login",
        data={"username": email, "password": "wrongpassword"}
    ), 401)

    check("Logout", requests.post(f"{BASE}/auth/logout", headers=auth), 200)

    # Re-login since we logged out
    r = requests.post(f"{BASE}/auth/login", data={"username": email, "password": "testpass123"})
    token = r.json().get("access_token")
    auth = {"Authorization": f"Bearer {token}"}

    print("\n── Users ─────────────────────────────────────────")

    check("GET /users/me", requests.get(f"{BASE}/users/me", headers=auth), 200)

    check("GET /users/me no token → 401",
        requests.get(f"{BASE}/users/me"), 401)

    check("PUT /users/me", requests.put(f"{BASE}/users/me", headers=auth, json={
        "about_me": "I love food", "city": "San Francisco"
    }), 200)

    check("POST /users/me/preferences", requests.post(f"{BASE}/users/me/preferences", headers=auth, json={
        "cuisine_preferences": ["Italian", "Thai"],
        "price_range": 2,
        "sort_preference": "rating"
    }), 201)

    check("GET /users/me/preferences", requests.get(f"{BASE}/users/me/preferences", headers=auth), 200)

    check("PUT /users/me/preferences", requests.put(f"{BASE}/users/me/preferences", headers=auth, json={
        "price_range": 3
    }), 200)

    print("\n── Restaurants ───────────────────────────────────")

    r = check("GET /restaurants/", requests.get(f"{BASE}/restaurants/"), 200)
    count = len(r.json())
    print(f"       → {count} restaurants returned")

    check("GET /restaurants/?keyword=italian",
        requests.get(f"{BASE}/restaurants/", params={"keyword": "italian"}), 200)

    check("GET /restaurants/?city=Berkeley",
        requests.get(f"{BASE}/restaurants/", params={"city": "Berkeley"}), 200)

    check("GET /restaurants/?pricing_tier=4",
        requests.get(f"{BASE}/restaurants/", params={"pricing_tier": 4}), 200)

    r = check("GET /restaurants/1", requests.get(f"{BASE}/restaurants/1"), 200)
    has_reviews = "reviews" in r.json()
    print(f"       → has 'reviews' field: {has_reviews}")

    check("GET /restaurants/9999 → 404", requests.get(f"{BASE}/restaurants/9999"), 404)

    print("\n── Reviews ───────────────────────────────────────")

    r = check("POST /reviews/", requests.post(f"{BASE}/reviews/", headers=auth, json={
        "restaurant_id": 1, "rating": 4, "comment": "Great place!"
    }), 201)
    review_id = r.json().get("id")

    check("POST /reviews/ duplicate → 400", requests.post(f"{BASE}/reviews/", headers=auth, json={
        "restaurant_id": 1, "rating": 5, "comment": "Again"
    }), 400)

    r2 = requests.get(f"{BASE}/restaurants/1").json()
    print(f"       → avg_rating after review: {r2.get('avg_rating')}, count: {r2.get('review_count')}")

    if review_id:
        check(f"PUT /reviews/{review_id}", requests.put(f"{BASE}/reviews/{review_id}", headers=auth, json={
            "rating": 5, "comment": "Actually amazing!"
        }), 200)

        r2 = requests.get(f"{BASE}/restaurants/1").json()
        print(f"       → avg_rating after update: {r2.get('avg_rating')}")

        check(f"DELETE /reviews/{review_id}", requests.delete(f"{BASE}/reviews/{review_id}", headers=auth), 204)

        r2 = requests.get(f"{BASE}/restaurants/1").json()
        print(f"       → avg_rating after delete: {r2.get('avg_rating')}, count: {r2.get('review_count')}")

    print("\n── Favorites ─────────────────────────────────────")

    check("POST /favorites/2", requests.post(f"{BASE}/favorites/2", headers=auth), 201)
    check("POST /favorites/3", requests.post(f"{BASE}/favorites/3", headers=auth), 201)
    check("POST /favorites/2 duplicate → 400", requests.post(f"{BASE}/favorites/2", headers=auth), 400)

    r = check("GET /favorites/", requests.get(f"{BASE}/favorites/", headers=auth), 200)
    print(f"       → {len(r.json())} favorites")

    check("DELETE /favorites/2", requests.delete(f"{BASE}/favorites/2", headers=auth), 204)

    r = check("GET /favorites/ after delete", requests.get(f"{BASE}/favorites/", headers=auth), 200)
    print(f"       → {len(r.json())} favorites remaining")

    print("\n── History ───────────────────────────────────────")

    requests.post(f"{BASE}/reviews/", headers=auth, json={
        "restaurant_id": 2, "rating": 3, "comment": "Decent"
    })
    r = check("GET /users/me/history", requests.get(f"{BASE}/users/me/history", headers=auth), 200)
    data = r.json()
    print(f"       → {len(data.get('reviews', []))} reviews in history")

    print("\n── Owner ─────────────────────────────────────────")

    requests.post(f"{BASE}/auth/register", json={
        "name": "Owner", "email": owner_email,
        "password": "ownerpass123", "role": "owner"
    })
    r = requests.post(f"{BASE}/auth/login", data={"username": owner_email, "password": "ownerpass123"})
    owner_token = r.json().get("access_token")
    oauth = {"Authorization": f"Bearer {owner_token}"}

    check("GET /owner/restaurants (owner)", requests.get(f"{BASE}/owner/restaurants", headers=oauth), 200)

    check("GET /owner/dashboard (owner)", requests.get(f"{BASE}/owner/dashboard", headers=oauth), 200)

    check("GET /owner/dashboard (user) → 403", requests.get(f"{BASE}/owner/dashboard", headers=auth), 403)

    check("POST /restaurants/4/claim", requests.post(f"{BASE}/restaurants/4/claim", headers=oauth), 200)

    check("PUT /owner/restaurants/4", requests.put(f"{BASE}/owner/restaurants/4", headers=oauth, json={
        "description": "Updated by owner"
    }), 200)

    print("\n─────────────────────────────────────────────────")
    print("Done.\n")


if __name__ == "__main__":
    run()

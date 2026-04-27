import asyncio
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.database import get_db

router = APIRouter()

FOOD_KEYWORDS = [
    "restaurant", "food", "eat", "dinner", "lunch", "breakfast", "cuisine",
    "hungry", "recommend", "find", "near", "vegan", "cheap", "expensive",
    "pizza", "sushi", "burger", "italian", "chinese", "mexican", "thai",
    "indian", "best", "rated", "review", "drink", "bar", "cafe", "coffee",
]

CUISINE_MAP = {
    "pizza": "Italian", "italian": "Italian",
    "sushi": "Japanese", "japanese": "Japanese",
    "burger": "American", "american": "American",
    "taco": "Mexican", "mexican": "Mexican",
    "thai": "Thai", "chinese": "Chinese",
    "indian": "Indian", "vegan": "Vegan",
    "coffee": "Cafe", "cafe": "Cafe",
}

SYSTEM_PROMPT = (
    "You are a restaurant assistant for a Yelp-like app. "
    "Reply in short bullet points (3-5 max). No long paragraphs. "
    "Each bullet should be one line. Be direct and helpful. "
    "Use plain bullets (•), not markdown headers or bold text. "
    "When recommending restaurants, just list name + one key detail per bullet. "
    "If web results are provided, pull in only the most relevant facts."
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


async def _get_relevant_restaurants(message: str, limit: int = 3):
    db = get_db()
    msg_lower = message.lower()
    query: dict = {"is_active": True}

    for keyword, cuisine in CUISINE_MAP.items():
        if keyword in msg_lower:
            query["cuisine_type"] = {"$regex": cuisine, "$options": "i"}
            break

    if any(w in msg_lower for w in ["cheap", "budget", "affordable"]):
        query["pricing_tier"] = {"$lte": 2}
    elif any(w in msg_lower for w in ["fancy", "expensive", "upscale", "fine dining"]):
        query["pricing_tier"] = {"$gte": 3}

    cursor = db.restaurants.find(query).sort("avg_rating", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [
        {
            "id": str(d["_id"]),
            "name": d.get("name", ""),
            "cuisine_type": d.get("cuisine_type", ""),
            "avg_rating": round(d.get("avg_rating") or 0, 1),
            "pricing_tier": d.get("pricing_tier", 1),
            "city": d.get("city", ""),
        }
        for d in docs
    ]


async def _tavily_search(query: str, max_results: int = 3) -> list[dict]:
    """Run a Tavily web search and return simplified result dicts."""
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return []
    try:
        from tavily import AsyncTavilyClient
        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,
        )
        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:400],
            })
        return results
    except Exception:
        return []


def _build_context(restaurants: list[dict], web_results: list[dict]) -> str:
    parts = []
    if restaurants:
        parts.append("Restaurants in our app:\n" + "".join(
            f"- {r['name']} ({r['cuisine_type']}, {'$' * r['pricing_tier']}, "
            f"★{r['avg_rating']}, {r['city']})\n"
            for r in restaurants
        ))
    if web_results:
        parts.append("Web search results:\n" + "".join(
            f"- {w['title']}: {w['content']}\n"
            for w in web_results
        ))
    return "\n\n".join(parts)


@router.post("/chat")
async def chat(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    openai_key = os.getenv("OPENAI_API_KEY", "")
    msg_lower = payload.message.lower()
    is_food_query = any(kw in msg_lower for kw in FOOD_KEYWORDS)

    # Run local DB lookup and Tavily search in parallel
    restaurants: list[dict] = []
    web_results: list[dict] = []

    if is_food_query:
        db_task = _get_relevant_restaurants(payload.message)
        web_task = _tavily_search(payload.message)
        try:
            restaurants, web_results = await asyncio.gather(db_task, web_task)
        except Exception:
            try:
                restaurants = await _get_relevant_restaurants(payload.message)
            except Exception:
                pass
    else:
        # Still do a web search for non-food queries so the bot can answer general questions
        web_results = await _tavily_search(payload.message)

    context = _build_context(restaurants, web_results)

    if not openai_key:
        names = ", ".join(r["name"] for r in restaurants) if restaurants else "nothing specific"
        web_summary = web_results[0]["content"] if web_results else ""
        reply = f"I found some options for you: {names}."
        if web_summary:
            reply += f" From the web: {web_summary[:200]}"
        reply += " For full AI-powered responses, an OpenAI API key is needed."
        return {"response": reply, "restaurants": restaurants, "session_id": payload.session_id}

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)

        system = SYSTEM_PROMPT
        if context:
            system += f"\n\n{context}"

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": payload.message},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

    return {
        "response": reply,
        "restaurants": restaurants,
        "web_results": web_results,
        "session_id": payload.session_id,
    }

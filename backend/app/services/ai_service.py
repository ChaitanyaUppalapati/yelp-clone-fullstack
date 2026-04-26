"""
AI assistant service backed by LangGraph + OpenAI with a local DB search tool
and a Tavily-powered web fallback for restaurants missing from the database.
"""

import json
import re
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.models.conversation import ConversationHistory, MessageRole
from app.models.restaurant import Restaurant
from app.models.user import UserPreferences


class SearchRestaurantsInput(BaseModel):
    cuisine: Optional[str] = Field(None, description="Cuisine type, e.g. Italian, Mexican, Japanese")
    city: Optional[str] = Field(None, description="City name to search in")
    price_tier: Optional[int] = Field(None, description="Price tier: 1=$, 2=$$, 3=$$$, 4=$$$$", ge=1, le=4)
    keyword: Optional[str] = Field(None, description="Keyword in name, description, or amenities")
    ambiance: Optional[str] = Field(None, description="Ambiance keyword e.g. romantic, casual, family-friendly")
    dietary: Optional[str] = Field(None, description="Dietary restriction e.g. vegan, halal, gluten-free")


class SearchWebRestaurantsInput(BaseModel):
    query: str = Field(
        ...,
        description="Natural-language restaurant query. Include the restaurant name or the cuisine, vibe, and city.",
    )
    city: Optional[str] = Field(None, description="Optional city to narrow the web search.")


class AIService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )

    def _load_preferences(self) -> dict:
        prefs = (
            self.db.query(UserPreferences)
            .filter(UserPreferences.user_id == self.user_id)
            .first()
        )
        if not prefs:
            return {}
        return {
            "cuisine_preferences": prefs.cuisine_preferences or [],
            "price_range": prefs.price_range,
            "dietary_needs": prefs.dietary_needs or [],
            "ambiance_preferences": prefs.ambiance_preferences or [],
            "preferred_locations": prefs.preferred_locations or [],
            "sort_preference": prefs.sort_preference.value if prefs.sort_preference else None,
        }

    def _get_history(self, session_id: str, limit: int = 10) -> list:
        rows = (
            self.db.query(ConversationHistory)
            .filter(
                ConversationHistory.user_id == self.user_id,
                ConversationHistory.session_id == session_id,
            )
            .order_by(ConversationHistory.id.asc())
            .limit(limit)
            .all()
        )

        messages = []
        for row in rows:
            if row.role == MessageRole.user:
                messages.append(HumanMessage(content=row.message))
            elif row.role == MessageRole.assistant:
                messages.append(AIMessage(content=row.message))
        return messages

    def _save_message(self, session_id: str, role: MessageRole, message: str):
        entry = ConversationHistory(
            user_id=self.user_id,
            session_id=session_id,
            role=role,
            message=message,
        )
        self.db.add(entry)
        self.db.commit()

    def _build_search_restaurants_tool(self) -> StructuredTool:
        db = self.db

        def search_restaurants(
            cuisine: Optional[str] = None,
            city: Optional[str] = None,
            price_tier: Optional[int] = None,
            keyword: Optional[str] = None,
            ambiance: Optional[str] = None,
            dietary: Optional[str] = None,
        ) -> str:
            """Search for restaurants in the local database."""
            from sqlalchemy import String as SAString, cast, or_

            query = db.query(Restaurant).filter(Restaurant.is_active == True)

            if cuisine:
                query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
            if city:
                query = query.filter(Restaurant.city.ilike(f"%{city}%"))
            if price_tier:
                query = query.filter(Restaurant.pricing_tier == price_tier)
            if keyword:
                query = query.filter(
                    or_(
                        Restaurant.name.ilike(f"%{keyword}%"),
                        Restaurant.description.ilike(f"%{keyword}%"),
                    )
                )
            if ambiance:
                query = query.filter(
                    or_(
                        Restaurant.description.ilike(f"%{ambiance}%"),
                        cast(Restaurant.amenities, SAString).ilike(f"%{ambiance}%"),
                    )
                )
            if dietary:
                query = query.filter(
                    or_(
                        Restaurant.description.ilike(f"%{dietary}%"),
                        cast(Restaurant.amenities, SAString).ilike(f"%{dietary}%"),
                    )
                )

            results = query.order_by(Restaurant.avg_rating.desc()).limit(8).all()

            if not results:
                return json.dumps({
                    "results": [],
                    "message": "No restaurants found matching the criteria.",
                })

            restaurants = []
            for restaurant in results:
                price_label = ["", "$", "$$", "$$$", "$$$$"][restaurant.pricing_tier or 2]
                restaurants.append({
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "cuisine_type": restaurant.cuisine_type or "Various",
                    "avg_rating": float(restaurant.avg_rating or 0),
                    "review_count": restaurant.review_count or 0,
                    "pricing_tier": restaurant.pricing_tier,
                    "price_label": price_label,
                    "city": restaurant.city or "",
                    "description": (restaurant.description or "")[:120],
                    "amenities": restaurant.amenities or [],
                    "source": "database",
                    "is_external": False,
                })
            return json.dumps({"results": restaurants})

        return StructuredTool.from_function(
            func=search_restaurants,
            name="search_restaurants",
            description=(
                "Search for restaurants in the local database. Always call this first for "
                "restaurant-related queries before deciding whether a web search is needed."
            ),
            args_schema=SearchRestaurantsInput,
        )

    def _build_tavily_tool(self):
        if not settings.TAVILY_API_KEY:
            return None

        try:
            from tavily import TavilyClient

            tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

            def clean_title(title: str) -> str:
                cleaned = re.split(r"\s+[|\-:]\s+", (title or "").strip(), maxsplit=1)[0].strip()
                return cleaned or (title or "Restaurant result")

            def search_web_restaurants(query: str, city: Optional[str] = None) -> str:
                """Search the web for restaurants that are not present in the local database."""
                search_query = query.strip()
                if city and city.lower() not in search_query.lower():
                    search_query = f"{search_query} in {city}"

                response = tavily_client.search(
                    query=f"{search_query} restaurant",
                    search_depth="advanced",
                    max_results=5,
                    include_answer=True,
                    include_raw_content=False,
                )

                results = []
                for index, item in enumerate(response.get("results", []), start=1):
                    title = clean_title(item.get("title") or "")
                    content = (item.get("content") or "").strip()
                    results.append({
                        "id": f"web-{index}-{abs(hash(item.get('url') or title))}",
                        "name": title,
                        "cuisine_type": None,
                        "avg_rating": None,
                        "review_count": None,
                        "pricing_tier": None,
                        "price_label": None,
                        "city": city or "",
                        "description": content[:220],
                        "amenities": [],
                        "website": item.get("url"),
                        "source_url": item.get("url"),
                        "source": "web",
                        "is_external": True,
                    })

                return json.dumps({
                    "results": results,
                    "answer": response.get("answer"),
                })

            return StructuredTool.from_function(
                func=search_web_restaurants,
                name="search_web_restaurants",
                description=(
                    "Search the web with Tavily for restaurants or restaurant details that are "
                    "missing from the local database. Use this when local search returns no matches, "
                    "too few matches, or the user asks about a specific place not in the app."
                ),
                args_schema=SearchWebRestaurantsInput,
            )
        except Exception:
            return None

    def _build_system_prompt(self, prefs: dict) -> str:
        pref_lines = []
        if prefs.get("cuisine_preferences"):
            pref_lines.append(f"- Preferred cuisines: {', '.join(prefs['cuisine_preferences'])}")
        if prefs.get("price_range"):
            price_label = ["", "$", "$$", "$$$", "$$$$"][prefs["price_range"]]
            pref_lines.append(f"- Preferred price range: {price_label}")
        if prefs.get("dietary_needs"):
            pref_lines.append(f"- Dietary needs: {', '.join(prefs['dietary_needs'])}")
        if prefs.get("ambiance_preferences"):
            pref_lines.append(f"- Preferred ambiance: {', '.join(prefs['ambiance_preferences'])}")
        if prefs.get("preferred_locations"):
            pref_lines.append(f"- Preferred locations: {', '.join(str(location) for location in prefs['preferred_locations'])}")

        pref_section = (
            "The user has the following saved preferences:\n" + "\n".join(pref_lines)
            if pref_lines
            else "The user has not set any preferences yet."
        )
        rules = [
            "1. Always call search_restaurants immediately for restaurant-related requests and do not ask clarifying questions first.",
            "2. Search broadly. Do not pass cuisine, dietary, or price preferences into the tool unless the user explicitly asked for them in this message.",
            "3. If local search returns no strong matches, too few useful matches, or the user asks about a restaurant that is not in the app, call search_web_restaurants.",
            "4. Use search_web_restaurants for current real-world info such as specific restaurants, recent openings, hours, or places missing from the database.",
            "5. If you use web results, clearly say they came from the web and may not yet exist in the local app database.",
            "6. If the user says yes, sure, go ahead, or a similar follow-up, call a search tool again with a broader or different keyword instead of failing.",
            "7. If no city is mentioned, omit the city filter and search the whole database.",
            "8. Preferences are for ranking and recommending, not for filtering the search query.",
            "9. Format each recommendation with the restaurant name, rating if known, price if known, and one sentence on why it suits the user.",
            "10. Keep responses conversational and warm, not robotic or overly formal.",
            "11. Never ask whether the user has preferences because you already know them from the section above.",
        ]

        return (
            "You are a friendly and knowledgeable restaurant discovery assistant for a Yelp-like platform.\n"
            "Your job is to help users find great restaurants based on their queries and preferences.\n\n"
            f"{pref_section}\n\n"
            "IMPORTANT RULES:\n"
            + "\n".join(rules)
        )

    async def chat(self, session_id: str, message: str) -> dict:
        prefs = self._load_preferences()
        history = self._get_history(session_id)

        tools = [self._build_search_restaurants_tool()]
        tavily = self._build_tavily_tool()
        if tavily:
            tools.append(tavily)

        agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=self._build_system_prompt(prefs),
        )

        result = await agent.ainvoke({"messages": history + [HumanMessage(content=message)]})

        response_text = ""
        for agent_message in reversed(result.get("messages", [])):
            if isinstance(agent_message, AIMessage) and agent_message.content:
                response_text = (
                    agent_message.content
                    if isinstance(agent_message.content, str)
                    else str(agent_message.content)
                )
                break
        if not response_text:
            response_text = "I'm sorry, I couldn't process your request."

        self._save_message(session_id, MessageRole.user, message)
        self._save_message(session_id, MessageRole.assistant, response_text)

        restaurants = []
        seen_restaurants = set()
        for tool_message in result.get("messages", []):
            if not isinstance(tool_message, ToolMessage):
                continue
            if tool_message.name not in {"search_restaurants", "search_web_restaurants"}:
                continue

            try:
                parsed = json.loads(tool_message.content)
            except (json.JSONDecodeError, TypeError):
                continue

            for restaurant in parsed.get("results", []):
                dedupe_key = (
                    str(restaurant.get("id") or ""),
                    restaurant.get("name"),
                    restaurant.get("source_url"),
                )
                if dedupe_key in seen_restaurants:
                    continue
                restaurants.append(restaurant)
                seen_restaurants.add(dedupe_key)

        return {
            "response": response_text,
            "session_id": session_id,
            "restaurants": restaurants,
        }

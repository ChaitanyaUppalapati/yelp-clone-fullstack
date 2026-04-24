"""
AI Assistant service — LangGraph (create_react_agent) + OpenAI (gpt-4o-mini) + Tavily.

LangChain 1.x no longer ships AgentExecutor; the recommended path is
langgraph.prebuilt.create_react_agent which builds a ReAct agent as a
compiled graph.

Flow per chat() call:
  1. Load user preferences from DB
  2. Load conversation history from DB (last 10 turns) as LangChain messages
  3. Build LangGraph agent with tools:
       - search_restaurants  (queries local MySQL DB)
       - tavily_web_search   (web search, only if TAVILY_API_KEY set)
  4. Run agent with [history…, HumanMessage(message)]
  5. Persist user + assistant messages to ConversationHistory table
  6. Scan result messages for tool outputs to surface restaurant data
  7. Return { response, session_id, restaurants }
"""

import json
import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.models.restaurant import Restaurant
from app.models.user import UserPreferences
from app.models.conversation import ConversationHistory, MessageRole


# ---------------------------------------------------------------------------
# Pydantic input schema for the search tool
# ---------------------------------------------------------------------------
class SearchRestaurantsInput(BaseModel):
    cuisine: Optional[str] = Field(None, description="Cuisine type, e.g. Italian, Mexican, Japanese")
    city: Optional[str] = Field(None, description="City name to search in")
    price_tier: Optional[int] = Field(None, description="Price tier: 1=$, 2=$$, 3=$$$, 4=$$$$", ge=1, le=4)
    keyword: Optional[str] = Field(None, description="Keyword in name, description, or amenities")
    ambiance: Optional[str] = Field(None, description="Ambiance keyword e.g. romantic, casual, family-friendly")
    dietary: Optional[str] = Field(None, description="Dietary restriction e.g. vegan, halal, gluten-free")


# ---------------------------------------------------------------------------
# AIService
# ---------------------------------------------------------------------------
class AIService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------
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
            from sqlalchemy import or_, cast, String as SAString

            q = db.query(Restaurant).filter(Restaurant.is_active == True)

            if cuisine:
                q = q.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
            if city:
                q = q.filter(Restaurant.city.ilike(f"%{city}%"))
            if price_tier:
                q = q.filter(Restaurant.pricing_tier == price_tier)
            if keyword:
                q = q.filter(
                    or_(
                        Restaurant.name.ilike(f"%{keyword}%"),
                        Restaurant.description.ilike(f"%{keyword}%"),
                    )
                )
            if ambiance:
                q = q.filter(
                    or_(
                        Restaurant.description.ilike(f"%{ambiance}%"),
                        cast(Restaurant.amenities, SAString).ilike(f"%{ambiance}%"),
                    )
                )
            if dietary:
                q = q.filter(
                    or_(
                        Restaurant.description.ilike(f"%{dietary}%"),
                        cast(Restaurant.amenities, SAString).ilike(f"%{dietary}%"),
                    )
                )

            results = q.order_by(Restaurant.avg_rating.desc()).limit(8).all()

            if not results:
                return json.dumps({"results": [], "message": "No restaurants found matching the criteria."})

            restaurants = []
            for r in results:
                price_label = ["", "$", "$$", "$$$", "$$$$"][r.pricing_tier or 2]
                restaurants.append({
                    "id": r.id,
                    "name": r.name,
                    "cuisine_type": r.cuisine_type or "Various",
                    "avg_rating": float(r.avg_rating or 0),
                    "review_count": r.review_count or 0,
                    "pricing_tier": r.pricing_tier,
                    "price_label": price_label,
                    "city": r.city or "",
                    "description": (r.description or "")[:120],
                    "amenities": r.amenities or [],
                })
            return json.dumps({"results": restaurants})

        return StructuredTool.from_function(
            func=search_restaurants,
            name="search_restaurants",
            description=(
                "Search for restaurants in the local database. "
                "Use this to find matching restaurants based on cuisine, city, price tier, "
                "keywords, ambiance, or dietary restrictions. "
                "Always call this before making specific restaurant recommendations."
            ),
            args_schema=SearchRestaurantsInput,
        )

    def _build_tavily_tool(self):
        if not settings.TAVILY_API_KEY:
            return None
        try:
            os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
            from langchain_community.tools.tavily_search import TavilySearchResults
            return TavilySearchResults(
                max_results=3,
                description=(
                    "Search the web for current information about restaurants, "
                    "hours, events, trending spots, or any real-world context. "
                    "Use this when local database results are insufficient."
                ),
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------
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
            pref_lines.append(f"- Preferred locations: {', '.join(str(l) for l in prefs['preferred_locations'])}")

        pref_section = (
            "The user has the following saved preferences:\n" + "\n".join(pref_lines)
            if pref_lines
            else "The user has not set any preferences yet."
        )

        return f"""You are a friendly and knowledgeable restaurant discovery assistant for a Yelp-like platform.
Your job is to help users find great restaurants based on their queries and preferences.

{pref_section}

IMPORTANT RULES:
1. ALWAYS call search_restaurants immediately for any restaurant-related query — never ask clarifying questions first.
2. Search BROADLY: do NOT pass cuisine, dietary, or price filters from the user's preferences into the tool. Instead, search with only a keyword or city if the user mentioned one. Return a wide set of results and then YOU pick the best matches based on preferences.
3. If the user says "yes", "sure", "go ahead", or similar follow-ups, call search_restaurants again with a broader or different keyword to find more options — do not error out.
4. If no city is mentioned, omit the city filter and search the whole database.
5. Preferences are for RANKING and RECOMMENDING, not for filtering the search query.
6. Format each recommendation: restaurant name, rating (★), price ($-$$$$), and one sentence on why it suits the user.
7. Keep responses conversational and warm — never robotic or overly formal.
8. NEVER ask "do you have any preferences?" — you already know them from the section above.
"""

    # ------------------------------------------------------------------
    # Main chat method
    # ------------------------------------------------------------------
    async def chat(self, session_id: str, message: str) -> dict:
        prefs = self._load_preferences()
        history = self._get_history(session_id)

        # Build tools
        tools = [self._build_search_restaurants_tool()]
        tavily = self._build_tavily_tool()
        if tavily:
            tools.append(tavily)

        system_prompt = self._build_system_prompt(prefs)

        # Build agent using LangGraph's create_react_agent
        agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )

        # Compose message list: history + new human message
        input_messages = history + [HumanMessage(content=message)]

        result = await agent.ainvoke({"messages": input_messages})

        # Extract final AI response (last AIMessage in result)
        response_text = ""
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                response_text = msg.content if isinstance(msg.content, str) else str(msg.content)
                break
        if not response_text:
            response_text = "I'm sorry, I couldn't process your request."

        # Save messages to DB
        self._save_message(session_id, MessageRole.user, message)
        self._save_message(session_id, MessageRole.assistant, response_text)

        # Extract restaurants from ToolMessage outputs
        restaurants = []
        for msg in result.get("messages", []):
            if isinstance(msg, ToolMessage) and msg.name == "search_restaurants":
                try:
                    parsed = json.loads(msg.content)
                    if "results" in parsed and parsed["results"]:
                        restaurants = parsed["results"]
                        break
                except (json.JSONDecodeError, TypeError):
                    pass

        return {
            "response": response_text,
            "session_id": session_id,
            "restaurants": restaurants,
        }

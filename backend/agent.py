"""The Campus Customs shopping assistant: a PydanticAI agent over the local catalogue."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

try:
    from . import audit, db, tools
    from .models import AgentReply
except ImportError:  # Running directly from the backend directory.
    import audit
    import db
    import tools
    from models import AgentReply

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SYSTEM_PROMPT = """You are the shopping assistant for Campus Customs, an officially licensed \
Yale apparel store. Your voice is warm, concise, and school-spirited — "casual comfort, classic \
Bulldog pride." You help shoppers find hoodies, crewnecks, tees, quarter-zips, and jackets tied to \
Yale's residential colleges, graduate schools, sports teams, and gifts for relatives.

Hard rules:
- Every claim about price, color, size, or stock MUST come from a tool call this turn. NEVER invent \
or guess prices or availability. If a tool did not give you the fact, say you need to check and call it.
- Only recommend products returned by your tools. Never make up a product that isn't in the catalogue.
- When a shopper asks for something, call search_catalogue. To answer a price or "do you have my size" \
question, call get_product so you quote exact, current numbers.
- Be honest: if something is sold out or only low stock remains, say so plainly. Don't oversell.
- Keep replies short and skimmable. Mention 2-5 items at most unless asked for more. Don't dump long lists.
- You are told the signed-in shopper's first name; greet returning shoppers naturally when relevant.

The product cards for everything you recommend are shown beside the chat, so don't repeat image links \
or restate every size count — summarize and let the shopper click through."""


class Recommendation(AgentReply):
    """Structured chat reply: a message plus the product ids to show as cards."""
    reply: str = Field(description="Your conversational answer to the shopper.")
    product_ids: list[str] = Field(default_factory=list, description="Catalogue ids to display as cards, in order of relevance.")


@dataclass
class ChatDeps:
    first_name: str = "there"
    email: str = ""
    page_context: str = ""
    # Product ids the tools actually surfaced this turn, so the API can hydrate real cards.
    seen: dict[str, dict] = field(default_factory=dict)


def _make_agent() -> Agent[ChatDeps, Recommendation]:
    api_key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is not configured in .env")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/"),
        default_headers={"x-portkey-api-key": api_key, "x-portkey-provider": os.getenv("PORTKEY_PROVIDER", "openai")},
    )
    model = OpenAIChatModel(
        os.getenv("OPENAI_MODEL", "gpt-5.6-terra"),
        provider=OpenAIProvider(openai_client=client),
    )
    agent = Agent(model, output_type=Recommendation, deps_type=ChatDeps, system_prompt=SYSTEM_PROMPT, retries=2)

    @agent.system_prompt
    def who(ctx: RunContext[ChatDeps]) -> str:
        return f"The signed-in shopper is {ctx.deps.first_name} ({ctx.deps.email}). Current page context: {ctx.deps.page_context or 'general store browsing'}."

    @agent.tool
    def search_catalogue(
        ctx: RunContext[ChatDeps],
        query: str = "",
        category: str = "",
        color: str = "",
        max_price: float | None = None,
        size: str = "",
        in_stock_only: bool = False,
    ) -> list[dict]:
        """Search Yale merch by keywords, category, color, max price, or a size that must be in stock.

        Categories: T-Shirts, Crewnecks, Hoodies, Quarter-Zips, Jackets & Fleece, Long Sleeve.
        Returns matching products with price, colors, and which sizes are in or low on stock."""
        results = db.search_products(query, category, color, max_price, size, in_stock_only, limit=8)
        for p in results:
            ctx.deps.seen[p["product_id"]] = p
        view = [_view(p) for p in results]
        audit.record("tool_call", "search_catalogue",
                     {"query": query, "category": category, "color": color, "max_price": max_price,
                      "size": size, "in_stock_only": in_stock_only},
                     {"count": len(view), "product_ids": [p["product_id"] for p in view]}, "tool_iteration")
        return view

    @agent.tool
    def get_product(ctx: RunContext[ChatDeps], product_id: str) -> dict:
        """Get one item's full description, exact price, colors, and per-size stock. Use for price/description/availability questions."""
        full = db.get_product(product_id)
        if full is not None:
            ctx.deps.seen[product_id] = full
        info = tools.product_information(product_id)
        audit.record("tool_call", "get_product", {"product_id": product_id},
                     {"found": info.get("found"), "price": info.get("price")}, "tool_iteration")
        return info

    @agent.tool
    def stock_status(ctx: RunContext[ChatDeps], product_id: str, size: str) -> dict:
        """Check the exact in-stock quantity for one product in one size. Use when the shopper asks 'do you have my size?'."""
        full = db.get_product(product_id)
        if full is not None:
            ctx.deps.seen[product_id] = full
        status = tools.stock_status(product_id, size)
        audit.record("tool_call", "stock_status", {"product_id": product_id, "size": size},
                     {"available": status.get("available"), "quantity": status.get("quantity")}, "tool_iteration")
        return status

    return agent


def _view(p: dict) -> dict:
    return {
        "product_id": p["product_id"], "name": p["name"], "category": p["category"],
        "price": p["price"], "colors": p["colors"],
        "in_stock_sizes": [s for s, n in p["stock"].items() if n > 0],
        "low_stock_sizes": [s for s, n in p["stock"].items() if 0 < n <= 5],
    }


_agent: Agent[ChatDeps, Recommendation] | None = None


def get_agent() -> Agent[ChatDeps, Recommendation]:
    global _agent
    if _agent is None:
        _agent = _make_agent()
    return _agent

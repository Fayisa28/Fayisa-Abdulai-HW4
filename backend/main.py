"""FastAPI backend for the Campus Customs storefront and shopping assistant."""

from __future__ import annotations

from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from pydantic_ai import UsageLimits
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

try:
    from . import agent as chat_agent
    from . import auth, db, audit
except ImportError:  # Running directly from the backend directory.
    import agent as chat_agent
    import auth
    import db
    import audit

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/images", StaticFiles(directory=db.BASE_DIR / "data" / "products"), name="images")

SESSION_COOKIE = "cc_session"


# ---- auth helpers ----

def current_user(cc_session: str | None = Cookie(default=None)) -> dict:
    user_id = auth.read_token(cc_session)
    user = db.get_user(user_id) if user_id else None
    if user is None:
        raise HTTPException(401, "Not signed in.")
    return user


def optional_user(cc_session: str | None = Cookie(default=None)) -> dict | None:
    user_id = auth.read_token(cc_session)
    return db.get_user(user_id) if user_id else None


def _public_user(user: dict) -> dict:
    return {"id": user["id"], "first_name": user.get("first_name") or user["name"].split()[0],
            "name": user["name"], "email": user["email"]}


def _set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE, auth.issue_token(user_id),
        httponly=True, samesite="lax", max_age=auth.SESSION_TTL,
    )


# ---- schemas ----

class SignupIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(default="", max_length=50)
    email: EmailStr
    password: str = Field(min_length=12, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    page_context: str = Field(default="", max_length=500)


# ---- browsing ----

@app.get("/api/categories")
def categories() -> list[str]:
    return db.garment_categories()


@app.get("/api/products")
def products(
    q: str = "", category: str = "", color: str = "",
    max_price: float | None = Query(None, ge=0), size: str = "", in_stock: bool = False,
) -> list[dict]:
    return db.search_products(q, category, color, max_price, size, in_stock)


@app.get("/api/products/{product_id}")
def product(product_id: str) -> dict:
    found = db.get_product(product_id)
    if found is None:
        raise HTTPException(404, "Product not found")
    return found


# ---- accounts ----

@app.post("/api/auth/signup")
def signup(body: SignupIn, response: Response) -> dict:
    try:
        user = auth.register(body.first_name, body.last_name, body.email, body.password)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    _set_session(response, user["id"])
    return _public_user(user)


@app.post("/api/auth/login")
def login(body: LoginIn, response: Response) -> dict:
    user = auth.authenticate(body.email, body.password)
    if user is None:
        raise HTTPException(401, "Wrong email or password.")
    _set_session(response, user["id"])
    return _public_user(user)


@app.post("/api/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return _public_user(user)


# ---- chat ----

def _to_model_messages(history: list[dict]) -> list[ModelMessage]:
    """Rebuild prior turns so the agent remembers the conversation (text only)."""
    messages: list[ModelMessage] = []
    for row in history:
        if row["role"] == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=row["content"])]))
        elif row["role"] == "assistant":
            messages.append(ModelResponse(parts=[TextPart(content=row["content"])]))
    return messages


@app.get("/api/chat/history")
def chat_history(user: dict = Depends(current_user)) -> list[dict]:
    return db.chat_history(user["id"])


@app.delete("/api/chat/history")
def clear_history(user: dict = Depends(current_user)) -> dict:
    db.clear_chat(user["id"])
    return {"ok": True}


@app.post("/api/chat")
async def chat(body: ChatIn, user: dict | None = Depends(optional_user)) -> dict:
    first_name = (user.get("first_name") or user["name"].split()[0]) if user else "there"
    history = db.chat_history(user["id"], limit=20) if user else []

    deps = chat_agent.ChatDeps(first_name=first_name, email=user["email"] if user else "", page_context=body.page_context)
    audit.record("agent_iteration", "chat", {"message": body.message, "page_context": body.page_context}, stop_reason="started")
    try:
        result = await chat_agent.get_agent().run(
            body.message, deps=deps, message_history=_to_model_messages(history),
            usage_limits=UsageLimits(request_limit=6),
        )
    except Exception as exc:
        audit.record("agent_iteration", "chat", {"message": body.message}, str(exc), "error")
        raise
    output = result.output
    audit.record("agent_iteration", "chat", {"message": body.message}, {"product_ids": output.product_ids}, "completed")

    # Only show cards the tools actually surfaced, in the model's requested order,
    # then fill in any it named without searching (still validated against the DB).
    ids = [pid for pid in output.product_ids]
    cards = [deps.seen[pid] for pid in ids if pid in deps.seen]
    missing = [pid for pid in ids if pid not in deps.seen]
    if missing:
        cards += db.get_products(missing)

    if user:
        db.save_message(user["id"], "user", body.message)
        db.save_message(user["id"], "assistant", output.reply, cards)
    return {"reply": output.reply, "products": cards}

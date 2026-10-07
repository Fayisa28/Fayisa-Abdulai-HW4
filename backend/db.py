"""SQLite access for the Campus Customs storefront and chatbot."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def connect() -> sqlite3.Connection:
    """Open a connection that returns rows as dict-like objects."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _product(row: sqlite3.Row, stock: dict[str, int] | None = None) -> dict:
    """Convert a catalogue row into a JSON-friendly product dict."""
    product = dict(row)
    product["colors"] = json.loads(product["colors"])
    product["search_tags"] = json.loads(product["search_tags"])
    product["image_url"] = "/images/" + product["image_file_path"].removeprefix("products/")
    if stock is not None:
        product["stock"] = stock
        product["in_stock"] = any(qty > 0 for qty in stock.values())
    return product


def _stock_for(conn: sqlite3.Connection, product_ids: list[str]) -> dict[str, dict[str, int]]:
    """Return {product_id: {size: quantity}} in standard size order."""
    if not product_ids:
        return {}
    marks = ",".join("?" * len(product_ids))
    rows = conn.execute(
        f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({marks})", product_ids
    ).fetchall()
    stock: dict[str, dict[str, int]] = {pid: {} for pid in product_ids}
    for row in rows:
        stock[row["product_id"]][row["size"]] = row["quantity"]
    return {
        pid: dict(sorted(sizes.items(), key=lambda kv: SIZE_ORDER.index(kv[0]) if kv[0] in SIZE_ORDER else 99))
        for pid, sizes in stock.items()
    }


def garment_categories() -> list[str]:
    """Group the messy garment_type values into a few shopper-friendly categories."""
    return ["T-Shirts", "Crewnecks", "Hoodies", "Quarter-Zips", "Jackets & Fleece", "Long Sleeve"]


def _category(garment_type: str) -> str:
    g = garment_type.lower()
    if "quarter-zip" in g:
        return "Quarter-Zips"
    if "hood" in g:
        return "Hoodies"
    if "jacket" in g or "fleece" in g:
        return "Jackets & Fleece"
    if "long-sleeve" in g:
        return "Long Sleeve"
    if "t-shirt" in g:
        return "T-Shirts"
    return "Crewnecks"


def search_products(
    query: str = "",
    category: str = "",
    color: str = "",
    max_price: float | None = None,
    size: str = "",
    in_stock_only: bool = False,
    limit: int = 120,
) -> list[dict]:
    """Search the catalogue by keyword, category, color, price, and size availability."""
    sql = "SELECT * FROM catalogue WHERE 1=1"
    params: list = []
    for word in query.lower().split():
        sql += " AND lower(name || ' ' || garment_type || ' ' || description || ' ' || colors || ' ' || search_tags) LIKE ?"
        params.append(f"%{word}%")
    if color:
        sql += " AND lower(colors) LIKE ?"
        params.append(f"%{color.lower()}%")
    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)
    sql += " ORDER BY name"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        if category:
            rows = [r for r in rows if _category(r["garment_type"]) == category]
        stock = _stock_for(conn, [r["product_id"] for r in rows])
    products = []
    for row in rows:
        sizes = stock.get(row["product_id"], {})
        if size and sizes.get(size.upper(), 0) <= 0:
            continue
        product = _product(row, sizes)
        product["category"] = _category(row["garment_type"])
        if in_stock_only and not product["in_stock"]:
            continue
        products.append(product)
    return products[:limit]


def get_product(product_id: str) -> dict | None:
    """Return one product with its per-size stock, or None."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        product = _product(row, _stock_for(conn, [product_id])[product_id])
    product["category"] = _category(row["garment_type"])
    return product


def get_products(product_ids: list[str]) -> list[dict]:
    """Return known products in the requested order, skipping unknown IDs."""
    found = (get_product(pid) for pid in dict.fromkeys(product_ids))
    return [p for p in found if p is not None]


# ---- users ----

def create_user(first_name: str, last_name: str, email: str, password_hash: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{first_name} {last_name}".strip(), email.lower(), password_hash, first_name, last_name),
        )
        return cur.lastrowid


def get_user_by_email(email: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    return dict(row) if row else None


def get_user(user_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


# ---- chat history ----

def save_message(user_id: int, role: str, content: str, products: list[dict] | None = None) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, json.dumps(products) if products is not None else None),
        )


def chat_history(user_id: int, limit: int = 50) -> list[dict]:
    """Return the user's most recent messages, oldest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    history = []
    for row in reversed(rows):
        products = json.loads(row["products_json"]) if row["products_json"] else []
        history.append({"role": row["role"], "content": row["content"], "products": products, "created_at": row["created_at"]})
    return history


def clear_chat(user_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))

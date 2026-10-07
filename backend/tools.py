"""Small database-facing helpers reserved for the future agent system."""

try:
    from . import db
except ImportError:  # Running directly from the backend directory.
    import db


def find_products(query: str = "") -> list[dict]:
    """Return catalogue matches for a shopper query."""
    return db.search_products(query)


def get_product(product_id: str) -> dict | None:
    """Return one catalogue item with its current per-size inventory."""
    return db.get_product(product_id)


def product_information(product_id: str) -> dict:
    """Return authoritative product facts and a plain-language size status.

    Every price, description, and quantity comes from SQLite. Unknown products
    are reported explicitly rather than filled with placeholder values.
    """
    product = db.get_product(product_id)
    if product is None:
        return {"found": False, "product_id": product_id, "message": "That product is not in the Campus Customs catalogue."}
    sizes = [
        {"size": size, "quantity": quantity, "available": quantity > 0,
         "status": "In stock" if quantity > 0 else "Out of stock"}
        for size, quantity in product["stock"].items()
    ]
    return {
        "found": True,
        "product_id": product["product_id"],
        "name": product["name"],
        "description": product["description"],
        "price": product["price"],
        "colors": product["colors"],
        "image_url": product["image_url"],
        "sizes": sizes,
    }


def stock_status(product_id: str, size: str) -> dict:
    """Check one exact size and state sold-out status without guessing."""
    product = db.get_product(product_id)
    if product is None:
        return {"found": False, "product_id": product_id, "size": size, "message": "That product is not in the catalogue."}
    normalized = size.upper()
    quantity = product["stock"].get(normalized, 0)
    return {
        "found": True, "product_id": product_id, "size": normalized,
        "quantity": quantity, "available": quantity > 0,
        "message": f"{normalized} is in stock." if quantity > 0 else f"{normalized} is currently out of stock.",
    }

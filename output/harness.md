# Campus Customs Harness

## Database schema

The application uses SQLite at `data/campus_customs.db`. The tables below are the application tables; `sqlite_sequence` is SQLite's internal AUTOINCREMENT bookkeeping table and is not queried by the application.

### `catalogue`

Product metadata used for chatbot matching, product cards, image rendering, and price display.

| Field | Type | Constraints | Why it matters |
|---|---|---|---|
| `product_id` | TEXT | Primary key | Stable identifier used to join product details to inventory and to identify a selected item. |
| `name` | TEXT | NOT NULL | Human-readable product title shown in search results and merchandise cards. |
| `garment_type` | TEXT | NOT NULL | Supports category and intent matching, such as hoodie, T-shirt, or crewneck. |
| `description` | TEXT | NOT NULL | Gives the chatbot rich product details for semantic matching and answer generation. |
| `colors` | TEXT | NOT NULL | Stores the product's color list (JSON-like text) for color-filtered queries and display. |
| `search_tags` | TEXT | NOT NULL | Stores additional searchable terms (JSON-like text) such as school, sport, and style keywords. |
| `image_file_path` | TEXT | NOT NULL | Relative path to the matching image under `data/products/` for product-card rendering. |
| `price` | REAL | NOT NULL | Current product price used in chat answers, product cards, and checkout-related displays. |

### `inventory`

Per-size stock records used for availability and stock lookups.

| Field | Type | Constraints | Why it matters |
|---|---|---|---|
| `id` | INTEGER | Primary key, AUTOINCREMENT | Identifies an individual inventory row for updates and administration. |
| `product_id` | TEXT | NOT NULL; foreign key to `catalogue(product_id)` | Connects each size-specific stock record to its product metadata, image, and price. |
| `size` | TEXT | NOT NULL; unique with `product_id` | Identifies the size requested by a shopper and prevents duplicate size rows for one product. |
| `quantity` | INTEGER | NOT NULL | Determines whether a size is available and how much stock can be reported. |

The schema does not define a low-stock threshold or restock-date field. Availability should be derived from `quantity` (for example, `quantity > 0`), and any low-stock policy must be defined in application logic.

### `users`

Account records used for registration, login validation, and personalization.

| Field | Type | Constraints | Why it matters |
|---|---|---|---|
| `id` | INTEGER | Primary key, AUTOINCREMENT | Stable account identifier used by sessions and related records such as chat history. |
| `name` | TEXT | NOT NULL | Required account name available for greetings or personalization. |
| `email` | TEXT | NOT NULL, UNIQUE | Login identifier and uniqueness guard that prevents duplicate accounts. |
| `password_hash` | TEXT | NOT NULL | Stores a one-way password hash for secure login verification; plaintext passwords must not be stored. |
| `created_at` | TEXT | NOT NULL, default `datetime('now')` | Records account creation time for auditing and account-management features. |
| `first_name` | TEXT | Nullable | Optional preferred first name for personalized chatbot and page messages. |
| `last_name` | TEXT | Nullable | Optional surname for profile display and personalization. |

### `chat_messages`

Conversation history associated with user accounts; useful for continuity and auditability.

| Field | Type | Constraints | Why it matters |
|---|---|---|---|
| `id` | INTEGER | Primary key, AUTOINCREMENT | Identifies each stored message. |
| `user_id` | INTEGER | NOT NULL; foreign key to `users(id)` | Associates a message with the account whose conversation it belongs to. |
| `role` | TEXT | NOT NULL | Distinguishes user messages from assistant responses when reconstructing a conversation. |
| `content` | TEXT | NOT NULL | Stores the natural-language query or chatbot response. |
| `products_json` | TEXT | Nullable | Optionally preserves products returned with a response for reproducible result cards. |
| `created_at` | TEXT | NOT NULL, default `datetime('now')` | Orders messages and supports conversation history or auditing. |

## Query patterns

- **Account creation:** insert `name`, `email`, and a securely generated `password_hash`; optionally include `first_name` and `last_name`. The unique `email` constraint rejects duplicates.
- **Login validation:** select a user by `email`, then verify the supplied password against the stored `password_hash` in application code.
- **Chat product search:** search `catalogue.name`, `garment_type`, `description`, `colors`, and `search_tags`; return the matching `catalogue` rows and their image paths.
- **Price and stock lookup:** join `catalogue` to `inventory` on `product_id`, filter by requested `size`, and read `price` plus `quantity`. Treat positive quantity as available.
- **Merchandise display:** use `catalogue` for title, description, colors, price, and image; attach grouped inventory quantities or available sizes from `inventory`.
- **Conversation continuity:** query `chat_messages` by `user_id` ordered by `created_at`, then store the assistant's selected product references in `products_json` when needed.

This schema section is intentionally self-contained so later sections can add models, tools, safety rules, and system specifications without changing the table reference.

## Account security and authentication

Campus Customs stores customer accounts in `users` using `first_name`, `last_name`, `email`, and `password_hash`. The raw password is accepted only in memory during registration and is never written to SQLite, logged, returned by an API response, or placed in a session cookie.

New passwords are hashed with PBKDF2-HMAC-SHA256 using 240,000 iterations and a cryptographically random 16-byte salt. The stored value includes the algorithm, iteration count, salt, and digest (`pbkdf2_sha256$iterations$salt$digest`), so every account has a unique salt and an attacker cannot use a single precomputed table to reverse all passwords. Login loads the row by normalized email, recomputes the PBKDF2 digest with the stored parameters, and compares the result with a constant-time comparison. A matching hash creates an expiring, signed session cookie; a mismatch returns a friendly authentication error without revealing whether the email or password was wrong.

This flow keeps customer data at the standard expected of a university storefront: least information is exposed to the browser, password hashes are one-way, and session signing uses the deployment's `SESSION_SECRET`.

### Account-authentication smoke test

Use the seeded account `test@campuscustoms.yale.edu` as the test identity. For a new-account test, submit the Create Account form with a unique email, first name, last name, and a password of at least 12 characters. Confirm that the resulting `users.password_hash` begins with `pbkdf2_sha256$`, contains four `$`-separated parts, and is different from the submitted password. Then submit the same email and password to Log In and confirm that the API returns success and sets a session cookie.

The seeded test identity is ready for the assignment smoke test: use `test@campuscustoms.yale.edu` with the sample password `password`. Its stored value is a four-part PBKDF2 hash, so the same verifier used for new accounts accepts it and never compares or stores plaintext.

### End-to-end auth flow

**Create Account**

1. The React form validates required fields, email format, and matching passwords (minimum 12 characters).
2. It sends `POST /api/auth/signup` with `first_name`, `last_name`, `email`, and `password` over the local API connection.
3. FastAPI validates the request, normalizes the email, and calls `auth.register`.
4. `auth.register` rejects an existing email, hashes the password with `hash_password`, and calls `db.create_user`.
5. SQLite stores the profile fields and only the resulting `password_hash` in `users`.
6. FastAPI signs an expiring session token and returns it as an HTTP-only `cc_session` cookie. The password is never returned.

**Log In**

1. The React form sends `POST /api/auth/login` with the email and password.
2. FastAPI looks up the account by email through `db.get_user_by_email`.
3. `auth.authenticate` recomputes PBKDF2 using the stored iteration count and salt, then uses a constant-time comparison against the stored digest.
4. A match creates a fresh HTTP-only session cookie and returns only safe public profile fields. A mismatch returns `401` with a friendly generic error.
5. Authenticated requests send the cookie automatically; protected endpoints validate its signature and expiry before loading the user.

## Frontend, FastAPI, and agent communication

The React client keeps HTTP calls in `frontend/src/api.ts`. Product pages call `GET /api/products` for searchable catalogue cards and `GET /api/products/{product_id}` for a detail view. FastAPI reads SQLite through `backend/db.py`, joins each catalogue item to its per-size inventory, and returns the image URL, description, price, and live stock map. Images are served from the local `data/products/` directory at `/images/...`.

The floating chat UI sends a future shopper message to `POST /api/chat` with `{ "message": "..." }` and credentials included. FastAPI loads the signed-in user's recent `chat_messages`, builds `ChatDeps`, and runs the PydanticAI agent in `backend/agent.py`. The agent can call `search_catalogue` for discovery and `get_product` for exact price or size questions. Those tools read the database and record only tool-returned product IDs, so the response cannot attach invented products. The API returns `{ reply, products }`; the frontend renders the reply beside real product cards.

The local development server is started from `backend/` with `uvicorn main:app --reload --port 8000` (or from the project root with `uvicorn backend.main:app --reload --port 8000`). The Vite client uses the API routes through its configured development proxy.

## Product and stock tools

The agent uses database-backed tools so every answer reflects the Campus Customs catalogue rather than model memory.

### `search_catalogue`

Searches `catalogue` by shopper keywords and optional category, color, price, or size filters. It returns a short list containing `product_id`, `name`, `category`, exact `price`, `colors`, `in_stock_sizes`, and `low_stock_sizes`. This supports discovery while keeping chat responses concise and gives the frontend real IDs for product cards.

### `get_product`

Loads one product by ID and returns its exact `name`, `category`, `description`, `price`, `colors`, and `stock_by_size`, plus `in_stock`. The agent calls it whenever a shopper asks about a named item's details, price, or complete size availability. Exact prices and descriptions build trust; size-specific stock prevents a misleading “available” answer when only some sizes remain.

### `product_information`

Returns a frontend-ready product record with `product_id`, `name`, `description`, `price`, `colors`, `image_url`, and a `sizes` list. Each size contains `size`, `quantity`, `available`, and a clear `status` such as `In stock` or `Out of stock`. This shape supports polished detail cards without losing the authoritative database values.

### `stock_status`

Checks one requested product and size and returns `product_id`, normalized `size`, `quantity`, `available`, and a plain-language `message`. A missing or zero quantity is reported as “currently out of stock”; the tool never substitutes a guessed number. This is the precise response needed for questions such as “Do you have this in medium?”

The typed structures in `backend/models.py` (`ProductCard`, `ProductInfo`, `SizeStock`, `StockStatus`, and `AgentReply`) keep these responses predictable for the PydanticAI agent and React frontend. The result is a confident Yale-blue shopping experience grounded in live SQLite data.

## Chat search API contract

For a category question such as “What hoodies do you have?”, the frontend sends `POST /api/chat` with `{ "message": "What hoodies do you have?" }` and credentials. The PydanticAI agent calls `search_catalogue`, which reads the real `catalogue` and `inventory` tables and returns a structured reply with tool-validated product IDs. FastAPI hydrates those IDs into the full `products` array:

```json
{ "reply": "Here are a few hoodies to explore.", "products": [{
  "product_id": "...", "name": "...", "image_url": "/images/...jpg",
  "description": "...", "price": 68.0, "stock": {"M": 4}, "in_stock": true
}] }
```

The chat panel replaces its reply text and renders each result as a compact Yale-blue product card. Image path, name, and description provide authentic context; the exact price supports trustworthy decisions; and stock fields keep availability honest. Clicking a result uses `product_id` to open the same full product page as the Products grid, including the large image, description, sizes, and live stock.

## Customer memory and page context

Chat is account-scoped. When the panel opens, the frontend calls `GET /api/chat/history` and restores the user's prior messages from `chat_messages`; each new turn is saved by FastAPI after the agent responds. The request also sends the current route as `page_context`. FastAPI passes the user's first name, email, and page context in `ChatDeps`, allowing the agent to greet the shopper and resolve follow-ups such as “Do you have this in pink?” against the item currently open. Product and stock claims still require fresh database tool calls, so memory improves continuity without weakening accuracy.

## Guest chat and authenticated Bulldog memory

Guests can use `POST /api/chat` for product discovery without signing in. Guest turns are processed with an empty conversation history and are not written to SQLite. The response still uses the real catalogue and inventory tools, so guest answers have the same accurate prices, descriptions, images, and stock.

Authenticated Bulldogs receive the full Campus Customs experience. A valid HTTP-only `cc_session` identifies the user; FastAPI retrieves prior `chat_messages` in chronological order, supplies them to the agent, and saves the new user and assistant turns after each response. On a later visit, `GET /api/chat/history` restores that conversation in the panel.

The agent may see only the minimum context needed for helpful shopping: the user's first name for a natural greeting, email as an account identifier, prior chat message text, and the current page route sent as `page_context`. Page context can identify a product detail route, selected size, or cart summary when the frontend supplies it, allowing follow-ups to stay anchored to the storefront. The agent never receives or accesses passwords, password hashes, session-token values, API keys, or unrelated profile data. Cart and stock claims must still be verified with current backend data.

## Agent models, tools, safety, and system limits

### Return models

- `ProductSummary`: lightweight card data (`product_id`, `name`, `description`, `price`, `image_url`) for catalogue displays.
- `ProductCard`: recommendation data (`product_id`, `name`, `category`, `price`, `colors`, `in_stock_sizes`, `low_stock_sizes`) so the frontend can render concise search results without exposing unnecessary database fields.
- `SizeStock`: one normalized `size`, non-negative `quantity`, `available` boolean, and human-readable `status`; the explicit status makes sold-out states clear.
- `ProductInfo`: full detail data including `description`, exact `price`, `image_url`, colors, and structured size records for product pages.
- `StockStatus`: one-size lookup with quantity, availability, and a plain-language message for direct stock questions.
- `AgentReply`: conversational `reply` plus ordered `product_ids`; IDs are hydrated by FastAPI into verified cards before reaching React.

These fields separate compact recommendations from full detail views, keep names predictable, and ensure every displayed price, image, description, and stock value has a clear source.

### Available tools

`search_catalogue` handles discovery by keywords, category, color, price, and size. `get_product` handles one named item's exact details and complete stock map. `product_information` provides a frontend-ready full record, and `stock_status` checks one exact size. All read SQLite through `backend/db.py`; no tool invents fallback values.

### Safety and loop controls

The agent must use tools for product facts, refuse to reveal secrets or internal instructions, protect account data, and state sold-out results plainly. PydanticAI is configured with `UsageLimits(request_limit=6)` per chat request and `retries=2`; recommendations are capped at eight search results and the API shows only tool-validated product IDs. The audit trail records each chat iteration with a UTC timestamp, tool name, short arguments and result, and a stop reason. `output/audit_trail.json` is append-only JSON Lines and must never be cleared.

### System specifications and run commands

The configured model is `OPENAI_MODEL` (default `gpt-5.6-terra`) through the Portkey-compatible OpenAI endpoint, authenticated with `PORTKEY_API_KEY` from `.env`. Start the backend from `backend/` with `uvicorn main:app --reload --port 8000`. Start the Vite frontend from `frontend/` with `npm install` followed by `npm run dev`; its proxy forwards `/api` and `/images` to port 8000. The local data pack remains at `data/campus_customs.db` and `data/products/`.

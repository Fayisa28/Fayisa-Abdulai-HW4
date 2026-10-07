# Campus Customs Usability Improvements

A Bulldog Blue usability review of four improvements live in the Campus Customs app. Each A/B panel shows the same improvement through the shopper experience and the business engine behind it.

## 1. Persistent branded navigation — front of house

**What I added:** A Yale-blue sticky header with the Campus Customs mark and Home, Products, About Us, Log In, and Create Account links. Active-link states, responsive wrapping, and a highlighted Create Account action keep the header useful on every screen.

| Shopper Lens (A) — why it helps the Campus Customs shopper | Business Lens (B) — why it helps the business |
|---|---|
| The next destination is always within reach. Clear spacing, active-link feedback, and a responsive layout make the storefront feel calm and easy to navigate. | Persistent navigation keeps high-value paths discoverable: product exploration, account conversion, and brand story. A consistent header also reinforces recognition on every route. |

## 2. Editorial product details and live size states — front of house

**What I added:** Product cards now link to one consistent detail page with a large image, full description, exact price, colors, disabled sold-out sizes, and live per-size availability.

| Shopper Lens (A) — why it helps the Campus Customs shopper | Business Lens (B) — why it helps the business |
|---|---|
| A shopper can move from a compact card to a confident purchase decision without losing context. Disabled sizes and plain-language stock notes prevent surprises. | The shared detail route gives every catalogue item the same polished presentation and turns inventory accuracy into fewer abandoned or disappointed purchases. |

## 3. Tool-grounded product search — agent/backend

**What I added:** The branded chat panel accepts category questions, calls database-backed search tools, and renders returned product objects as clickable cards with images and prices.

| Shopper Lens (A) — why it helps the Campus Customs shopper | Business Lens (B) — why it helps the business |
|---|---|
| “What hoodies do you have?” becomes a focused set of real merchandise with images, names, descriptions, and prices. Selecting a result opens the same detail experience as the Products page. | Tool calls keep recommendations tied to `catalogue` and `inventory`. Exact prices, image paths, and stock states come from SQLite, reducing hallucinated offers and protecting trust in the Campus Customs brand. |

## 4. Account memory and context-aware assistance — agent/backend

**What I added:** Guest chat access plus authenticated customer memory, including saved history, personalized greetings, and page context such as the current product and selected size.

| Shopper Lens (A) — why it helps the Campus Customs shopper | Business Lens (B) — why it helps the business |
|---|---|
| Returning Bulldogs can pick up where they left off. A follow-up like “Do you have this in pink?” stays anchored to the item on screen and feels natural. | Conversation continuity supports retention without exposing sensitive credentials. Account-scoped history and minimal agent dependencies create useful personalization while keeping privacy boundaries clear. |

These improvements share one standard: a crisp Yale-blue interface backed by precise data, so the storefront feels premium at the surface and dependable underneath.

## Verification note

These improvements are connected to the running React/FastAPI app: the header is rendered by the shared app shell, product details use `/products/:id`, chat cards come from the `/api/chat` response, and signed-in memory uses `/api/chat/history`. The screenshots in `output/app_check.html` document those live flows.

# AI Prompts

## Problem 1: VIBE CODER PROMPTS

- Please bolden the page numbers in the final homework write-up so they are easy to scan.

## Problem 2: ANALYZE THE DATABASE

Inspect the SQLite database at `data/campus_customs.db` and build a complete understanding of its schema. Pay particular attention to the structure and purpose of the three core tables:

- `catalogue` — product metadata, image file patterns, and descriptive fields used to match items to user queries.
- `inventory` — stock levels broken down by product and size, including availability and low-stock information.
- `users` — account records containing usernames, hashed passwords, and profile fields relevant to authentication or personalization.

Document the fields, data types, relationships, and constraints for each table. Identify how these tables should be queried together to support account creation and login validation, chat-based product search and matching, real-time price and stock lookups, and displaying relevant merchandise on the page.

## Problem 3: BUILD THE CAMPUS CUSTOMS WEBSITE

I’m building the Campus Customs frontend using React, Vite, and TypeScript. Help me plan the site structure around a navigation bar with Home, Products, About Us, Log In, and Create Account. The Products page should load product cards from the database through FastAPI; each card should show an image, name, price, and short description. Clicking a card should open a product detail page with a larger image, full description, price, and size availability. Explain how to organize the components, how the frontend should request product data from FastAPI, and how to structure product-card and product-detail views so they use original, polished campus-store wording for the Home and About Us pages.

On the Products page, present merchandise with a Yale Bulldog Blue-inspired visual system: deep navy accents, white surfaces, subtle gray dividers, centered catalogue images, bold product names, clear prices, and concise lighter descriptions. Product cards should link to branded detail pages with a large image, full description, price, available sizes, and live per-size stock. Keep the Campus Customs logo at the left of the persistent navigation bar, with evenly spaced Home, Products, About Us, Log In, and Create Account links. Add a fixed bottom-right chat panel with a Yale-blue header, rounded corners, and a gentle slide-up animation; it can remain a non-functional branded placeholder for now. Keep the FastAPI backend focused on serving catalogue data and product images as the foundation for the later agent system.

## Problem 4: CREATE ACCOUNT AND LOGIN

Design the account-creation and login experience so it feels consistent with the Campus Customs brand and trustworthy for shoppers. Create Account collects first name, last name, email, password, and confirm password. Log In collects email and password. Use Yale blue accents, white fields, subtle gray borders, balanced spacing, and clear friendly validation feedback. Store new accounts in the `users` table with securely hashed passwords only; validate login credentials against the stored hash and never store plaintext passwords.

## Problem 5: PydanticAI Agent Backend

Define the Campus Customs voice and safety rules in `backend/prompts/prompt.md`. Set up the PydanticAI agent in `backend/agent.py` with the Portkey API key and database-backed tools. Define typed reply and product-card structures in `backend/models.py`, and implement tools in `backend/tools.py` that read real catalogue and inventory data without inventing prices or stock. Ensure the backend runs with `uvicorn main:app --reload --port 8000`. Document in `output/harness.md` how the React frontend fetches products, sends chat messages, and receives agent responses from FastAPI.

## Problem 6: TOOLS — PRODUCT INFO AND STOCK

Create backend tools that retrieve real product information directly from `data/campus_customs.db`, including the full description, exact catalogue price, and size-specific inventory. Tools must return only values read from the `catalogue` and `inventory` tables: no invented prices, quantities, placeholders, or assumptions. If a requested size has no available quantity, report clearly that it is currently out of stock. Keep responses precise, reliable, and polished in the Campus Customs voice.

## Problem 7: CHAT SEARCH THAT UPDATES THE PAGES

After chat search results load, every injected product card must use the same `/products/:id` route and branded detail view as the main Products page. The detail view must preserve the large image, full description, exact price, sizes, and live stock layout so browsing and agent-generated results feel like one seamless Campus Customs storefront.

## Problem 8: CUSTOMER MEMORY

For logged-in customers, save and restore chat history from `chat_messages`. Pass the signed-in user's name, email, and current page context through agent dependencies so follow-up references such as “this” can be resolved against the product being viewed. Use real product tools for every answer and return structured results for the frontend.

## Problem 9: USABILITY IMPROVEMENTS

## Problem 10: STYLE THE WEBSITE

Craft a premium Campus Customs design language inspired by a Yale campus boutique: Yale Blue, crisp white, heritage gray, collegiate serif headings, and clean humanist sans-serif details. Use generous spacing, editorial product cards, soft shadows, gentle hover lifts, calm reveal transitions, and a graceful chat-dock slide. Keep motion purposeful and accessible, with a polished, trustworthy, unmistakably Yale atmosphere.

## Problem 11: SITE TESTING (APP CHECK)

# Campus Customs

Campus Customs is a Yale-inspired merchandise storefront with a React/Vite/TypeScript frontend and FastAPI backend.

## Run locally

1. Copy `.env.example` to `.env` and add local credentials.
2. Install backend dependencies with `pip install -r requirements.txt`.
3. Start the API from the project root with `uvicorn backend.main:app --reload --port 8000`.
4. Start the frontend with `cd frontend && npm install && npm run dev`.

The SQLite data pack is local-only at `data/campus_customs.db`, with product images in `data/products/`.

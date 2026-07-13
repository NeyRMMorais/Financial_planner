from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.financial_planner.api.routes import router as api_router
from src.financial_planner.data_ingestion.scenario_manager import ensure_baseline_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure baseline scenario is initialized on startup."""
    ensure_baseline_exists()
    yield


app = FastAPI(
    title="Financial Planner API",
    description="Backend calculation and scenario engine API for the corporate FP&A model.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:5173", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register calculation and scenarios API routes
app.include_router(api_router, prefix="/api")


# Mount compiled static assets from React Vite app in production mode
FRONTEND_DIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "ui", "frontend", "dist")
)

if os.path.exists(FRONTEND_DIST_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "message": "FastAPI server running. Frontend is not compiled yet. Run Vite dev server to access the UI.",
            "api_docs": "/docs",
        }

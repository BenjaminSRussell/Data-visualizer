"""Main FastAPI application for Data Visualizer."""
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.database import test_connection, init_db

# Create FastAPI app
app = FastAPI(
    title="Data Visualizer",
    description="PostgreSQL-backed data visualization and exploration platform",
    version="2.0.0"
)

# CORS middleware for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Setup static files and templates
static_path = os.path.join(os.path.dirname(__file__), "static")
templates_path = os.path.join(os.path.dirname(__file__), "templates")

# Create directories if they don't exist
os.makedirs(static_path, exist_ok=True)
os.makedirs(templates_path, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Setup templates
templates = Jinja2Templates(directory=templates_path)


# Web UI routes
@app.get("/", response_class=HTMLResponse, tags=["ui"])
async def index(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/datasets-explorer", response_class=HTMLResponse, tags=["ui"])
async def datasets_explorer(request: Request):
    """Dataset explorer page."""
    return templates.TemplateResponse("datasets.html", {"request": request})


@app.get("/url-explorer", response_class=HTMLResponse, tags=["ui"])
async def url_explorer(request: Request):
    """URL explorer page."""
    return templates.TemplateResponse("urls.html", {"request": request})


@app.get("/patterns", response_class=HTMLResponse, tags=["ui"])
async def patterns_page(request: Request):
    """Patterns visualization page."""
    return templates.TemplateResponse("patterns.html", {"request": request})


@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    print("=" * 60)
    print("Data Visualizer - Starting Up")
    print("=" * 60)

    # Test database connection
    if test_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
        print("  Please check your DATABASE_URL environment variable")

    # Initialize database tables
    try:
        init_db()
        print("✓ Database tables initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")

    print("=" * 60)
    print("Server ready at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    print("Data Visualizer - Shutting Down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Main FastAPI application with comprehensive security and error handling.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api import router as api_router
from app.database import test_connection, init_db
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("Data Visualizer - Starting Up")
    logger.info("=" * 60)

    connection_successful = test_connection(max_retries=3)
    if connection_successful:
        logger.info("[OK] Database connection successful")
    else:
        logger.error("[FAIL] Database connection failed")
        logger.error("Please check your DATABASE_URL environment variable")

    db_initialized = init_db()
    if db_initialized:
        logger.info("[OK] Database tables initialized")
    else:
        logger.warning("[WARN] Database initialization had issues")

    logger.info("=" * 60)
    logger.info(f"Server ready at: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API docs at: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("=" * 60)

    yield

    logger.info("Data Visualizer - Shutting Down")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost,http://localhost:8000,http://127.0.0.1,http://127.0.0.1:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")
if trusted_hosts and trusted_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

app.include_router(api_router, prefix="/api")

current_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(current_dir, "static")
templates_path = os.path.join(current_dir, "templates")

os.makedirs(static_path, exist_ok=True)
os.makedirs(templates_path, exist_ok=True)

try:
    app.mount("/static", StaticFiles(directory=static_path), name="static")
except RuntimeError as mount_error:
    logger.warning(f"Static files directory issue: {mount_error}")

templates = Jinja2Templates(directory=templates_path)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler for better user experience."""
    if request.url.path.startswith("/api/"):
        return {"error": "Endpoint not found", "path": request.url.path}

    try:
        return templates.TemplateResponse(
            "index.html",
            {"request": request},
            status_code=404
        )
    except Exception:
        return {"error": "Page not found"}


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """Custom 500 handler to prevent information disclosure."""
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error occurred"}


@app.get("/", response_class=HTMLResponse, tags=["ui"])
async def index(request: Request):
    """Main dashboard page."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as template_error:
        logger.error(f"Template rendering error: {template_error}")
        return HTMLResponse(
            content="<h1>Data Visualizer</h1><p>Dashboard loading error. Please check logs.</p>",
            status_code=500
        )


@app.get("/datasets-explorer", response_class=HTMLResponse, tags=["ui"])
async def datasets_explorer(request: Request):
    """Dataset explorer page."""
    try:
        return templates.TemplateResponse("datasets.html", {"request": request})
    except Exception as template_error:
        logger.error(f"Template rendering error: {template_error}")
        return HTMLResponse(content="<h1>Error loading dataset explorer</h1>", status_code=500)


@app.get("/url-explorer", response_class=HTMLResponse, tags=["ui"])
async def url_explorer(request: Request):
    """URL explorer page."""
    try:
        return templates.TemplateResponse("urls.html", {"request": request})
    except Exception as template_error:
        logger.error(f"Template rendering error: {template_error}")
        return HTMLResponse(content="<h1>Error loading URL explorer</h1>", status_code=500)


@app.get("/patterns", response_class=HTMLResponse, tags=["ui"])
async def patterns_page(request: Request):
    """Patterns visualization page."""
    try:
        return templates.TemplateResponse("patterns.html", {"request": request})
    except Exception as template_error:
        logger.error(f"Template rendering error: {template_error}")
        return HTMLResponse(content="<h1>Error loading patterns page</h1>", status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        access_log=True
    )

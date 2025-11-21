"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from app.database import Database
from app.routers import customers, licenses, messages, webhooks, csv, companies
from app.config import settings
from app.services.startup_console import StartupConsole

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Sets logging level by environment
if settings.environment == "development":
    logging.getLogger().setLevel(logging.DEBUG)
    logger.debug("Development mode enabled - detailed logs enabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application lifecycle."""
    # Startup
    logger.info("Starting application...")
    await Database.connect()
    logger.info("Application started successfully")
    
    # Exibe console de inicialização
    try:
        await StartupConsole.display_startup_info()
    except Exception as e:
        logger.warning(f"Erro ao exibir console de inicialização: {e}")
        # Não falha o startup se o console tiver problemas
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await Database.disconnect()
    logger.info("Application shut down")


app = FastAPI(
    title="WhatsApp Integration Middleware",
    description="Middleware for integration between License Portal and WhatsApp Cloud API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(customers.router)
app.include_router(licenses.router)
app.include_router(messages.router)
app.include_router(webhooks.router)
app.include_router(csv.router)
app.include_router(companies.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WhatsApp Integration Middleware - MVP",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Tests MongoDB connection
        db = Database.get_database()
        await db.command('ping')
        
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


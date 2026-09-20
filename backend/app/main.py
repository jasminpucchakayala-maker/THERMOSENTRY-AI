from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.api.thermal import router as thermal_router
from backend.app.api.classification_api import router as classification_router
from backend.app.api.persistence_api import router as persistence_router
from backend.app.api.osm_api import router as osm_router
from backend.app.api.decision_api import router as decision_router
from backend.app.utils.logging_config import logger

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} Backend starting up in [{settings.APP_ENV}] mode.")
    logger.info(f"FIRMS API Configuration: {'CONFIGURED' if settings.FIRMS_API_KEY else 'UNCONFIGURED (Using Fallback/Sample Mode)'}")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Satellite Thermal Intelligence System Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for dashboard integration in future steps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(thermal_router)
app.include_router(classification_router)
app.include_router(persistence_router)
app.include_router(osm_router)
app.include_router(decision_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

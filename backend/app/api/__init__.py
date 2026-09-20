from .thermal import router as thermal_router
from .classification_api import router as classification_router
from .persistence_api import router as persistence_router
from .osm_api import router as osm_router
from .decision_api import router as decision_router

__all__ = [
    "thermal_router",
    "classification_router",
    "persistence_router",
    "osm_router",
    "decision_router"
]

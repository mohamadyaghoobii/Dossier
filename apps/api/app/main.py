from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.settings import get_settings
from app.services.reporting import VERSION

settings = get_settings()
app = FastAPI(
    title="Dossier API",
    version=VERSION,
    description="Reporting and documentation engine for the DevSecOps platform ecosystem.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "dossier-api", "version": VERSION}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "ai_provider": settings.ai_provider, "version": VERSION}

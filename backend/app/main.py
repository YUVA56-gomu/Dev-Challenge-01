from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.routes import router
from app.db.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables and seed data if needed
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend service for Sathi CA Companion powered by open-weight Gemma",
    version="0.2.0",
    lifespan=lifespan,
)

# Resilient CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

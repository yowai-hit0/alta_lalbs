from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from contextlib import asynccontextmanager
from .api.routes.auth import router as auth_router
from .api.routes.projects import router as projects_router
from .api.routes.data import router as data_router
from .api.routes.review import router as review_router
from .api.routes.analytics import router as analytics_router
from .api.routes.admin import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev-only: create tables if not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title='Alta Data API', version='0.1.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/health')
async def health():
    return {'status': 'ok'}

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(data_router)
app.include_router(review_router)
app.include_router(analytics_router)
app.include_router(admin_router)



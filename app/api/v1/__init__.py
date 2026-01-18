from fastapi import APIRouter
from app.api.v1 import auth, projects, tasks, payments, admin, proposals

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(proposals.router)
api_router.include_router(tasks.router)
api_router.include_router(payments.router)
api_router.include_router(admin.router)
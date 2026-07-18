from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    organizations,
    repositories,
    scans,
    secrets,
    dashboard,
    ai,
    webhooks,
    audit
)

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["repositories"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(secrets.router, prefix="/secrets", tags=["secrets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["audit"])

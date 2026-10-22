"""Dashboard stats API routes."""
from fastapi import APIRouter, Depends

from app.api.dependencies import get_job_service
from app.db.schemas.stats import DashboardStatsResponse
from app.services.job_service import JobService

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(job_service: JobService = Depends(get_job_service)):
    """Fetches live summary statistics and recent activity."""
    return await job_service.get_dashboard_stats()

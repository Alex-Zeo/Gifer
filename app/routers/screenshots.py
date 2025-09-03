import uuid
from fastapi import APIRouter
from app.models.requests import ScreenshotJobRequest
from app.models.responses import ScreenshotJobResponse
from app.services.screenshot_service import ScreenshotAgent
from app.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/screenshots", response_model=ScreenshotJobResponse)
async def create_screenshot_job(request: ScreenshotJobRequest):
    job_id = str(uuid.uuid4())
    logger.info("Starting screenshot job", job_id=job_id, params=request.dict())

    agent = ScreenshotAgent(
        concurrency=request.concurrency,
        rps=request.per_host_rate_limit_rps,
    )

    files = await agent.capture_date_range(**request.dict())

    # Simplified response for now
    return ScreenshotJobResponse(
        job_id=job_id,
        saved_count=len(files),
        skipped_existing=0,  # TODO: Implement skip logic
        failures=[],  # TODO: Implement failure tracking
        out_dir=request.out_dir,
        files=[str(f) for f in files],
    )

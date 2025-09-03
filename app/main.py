from fastapi import FastAPI, Depends
from app.logger import setup_logging, get_logger
from app.routers import screenshots, convert
from app.security import get_api_key

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Screenshot to GIF/Video Service",
    description="A service to generate screenshots and convert them to GIFs or videos.",
    version="0.1.0",
)


@app.get("/healthz")
async def health_check():
    logger.info("Health check requested")
    return {"status": "ok"}


# Mount routers
app.include_router(
    screenshots.router,
    prefix="/api/v1",
    tags=["screenshots"],
    dependencies=[Depends(get_api_key)],
)
app.include_router(
    convert.router,
    prefix="/api/v1",
    tags=["convert"],
    dependencies=[Depends(get_api_key)],
)

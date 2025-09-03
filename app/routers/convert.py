from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models.requests import GifJobRequest, VideoJobRequest
from app.models.responses import ConvertGifResponse, ConvertVideoResponse
from app.services.gif_service import GifAgent
from app.services.video_service import VideoAgent
from app.services.ordering import order_images
from app.utils.files import list_images
from app.logger import get_logger
from app.services.drive_service import GoogleDriveUploader

router = APIRouter()
logger = get_logger(__name__)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


@router.post("/convert/gif", response_model=ConvertGifResponse)
async def create_gif_job(request: GifJobRequest):
    logger.info("Starting GIF conversion job", params=request.dict())

    source_images = list_images(request.images_glob, IMAGE_EXTENSIONS)
    if not source_images:
        raise HTTPException(
            status_code=404, detail="No images found matching the glob pattern."
        )

    ordered = order_images(
        source_images,
        request.order_strategy,
        [Path(p) for p in request.explicit_images] if request.explicit_images else None,
    )

    agent = GifAgent()
    gif_path = agent.build_gif(
        ordered,
        Path(request.output_path),
        request.seconds_per_image,
        request.loop,
        request.optimize,
    )

    drive_file_id = None
    if request.drive_upload.enabled:
        uploader = GoogleDriveUploader()
        drive_file_id = uploader.upload(
            gif_path,
            request.drive_upload.folder_id,
            request.drive_upload.make_anyone_with_link_reader,
        )

    return ConvertGifResponse(
        frames=len(ordered),
        duration_s=len(ordered) * request.seconds_per_image,
        gif_path=str(gif_path),
        drive_file_id=drive_file_id,
    )


@router.post("/convert/video", response_model=ConvertVideoResponse)
async def create_video_job(request: VideoJobRequest):
    logger.info("Starting video conversion job", params=request.dict())

    source_images = list_images(request.images_glob, IMAGE_EXTENSIONS)
    if not source_images:
        raise HTTPException(
            status_code=404, detail="No images found matching the glob pattern."
        )

    ordered = order_images(
        source_images,
        request.order_strategy,
        [Path(p) for p in request.explicit_images] if request.explicit_images else None,
    )

    agent = VideoAgent()
    video_path = agent.build_video(
        ordered,
        Path(request.output_path),
        request.seconds_per_image,
        request.container,
        request.codec,
        request.crf,
        request.preset,
        request.pix_fmt,
    )

    drive_file_id = None
    if request.drive_upload.enabled:
        uploader = GoogleDriveUploader()
        drive_file_id = uploader.upload(
            video_path,
            request.drive_upload.folder_id,
            request.drive_upload.make_anyone_with_link_reader,
        )

    return ConvertVideoResponse(
        frames=len(ordered),
        duration_s=len(ordered) * request.seconds_per_image,
        video_path=str(video_path),
        drive_file_id=drive_file_id,
    )

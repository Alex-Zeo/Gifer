CLAUDE.md — Screenshot ⇢ GIF/Video Service (Finalized to Your Specs)

A production‑ready, async FastAPI service to:

Generate daily screenshots for a URL over a date range into converter/images/{slug}/YYYY-MM-DD.png.

Make a GIF from an ordered list of images (auto date sort, natural sort for names like 1.jpg, a.png, etc.).

Make a video from the same ordered list (fixed duration per image).

(Optional) Upload outputs to Google Drive.

All modules are typed, testable, and CI/CD‑ready.

0) Decisions Locked‑In (from your answers)

Foldering: converter/images/{slug}/ per job.

Range: Inclusive [start_date, end_date].

Timezone: Apply timezone on date injection.

Ordering: Accept any file names (date‑like or not) and natural order; also support explicit list ordering. Handle common types: .png, .jpg, .jpeg, .webp, .bmp. Auto‑rotate via EXIF.

Screenshots: Capture full page content (not browser UI), SOTA loading checks.

Loading Speed & Robustness: Multi‑signal readiness (DOM ready, images loaded, fonts ready, network idle) with fast‑fail & retries.

Cropping/Watermark: Both supported via params.

Concurrency: Up to 5 concurrent page captures.

Retries: Best practice with jittered exponential backoff; log retries & failures, skip after limit.

Politeness: Best practice rate limiting per host.

Security: No domain allow‑list.

Parametrization: All knobs exposed via API.

Storage: Local by default + Google Drive upload option.

API Auth: Best‑practice bearer/API key.

Async: SOTA async (FastAPI + Playwright async + TaskGroup), bounded concurrency.

Limits: No artificial max date span.

1) Repository Map
.
├─ app/
│  ├─ main.py                        # FastAPI bootstrap, routers mount, security
│  ├─ config.py                      # Pydantic BaseSettings (env -> config)
│  ├─ logger.py                      # structlog JSON logging
│  ├─ security.py                    # API key / Bearer auth, CORS
│  ├─ models/
│  │  ├─ requests.py                 # Pydantic request DTOs
│  │  └─ responses.py                # Pydantic response DTOs
│  ├─ routers/
│  │  ├─ screenshots.py              # /api/v1/screenshots
│  │  └─ convert.py                  # /api/v1/convert (gif, video, upload)
│  ├─ services/
│  │  ├─ screenshot_service.py       # ScreenshotAgent (Playwright)
│  │  ├─ gif_service.py              # GifAgent (Pillow/imageio + 2‑pass palette opt)
│  │  ├─ video_service.py            # VideoAgent (FFmpeg staging/sequence)
│  │  ├─ drive_service.py            # GoogleDriveUploader (optional)
│  │  └─ ordering.py                 # smart ordering (date, natural, explicit)
│  ├─ utils/
│  │  ├─ url.py                      # query param inject/replace
│  │  ├─ dates.py                    # inclusive ranges, tz application
│  │  ├─ files.py                    # ensure_dir, extension filters, EXIF autorotate
│  │  ├─ image_ops.py                # crop, watermark, mode conversions
│  │  └─ render_wait.py              # multi-signal "ready" checks for pages
│  └─ domain/
│     ├─ ports.py                    # Interfaces for agents (ports/adapters)
│     └─ types.py                    # Typed aliases, enums
│
├─ converter/
│  └─ images/
│     └─ {slug}/                     # OUTPUT screenshots (YYYY-MM-DD.png or other names)
│
├─ results/
│  ├─ gifs/                          # OUTPUT animated gifs
│  └─ videos/                        # OUTPUT .mp4 (default) or .webm
│
├─ scripts/
│  ├─ scrape_screenshots.py          # CLI for endpoint (1)
│  ├─ make_gif.py                    # CLI for endpoint (2)
│  └─ make_video.py                  # CLI for endpoint (3)
│
├─ tests/
│  ├─ test_date_utils.py
│  ├─ test_url_utils.py
│  ├─ test_ordering.py               # natural/date ordering incl. edge cases
│  ├─ test_file_filters.py
│  ├─ test_image_ops.py              # crop, watermark
│  ├─ test_gif_service.py
│  ├─ test_video_service.py
│  └─ test_screenshot_contract.py    # Playwright contract tests (mock tolerant)
│
├─ .env.example
├─ pyproject.toml / requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ .pre-commit-config.yaml
├─ .ruff.toml
├─ mypy.ini
├─ .github/workflows/ci.yml
└─ AGENTS.md

2) Endpoints (Stable Contracts)

Base: /api/v1

2.1 POST /screenshots

Generate screenshots for each date inclusively.

Request

{
  "url": "https://gpsjam.org/?lat=57.48042&lon=21.30953&z=5.0&date=2025-08-31",
  "start_date": "2025-08-01",
  "end_date": "2025-08-31",
  "timezone": "UTC",                     // IANA tz for date injection
  "date_param_name": "date",
  "date_format": "YYYY-MM-DD",           // injected into query param
  "slug": "gpsjam-57.48_21.31_z5-2025-08",
  "out_dir": "converter/images/gpsjam-57.48_21.31_z5-2025-08",
  "viewport": {"width": 1920, "height": 1080, "device_scale_factor": 1.0},
  "full_page": true,                     // capture page content, not browser UI
  "render_wait": {                       // SOTA ready checks
    "wait_until": ["domcontentloaded", "networkidle"],
    "ensure_images_loaded": true,
    "ensure_fonts_loaded": true,
    "extra_wait_ms": 300,
    "timeout_ms": 30000
  },
  "concurrency": 5,                      // max parallel pages (<= 5)
  "per_host_rate_limit_rps": 4,          // polite throttling
  "retries": {"max_attempts": 3, "backoff_base_ms": 400, "backoff_jitter_ms": 200},
  "crop": {                              // optional; one of:
    "selector": null,                    // e.g. "#mapCanvas"
    "box": null                          // {"left":0,"top":0,"width":1200,"height":800}
  },
  "watermark": {                         // optional text overlay
    "text": null,                        // e.g., "gpsjam • 2025‑08‑03"
    "position": "bottom-right",          // TL/TR/BL/BR/center
    "opacity": 0.3,
    "font_size": 18,
    "margin_px": 12
  },
  "overwrite": false                     // skip existing files if false
}


Response

{
  "job_id": "af5e7a2a-...-d9ef",
  "saved_count": 31,
  "skipped_existing": 0,
  "failures": [],
  "out_dir": "converter/images/gpsjam-57.48_21.31_z5-2025-08",
  "files": [
    "converter/images/gpsjam-57.48_21.31_z5-2025-08/2025-08-01.png",
    "..."
  ]
}

2.2 POST /convert/gif

Make a GIF from an ordered list of images (auto‑ordered unless provided explicitly).

Request

{
  "images_glob": "converter/images/gpsjam-57.48_21.31_z5-2025-08/*",
  "explicit_images": null,                 // optional: explicit ordered array of paths
  "order_strategy": "auto",                // auto | date | natural | explicit
  "output_path": "results/gifs/gpsjam-2025-08.gif",
  "seconds_per_image": 0.5,
  "loop": 0,
  "optimize": true,                        // palette optimization
  "transparency": true,                    // keep alpha where possible
  "drive_upload": {                        // optional Google Drive upload
    "enabled": false,
    "folder_id": null,
    "make_anyone_with_link_reader": false
  }
}


Response

{
  "frames": 31,
  "duration_s": 15.5,
  "gif_path": "results/gifs/gpsjam-2025-08.gif",
  "drive_file_id": null,
  "warnings": []
}

2.3 POST /convert/video

Make a video from the same ordered list.

Request

{
  "images_glob": "converter/images/gpsjam-57.48_21.31_z5-2025-08/*",
  "explicit_images": null,
  "order_strategy": "auto",
  "output_path": "results/videos/gpsjam-2025-08.mp4",
  "seconds_per_image": 0.5,
  "container": "mp4",                      // mp4 | webm
  "codec": "libx264",                      // libx264 | libvpx-vp9 | libaom-av1
  "crf": 18,
  "preset": "medium",
  "pix_fmt": "yuv420p",
  "drive_upload": {
    "enabled": false,
    "folder_id": null,
    "make_anyone_with_link_reader": false
  }
}


Response

{
  "frames": 31,
  "duration_s": 15.5,
  "video_path": "results/videos/gpsjam-2025-08.mp4",
  "drive_file_id": null,
  "warnings": []
}

2.4 GET /healthz

Simple liveness probe.

3) Agents & Core Responsibilities
ScreenshotAgent (app/services/screenshot_service.py)

Input: Base URL + inclusive date range + tz + params.

Logic:

For each date, replace/insert date_param_name using date_format (tz‑aware).

Async capture with TaskGroup and Semaphore(5).

Render readiness:

page.goto(..., wait_until='domcontentloaded') → page.wait_for_load_state('networkidle')

document.fonts.ready + all <img> complete (via evaluate)

optional selector wait (crop.selector)

small extra_wait_ms stabilization.

Capture: page.screenshot(full_page=True) (pure page content; no browser UI).

Post‑ops: optional crop (selector/box) and watermark (PIL).

Retry: tenacity with exp backoff + jitter; log attempts; skip after max.

Politeness: aiolimiter per host RPS.

Output: {slug}/YYYY-MM-DD.png files (or overridden via params).

GifAgent (app/services/gif_service.py)

Input: image paths from ordering.py.

Process:

Load streamingly; EXIF auto‑rotate; convert to P with palette optimization (2‑pass where enabled).

duration = int(seconds_per_image * 1000); loop default infinite (0).

Atomic write (tmp → move).

Output: results/gifs/{slug-or-name}.gif.

VideoAgent (app/services/video_service.py)

Input: ordered image paths.

Process:

Stage into temp numeric sequence (000001.png …) to preserve order across mixed names/types.

ffmpeg -framerate 1/{seconds_per_image} -i %06d.png -c:v <codec> -crf <crf> -preset <preset> -pix_fmt <pix_fmt>

Atomic write.

Output: results/videos/{slug-or-name}.mp4 (or .webm).

GoogleDriveUploader (app/services/drive_service.py)

Options: Service Account (server‑side) or OAuth Installed App (dev).

Features: Upload file, set parent folder, optional link‑sharing (anyoneWithLink: reader).

Output: drive_file_id (+ link if sharing enabled).

4) Public Models (Pydantic)
Requests

ScreenshotJobRequest

GifJobRequest

VideoJobRequest

Responses

ScreenshotJobResponse

ConvertGifResponse

ConvertVideoResponse

5) Utilities — Key Functions & Signatures
app/utils/url.py
def with_query_param(url: str, key: str, value: str) -> str: ...
def ensure_date_param(url: str, date_param_name: str, dt: date, fmt: str, tz: str) -> str: ...

app/utils/dates.py
def inclusive_date_range(start: date, end: date) -> list[date]: ...
def to_tz(d: date, tz: str) -> date: ...

app/utils/files.py
def ensure_dir(path: Path) -> None: ...
def list_images(glob_pattern: str, exts: tuple[str,...]) -> list[Path]: ...
def exif_autorotate(img: Image.Image) -> Image.Image: ...

app/services/ordering.py
def detect_date_from_name(name: str) -> date | None: ...
def natural_key(s: str) -> tuple: ...                 # split digits/non-digits; casefolded
def order_images(
    images: list[Path],
    strategy: Literal["auto", "date", "natural", "explicit"],
    explicit: list[Path] | None = None
) -> list[Path]: ...

app/utils/image_ops.py
def crop_image(img: Image.Image, box: dict | None) -> Image.Image: ...
def watermark_text(
    img: Image.Image, text: str, pos: Literal["top-left","top-right","bottom-left","bottom-right","center"],
    opacity: float = 0.3, font_size: int = 18, margin_px: int = 12
) -> Image.Image: ...

app/utils/render_wait.py
async def wait_render_ready(
    page, *,
    wait_until: tuple[str, ...] = ("domcontentloaded","networkidle"),
    ensure_images_loaded: bool = True,
    ensure_fonts_loaded: bool = True,
    extra_wait_ms: int = 0,
    timeout_ms: int = 30000,
    selector: str | None = None
) -> None: ...

app/services/screenshot_service.py
class ScreenshotAgent:
    def __init__(self, *, headless: bool = True, timeout_ms: int = 30000,
                 concurrency: int = 5, rps: float = 4.0): ...
    async def capture_date_range(... ) -> list[Path]: ...

app/services/gif_service.py
class GifAgent:
    def build_gif(
        self, *, images: list[Path], output_path: Path,
        seconds_per_image: float = 0.5, loop: int = 0, optimize: bool = True,
        transparency: bool = True
    ) -> Path: ...

app/services/video_service.py
class VideoAgent:
    def build_video(
        self, *, images: list[Path], output_path: Path,
        seconds_per_image: float = 0.5, container: str = "mp4",
        codec: str = "libx264", crf: int = 18, preset: str = "medium",
        pix_fmt: str = "yuv420p"
    ) -> Path: ...

app/services/drive_service.py
class GoogleDriveUploader:
    def upload(self, *, local_path: Path, folder_id: str | None,
               share_anyone_reader: bool = False) -> str: ...

6) Full Stack (Libraries & Tools)

Python 3.11, FastAPI, Uvicorn

Playwright (Python) + Chromium (headless)

Pillow + imageio (GIF)

FFmpeg CLI (H.264 / VP9 / AV1)

structlog (JSON logs), tenacity (retries), aiolimiter (per‑host rate limiting)

pydantic (v2), typing‑extensions

Google Drive: google-api-python-client + google-auth (or pydrive2)

Quality: Ruff, Black, Mypy (strict), Pytest, pre‑commit

Packaging/Runtime: Docker (multi‑stage), docker‑compose, GitHub Actions

7) Usage (Concise)
7.1 Local Dev
python -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt
python -m playwright install --with-deps chromium
ffmpeg -version
cp .env.example .env
uvicorn app.main:app --reload

7.2 Docker
docker build -t screenshot-converter:latest .
docker run --rm -p 8000:8000 \
  -v $PWD/converter:/app/converter \
  -v $PWD/results:/app/results \
  screenshot-converter:latest

7.3 API Examples

Screenshots (Aug 2025, GPSJam)

curl -X POST http://localhost:8000/api/v1/screenshots -H "Content-Type: application/json" -d '{
  "url": "https://gpsjam.org/?lat=57.48042&lon=21.30953&z=5.0&date=2025-08-31",
  "start_date": "2025-08-01",
  "end_date": "2025-08-31",
  "timezone": "UTC",
  "slug": "gpsjam-57.48_21.31_z5-2025-08",
  "out_dir": "converter/images/gpsjam-57.48_21.31_z5-2025-08",
  "render_wait": {"wait_until":["domcontentloaded","networkidle"], "ensure_images_loaded":true, "ensure_fonts_loaded":true, "extra_wait_ms":300, "timeout_ms":30000},
  "concurrency": 5,
  "retries": {"max_attempts": 3, "backoff_base_ms": 400, "backoff_jitter_ms": 200}
}'


GIF from images (natural order; 0.5s each)

curl -X POST http://localhost:8000/api/v1/convert/gif -H "Content-Type: application/json" -d '{
  "images_glob": "converter/images/gpsjam-57.48_21.31_z5-2025-08/*",
  "order_strategy": "auto",
  "output_path": "results/gifs/gpsjam-2025-08.gif",
  "seconds_per_image": 0.5,
  "optimize": true
}'


Video from images (MP4 / H.264)

curl -X POST http://localhost:8000/api/v1/convert/video -H "Content-Type: application/json" -d '{
  "images_glob": "converter/images/gpsjam-57.48_21.31_z5-2025-08/*",
  "order_strategy": "auto",
  "output_path": "results/videos/gpsjam-2025-08.mp4",
  "seconds_per_image": 0.5,
  "codec": "libx264", "crf": 18, "preset": "medium", "pix_fmt": "yuv420p"
}'


Explicit ordering (non‑date names)

curl -X POST http://localhost:8000/api/v1/convert/gif -H "Content-Type: application/json" -d '{
  "explicit_images": ["converter/images/job/1.jpg","converter/images/job/2.jpg","converter/images/job/10.jpg"],
  "order_strategy": "explicit",
  "output_path": "results/gifs/custom.gif",
  "seconds_per_image": 0.6
}'


Upload results to Google Drive
Add "drive_upload": {"enabled": true, "folder_id": "abc123", "make_anyone_with_link_reader": true} to GIF/Video requests.

8) Security, Observability, and Policies

Auth:

API Key via X-API-Key or Bearer token (Authorization: Bearer ...).

CORS allow‑list via env.

Rate limiting: Per‑host capture limiter (aiolimiter) + optional API rate limits.

Logging: structlog JSON with job_id, slug, attempt, duration, image_count, failures.

Tracing (optional): OpenTelemetry hooks.

Idempotency: Skip if file exists unless overwrite=true.

Error mapping: 4xx for validation, 5xx for internal; partial successes reported.

9) CI/CD Best Practices

GitHub Actions (.github/workflows/ci.yml)

ruff check .

black --check .

mypy --strict .

pytest -q

Docker build; push on tag (GHCR/ECR).

Dockerfile

Base: mcr.microsoft.com/playwright/python

Install ffmpeg + Python deps

Non‑root user; UVICORN_WORKERS=1 (async I/O bound)

Pre‑commit

Ruff, Black, Mypy, Codespell, EoF‑fixer.

Versioning & Releases

Semantic tags → container push; changelog from conventional commits (optional).

10) Configuration (.env.example)
APP_ENV=local
LOG_LEVEL=INFO

API_MODE=api-key
API_KEY=change-me
CORS_ORIGINS=http://localhost:3000

PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT_MS=30000
CONCURRENCY_MAX=5
PER_HOST_RPS=4

CONVERTER_DIR=converter/images
RESULT_GIFS_DIR=results/gifs
RESULT_VIDEOS_DIR=results/videos

# Google Drive (optional)
GOOGLE_DRIVE_ENABLED=false
GOOGLE_DRIVE_CREDENTIALS_JSON=/app/creds/drive-creds.json
GOOGLE_DRIVE_DEFAULT_FOLDER_ID=
GOOGLE_DRIVE_SHARE_ANYONE=false

11) Notes on Ordering & Types

Auto ordering resolves to:

Date if names parse as YYYY-MM-DD (or close variants); else

Natural (human) order: "2.jpg" < "10.jpg"; case‑insensitive; ignores extension.

Explicit if provided.

Supported types: .png, .jpg, .jpeg, .webp, .bmp; others ignored (logged).

GIF duration: seconds_per_image * frame_count (e.g., 0.5s × 30 ≈ 15s).

Video timing: Input framerate = 1 / seconds_per_image.

12) Acceptance Trace

✅ Endpoint 1: Date‑range screenshots to converter/images/{slug}/YYYY-MM-DD.png.

✅ Endpoint 2: GIF from ordered images; seconds_per_image param.

✅ Endpoint 3: Video from ordered images; same timing.

✅ Subfolder per job, inclusive, tz‑aware, non‑date names supported, common image types.

✅ Full‑page page content only, SOTA readiness checks, crop/watermark params.

✅ Concurrency=5, retries with logs, politeness, Drive upload, API auth, SOTA async.

13) Remaining Uncertainties (Defaults below unless you override)

Timezone value default: use UTC unless specified per job.

Watermark defaults: disabled by default; when enabled, BR position, 30% opacity, 18px.

GIF optimization: enable 2‑pass palette when optimize=true. Best practices max palette size constraint.

Drive auth mode: support Service Account (server) with shared folder and Or OAuth Installed App for dev

API Auth mode: default X-API-Key

Per‑host RPS default: set to 4 rps. Different default?

Failure policy: continue on errors and report partial success; strict=true parameter to fail the whole job on any error

Crop precedence: if both selector and box provided, we’ll prioritize selector.

Output containers: add webm/VP9 as a first‑class preset (container=webm, codec=libvpx-vp9)

Public links: when Drive upload is enabled with make_anyone_with_link_reader=true, return the webViewLink in response

14) Quick Start Happy Path

Start the API (Docker or local).

POST /screenshots with the GPSJam URL for Aug 2025 (see example).

POST /convert/gif with the output folder glob, seconds_per_image=0.5.

POST /convert/video similarly.

(Optional) re‑POST GIF/Video with drive_upload.enabled=true to push to Google Drive.
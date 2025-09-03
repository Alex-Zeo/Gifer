import asyncio
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import tenacity
from aiolimiter import AsyncLimiter
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)
from PIL import Image
from app.logger import get_logger
from app.utils.dates import inclusive_date_range
from app.utils.files import ensure_dir
from app.utils.image_ops import crop_image, watermark_text
from app.utils.url import ensure_date_param
from app.utils.render_wait import comprehensive_render_wait
from app.utils.gpsjam_handler import is_gpsjam_domain, handle_gpsjam_page

logger = get_logger(__name__)

class ScreenshotAgent:
    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 30000,
        concurrency: int = 2,
        rps: float = 4.0,
    ):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.semaphore = asyncio.Semaphore(concurrency)
        self.rate_limiter = AsyncLimiter(rps, 1)

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser.close()
        await self.playwright.stop()

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        stop=tenacity.stop_after_attempt(3),
        reraise=True,
    )
    async def _take_screenshot(
        self,
        context: BrowserContext,
        url: str,
        output_path: Path,
        full_page: bool,
        crop_box: Optional[Dict],
        watermark: Optional[Dict],
        render_wait_config: Optional[Dict] = None,
        custom_selector: Optional[str] = None,
    ):
        page = await context.new_page()
        try:
            # Stage 1: Initial page load with basic wait conditions
            wait_until_conditions = ["domcontentloaded", "networkidle"]
            if render_wait_config and "wait_until" in render_wait_config:
                wait_until_conditions = render_wait_config["wait_until"]
            
            # Load page with progressive wait strategy
            logger.debug(f"Loading page: {url}")
            await page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
            
            # Wait for network idle if specified
            if "networkidle" in wait_until_conditions:
                logger.debug("Waiting for network idle...")
                await page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
            
            # Stage 2: GPSJAM-specific handling (if applicable)
            gpsjam_results = None
            if is_gpsjam_domain(url):
                logger.info("GPSJAM domain detected, applying special handling...")
                gpsjam_results = await handle_gpsjam_page(page, self.timeout_ms)
                logger.info(f"GPSJAM handling results: {gpsjam_results}")
            
            # Stage 3: Comprehensive render waiting
            if render_wait_config:
                logger.debug("Performing comprehensive render wait...")
                wait_results = await comprehensive_render_wait(
                    page, render_wait_config, custom_selector
                )
                logger.debug(f"Render wait results: {wait_results}")
            
            # Stage 4: Take screenshot
            logger.debug("Taking screenshot...")
            screenshot_bytes = await page.screenshot(
                path=str(output_path), full_page=full_page
            )

            # Stage 5: Post-processing
            if crop_box or watermark:
                logger.debug("Applying post-processing...")
                img = Image.open(output_path)
                if crop_box:
                    img = crop_image(img, crop_box)
                if watermark:
                    img = watermark_text(img, **watermark)
                img.save(output_path)
                
            logger.debug(f"Screenshot saved: {output_path}")
            
        finally:
            await page.close()

    async def _capture_one_date(self, browser: Browser, url: str, dt: date, **kwargs):
        async with self.semaphore:
            async with self.rate_limiter:
                output_path = Path(kwargs["out_dir"]) / f"{dt.isoformat()}.png"
                if not kwargs.get("overwrite", False) and output_path.exists():
                    logger.info("File exists, skipping", path=str(output_path))
                    return

                context = await browser.new_context(
                    viewport=kwargs.get("viewport"),
                    device_scale_factor=kwargs.get("device_scale_factor"),
                )
                
                request_url = ensure_date_param(
                    url,
                    kwargs["date_param_name"],
                    dt,
                    kwargs["date_format"],
                    kwargs["timezone"],
                )

                try:
                    await self._take_screenshot(
                        context,
                        request_url,
                        output_path,
                        kwargs.get("full_page", True),
                        kwargs.get("crop"),
                        kwargs.get("watermark"),
                        kwargs.get("render_wait"),
                        kwargs.get("custom_selector"),
                    )
                except Exception as e:
                    logger.error("Failed to capture screenshot", url=request_url, error=e)
                finally:
                    await context.close()

    async def capture_date_range(self, **kwargs) -> List[Path]:
        ensure_dir(Path(kwargs["out_dir"]))
        dates = inclusive_date_range(kwargs["start_date"], kwargs["end_date"])

        # Extract url from kwargs to avoid duplicate argument error
        url = kwargs.pop("url")
        
        async with self as agent:
            tasks = [
                agent._capture_one_date(agent.browser, url, dt, **kwargs)
                for dt in dates
            ]
            await asyncio.gather(*tasks)

        # Return list of generated files
        return [
            Path(kwargs["out_dir"]) / f"{dt.isoformat()}.png"
            for dt in dates
        ]

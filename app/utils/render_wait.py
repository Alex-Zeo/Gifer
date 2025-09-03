"""
Advanced page rendering wait utilities for reliable screenshot capture.
"""

import asyncio
from typing import Dict, List, Optional
from playwright.async_api import Page
from app.logger import get_logger

logger = get_logger(__name__)


async def wait_for_images_loaded(page: Page, timeout_ms: int = 10000) -> bool:
    """
    Wait for all images on the page to finish loading.
    
    Returns:
        bool: True if all images loaded, False if timeout occurred
    """
    try:
        # JavaScript to check if all images are loaded
        js_code = """
        () => {
            const images = Array.from(document.images);
            if (images.length === 0) return true;
            
            return images.every(img => {
                // Check if image is complete and has valid dimensions
                if (!img.complete) return false;
                if (img.naturalWidth === 0 || img.naturalHeight === 0) return false;
                return true;
            });
        }
        """
        
        # Wait for the condition with polling
        await page.wait_for_function(js_code, timeout=timeout_ms)
        logger.debug("All images loaded successfully")
        return True
        
    except Exception as e:
        logger.warning(f"Image loading wait failed: {e}")
        return False


async def wait_for_fonts_loaded(page: Page, timeout_ms: int = 10000) -> bool:
    """
    Wait for all fonts to finish loading.
    
    Returns:
        bool: True if all fonts loaded, False if timeout occurred
    """
    try:
        # JavaScript to check if fonts are ready
        js_code = """
        () => {
            // Check if document.fonts API is available
            if (!document.fonts) return true;
            
            // Return true if fonts are ready
            return document.fonts.status === 'loaded';
        }
        """
        
        # First wait for document.fonts.ready promise
        await page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
        
        # Then verify the status
        await page.wait_for_function(js_code, timeout=timeout_ms)
        logger.debug("All fonts loaded successfully")
        return True
        
    except Exception as e:
        logger.warning(f"Font loading wait failed: {e}")
        return False


async def wait_for_map_ready(page: Page, timeout_ms: int = 15000) -> bool:
    """
    Wait for map-specific elements to be ready (gpsjam.org specific).
    
    Returns:
        bool: True if map is ready, False if timeout occurred
    """
    try:
        # JavaScript to check for common map indicators
        js_code = """
        () => {
            // Check for common map container selectors
            const mapSelectors = [
                'canvas',           // Map canvas elements
                '[class*="map"]',   // Elements with "map" in class name
                '[id*="map"]',      // Elements with "map" in id
                '.leaflet-container', // Leaflet maps
                '.mapboxgl-map',    // Mapbox maps
                '.ol-viewport'      // OpenLayers maps
            ];
            
            for (const selector of mapSelectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    // Check if at least one map element has content
                    for (const elem of elements) {
                        if (elem.offsetWidth > 0 && elem.offsetHeight > 0) {
                            return true;
                        }
                    }
                }
            }
            
            // If no map elements found, assume it's ready
            return true;
        }
        """
        
        await page.wait_for_function(js_code, timeout=timeout_ms)
        logger.debug("Map elements ready")
        return True
        
    except Exception as e:
        logger.warning(f"Map ready wait failed: {e}")
        return False


async def wait_for_no_loading_indicators(page: Page, timeout_ms: int = 10000) -> bool:
    """
    Wait for loading indicators to disappear.
    
    Returns:
        bool: True if no loading indicators, False if timeout occurred
    """
    try:
        # JavaScript to check for loading indicators
        js_code = """
        () => {
            const loadingSelectors = [
                '[class*="loading"]',
                '[class*="spinner"]',
                '[class*="loader"]',
                '.loading',
                '.spinner',
                '.loader',
                '[aria-label*="loading" i]',
                '[aria-label*="Loading" i]'
            ];
            
            for (const selector of loadingSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const elem of elements) {
                    // Check if element is visible
                    const style = window.getComputedStyle(elem);
                    if (style.display !== 'none' && 
                        style.visibility !== 'hidden' && 
                        style.opacity !== '0') {
                        return false;
                    }
                }
            }
            
            return true;
        }
        """
        
        await page.wait_for_function(js_code, timeout=timeout_ms)
        logger.debug("No loading indicators visible")
        return True
        
    except Exception as e:
        logger.warning(f"Loading indicator wait failed: {e}")
        return False


async def comprehensive_render_wait(
    page: Page,
    render_wait_config: Dict,
    custom_selector: Optional[str] = None
) -> Dict[str, bool]:
    """
    Perform comprehensive page render waiting based on configuration.
    
    Args:
        page: Playwright page object
        render_wait_config: RenderWait configuration dict
        custom_selector: Optional custom selector to wait for
        
    Returns:
        Dict with results of each wait condition
    """
    results = {
        "dom_content_loaded": True,  # Assumed already done by page.goto
        "network_idle": True,        # Assumed already done by page.goto
        "images_loaded": False,
        "fonts_loaded": False,
        "map_ready": False,
        "no_loading_indicators": False,
        "custom_selector": False,
        "extra_wait": True
    }
    
    timeout_ms = render_wait_config.get("timeout_ms", 30000)
    
    # Stage 1: Wait for images if enabled
    if render_wait_config.get("ensure_images_loaded", True):
        logger.debug("Waiting for images to load...")
        results["images_loaded"] = await wait_for_images_loaded(page, timeout_ms // 3)
    else:
        results["images_loaded"] = True
    
    # Stage 2: Wait for fonts if enabled
    if render_wait_config.get("ensure_fonts_loaded", True):
        logger.debug("Waiting for fonts to load...")
        results["fonts_loaded"] = await wait_for_fonts_loaded(page, timeout_ms // 3)
    else:
        results["fonts_loaded"] = True
    
    # Stage 3: Wait for map to be ready
    logger.debug("Waiting for map elements...")
    results["map_ready"] = await wait_for_map_ready(page, timeout_ms // 2)
    
    # Stage 4: Wait for loading indicators to disappear
    logger.debug("Waiting for loading indicators to disappear...")
    results["no_loading_indicators"] = await wait_for_no_loading_indicators(page, timeout_ms // 3)
    
    # Stage 5: Wait for custom selector if provided
    if custom_selector:
        try:
            logger.debug(f"Waiting for custom selector: {custom_selector}")
            await page.wait_for_selector(custom_selector, timeout=timeout_ms // 3)
            results["custom_selector"] = True
        except Exception as e:
            logger.warning(f"Custom selector wait failed: {e}")
            results["custom_selector"] = False
    else:
        results["custom_selector"] = True
    
    # Stage 6: Extra stabilization wait
    extra_wait_ms = render_wait_config.get("extra_wait_ms", 300)
    if extra_wait_ms > 0:
        logger.debug(f"Extra stabilization wait: {extra_wait_ms}ms")
        await asyncio.sleep(extra_wait_ms / 1000)
        results["extra_wait"] = True
    
    # Log summary
    failed_conditions = [k for k, v in results.items() if not v]
    if failed_conditions:
        logger.warning(f"Some wait conditions failed: {failed_conditions}")
    else:
        logger.debug("All render wait conditions satisfied")
    
    return results

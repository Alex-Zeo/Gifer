"""
GPSJAM-specific page handling utilities for reliable screenshot capture.
"""

import asyncio
from typing import Optional
from urllib.parse import urlparse
from playwright.async_api import Page
from app.logger import get_logger

logger = get_logger(__name__)


def is_gpsjam_domain(url: str) -> bool:
    """
    Check if the URL belongs to a GPSJAM domain.
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if URL contains gpsjam domain
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # More specific check: domain should end with gpsjam.org or be exactly gpsjam.org
        return domain == "gpsjam.org" or domain.endswith(".gpsjam.org")
    except Exception:
        return False


async def click_more_button(page: Page, timeout_ms: int = 10000) -> bool:
    """
    Click the "More" button in GPSJAM sidebar to load interference data.
    
    Args:
        page: Playwright page object
        timeout_ms: Timeout for finding and clicking the button
        
    Returns:
        bool: True if button was found and clicked, False otherwise
    """
    try:
        logger.debug("Looking for GPSJAM 'More' button...")
        
        # Common selectors for the "More" button
        more_button_selectors = [
            'button:has-text("More")',
            'a:has-text("More")',
            '[data-testid*="more"]',
            '.more-button',
            '#more-button',
            'button[class*="more"]',
            'a[class*="more"]'
        ]
        
        # Try each selector until we find the button
        for selector in more_button_selectors:
            try:
                logger.debug(f"Trying selector: {selector}")
                
                # Wait for the button to be visible and clickable
                await page.wait_for_selector(selector, timeout=timeout_ms // len(more_button_selectors))
                
                # Check if button is visible and enabled
                is_visible = await page.is_visible(selector)
                is_enabled = await page.is_enabled(selector)
                
                if is_visible and is_enabled:
                    logger.debug(f"Found 'More' button with selector: {selector}")
                    await page.click(selector)
                    logger.info("Successfully clicked 'More' button")
                    
                    # Small wait after clicking to allow UI updates
                    await asyncio.sleep(0.5)
                    return True
                    
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # If no button found with text selectors, try generic approach
        logger.debug("Trying generic button detection...")
        try:
            # Look for any button/link that might trigger layer loading
            buttons = await page.query_selector_all('button, a[role="button"], .btn')
            
            for button in buttons:
                text = await button.inner_text()
                if text and any(keyword in text.lower() for keyword in ['more', 'show', 'load', 'data', 'layer']):
                    logger.debug(f"Found potential button: {text}")
                    await button.click()
                    logger.info(f"Clicked button: {text}")
                    await asyncio.sleep(0.5)
                    return True
                    
        except Exception as e:
            logger.debug(f"Generic button detection failed: {e}")
        
        logger.warning("Could not find 'More' button on GPSJAM page")
        return False
        
    except Exception as e:
        logger.error(f"Error clicking 'More' button: {e}")
        return False


async def wait_for_gpsjam_hexagons(page: Page, timeout_ms: int = 30000) -> bool:
    """
    Wait for GPSJAM hexagonal interference overlay to fully load.
    
    Args:
        page: Playwright page object
        timeout_ms: Maximum time to wait for hexagons
        
    Returns:
        bool: True if hexagons loaded, False if timeout
    """
    try:
        logger.debug("Waiting for GPSJAM hexagonal overlay to load...")
        
        # JavaScript to check for hexagon paths in Leaflet overlay
        js_check_hexagons = """
        () => {
            // Look for hexagon paths in Leaflet overlay pane
            const overlayPane = document.querySelector('.leaflet-overlay-pane');
            if (!overlayPane) return { ready: false, count: 0, reason: 'No overlay pane found' };
            
            const paths = overlayPane.querySelectorAll('path');
            const pathCount = paths.length;
            
            // Check if we have a reasonable number of hexagons
            if (pathCount === 0) {
                return { ready: false, count: pathCount, reason: 'No paths found' };
            }
            
            // Check if paths have proper attributes (indicating they're rendered hexagons)
            let validPaths = 0;
            for (const path of paths) {
                const d = path.getAttribute('d');
                const style = window.getComputedStyle(path);
                
                // Valid hexagon should have path data and be visible
                if (d && d.length > 10 && style.display !== 'none' && style.opacity !== '0') {
                    validPaths++;
                }
            }
            
            // Consider ready if we have at least some valid hexagons
            const ready = validPaths >= Math.min(5, pathCount * 0.8);
            
            return { 
                ready: ready, 
                count: pathCount, 
                validCount: validPaths,
                reason: ready ? 'Hexagons loaded' : `Only ${validPaths}/${pathCount} valid paths`
            };
        }
        """
        
        # Wait for initial hexagons to appear
        logger.debug("Waiting for hexagons to appear...")
        await page.wait_for_function(
            f"() => {{ const result = ({js_check_hexagons})(); return result.count > 0; }}",
            timeout=timeout_ms // 2
        )
        
        logger.debug("Initial hexagons detected, waiting for stabilization...")
        
        # Wait for hexagon count to stabilize (no new hexagons added for 3 seconds)
        stable_duration = 3000  # 3 seconds
        check_interval = 500    # 0.5 seconds
        last_count = -1  # Initialize to -1 to ensure first comparison works
        stable_start = None
        max_iterations = (timeout_ms // 2) // check_interval
        
        for i in range(max_iterations):
            try:
                result = await page.evaluate(js_check_hexagons)
                current_count = result.get('validCount', 0)
                
                logger.debug(f"Hexagon check: {result}")
                
                if result.get('ready', False):
                    logger.info(f"GPSJAM hexagons ready: {current_count} valid hexagons")
                    return True
                
                # Check if count is stable
                if current_count == last_count and current_count > 0:
                    if stable_start is None:
                        stable_start = asyncio.get_event_loop().time()
                    elif (asyncio.get_event_loop().time() - stable_start) * 1000 >= stable_duration:
                        logger.info(f"GPSJAM hexagons stabilized: {current_count} hexagons")
                        return True
                else:
                    stable_start = None
                    last_count = current_count
                
                await asyncio.sleep(check_interval / 1000)
                
            except Exception as e:
                logger.debug(f"Error in hexagon check iteration {i}: {e}")
                break
        
        # Final check
        final_result = await page.evaluate(js_check_hexagons)
        if final_result.get('ready', False) or final_result.get('validCount', 0) > 0:
            logger.info(f"GPSJAM hexagons loaded (final): {final_result}")
            return True
        
        logger.warning(f"GPSJAM hexagons failed to load within timeout: {final_result}")
        return False
        
    except Exception as e:
        logger.error(f"Error waiting for GPSJAM hexagons: {e}")
        return False


async def hide_gpsjam_ui_elements(page: Page) -> bool:
    """
    Hide GPSJAM UI elements that might obstruct the map view.
    
    Args:
        page: Playwright page object
        
    Returns:
        bool: True if UI elements were hidden successfully
    """
    try:
        logger.debug("Hiding GPSJAM UI elements...")
        
        # JavaScript to hide common UI elements
        js_hide_ui = """
        () => {
            const elementsToHide = [
                // Common sidebar/panel selectors
                '.sidebar',
                '.panel',
                '.more-panel',
                '.info-panel',
                '.control-panel',
                '.leaflet-control-container .leaflet-right',
                '.leaflet-control-container .leaflet-left',
                
                // Modal/popup selectors
                '.modal',
                '.popup',
                '.overlay',
                '.tooltip',
                
                // Navigation/menu selectors
                '.navbar',
                '.menu',
                '.navigation',
                
                // Attribution that might be large
                '.leaflet-control-attribution'
            ];
            
            let hiddenCount = 0;
            
            elementsToHide.forEach(selector => {
                try {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        // Only hide if element is visible and takes up significant space
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 100 || rect.height > 100) {
                            el.style.display = 'none';
                            hiddenCount++;
                        }
                    });
                } catch (e) {
                    // Ignore individual selector errors
                }
            });
            
            // Special handling for GPSJAM-specific elements
            try {
                // Hide any element containing "more" text that's positioned over the map
                const moreElements = document.querySelectorAll('*');
                for (const el of moreElements) {
                    const text = el.textContent || '';
                    if (text.toLowerCase().includes('more') && 
                        el.offsetWidth > 50 && el.offsetHeight > 20) {
                        const rect = el.getBoundingClientRect();
                        // If positioned over the main map area
                        if (rect.left < window.innerWidth / 2 && rect.top < window.innerHeight / 2) {
                            el.style.display = 'none';
                            hiddenCount++;
                        }
                    }
                }
            } catch (e) {
                // Ignore errors in special handling
            }
            
            return { hiddenCount, success: true };
        }
        """
        
        result = await page.evaluate(js_hide_ui)
        hidden_count = result.get('hiddenCount', 0)
        
        if hidden_count > 0:
            logger.info(f"Hidden {hidden_count} GPSJAM UI elements")
        else:
            logger.debug("No GPSJAM UI elements needed hiding")
        
        # Small wait for any CSS transitions
        await asyncio.sleep(0.3)
        
        return True
        
    except Exception as e:
        logger.error(f"Error hiding GPSJAM UI elements: {e}")
        return False


async def handle_gpsjam_page(page: Page, timeout_ms: int = 30000) -> dict:
    """
    Complete GPSJAM page handling: click More, wait for hexagons, hide UI.
    
    Args:
        page: Playwright page object
        timeout_ms: Total timeout for all operations
        
    Returns:
        dict: Results of each operation
    """
    import time
    start_time = time.time()
    
    results = {
        'more_button_clicked': False,
        'hexagons_loaded': False,
        'ui_hidden': False,
        'total_time_ms': 0
    }
    
    try:
        logger.info("Starting GPSJAM page handling...")
        
        # Step 1: Click the "More" button
        logger.debug("Step 1: Clicking 'More' button...")
        results['more_button_clicked'] = await click_more_button(page, timeout_ms // 3)
        
        if not results['more_button_clicked']:
            logger.warning("Failed to click 'More' button, proceeding anyway...")
        
        # Step 2: Wait for hexagonal overlay to load
        logger.debug("Step 2: Waiting for hexagons...")
        results['hexagons_loaded'] = await wait_for_gpsjam_hexagons(page, timeout_ms * 2 // 3)
        
        # Step 3: Hide UI elements
        logger.debug("Step 3: Hiding UI elements...")
        results['ui_hidden'] = await hide_gpsjam_ui_elements(page)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in GPSJAM page handling: {e}")
        return results
    
    finally:
        # Calculate total time
        results['total_time_ms'] = int((time.time() - start_time) * 1000)
        
        success_count = sum([results['more_button_clicked'], results['hexagons_loaded'], results['ui_hidden']])
        logger.info(f"GPSJAM handling completed: {success_count}/3 operations successful in {results['total_time_ms']}ms")

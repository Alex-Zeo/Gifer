"""
Tests for GPSJAM-specific page handling utilities.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.utils.gpsjam_handler import (
    is_gpsjam_domain,
    click_more_button,
    wait_for_gpsjam_hexagons,
    hide_gpsjam_ui_elements,
    handle_gpsjam_page
)


def test_is_gpsjam_domain():
    """Test GPSJAM domain detection."""
    # Valid GPSJAM domains
    assert is_gpsjam_domain("https://gpsjam.org") is True
    assert is_gpsjam_domain("https://www.gpsjam.org") is True
    assert is_gpsjam_domain("https://gpsjam.org/path") is True
    assert is_gpsjam_domain("http://gpsjam.org") is True
    assert is_gpsjam_domain("https://sub.gpsjam.org") is True
    
    # Non-GPSJAM domains
    assert is_gpsjam_domain("https://google.com") is False
    assert is_gpsjam_domain("https://example.com") is False
    assert is_gpsjam_domain("https://gpsjam-fake.com") is False
    assert is_gpsjam_domain("https://notgpsjam.org") is False
    assert is_gpsjam_domain("https://fakegpsjam.org") is False
    
    # Invalid URLs
    assert is_gpsjam_domain("invalid-url") is False
    assert is_gpsjam_domain("") is False


@pytest.fixture
def mock_page():
    """Create a mock Playwright page object."""
    page = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.is_visible = AsyncMock(return_value=True)
    page.is_enabled = AsyncMock(return_value=True)
    page.click = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])
    page.wait_for_function = AsyncMock()
    page.evaluate = AsyncMock()
    return page


@pytest.mark.asyncio
async def test_click_more_button_success(mock_page):
    """Test successful More button clicking."""
    mock_page.wait_for_selector.return_value = None  # Button found
    mock_page.is_visible.return_value = True
    mock_page.is_enabled.return_value = True
    
    result = await click_more_button(mock_page, 5000)
    
    assert result is True
    mock_page.click.assert_called_once()


@pytest.mark.asyncio
async def test_click_more_button_not_found(mock_page):
    """Test More button not found."""
    mock_page.wait_for_selector.side_effect = Exception("Selector not found")
    mock_page.query_selector_all.return_value = []
    
    result = await click_more_button(mock_page, 5000)
    
    assert result is False


@pytest.mark.asyncio
async def test_click_more_button_generic_fallback(mock_page):
    """Test generic button fallback when specific selectors fail."""
    # First selector fails
    mock_page.wait_for_selector.side_effect = Exception("Not found")
    
    # Mock button with "More" text
    mock_button = AsyncMock()
    mock_button.inner_text.return_value = "More"
    mock_page.query_selector_all.return_value = [mock_button]
    
    result = await click_more_button(mock_page, 5000)
    
    assert result is True
    mock_button.click.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_gpsjam_hexagons_success(mock_page):
    """Test successful hexagon waiting."""
    # Mock successful hexagon detection
    hexagon_result = {
        'ready': True,
        'count': 50,
        'validCount': 45,
        'reason': 'Hexagons loaded'
    }
    
    mock_page.wait_for_function.return_value = None
    mock_page.evaluate.return_value = hexagon_result
    
    result = await wait_for_gpsjam_hexagons(mock_page, 10000)
    
    assert result is True
    mock_page.wait_for_function.assert_called()
    mock_page.evaluate.assert_called()


@pytest.mark.asyncio
async def test_wait_for_gpsjam_hexagons_timeout(mock_page):
    """Test hexagon waiting timeout."""
    # Mock timeout on initial wait
    mock_page.wait_for_function.side_effect = Exception("Timeout")
    
    result = await wait_for_gpsjam_hexagons(mock_page, 1000)
    
    assert result is False


@pytest.mark.asyncio
async def test_wait_for_gpsjam_hexagons_stabilization(mock_page):
    """Test hexagon count stabilization logic."""
    # Mock initial hexagons appearing
    mock_page.wait_for_function.return_value = None
    
    # Mock progressive hexagon loading then stabilization
    hexagon_results = [
        {'ready': False, 'count': 10, 'validCount': 8, 'reason': 'Loading'},
        {'ready': False, 'count': 20, 'validCount': 18, 'reason': 'Loading'},
        {'ready': False, 'count': 25, 'validCount': 23, 'reason': 'Loading'},
        {'ready': False, 'count': 25, 'validCount': 23, 'reason': 'Loading'},  # Stable
        {'ready': False, 'count': 25, 'validCount': 23, 'reason': 'Loading'},  # Still stable
        {'ready': False, 'count': 25, 'validCount': 23, 'reason': 'Loading'},  # Still stable
        {'ready': False, 'count': 25, 'validCount': 23, 'reason': 'Loading'},  # Still stable
        {'ready': False, 'count': 25, 'validCount': 23, 'reason': 'Loading'},  # Still stable
        {'ready': False, 'count': 25, 'validCount': 23, 'reason': 'Loading'},  # Still stable
    ]
    
    # Use cycle to handle multiple calls
    from itertools import cycle
    result_cycle = cycle(hexagon_results)
    mock_page.evaluate.side_effect = lambda _: next(result_cycle)
    
    result = await wait_for_gpsjam_hexagons(mock_page, 10000)
    
    assert result is True
    assert mock_page.evaluate.call_count >= 2


@pytest.mark.asyncio
async def test_hide_gpsjam_ui_elements_success(mock_page):
    """Test successful UI element hiding."""
    mock_page.evaluate.return_value = {'hiddenCount': 3, 'success': True}
    
    result = await hide_gpsjam_ui_elements(mock_page)
    
    assert result is True
    mock_page.evaluate.assert_called_once()


@pytest.mark.asyncio
async def test_hide_gpsjam_ui_elements_error(mock_page):
    """Test UI element hiding with error."""
    mock_page.evaluate.side_effect = Exception("JavaScript error")
    
    result = await hide_gpsjam_ui_elements(mock_page)
    
    assert result is False


@pytest.mark.asyncio
async def test_handle_gpsjam_page_full_success(mock_page):
    """Test complete GPSJAM page handling with all operations successful."""
    # Mock all operations to succeed
    mock_page.wait_for_selector.return_value = None
    mock_page.is_visible.return_value = True
    mock_page.is_enabled.return_value = True
    mock_page.click.return_value = None
    mock_page.wait_for_function.return_value = None
    mock_page.evaluate.return_value = {
        'ready': True, 'count': 50, 'validCount': 45, 'reason': 'Hexagons loaded'
    }
    
    # Mock UI hiding
    hide_result = {'hiddenCount': 2, 'success': True}
    mock_page.evaluate.side_effect = [
        # First call for hexagon checking
        {'ready': True, 'count': 50, 'validCount': 45, 'reason': 'Hexagons loaded'},
        # Second call for UI hiding
        hide_result
    ]
    
    results = await handle_gpsjam_page(mock_page, 10000)
    
    assert results['more_button_clicked'] is True
    assert results['hexagons_loaded'] is True
    assert results['ui_hidden'] is True
    assert results['total_time_ms'] > 0


@pytest.mark.asyncio
async def test_handle_gpsjam_page_partial_success(mock_page):
    """Test GPSJAM page handling with some operations failing."""
    # Mock More button to fail
    mock_page.wait_for_selector.side_effect = Exception("Button not found")
    mock_page.query_selector_all.return_value = []
    
    # Mock hexagons to succeed
    mock_page.wait_for_function.return_value = None
    mock_page.evaluate.side_effect = [
        {'ready': True, 'count': 30, 'validCount': 28, 'reason': 'Hexagons loaded'},
        {'hiddenCount': 1, 'success': True}
    ]
    
    results = await handle_gpsjam_page(mock_page, 10000)
    
    assert results['more_button_clicked'] is False
    assert results['hexagons_loaded'] is True
    assert results['ui_hidden'] is True
    assert results['total_time_ms'] > 0


@pytest.mark.asyncio
async def test_handle_gpsjam_page_complete_failure(mock_page):
    """Test GPSJAM page handling with all operations failing."""
    # Mock all operations to fail
    mock_page.wait_for_selector.side_effect = Exception("Not found")
    mock_page.query_selector_all.return_value = []
    mock_page.wait_for_function.side_effect = Exception("Timeout")
    mock_page.evaluate.side_effect = Exception("JavaScript error")
    
    results = await handle_gpsjam_page(mock_page, 5000)
    
    assert results['more_button_clicked'] is False
    assert results['hexagons_loaded'] is False
    assert results['ui_hidden'] is False
    assert results['total_time_ms'] > 0

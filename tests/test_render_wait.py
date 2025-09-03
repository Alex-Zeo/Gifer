"""
Tests for render wait utilities.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.utils.render_wait import (
    wait_for_images_loaded,
    wait_for_fonts_loaded,
    wait_for_map_ready,
    wait_for_no_loading_indicators,
    comprehensive_render_wait
)


@pytest.fixture
def mock_page():
    """Create a mock Playwright page object."""
    page = AsyncMock()
    page.wait_for_function = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.evaluate = AsyncMock()
    return page


@pytest.mark.asyncio
async def test_wait_for_images_loaded_success(mock_page):
    """Test successful image loading wait."""
    mock_page.wait_for_function.return_value = None  # Success
    
    result = await wait_for_images_loaded(mock_page, 5000)
    
    assert result is True
    mock_page.wait_for_function.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_images_loaded_timeout(mock_page):
    """Test image loading wait timeout."""
    mock_page.wait_for_function.side_effect = Exception("Timeout")
    
    result = await wait_for_images_loaded(mock_page, 5000)
    
    assert result is False
    mock_page.wait_for_function.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_fonts_loaded_success(mock_page):
    """Test successful font loading wait."""
    mock_page.evaluate.return_value = None  # document.fonts.ready resolved
    mock_page.wait_for_function.return_value = None  # Success
    
    result = await wait_for_fonts_loaded(mock_page, 5000)
    
    assert result is True
    mock_page.evaluate.assert_called_once()
    mock_page.wait_for_function.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_fonts_loaded_timeout(mock_page):
    """Test font loading wait timeout."""
    mock_page.evaluate.return_value = None
    mock_page.wait_for_function.side_effect = Exception("Timeout")
    
    result = await wait_for_fonts_loaded(mock_page, 5000)
    
    assert result is False


@pytest.mark.asyncio
async def test_wait_for_map_ready_success(mock_page):
    """Test successful map ready wait."""
    mock_page.wait_for_function.return_value = None  # Success
    
    result = await wait_for_map_ready(mock_page, 5000)
    
    assert result is True
    mock_page.wait_for_function.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_map_ready_timeout(mock_page):
    """Test map ready wait timeout."""
    mock_page.wait_for_function.side_effect = Exception("Timeout")
    
    result = await wait_for_map_ready(mock_page, 5000)
    
    assert result is False


@pytest.mark.asyncio
async def test_wait_for_no_loading_indicators_success(mock_page):
    """Test successful loading indicators wait."""
    mock_page.wait_for_function.return_value = None  # Success
    
    result = await wait_for_no_loading_indicators(mock_page, 5000)
    
    assert result is True
    mock_page.wait_for_function.assert_called_once()


@pytest.mark.asyncio
async def test_comprehensive_render_wait_all_success(mock_page):
    """Test comprehensive render wait with all conditions successful."""
    # Mock all async functions to succeed
    mock_page.wait_for_function.return_value = None
    mock_page.evaluate.return_value = None
    mock_page.wait_for_selector.return_value = None
    
    config = {
        "ensure_images_loaded": True,
        "ensure_fonts_loaded": True,
        "extra_wait_ms": 100,
        "timeout_ms": 10000
    }
    
    results = await comprehensive_render_wait(mock_page, config, "#map-canvas")
    
    # All conditions should be successful
    assert all(results.values()), f"Failed conditions: {[k for k, v in results.items() if not v]}"
    
    # Verify all expected calls were made
    assert mock_page.wait_for_function.call_count >= 3  # images, map, loading indicators
    mock_page.evaluate.assert_called()  # fonts
    mock_page.wait_for_selector.assert_called_with("#map-canvas", timeout=10000 // 3)


@pytest.mark.asyncio
async def test_comprehensive_render_wait_partial_failure(mock_page):
    """Test comprehensive render wait with some conditions failing."""
    # Mock images to fail, others to succeed
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # First call (images)
            raise Exception("Timeout")
        return None
    
    mock_page.wait_for_function.side_effect = side_effect
    mock_page.evaluate.return_value = None
    mock_page.wait_for_selector.return_value = None
    
    config = {
        "ensure_images_loaded": True,
        "ensure_fonts_loaded": True,
        "extra_wait_ms": 50,
        "timeout_ms": 10000
    }
    
    results = await comprehensive_render_wait(mock_page, config)
    
    # Images should fail, others should succeed
    assert not results["images_loaded"]
    assert results["fonts_loaded"]
    assert results["map_ready"]
    assert results["no_loading_indicators"]
    assert results["extra_wait"]


@pytest.mark.asyncio
async def test_comprehensive_render_wait_disabled_conditions(mock_page):
    """Test comprehensive render wait with some conditions disabled."""
    mock_page.wait_for_function.return_value = None
    mock_page.evaluate.return_value = None
    
    config = {
        "ensure_images_loaded": False,
        "ensure_fonts_loaded": False,
        "extra_wait_ms": 0,
        "timeout_ms": 10000
    }
    
    results = await comprehensive_render_wait(mock_page, config)
    
    # Disabled conditions should be marked as successful
    assert results["images_loaded"]
    assert results["fonts_loaded"]
    assert results["map_ready"]  # Always checked
    assert results["no_loading_indicators"]  # Always checked
    assert results["extra_wait"]
    
    # Fonts and images shouldn't be checked when disabled
    mock_page.evaluate.assert_not_called()
    # Only map and loading indicators should be checked
    assert mock_page.wait_for_function.call_count == 2

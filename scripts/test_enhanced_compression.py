#!/usr/bin/env python3
"""
Test script for the enhanced GIF compression system.

Tests watermark scaling, compression quality, and external tool integration.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.compression_service import CompressionService
from app.compressor.external_tools import ExternalToolManager
from app.utils.image_ops import watermark_text
from PIL import Image
from app.logger import get_logger

logger = get_logger(__name__)


def test_dynamic_watermarks():
    """Test dynamic watermark scaling across different image sizes."""
    print("🔍 Testing Dynamic Watermark Scaling...")
    
    # Test different image sizes
    test_sizes = [
        (640, 480, "SD"),
        (1280, 720, "HD"),
        (1920, 1080, "Full HD"),
        (3840, 2160, "4K")
    ]
    
    for width, height, label in test_sizes:
        # Create test image with map-like colors
        img = Image.new('RGB', (width, height), color=(70, 130, 180))  # Steel blue background
        
        # Add some map-like details
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([width//4, height//4, 3*width//4, 3*height//4], fill=(34, 139, 34))  # Forest green
        draw.ellipse([width//3, height//3, 2*width//3, 2*height//3], fill=(255, 215, 0))  # Gold
        
        # Test watermark
        watermarked = watermark_text(
            img, 
            "GPSJAM 08-15-25", 
            "center",
            opacity=0.4,
            font_size=None,  # Dynamic sizing
            scale_factor=0.08
        )
        
        # Save for manual inspection
        output_path = f"test_watermark_{label.lower().replace(' ', '_')}.png"
        watermarked.save(output_path)
        print(f"  ✅ {label} ({width}×{height}): Dynamic watermark saved to {output_path}")
    
    print("📝 Review the generated test files to verify watermark scaling\n")


def test_external_tools():
    """Test external tool detection and availability."""
    print("🔧 Testing External Tool Integration...")
    
    tool_manager = ExternalToolManager()
    available_tools = tool_manager.detect_tools()
    
    print(f"  Gifsicle: {'✅ Available' if available_tools.get('gifsicle') else '❌ Not found'}")
    print(f"  Gifski: {'✅ Available' if available_tools.get('gifski') else '❌ Not found'}")
    
    if not any(available_tools.values()):
        print("  💡 Install tools for better compression:")
        print("     • Gifsicle: apt-get install gifsicle (Linux) or brew install gifsicle (Mac)")
        print("     • Gifski: Download from https://gif.ski/")
    
    print()
    return available_tools


def test_compression_pipeline():
    """Test the complete compression pipeline."""
    print("🎬 Testing Enhanced Compression Pipeline...")
    
    # Check if we have a real GIF to test with
    gif_candidates = [
        "results/gifs/GPSJAM_AUG_2025.gif",
        "results/gifs/*.gif"
    ]
    
    test_gif = None
    for candidate in gif_candidates:
        if Path(candidate).exists():
            test_gif = candidate
            break
        elif "*" in candidate:
            # Try glob pattern
            import glob
            matches = glob.glob(candidate)
            if matches:
                test_gif = matches[0]
                break
    
    if not test_gif:
        print("  ⚠️ No existing GIF found to test compression")
        print("  💡 Generate a GIF first using the main pipeline")
        return
    
    test_gif = Path(test_gif)
    original_size = test_gif.stat().st_size
    print(f"  📂 Testing with: {test_gif.name} ({original_size / 1024 / 1024:.2f} MB)")
    
    # Test adaptive compression (should skip if already small)
    compression_service = CompressionService()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test 1: Adaptive compression (may skip)
        print("  🧪 Test 1: Adaptive compression...")
        result1 = compression_service.compress_gif_file(
            input_path=str(test_gif),
            output_path=str(Path(temp_dir) / "adaptive_test.gif"),
            max_size_mb=20.0  # High limit to test adaptive behavior
        )
        
        if result1.get('skipped_compression'):
            print(f"    ✅ Correctly skipped compression (already {result1['final_size_mb']:.2f} MB < 20.0 MB)")
        else:
            print(f"    ✅ Applied compression: {result1['compression_ratio']:.1f}% reduction")
        
        # Test 2: Forced compression with quality preservation
        print("  🧪 Test 2: Quality-preserving compression...")
        result2 = compression_service.compress_gif_file(
            input_path=str(test_gif),
            output_path=str(Path(temp_dir) / "quality_test.gif"),
            max_size_mb=10.0,  # Lower limit to force compression
            custom_settings={
                'enable_lossy': False,
                'use_external_tools': False,
                'allow_resize': False
            },
            force_compression=True
        )
        
        if result2.get('success'):
            print(f"    ✅ Quality compression: {result2['compression_ratio']:.1f}% reduction")
            print(f"    📊 Techniques: {', '.join(result2.get('techniques_used', []))}")
        else:
            print(f"    ❌ Quality compression failed: {result2.get('error')}")
        
        # Test 3: Aggressive compression
        print("  🧪 Test 3: Aggressive compression...")
        result3 = compression_service.compress_gif_file(
            input_path=str(test_gif),
            output_path=str(Path(temp_dir) / "aggressive_test.gif"),
            max_size_mb=5.0,  # Very low limit
            custom_settings={
                'enable_lossy': True,
                'use_external_tools': True,
                'enable_frame_subsampling': True,
                'allow_resize': True,
                'min_colors': 16
            },
            force_compression=True
        )
        
        if result3.get('success'):
            print(f"    ✅ Aggressive compression: {result3['compression_ratio']:.1f}% reduction")
            print(f"    📊 Final size: {result3['final_size_mb']:.2f} MB")
            print(f"    🛠️ Techniques: {', '.join(result3.get('techniques_used', []))}")
            
            if result3['final_size_mb'] <= 5.0:
                print("    🎯 Successfully achieved target size!")
            else:
                print("    ⚠️ Target size not reached, but maximum compression applied")
        else:
            print(f"    ❌ Aggressive compression failed: {result3.get('error')}")
    
    print()


def main():
    """Run all compression system tests."""
    print("🚀 Enhanced GIF Compression System Tests\n")
    
    # Test 1: Dynamic watermarks
    test_dynamic_watermarks()
    
    # Test 2: External tools
    available_tools = test_external_tools()
    
    # Test 3: Compression pipeline
    test_compression_pipeline()
    
    print("✅ Testing complete!")
    print("\n💡 Next steps:")
    print("   1. Review watermark test images for appropriate scaling")
    print("   2. Install missing external tools for better compression")
    print("   3. Generate a full GIF with the enhanced pipeline")
    
    # Cleanup test files
    test_files = Path().glob("test_watermark_*.png")
    for file in test_files:
        file.unlink()
    print("   4. Test files cleaned up")


if __name__ == "__main__":
    main()

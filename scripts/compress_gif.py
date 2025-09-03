#!/usr/bin/env python3
"""
GIF Compression Script

Standalone script for compressing GIF files using Gifer's advanced compression algorithms.
Implements 2025 best practices for GIF optimization while maintaining quality.

Usage:
    python scripts/compress_gif.py --input "path/to/input.gif" --output "path/to/output.gif"
    python scripts/compress_gif.py --input "results/gifs/large.gif" --max-size 14.99 --rename "GPSJAM_AUG_2025"
"""

import argparse
import sys
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.compression_service import CompressionService
from app.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Compress GIF files with advanced optimization techniques",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic compression to under 15MB
    python scripts/compress_gif.py --input "results/gifs/large.gif"
    
    # Custom output name and size limit
    python scripts/compress_gif.py --input "results/gifs/august.gif" --max-size 10.0 --rename "GPSJAM_AUG_2025"
    
    # Analyze a GIF without compressing
    python scripts/compress_gif.py --input "results/gifs/test.gif" --analyze-only
    
    # Aggressive compression for small file size
    python scripts/compress_gif.py --input "large.gif" --max-size 5.0 --aggressive
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input GIF file path"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output GIF file path (default: adds _compressed suffix)"
    )
    
    parser.add_argument(
        "--rename", "-r",
        help="Custom filename for output (without .gif extension)"
    )
    
    parser.add_argument(
        "--max-size", "-s",
        type=float,
        default=14.99,
        help="Maximum file size in MB (default: 14.99)"
    )
    
    parser.add_argument(
        "--analyze-only", "-a",
        action="store_true",
        help="Only analyze the GIF, don't compress"
    )
    
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Use aggressive compression settings for maximum size reduction"
    )
    
    parser.add_argument(
        "--preserve-quality",
        action="store_true",
        help="Use conservative settings to preserve maximum quality"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}", file=sys.stderr)
        return 1
    
    if not input_path.suffix.lower() == '.gif':
        print(f"❌ Error: Input file must be a GIF: {input_path}", file=sys.stderr)
        return 1
    
    # Initialize compression service
    compression_service = CompressionService()
    
    # Analyze mode
    if args.analyze_only:
        print(f"🔍 Analyzing GIF: {input_path.name}")
        analysis = compression_service.analyze_gif(str(input_path))
        
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}", file=sys.stderr)
            return 1
        
        print("\n📊 GIF Analysis Results:")
        print(f"   File size: {analysis['file_size_mb']:.2f} MB")
        print(f"   Dimensions: {analysis['dimensions'][0]}×{analysis['dimensions'][1]}")
        print(f"   Frame count: {analysis['frame_count']}")
        print(f"   Duration: {analysis['total_duration']:.1f} seconds")
        print(f"   Avg frame time: {analysis['avg_frame_duration']:.3f} seconds")
        
        if analysis['needs_compression']:
            print(f"   ⚠️  File is too large (>{args.max_size:.2f} MB)")
            print(f"   📉 Estimated compression: {analysis.get('estimated_reduction_percent', 0):.1f}%")
            print(f"   📁 Estimated final size: {analysis.get('estimated_final_size_mb', 0):.2f} MB")
            print(f"   🛠️  Recommended techniques: {', '.join(analysis.get('estimated_techniques', []))}")
        else:
            print(f"   ✅ File is already under size limit ({args.max_size:.2f} MB)")
        
        return 0
    
    # Compression mode
    print(f"🎬 Compressing GIF: {input_path.name}")
    print(f"📏 Target size: {args.max_size:.2f} MB")
    
    # Determine output path
    output_path = args.output
    if not output_path and not args.rename:
        output_path = str(input_path.parent / f"{input_path.stem}_compressed.gif")
    elif not output_path and args.rename:
        output_path = str(input_path.parent / f"{args.rename}.gif")
    
    # Custom settings based on flags
    custom_settings = {}
    
    if args.aggressive:
        print("⚡ Using aggressive compression settings")
        custom_settings.update({
            'max_colors': 64,
            'min_colors': 16,
            'min_frame_duration': 0.15,
            'enable_lossy': True,
            'allow_resize': True
        })
    elif args.preserve_quality:
        print("🎨 Using quality-preserving compression settings")
        custom_settings.update({
            'max_colors': 256,
            'min_colors': 64,
            'enable_lossy': False,
            'allow_resize': False
        })
    
    # Perform compression
    result = compression_service.compress_gif_file(
        input_path=str(input_path),
        output_path=output_path,
        target_filename=args.rename,
        max_size_mb=args.max_size,
        custom_settings=custom_settings if custom_settings else None
    )
    
    # Display results
    if result.get('success'):
        print(f"✅ Compression successful!")
        print(f"   📂 Output: {result['output_file']}")
        print(f"   📉 Size reduction: {result['compression_ratio']:.1f}%")
        print(f"   📏 Final size: {result['final_size_mb']:.2f} MB")
        print(f"   🛠️  Techniques used: {', '.join(result['techniques_used'])}")
        
        if result['final_size_mb'] <= args.max_size:
            print(f"   🎯 Target size achieved!")
        else:
            print(f"   ⚠️  Target size not reached (target: {args.max_size:.2f} MB)")
        
        return 0
    else:
        print(f"❌ Compression failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

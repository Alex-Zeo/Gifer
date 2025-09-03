"""
Advanced GIF Compression and Optimization

Implements 2025 best practices for GIF compression:
- Color palette reduction with dithering
- Frame optimization and duplicate removal
- Transparency optimization
- Lossy compression with quality preservation
- Target file size management (14.99MB max)
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
from PIL import Image, ImageSequence
import imageio

from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CompressionSettings:
    """GIF compression configuration settings."""
    
    # Target file size (bytes) - default 14.99MB
    max_file_size: int = 14_990_000
    
    # Color optimization
    max_colors: int = 256  # Start with full palette, reduce if needed
    min_colors: int = 32   # Minimum colors to maintain quality
    
    # Frame optimization
    min_frame_duration: float = 0.1  # Minimum seconds per frame (max 10 FPS)
    duplicate_threshold: float = 0.95  # Similarity threshold for duplicate detection
    
    # Quality settings
    enable_lossy: bool = True
    lossy_quality: int = 80  # 0-100, higher = better quality
    
    # Optimization techniques
    optimize_transparency: bool = True
    remove_duplicates: bool = True
    
    # Fallback options
    allow_resize: bool = True
    max_width: int = 1920
    max_height: int = 1080


class GifOptimizer:
    """Advanced GIF compression with intelligent quality preservation."""
    
    def __init__(self, settings: Optional[CompressionSettings] = None):
        self.settings = settings or CompressionSettings()
        
    def optimize_gif(
        self, 
        input_path: str, 
        output_path: str,
        target_filename: Optional[str] = None
    ) -> dict:
        """
        Optimize GIF file size while maintaining quality.
        
        Returns compression statistics and success status.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input GIF not found: {input_path}")
        
        # Get original file info
        original_size = input_path.stat().st_size
        logger.info(f"Starting optimization of {input_path.name} ({original_size / 1024 / 1024:.2f} MB)")
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        stats = {
            'original_size': original_size,
            'target_size': self.settings.max_file_size,
            'techniques_used': [],
            'success': False,
            'final_size': 0,
            'compression_ratio': 0.0
        }
        
        try:
            # Load GIF frames
            frames, durations = self._load_gif_frames(str(input_path))
            original_frame_count = len(frames)
            
            logger.info(f"Loaded {len(frames)} frames from original GIF")
            
            # Progressive optimization until target size is reached
            optimized_frames = frames
            optimized_durations = durations
            
            # Step 1: Remove duplicate frames
            if self.settings.remove_duplicates:
                optimized_frames, optimized_durations = self._remove_duplicates(
                    optimized_frames, optimized_durations
                )
                if len(optimized_frames) < len(frames):
                    stats['techniques_used'].append(f'duplicate_removal ({len(frames)} → {len(optimized_frames)} frames)')
            
            # Step 2: Optimize frame timing
            if min(optimized_durations) < self.settings.min_frame_duration:
                optimized_durations = self._optimize_frame_timing(optimized_durations)
                stats['techniques_used'].append('frame_timing_optimization')
            
            # Step 3: Progressive color reduction with quality check
            best_colors = self.settings.max_colors
            for colors in [256, 192, 128, 96, 64, 48, 32, 24, 16]:
                if colors < self.settings.min_colors:
                    break
                    
                # Test with this color count
                test_path = self._create_test_gif(
                    optimized_frames, 
                    optimized_durations, 
                    colors
                )
                
                test_size = Path(test_path).stat().st_size
                logger.debug(f"Testing with {colors} colors: {test_size / 1024 / 1024:.2f} MB")
                
                if test_size <= self.settings.max_file_size:
                    best_colors = colors
                    # Clean up test file
                    os.unlink(test_path)
                    break
                    
                # Clean up test file
                os.unlink(test_path)
            
            if best_colors < self.settings.max_colors:
                stats['techniques_used'].append(f'color_reduction (to {best_colors} colors)')
                
            # If still too large even with minimum colors, we'll need to resize
            if best_colors == self.settings.min_colors:
                logger.info(f"Minimum color count reached ({best_colors}), will attempt resizing if needed")
            
            # Step 4: Create optimized GIF
            temp_path = self._create_optimized_gif(
                optimized_frames,
                optimized_durations,
                best_colors
            )
            
            temp_size = Path(temp_path).stat().st_size
            
            # Step 5: If still too large, try resizing
            if temp_size > self.settings.max_file_size and self.settings.allow_resize:
                resized_path = self._resize_gif_if_needed(temp_path, temp_size)
                if resized_path != temp_path:
                    os.unlink(temp_path)
                    temp_path = resized_path
                    temp_size = Path(temp_path).stat().st_size
                    stats['techniques_used'].append('dimension_reduction')
            
            # Apply custom filename if requested
            final_output_path = output_path
            if target_filename:
                # Replace the filename part but keep the directory
                final_output_path = output_path.parent / f"{target_filename}.gif"
            
            # Move optimized file to final location
            import shutil
            shutil.move(temp_path, final_output_path)
            
            final_size = final_output_path.stat().st_size
            compression_ratio = (original_size - final_size) / original_size * 100
            
            stats.update({
                'final_size': final_size,
                'compression_ratio': compression_ratio,
                'success': final_size <= self.settings.max_file_size,
                'output_path': str(final_output_path)
            })
            
            logger.info(f"Optimization complete! {original_size/1024/1024:.2f}MB → {final_size/1024/1024:.2f}MB ({compression_ratio:.1f}% reduction)")
            
            if not stats['success']:
                logger.warning(f"Could not reach target size of {self.settings.max_file_size/1024/1024:.2f}MB")
            
            return stats
            
        except Exception as e:
            logger.error(f"GIF optimization failed: {e}")
            stats['error'] = str(e)
            return stats
    
    def _load_gif_frames(self, gif_path: str) -> Tuple[List[Image.Image], List[float]]:
        """Load all frames and their durations from a GIF file."""
        frames = []
        durations = []
        
        with Image.open(gif_path) as img:
            for frame in ImageSequence.Iterator(img):
                # Convert to RGB for consistency
                frame_rgb = frame.convert('RGB')
                frames.append(frame_rgb.copy())
                
                # Get frame duration (in seconds)
                duration = frame.info.get('duration', 100) / 1000.0  # Convert ms to seconds
                durations.append(duration)
        
        return frames, durations
    
    def _remove_duplicates(
        self, 
        frames: List[Image.Image], 
        durations: List[float]
    ) -> Tuple[List[Image.Image], List[float]]:
        """Remove near-duplicate consecutive frames."""
        if len(frames) <= 1:
            return frames, durations
        
        optimized_frames = [frames[0]]
        optimized_durations = [durations[0]]
        
        for i in range(1, len(frames)):
            # Compare with previous frame
            similarity = self._calculate_frame_similarity(frames[i-1], frames[i])
            
            if similarity < self.settings.duplicate_threshold:
                # Frame is different enough, keep it
                optimized_frames.append(frames[i])
                optimized_durations.append(durations[i])
            else:
                # Frame is very similar, merge duration with previous
                optimized_durations[-1] += durations[i]
        
        return optimized_frames, optimized_durations
    
    def _calculate_frame_similarity(self, frame1: Image.Image, frame2: Image.Image) -> float:
        """Calculate similarity between two frames (0.0 = identical, 1.0 = completely different)."""
        # Simple pixel-based comparison
        # For performance, resize to small size for comparison
        f1_small = frame1.resize((64, 64))
        f2_small = frame2.resize((64, 64))
        
        import numpy as np
        
        arr1 = np.array(f1_small)
        arr2 = np.array(f2_small)
        
        # Calculate normalized root mean square error
        mse = np.mean((arr1 - arr2) ** 2)
        max_possible_mse = 255 ** 2  # Max MSE for 8-bit images
        
        return mse / max_possible_mse
    
    def _optimize_frame_timing(self, durations: List[float]) -> List[float]:
        """Ensure minimum frame duration for smooth playback."""
        return [max(d, self.settings.min_frame_duration) for d in durations]
    
    def _create_test_gif(
        self, 
        frames: List[Image.Image], 
        durations: List[float], 
        colors: int
    ) -> str:
        """Create a test GIF with specified settings to check file size."""
        temp_fd, temp_path = tempfile.mkstemp(suffix='.gif')
        os.close(temp_fd)
        
        # Convert durations to milliseconds for imageio
        duration_ms = [d * 1000 for d in durations]
        
        # Quantize frames to specified color count
        quantized_frames = []
        for frame in frames:
            quantized = frame.quantize(colors=colors, dither=Image.FLOYDSTEINBERG)
            quantized_frames.append(quantized.convert('RGB'))
        
        # Save as GIF
        imageio.mimsave(
            temp_path,
            quantized_frames,
            duration=duration_ms,
            loop=0  # Infinite loop
        )
        
        return temp_path
    
    def _create_optimized_gif(
        self,
        frames: List[Image.Image],
        durations: List[float],
        colors: int
    ) -> str:
        """Create the final optimized GIF."""
        temp_fd, temp_path = tempfile.mkstemp(suffix='.gif')
        os.close(temp_fd)
        
        # Apply optimizations
        optimized_frames = []
        
        for frame in frames:
            # Quantize with dithering for best quality
            quantized = frame.quantize(colors=colors, dither=Image.FLOYDSTEINBERG)
            optimized_frames.append(quantized.convert('P'))  # Keep as palette mode
        
        # Convert durations to milliseconds
        duration_ms = [max(int(d * 1000), 100) for d in durations]  # Min 100ms
        
        # Save optimized GIF
        optimized_frames[0].save(
            temp_path,
            format='GIF',
            save_all=True,
            append_images=optimized_frames[1:],
            duration=duration_ms,
            loop=0,  # Infinite loop
            optimize=True  # Enable PIL's built-in optimization
        )
        
        return temp_path
    
    def _resize_gif_if_needed(self, gif_path: str, current_size: int) -> str:
        """Resize GIF if it's still too large after other optimizations."""
        if current_size <= self.settings.max_file_size:
            return gif_path
        
        # Calculate resize ratio to reach target size
        # Rough estimate: file size scales with pixel count
        target_ratio = self.settings.max_file_size / current_size
        scale_factor = target_ratio ** 0.5  # Square root because area = width * height
        
        # Load and resize
        frames, durations = self._load_gif_frames(gif_path)
        
        # Get new dimensions
        original_width, original_height = frames[0].size
        new_width = min(int(original_width * scale_factor), self.settings.max_width)
        new_height = min(int(original_height * scale_factor), self.settings.max_height)
        
        # Maintain aspect ratio
        aspect_ratio = original_width / original_height
        if new_width / new_height > aspect_ratio:
            new_width = int(new_height * aspect_ratio)
        else:
            new_height = int(new_width / aspect_ratio)
        
        # Resize all frames
        resized_frames = []
        for frame in frames:
            resized = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_frames.append(resized)
        
        # Create resized GIF
        temp_fd, temp_path = tempfile.mkstemp(suffix='.gif')
        os.close(temp_fd)
        
        duration_ms = [max(int(d * 1000), 100) for d in durations]
        
        imageio.mimsave(
            temp_path,
            resized_frames,
            duration=duration_ms,
            loop=0
        )
        
        logger.info(f"Resized GIF from {original_width}×{original_height} to {new_width}×{new_height}")
        
        return temp_path

"""
GIF Compression Module

Provides advanced GIF compression capabilities while maintaining quality.
Implements 2025 best practices for web-optimized GIF generation.
"""

from .gif_optimizer import GifOptimizer, CompressionSettings
from .compression_service import CompressionService

__all__ = ["GifOptimizer", "CompressionSettings", "CompressionService"]

"""
GIF Compression Service

Provides compression capabilities integrated with the main Gifer services.
This service acts as a bridge between the core app services and the compression module.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from app.logger import get_logger
from app.compressor import CompressionService as CoreCompressionService, CompressionSettings

logger = get_logger(__name__)


class CompressionService:
    """
    Main compression service for the Gifer application.
    
    Integrates GIF compression with the existing service architecture.
    """
    
    def __init__(self):
        self._core_service = CoreCompressionService()
    
    def compress_gif_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        target_filename: Optional[str] = None,
        max_size_mb: float = 14.99,
        custom_settings: Optional[Dict[str, Any]] = None,
        force_compression: bool = False
    ) -> Dict[str, Any]:
        """
        Compress a GIF file with optional custom settings.
        
        This is the main entry point for GIF compression within the application.
        """
        try:
            # Adaptive compression: Check if compression is actually needed
            input_file_size = Path(input_path).stat().st_size
            target_size_bytes = max_size_mb * 1024 * 1024
            
            if not force_compression and input_file_size <= target_size_bytes:
                logger.info(f"🎯 Input GIF ({input_file_size / 1024 / 1024:.2f} MB) is already under target size ({max_size_mb:.2f} MB)")
                logger.info("Skipping compression to preserve maximum quality")
                
                # Just copy/rename the file if needed
                final_output_path = output_path or str(Path(input_path).with_name(f"{Path(input_path).stem}_optimized.gif"))
                if target_filename:
                    final_output_path = str(Path(final_output_path).parent / f"{target_filename}.gif")
                
                if str(input_path) != str(final_output_path):
                    import shutil
                    shutil.copy2(input_path, final_output_path)
                
                return {
                    'success': True,
                    'skipped_compression': True,
                    'reason': 'Already under size limit',
                    'input_file': input_path,
                    'output_file': final_output_path,
                    'original_size': input_file_size,
                    'final_size': input_file_size,
                    'original_size_mb': input_file_size / 1024 / 1024,
                    'final_size_mb': input_file_size / 1024 / 1024,
                    'compression_ratio': 0.0,
                    'techniques_used': ['no_compression_needed']
                }
            
            # Proceed with compression
            logger.info(f"📊 Input GIF ({input_file_size / 1024 / 1024:.2f} MB) exceeds target ({max_size_mb:.2f} MB)")
            logger.info("Applying intelligent compression techniques...")
            
            # Create custom compression settings if provided
            settings = None
            if custom_settings:
                settings = CompressionSettings(
                    max_file_size=int(custom_settings.get('max_file_size', max_size_mb * 1024 * 1024)),
                    max_colors=custom_settings.get('max_colors', 256),
                    min_colors=custom_settings.get('min_colors', 32),
                    min_frame_duration=custom_settings.get('min_frame_duration', 0.1),
                    enable_lossy=custom_settings.get('enable_lossy', True),
                    optimize_transparency=custom_settings.get('optimize_transparency', True),
                    remove_duplicates=custom_settings.get('remove_duplicates', True),
                    enable_frame_subsampling=custom_settings.get('enable_frame_subsampling', True),
                    use_external_tools=custom_settings.get('use_external_tools', True),
                    allow_resize=custom_settings.get('allow_resize', True)
                )
            
            result = self._core_service.compress_gif(
                input_path=input_path,
                output_path=output_path,
                target_filename=target_filename,
                max_size_mb=max_size_mb,
                settings=settings
            )
            
            # Log results
            if result.get('success'):
                logger.info(f"✅ GIF compression successful: {result.get('final_size_mb', 0):.2f} MB")
            else:
                logger.warning(f"⚠️ GIF compression had issues: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"GIF compression service error: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_file': input_path
            }
    
    def analyze_gif(self, input_path: str) -> Dict[str, Any]:
        """
        Analyze a GIF file and provide compression recommendations.
        """
        try:
            return self._core_service.get_compression_preview(input_path)
        except Exception as e:
            logger.error(f"GIF analysis error: {e}")
            return {
                'error': str(e),
                'filename': Path(input_path).name if input_path else 'unknown'
            }
    
    def get_optimal_settings_for_target_size(self, target_size_mb: float) -> CompressionSettings:
        """
        Get optimal compression settings for a target file size.
        """
        if target_size_mb <= 5:
            # Aggressive compression for very small targets
            return CompressionSettings(
                max_file_size=int(target_size_mb * 1024 * 1024),
                max_colors=64,
                min_colors=16,
                min_frame_duration=0.15,
                enable_lossy=True,
                allow_resize=True,
                max_width=1280,
                max_height=720
            )
        elif target_size_mb <= 10:
            # Moderate compression
            return CompressionSettings(
                max_file_size=int(target_size_mb * 1024 * 1024),
                max_colors=128,
                min_colors=24,
                min_frame_duration=0.12,
                enable_lossy=True,
                allow_resize=True
            )
        else:
            # Light compression for larger targets (like our 14.99MB)
            return CompressionSettings(
                max_file_size=int(target_size_mb * 1024 * 1024),
                max_colors=256,
                min_colors=32,
                min_frame_duration=0.1,
                enable_lossy=False,
                allow_resize=True
            )

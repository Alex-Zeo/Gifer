"""
Compression Service Integration

Provides high-level API for GIF compression within the Gifer application.
Integrates with existing services and provides unified compression interface.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from app.logger import get_logger
from .gif_optimizer import GifOptimizer, CompressionSettings

logger = get_logger(__name__)


class CompressionService:
    """High-level service for GIF compression and optimization."""
    
    def __init__(self):
        self.optimizer = GifOptimizer()
    
    def compress_gif(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        target_filename: Optional[str] = None,
        max_size_mb: float = 14.99,
        settings: Optional[CompressionSettings] = None
    ) -> Dict[str, Any]:
        """
        Compress a GIF file with intelligent optimization.
        
        Args:
            input_path: Path to input GIF file
            output_path: Optional output path (defaults to same directory with _compressed suffix)
            target_filename: Optional custom filename (without extension)
            max_size_mb: Maximum file size in MB
            settings: Optional custom compression settings
            
        Returns:
            Dictionary with compression results and statistics
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input GIF not found: {input_path}")
        
        # Default output path
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_compressed.gif"
        else:
            output_path = Path(output_path)
        
        # Custom settings if provided
        if settings is None:
            settings = CompressionSettings(max_file_size=int(max_size_mb * 1024 * 1024))
        
        # Update optimizer with new settings
        self.optimizer.settings = settings
        
        logger.info(f"Starting GIF compression: {input_path.name} → {output_path.name}")
        logger.info(f"Target size: {max_size_mb:.2f} MB")
        
        # Perform optimization
        try:
            result = self.optimizer.optimize_gif(
                str(input_path),
                str(output_path),
                target_filename
            )
            
            # Enhanced result information
            result.update({
                'input_file': str(input_path),
                'output_file': result.get('output_path', str(output_path)),
                'timestamp': datetime.now().isoformat(),
                'target_size_mb': max_size_mb,
                'original_size_mb': result['original_size'] / 1024 / 1024,
                'final_size_mb': result['final_size'] / 1024 / 1024
            })
            
            if result['success']:
                logger.info(f"✅ Compression successful! Final size: {result['final_size_mb']:.2f} MB")
                logger.info(f"Techniques used: {', '.join(result['techniques_used'])}")
            else:
                logger.warning(f"⚠️ Compression completed but target size not reached")
                logger.warning(f"Final size: {result['final_size_mb']:.2f} MB (target: {max_size_mb:.2f} MB)")
            
            return result
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_file': str(input_path),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_compression_preview(self, input_path: str) -> Dict[str, Any]:
        """
        Get information about a GIF file and estimated compression results.
        
        Args:
            input_path: Path to GIF file
            
        Returns:
            Dictionary with file information and compression estimates
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"GIF file not found: {input_path}")
        
        # Get basic file info
        file_size = input_path.stat().st_size
        size_mb = file_size / 1024 / 1024
        
        # Load GIF to analyze
        try:
            frames, durations = self.optimizer._load_gif_frames(str(input_path))
            
            info = {
                'filename': input_path.name,
                'file_size_bytes': file_size,
                'file_size_mb': size_mb,
                'frame_count': len(frames),
                'total_duration': sum(durations),
                'avg_frame_duration': sum(durations) / len(durations) if durations else 0,
                'dimensions': frames[0].size if frames else (0, 0),
                'needs_compression': size_mb > 14.99,
                'estimated_techniques': []
            }
            
            # Estimate which compression techniques would be beneficial
            if info['avg_frame_duration'] < 0.1:
                info['estimated_techniques'].append('frame_timing_optimization')
            
            if len(frames) > 10:
                info['estimated_techniques'].append('duplicate_frame_removal')
            
            if size_mb > 20:
                info['estimated_techniques'].append('color_reduction')
            
            if size_mb > 30:
                info['estimated_techniques'].append('dimension_reduction')
            
            # Rough compression estimate
            if size_mb > 14.99:
                estimated_reduction = min(70, (size_mb - 14.99) / size_mb * 100 + 30)
                info['estimated_reduction_percent'] = estimated_reduction
                info['estimated_final_size_mb'] = size_mb * (1 - estimated_reduction / 100)
            else:
                info['estimated_reduction_percent'] = 0
                info['estimated_final_size_mb'] = size_mb
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to analyze GIF: {e}")
            return {
                'filename': input_path.name,
                'file_size_bytes': file_size,
                'file_size_mb': size_mb,
                'error': str(e)
            }
    
    def compress_directory(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        pattern: str = "*.gif",
        max_size_mb: float = 14.99
    ) -> Dict[str, Any]:
        """
        Compress all GIF files in a directory.
        
        Args:
            input_dir: Directory containing GIF files
            output_dir: Output directory (defaults to input_dir/compressed)
            pattern: File pattern to match (default: *.gif)
            max_size_mb: Maximum file size in MB
            
        Returns:
            Dictionary with batch compression results
        """
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Default output directory
        if output_dir is None:
            output_dir = input_dir / "compressed"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all GIF files
        gif_files = list(input_dir.glob(pattern))
        
        if not gif_files:
            return {
                'success': False,
                'error': f'No GIF files found matching pattern: {pattern}',
                'processed_count': 0
            }
        
        logger.info(f"Found {len(gif_files)} GIF files to compress")
        
        # Process each file
        results = {
            'success': True,
            'processed_count': 0,
            'successful_count': 0,
            'failed_count': 0,
            'total_size_before_mb': 0,
            'total_size_after_mb': 0,
            'file_results': []
        }
        
        for gif_file in gif_files:
            try:
                output_path = output_dir / gif_file.name
                
                result = self.compress_gif(
                    str(gif_file),
                    str(output_path),
                    max_size_mb=max_size_mb
                )
                
                results['file_results'].append(result)
                results['processed_count'] += 1
                
                if result['success']:
                    results['successful_count'] += 1
                    results['total_size_before_mb'] += result['original_size_mb']
                    results['total_size_after_mb'] += result['final_size_mb']
                else:
                    results['failed_count'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to compress {gif_file.name}: {e}")
                results['failed_count'] += 1
                results['file_results'].append({
                    'success': False,
                    'error': str(e),
                    'input_file': str(gif_file)
                })
        
        # Calculate overall statistics
        if results['successful_count'] > 0:
            overall_reduction = (results['total_size_before_mb'] - results['total_size_after_mb']) / results['total_size_before_mb'] * 100
            results['overall_reduction_percent'] = overall_reduction
            
        logger.info(f"Batch compression complete: {results['successful_count']}/{results['processed_count']} successful")
        
        return results

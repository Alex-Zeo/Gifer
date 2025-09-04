"""
External Tool Integration for Advanced GIF Compression

Integrates state-of-the-art GIF optimization tools like Gifsicle and Gifski
for superior quality and compression compared to pure Python approaches.
"""

import subprocess
import shutil
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExternalToolSettings:
    """Settings for external compression tools."""
    
    # Gifsicle settings
    gifsicle_path: Optional[str] = None  # Auto-detect if None
    gifsicle_lossy: int = 80  # Lossy compression level (20-200, higher = more loss)
    gifsicle_optimize: int = 3  # Optimization level (1-3)
    gifsicle_colors: Optional[int] = None  # Color limit (None = auto)
    
    # Gifski settings  
    gifski_path: Optional[str] = None  # Auto-detect if None
    gifski_quality: int = 90  # Quality (1-100)
    gifski_fps: Optional[float] = None  # FPS override
    
    # General settings
    prefer_tool: str = "gifsicle"  # "gifsicle", "gifski", or "auto"
    fallback_enabled: bool = True  # Fall back to pure Python if tools unavailable


class ExternalToolManager:
    """Manages external GIF optimization tools."""
    
    def __init__(self, settings: Optional[ExternalToolSettings] = None):
        self.settings = settings or ExternalToolSettings()
        self._tool_cache = {}  # Cache tool availability
        
    def detect_tools(self) -> Dict[str, bool]:
        """
        Detect which external tools are available on the system.
        
        Returns:
            Dictionary mapping tool names to availability status
        """
        tools = {}
        
        # Check Gifsicle
        gifsicle_path = self.settings.gifsicle_path or self._find_executable("gifsicle")
        if gifsicle_path and self._test_gifsicle(gifsicle_path):
            tools["gifsicle"] = True
            self._tool_cache["gifsicle_path"] = gifsicle_path
            logger.info(f"✅ Gifsicle detected at: {gifsicle_path}")
        else:
            tools["gifsicle"] = False
            logger.info("⚠️ Gifsicle not found. Install with: apt-get install gifsicle (Linux) or brew install gifsicle (Mac)")
        
        # Check Gifski
        gifski_path = self.settings.gifski_path or self._find_executable("gifski")
        if gifski_path and self._test_gifski(gifski_path):
            tools["gifski"] = True
            self._tool_cache["gifski_path"] = gifski_path
            logger.info(f"✅ Gifski detected at: {gifski_path}")
        else:
            tools["gifski"] = False
            logger.info("⚠️ Gifski not found. Install from: https://gif.ski/")
        
        return tools
    
    def optimize_with_gifsicle(
        self, 
        input_path: str, 
        output_path: str,
        target_size_mb: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Optimize GIF using Gifsicle with lossy compression.
        
        Args:
            input_path: Path to input GIF
            output_path: Path for optimized output
            target_size_mb: Target file size in MB (will adjust settings if needed)
            
        Returns:
            Results dictionary with success status and metrics
        """
        gifsicle_path = self._tool_cache.get("gifsicle_path")
        if not gifsicle_path:
            available_tools = self.detect_tools()
            if not available_tools.get("gifsicle"):
                return {"success": False, "error": "Gifsicle not available"}
            gifsicle_path = self._tool_cache["gifsicle_path"]
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        original_size = input_path.stat().st_size
        
        try:
            # Start with base settings
            lossy_level = self.settings.gifsicle_lossy
            optimize_level = self.settings.gifsicle_optimize
            color_limit = self.settings.gifsicle_colors
            
            # Progressive optimization if target size specified
            if target_size_mb:
                target_bytes = target_size_mb * 1024 * 1024
                attempts = []
                
                # Try different lossy levels
                for lossy in [60, 80, 100, 120, 150]:
                    result = self._run_gifsicle(
                        gifsicle_path, input_path, output_path,
                        lossy_level=lossy,
                        optimize_level=optimize_level,
                        color_limit=color_limit
                    )
                    
                    if result["success"] and output_path.exists():
                        file_size = output_path.stat().st_size
                        attempts.append({
                            "lossy": lossy,
                            "size": file_size,
                            "under_target": file_size <= target_bytes
                        })
                        
                        if file_size <= target_bytes:
                            logger.info(f"✅ Gifsicle achieved target size with lossy={lossy}")
                            break
                
                # If still too large, try with color reduction
                if not attempts or not attempts[-1]["under_target"]:
                    for colors in [128, 96, 64, 48]:
                        result = self._run_gifsicle(
                            gifsicle_path, input_path, output_path,
                            lossy_level=150,  # High lossy with color limit
                            optimize_level=optimize_level,
                            color_limit=colors
                        )
                        
                        if result["success"] and output_path.exists():
                            file_size = output_path.stat().st_size
                            if file_size <= target_bytes:
                                logger.info(f"✅ Gifsicle achieved target size with {colors} colors")
                                break
            else:
                # Single optimization attempt
                result = self._run_gifsicle(
                    gifsicle_path, input_path, output_path,
                    lossy_level=lossy_level,
                    optimize_level=optimize_level,
                    color_limit=color_limit
                )
            
            # Final results
            if output_path.exists():
                final_size = output_path.stat().st_size
                compression_ratio = (original_size - final_size) / original_size * 100
                
                return {
                    "success": True,
                    "tool": "gifsicle",
                    "original_size": original_size,
                    "final_size": final_size,
                    "compression_ratio": compression_ratio,
                    "settings_used": {
                        "lossy": lossy_level,
                        "optimize": optimize_level,
                        "colors": color_limit
                    }
                }
            else:
                return {"success": False, "error": "Gifsicle failed to create output file"}
                
        except Exception as e:
            logger.error(f"Gifsicle optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    def optimize_with_gifski(
        self,
        frames_dir: str,
        output_path: str,
        fps: float = 3.33,  # ~0.3 seconds per frame
        quality: int = 90
    ) -> Dict[str, Any]:
        """
        Create GIF using Gifski for superior quality encoding.
        
        Args:
            frames_dir: Directory containing PNG frames
            output_path: Output GIF path
            fps: Frames per second
            quality: Quality level (1-100)
            
        Returns:
            Results dictionary
        """
        gifski_path = self._tool_cache.get("gifski_path")
        if not gifski_path:
            available_tools = self.detect_tools()
            if not available_tools.get("gifski"):
                return {"success": False, "error": "Gifski not available"}
            gifski_path = self._tool_cache["gifski_path"]
        
        frames_dir = Path(frames_dir)
        output_path = Path(output_path)
        
        if not frames_dir.exists():
            return {"success": False, "error": f"Frames directory not found: {frames_dir}"}
        
        # Find PNG frames
        frame_files = sorted(frames_dir.glob("*.png"))
        if not frame_files:
            return {"success": False, "error": "No PNG frames found"}
        
        try:
            # Build Gifski command
            cmd = [
                str(gifski_path),
                "-o", str(output_path),
                "--fps", str(fps),
                "--quality", str(quality),
                "--quiet"
            ]
            
            # Add frame files
            cmd.extend([str(f) for f in frame_files])
            
            logger.info(f"Running Gifski with {len(frame_files)} frames at {fps} FPS, quality {quality}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0 and output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"✅ Gifski created GIF: {file_size / 1024 / 1024:.2f} MB")
                
                return {
                    "success": True,
                    "tool": "gifski",
                    "final_size": file_size,
                    "frame_count": len(frame_files),
                    "settings_used": {
                        "fps": fps,
                        "quality": quality
                    }
                }
            else:
                error_msg = result.stderr or "Unknown error"
                logger.error(f"Gifski failed: {error_msg}")
                return {"success": False, "error": f"Gifski failed: {error_msg}"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Gifski timed out"}
        except Exception as e:
            logger.error(f"Gifski execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _find_executable(self, name: str) -> Optional[str]:
        """Find executable in system PATH."""
        return shutil.which(name)
    
    def _test_gifsicle(self, path: str) -> bool:
        """Test if Gifsicle is working."""
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _test_gifski(self, path: str) -> bool:
        """Test if Gifski is working."""
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _run_gifsicle(
        self,
        gifsicle_path: str,
        input_path: Path,
        output_path: Path,
        lossy_level: int = 80,
        optimize_level: int = 3,
        color_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute Gifsicle with specified settings."""
        cmd = [
            str(gifsicle_path),
            f"-O{optimize_level}",
            f"--lossy={lossy_level}",
            "--no-warnings"
        ]
        
        if color_limit:
            cmd.append(f"--colors={color_limit}")
        
        cmd.extend([str(input_path), "-o", str(output_path)])
        
        try:
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return {"success": True}
            else:
                error_msg = result.stderr or "Unknown error"
                logger.warning(f"Gifsicle warning/error: {error_msg}")
                # Gifsicle sometimes returns non-zero but still creates valid output
                return {"success": output_path.exists()}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Gifsicle timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

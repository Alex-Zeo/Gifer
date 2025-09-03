# Gifer - Agent Instructions

## 🎯 Quick Start

**Gifer** is a professional web automation tool that captures screenshots from websites over time and converts them into GIFs or videos. Perfect for monitoring dashboards, tracking changes, or creating time-lapse visualizations.

## 🚀 Installation & Setup

```bash
# 1. Clone repository
git clone https://github.com/Alex-Zeo/Gifer.git
cd gifer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install browser binaries
python -m playwright install

# 4. Optional: Configure environment
cp .env.example .env
```

## 🎬 Running the Application

### GPS JAM Monitoring (Most Common Use Case)

**Windows PowerShell:**
```powershell
# Generate GIFs for any month (example: August 2025)
pwsh -ExecutionPolicy Bypass -File scripts/generate_august_gifs.ps1 -SecondsPerImage 0.3
```

**Python (Cross-platform):**
```bash
# 1. Capture screenshots for date range
python scripts/scrape_screenshots.py --start-date 2025-08-01 --end-date 2025-08-31

# 2. Generate GIF
python scripts/make_gif.py --input-dir "converter/images/gpsjam-2025-08" --output-path "results/gifs/august-2025.gif" --seconds-per-image 0.3
```

### Custom Website Monitoring

```bash
# Capture any website over time
python scripts/scrape_screenshots.py \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --lat 57.48042 \
  --lon 21.30953 \
  --zoom 5.0

# Create video instead of GIF
python scripts/make_video.py \
  --input-dir "converter/images/gpsjam-2025-08" \
  --output-path "results/videos/timeline.mp4" \
  --seconds-per-image 0.5
```

## 🛠️ Key Features

- **🌐 Smart Page Loading**: Advanced wait strategies for complete page rendering
- **🗺️ GPSJAM Specialized**: Automatic "More" button clicking and hexagon detection
- **☁️ Google Drive**: Automatic upload with `--upload-to-drive --make-public`
- **🎨 Professional Quality**: Optimized GIFs with proper timing and compression
- **⚡ Concurrent Processing**: 2 workers with intelligent rate limiting

## 📁 Output Structure

```
results/
├── gifs/               # Generated GIF files
└── videos/            # Generated video files

converter/images/
└── gpsjam-2025-08/    # Screenshot storage by date
    ├── 2025-08-01.png
    ├── 2025-08-02.png
    └── ...
```

## 🔧 Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--seconds-per-image` | Frame duration in GIF/video | `0.3` |
| `--order-strategy` | Image ordering method | `date` |
| `--overwrite` | Replace existing screenshots | `false` |
| `--upload-to-drive` | Auto-upload to Google Drive | `false` |
| `--make-public` | Make Drive files public | `false` |

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Test specific functionality
python -m pytest tests/test_gpsjam_handler.py -v
```

## 📊 Success Metrics

- **Screenshot Success Rate**: >95% for GPSJAM captures
- **File Quality**: ~3MB per 1920x1080 PNG screenshot
- **GIF Compression**: Optimized for web delivery
- **Processing Speed**: ~10-15 seconds per screenshot with full wait strategies

## 🆘 Troubleshooting

**Common Issues:**
- **"No images found"**: Check directory path in error message
- **Browser timeout**: Increase timeout in config or use `--overwrite`
- **Memory issues**: Reduce concurrency in `app/config.py`

**Debug Mode:**
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python scripts/scrape_screenshots.py --start-date 2025-08-01 --end-date 2025-08-01
```

## 🎯 Expected Results

After running for August 2025:
- **31 screenshots** captured (one per day)
- **High-quality GIF** (~18MB) showing GPS interference patterns
- **Complete automation** with GPSJAM-specific handling
- **Professional output** ready for presentations or monitoring

## 📝 Notes

- **GPSJAM Future Dates**: Hexagon timeouts are expected for future dates (no data available)
- **Rate Limiting**: Automatic 4 RPS limit to be respectful to target websites
- **Error Handling**: Graceful degradation ensures partial success even with network issues

# Kusaira Conventor

**Kusaira Conventor** is a fast and lightweight media processing toolkit designed for batch video optimization.

## 🔥 Key Features

1. **Turbo MP4 Conversion**
   - Hardware-accelerated (NVENC) batch conversion to HEVC/H.265 + AAC.
   - Significantly compresses file size with zero visual quality loss.

2. **Safe Mode (Track Cleanup)**
   - Easily strip unnecessary audio tracks, hardsubs, global tags, and embedded fonts.
   - Keep only the clean video/audio streams you need by specifying their IDs.
   - Seamlessly merge external audio files (`.mka` or `.ac3`) into your videos.

3. **Smart Renamer**
   - Automatically extracts episode numbers from messy file names and standardizes them (e.g., `[1]_Prefix.mp4`).
   - Built-in overwrite protection to prevent data loss.

## 📥 How to Use

1. Download `anime_toolkit.exe` from the **Releases** section.
2. Place the file inside the folder containing your videos.
3. Run it directly! **No installation required** (FFmpeg and MKVToolNix are already bundled inside).

## 🛠 Build from Source

If you prefer to run the Python script directly or build your own executable:

```bash
# Clone the repository
git clone https://github.com/kusaira/kusaira_conventor.git
cd kusaira_conventor

# Build the executable
pyinstaller --clean --onefile anime_toolkit.py
```
*(Note: For the remuxing and conversion features to work properly, `ffmpeg.exe` and `mkvmerge.exe` must be present in the same directory, or bundled using the `--add-binary` argument in PyInstaller).*

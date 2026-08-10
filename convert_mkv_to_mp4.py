#!/usr/bin/env python3
"""
Convert all MKV files to MP4 on TrueNAS Media share.
Runs on Linux server (clawz840) which has ffmpeg installed.
Mounts TrueNAS via NFS at /home/scott/truenas-media
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuration
MEDIA_ROOT = Path("/home/scott/truenas-media/Movies")
FFMPEG = "/usr/bin/ffmpeg"
LOG_FILE = Path.home() / "mkv_conversion.log"

# Thread-safe logging
log_lock = threading.Lock()

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with log_lock:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")

def get_video_info(filepath: Path) -> dict:
    """Get video stream info using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,bit_rate",
        "-of", "json", str(filepath)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        import json
        data = json.loads(result.stdout)
        if data.get("streams"):
            return data["streams"][0]
    except Exception as e:
        log(f"  ⚠️ ffprobe failed for {filepath.name}: {e}")
    return {}

def convert_mkv_to_mp4(mkv_path: Path, dry_run: bool = False, overwrite: bool = False) -> dict:
    """Convert a single MKV to MP4 using ffmpeg."""
    mp4_path = mkv_path.with_suffix(".mp4")
    
    # Skip if MP4 already exists and not overwriting
    if mp4_path.exists() and not overwrite:
        return {"file": mkv_path.name, "status": "skipped", "reason": "MP4 already exists"}
    
    # Get video info for logging
    info = get_video_info(mkv_path)
    vcodec = info.get("codec_name", "unknown")
    width = info.get("width", "?")
    height = info.get("height", "?")
    
    log(f"🎬 Converting: {mkv_path.name} ({vcodec}, {width}x{height})")
    
    if dry_run:
        return {"file": mkv_path.name, "status": "dry-run", "output": str(mp4_path)}
    
    # ffmpeg command: copy all streams, remux to MP4
    # -c copy = stream copy (no re-encode, fastest, no quality loss)
    # -map 0 = include all streams (video, audio, subtitles)
    # -movflags +faststart = web optimization
    cmd = [
        FFMPEG, "-y",  # overwrite output
        "-i", str(mkv_path),
        "-c", "copy",
        "-map", "0",
        "-movflags", "+faststart",
        str(mp4_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            # Verify output file exists and has size
            if mp4_path.exists() and mp4_path.stat().st_size > 0:
                size_mb = mp4_path.stat().st_size / (1024 * 1024)
                log(f"  ✅ Done: {mp4_path.name} ({size_mb:.1f} MB)")
                return {"file": mkv_path.name, "status": "success", "output": str(mp4_path), "size_mb": size_mb}
            else:
                return {"file": mkv_path.name, "status": "failed", "reason": "Output file empty/missing"}
        else:
            # If copy fails (e.g., subtitle codec not supported in MP4), try re-encoding subtitles
            log(f"  ⚠️ Stream copy failed, trying with subtitle conversion...")
            return convert_with_subtitle_fix(mkv_path, mp4_path)
    except subprocess.TimeoutExpired:
        return {"file": mkv_path.name, "status": "failed", "reason": "Timeout (5 min)"}
    except Exception as e:
        return {"file": mkv_path.name, "status": "failed", "reason": str(e)}

def convert_with_subtitle_fix(mkv_path: Path, mp4_path: Path) -> dict:
    """Fallback: convert with subtitle handling for MP4 compatibility."""
    # MP4 supports: mov_text (tx3g), not all MKV subtitle formats (ASS, SRT, PGS, etc.)
    # PGS (hdmv_pgs_subtitle) are bitmap subtitles - can't convert to text-based mov_text
    # Strategy: copy video/audio, drop unsupported subtitles
    cmd = [
        FFMPEG, "-y",
        "-i", str(mkv_path),
        "-c:v", "copy",
        "-c:a", "copy",
        "-sn",  # drop all subtitles (PGS can't go in MP4)
        "-map", "0:v",
        "-map", "0:a",
        "-movflags", "+faststart",
        str(mp4_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            if mp4_path.exists() and mp4_path.stat().st_size > 0:
                size_mb = mp4_path.stat().st_size / (1024 * 1024)
                log(f"  ✅ Done (video+audio only, subtitles dropped): {mp4_path.name} ({size_mb:.1f} MB)")
                return {"file": mkv_path.name, "status": "success", "output": str(mp4_path), "size_mb": size_mb}
        log(f"  ❌ Video+audio copy failed: {result.stderr[:500]}")
        return {"file": mkv_path.name, "status": "failed", "reason": "Video+audio copy failed"}
    except Exception as e:
        return {"file": mkv_path.name, "status": "failed", "reason": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Convert MKV to MP4 on TrueNAS Media")
    parser.add_argument("--dry-run", action="store_true", help="List files without converting")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing MP4 files")
    parser.add_argument("--workers", type=int, default=2, help="Parallel workers (default: 2)")
    parser.add_argument("--pattern", default="*.mkv", help="File pattern (default: *.mkv)")
    parser.add_argument("--max-files", type=int, help="Limit number of files to process")
    args = parser.parse_args()
    
    # Find all MKV files
    mkv_files = list(MEDIA_ROOT.rglob(args.pattern))
    if args.max_files:
        mkv_files = mkv_files[:args.max_files]
    
    log(f"{'='*60}")
    log(f"MKV → MP4 CONVERSION")
    log(f"{'='*60}")
    log(f"Source: {MEDIA_ROOT}")
    log(f"Files found: {len(mkv_files)}")
    log(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    log(f"Workers: {args.workers}")
    log(f"{'='*60}")
    
    if not mkv_files:
        log("No MKV files found!")
        return
    
    # Process files
    results = {"success": 0, "failed": 0, "skipped": 0, "dry_run": 0}
    details = []
    
    if args.dry_run:
        for mkv in mkv_files:
            mp4 = mkv.with_suffix(".mp4")
            status = "would convert" if not mp4.exists() else "would skip (exists)"
            log(f"  📝 {mkv.relative_to(MEDIA_ROOT)} → {status}")
            results["dry_run"] += 1
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(convert_mkv_to_mp4, mkv, False, args.overwrite): mkv for mkv in mkv_files}
            for future in as_completed(futures):
                result = future.result()
                details.append(result)
                results[result["status"]] = results.get(result["status"], 0) + 1
    
    # Summary
    log(f"\n{'='*60}")
    log(f"SUMMARY")
    log(f"{'='*60}")
    log(f"✅ Success: {results.get('success', 0)}")
    log(f"❌ Failed: {results.get('failed', 0)}")
    log(f"⏭️  Skipped: {results.get('skipped', 0)}")
    log(f"📝 Dry-run: {results.get('dry_run', 0)}")
    log(f"📄 Log: {LOG_FILE}")
    
    if results.get("failed", 0) > 0:
        log(f"\nFailed files:")
        for d in details:
            if d["status"] == "failed":
                log(f"  - {d['file']}: {d.get('reason', 'unknown')}")

if __name__ == "__main__":
    main()
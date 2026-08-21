#!/usr/bin/env python3
"""
TV-Shows-Series MKV to MP4 Transcoder
Runs on clawz840, mounts TrueNAS via NFS
Smart remux vs transcode based on codec
"""

import os
import sys
import subprocess
import argparse
import json
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configuration
SOURCE_ROOT = Path("/home/scott/truenas-tv")
OUTPUT_ROOT = Path("/home/scott/truenas-tv-out/TV-Shows-Series-transcoded")
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
LOG_FILE = Path.home() / "tv_transcode.log"
PLAN_FILE = Path.home() / "tv_transcode_plan.json"
SUMMARY_FILE = Path.home() / "tv_transcode_summary.json"

# Thread-safe logging
log_lock = threading.Lock()
plan_lock = threading.Lock()

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with log_lock:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")

def get_video_info(filepath: Path) -> dict:
    """Get video/audio stream info using ffprobe."""
    cmd = [
        FFPROBE, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,bit_rate,duration",
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

def get_audio_info(filepath: Path) -> dict:
    """Get audio stream info."""
    cmd = [
        FFPROBE, "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,channels,channel_layout,sample_rate",
        "-of", "json", str(filepath)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        import json
        data = json.loads(result.stdout)
        if data.get("streams"):
            return data["streams"][0]
    except Exception as e:
        log(f"  ⚠️ ffprobe audio failed for {filepath.name}: {e}")
    return {}

def get_subtitle_info(filepath: Path) -> list:
    """Get subtitle stream info."""
    cmd = [
        FFPROBE, "-v", "error",
        "-select_streams", "s",
        "-show_entries", "stream=codec_name,language",
        "-of", "json", str(filepath)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        import json
        data = json.loads(result.stdout)
        return data.get("streams", [])
    except Exception as e:
        log(f"  ⚠️ ffprobe subtitle failed for {filepath.name}: {e}")
    return []

def has_pgs_subtitles(sub_info: list) -> bool:
    """Check if any subtitle stream is PGS (bitmap)."""
    for s in sub_info:
        codec = s.get("codec_name", "").lower()
        if codec in ("hdmv_pgs_subtitle", "pgs", "dvd_subtitle", "dvdsub"):
            return True
    return False

def decide_action(vcodec: str) -> str:
    """Decide remux vs transcode based on video codec."""
    vcodec = vcodec.lower()
    if vcodec in ("h264", "hevc", "h265"):
        return "remux"
    return "transcode"

def build_ffmpeg_cmd(mkv_path: Path, mp4_path: Path, action: str, 
                      audio_info: dict, sub_info: list) -> list:
    """Build ffmpeg command based on action."""
    
    pgs_present = has_pgs_subtitles(sub_info)
    
    # Base command
    cmd = [FFMPEG, "-y", "-i", str(mkv_path)]
    
    if action == "remux":
        # Copy video, convert audio to AAC, handle subtitles
        cmd.extend(["-c:v", "copy"])
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        
        # Handle subtitles - PGS can't go to MP4, drop them
        if pgs_present:
            cmd.extend(["-sn"])  # no subtitles for PGS
        elif sub_info:
            # Text subtitles can convert to mov_text
            cmd.extend(["-c:s", "mov_text"])
        else:
            cmd.extend(["-sn"])
            
    else:  # transcode to H.265
        cmd.extend([
            "-c:v", "libx265", "-preset", "medium", "-crf", "22", "-tag:v", "hvc1",
            "-c:a", "aac", "-b:a", "192k"
        ])
        if pgs_present:
            cmd.extend(["-sn"])
        elif sub_info:
            cmd.extend(["-c:s", "mov_text"])
        else:
            cmd.extend(["-sn"])
    
    # Map all streams
    cmd.extend(["-map", "0"])
    cmd.extend(["-movflags", "+faststart"])
    cmd.append(str(mp4_path))
    
    return cmd

def convert_file(mkv_path: Path, dry_run: bool = False, overwrite: bool = False) -> dict:
    """Convert a single MKV to MP4."""
    
    # Compute relative path for output mirroring
    rel_path = mkv_path.relative_to(SOURCE_ROOT)
    mp4_path = OUTPUT_ROOT / rel_path.with_suffix(".mp4")
    mp4_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Skip if MP4 exists and not overwriting
    if mp4_path.exists() and not overwrite:
        # Quick verify - check duration matches
        try:
            src_info = get_video_info(mkv_path)
            dst_info = get_video_info(mp4_path)
            src_dur = float(src_info.get("duration", 0))
            dst_dur = float(dst_info.get("duration", 0))
            if src_dur > 0 and abs(src_dur - dst_dur) < 2:
                return {"file": str(rel_path), "status": "skipped", "reason": "MP4 exists, duration matches"}
        except:
            pass
    
    # Probe source
    vinfo = get_video_info(mkv_path)
    ainfo = get_audio_info(mkv_path)
    sinfo = get_subtitle_info(mkv_path)
    
    vcodec = vinfo.get("codec_name", "unknown")
    width = vinfo.get("width", "?")
    height = vinfo.get("height", "?")
    duration = vinfo.get("duration", "?")
    
    action = decide_action(vcodec)
    log(f"🎬 [{action.upper()}] {rel_path} ({vcodec}, {width}x{height}, {duration}s)")
    
    if dry_run:
        return {"file": str(rel_path), "status": "dry-run", "action": action, "output": str(mp4_path)}
    
    # Build and run ffmpeg
    cmd = build_ffmpeg_cmd(mkv_path, mp4_path, action, ainfo, sinfo)
    
    # Calculate timeout: 2x duration, with 1800s (30min) minimum for unknown durations
    try:
        dur = float(duration) if duration != "?" else 1800
        timeout = max(int(dur * 2), 1800)
    except:
        timeout = 1800
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            # Verify output
            if mp4_path.exists() and mp4_path.stat().st_size > 0:
                dst_info = get_video_info(mp4_path)
                dst_dur = float(dst_info.get("duration", 0))
                src_dur = float(vinfo.get("duration", 0)) if vinfo.get("duration") else 0
                
                size_mb = mp4_path.stat().st_size / (1024 * 1024)
                log(f"  ✅ Done: {mp4_path.name} ({size_mb:.1f} MB)")
                
                return {
                    "file": str(rel_path),
                    "status": "success",
                    "action": action,
                    "output": str(mp4_path),
                    "size_mb": round(size_mb, 1),
                    "duration_match": abs(src_dur - dst_dur) < 2 if src_dur > 0 else True
                }
            else:
                return {"file": str(rel_path), "status": "failed", "action": action, "reason": "Output file empty/missing"}
        else:
            log(f"  ❌ FFmpeg failed: {result.stderr[:500]}")
            return {"file": str(rel_path), "status": "failed", "action": action, "reason": result.stderr[:500]}
            
    except subprocess.TimeoutExpired:
        return {"file": str(rel_path), "status": "failed", "action": action, "reason": f"Timeout ({timeout}s)"}
    except Exception as e:
        return {"file": str(rel_path), "status": "failed", "action": action, "reason": str(e)}

def main():
    parser = argparse.ArgumentParser(description="TV-Shows-Series MKV → MP4 Transcoder")
    parser.add_argument("--dry-run", action="store_true", help="List files without converting")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing MP4 files")
    parser.add_argument("--workers", type=int, default=3, help="Parallel workers (default: 3)")
    parser.add_argument("--max-files", type=int, help="Limit number of files to process")
    parser.add_argument("--series", help="Process only specific series folder")
    args = parser.parse_args()
    
    # Find all MKV files
    if args.series:
        search_root = SOURCE_ROOT / args.series
        if not search_root.exists():
            log(f"Series folder not found: {search_root}")
            return
        mkv_files = list(search_root.rglob("*.mkv"))
    else:
        mkv_files = list(SOURCE_ROOT.rglob("*.mkv"))
    
    if args.max_files:
        mkv_files = mkv_files[:args.max_files]
    
    log(f"{'='*60}")
    log(f"TV-SERIES MKV → MP4 TRANSCODER")
    log(f"{'='*60}")
    log(f"Source: {SOURCE_ROOT}")
    log(f"Output: {OUTPUT_ROOT}")
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
            rel = mkv.relative_to(SOURCE_ROOT)
            mp4 = OUTPUT_ROOT / rel.with_suffix(".mp4")
            status = "would convert" if not mp4.exists() else "would skip (exists)"
            log(f"  📝 {rel} → {status}")
            results["dry_run"] += 1
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(convert_file, mkv, False, args.overwrite): mkv for mkv in mkv_files}
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
    
    # Save summary JSON
    summary = {
        "timestamp": datetime.now().isoformat(),
        "source": str(SOURCE_ROOT),
        "output": str(OUTPUT_ROOT),
        "results": results,
        "details": details
    }
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    log(f"📊 Summary saved: {SUMMARY_FILE}")

if __name__ == "__main__":
    main()
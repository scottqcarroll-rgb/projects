#!/usr/bin/env python3
"""
AVI to MP4 Transcoder for TV-Shows-Series
Transcodes Xvid/DivX (MPEG-4 Part 2) + MP3 AVI files to H.264 + AAC MP4
Preserves quality with CRF 18, AAC 192kbps
"""

import os
import sys
import subprocess
import argparse
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/home/scott/avi_transcode.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)


def get_media_info(filepath: Path) -> dict:
    """Get video/audio codec info using ffprobe"""
    info = {
        'video_codec': 'unknown',
        'width': 0,
        'height': 0,
        'pix_fmt': 'unknown',
        'video_bitrate': 'unknown',
        'audio_codec': 'unknown',
        'audio_sample_rate': 0,
        'audio_channels': 0,
        'audio_bitrate': 'unknown',
    }
    
    # Video info
    try:
        result = subprocess.run(['ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height,pix_fmt,bit_rate',
            '-of', 'json', str(filepath)],
            capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            v_info = json.loads(result.stdout)
            if v_info['streams']:
                v_stream = v_info['streams'][0]
                info['video_codec'] = v_stream.get('codec_name', 'unknown')
                info['width'] = v_stream.get('width', 0)
                info['height'] = v_stream.get('height', 0)
                info['pix_fmt'] = v_stream.get('pix_fmt', 'unknown')
                info['video_bitrate'] = v_stream.get('bit_rate', 'unknown')
    except Exception:
        pass

    # Audio info
    try:
        result = subprocess.run(['ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name,sample_rate,channels,bit_rate',
            '-of', 'json', str(filepath)],
            capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            a_info = json.loads(result.stdout)
            if a_info['streams']:
                a_stream = a_info['streams'][0]
                info['audio_codec'] = a_stream.get('codec_name', 'unknown')
                info['audio_sample_rate'] = int(a_stream.get('sample_rate', 0))
                info['audio_channels'] = int(a_stream.get('channels', 0))
                info['audio_bitrate'] = a_stream.get('bit_rate', 'unknown')
    except Exception:
        pass

    return info


def get_duration(filepath: Path) -> float:
    """Get video duration in seconds"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(filepath)],
            capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def get_file_size(filepath: Path) -> int:
    """Get file size in bytes"""
    try:
        return filepath.stat().st_size
    except OSError:
        return 0


def build_ffmpeg_cmd(input_file: Path, output_file: Path) -> list:
    """Build ffmpeg command for AVI -> MP4 transcode
    Xvid/DivX (MPEG-4 Part 2) + MP3 -> H.264 + AAC
    """
    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-i', str(input_file),
        # Video: H.264, CRF 18 (high quality), slow preset for efficiency
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',  # Ensure compatibility
        # Audio: AAC 192kbps stereo
        '-c:a', 'aac',
        '-b:a', '192k',
        '-ac', '2',
        # MP4 container
        '-movflags', '+faststart',
        '-map_metadata', '0',
        str(output_file)
    ]
    return cmd


def transcode_file(input_file: Path, output_file: Path, dry_run: bool = False) -> dict:
    """Transcode a single AVI file to MP4"""
    start_time = datetime.now()
    info = get_media_info(input_file)
    duration = get_duration(input_file)
    input_size = get_file_size(input_file)

    # Skip if output exists and is valid
    if output_file.exists() and output_file.stat().st_size > 0:
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-i', str(output_file)],
                capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {
                    'status': 'skipped',
                    'input_file': str(input_file),
                    'output_file': str(output_file),
                    'reason': 'Output exists and valid',
                    'input_size': input_size,
                    'output_size': output_file.stat().st_size,
                    'duration': 0,
                    'elapsed': 0,
                }
        except Exception:
            pass  # File exists but invalid, re-transcode

    log.info(f"{'[DRY-RUN] ' if dry_run else '🎬 [TRANSCODE]'} {input_file.name} "
             f"({info['video_codec']} {info['width']}x{info['height']} {info['pix_fmt']}, "
             f"{info['audio_codec']} {info['audio_sample_rate']}Hz {info['audio_channels']}ch, "
             f"{input_size/1024/1024:.1f} MB, {duration:.0f}s)")

    if dry_run:
        return {
            'status': 'dry-run',
            'input_file': str(input_file),
            'output_file': str(output_file),
            'input_size': input_size,
            'output_size': 0,
            'duration': duration,
            'elapsed': 0,
        }

    # Build command
    cmd = build_ffmpeg_cmd(input_file, output_file)

    log.info(f"  Command: {' '.join(cmd)}")

    try:
        start = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        elapsed = (datetime.now() - start).total_seconds()

        if result.returncode != 0:
            log.error(f"  ❌ FAILED: {result.stderr[-500:] if result.stderr else 'Unknown error'}")
            return {
                'status': 'failed',
                'input_file': str(input_file),
                'output_file': str(output_file),
                'error': result.stderr[-1000:] if result.stderr else 'Unknown error',
                'input_size': input_size,
                'output_size': 0,
                'duration': duration,
                'elapsed': 0,
            }

        output_size = output_file.stat().st_size
        elapsed = (datetime.now() - start_time).total_seconds()

        log.info(f"  ✅ Done: {output_file.name} ({output_size/1024/1024:.1f} MB, "
                 f"{input_size/1024/1024:.1f} MB -> {output_size/1024/1024:.1f} MB, "
                 f"{elapsed:.0f}s, {duration/elapsed:.2f}x speed)")

        return {
            'status': 'success',
            'input_file': str(input_file),
            'output_file': str(output_file),
            'input_size': input_size,
            'output_size': output_file.stat().st_size,
            'duration': duration,
            'elapsed': elapsed,
        }

    except subprocess.TimeoutExpired:
        log.error(f"  ❌ TIMEOUT after 2 hours")
        return {
            'status': 'failed',
            'input_file': str(input_file),
            'output_file': str(output_file),
            'error': 'Timeout after 7200 seconds',
            'input_size': input_size,
            'output_size': 0,
            'duration': duration,
            'elapsed': 0,
        }
    except Exception as e:
        log.error(f"  ❌ EXCEPTION: {e}")
        return {
            'status': 'failed',
            'input_file': str(input_file),
            'output_file': str(output_file),
            'error': str(e),
            'input_size': input_size,
            'output_size': 0,
            'duration': duration,
            'elapsed': 0,
        }


def process_series(series_dir: Path, output_root: Path, workers: int, dry_run: bool) -> dict:
    """Process all AVI files in a series directory"""
    avi_files = sorted(series_dir.rglob('*.avi'))
    if not avi_files:
        return {'series': series_dir.name, 'processed': 0, 'success': 0, 'failed': 0, 'skipped': 0, 'dry_run': 0, 'files': []}

    # Get series name from the directory name
    series_name = series_dir.name

    log.info(f"\n{'='*60}")
    log.info(f"Processing series: {series_name} ({len(avi_files)} episodes)")
    log.info(f"{'='*60}")

    results = []
    output_root.mkdir(parents=True, exist_ok=True)

    # Process with thread pool
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_file = {}
        for avi_file in avi_files:
            rel_path = avi_file.relative_to(series_dir)
            output_file = output_root / series_name / rel_path.with_suffix('.mp4')
            output_file.parent.mkdir(parents=True, exist_ok=True)
            future = executor.submit(transcode_file, avi_file, output_file, dry_run)
            future_to_file[future] = avi_file

        for future in as_completed(future_to_file):
            result = future.result()
            avi_file = future_to_file[future]
            log.info(f"  {result['status'].upper()}: {Path(result['input_file']).name} "
                     f"({result.get('output_size', 0)/1024/1024:.1f} MB, {result.get('elapsed', 0):.0f}s)")
            results.append(result)

    # Count results
    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    dry_run_count = sum(1 for r in results if r['status'] == 'dry-run')

    log.info(f"\n{'='*60}")
    log.info(f"Series Summary: {series_name}")
    log.info(f"  ✅ Success: {success}")
    log.info(f"  ❌ Failed: {failed}")
    log.info(f"  ⏭️  Skipped: {skipped}")
    log.info(f"  📝 Dry-run: {dry_run_count}")
    log.info(f"  📝 Total: {len(results)}")
    log.info(f"{'='*60}")

    return {
        'series': series_name,
        'processed': len(results),
        'success': success,
        'failed': failed,
        'skipped': skipped,
        'dry_run': dry_run_count,
        'files': results,
    }


def main():
    parser = argparse.ArgumentParser(description='AVI to MP4 Transcoder for TV-Shows-Series')
    parser.add_argument('--input-root', default='/home/scott/truenas-tv',
                        help='Root directory containing TV series folders')
    parser.add_argument('--output-root', default='/home/scott/truenas-tv-out/TV-Shows-Series-transcoded',
                        help='Output root directory')
    parser.add_argument('--series', help='Process specific series folder name (e.g., "Star Trek The Next Generation")')
    parser.add_argument('--workers', type=int, default=3, help='Parallel workers (default: 3)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run - show what would be done')
    parser.add_argument('--list-series', action='store_true', help='List available series and exit')
    args = parser.parse_args()

    input_root = Path(args.input_root)
    output_root = Path(args.output_root)

    if not input_root.exists():
        log.error(f"Input root does not exist: {args.input_root}")
        sys.exit(1)

    # List series
    if args.list_series:
        for d in sorted(input_root.iterdir()):
            if d.is_dir():
                avi_count = len(list(d.rglob('*.avi')))
                if avi_count > 0:
                    print(f"  {d.name}: {avi_count} AVI files")
        return

    # Process specific series or all
    if args.series:
        series_dir = input_root / args.series
        if not series_dir.exists():
            log.error(f"Series not found: {args.series}")
            sys.exit(1)
        result = process_series(series_dir, output_root, args.workers, args.dry_run)
        print(json.dumps({'series': result, 'output_root': str(output_root)}, indent=2))
    else:
        # Process all series with AVI files
        all_results = []

        for series_dir in sorted(input_root.iterdir()):
            if not series_dir.is_dir():
                continue
            avi_count = len(list(series_dir.rglob('*.avi')))
            if avi_count == 0:
                continue
            result = process_series(series_dir, output_root, args.workers, args.dry_run)
            all_results.append(result)

        # Overall summary
        total_success = sum(r['success'] for r in all_results)
        total_failed = sum(r['failed'] for r in all_results)
        total_skipped = sum(r['skipped'] for r in all_results)
        total_dry_run = sum(r['dry_run'] for r in all_results)
        total_files = sum(r['processed'] for r in all_results)

        log.info(f"\n{'='*60}")
        log.info("OVERALL SUMMARY")
        log.info(f"{'='*60}")
        log.info(f"Series processed: {len(all_results)}")
        log.info(f"  ✅ Success: {total_success}")
        log.info(f"  ❌ Failed: {total_failed}")
        log.info(f"  ⏭️  Skipped: {total_skipped}")
        log.info(f"  📝 Dry-run: {total_dry_run}")
        log.info(f"  📝 Total files: {total_files}")
        log.info(f"{'='*60}")

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'input_root': str(input_root),
            'output_root': str(output_root),
            'workers': args.workers,
            'dry_run': args.dry_run,
            'series_results': all_results,
            'total_success': total_success,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'total_dry_run': total_dry_run,
            'total_files': total_files,
        }
        summary_file = Path('/home/scott/avi_transcode_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        log.info(f"\n📄 Summary saved: /home/scott/avi_transcode_summary.json")
        log.info(f"📝 Log: /home/scott/avi_transcode.log")


if __name__ == '__main__':
    main()
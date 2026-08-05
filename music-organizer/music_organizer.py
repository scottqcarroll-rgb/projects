#!/usr/bin/env python3
"""
Music Organizer for TrueNAS - Phase 2 with LLM Artist Identification
Uses TrueNAS Filesystem API v2.0 + Ollama (Mac Studio) for artist ID
"""

import os
import json
import requests
import re
import time
from urllib.parse import quote
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Disable SSL warnings for self-signed certs
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============ CONFIGURATION ============
TRUENAS_HOST = "192.168.1.68"
TRUENAS_API_KEY = os.environ.get("TRUENAS_API_KEY", "1-J2O5MJ9HBpASjP8HdYHF7lR84oisqNUW4SVYBTz7bPJ4U17z6cbjuwC4QntqT56z")
MUSIC_ROOT = "/mnt/Family/Media/Music"
API_BASE = f"https://{TRUENAS_HOST}/api/v2.0"

# Ollama on Mac Studio (Tailscale)
OLLAMA_HOST = "100.75.240.39"
OLLAMA_PORT = 11434
OLLAMA_MODEL = "qwen3:14b"  # or hermes-4-14b:latest
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

# Audio file extensions
AUDIO_EXTS = {'.mp3', '.flac', '.m4a', '.wav', '.ogg', '.wma', '.aac', '.mp4', '.m4b'}

# Filename pattern: "Artist - Title.ext" or "Artist - Album - Title.ext"
ARTIST_TITLE_PATTERN = re.compile(r'^([^-\/]+?)\s*-\s*(.+?)(?:\.[^.]+)$')

# Session for connection pooling
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {TRUENAS_API_KEY}",
    "Content-Type": "application/json"
})
session.verify = False

# Ollama session
ollama_session = requests.Session()


@dataclass
class MusicFile:
    path: str
    filename: str
    artist: Optional[str] = None
    title: Optional[str] = None
    extension: str = ""
    size: int = 0
    matched_artist: Optional[str] = None
    match_type: str = ""  # "exact", "fuzzy", "llm", "none"
    llm_confidence: float = 0.0
    
    def __post_init__(self):
        self.extension = os.path.splitext(self.filename)[1].lower()


# ============ TRUENAS API ============
def api_call(method: str, endpoint: str, **kwargs) -> Dict:
    """Make API call to TrueNAS"""
    url = f"{API_BASE}{endpoint}"
    response = session.request(method, url, timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()


def list_directory(path: str) -> List[Dict]:
    """List directory contents via TrueNAS filesystem API"""
    return api_call("POST", f"/filesystem/listdir", json={"path": path})


def create_directory(path: str) -> bool:
    """Create directory via TrueNAS filesystem API"""
    try:
        api_call("POST", f"/filesystem/mkdir", json={"path": path})
        return True
    except requests.HTTPError as e:
        if e.response.status_code in (409, 422):  # Already exists (409=Conflict, 422=Unprocessable)
            return True
        raise


def move_file(src: str, dst: str) -> bool:
    """Copy file via TrueNAS filesystem API (source preserved)"""
    try:
        # Step 1: Get download job for source file
        download_result = api_call("POST", "/core/download", json={
            "method": "filesystem.get",
            "args": [src],
            "filename": os.path.basename(src)
        })
        job_id, download_url = download_result[0], download_result[1]
        
        # Step 2: Download the file content (need raw session without JSON content-type)
        download_session = requests.Session()
        download_session.verify = False
        download_session.headers.update({
            "Authorization": f"Bearer {TRUENAS_API_KEY}"
        })
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = download_session.get(f"https://192.168.1.68{download_url}", timeout=30)
        response.raise_for_status()
        src_content = response.content
        
        # Step 3: Upload to destination using multipart (no Content-Type header)
        upload_session = requests.Session()
        upload_session.verify = False
        upload_session.headers.update({
            "Authorization": f"Bearer {TRUENAS_API_KEY}"
        })
        files = {
            'data': (None, json.dumps({"path": dst}), 'application/json'),
            'file': ('file', src_content, 'application/octet-stream')
        }
        response = upload_session.post(f"{API_BASE}/filesystem/put", files=files, timeout=30)
        response.raise_for_status()
        
        # NOTE: Source file preserved (no delete - TrueNAS API has no delete endpoint)
        return True
    except requests.HTTPError as e:
        print(f"  ❌ Copy failed: {src} -> {dst}: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Copy failed: {src} -> {dst}: {e}")
        return False


# ============ OLLAMA LLM ============
def ollama_generate(prompt: str, model: str = OLLAMA_MODEL, temperature: float = 0.1) -> str:
    """Generate response from Ollama"""
    try:
        response = ollama_session.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"  ⚠️ Ollama error: {e}")
        return ""


def identify_artist_with_llm(filename: str, existing_artists: List[str]) -> Dict:
    """Use LLM to identify artist from ambiguous filename"""
    
    # Build prompt with context
    artist_list = ", ".join(existing_artists[:100])  # Limit context
    prompt = f"""You are a music metadata expert. Identify the ARTIST for this filename.

FILENAME: "{filename}"

KNOWN ARTISTS IN LIBRARY (sample): {artist_list}...

RULES:
1. Return ONLY the artist name, nothing else
2. If the filename is "Dr. Feelgood.mp3" → artist is "Mötley Crüe"
3. If filename is "Kickstart My Heart.mp3" → artist is "Mötley Crüe"
4. If filename is "Shout at the Devil.MP3" → artist is "Mötley Crüe"
5. If filename is "Looks That Kill.mp3" → artist is "Mötley Crüe"
6. If filename is "Too Young to Fall in Love.mp3" → artist is "Mötley Crüe"
7. If filename is "Wild Side.mp3" → artist is "Mötley Crüe"
7. If filename is "Neon Knights.mp3" → artist is "Black Sabbath"
8. If filename is "Play That Funky music white boy.mp3" → artist is "Wild Cherry"
9. If filename is "Passion Rules The Game Scorpions Savage Amusement.wma" → artist is "Scorpions"
10. If filename is "Same 'Ol Situation.mp3" → artist is "Mötley Crüe"
11. If filename is "I Walk Alone .m4a" → artist is "Cher"
12. If filename is "Blue Murder Valley of the Kings .mp3" → artist is "Blue Murder"
13. If filename is "Nothin' at All.wma" → artist is "Heart" or "Glenn Frey"
14. If filename is "Lights.mp3" → artist is "Journey" or "Ellie Goulding"
15. If filename is "Passion Rules The Game.m4a" → artist is "Scorpions"
16. If filename is "Whenever You Remember.wma" → artist is "Carrie Underwood"
16. If filename is "Love Song (rare).mp3" → artist is "Tesla" or "The Cure"
17. If filename is "Starts with Goodbye.wma" → artist is "Carrie Underwood"

Return ONLY the artist name. No explanation, no quotes, no markdown.
If uncertain, return "UNKNOWN"."""

    response = ollama_generate(prompt)
    
    # Clean up response
    artist = response.strip().strip('"').strip("'").strip()
    
    # Validate against existing artists (fuzzy match)
    if artist != "UNKNOWN":
        artist_lower = artist.lower()
        for existing in existing_artists:
            if existing.lower() == artist_lower:
                return {"artist": existing, "confidence": 0.95, "source": "llm_exact"}
            if artist_lower in existing.lower() or existing.lower() in artist_lower:
                return {"artist": existing, "confidence": 0.85, "source": "llm_fuzzy"}
        return {"artist": artist, "confidence": 0.7, "source": "llm_new"}
    
    return {"artist": None, "confidence": 0.0, "source": "llm_failed"}


# ============ FILE PROCESSING ============
def parse_artist_from_filename(filename: str) -> Optional[str]:
    """Extract artist from filename like 'Artist - Title.mp3'"""
    match = ARTIST_TITLE_PATTERN.match(filename)
    if match:
        artist = match.group(1).strip()
        artist = re.sub(r'^\d+\s*[-.]\s*', '', artist)  # Remove track numbers
        artist = artist.strip(' .-_')
        return artist if artist else None
    return None


def find_best_artist_match(artist: str, existing_artists: List[str]) -> Optional[str]:
    """Find best matching existing artist (case-insensitive, fuzzy)"""
    artist_lower = artist.lower().strip()
    
    # Exact match (case insensitive)
    for existing in existing_artists:
        if existing.lower() == artist_lower:
            return existing
    
    # Contains match
    for existing in existing_artists:
        if artist_lower in existing.lower() or existing.lower() in artist_lower:
            return existing
    
    return None


def scan_music_root() -> List[MusicFile]:
    """Scan music root for loose audio files"""
    print(f"🔍 Scanning {MUSIC_ROOT}...")
    entries = list_directory(MUSIC_ROOT)
    
    loose_files = []
    artist_dirs = []
    
    for entry in entries:
        if entry['type'] == 'FILE':
            ext = os.path.splitext(entry['name'])[1].lower()
            if ext in AUDIO_EXTS:
                artist = parse_artist_from_filename(entry['name'])
                loose_files.append(MusicFile(
                    path=f"{MUSIC_ROOT}/{entry['name']}",
                    filename=entry['name'],
                    artist=artist,
                    size=entry.get('size', 0)
                ))
        elif entry['type'] == 'DIRECTORY':
            artist_dirs.append(entry['name'])
    
    print(f"  📁 Found {len(artist_dirs)} artist directories")
    print(f"  🎵 Found {len(loose_files)} loose audio files")
    
    return loose_files, artist_dirs


def process_files(loose_files: List[MusicFile], existing_artists: List[str], use_llm: bool = True) -> List[MusicFile]:
    """Process files: parse, match, LLM identify"""
    
    # First pass: parse and match to existing artists
    for mf in loose_files:
        if mf.artist:
            matched = find_best_artist_match(mf.artist, existing_artists)
            if matched:
                mf.matched_artist = matched
                mf.match_type = "exact" if matched.lower() == mf.artist.lower() else "fuzzy"
            else:
                mf.matched_artist = mf.artist  # New artist folder needed
                mf.match_type = "new"
        else:
            mf.match_type = "none"
    
    # Count matches
    matched = [f for f in loose_files if f.match_type in ("exact", "fuzzy")]
    new_artists = [f for f in loose_files if f.match_type == "new"]
    unmatched = [f for f in loose_files if f.match_type == "none"]
    
    print(f"\n📊 Initial Analysis:")
    print(f"  ✅ Matched to existing artists: {len(matched)}")
    print(f"  📂 New artist folders needed: {len(new_artists)}")
    print(f"  ❓ Unparseable (need LLM): {len(unmatched)}")
    
    # Second pass: LLM for unmatched
    if use_llm and unmatched:
        print(f"\n🤖 Using Ollama ({OLLAMA_MODEL} @ {OLLAMA_HOST}) to identify {len(unmatched)} files...")
        
        for i, mf in enumerate(unmatched, 1):
            print(f"  [{i}/{len(unmatched)}] {mf.filename}")
            result = identify_artist_with_llm(mf.filename, existing_artists)
            
            if result["artist"]:
                mf.matched_artist = result["artist"]
                mf.match_type = result["source"]
                mf.llm_confidence = result["confidence"]
                print(f"      → {result['artist']} ({result['source']}, conf={result['confidence']:.0%})")
            else:
                print(f"      → UNKNOWN")
    
    return loose_files


def build_move_plan(files: List[MusicFile]) -> List[Dict]:
    """Build the move plan"""
    moves = []
    skipped = []
    
    for mf in files:
        if mf.matched_artist:
            src = mf.path
            dst = f"{MUSIC_ROOT}/{mf.matched_artist}/{mf.filename}"
            moves.append({
                "source": src,
                "destination": dst,
                "artist": mf.matched_artist,
                "filename": mf.filename,
                "match_type": mf.match_type,
                "llm_confidence": mf.llm_confidence
            })
        else:
            skipped.append({
                "filename": mf.filename,
                "reason": "Could not identify artist"
            })
    
    return moves, skipped


def save_plan(moves: List[Dict], skipped: List[Dict]) -> str:
    """Save plan to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_file = f"music_organize_plan_{timestamp}.json"
    
    plan = {
        "timestamp": timestamp,
        "music_root": MUSIC_ROOT,
        "total_moves": len(moves),
        "total_skipped": len(skipped),
        "moves": moves,
        "skipped": skipped
    }
    
    with open(plan_file, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print(f"\n💾 Plan saved to: {plan_file}")
    return plan_file


def execute_moves(moves: List[Dict], dry_run: bool = True) -> Dict:
    """Execute or simulate moves"""
    results = {"moved": [], "failed": [], "created_dirs": set()}
    
    if dry_run:
        print(f"\n🔍 DRY RUN - Would execute {len(moves)} moves:")
    else:
        print(f"\n🚀 EXECUTING {len(moves)} moves...")
    
    for i, move in enumerate(moves, 1):
        artist = move["artist"]
        filename = move["filename"]
        src = move["source"]
        dst = move["destination"]
        
        # Ensure artist directory exists
        artist_dir = f"{MUSIC_ROOT}/{artist}"
        if artist_dir not in results["created_dirs"]:
            if not dry_run:
                if create_directory(artist_dir):
                    results["created_dirs"].add(artist_dir)
                    print(f"  📁 Created: {artist}")
            else:
                print(f"  📁 Would create: {artist}")
                results["created_dirs"].add(artist_dir)
        
        if dry_run:
            print(f"  [{i}/{len(moves)}] {filename} → {artist}/")
            results["moved"].append(move)
        else:
            print(f"  [{i}/{len(moves)}] Moving: {filename} → {artist}/")
            if move_file(src, dst):
                results["moved"].append(move)
            else:
                results["failed"].append(move)
    
    return results


# ============ MAIN ============
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize music files on TrueNAS")
    parser.add_argument("--execute", action="store_true", help="Execute moves (default: dry-run)")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM identification")
    parser.add_argument("--plan-only", action="store_true", help="Only generate plan, don't execute")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"🎵 TRUENAS MUSIC ORGANIZER")
    print(f"{'='*60}")
    print(f"Source: {MUSIC_ROOT}")
    print(f"TrueNAS: {TRUENAS_HOST}")
    print(f"Ollama: {OLLAMA_MODEL} @ {OLLAMA_HOST}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"LLM: {'Disabled' if args.no_llm else 'Enabled'}")
    
    # Step 1: Scan
    loose_files, existing_artists = scan_music_root()
    
    if not loose_files:
        print("✅ No loose files to organize!")
        return
    
    # Step 2: Process (parse + match + LLM)
    processed_files = process_files(loose_files, existing_artists, use_llm=not args.no_llm)
    
    # Step 3: Build plan
    moves, skipped = build_move_plan(processed_files)
    
    # Step 4: Save plan
    plan_file = save_plan(moves, skipped)
    
    # Step 5: Show summary
    print(f"\n📋 PLAN SUMMARY:")
    print(f"  ✅ Moves planned: {len(moves)}")
    print(f"  ⏭️  Skipped: {len(skipped)}")
    
    if moves:
        by_type = {}
        for m in moves:
            by_type[m['match_type']] = by_type.get(m['match_type'], 0) + 1
        for t, c in sorted(by_type.items()):
            print(f"    {t}: {c}")
    
    if skipped:
        print(f"\n⏭️  Skipped files:")
        for s in skipped:
            print(f"    - {s['filename']}: {s['reason']}")
    
    # Step 6: Execute or dry run
    if not args.plan_only:
        if args.execute:
            if not args.yes:
                confirm = input("\n⚠️  Execute moves? (yes/no): ").strip().lower()
                if confirm not in ('yes', 'y'):
                    print("Cancelled.")
                    return
            results = execute_moves(moves, dry_run=False)
            print(f"\n✅ Done! Moved: {len(results['moved'])}, Failed: {len(results['failed'])}")


if __name__ == "__main__":
    main()
# TrueNAS Media Transcoding Plan
**Target:** `smb://truenas.local/media/TV-Shows-Series` (actually NFS at `/mnt/Family/Media/TV-Shows-Series` + Movies)
**Goal:** Convert all AVI and MKV files to MP4 (H.264/H.265)
**Execution:** Local LLM agent via script on `clawz840` (Linux server)

---

## 📊 Inventory Summary

### Movies (`/mnt/Family/Media/Movies/`)
| Format | Count | Examples |
|--------|-------|----------|
| AVI | ~18 | The Bounty 1984.avi, PEARL HARBOR (2001).avi, Jurassic World.2015.avi, Batman[1989].avi, Batman.Returns[1992).avi, etc. |
| MKV | ~25 | A Knights Tale 2001.mkv, Mission Impossible The Final Reckoning 2025.mkv, Forgetting Sarah Marshall 2008.mkv, Hacksaw Ridge 2016.mkv, Inglourious Basterds 2009.mkv, Die.Hard.1988.mkv, Schindler's List (1993).mkv, etc. |

### TV-Shows-Series (`/mnt/Family/Media/TV-Shows-Series/`)
| Series | MKV Count | Notes |
|--------|-----------|-------|
| The Pillars of the Earth | 8 | S01E01-E08 |
| The White Queen | 10 | S01E01-E10 |
| The West Wing S1 | 22 | S01E01-E22 |
| Wolf Hall | 6 | S01E01-E06 |
| The White Princess | 8 | S01E01-E08 |
| Knightfall | 10 | S01E01-E10 |
| Other series | Likely more | Need full scan |

**Total estimated files:** ~100+ (AVI + MKV combined)

---

## ⚙️ Technical Approach

### Tool: `ffmpeg` on `clawz840` (Linux server)
- Already installed or installable via `apt`
- Hardware encoding: Check for Intel QuickSync / NVIDIA NVENC / AMD VAAPI
- Fallback: software encoding (libx264 / libx265)

### Encoding Parameters

**Option A: H.264 (Maximum Compatibility)**
```bash
-c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k
```
- CRF 20 = visually transparent for most content
- Plays on everything (TVs, phones, Plex, Jellyfin, browsers)

**Option B: H.265/HEVC (Smaller Files, 30-50% savings)**
```bash
-c:v libx265 -preset medium -crf 22 -c:a aac -b:a 192k -tag:v hvc1
```
- CRF 22 ≈ CRF 20 H.264 quality
- Needs HEVC support (modern devices, Plex/Jellyfin transcode if needed)
- `-tag:v hvc1` for MP4 compatibility

**Recommendation: H.265 for new encodes, keep H.264 for already-H.264 MKVs (remux only)**

### Smart Logic
1. **AVI files** → Full transcode to H.265 MP4
2. **MKV files** → Probe video codec:
   - Already H.264/H.265 → **Remux only** (copy video, convert audio to AAC if needed)
   - Other codecs (MPEG-2, VC-1, etc.) → Full transcode to H.265
3. **Audio** → Convert to AAC 192k stereo (or keep 5.1 if present)
4. **Subtitles** → Preserve (embed as mov_text for MP4)

---

## 📁 File Organization

### Output Structure
```
/mnt/truenas-transcoded/
├── Movies/
│   ├── The Bounty 1984.mp4
│   ├── PEARL HARBOR (2001).mp4
│   └── ...
└── TV-Shows-Series/
    ├── The Pillars of the Earth/
    │   ├── The.Pillars.of.the.Earth.S01E01.mp4
    │   └── ...
    ├── The White Queen/
    │   └── ...
    └── ...
```

### Preservation
- **Original files UNTOUCHED** — never delete until verified
- **Log file** per conversion: `/mnt/truenas-transcoded/logs/<filename>.log`
- **Checksum verification** (optional): MD5 of source vs destination

---

## 🚀 Execution Plan

### Phase 1: Setup (One-time)
1. Mount TrueNAS NFS share on `clawz840` at `/mnt/truenas-media`
2. Create output directory `/mnt/truenas-transcoded`
3. Install ffmpeg + mediainfo (for probing)
4. Test with 1 file

### Phase 2: Inventory & Probe
1. Recursive scan for all `.avi` and `.mkv` files
2. For each file, run `ffprobe` to detect:
   - Video codec, resolution, bitrate, frame rate
   - Audio codec, channels, sample rate
   - Subtitle tracks
3. Generate conversion plan CSV

### Phase 3: Batch Conversion
1. Process files in parallel (2-4 concurrent based on CPU)
2. For each file:
   - Determine strategy (remux vs transcode)
   - Run ffmpeg with appropriate params
   - Verify output (duration matches, file > 0)
   - Log success/failure
3. Generate summary report

### Phase 4: Verification & Cleanup
1. Spot-check 10% of outputs (play in VLC/mpv)
2. Compare file sizes (H.265 should be smaller than AVI/original MKV)
3. Optional: Generate Plex/Jellyfin library refresh

---

## 🤖 Local LLM Agent Execution

### Agent Role
The "local LLM agent" will be a **Python script running on `clawz840`** that:
1. Reads the inventory
2. Decides remux vs transcode per file
3. Executes ffmpeg commands
4. Logs results
5. Handles errors/retries

### Why Not a "Real" LLM?
- ffmpeg is deterministic — no LLM reasoning needed per file
- The "agent" = orchestration script with decision logic
- Can be triggered via cron, systemd timer, or manual run

### Script Location
```
/home/scott/projects/transcode_agent/
├── transcode_agent.py      # Main orchestrator
├── config.yaml             # Settings (paths, quality, parallelism)
├── inventory.json          # Generated file list with probe data
├── plan.csv                # Generated conversion plan
└── logs/                   # Per-file logs
```

---

## ✅ Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| All AVI → MP4 | 100% |
| All MKV → MP4 (remux or transcode) | 100% |
| Original files preserved | Yes |
| Audio playable (AAC) | Yes |
| Subtitles preserved | Yes |
| No corrupted outputs | 0 |
| Summary report generated | Yes |

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Disk space on TrueNAS | Monitor `df -h`; output to separate dataset |
| ffmpeg hangs on corrupt files | Timeout per file (e.g., 2x duration) |
| Permission issues | Run as user with RW access to NFS share |
| Network interrupt | Resume from inventory (skip completed) |
| H.265 not playing on old TVs | Keep H.264 option in config |

---

## 📋 Next Steps (Your Approval Needed)

1. **Confirm encoding choice:** H.265 (recommended) or H.264?
2. **Mount method:** NFS (current) or SMB? NFS is faster for batch.
3. **Parallelism:** 2, 3, or 4 concurrent jobs? (Based on clawz840 CPU cores)
4. **Delete originals after?** Default: NO — keep originals
5. **Schedule:** One-time run or recurring cron?

---

**Ready to execute when you approve the plan.**
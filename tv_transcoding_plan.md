# TrueNAS TV-Shows-Series Transcoding Plan (FINAL)
**Target:** `smb://truenas.local/media/TV-Shows-Series` → NFS at `192.168.1.68:/mnt/Family/Media/TV-Shows-Series`
**Scope:** **ONLY TV-Shows-Series** — Movies folder EXCLUDED
**Action:** Convert all MKV → MP4 (no AVI files found in this share)
**Deletion:** **NEVER** — originals preserved

---

## 📊 Inventory: TV-Shows-Series Only

| Series | Episodes | Current Codec | Action Needed |
|--------|----------|---------------|---------------|
| The Pillars of the Earth | 8 | H.265 10-bit (x265) | **Remux only** (copy video, convert audio to AAC) |
| The White Queen | 10 | H.264 (x264) | **Remux only** (copy video, convert audio to AAC) |
| The West Wing S1 | 22 | Likely H.264 | Probe → Remux if H.264/H.265 |
| Wolf Hall | 6 | Likely H.264 | Probe → Remux if H.264/H.265 |
| The White Princess | 8 | Likely H.264 | Probe → Remux if H.264/H.265 |
| Knightfall | 10 | Likely H.264 | Probe → Remux if H.264/H.265 |
| **Total** | **64** | | |

**No AVI files found in TV-Shows-Series.**

---

## ⚙️ Technical Spec

### Encoding Strategy
| Source Codec | Action | FFmpeg Params |
|--------------|--------|---------------|
| H.264 / H.265 | **Remux** (fast, no quality loss) | `-c:v copy -c:a aac -b:a 192k -movflags +faststart` |
| Other (MPEG-2, VC-1, etc.) | **Transcode to H.265** | `-c:v libx265 -preset medium -crf 22 -c:a aac -b:a 192k -tag:v hvc1 -movflags +faststart` |

### Audio Handling
- Convert all audio → AAC 192k stereo (or 5.1 if source has 5.1)
- `-c:a aac -b:a 192k -ac 2` (stereo) or auto-detect channels

### Subtitles
- Preserve all subtitle tracks → `mov_text` (MP4 compatible)
- `-c:s mov_text`

### Output Container
- MP4 with `-movflags +faststart` for streaming

---

## 🤖 Local Agent: Python Orchestrator on `clawz840`

### Structure
```
/home/scott/projects/tv_transcoder/
├── tv_transcoder.py        # Main agent
├── config.yaml             # Settings
├── inventory.json          # Auto-generated
├── plan.json               # Auto-generated (remux vs transcode per file)
├── logs/                   # Per-file logs
└── summary.json            # Final report
```

### Agent Logic
1. **Mount** TrueNAS NFS at `/mnt/truenas-tv`
2. **Scan** recursively for `.mkv` files
3. **Probe** each with `ffprobe` (video codec, audio, subs, duration)
4. **Decide** remux vs transcode per file
5. **Execute** in parallel (2-4 workers)
6. **Verify** output (duration match, file > 0, playable)
7. **Log** everything, write summary

### Parallelism
- Check `nproc` on clawz840 → use 50% cores (default 2-4)
- Queue-based worker pool

### Resume Capability
- Skip files with existing `.mp4` output + matching duration
- Track progress in `plan.json`

---

## 📁 Output Structure (Mirror)
```
/mnt/truenas-tv-transcoded/
├── The Pillars of the Earth/
│   ├── The.Pillars.of.the.Earth.S01E01.mp4
│   └── ...
├── The White Queen/
│   ├── the.white.queen.s01e01.mp4
│   └── ...
├── The West Wing 1999 Season 1 Complete 720p/
│   ├── The West Wing S01E01 Pilot.mp4
│   └── ...
├── Wolf Hall/
├── The White Princess/
└── Knightfall/
```

---

## ✅ Acceptance Criteria
- [ ] All 64 MKV → MP4
- [ ] Originals untouched
- [ ] Audio plays (AAC)
- [ ] Subtitles work
- [ ] Duration matches source (±1 sec)
- [ ] Summary report with success/fail counts

---

## 🚀 Ready to Execute

**Mount command:**
```bash
sudo mount -t nfs 192.168.1.68:/mnt/Family/Media/TV-Shows-Series /mnt/truenas-tv
```

**Output mount:**
```bash
sudo mount -t nfs 192.168.1.68:/mnt/Family/Media /mnt/truenas-tv-out
# (write to /mnt/truenas-tv-out/TV-Shows-Series-transcoded/)
```

**Or write locally on clawz840 then rsync to TrueNAS.**

---

**Confirm: Proceed with H.265 remux/transcode, 3 parallel workers, output to TrueNAS NFS?**
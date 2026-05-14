# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL: Linux Server Setup

**ON EVERY SESSION START:** You must read `SETUP_SUMMARY.md` in this directory. It contains:

- Server login credentials and connection methods
- SSH configuration (Host: `clawz840`, IP: `100.124.71.12`)
- Project locations on the Linux server (`~/projects/`)
- Tailscale VPN network configuration
- Daily automated tasks and monitoring
- Quick start commands for all operations

**Never ask the user how to login to the Linux server.** If you need to SSH, use `ssh clawz840` and reference the setup guide.

---

## ⚠️ CRITICAL: GitHub Push Protocol

**EVERY skill, project, or file created on this server must be committed and pushed to GitHub immediately.**

- After every `git commit` → immediately run `git push`
- Every new project folder → add to git, commit, push
- Every new skill (.md file) → copy to `/home/scott/projects/.claude/skills/`, commit, push
- Skills live in TWO places: `~/.claude/skills/` (active) AND `projects/.claude/skills/` (backed up to GitHub)
- Never leave work only on the server — if the server is lost, GitHub is the backup

**No exceptions. Every session. Every change.**

---

## Repository Overview

This repository is a **collection of independent projects and tools**, not a monolithic codebase. Each project operates independently:

1. **Wedding Venue Research Tool** — The primary project. Researches distressed/challenged wedding venues, scores them on acquisition and partnership potential, and generates data + visual reports.
2. **Game Projects** — Standalone games (tic-tac-toe, top-down-shooter) built with HTML/CSS/JavaScript.
3. **Supporting Data** — CSV files and generated HTML reports.

## Wedding Venue Research Tool

### The Venue-Dossier Skill

The main tool is a custom Claude Code skill located at `.claude/skills/venue-dossier.md`. This skill automates the research process.

**To use it:**

```bash
/venue-dossier <location>
```

Examples: `/venue-dossier "Asheville NC"`, `/venue-dossier "Nashville TN"`

**What it does:**

1. **Web Research Phase** — Runs 8+ parallel WebSearch queries to find venues with documented problems (closures, refunds, complaints, fraud, etc.).
2. **Scoring Phase** — Evaluates each venue on:
   - **Acquisition Fit Score** (1–5): How viable for acquisition based on financial distress, foreclosure status, property issues.
   - **Partnership Fit Score** (1–5): How viable for management partnership based on operational failures, communication issues, current open status.
3. **Data Output** — Generates a CSV scorecard with venue details, pain point assessments, scores, and recommended paths.
4. **Visual Output** — Produces an HTML dossier with formatted results.

### Pain Point Fields Scored

- Refund Disputes
- Communication Failures
- Undisclosed Limitations
- Financial/Debt Insolvency
- Operational Failures
- Hostile Owner Response
- Construction/Property Issues

### Data Files

- `nc_distressed_wedding_venues.csv` — Input data (venue names, locations, basic info).
- `nc_venues_scorecard.csv` — Output scorecard with all scoring results.
- `venue_dossier.html` — Generated HTML report (latest run).

### Scoring Logic

The skill uses a comprehensive rubric that applies point modifiers for various signals (media coverage, status, confidence level). The **Overall Opportunity Score** is the higher of Acquisition vs Partnership Fit, adjusted for data confidence, floored at 1 and capped at 5.

### Data Confidence Levels

Venues are marked with data confidence (High/Medium/Low) based on how many pain point fields can be confirmed from search results. Low confidence venues may be marked "Insufficient Data" if both scores are ≤ 2.

## Game Projects

### Tic-Tac-Toe (`tic-tac-toe.html`)

A playable tic-tac-toe game. Open directly in a browser. Fully self-contained (HTML + embedded CSS + JavaScript). No dependencies.

### Top-Down Shooter (`top-down-shooter/`)

A game project in development. Structure and build process TBD based on implementation.

## Git Workflow

**Commit and push regularly.** This is critical for preserving work and maintaining a clear history.

- **Commit frequently** — Every time you complete a meaningful change (fix, feature, data update), commit with a clean, descriptive message.

- **Push to GitHub regularly** — Push after each commit or batch of related commits. Do not accumulate unpushed work.
- **Commit message standards:**
  - Start with a verb: "Add", "Fix", "Update", "Refactor", "Remove"
  - Keep the first line under 70 characters
  - Use present tense: "Add venue dossier" not "Added venue dossier"
  - If needed, add a body explaining the why (not just the what)

**Examples:**

- `Add venue scoring rubric for financial distress signals`
- `Fix tic-tac-toe board reset logic`
- `Update NC venues scorecard with new research data`

This ensures we never lose work and maintain a clear audit trail of what changed and when.

## Development Notes

### Environment

- **OS:** Windows (PowerShell for scripts)
- **IDE:** VS Code
- **Main Directory:** `Desktop/Claude_Code`

### When Adding Features or Fixes

- **Venue Tool:** If modifying the skill, test with at least 2–3 locations to verify research queries and scoring logic.
- **Games:** Test in a browser before committing. Ensure no console errors.
- **Data Processing:** Verify CSV outputs are valid and human-readable.

### Before Starting Complex Tasks

- Check for the latest superpowers skills (brainstorming, plans, debugging) which provide structured workflows.
- If a session error occurs, refer to this file and `.claude/skills/` for recovery context.

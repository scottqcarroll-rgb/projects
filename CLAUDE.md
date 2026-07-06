# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL: Session Continuity — Read Previous Sessions

**ON EVERY SESSION START:** Read the most recent session log from `.claude/sessions/`. Session logs are named `YYYY-MM-DD.md` and contain a full summary of what was built, decisions made, next steps, and active projects.

```bash
ls /home/scott/projects/.claude/sessions/
```

Read the most recent file to get full context before starting any work. This is how you know what Scott has been working on without him having to explain it every time.

**At the END of every session:** Save a new session log to `.claude/sessions/YYYY-MM-DD.md` (use today's date), then commit and push it to GitHub.

---

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

This repository is a **collection of independent projects and tools**, not a monolithic codebase. Each project operates independently. Current projects live under `projects/` and are tracked here: https://github.com/scottqcarroll-rgb/projects

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

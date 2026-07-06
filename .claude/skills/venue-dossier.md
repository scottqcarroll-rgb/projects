# Skill: venue-dossier

Generate a distressed wedding venue intelligence dossier for any location.

## Invocation

```
/venue-dossier <location>
```

Examples:
- `/venue-dossier Asheville NC`
- `/venue-dossier Charlotte NC`
- `/venue-dossier Georgia`
- `/venue-dossier Nashville TN`

## What This Skill Does

Runs web research, scores venues on acquisition and partnership fit, generates a CSV scorecard, and produces a visual HTML dossier — all for the specified location.

---

## EXECUTION INSTRUCTIONS

When this skill is invoked, follow these phases exactly.

### Phase 1 — Web Research

Run ALL of these search queries in parallel using WebSearch. Replace `{LOCATION}` with the user-supplied location.

**Batch A — News & Media (run in parallel):**
1. `"wedding venue" {LOCATION} closed OR foreclosed OR "refund dispute" OR bankruptcy 2023 2024 2025`
2. `"wedding venue" {LOCATION} "bad experience" OR "do not book" OR "lost deposit" OR scam 2024 2025`
3. `"wedding venue" {LOCATION} owner arrested OR fraud OR lawsuit 2024 2025`
4. `{LOCATION} wedding venue complaints refund deposit dispute 2024 2025`

**Batch B — Local News (run in parallel):**
5. `site:wral.com OR site:wbtv.com OR site:wsoctv.com OR site:wcnc.com "wedding venue" {LOCATION} 2024 2025`
6. `{LOCATION} wedding venue closed suddenly OR abrupt closure 2024 2025`
7. `{LOCATION} wedding venue reviews "1 star" OR "poor communication" OR "lost money" 2024 2025`

**Batch C — Review Platforms:**
8. `site:theknot.com OR site:weddingwire.com OR site:zola.com {LOCATION} wedding venue negative reviews 2024`

After all searches complete, compile a candidate list. **Accept a venue only if at least 3 pain point fields can be confirmed Yes/No** (not Unknown) from the research. Discard venues with fewer than 3 confirmed signals — mark them "Insufficient Data."

For each accepted venue, also run:
- `"{VENUE NAME}" current status reviews 2025 2026`
- `"{VENUE NAME}" {LOCATION} Google rating complaints`

---

### Phase 2 — Score Each Venue

For each venue, populate all fields and apply the scoring rubric below.

#### Pain Point Fields (Yes / No / Unknown per venue)
- Refund Dispute
- Communication Failure
- Undisclosed Limitations
- Financial / Debt Insolvency
- Operational Failures
- Hostile Owner Response
- Construction / Property Issues

#### Acquisition Fit Score (base 1, floor 1, ceiling 5)

| Signal | Points |
|---|---|
| Financial / Debt Insolvency = Yes | +2 |
| Status contains "Foreclosed" | +2 |
| Status contains "Closed" (not Foreclosed) | +1 |
| Construction / Property Issues = Yes | +1 |
| Refund Dispute = Yes (active legal/financial pressure) | +1 |
| Media Coverage = Yes (national or regional broadcast) | -1 |
| Status = Open | -1 |
| 5 or more pain point fields = Unknown | -1 |

#### Management Partnership Fit Score (base 1, floor 1, ceiling 5)

| Signal | Points |
|---|---|
| Status = Open (any variant) | +2 |
| Communication Failure = Yes | +1 |
| Operational Failures = Yes | +1 |
| Hostile Owner Response = Yes | +1 |
| Google Rating at peak distress < 3.0 | +1 |
| Active bookings likely in pipeline (Open + Refund Disputes) | +1 |
| Status = Foreclosed | -2 |
| Status = Closed (not Foreclosed) | -1 |
| 5 or more pain point fields = Unknown | -1 |

#### Overall Opportunity Score (1–5)
- Take the higher of Acquisition Fit vs Management Partnership Fit
- Apply Data Confidence modifier: High = no penalty, Medium = -0.5 (round), Low = -1
- Floor 1, ceiling 5

#### Recommended Path Logic
- Data Confidence = Low AND both scores ≤ 2 → **Insufficient Data**
- Acquisition ≥ 4 AND Acquisition > Partnership → **Acquire**
- Partnership ≥ 4 AND Partnership > Acquisition → **Partner**
- Both scores 2–3 → **Monitor**
- Tie at ≥ 4 → **Acquire**

#### Outreach Priority
- Recommended Path = Acquire or Partner AND top score = 4 or 5 → **High**
- Recommended Path = Monitor → **Medium**
- Recommended Path = Insufficient Data OR Data Confidence = Low → **Low**

#### Time Sensitivity Classification
Assign based on the following:
- **Critical**: Active court proceedings, foreclosure filing, or bankruptcy — asset window open NOW
- **High**: Still-open venue with fresh media incident (< 6 months), or venue reopening within 90 days
- **Medium**: Closed voluntarily, no confirmed insolvency — financial distress may develop
- **Low**: Currently stable under new management, or insufficient data — monitor only

#### Owner Motivation Signal
- Financial/Debt Insolvency = Yes OR Status = Foreclosed → **Distressed Seller**
- Hostile Owner Response = Yes OR Operational Failures = Yes AND Status = Open → **Burned Out Operator**
- Both signals → **Distressed Seller** (financial takes priority)
- Otherwise → **Unknown**

#### Data Confidence
- Media Coverage = Yes AND ≥ 4 pain points confirmed → **High**
- Media Coverage = No but ≥ 3 pain points confirmed → **Medium**
- 3+ pain points Unknown OR Status unclear → **Low**

---

### Phase 3 — Write CSV Scorecard

Write a file named `{location_slug}_venues_scorecard.csv` (e.g., `charlotte_nc_venues_scorecard.csv`) in the current working directory.

Columns (in order):
```
Rank, Venue Name, City, Region, Status, Recommended Path,
Acquisition Fit (1-5), Management Partnership Fit (1-5),
Overall Opportunity Score (1-5), Outreach Priority, Time Sensitivity,
Data Confidence, Key Distress Signal, Outreach Angle
```

Sort rows by Overall Opportunity Score descending, then Outreach Priority (High > Medium > Low).

---

### Phase 4 — Generate HTML Dossier

Write a file named `{location_slug}_venue_dossier.html` in the current working directory.

The HTML must follow this exact structure and style. Replace all `{PLACEHOLDER}` values with real venue data.

````html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{LOCATION} Distressed Venue Targets — Strategy Dossier</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e2e8f0; min-height: 100vh; padding: 40px 24px; }
  header { max-width: 1100px; margin: 0 auto 48px; border-bottom: 1px solid #2d3748; padding-bottom: 28px; }
  header h1 { font-size: 22px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #a0aec0; }
  header h2 { font-size: 36px; font-weight: 800; color: #f7fafc; margin-top: 6px; line-height: 1.2; }
  header p { margin-top: 12px; color: #718096; font-size: 14px; }
  .legend { display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }
  .legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #a0aec0; }
  .legend-dot { width: 12px; height: 12px; border-radius: 50%; }
  .grid { max-width: 1100px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); gap: 24px; }
  .card { background: #1a1f2e; border-radius: 16px; border: 1px solid #2d3748; overflow: hidden; display: flex; flex-direction: column; transition: border-color 0.2s; }
  .card:hover { border-color: #4a5568; }
  .card-header { padding: 20px 24px 16px; border-bottom: 1px solid #2d3748; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
  .card-title-block { flex: 1; }
  .card-title { font-size: 18px; font-weight: 700; color: #f7fafc; line-height: 1.3; }
  .card-location { font-size: 12px; color: #718096; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }
  .badge-group { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; flex-shrink: 0; }
  .badge { font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 20px; letter-spacing: 0.05em; text-transform: uppercase; white-space: nowrap; }
  .badge-acquire { background: #2d1b1b; color: #fc8181; border: 1px solid #9b2c2c; }
  .badge-partner { background: #1a2d1e; color: #68d391; border: 1px solid #276749; }
  .badge-monitor { background: #1a1f2d; color: #76e4f7; border: 1px solid #2b6cb0; }
  .badge-nodata  { background: #2d2d1a; color: #f6e05e; border: 1px solid #975a16; }
  .score-ring { display: flex; align-items: center; justify-content: center; width: 52px; height: 52px; border-radius: 50%; font-size: 22px; font-weight: 900; flex-shrink: 0; }
  .score-5 { background: #1a2d20; color: #48bb78; border: 2px solid #48bb78; }
  .score-4 { background: #1a2820; color: #68d391; border: 2px solid #68d391; }
  .score-3 { background: #1e2a1a; color: #f6e05e; border: 2px solid #d69e2e; }
  .score-2 { background: #2a1e1a; color: #fbd38d; border: 2px solid #c05621; }
  .score-1 { background: #2d1a1a; color: #fc8181; border: 2px solid #9b2c2c; }
  .card-body { padding: 20px 24px; flex: 1; display: flex; flex-direction: column; gap: 16px; }
  .section-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #4a5568; margin-bottom: 6px; }
  .status-pill { display: inline-block; font-size: 12px; padding: 3px 10px; border-radius: 12px; font-weight: 600; }
  .status-open    { background: #1a2d20; color: #68d391; }
  .status-closed  { background: #2d1b1b; color: #fc8181; }
  .status-active  { background: #1a2438; color: #76e4f7; }
  .status-unclear { background: #2d2d1a; color: #f6e05e; }
  .scores-row { display: flex; gap: 12px; }
  .score-mini-block { flex: 1; background: #131720; border-radius: 8px; padding: 10px 12px; text-align: center; }
  .score-mini-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #4a5568; margin-bottom: 4px; }
  .score-mini-val { font-size: 24px; font-weight: 800; line-height: 1; }
  .score-mini-dots { display: flex; justify-content: center; gap: 3px; margin-top: 5px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: #2d3748; }
  .dot.on-acq  { background: #fc8181; }
  .dot.on-part { background: #68d391; }
  .bar-bg { flex: 1; height: 6px; background: #2d3748; border-radius: 3px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 3px; }
  .conf-high   { background: #48bb78; width: 100%; }
  .conf-medium { background: #f6e05e; width: 60%; }
  .conf-low    { background: #e53e3e; width: 25%; }
  .time-sensitivity-chip { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; padding: 5px 12px; border-radius: 20px; }
  .ts-critical { background: #2d1b1b; color: #fc8181; border: 1px solid #9b2c2c; }
  .ts-high     { background: #2d2415; color: #fbd38d; border: 1px solid #c05621; }
  .ts-medium   { background: #1a2438; color: #76e4f7; border: 1px solid #2b6cb0; }
  .ts-low      { background: #1e2030; color: #718096; border: 1px solid #4a5568; }
  .pulse { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
  .pulse-critical { background: #fc8181; animation: pulse 1.2s infinite; }
  .pulse-high     { background: #fbd38d; }
  .pulse-medium   { background: #76e4f7; }
  .pulse-low      { background: #718096; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
  .distress-box { background: #131720; border-left: 3px solid #4a5568; border-radius: 0 8px 8px 0; padding: 10px 14px; font-size: 13px; color: #a0aec0; line-height: 1.6; }
  .outreach-box { background: #131a14; border-left: 3px solid #276749; border-radius: 0 8px 8px 0; padding: 10px 14px; font-size: 13px; color: #9ae6b4; line-height: 1.6; font-style: italic; }
  .card-footer { padding: 12px 24px; border-top: 1px solid #2d3748; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #4a5568; }
  .insufficient { opacity: 0.55; }
  @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>

<header>
  <h1>{LOCATION} Distressed Wedding Venue Intelligence</h1>
  <h2>Acquisition &amp; Partnership Target Dossier</h2>
  <p>Generated {DATE} &nbsp;·&nbsp; {N} targets identified &nbsp;·&nbsp; {N_ACTIONABLE} actionable &nbsp;·&nbsp; {N_MONITOR} monitor &nbsp;·&nbsp; {N_NODATA} insufficient data</p>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#fc8181"></div> Acquire</div>
    <div class="legend-item"><div class="legend-dot" style="background:#68d391"></div> Partner</div>
    <div class="legend-item"><div class="legend-dot" style="background:#76e4f7"></div> Monitor</div>
    <div class="legend-item"><div class="legend-dot" style="background:#f6e05e"></div> Insufficient Data</div>
  </div>
</header>

<div class="grid">
  {VENUE_CARDS}
</div>

<div style="max-width:1100px;margin:48px auto 0;padding:24px;border-top:1px solid #2d3748;font-size:12px;color:#4a5568;text-align:center;">
  {LOCATION} Distressed Wedding Venue Intelligence &nbsp;·&nbsp; Compiled {DATE} &nbsp;·&nbsp; For internal strategy use only
</div>

</body>
</html>
````

#### Venue Card Template

For each venue, generate one card block using this template. Select CSS classes based on the venue's data:

- **Path badge class**: `badge-acquire` / `badge-partner` / `badge-monitor` / `badge-nodata`
- **Score ring class**: `score-5` / `score-4` / `score-3` / `score-2` / `score-1`
- **Status pill class**: `status-open` / `status-closed` / `status-active` / `status-unclear`
- **Time sensitivity class**: `ts-critical` / `ts-high` / `ts-medium` / `ts-low`
- **Pulse class**: `pulse-critical` / `pulse-high` / `pulse-medium` / `pulse-low`
- **Confidence bar class**: `conf-high` / `conf-medium` / `conf-low`
- **Acquisition dot fill**: use `on-acq` class for filled dots (fill N dots where N = Acquisition Fit Score)
- **Partnership dot fill**: use `on-part` class for filled dots (fill N dots where N = Partnership Fit Score)
- **Card wrapper**: add class `insufficient` if Recommended Path = Insufficient Data

```html
<div class="card {INSUFFICIENT_CLASS}">
  <div class="card-header">
    <div class="card-title-block">
      <div class="card-title">{VENUE_NAME}</div>
      <div class="card-location">{CITY} &nbsp;·&nbsp; {REGION}</div>
    </div>
    <div class="badge-group">
      <span class="badge {BADGE_CLASS}">{RECOMMENDED_PATH}</span>
      <span class="score-ring {SCORE_CLASS}">{OVERALL_SCORE}</span>
    </div>
  </div>
  <div class="card-body">

    <div>
      <div class="section-label">Status</div>
      <span class="status-pill {STATUS_CLASS}">{STATUS}</span>
    </div>

    <div>
      <div class="section-label">Time Sensitivity</div>
      <span class="time-sensitivity-chip {TS_CLASS}">
        <span class="pulse {PULSE_CLASS}"></span>
        {TIME_SENSITIVITY_LABEL}
      </span>
      <div style="font-size:12px;color:#718096;margin-top:8px;">{TIME_SENSITIVITY_EXPLANATION}</div>
    </div>

    <div>
      <div class="section-label">Scores</div>
      <div class="scores-row">
        <div class="score-mini-block">
          <div class="score-mini-label">Acquisition</div>
          <div class="score-mini-val" style="color:{ACQ_COLOR};">{ACQ_SCORE}</div>
          <div class="score-mini-dots">
            {ACQ_DOTS}
          </div>
        </div>
        <div class="score-mini-block">
          <div class="score-mini-label">Partnership</div>
          <div class="score-mini-val" style="color:{PART_COLOR};">{PART_SCORE}</div>
          <div class="score-mini-dots">
            {PART_DOTS}
          </div>
        </div>
        <div class="score-mini-block">
          <div class="score-mini-label">Data Confidence</div>
          <div class="score-mini-val" style="color:{CONF_COLOR};">{CONF_LABEL}</div>
          <div class="bar-bg" style="margin-top:6px;"><div class="bar-fill {CONF_BAR_CLASS}"></div></div>
        </div>
      </div>
    </div>

    <div>
      <div class="section-label">Key Distress Signals</div>
      <div class="distress-box">{KEY_DISTRESS}</div>
    </div>

    <div>
      <div class="section-label">Outreach Angle</div>
      <div class="outreach-box">{OUTREACH_ANGLE}</div>
    </div>

  </div>
  <div class="card-footer">
    <span>Source: {SOURCE}</span>
    <span>Outreach Priority: <strong style="color:{PRIORITY_COLOR}">{OUTREACH_PRIORITY}</strong></span>
  </div>
</div>
```

**Color values by score/level:**
- Score 5: `#48bb78` | Score 4: `#68d391` | Score 3: `#f6e05e` | Score 2: `#fbd38d` | Score 1: `#4a5568`
- Confidence High: `#48bb78` | Medium: `#f6e05e` | Low: `#e53e3e`
- Priority High: `#fc8181` | Medium: `#76e4f7` | Low: `#718096`

---

### Phase 5 — Open in Browser

After writing the HTML file, open it automatically using:
- On Windows: `start "{filename}.html"`
- On Mac: `open "{filename}.html"`
- On Linux: `xdg-open "{filename}.html"`

---

### Phase 6 — Report to User

After completing all phases, give the user a brief summary:
- How many venues were found and scored
- The top 3 targets with their path and score
- File names written (CSV + HTML)
- Any regions or data gaps worth noting

Keep it to 6–8 lines. Do not recite all venue data — the dossier does that.

---

## Notes

- If no distressed venues are found for the location, say so clearly and suggest broadening the search area or trying adjacent cities.
- If fewer than 3 venues qualify (meet the ≥3 confirmed pain points threshold), still generate the dossier with what was found — just note the limited dataset.
- Always source every venue to at least one URL. Never invent venue details.
- The CSV and HTML filenames should use lowercase with underscores: `charlotte_nc_venues_scorecard.csv`, `charlotte_nc_venue_dossier.html`.

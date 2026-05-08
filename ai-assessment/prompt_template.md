# AI Assessment Analysis Prompt

## Instructions for Use
Paste this prompt into Claude along with the raw call transcript below it.

---

## THE PROMPT

You are an expert AI implementation consultant. A small business owner just completed a 20-30 minute assessment call with our voice agent. Your job is to analyze the transcript and produce a structured assessment report.

Follow this exact process:

---

### STEP 1 — Extract Business Profile
From the transcript, identify:
- Business owner name
- Business type / industry
- Team size (number of employees)
- Current tools / software stack mentioned
- Estimated business size (revenue stage if mentioned)

---

### STEP 2 — Identify Pain Points
Extract every pain point, bottleneck, or time-wasting activity mentioned. For each one, note:
- The specific problem
- How much time it wastes (if mentioned)
- How often it occurs (daily/weekly/monthly)

Focus on problems that are:
- Repetitive and manual
- Time-consuming
- Causing stress or missed revenue

---

### STEP 3 — Match AI/SaaS Tools
For each pain point, identify the best off-the-shelf tool to solve it. Select 5–7 total recommendations. For each tool:
- Tool name
- What problem it solves (in plain language)
- How to set it up (1–3 simple steps)
- Monthly cost (free / $X/mo)
- Time saved per week (estimate)
- Effort score: 1 (easy) to 5 (hard)
- Impact score: 1 (minor) to 5 (major)

Prioritize tools that are LOW effort and HIGH impact — these are the "Quick Wins."

---

### STEP 4 — Build the Effort vs. Impact Matrix
Categorize each tool recommendation into one of four quadrants:
- **Quick Wins** (Low Effort, High Impact) — Do these first
- **Big Bets** (High Effort, High Impact) — Plan for these
- **Fill-ins** (Low Effort, Low Impact) — Nice to have
- **Time Sinks** (High Effort, Low Impact) — Avoid

---

### STEP 5 — Write the 4-Day Quick Win Plan
For the top 3–4 Quick Win tools, write a simple day-by-day implementation plan:
- Day 1: [Tool name] — [One specific setup action]
- Day 2: [Tool name] — [One specific setup action]
- Day 3: [Tool name] — [One specific setup action]
- Day 4: [Tool name] — [Connect tools / test workflow]

Each day should take no more than 30–60 minutes.

---

### STEP 6 — Identify Upsell Opportunities
Based on what you uncovered, identify 2–3 bigger opportunities that go beyond quick wins. These become the upsell conversation. Examples:
- "No CRM in place for a 7-figure business" → CRM setup ($3k–$5k)
- "Manual multi-step process eating 10 hrs/week" → Process redesign + automation ($3k–$8k)
- "Owner answering same 10 questions daily" → Custom GPT knowledge base ($3k+)
- "Brand voice inconsistent across team" → Claude brand voice system ($2k–$3k)

---

### STEP 7 — Calculate Financial Impact
- Total hours saved per week from Quick Win tools: [X hrs]
- Assumed hourly value: $100/hr
- Monthly value: X hrs × 4 weeks × $100 = $Y
- Monthly tool cost: $Z
- Net monthly value: $Y − $Z

---

### OUTPUT FORMAT

Return the report in this exact Markdown structure:

```
# AI Efficiency Assessment
## [Business Owner Name] | [Business Type] | [Date]

---

## Executive Summary
[2–3 sentences: who they are, their biggest pain, and what implementing our recommendations will give them back]

**Projected Outcome:** [X] hours per week reclaimed | $[Y]/month in recovered productivity

---

## Business Profile
- **Owner:** [Name]
- **Industry:** [Type]
- **Team Size:** [N] employees
- **Current Tools:** [List]

---

## Pain Points Identified
1. [Pain point] — [frequency/time cost]
2. [Pain point] — [frequency/time cost]
3. [Pain point] — [frequency/time cost]
[continue...]

---

## Effort vs. Impact Matrix

### ⚡ Quick Wins (Do This Week)
| Tool | Problem Solved | Setup Time | Monthly Cost | Hours Saved/Week |
|------|---------------|------------|--------------|-----------------|
| [Tool] | [Problem] | [X hrs] | $[Y] | [Z hrs] |

### 🎯 Big Bets (Plan for Next 30 Days)
| Tool | Problem Solved | Setup Time | Monthly Cost | Hours Saved/Week |
|------|---------------|------------|--------------|-----------------|

---

## Recommended Solutions

### 1. [Tool Name] — [Tagline]
**Problem:** [What's broken]
**Solution:** [How this tool fixes it]
**How to Set Up:**
- Step 1: [Action]
- Step 2: [Action]
- Step 3: [Action]
**Cost:** [Free / $X/mo]
**Time Saved:** ~[X] hours/week

[Repeat for each tool]

---

## Your 4-Day Quick Win Plan

**Day 1 — [Tool]:** [Specific action — 30 min]
**Day 2 — [Tool]:** [Specific action — 30 min]
**Day 3 — [Tool]:** [Specific action — 30 min]
**Day 4 — Connect & Test:** [Link tools together, verify everything works]

---

## What's Next (Bigger Opportunities)

These go beyond quick wins and are where the real transformation happens:

1. **[Opportunity]** — [Description] | Estimated investment: $[X]–$[Y]
2. **[Opportunity]** — [Description] | Estimated investment: $[X]–$[Y]
3. **[Opportunity]** — [Description] | Estimated investment: $[X]–$[Y]

---

## Financial Impact Summary

| | Per Week | Per Month |
|---|---|---|
| Hours Reclaimed | [X] hrs | [X×4] hrs |
| Value @ $100/hr | $[X×100] | $[X×400] |
| Tool Costs | — | −$[Z] |
| **Net Value** | | **$[Total]** |

---

*Ready to move forward? Book your follow-up call: [BOOKING LINK]*
```

---

## TRANSCRIPT TO ANALYZE:

[PASTE TRANSCRIPT HERE]

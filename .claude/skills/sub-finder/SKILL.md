# Subcontractor Finder Skill

## What This Skill Does
Given a government contract location and type of work, finds and vets local subcontractors in that area. Scores each sub on hunger, reliability, and fit. Outputs a prioritized call list with scripts so you can get quotes fast before the bid deadline.

---

## The Golden Rule
You are looking for HUNGRY small businesses — not big established firms that are too busy to care. The perfect sub is one that is established enough to be reliable but small enough to need your contract.

---

## Step 1 — Get the Contract Details

Ask the user:

> "What type of work does this contract require? (e.g., HVAC maintenance, landscaping, hazardous waste removal, janitorial, IT support)"

> "What city and state is the work performed in?"

> "When is the bid deadline? I'll prioritize speed accordingly."

> "Rough contract value range? This helps me find subs at the right scale."

Confirm:
> "Finding [TRADE] subcontractors in [CITY, STATE] — deadline [DATE]. Running search..."

---

## Step 2 — Search for Subcontractors

Use WebSearch to find local subs. Run these searches in parallel:

**Search 1 — Google Business:**
`[TRADE TYPE] company [CITY STATE] small business`

**Search 2 — Licensed Contractors:**
`[TRADE TYPE] licensed contractor [CITY STATE] reviews`

**Search 3 — BBB / Angi / HomeAdvisor:**
`site:bbb.org [TRADE TYPE] [CITY STATE]`
`site:angi.com [TRADE TYPE] [CITY STATE]`

**Search 4 — Government Sub Databases:**
`site:sam.gov [TRADE TYPE] [STATE]` (finds subs already registered for government work)

**Search 5 — LinkedIn:**
`[TRADE TYPE] business owner [CITY STATE]`

Collect at minimum 8–10 candidates before scoring. More is better.

---

## Step 3 — Score Each Subcontractor

For each candidate, research and score:

| Factor | Points | How to Check |
|---|---|---|
| Has a real website | +2 | Google their name |
| Google reviews: 4.0+ stars | +2 | Google Maps |
| Google reviews: 10+ reviews | +1 | Google Maps |
| Been in business 3+ years | +2 | Website, BBB, LinkedIn |
| Small team (2–20 employees) | +2 | LinkedIn, website About page |
| Already registered on SAM.gov | +3 | They know government contracts |
| Licensed in the contract state | +2 | Check state contractor board |
| Located within 50 miles of contract | +2 | Google Maps |
| Located within 100 miles | +1 | Google Maps |
| Professional email (not Gmail) | +1 | Website contact page |
| Active social media / recent posts | +1 | Facebook, Instagram, LinkedIn |
| Specializes in exact trade needed | +2 | Website services page |

Score 12+ = **HOT CALL** (call first)
Score 7–11 = **CALL** (good candidate)
Score below 7 = **BACKUP** (only if others fall through)

---

## Step 4 — Output the Call List

```
SUBCONTRACTOR CALL LIST
Trade: [TYPE OF WORK] | Location: [CITY, STATE]
Contract Deadline: [DATE] — Call HOT candidates TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 HOT CALLS — DO THESE FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [Company Name]
   Phone: [Number]
   Address: [City, State]
   Website: [URL]
   Reviews: [X stars / Y reviews]
   Why Hot: [1-line — e.g., "SAM registered, 4.8 stars, 8 years in business"]
   Distance from job: [X miles]

[repeat for each HOT candidate]

📋 CALL LIST — BACKUP OPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[condensed — name, phone, score, one-line note]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CALLING SCRIPT (read this when they pick up):

"Hi, this is Scott Carroll from Breezar Investments. We're a government
contracting firm and we have an opportunity — the [AGENCY] is putting out
a contract for [BRIEF DESCRIPTION] in [CITY]. The job runs [TIMEFRAME].
We'd like to bring you on as our subcontractor for this. I need a quote
by [DEADLINE MINUS 2 DAYS] to put together our proposal.
Are you available and interested?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO ASK FOR WHEN THEY SAY YES:
- Written quote (email or text is fine)
- Confirmation they're licensed in [STATE]
- Availability for [CONTRACT START DATE]
- Any questions about the scope of work

RED FLAGS — HANG UP AND CALL NEXT:
- "I'll get back to you" without setting a time
- "We're pretty busy right now"
- No answer to 2 calls with no callback
- Quote arrives after deadline
```

---

## Step 5 — Track Quote Collection

After the call list is delivered, ask:
> "When you get quotes back, tell me the sub's name and their number. I'll calculate your bid price based on the margin formula and past pricing data."

When user provides a quote:
- Apply 25–40% margin (lower end for competitive jobs, higher for niche)
- Cross-reference with past pricing data if available
- Flag if the sub's quote would put the bid above the historical ceiling

---

## Step 6 — Save the Sub List

Save to:
`/home/scott/projects/govt-contracts/prospect-lists/subs-[TRADE]-[CITY]-[DATE].md`

If a sub works out well — reliable, communicates, delivers — note them in the file as a **Trusted Sub** for future contracts in that region.

---

## Notes
- Always contact at least 3 subs before submitting a bid — if one falls through, you have backup
- Never reveal the government contract value to the sub upfront — get their quote first
- If a sub asks "is this for the government?" — say yes, be honest. They may actually prefer it (guaranteed payment)
- Subs that have previously worked with that government agency are gold — they already know the process
- For contracts in rural areas with thin sub markets: expand search radius to 100-150 miles
- Build a running list of trusted subs by trade and region — over time this becomes a major competitive advantage

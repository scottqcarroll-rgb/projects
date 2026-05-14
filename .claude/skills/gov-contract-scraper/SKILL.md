# Government Contract Scraper Skill

## What This Skill Does
Searches SAM.gov for active contract opportunities by PRICE. Asks how much, searches, returns results. No industry assumptions. No NAICS codes unless the user asks. Price is the primary filter.

---

## Step 1 — Load API Key

Read the API key from `/home/scott/projects/.env.samgov` (line: `SAM_API_KEY=...`).

If not found, ask the user to paste their SAM.gov API key.

---

## Step 2 — Ask Three Questions Only

**Question 1 — Max price:**
> "What's the maximum contract value you want to see? (e.g. $300,000)"

**Question 2 — Min price (optional):**
> "Any minimum? Or just show everything under that max?"

**Question 3 — Location (optional):**
> "Any specific state? Or search nationwide?"

Do NOT ask about industry. Do NOT ask about NAICS. Search broad unless the user specifically requests a category.

Confirm:
> "Searching SAM.gov for contracts under $[MAX], [location or nationwide]. Running now..."

---

## Step 3 — Make ONE API Call

Make a single GET request. Wait for it to complete before doing anything else.

```
GET https://api.sam.gov/opportunities/v2/search?
  api_key={SAM_API_KEY}
  &ptype=o,k
  &awardCeiling={MAX_PRICE}
  &postedFrom={DATE_14_DAYS_AGO}
  &postedTo={TODAY}
  &limit=25
  &offset=0
```

If a state was specified, add `&state={STATE_CODE}`.

Date format: MM/dd/yyyy

Do NOT make multiple calls. Do NOT loop through industries. ONE call. That's it.

---

## Step 4 — Score Each Result

For each contract returned, score 1–10:

| Factor | Points |
|---|---|
| Service contract (title has: maintenance, service, repair, support, cleaning, disposal, grounds, inspection, installation, management) | +3 |
| Small Business Set-Aside | +2 |
| Deadline 7+ days away | +2 |
| Deadline 3–6 days away | +1 |
| Deadline under 2 days | -3 |
| Has a listed location (city/state) | +1 |
| Value under $25K | +2 (easiest to win) |
| Value $25K–$100K | +1 |

---

## Step 5 — Output the List

```
GOVERNMENT CONTRACT OPPORTUNITIES
Under $[MAX] | [Location] | Posted last 14 days
Found: XX contracts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [Contract Title]
   Agency: [Agency]
   Location: [City, State]
   Value: $[Amount] (or "not listed")
   Deadline: [Date] ([X days away])
   Set-Aside: [Type or None]
   NAICS: [Code]
   Link: [SAM.gov URL]

[repeat for all 25]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVICE CONTRACTS TO LOOK AT FIRST:
[list only the ones with service-type titles]
```

---

## Step 6 — Save Results

Save to `/home/scott/projects/govt-contracts/prospect-lists/[DATE]-under-[MAX].md`

---

## Important Notes
- ONE API call per session. The free SAM.gov key rate-limits quickly if you fire multiple calls.
- Many contracts do not list a dollar amount upfront — the `awardCeiling` filter only catches ones that do. That is normal. Show all results and let the user decide.
- Do not filter by industry unless the user specifically asks for it.
- Do not make follow-up API calls unless the user explicitly requests more results.

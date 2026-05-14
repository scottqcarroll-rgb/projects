# Government Contract Scraper Skill

## What This Skill Does
Searches SAM.gov for active government contract opportunities matching your industries, under $350,000, in any location. Scores each opportunity and outputs a prioritized bid list. Connects to the Breezar Investments LLC government contracting business.

---

## Step 1 — Load API Key

Check for SAM.gov API key at `/home/scott/projects/.env.samgov`.

If not found, ask:
> "I need your SAM.gov API key to search contracts. Get it free at sam.gov → sign in → profile → API keys. Paste it here and I'll save it."

If provided, save to `/home/scott/projects/.env.samgov`:
```
SAM_API_KEY=their_key_here
```

Add `.env.samgov` to `.gitignore` if not already there.

---

## Step 2 — Ask Search Parameters

Ask the user (accept defaults if they say "run it" or "go"):

**Question 1 — Industry:**
> "What industry do you want to search? Or say 'all' to search across all your target industries.
> Options: HVAC, Facility Maintenance, IT Services, Construction, Landscaping, Janitorial, Hazardous Waste, Equipment Repair, All"

**Question 2 — Location:**
> "What location? City and state, just a state, or 'anywhere in the US'?"

**Question 3 — Contract Size:**
> "Max contract value? Default is $350,000. Or say 'under 25K' to start small."

**Question 4 — Date Range:**
> "How recently posted? Default: last 14 days. Or say 7 days, 30 days."

Confirm before running:
> "Searching SAM.gov for [INDUSTRY] contracts in [LOCATION], under $[AMOUNT], posted in the last [DAYS] days. Running now..."

---

## Step 3 — Map Industry to NAICS Codes

Use this mapping to build the NAICS filter:

| User Says | NAICS Codes to Search |
|---|---|
| HVAC | 238220 |
| Facility Maintenance | 561210, 811310 |
| IT Services | 541519, 334111 |
| Construction | 236220, 236118 |
| Landscaping | 561730 |
| Janitorial | 561720 |
| Hazardous Waste | 562112 |
| Equipment Repair | 811310 |
| All | 238220, 561210, 811310, 541519, 236220, 561730, 561720, 562112 |

---

## Step 4 — Call SAM.gov API

Make this GET request for each NAICS code:

```
GET https://api.sam.gov/opportunities/v2/search?
  api_key={SAM_API_KEY}
  &ptype=o,k
  &naicsCode={NAICS}
  &postedFrom={DATE_14_DAYS_AGO}
  &postedTo={TODAY}
  &limit=25
  &offset=0
  &typeOfSetAside=SBA,8A,HZC,WOSB,EDWOSB,VSB,SDVOSB
```

Date format: MM/dd/yyyy

If a location was specified, add:
```
  &state={STATE_ABBREVIATION}
```

Parse the response JSON. Each result contains:
- `title` — contract name
- `solicitationNumber` — the ID
- `fullParentPathName` — agency
- `postedDate` — when posted
- `responseDeadLine` — bid due date
- `naicsCode` — industry code
- `placeOfPerformance` — location
- `description` — what they need
- `uiLink` — direct URL to the opportunity on SAM.gov

---

## Step 5 — Score Each Opportunity

Score each contract 1–10:

| Factor | Points |
|---|---|
| Under $25,000 | +3 (fastest to win, simplest) |
| $25K–$100K | +2 |
| $100K–$350K | +1 |
| Bid deadline 7+ days away | +2 |
| Bid deadline 3–6 days away | +1 |
| Bid deadline under 3 days | -2 |
| Set-aside for small business | +2 |
| Service contract (not product) | +2 |
| Product/supply contract | +0 |
| Location: state with known subs (Georgia base) | +1 |
| Fewer than 5 interested parties on SAM | +1 |
| NAICS matches Scott's core industries | +1 |

Flag contracts with score 7+ as **HOT**, 4–6 as **WORTH REVIEWING**, below 4 as **SKIP**.

---

## Step 6 — Output the Opportunity List

Format output:

```
GOVERNMENT CONTRACT OPPORTUNITIES
Search: [INDUSTRY] | Location: [LOCATION] | Under $[AMOUNT] | [DATE RANGE]
Found: XX total | HOT: XX | Worth Reviewing: XX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 HOT — BID THESE FIRST (Score 7-10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [Contract Title]
   Agency: [Agency Name]
   Location: [City, State]
   Value: ~$[Estimated Value] | NAICS: [Code]
   Deadline: [Date] ([X days away])
   Set-Aside: [Small Business / 8(a) / None]
   SAM Link: [URL]
   Why Hot: [1-line reason]

[repeat]

📋 WORTH REVIEWING (Score 4-6)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[condensed — title, agency, deadline, link]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED NEXT STEPS:
1. Run /past-pricing-lookup on the top HOT contracts to see what the government paid before
2. Run /sub-finder on top contracts to find subs in those locations
3. Bid deadline soonest = priority
```

---

## Step 7 — Save Results

Save the output to:
`/home/scott/projects/govt-contracts/prospect-lists/[DATE]-[INDUSTRY]-[LOCATION].md`

Ask: "Want me to also check historical pricing on any of these? Just say the contract number or title."

---

## Fallback — No API Key Yet

If SAM.gov API key not available, guide the user to search manually:

1. Go to sam.gov/opportunities
2. Click "Advanced Search"
3. Filter: NAICS Code → [relevant codes]
4. Filter: Place of Performance → [state]
5. Filter: Set Aside → Small Business
6. Sort by: Response Deadline (soonest first)
7. Copy the contract details and paste them here — I'll score and analyze them

---

## Notes
- SAM.gov API is free with registration at sam.gov/profile/developer
- The free key allows up to 450 requests/day — more than enough for weekly searches
- Small Business set-asides are the best targets — competition is limited to small businesses only
- "8(a)" set-asides are for SBA-certified firms — skip these until 8(a) certification is pursued
- Always check the "Interested Vendors List" on each contract — fewer = less competition

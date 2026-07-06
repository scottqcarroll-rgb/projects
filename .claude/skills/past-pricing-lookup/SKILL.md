# Past Pricing Lookup Skill

## What This Skill Does
Searches USASpending.gov to find what the government previously paid for contracts similar to the one you're about to bid on. This tells you the pricing ceiling — what you can charge without being thrown out — and gives you the edge to bid just below it and win.

---

## Why This Matters
The government paid $1.6 million for a Colorado landscaping contract. Knowing that, you bid $962K and won — and still left $200K on the table. Without this data, you're guessing. With it, you know your ceiling.

---

## Step 1 — Get the Contract Details

Ask the user:

**Option A — I have a SAM.gov contract number:**
> "Paste the solicitation number from SAM.gov and I'll look up what the government paid for this or similar contracts before."

**Option B — I'm searching by type:**
> "What type of work is the contract for? (e.g., 'HVAC maintenance at VA facility in Texas')"
> "What's the approximate contract value range you're expecting?"
> "What state or agency is this for?"

---

## Step 2 — Search USASpending.gov API

### Search by NAICS Code and Location

```
POST https://api.usaspending.gov/api/v2/search/spending_by_award/

Body:
{
  "filters": {
    "award_type_codes": ["A", "B", "C", "D"],
    "naics_codes": ["[NAICS_CODE]"],
    "place_of_performance_locations": [
      {"country": "USA", "state": "[STATE_ABBREV]"}
    ],
    "time_period": [
      {"start_date": "2020-01-01", "end_date": "2026-12-31"}
    ]
  },
  "fields": [
    "Award ID", "Recipient Name", "Award Amount",
    "Total Outlays", "Description", "Action Date",
    "Awarding Agency", "Period of Performance Start Date",
    "Period of Performance Current End Date", "Place of Performance State Code"
  ],
  "sort": "Action Date",
  "order": "desc",
  "limit": 10,
  "page": 1
}
```

No API key required — USASpending.gov is fully public.

### Search by Agency + Description Keywords

```
POST https://api.usaspending.gov/api/v2/search/spending_by_award/

Body:
{
  "filters": {
    "award_type_codes": ["A", "B", "C", "D"],
    "keywords": ["[KEY_WORDS_FROM_CONTRACT_TITLE]"],
    "time_period": [
      {"start_date": "2018-01-01", "end_date": "2026-12-31"}
    ]
  },
  "fields": [
    "Award ID", "Recipient Name", "Award Amount",
    "Description", "Action Date", "Awarding Agency",
    "Period of Performance Start Date",
    "Period of Performance Current End Date"
  ],
  "sort": "Action Date",
  "order": "desc",
  "limit": 10
}
```

---

## Step 3 — Analyze the Results

For each matching past contract found, extract:
- Original award amount
- Any modification amounts (contract changes)
- Length of contract (calculate from start/end dates)
- Who won it (the previous vendor)
- Which agency awarded it
- When it was awarded

Calculate:
- **Annual value** = Total Award ÷ Contract Years
- **Price per unit** (if inferable from description — per person, per pickup, per acre, per month)
- **Inflation adjustment** = multiply by 1.03 per year since award to get today's equivalent

---

## Step 4 — Output the Pricing Intelligence Report

```
PAST PRICING INTELLIGENCE REPORT
Contract Type: [NAICS + Description]
Location: [State/Region]
Search Date: [Today]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HISTORICAL CONTRACTS FOUND: [X]

Most Recent Match:
  Agency: [Agency Name]
  Description: [What it was for]
  Award Date: [Date]
  Total Value: $[Amount] over [X] years
  Annual Value: $[Amount/year]
  Won By: [Company Name]
  Modification History: [Any price changes noted]

Other Matches:
  [List additional contracts with amounts and dates]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRICING ANALYSIS

Historical ceiling (highest paid):     $[Amount]
Historical floor (lowest paid):         $[Amount]
Average paid:                           $[Amount]
Inflation-adjusted today's equivalent: $[Amount]

RECOMMENDED BID RANGE:
  Aggressive (to win):    $[Floor + 5%]
  Balanced (good margin): $[Average − 10%]
  Maximum (ceiling):      $[Highest − 5%]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MARGIN CALCULATOR

Enter your sub's quote and I'll calculate your bid:
  Sub Quote:     $[INPUT]
  Recommended Bid: $[Sub × 1.30] (30% margin)
  Maximum Bid:     $[Historical ceiling − 5%]
  Do NOT bid above: $[Historical ceiling]

VERDICT: [Plain English recommendation — e.g., "This contract historically pays $85K/year. If your sub quotes under $65K, you have strong margin. Bid at $82K to be competitive."]
```

---

## Step 5 — Save the Report

Save to:
`/home/scott/projects/govt-contracts/prospect-lists/pricing-[CONTRACT-ID]-[DATE].md`

Then ask:
> "Want me to find local subcontractors for this contract? Run /sub-finder and I'll pull subs in [location]."

---

## Notes
- USASpending.gov data is public — no login, no API key needed
- Data goes back to 2008 — excellent historical coverage
- Look for contracts that were renewed (same agency, same NAICS, recurring) — these are the most predictable
- If the previous winner charged very low, look for why — maybe they lost money. Don't race to the bottom.
- Modifications that increased contract value = government made a mistake in scope. Note these for your own proposals — always read scope carefully.
- The old FPDS site was decommissioned — USASpending.gov is the current replacement with the same data

# Government Contracts Business — Breezar Investments LLC
**Created:** 2026-05-14
**Entity:** Breezar Investments LLC — registered Georgia
**Model:** Prime contractor → subcontract the work → keep the margin

---

## Business Model
1. Find contracts on SAM.gov under $350K (no past performance required)
2. Look up historical pricing on USASpending.gov — know what the government paid before
3. Find hungry local subs in the contract's city/state
4. Get sub's quote → add margin → submit proposal
5. Win → sub does the work → submit invoice → collect net 30-45
6. Build past performance → scale to $1M+ contracts
7. Eventually: consult for other businesses (take % of their wins)

---

## Target Industries & NAICS Codes

| Industry | NAICS Code | Notes |
|---|---|---|
| HVAC — Installation & Repair | 238220 | Plumbing, Heating, Air Conditioning |
| Facility Maintenance | 561210 | Facilities Support Services |
| Building Maintenance | 811310 | Commercial/Industrial Equipment Repair |
| IT Services / Support | 541519 | Other Computer Related Services |
| IT Hardware/Equipment | 334111 | Computer Hardware |
| Construction — General | 236220 | Commercial/Industrial Building |
| Landscaping | 561730 | Landscaping Services |
| Janitorial / Cleaning | 561720 | Janitorial Services |
| Hazardous Waste | 562112 | Hazardous Waste Collection |
| Equipment Repair | 811310 | Commercial Equipment Repair |

---

## Setup Checklist
- [x] LLC formed — Breezar Investments LLC (Georgia)
- [ ] SAM.gov registration — **NEXT STEP**
- [ ] Get SAM.gov API key (free at sam.gov/profile/developer)
- [ ] First contract found and bid
- [ ] First contract won

---

## SAM.gov Setup Instructions
1. Go to sam.gov → Create Account
2. Register your entity (Breezar Investments LLC)
   - Have your EIN ready
   - Have your NAICS codes ready (use the list above)
   - Bank account for EFT payment setup
3. Registration takes 24-48 hours to activate
4. After active: go to sam.gov/profile/developer → get free API key
5. Give API key to Claude → skills will use it automatically

---

## The Pricing Formula
```
Sub's Quote × 1.25 to 1.40 = Your Bid Price

OR: Check USASpending.gov for previous contract price
    Come in 10-15% below that number
    That number becomes your ceiling — never go above it
```

---

## The Weekly Workflow (2-3 hrs/week while building)
- **Monday:** Run /gov-contract-scraper — find this week's opportunities
- **Tuesday:** Run /past-pricing-lookup on promising contracts — know the ceiling
- **Wednesday:** Run /sub-finder — call the top 3 subs per contract
- **Thursday:** Gather sub quotes, build proposals
- **Friday:** Submit proposals, follow up on open bids

---

## Subcontractor Vetting Checklist
Before committing to a sub, verify:
- [ ] Google reviews (4+ stars minimum)
- [ ] Has a real website
- [ ] Responds within 24 hours
- [ ] Licensed in the state of the contract
- [ ] Has done similar work before
- [ ] Will give a written quote before deadline
- [ ] Willing to accept net 30-45 payment terms

---

## Consulting Angle (Phase 2)
Once past performance is established:
- Help established businesses (HVAC companies, IT firms, contractors) win government contracts
- They do the work — you manage the contract process
- Take 10-15% of contract value as consulting fee
- Build a Claude skill stack and sell it for $99 on Stripe

---

## Key Websites
- **SAM.gov** — sam.gov/opportunities (find contracts)
- **USASpending.gov** — usaspending.gov (past pricing)
- **APEX Accelerators** — apexaccelerators.us (free local advisors)
- **SAM API Docs** — open.gsa.gov/api/sam/

---

## Won Contracts Log
| Contract | Agency | Value | Sub | Margin | Status |
|---|---|---|---|---|---|
| (none yet) | | | | | |

---

## Notes from Transcript
- Generic name "Breezar Investments" = can bid on ANY industry ✓
- Under $350K = RFQ (Request for Quote) — no past performance needed
- Over $350K = RFP (Request for Proposal) — need past performance or teaming partner
- Government modifications: if scope creep, push back and get paid more
- 8-9% of contracts get ZERO bids — focus on less popular ones
- Subcontracting is expected and disclosed — never hidden
- Progress payments: ask for milestone-based payment (not all at end)

# LinkedIn Prospector Skill

## What This Skill Does
Scrapes LinkedIn to build a targeted prospect list of business owners by industry, location, and company size. Uses Apify as the scraping engine. Analyzes results and outputs a prioritized hit list ready for outreach.

---

## Step 1 — Check for Apify API Key

Look for the Apify API key in these locations in order:
1. Environment variable: `APIFY_API_KEY`
2. File: `~/.apify/token`
3. File: `/home/scott/projects/.env.apify`

If no key is found, ask the user:
> "I need your Apify API key to run the scraper. You can get a free one at apify.com — sign up, go to Settings → Integrations → API Key, and paste it here. Want me to save it for future use?"

If they provide the key, save it to `/home/scott/projects/.env.apify` with the line:
```
APIFY_API_KEY=their_key_here
```

Then confirm: "Got it — saved for next time."

---

## Step 2 — Ask What to Scrape

Ask the user these questions one at a time (wait for each answer before asking the next):

**Question 1:**
> "What type of business owner do you want to target? Examples: HVAC company owners, alcohol distributors, restaurant owners, dental practice owners, manufacturing plant managers — just tell me the category."

**Question 2:**
> "What location? You can say a city, state, metro area, or 'anywhere in the US'."

**Question 3:**
> "Any company size preference? For example: solo operators, 5–50 employees, 50–200 employees, or no preference?"

**Question 4:**
> "How many leads do you want? (Apify free tier handles up to ~100 per run — recommend starting with 25–50)"

Confirm back to the user before running:
> "Got it — I'm going to search for [CATEGORY] in [LOCATION], company size [SIZE], pulling [NUMBER] leads. Running now..."

---

## Step 3 — Build the Apify Search

Use the Apify actor: `curious_coder/linkedin-people-search-scraper`

Build the search query from the user's answers:
- Job titles to search: derive from category (e.g., "HVAC owner" → search titles: "Owner", "President", "Founder", "CEO" at HVAC companies)
- Location: convert to LinkedIn location format (e.g., "Charlotte NC" → "Charlotte, North Carolina, United States")
- Combine into a LinkedIn People Search URL format

Construct the actor input JSON:
```json
{
  "searchUrl": "https://www.linkedin.com/search/results/people/?keywords=[JOB_TITLE]%20[INDUSTRY]&origin=GLOBAL_SEARCH_HEADER&geoUrn=[LOCATION_CODE]",
  "maxResults": [NUMBER],
  "proxyConfiguration": {
    "useApifyProxy": true
  }
}
```

---

## Step 4 — Call Apify API

Make a POST request to run the actor:

```
POST https://api.apify.com/v2/acts/curious_coder~linkedin-people-search-scraper/runs?token={APIFY_API_KEY}
Content-Type: application/json

{body from Step 3}
```

After submitting, poll for completion:
```
GET https://api.apify.com/v2/acts/curious_coder~linkedin-people-search-scraper/runs/last?token={APIFY_API_KEY}
```

Check the `status` field every 15 seconds until it shows `SUCCEEDED` or `FAILED`.

When complete, fetch results:
```
GET https://api.apify.com/v2/acts/curious_coder~linkedin-people-search-scraper/runs/last/dataset/items?token={APIFY_API_KEY}
```

---

## Step 5 — Analyze and Score the Results

For each profile returned, score them as a prospect (1–5) based on:

| Signal | Points |
|---|---|
| Title includes "Owner", "Founder", "President" | +2 |
| Title includes "CEO", "Managing Director" | +2 |
| Title includes "Manager" or "Director" | +1 |
| Company size matches target range | +1 |
| Location matches exactly | +1 |
| Has recent LinkedIn activity (posts in last 30 days) | +1 |
| Profile is complete (photo, summary, experience) | +1 |

---

## Step 6 — Output the Prospect Hit List

Format the output as a clean table:

```
LINKEDIN PROSPECT LIST
Target: [CATEGORY] | Location: [LOCATION] | Run Date: [DATE]
Total Found: XX | High Priority: XX | Review Later: XX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 HIGH PRIORITY (Score 4-5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. [Full Name] — [Title] at [Company]
   📍 [Location] | 👥 [Company Size] employees
   🔗 [LinkedIn URL]
   💡 Why: [1-line reason they're a good fit]

[repeat for each high priority lead]

📋 REVIEW LATER (Score 2-3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━
[condensed list — name, title, company, URL only]

❌ SKIP (Score 1)
━━━━━━━━━━━━━━━━
[count only — "X profiles skipped — not decision makers"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED NEXT STEP:
Start with the top 5 High Priority leads. Suggested opening message:

"Hi [Name] — I help [industry] businesses find where AI can save them 5–10 hours a week. I do a free 15-minute AI Quick Scan to identify the biggest opportunities. Would that be worth a conversation?"
```

---

## Step 7 — Save and Offer Export

Ask the user:
> "Want me to save this list as a CSV file? I can put it at `/home/scott/projects/ai-assessment/prospect-lists/[DATE]-[CATEGORY].csv`"

If yes, create the CSV with columns:
`Name, Title, Company, Location, Company Size, LinkedIn URL, Score, Priority, Notes`

Then commit and push to GitHub.

---

## Fallback — If Apify API Fails or Rate Limits

If the API call fails, do not give up. Instead:

1. Tell the user what went wrong in plain English
2. Offer the manual path:
   > "No problem — I can walk you through running this manually in Apify in about 3 minutes. Want me to do that instead?"
3. If yes, provide:
   - The exact Apify actor URL to open
   - The exact settings to paste in
   - What to download when it finishes
   - Tell them to paste or upload the CSV and you'll analyze it

---

## Notes
- LinkedIn actively limits scraping — Apify routes through residential proxies to avoid blocks, which uses proxy credits. Free Apify plan includes $5/mo credits which covers ~50–100 LinkedIn profiles per run.
- If the `curious_coder/linkedin-people-search-scraper` actor is unavailable, try `apify/linkedin-profile-scraper` as a fallback.
- Always tell the user how many Apify credits were used after each run so they can track their free tier usage.
- The prospect list and CSV should always be saved to `/home/scott/projects/ai-assessment/prospect-lists/` — this connects directly to the AI Assessment Agency pipeline.

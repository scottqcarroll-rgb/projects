# Scott's Profile Skill

Recall who Scott is — name, email, home address, work address, timezone — without asking him each session. Use this whenever the user asks "who am I", "where do I live/work", or needs a local weather/commute lookup.

## Where To Get This Data (Source of Truth)

The canonical, always-current values live in the dashboard data fetcher:

- **`/home/scott/projects/dashboard/data_fetcher.py`**
  - `get_drive_report()` — hardcodes HOME (origin) and WORK (destination) addresses
  - `get_pm_drive_report()` — reverse route (work → home)
  - `get_weather()` — hardcoded lat/lon for Temple, GA + timezone
  - `get_gmail_summary()` — hardcodes the email address

> Always re-read `data_fetcher.py` before quoting these values; if a value below
> disagrees with the file, the file wins. Update this file to match afterward.

## Known Values (verify against source above)

| Field | Value | Source in data_fetcher.py |
|---|---|---|
| **Name** | Scott Carroll (user `scott`, git handle `scottqcarroll`) | — |
| **Email** | scottqcarroll@gmail.com | `get_gmail_summary()` |
| **Home** | 616 Huntwood Cir, Temple GA 30179 | `get_drive_report()` ORIGIN |
| **Work** | 5303 New Peachtree Rd, Chamblee GA 30341 | `get_drive_report()` DESTINATION |
| **Weather location** | Temple, GA (lat 33.7353, lon -85.0308) | `get_weather()` |
| **Timezone** | America/New_York (Eastern) | `get_weather()` tz param |

## Commute Routes

- **AM (home → work):** 616 Huntwood Cir, Temple GA → 5303 New Peachtree Rd, Chamblee GA
- **PM (work → home):** reverse of the above

## When To Use

- "Who am I?" / "Where do I live or work?" → answer from the table.
- "Weather for me" / "Should I bring an umbrella?" → pull a forecast for Temple, GA
  via Open-Meteo (`https://api.open-meteo.com/v1/forecast?latitude=33.7353&longitude=-85.0308...`).
- Any commute/drive-time question → use the two routes above.

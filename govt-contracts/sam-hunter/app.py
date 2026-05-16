import os, json, datetime, re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import requests

app = Flask(__name__)

BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
PROSPECT_DIR  = BASE_DIR.parent / "prospect-lists"

ENV_FILE      = Path("/home/scott/projects/.env.samgov")
PROFILE_FILE  = DATA_DIR / "profile.json"
BIDS_FILE     = DATA_DIR / "bids.json"
USAGE_FILE    = DATA_DIR / "api_usage.json"   # tracks daily API call count

UEI = "QMGQE3CJK923"

NAICS_LABELS = {
    "561210": "Facilities Support",
    "561720": "Janitorial Services",
    "561730": "Landscaping",
    "561740": "Carpet & Upholstery Cleaning",
    "238910": "Site Preparation",
    "561612": "Security Guards",
    "561710": "Exterminating & Pest Control",
    "562111": "Solid Waste Collection",
    "562112": "Hazardous Waste Collection",
    "562211": "Hazardous Waste Treatment",
    "562998": "Other Waste Management",
    "812331": "Linen Supply",
    "812332": "Industrial Launderers",
}

SETASIDE_LABELS = {
    "SBA":   "Small Business",
    "8AN":   "8(a) Set-Aside",
    "SDVOSB":"SDVOSB",
    "HZC":   "HUBZone",
    "WOSB":  "WOSB",
    "EDWOSB":"EDWOSB",
    "VSB":   "Veteran-Owned",
    "":      "None",
}


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_api_key():
    return load_env().get("SAM_API_KEY", "")


def load_profile():
    if PROFILE_FILE.exists():
        return json.loads(PROFILE_FILE.read_text())
    return {
        "uei": UEI,
        "legal_name": "Brisar Investment, LLC",
        "cage_code": "",
        "address": "616 Huntwood Cir, Temple, GA 30179",
        "status": "Active",
        "last_synced": None,
        "naics_primary": "561720",
        "small_business": True,
    }


def load_bids():
    if BIDS_FILE.exists():
        return json.loads(BIDS_FILE.read_text())
    return {"TRACKING": [], "PREPARING": [], "SUBMITTED": [], "AWARDED": [], "LOST": []}


def save_bids(bids):
    BIDS_FILE.write_text(json.dumps(bids, indent=2))


def score_contract(c):
    SERVICE_KEYWORDS = [
        "maintenance", "cleaning", "janitorial", "grounds", "mowing", "landscaping",
        "pest", "extermination", "waste", "refuse", "linen", "laundry", "security",
        "guard", "custodial", "sanitation", "facilities", "housekeeping",
    ]
    pts = 0
    title = (c.get("title") or "").lower()
    setaside = (c.get("typeOfSetAsideDescription") or "").lower()
    city  = c.get("placeOfPerformance", {}).get("city", {}).get("name", "")
    state = c.get("placeOfPerformance", {}).get("state", {}).get("code", "")

    if any(k in title for k in SERVICE_KEYWORDS):
        pts += 3
    if "small business" in setaside:
        pts += 2
    if city or state:
        pts += 1

    # Value scoring
    val = 0
    award = c.get("award") or {}
    val_str = str(award.get("amount") or c.get("baseAndAllOptionsValue") or 0)
    try:
        val = float(re.sub(r"[^0-9.]", "", val_str))
    except Exception:
        val = 0
    if val and val < 25000:
        pts += 2
    elif val and val <= 100000:
        pts += 1

    # Deadline scoring
    days_away = 999
    deadline_str = c.get("responseDeadLine") or c.get("archiveDate") or ""
    if deadline_str:
        try:
            deadline = datetime.datetime.fromisoformat(deadline_str[:19])
            days_away = (deadline - datetime.datetime.now()).days
        except Exception:
            pass
    if days_away >= 21:
        pts += 3
    elif days_away >= 14:
        pts += 1
    elif days_away >= 7:
        pts -= 2
    else:
        pts -= 5

    return max(1, min(10, pts)), days_away


def enrich(opportunities):
    enriched = []
    for c in opportunities:
        score, days_away = score_contract(c)
        notice_id = c.get("noticeId") or c.get("id") or ""
        naics = c.get("naicsCode") or ""
        val = 0
        award = c.get("award") or {}
        val_str = str(award.get("amount") or c.get("baseAndAllOptionsValue") or 0)
        try:
            val = float(re.sub(r"[^0-9.]", "", val_str))
        except Exception:
            pass
        pop = c.get("placeOfPerformance") or {}
        city  = pop.get("city", {}).get("name", "") if isinstance(pop.get("city"), dict) else ""
        state_code = pop.get("state", {}).get("code", "") if isinstance(pop.get("state"), dict) else ""

        # Contracting officer
        pocs = c.get("pointOfContact") or []
        co = {}
        for p in pocs:
            if p.get("type") in ("primary", ""):
                co = p
                break
        if not co and pocs:
            co = pocs[0]

        enriched.append({
            "id": notice_id,
            "title": c.get("title") or "Untitled",
            "agency": c.get("departmentName") or c.get("organizationHierarchy", [{}])[0].get("name", "") if c.get("organizationHierarchy") else c.get("departmentName") or "",
            "subtier": c.get("subtierName") or "",
            "naics": naics,
            "naics_label": NAICS_LABELS.get(naics, naics),
            "setaside": c.get("typeOfSetAside") or "",
            "setaside_label": SETASIDE_LABELS.get(c.get("typeOfSetAside") or "", c.get("typeOfSetAsideDescription") or ""),
            "value": val,
            "value_fmt": f"${val:,.0f}" if val else "TBD",
            "deadline": c.get("responseDeadLine") or c.get("archiveDate") or "",
            "days_away": days_away,
            "city": city,
            "state": state_code,
            "location": f"{city}, {state_code}".strip(", ") if (city or state_code) else "N/A",
            "score": score,
            "co_name":  co.get("fullName") or "",
            "co_email": co.get("email") or "",
            "co_phone": co.get("phone") or "",
            "type":     c.get("type") or c.get("baseType") or "",
            "description": c.get("description") or "",
            "sam_url": f"https://sam.gov/opp/{notice_id}/view" if notice_id else "",
            "posted": c.get("postedDate") or "",
            "solicitation_number": c.get("solicitationNumber") or "",
            "urgent": days_away < 14,
        })
    return enriched


# ── Routes ────────────────────────────────────────────────

@app.route("/")
def index():
    profile = load_profile()
    bids = load_bids()
    bid_count = sum(len(v) for v in bids.values())
    return render_template("index.html",
        profile=profile,
        naics_labels=NAICS_LABELS,
        setaside_labels=SETASIDE_LABELS,
        bid_count=bid_count,
    )


@app.route("/bid-tracker")
def bid_tracker():
    profile = load_profile()
    bids = load_bids()
    now = datetime.datetime.now().isoformat()
    bid_count = sum(len(v) for v in bids.values())
    return render_template("bid_tracker.html", profile=profile, bids=bids, now=now, bid_count=bid_count)


@app.route("/proposal-wizard")
def proposal_wizard():
    profile  = load_profile()
    bids     = load_bids()
    bid_count = sum(len(v) for v in bids.values())
    return render_template("proposal_wizard.html", profile=profile, bid_count=bid_count)


def get_daily_raw_file(date_str=None):
    """Return path to today's 1000-record raw JSON saved by the daily report cron."""
    d = date_str or datetime.date.today().isoformat()
    return PROSPECT_DIR / f"{d}-raw.json"


def load_daily_raw(date_str=None):
    """Load opportunitiesData from the daily raw JSON. Checks multiple filename patterns."""
    d = date_str or datetime.date.today().isoformat()
    # Check candidate filenames in order of preference (newest/biggest first)
    candidates = [
        PROSPECT_DIR / f"{d}-raw.json",        # written by daily cron going forward
        PROSPECT_DIR / f"{d}-naics-raw.json",   # legacy name from early test runs
    ]
    for path in candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text())
                records = data.get("opportunitiesData") or []
                total   = data.get("totalRecords", len(records))
                pulled  = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %I:%M %p")
                return records, {"total": total, "pulled": pulled, "file": str(path.name)}
            except Exception:
                pass
    return None, {}


def load_usage():
    today = datetime.date.today().isoformat()
    if USAGE_FILE.exists():
        try:
            u = json.loads(USAGE_FILE.read_text())
            if u.get("date") == today:
                return u
        except Exception:
            pass
    return {"date": today, "calls": 0, "limit": 1000, "last_call": None}


def save_usage(u):
    USAGE_FILE.write_text(json.dumps(u))


INELIGIBLE_SETASIDES = {"VSB", "SDVOSB"}  # Brisar is not veteran-owned


def filter_records(records, keyword, naics, setaside, val_max, state):
    """Filter raw SAM.gov records client-side — no extra API calls."""
    tracked = set(NAICS_LABELS.keys())
    out = []
    val_ceiling = float(val_max) if val_max else 350000.0

    for c in records:
        code = c.get("naicsCode") or ""

        # Always restrict to Brisar's tracked codes unless a specific code is chosen
        if naics:
            if code != naics:
                continue
        else:
            if code not in tracked:
                continue

        # Always exclude set-asides Brisar doesn't qualify for
        if c.get("typeOfSetAside") in INELIGIBLE_SETASIDES:
            continue

        # Set-aside filter
        if setaside and c.get("typeOfSetAside") != setaside:
            continue

        # Value ceiling
        try:
            award = c.get("award") or {}
            v = float(re.sub(r"[^0-9.]", "", str(award.get("amount") or c.get("baseAndAllOptionsValue") or 0)))
            if v and v > val_ceiling:
                continue
        except Exception:
            pass

        # State filter
        if state:
            pop = c.get("placeOfPerformance") or {}
            s = pop.get("state", {}).get("code", "") if isinstance(pop.get("state"), dict) else ""
            if s.upper() != state.upper():
                continue

        # Keyword filter (title search)
        if keyword:
            title = (c.get("title") or "").lower()
            if keyword.lower() not in title:
                continue

        out.append(c)
    return out


@app.route("/api/status")
def api_status():
    """Returns data source info + API usage counter. Called on page load."""
    today = datetime.date.today().isoformat()
    records, meta = load_daily_raw()
    usage = load_usage()
    has_daily = records is not None

    return jsonify({
        "has_daily_file": has_daily,
        "daily_record_count": len(records) if records else 0,
        "daily_pulled": meta.get("pulled"),
        "daily_file": meta.get("file"),
        "api_calls_today": usage["calls"],
        "api_limit": usage["limit"],
        "date": today,
    })


@app.route("/api/search")
def api_search():
    keyword  = request.args.get("keyword", "").strip()
    naics    = request.args.get("naics", "").strip()
    setaside = request.args.get("setaside", "").strip()
    val_max  = request.args.get("val_max", "350000")
    state    = request.args.get("state", "").strip()
    force    = request.args.get("force", "0") == "1"   # explicit SAM.gov refresh

    # ── Step 1: Try today's daily raw file (written by 8 AM cron) ──
    if not force:
        records, meta = load_daily_raw()
        if records is not None:
            filtered = filter_records(records, keyword, naics, setaside, val_max, state)
            results  = sorted(enrich(filtered), key=lambda x: -x["score"])
            return jsonify({
                "results":     results,
                "source":      "daily",
                "count":       len(results),
                "total":       meta.get("total", len(records)),
                "pulled":      meta.get("pulled"),
                "record_pool": len(records),
            })
        # No daily file and not a forced refresh — tell frontend to prompt user
        return jsonify({"error": "no_data", "message": "No data file for today yet."}), 404

    # ── Step 2: Force refresh — call SAM.gov API ──────────────────
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "No SAM.gov API key found"}), 500

    usage = load_usage()
    if usage["calls"] >= usage["limit"]:
        return jsonify({
            "error": "daily_limit",
            "message": f"Daily SAM.gov limit reached ({usage['limit']} calls). Resets at midnight UTC."
        }), 429

    today      = datetime.date.today().isoformat()
    posted_from = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%m/%d/%Y")
    posted_to   = datetime.date.today().strftime("%m/%d/%Y")

    url = (
        f"https://api.sam.gov/opportunities/v2/search"
        f"?api_key={api_key}"
        f"&ptype=o,k"
        f"&awardCeiling=350000"
        f"&postedFrom={posted_from}"
        f"&postedTo={posted_to}"
        f"&limit=1000"
        f"&offset=0"
    )

    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 429:
            return jsonify({
                "error": "rate_limited",
                "message": "SAM.gov rate limit hit. Wait 60 seconds and try again."
            }), 429
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        if "429" in str(e):
            return jsonify({"error": "rate_limited", "message": "SAM.gov rate limit. Wait 60 seconds."}), 429
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Save as today's daily file so all future searches read from it
    raw_path = get_daily_raw_file()
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(data))

    # Update usage counter
    usage["calls"] += 1
    usage["last_call"] = datetime.datetime.now().isoformat()
    save_usage(usage)

    records = data.get("opportunitiesData") or []
    filtered = filter_records(records, keyword, naics, setaside, val_max, state)
    results  = sorted(enrich(filtered), key=lambda x: -x["score"])
    pulled   = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")

    return jsonify({
        "results":     results,
        "source":      "api",
        "count":       len(results),
        "total":       data.get("totalRecords", 0),
        "pulled":      pulled,
        "record_pool": len(records),
        "calls_used":  usage["calls"],
    })


@app.route("/api/profile")
def api_profile():
    return jsonify(load_profile())


@app.route("/api/profile/sync", methods=["POST"])
def api_profile_sync():
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "No API key"}), 500
    try:
        resp = requests.get(
            f"https://api.sam.gov/entity-information/v3/entities",
            params={"api_key": api_key, "ueiSAM": UEI, "includeSections": "all"},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        entities = data.get("entityData") or []
        if not entities:
            return jsonify({"error": "Entity not found"}), 404
        e = entities[0]
        reg = e.get("coreData", {}).get("entityRegistration", {})
        naics_list = e.get("assertions", {}).get("goodsAndServices", {}).get("naicsList") or []
        primary_naics = next((n["naicsCode"] for n in naics_list if n.get("isPrimary")), "561720")
        addr = reg.get("physicalAddress", {})
        profile = {
            "uei": UEI,
            "legal_name": reg.get("legalBusinessName", "Brisar Investment, LLC"),
            "cage_code": reg.get("cageCode", ""),
            "address": f"{addr.get('addressLine1','')}, {addr.get('city','')}, {addr.get('stateOrProvinceCode','')}, {addr.get('zipCode','')}".strip(", "),
            "status": reg.get("registrationStatus", "Active"),
            "last_synced": datetime.datetime.now().isoformat(),
            "naics_primary": primary_naics,
            "small_business": True,
            "expiration": reg.get("registrationExpirationDate", ""),
        }
        PROFILE_FILE.write_text(json.dumps(profile, indent=2))
        return jsonify({"ok": True, "profile": profile})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.route("/api/bids", methods=["GET"])
def api_bids_get():
    return jsonify(load_bids())


@app.route("/api/bids", methods=["POST"])
def api_bids_post():
    bids = load_bids()
    body = request.get_json()
    stage = body.get("stage", "TRACKING")
    if stage not in bids:
        return jsonify({"error": "Invalid stage"}), 400
    card = {
        "id": body.get("id") or f"bid_{datetime.datetime.now().timestamp():.0f}",
        "title": body.get("title", ""),
        "agency": body.get("agency", ""),
        "value": body.get("value", ""),
        "deadline": body.get("deadline", ""),
        "naics": body.get("naics", ""),
        "location": body.get("location", ""),
        "score": body.get("score", 0),
        "notes": body.get("notes", ""),
        "sub_quote": body.get("sub_quote", ""),
        "sam_url": body.get("sam_url", ""),
        "added": datetime.datetime.now().isoformat(),
    }
    bids[stage].append(card)
    save_bids(bids)
    return jsonify({"ok": True, "card": card})


@app.route("/api/bids/move", methods=["POST"])
def api_bids_move():
    bids = load_bids()
    body = request.get_json()
    bid_id  = body.get("id")
    to_stage = body.get("to")
    if to_stage not in bids:
        return jsonify({"error": "Invalid stage"}), 400
    card = None
    for stage, cards in bids.items():
        for i, c in enumerate(cards):
            if c["id"] == bid_id:
                card = cards.pop(i)
                break
        if card:
            break
    if not card:
        return jsonify({"error": "Card not found"}), 404
    bids[to_stage].append(card)
    save_bids(bids)
    return jsonify({"ok": True})


@app.route("/api/bids/<bid_id>", methods=["PATCH"])
def api_bids_patch(bid_id):
    bids = load_bids()
    body = request.get_json()
    for stage, cards in bids.items():
        for c in cards:
            if c["id"] == bid_id:
                c.update({k: v for k, v in body.items() if k != "id"})
                save_bids(bids)
                return jsonify({"ok": True, "card": c})
    return jsonify({"error": "Not found"}), 404


@app.route("/api/bids/<bid_id>", methods=["DELETE"])
def api_bids_delete(bid_id):
    bids = load_bids()
    for stage, cards in bids.items():
        for i, c in enumerate(cards):
            if c["id"] == bid_id:
                cards.pop(i)
                save_bids(bids)
                return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


def parse_entity(e):
    """Extract useful display fields from a SAM.gov entity record."""
    reg  = e.get("coreData", {}).get("entityRegistration", {})
    addr = e.get("coreData", {}).get("physicalAddress", {})
    biz  = e.get("coreData", {}).get("businessTypes", {})
    pocs = e.get("pointsOfContact", {})
    poc  = pocs.get("governmentBusinessPOC") or pocs.get("electronicBusinessPOC") or {}
    sba_types = biz.get("sbaBusinessTypeList") or []
    certs = [b["sbaBusinessTypeDesc"] for b in sba_types if b.get("certificationEntryDate") and b.get("sbaBusinessTypeDesc")]
    return {
        "uei":           reg.get("ueiSAM", ""),
        "cage":          reg.get("cageCode", ""),
        "name":          reg.get("legalBusinessName", ""),
        "status":        reg.get("registrationStatus", ""),
        "expires":       (reg.get("registrationExpirationDate") or "")[:10],
        "website":       reg.get("entityURL", ""),
        "address":       ", ".join(filter(None, [
                             addr.get("addressLine1",""),
                             addr.get("city",""),
                             addr.get("stateOrProvinceCode",""),
                             addr.get("zipCode",""),
                         ])),
        "contact_name":  f"{poc.get('firstName','')} {poc.get('lastName','')}".strip(),
        "contact_title": poc.get("title", ""),
        "contact_phone": poc.get("phoneNumber", ""),
        "contact_email": poc.get("emailAddress", ""),
        "certifications": certs,
    }


@app.route("/api/entity/lookup")
def api_entity_lookup():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "No SAM.gov API key"}), 500
    try:
        resp = requests.get(
            "https://api.sam.gov/entity-information/v3/entities",
            params={
                "api_key": api_key,
                "legalBusinessName": name,
                "includeSections": "entityRegistration,coreData,pointsOfContact",
                "registrationStatus": "A",
            },
            timeout=30
        )
        resp.raise_for_status()
        entities = resp.json().get("entityData") or []
        if not entities:
            return jsonify({"found": False})
        return jsonify({"found": True, "entity": parse_entity(entities[0])})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.route("/api/entity/subs")
def api_entity_subs():
    naics = request.args.get("naics", "").strip()
    state = request.args.get("state", "").strip()
    if not naics:
        return jsonify({"error": "naics required"}), 400
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "No SAM.gov API key"}), 500
    try:
        params = {
            "api_key": api_key,
            "naicsCode": naics,
            "includeSections": "entityRegistration,coreData,pointsOfContact",
            "registrationStatus": "A",
            "purposeOfRegistrationCode": "Z2",
            "limit": 25,
        }
        if state:
            params["stateOrProvinceCode"] = state
        resp = requests.get(
            "https://api.sam.gov/entity-information/v3/entities",
            params=params,
            timeout=30
        )
        resp.raise_for_status()
        entities = resp.json().get("entityData") or []
        return jsonify({
            "naics": naics,
            "state": state,
            "count": len(entities),
            "entities": [parse_entity(e) for e in entities],
        })
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


def _usaspending_awards(naics, state="", limit=100):
    """Shared helper — fetch recent contract awards from USASpending.gov for a NAICS code.
    Max 100 per page (USASpending hard limit)."""
    body = {
        "subawards": False,
        "fields": [
            "Award ID", "Recipient Name", "Award Amount",
            "Awarding Agency", "Awarding Sub Agency",
            "Period of Performance Start Date", "Place of Performance State Code",
            "NAICS Code",
        ],
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"],   # procurement contracts only
            "naics_codes": [naics],
            "award_amounts": [{"lower_bound": 1, "upper_bound": 350000}],
        },
        "limit": min(limit, 100),   # USASpending max is 100 per page
        "page": 1,
        "sort": "Award Amount",
        "order": "desc",
    }
    if state:
        body["filters"]["place_of_performance_scope"] = "domestic"
        body["filters"]["place_of_performance_states"] = [state]

    resp = requests.post(
        "https://api.usaspending.gov/api/v2/search/spending_by_award/",
        json=body, timeout=30
    )
    resp.raise_for_status()
    return resp.json().get("results") or []


@app.route("/api/usaspending/pricing")
def api_pricing():
    naics = request.args.get("naics", "")
    state = request.args.get("state", "")
    if not naics:
        return jsonify({"error": "naics required"}), 400
    try:
        results = _usaspending_awards(naics, state, limit=100)
        amounts = []
        for r in results:
            try:
                v = float(r.get("Award Amount") or 0)
                if v > 0:
                    amounts.append(v)
            except Exception:
                pass
        if amounts:
            return jsonify({
                "naics": naics,
                "avg":   sum(amounts) / len(amounts),
                "high":  max(amounts),
                "low":   min(amounts),
                "count": len(amounts),
            })
        return jsonify({"naics": naics, "avg": 0, "high": 0, "low": 0, "count": 0})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.route("/api/usaspending/competitors")
def api_competitors():
    """Return top previous winners for a NAICS code — the Competitor X-Ray."""
    naics = request.args.get("naics", "")
    state = request.args.get("state", "")
    if not naics:
        return jsonify({"error": "naics required"}), 400
    try:
        results = _usaspending_awards(naics, state, limit=200)

        # Group by recipient
        winners = {}
        for r in results:
            name   = (r.get("Recipient Name") or "Unknown").title()
            amount = float(r.get("Award Amount") or 0)
            agency = r.get("Awarding Sub Agency") or r.get("Awarding Agency") or "Unknown"
            date   = (r.get("Period of Performance Start Date") or "")[:10]
            st     = r.get("Place of Performance State Code") or ""

            if name not in winners:
                winners[name] = {
                    "name":        name,
                    "win_count":   0,
                    "total_value": 0,
                    "agencies":    set(),
                    "states":      set(),
                    "latest":      "",
                }
            w = winners[name]
            w["win_count"]   += 1
            w["total_value"] += amount
            w["agencies"].add(agency)
            if st:
                w["states"].add(st)
            if date > w["latest"]:
                w["latest"] = date

        # Serialize and sort by win count
        ranked = sorted(
            [
                {
                    "name":        v["name"],
                    "win_count":   v["win_count"],
                    "total_value": v["total_value"],
                    "avg_value":   v["total_value"] / v["win_count"] if v["win_count"] else 0,
                    "agencies":    sorted(v["agencies"])[:3],   # top 3 agencies
                    "states":      sorted(v["states"]),
                    "latest":      v["latest"],
                }
                for v in winners.values()
            ],
            key=lambda x: (-x["win_count"], -x["total_value"])
        )
        return jsonify({"naics": naics, "competitors": ranked[:20], "total_awards": len(results)})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)

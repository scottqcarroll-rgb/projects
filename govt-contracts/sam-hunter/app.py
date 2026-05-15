import os, json, datetime, re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import requests

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ENV_FILE = Path("/home/scott/projects/.env.samgov")
PROFILE_FILE = DATA_DIR / "profile.json"
BIDS_FILE    = DATA_DIR / "bids.json"
CACHE_FILE   = DATA_DIR / "search_cache.json"

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


@app.route("/api/search")
def api_search():
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "No SAM.gov API key found"}), 500

    keyword   = request.args.get("keyword", "").strip()
    naics     = request.args.get("naics", "").strip()
    setaside  = request.args.get("setaside", "").strip()
    val_max   = request.args.get("val_max", "350000")
    deadline  = request.args.get("deadline", "30")
    state     = request.args.get("state", "").strip()
    limit     = int(request.args.get("limit", 200))
    use_cache = request.args.get("cache", "1") == "1"

    # Use today's cache if available and no filters changed
    cache_key = f"{keyword}|{naics}|{setaside}|{val_max}|{deadline}|{state}"
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text())
        except Exception:
            cache = {}

    today = datetime.date.today().isoformat()
    cached = cache.get(today, {}).get(cache_key)
    if use_cache and cached:
        return jsonify({"results": cached, "source": "cache", "count": len(cached)})

    # Build API call
    days = int(deadline) if deadline.isdigit() else 30
    posted_from = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%m/%d/%Y")

    params = {
        "api_key": api_key,
        "ptype":   "o,p,k,r,s,g,i",
        "postedFrom": posted_from,
        "limit":   min(limit, 1000),
        "offset":  0,
    }
    if keyword:
        params["keyword"] = keyword
    if naics:
        params["naicsCode"] = naics
    if state:
        params["state"] = state

    try:
        resp = requests.get(
            "https://api.sam.gov/opportunities/v2/search",
            params=params, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    raw = data.get("opportunitiesData") or []

    # Client-side filtering
    def passes(c):
        # NAICS filter
        if naics and c.get("naicsCode") != naics:
            return False
        # Set-aside
        if setaside and c.get("typeOfSetAside") != setaside:
            return False
        # Value ceiling
        try:
            award = c.get("award") or {}
            v = float(re.sub(r"[^0-9.]", "", str(award.get("amount") or c.get("baseAndAllOptionsValue") or 0)))
            if v and v > float(val_max):
                return False
        except Exception:
            pass
        return True

    filtered = [c for c in raw if passes(c)]

    # If no naics filter was specified, apply Brisar's tracked codes
    if not naics:
        tracked = set(NAICS_LABELS.keys())
        brisar_matches = [c for c in filtered if c.get("naicsCode") in tracked]
        if brisar_matches:
            filtered = brisar_matches

    results = sorted(enrich(filtered), key=lambda x: -x["score"])

    # Save to cache
    if today not in cache:
        cache[today] = {}
    cache[today][cache_key] = results
    # Keep only last 3 days
    keys = sorted(cache.keys())
    if len(keys) > 3:
        for old in keys[:-3]:
            del cache[old]
    CACHE_FILE.write_text(json.dumps(cache))

    return jsonify({"results": results, "source": "api", "count": len(results), "total": data.get("totalRecords", 0)})


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


@app.route("/api/usaspending/pricing")
def api_pricing():
    naics = request.args.get("naics", "")
    state = request.args.get("state", "")
    if not naics:
        return jsonify({"error": "naics required"}), 400
    try:
        body = {
            "filters": {
                "naics_codes": [naics],
                "award_amounts": [{"lower_bound": 0, "upper_bound": 350000}],
            },
            "fields": ["Award Amount", "recipient_name", "awarding_agency_name", "place_of_performance_state_code"],
            "limit": 100,
            "page": 1,
            "sort": "Award Amount",
            "order": "desc",
        }
        if state:
            body["filters"]["place_of_performance_scope"] = "domestic"
            body["filters"]["place_of_performance_states"] = [state]
        resp = requests.post(
            "https://api.usaspending.gov/api/v2/search/spending_by_award/",
            json=body, timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
        awards = [r["data"] for r in (data.get("results") or [])]
        if awards:
            amounts = [float(a[0]) for a in awards if a and a[0]]
            avg = sum(amounts) / len(amounts) if amounts else 0
            high = max(amounts) if amounts else 0
            low  = min(amounts) if amounts else 0
            return jsonify({"naics": naics, "avg": avg, "high": high, "low": low, "count": len(amounts)})
        return jsonify({"naics": naics, "avg": 0, "high": 0, "low": 0, "count": 0})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)

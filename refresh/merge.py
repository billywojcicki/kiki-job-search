"""Merge one day's sweep results into the site's data files."""
import json, glob, sys, datetime, os

# usage: python3 refresh/merge.py TODAY SWEEP_DIR "id-to-drop,id-to-drop" "extra note for the update log" [append]
TODAY = sys.argv[1]
SWEEP = sys.argv[2]
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DROP = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else set()
NOTE = sys.argv[4] if len(sys.argv) > 4 else ""
APPEND = len(sys.argv) > 5 and sys.argv[5] == "append"

jobs = {j["id"]: j for j in json.load(open(f"{SITE}/jobs.json"))}
facs = json.load(open(f"{SITE}/facilities.json"))
fac_by = {f["key"]: f for f in facs}
updates = json.load(open(f"{SITE}/updates.json"))
meta = json.load(open(f"{SITE}/meta.json"))

seen, closed_ev, failed = {}, {}, []
new_facs, fac_units = {}, {}
for f in sorted(glob.glob(f"{SWEEP}/[A-Z].json")):
    d = json.load(open(f))
    for j in d.get("jobs", []):
        if j["id"] in DROP:
            continue
        prev = seen.get(j["id"])
        if prev is None:
            seen[j["id"]] = j
        else:
            # two sweeps reported the same job: keep the better-evidenced copy
            def score(r):
                q = 0 if not r.get("posted") else (1 if r.get("postedBefore") else (2 if r.get("postedApprox") else 3))
                return (bool(r.get("verified", True)), q)
            if score(j) > score(prev):
                seen[j["id"]] = j
    for s in d.get("existingStatus", []):
        if s.get("status") == "closed":
            closed_ev[s["id"]] = s.get("evidence", "")
    for nf in d.get("newFacilities", []):
        new_facs.setdefault(nf["key"], nf)
    fac_units.update(d.get("facilityUnits") or {})
    failed += d.get("failedSources", [])

# facilities
for k, nf in new_facs.items():
    if k not in fac_by:
        rec = {x: nf.get(x, "") for x in ["key", "name", "system", "city", "area", "drive", "toll", "units", "careers"]}
        facs.append(rec)
        fac_by[k] = rec
for k, u in fac_units.items():
    if k in fac_by and u:
        fac_by[k]["units"] = u

def norm_emp(e):
    return e if e in ("Full-time", "Part-time", "Per diem") else "Unknown"

def days(a, b):
    return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days

added, closed = [], []
REFRESH = ["title", "url", "pay", "shift", "fte", "needs", "employment"]

def posted_quality(rec):
    """3 = exact date, 2 = approximate, 1 = only a 'before' bound, 0 = none."""
    if not rec.get("posted"):
        return 0
    if rec.get("postedBefore"):
        return 1
    return 2 if rec.get("postedApprox") else 3

def apply_posted(cur, s):
    """Keep the best posting date we have seen; never replace an exact date with a guess."""
    p = s.get("posted")
    if p and p > TODAY:
        p = TODAY
    new = {"posted": p, "postedApprox": bool(s.get("postedApprox")), "postedBefore": bool(s.get("postedBefore"))}
    if posted_quality(new) >= max(1, posted_quality(cur)):
        cur["posted"] = new["posted"]
        cur["postedApprox"] = new["postedApprox"]
        cur["postedBefore"] = new["postedBefore"]
    cur.setdefault("posted", None)
    cur.setdefault("postedApprox", False)
    cur.setdefault("postedBefore", False)

for jid, s in seen.items():
    status = "open" if s.get("verified", True) else "unconfirmed"
    if jid in jobs:
        cur = jobs[jid]
        for k in REFRESH:
            v = s.get(k)
            if v not in (None, "", []):
                cur[k] = norm_emp(v) if k == "employment" else v
        apply_posted(cur, s)
        cur["lastSeen"] = TODAY
        cur["status"] = status
        cur.pop("closedAt", None)
    else:
        fk = s.get("facility")
        f = fac_by.get(fk)
        if not f:
            print("MISSING FACILITY", jid, fk)
            continue
        posted = s.get("posted")
        if posted and posted > TODAY:
            posted = TODAY
        rec = {
            "id": jid, "title": s["title"].lstrip("*").strip(), "system": f["system"], "facility": fk,
            "facilityName": f["name"], "city": f["city"], "area": f["area"], "drive": f["drive"], "toll": f["toll"],
            "unit": s["unit"], "employment": norm_emp(s.get("employment")),
            "fte": s["fte"] if isinstance(s.get("fte"), (int, float)) else None,
            "shift": s.get("shift") or "", "pay": s.get("pay") or "", "posted": posted,
            "needs": s.get("needs") or "", "fit": s.get("fit") or "stretch", "fitNote": s.get("fitNote") or "",
            "url": s["url"], "status": status, "firstSeen": TODAY, "lastSeen": TODAY,
        }
        apply_posted(rec, s)
        jobs[jid] = rec
        added.append(rec)

for jid, j in jobs.items():
    if jid in seen or j.get("status") == "closed":
        continue
    # Close on explicit evidence. Without it (e.g. the employer site refused us), wait two weeks
    # so a few days of blocked checks can't knock real openings off the list.
    if jid in closed_ev or days(j["lastSeen"], TODAY) >= 14:
        j["status"] = "closed"
        j["closedAt"] = TODAY
        closed.append(j)
    elif days(j["lastSeen"], TODAY) >= 3:
        j["status"] = "unconfirmed"

# prune long-closed
jobs = {k: v for k, v in jobs.items() if not (v.get("status") == "closed" and days(v["closedAt"], TODAY) > 30)}

open_jobs = [j for j in jobs.values() if j["status"] != "closed"]
good_new = [a for a in added if a["fit"] != "stretch"]
rank = {"strong": 0, "possible": 1, "stretch": 2}
added.sort(key=lambda a: (rank.get(a["fit"], 3), a["drive"]))
summary = (f"{len(added)} new openings, {len(good_new)} of them strong or worth applying. "
           f"{len(closed)} closed. " + NOTE).strip()
entry = {
    "date": TODAY,
    "ranAt": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
    "summary": summary, "addedCount": len(added), "closedCount": len(closed),
    "added": [{"id": a["id"], "title": a["title"], "facilityName": a["facilityName"], "fit": a["fit"]} for a in added],
    "closed": [{"id": c["id"], "title": c["title"], "facilityName": c["facilityName"]} for c in closed],
}
issues_path = os.path.join(SWEEP, "issues.json")
entry["issues"] = json.load(open(issues_path)) if os.path.exists(issues_path) else []
prev = next((u for u in updates if u["date"] == TODAY), None)
if APPEND and prev:
    entry["added"] = prev.get("added", []) + entry["added"]
    entry["closed"] = prev.get("closed", []) + entry["closed"]
    entry["addedCount"] = len(entry["added"])
    entry["closedCount"] = len(entry["closed"])
    entry["summary"] = (prev.get("summary", "") + " " + NOTE).strip()
    entry["issues"] = prev.get("issues", []) + entry["issues"]
updates = [u for u in updates if u["date"] != TODAY and days(u["date"], TODAY) <= 60] + [entry]
meta["lastRun"] = entry["ranAt"]
meta["openCount"] = len(open_jobs)

json.dump(sorted(jobs.values(), key=lambda j: j["id"]), open(f"{SITE}/jobs.json", "w"), indent=1, ensure_ascii=False)
json.dump(facs, open(f"{SITE}/facilities.json", "w"), indent=1, ensure_ascii=False)
json.dump(updates, open(f"{SITE}/updates.json", "w"), indent=1, ensure_ascii=False)
json.dump(meta, open(f"{SITE}/meta.json", "w"), indent=1)

print("added", len(added), "closed", len(closed), "open", len(open_jobs), "facilities", len(facs))
for a in added:
    print(f"  + [{a['fit']}] {a['unit']} {a['title']} | {a['facilityName']} ({a['drive']} min) | {a['employment']} | {a['status']}")
for c in closed:
    print(f"  - {c['title']} | {c['facilityName']}")

"""Split the currently open jobs into one file per sweep group (A-G) so each sweep re-checks its own jobs.

usage: python3 refresh/split_existing.py SWEEP_DIR
"""
import json, os, sys, collections

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
site = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
jobs = [x for x in json.load(open(os.path.join(site, "jobs.json"))) if x["status"] != "closed"]


def group(x):
    i = x["id"]
    if x["unit"] == "FERT":
        return "G"
    if i.startswith("sutter"):
        return "A"
    if i.startswith("kp-"):
        return "B"
    if i.startswith(("ucsf", "zsfg", "AHS")):
        return "C"
    if i.startswith(("MH-", "SETON", "DIG", "SEQ", "JMH", "WHHS", "CCRMC", "ECH", "CHIN", "SMMC")):
        return "D"
    if i.startswith(("LPCH", "SHC")):
        return "E"
    return "F"


groups = collections.defaultdict(list)
keep = ["id", "title", "facilityName", "unit", "url", "posted", "postedApprox", "postedBefore", "status"]
for x in jobs:
    groups[group(x)].append({k: x.get(k) for k in keep})
for g in "ABCDEFG":
    json.dump(groups[g], open(os.path.join(out, f"existing_{g}.json"), "w"), indent=1)
print({g: len(groups[g]) for g in "ABCDEFG"})

# Kiki's Job Search

A phone-friendly board of Bay Area RN openings in L&D, mother-baby, antepartum, NICU and pre-op/PACU, within about 55 minutes of north and central San Francisco.

- `index.html` is the whole site (no build step).
- `data/jobs.json` holds the openings. `data/facilities.json` lists every hospital checked, with rough drive times. `data/updates.json` logs what changed on each refresh. `data/meta.json` holds the last refresh time.
- Saved jobs, statuses and notes are stored in the browser on each device.

To refresh, ask Claude to re-check the job sites and push updated `data/*.json` files.

# Refresh recipe

How the job list on this site is refreshed. A refresh can be started by hand or by the daily scheduled task. The candidate profile (experience, certifications, home area) is kept in the task instructions, not in this public repo.

## Goal
Find every currently open job that fits the candidate and keep the data files current: add new openings, refresh ones still open, mark ones that closed. Work unattended: do not ask questions, and if a website is refused, denied or waiting for approval, skip it, note it, and use another source.

## Units, exclusions and fit
The candidate (profile in your task instructions) wants full-time staff RN roles (but track part-time and per diem too, labeled) in these units:
- LD = Labor & Delivery / Birth Center / LDRP
- PP = Postpartum / Mother-Baby / Couplet / Well-baby nursery
- ANTE = Antepartum / high-risk OB / perinatal / MFM
- FERT = Fertility clinic / IVF / reproductive endocrinology and infertility (REI) RN roles, incl. IVF procedure and egg-retrieval recovery nurses, nurse coordinators who are RNs, and fertility triage RNs
- NICU = NICU / ICN / special care nursery
- PREOP = Pre-op only: pre-admission testing (PAT), pre-op holding, pre-procedure, pre-op clinic, pre-op phone screening (she asked for these specifically, on top of combined pre-op/PACU roles)
- PACU = PACU / Phase I-II recovery / combined pre-op + PACU / ASU / ACU / pre-post procedure care
- GI = GI lab / endoscopy / gastroenterology procedures / bronchoscopy-endoscopy procedure units (RN roles only; GI techs excluded)
- OR = Operating room / circulating (weaker fit, still track)
Exclude: managers, directors, educators, CNS, NPs, CNAs, LVNs, techs (incl. GI/endoscopy techs), therapists, travel/agency/staffing-firm posts, new-grad residency programs, and any other unit (med-surg, ED, ICU, PICU-only, oncology infusion, cath lab, IR-only, dialysis, etc.).

Fit rating for each job (write one plain-English sentence as fitNote saying what they ask for and how she stacks up):
- strong: she clearly meets the stated minimums (e.g. "1 yr acute care", "6 months RN", "2 yrs OB/postpartum", combined OB units, pre-op/PACU/GI roles that ask only for general acute care experience, fertility roles that ask for general RN or OB/GYN/women's health experience).
- possible: needs 1-2 yrs in the specific unit where her float or adjacent experience is a reasonable argument (e.g. 1 yr PACU, 1 yr GI/endoscopy or procedural sedation, 1 yr L&D, 1-2 yrs fertility/IVF/REI), or the employer offers a training program route (Kaiser's "or KP training program"). ACLS required within a few months of hire does not lower the rating; ACLS required at hire makes a strong role possible.
- stretch: needs 2+ yrs of unit experience she lacks (surgical Level III/IV ICN, critical care, pediatric PACU, 2+ yrs GI/endoscopy, 3+ yrs IVF/REI specifically, 7 yrs PACU), or OR circulating/scrub experience.

## Database shape
data/jobs.json: array, one object per opening. Fields:
{id, title, system, facility (key below), facilityName, city, area, drive (minutes), toll, unit (LD|PP|ANTE|FERT|NICU|PREOP|PACU|GI|OR), employment ("Full-time"|"Part-time"|"Per diem"|"Unknown"), fte (number or null), shift, pay (as posted, e.g. "$89.75-$106.61/hr"), posted ("YYYY-MM-DD" or null), postedApprox (true/false), postedBefore (true/false), needs (their stated minimum experience/certs), fit, fitNote, url (the employer's own posting URL when possible), status ("open"|"unconfirmed"|"closed"), firstSeen, lastSeen, closedAt (only when closed)}
data/updates.json: array with one entry per refresh: {date, ranAt (ISO), summary (2-3 plain sentences: what changed, anything notable like a full-time mother-baby or L&D role, any source that failed), addedCount, closedCount, added: [{id,title,facilityName,fit}], closed: [{id,title,facilityName}]}
data/meta.json: update lastRun (ISO now) and openCount. Keep baseline unchanged.

Posting date (always try to fill it; Kiki relies on it): use the most exact source available. Exact dates: employer "Date posted", Workday postedOn / startDate, UCSF feed pubDate, Kaiser "Date posted", Greenhouse/ADP/UltiPro post dates. Relative ages ("Posted 3 Days Ago", "2d", "3 weeks ago", "re-posted 13 days ago") on Workday, Glassdoor, Built In, Credenza, ZipRecruiter or Indeed: convert to a date by subtracting from the day you saw it and set postedApprox=true. Open-ended ages ("30d+", "30+ days ago"): set posted to the date that many days back, postedApprox=true and postedBefore=true. Leave posted null only when nothing shows an age, and say why in evidence. Never guess a date from an ID number.

Job id conventions (keep these stable so a posting matches across days): Kaiser kp-<Taleo job number>; Sutter sutter-R-<number> (no "-1" suffix); UCSF ucsf-<number at end of the careers.ucsf.edu JobDetail URL>; SF General zsfg-<SmartRecruiters posting id>; MarinHealth MH-<JR number>; Seton SETON-<iCIMS id>; Dignity/CommonSpirit DIG-<req>; Lucile Packard LPCH-<req or URL id>; Stanford Health Care SHC-<R number>, Tri-Valley SHCTV-<R number>; John Muir JMH-<JR number>; Washington Hospital WHHS-<jobvite id>; El Camino ECH-<id>; Contra Costa CCRMC-<id>; anything else <SHORTNAME>-<req>. Before adding a "new" job, check it is not already in the DB under another id (same employer + same req number, same URL, or same title + facility + FTE + shift).

## Facilities
data/facilities.json is the list of every hospital, surgery center, endoscopy center and fertility clinic tracked, with its key, name, system, city, area, drive minutes from north/central SF, bridge toll on the drive home, units and careers URL. Use those keys. A job at a site not listed: add it if it fits and is within about 55 min, with a new short key, and return the site in "newFacilities" (same fields; short name without street address).

## How to run
Today = the date in America/Los_Angeles (YYYY-MM-DD). SWEEP = /home/claude/research/<today>.
1. In the repo: git pull. Then `python3 refresh/split_existing.py SWEEP` (writes existing_A.json .. existing_G.json).
2. Start the 7 sweeps as subagents (Agent tool, general-purpose, run_in_background true) in ONE message so they run in parallel, then wait for all 7 to finish:
   A) Sutter Health  B) Kaiser Permanente  C) UCSF Health + SF General + Alameda Health (Highland)  D) MarinHealth, Dignity/CommonSpirit (Sequoia), Seton, Chinese Hospital, John Muir, Washington Hospital, Contra Costa Regional, El Camino, San Mateo Medical Center  E) Stanford (LPCH + SHC) + job-board catch-all  F) Independent endoscopy and surgery centers (incl. Tenet San Ramon) + GI / pre-op catch-all  G) Fertility clinics (system-owned and private)
   Give each agent this prompt, filled in:
   "You are one of seven parallel sweeps refreshing an RN job tracker. Today is <today>. Be thorough; many tool calls are fine. If any web fetch is refused, denied or times out waiting for approval, do not retry it; note it in failedSources and use another route (WebSearch results, Glassdoor, Indeed, Built In, Credenza, ZipRecruiter, SimplyHired). Use cache-busters (e.g. ?v=<today digits>) on Workday, Glassdoor and Built In fetches.
   Candidate: <paste the candidate profile from your task instructions>.
   1. Read <repo>/refresh/RECIPE.md in full. Follow: Units, exclusions and fit; Database shape (incl. the posting date rules); Job id conventions; Facilities (keys in <repo>/data/facilities.json); Search terms for the newer units; General notes; and recipe section <X>.
   2. Scope: <scope line for X from step 2 above>, all units listed in the recipe.
   3. Existing open jobs in your scope: SWEEP/existing_<X>.json. For each, decide open / closed / unknown with evidence, and fill or improve its posting date if missing or approximate. Try to confirm 'unconfirmed' ones on the employer's own page.
   4. Find every currently open relevant job in scope that is not already in the existing list. Verify each. Write each fitNote as one sentence addressed to her as 'you'. Exclude postings open only to current employees.
   5. Write SWEEP/<X>.json: {jobs:[full job objects per the schema incl. posted/postedApprox/postedBefore, minus firstSeen/lastSeen/status, plus verified and evidence], existingStatus:[{id,status,evidence}], newFacilities:[...], facilityUnits:{}, failedSources:[...]}. Include still-open existing jobs in jobs too, under the same id.
   6. Use only WebSearch and WebFetch for the web (the shell has no internet). Never invent a job.
   Reply with only: existing open / closed / unknown counts, new jobs by unit, failed sources, under 100 words."
3. Review the new jobs across the 7 files (print id, unit, fit, verified, title, facility, url, evidence). Drop duplicates of jobs already listed under another id, leads another sweep already verified, and postings she cannot apply to. Then:
   `python3 refresh/merge.py <today> SWEEP "<comma-separated ids to drop>" "<one or two sentences on anything notable or any source that failed>"`
   merge.py keeps the better-evidenced copy when two sweeps report the same job, never replaces an exact posting date with a guess, marks jobs reported closed, marks unseen jobs unconfirmed after 3 days and closed after 7, prunes jobs closed more than 30 days, and writes the day's entry to data/updates.json and data/meta.json.
4. Check: every job's facility key exists in data/facilities.json, ids are unique, and the counts printed by merge.py look right.
5. Commit only data/*.json with a short message ("Refresh <today>: N new openings, M closed"), git fetch origin main, then push to main.
6. Finish with a short plain-text summary (it becomes the phone notification): number of new openings and closed ones, then each new strong or possible job as "Title, Facility (~N min)". If nothing changed, say "No new openings today."

## Search terms for the newer units (use alongside each recipe's own terms)
GI: "GI lab", "endoscopy", "gastroenterology", "GI/endo", "procedure center", "procedural sedation", "digestive health", "bronch/endo". Kaiser department names: "Gastroenterology", "GI Lab", "Endoscopy". UCSF feed terms: Endoscopy, GI+Lab, Gastroenterology, Digestive. Glassdoor kw: endoscopy, gi-lab, gi-nurse. Built In search: endoscopy, GI. Indeed: endoscopy-rn, gi-lab-rn.
PREOP: "pre-op", "preop", "pre-operative", "pre-admission", "PAT", "pre-procedure", "pre-anesthesia", "perioperative screening", "surgical screening". UCSF feed terms: Pre-Admission, Preop, Pre-Op, Pre-Anesthesia, Perioperative. Glassdoor kw: pre-op-nurse, preop, pre-admission.

FERT: "fertility nurse", "IVF nurse", "REI nurse", "reproductive endocrinology", "fertility RN", "nurse coordinator fertility", "egg retrieval", "reproductive health". UCSF feed terms: Fertility, Reproductive, IVF. Glassdoor kw: fertility-nurse, ivf-nurse. Indeed: fertility-nurse, ivf-nurse.

## Recipes by source
General: WebFetch respects robots.txt, so some hosts refuse (LinkedIn, dejobs.org, api.smartrecruiters.com, governmentjobs.com, kaiserpermanentejobs.org/search-jobs). Keep WebFetch URLs short. Prefer fetching URLs taken from search results or from pages already read; some hand-typed URLs get refused. Use WebSearch mode "extended" for fresh results. Most Workday/Phenom search pages render empty; their sitemaps and detail JSON usually work.

A) SUTTER
- Discovery, Glassdoor keyword pages (current, show posted age and pay; only page 1 loads): https://www.glassdoor.com/Jobs/Sutter-Health-<kw>-Jobs-EI_IE4654.0,13_KO14,<14+len(kw)>.htm for kw in labor-and-delivery, postpartum, nicu, nursery, neonatal, perinatal, maternal, pacu, pre-op, operating-room-nurse, surgery-nurse, surgery-center. Example: https://www.glassdoor.com/Jobs/Sutter-Health-nicu-Jobs-EI_IE4654.0,13_KO14,18.htm
- Discovery, Workday sitemap with city + exact slug in each path (cuts off around 230 entries): https://wd1.myworkdaysite.com/recruiting/sutterhealth/SH/siteMap.xml
- Discovery, Built In: https://builtin.com/jobs?search=staff%20nurse&city=San%20Francisco&state=California&country=USA (also page=2, and search=neonatal, NICU, PACU, nursery, LDRP; and city=Oakland). Shows "posted X days ago".
- Verify each job: GET https://sutterhealth.wd1.myworkdayjobs.com/wday/cxs/sutterhealth/SH/job/x/<Exact-Title-Slug>_R-NNNNNN (try with and without "-1"). Slug rules: ", " becomes "--", " & " becomes "---". JSON with canApply=true means open; it also gives location, postedOn, timeType and the description (Organization, Weekly Hours, Shift, Pay Range, experience) and similarJobs. An error means closed OR wrong slug; get the exact slug from the sitemap or a similarJobs externalPath before calling it closed.
- Do NOT use jobs.sutterhealth.org job pages for status; they say "Inactive" for everything.
- Posting URL to store: https://sutterhealth.wd1.myworkdayjobs.com/en-US/SH/job/<City>/<Slug>_R-NNNNNN[-1]
- Sites: CPMC Van Ness (L&D, Mom & Baby, NICU, ASU/PACU), CPMC Mission Bernal, CPMC Davies, Sutter Outpatient SF (1635 Divisadero), Mills-Peninsula (Family Birth Center, NICU, PACU), Alta Bates Berkeley (L&D, NICU), Summit Oakland, Oakland Oncology Surgery Center, Novato, Eden Castro Valley (nursery + postpartum couplets), Sutter MFM clinics.

B) KAISER
- City nursing lists, page 1 and page 2 (add /2): https://www.kaiserpermanentejobs.org/employment/<city>-nursing-licensed-and-nurse-practitioners-jobs/641/8267760/<geo>/4
  geo codes: san-francisco 6252001-5332921-5391997-5391959 ; oakland 6252001-5332921-5322745-5378538 ; walnut-creek 6252001-5332921-5406990 ; richmond 6252001-5332921-5387428 ; san-leandro 6252001-5332921-5392263 ; san-rafael 6252001-5332921-5392567 ; redwood-city 6252001-5332921-5386834 ; south-san-francisco 6252001-5332921-5397765
- Open every job on those lists titled only "Staff Nurse II" or similar generic titles: the unit is named only on the job page (that is how the Oakland NICU jobs were found). Job pages give Date posted, department, hours, shift, pay, requirements.
- A job is open only if all three hold: its page loads; "Submit Interest" links to kp.taleo.net ... job=<number>; and https://www.kaiserpermanentejobs.org/business/custom_fields.reqid/<number>/641/5 shows "1 Job Results". A page that loads but shows 0 there is closed.
- Backup: Glassdoor Kaiser pages and WebSearch site:kaiserpermanentejobs.org with unit words (results include many stale jobs; verify).
- Note: Kaiser labels 36 h/wk (0.9) as part-time; record fte.
- The statewide California nursing list (all pages) catches jobs the city lists miss, e.g. Pleasanton medical offices; scan it too. Exclude lactation-only roles that require IBCLC.

C) UCSF + SF GENERAL + ALAMEDA HEALTH
- UCSF RSS feeds list only open jobs, posted date included, max 20 items oldest first, paging ignored, so use narrow terms: https://ucsf.avature.net/careers/SearchJobs/feed/?search=<term> for Birth+Center, Postpartum, Antepartum, Mother+Baby, Nursery, Intensive+Care+Nursery, Registered+Nurse+NICU, Registered+Nurse+PACU, Preop, Pre-Op, Perianesthesia, Perioperative, Registered+Nurse+PD, Stanyan+PACU, Hyde+PACU, Stanyan+Registered+Nurse, Hyde+Surgery. A job has closed when its id drops out of every feed (detail pages often stay up, so they don't prove it's open).
- Detail for unit, FTE, shift, requirements: https://careers.ucsf.edu/careers/JobDetail/x/<id>
- UCSF campuses: Mission Bay Birth Center (Betty Irene Moore), ICN at Benioff Children's SF, Benioff Children's Oakland NICU and PACU, Bayfront ASC, Stanyan, Hyde, Parnassus, Mount Zion, Peninsula Outpatient Surgery (Burlingame).
- SF General / SFDPH: https://careers.smartrecruiters.com/cityandcountyofsanfrancisco1/?search=2320 and ?search=registered%20nurse . Status: jobs.smartrecruiters.com/cityandcountyofsanfrancisco1/<id> ("Sorry, this job has expired" = closed). careers.sf.gov role pages show expired jobs as open; don't use them for status. Known continuous postings: the 2320 citywide experienced RN list (H00083) and P103 per diem; also watch for unit-specific 2320 Perinatal / Birth Center / NICU / PACU postings.
- Alameda Health System (Highland): its site and dejobs mirrors are blocked; check https://www.glassdoor.com/Jobs/Alameda-Health-System-Jobs-E844633.htm and open Oakland "Clinical Nurse" listings for unit and "Job expired". Its OB/NICU openings have mostly been new-grad only (exclude those).
- Backup: Credenza SF RN list, newest first: https://credenzahealth.com/jobs/rn/in-san-francisco-ca (and ?page=2, ?page=3; stop once listings are a week old).

D) MARIN, DIGNITY, SETON, OTHERS
- MarinHealth Workday sitemap (cap 100; add a cache-buster like ?v=<today digits>): https://mymarinhealth.wd5.myworkdayjobs.com/MHCareers/siteMap.xml . Look for LDRP, Neonatal, Birth, Mother, Post Anesthesia, Pre-Op, Surgery and Procedures. Detail JSON: https://mymarinhealth.wd5.myworkdayjobs.com/wday/cxs/mymarinhealth/MHCareers/job/Greenbrae-CA/<slug>_<JR#> (posted date, pay). Closed = gone from sitemap and detail errors. Indeed and Credenza keep showing closed MarinHealth jobs; don't trust them for status.
- Dignity / CommonSpirit (Sequoia Hospital birth center and PACU; St. Mary's and Saint Francis are now UCSF Stanyan and Hyde): https://www.commonspirit.careers/employment/redwood-city-california-united-states-staff-nurse-jobs/35300/8231200/6252001-5332921-5392427-5386834/4?x=<n> and https://www.commonspirit.careers/business/custom_fields.facility/sequoia%20hospital/35300/5?x=<n> and https://www.commonspirit.careers/employment/san-francisco-california-united-states-staff-nurse-jobs/35300/8231200/6252001-5332921-5391997-5391959/4 . Only presence on the live list counts as open; old detail pages keep rendering.
- Seton (Daly City; no maternity; OR and PACU): https://careers-ahmchealth.icims.com/jobs/search?searchKeyword=seton+nurse&in_iframe=1 and &pr=1 for page 2. The list shows department, shift and pay. Jobs drop off when closed.
- Chinese Hospital: https://chinesehospital-sf.org/job-opportunities/ (no maternity; only PACU/OR would fit).
- John Muir Walnut Creek: https://careers.johnmuirhealth.com/employment/walnut-creek-nursing-jobs/14695/8581824/6252001-5332921-5339268-5406990/4 , https://jmh.wd5.myworkdayjobs.com/JohnMuirHealthCareers/siteMap.xml (lists jobs the first one misses), https://careers.johnmuirhealth.com/sitemap.xml . Employer detail pages show Apply when open.
- Washington Hospital Fremont: https://jobs.jobvite.com/washingtonhospital/jobs
- Contra Costa Regional (Martinez): governmentjobs.com is blocked; use WebSearch for "Contra Costa Registered Nurse Labor Delivery Nursery Postpartum" and Indeed viewjob pages for expired status.
- El Camino (Mountain View): Indeed search/viewjob pages, e.g. https://www.indeed.com/q-nicu-rn-l-mountain-view,-ca-jobs.html

E) STANFORD + JOB-BOARD CATCH-ALL
- Lucile Packard: https://careers.stanfordchildrens.org/sitemap.xml (complete list). Check Clinical Nurse roles in Labor and Delivery, Mother Baby / Postpartum, Antepartum, NICU / Intensive Care Nursery, Pre-op / PACU. Detail pages show Apply Now when open.
- Stanford Health Care: Glassdoor https://www.glassdoor.com/Jobs/Stanford-Health-Care-Registered-Nurse-Jobs-EI_IE11884.0,20_KO21,37.htm and https://www.glassdoor.com/Jobs/Stanford-Health-Care-pacu-rn-Jobs-EI_IE11884.0,20_KO21,28.htm ; Workday sitemaps https://stanfordmedicine.wd115.myworkdayjobs.com/SHC_External_Career_Site/siteMap.xml and https://stanfordmedicine.wd115.myworkdayjobs.com/SHC_Tri-Valley_External_Careers/siteMap.xml . SHC's old Phenom pages say "no longer available" for everything; ignore them.
- Catch-all boards for any employer within ~55 min: Glassdoor searches https://www.glassdoor.com/Job/san-francisco-ca-nicu-rn-jobs-SRCH_IL.0,16_IC1147401_KO17,24.htm , https://www.glassdoor.com/Job/san-francisco-pacu-rn-jobs-SRCH_IL.0,13_IC1147401_KO14,21.htm , https://www.glassdoor.com/Job/san-francisco-ca-labor-and-delivery-nurse-jobs-SRCH_IL.0,16_IC1147401_KO17,41.htm , https://www.glassdoor.com/Job/walnut-creek-labor-delivery-rn-jobs-SRCH_IL.0,12_IC1147417_KO13,30.htm ; Built In (as in A); Credenza (as in C); Indeed searches https://www.indeed.com/q-rn-labor-delivery-l-san-francisco-bay-area,-ca-jobs.html , https://www.indeed.com/q-mother-baby-nurse-l-san-francisco-bay-area,-ca-jobs.html , https://www.indeed.com/q-Postpartum-RN-l-San-Francisco-Bay-Area,-CA-jobs.html , https://www.indeed.com/q-nicu-rn-l-san-francisco,-ca-jobs.html , https://www.indeed.com/q-perinatal-nurse-l-san-francisco,-ca-jobs.html . Indeed rate-limits: open at most about 20 Indeed viewjob pages per run; their "expired" banner is reliable but they show no dates. Pass any lead for an employer covered by A-D through to the merge with its employer URL if you can find it.

F) OUTPATIENT ENDOSCOPY + SURGERY CENTERS, GI / PRE-OP CATCH-ALL
- Find independent and joint-venture endoscopy centers and ambulatory surgery centers within ~55 min of north/central SF (SF, Marin, north Peninsula, inner East Bay): e.g. endoscopy centers in SF, Marin, San Mateo, Oakland, Walnut Creek; USPI, SCA Health, Optum, AmSurg/Envision, Covenant and independent ASCs; GI physician groups that run their own endoscopy centers. WebSearch "endoscopy center San Francisco RN job", "ambulatory surgery center pre-op RN San Francisco", "GI lab RN Bay Area", etc. (mode "extended").
- Employer career pages (often Workday, iCIMS, Paylocity, UKG, BambooHR, ADP) or Indeed/Glassdoor/Built In listings. Verify each lead is open (employer page with Apply, or a board page without an expired notice and with a recent date).
- Catch-all boards across all employers for GI and pre-op: Glassdoor https://www.glassdoor.com/Job/san-francisco-endoscopy-rn-jobs-SRCH_IL.0,13_IC1147401_KO14,26.htm , https://www.glassdoor.com/Job/san-francisco-gi-lab-rn-jobs-SRCH_IL.0,13_IC1147401_KO14,23.htm , https://www.glassdoor.com/Job/san-francisco-pre-op-nurse-jobs-SRCH_IL.0,13_IC1147401_KO14,26.htm ; Indeed https://www.indeed.com/q-endoscopy-rn-l-san-francisco-bay-area,-ca-jobs.html , https://www.indeed.com/q-gi-lab-rn-l-san-francisco-bay-area,-ca-jobs.html , https://www.indeed.com/q-pre-op-rn-l-san-francisco-bay-area,-ca-jobs.html ; Built In https://builtin.com/jobs?search=endoscopy&city=San%20Francisco&state=California&country=USA ; Credenza https://credenzahealth.com/jobs/rn/in-san-francisco-ca . If a URL pattern is refused, find the working one through WebSearch results.
- Leads at Sutter, Kaiser, UCSF, ZSFG, MarinHealth, Dignity, Seton, John Muir, Stanford are covered by other agents; still report them (with employer URL if found) so the merge can cross-check.

G) FERTILITY CLINICS
- System-owned: UCSF Center for Reproductive Health (Mission Bay; via UCSF feeds), Kaiser fertility / reproductive endocrinology services in NorCal, Stanford Fertility and Reproductive Health, Sutter / Palo Alto Medical Foundation fertility, John Muir, MarinHealth, CPMC.
- Private and network clinics in SF, Marin, the Peninsula and the inner East Bay (and Stanford-area if within ~55 min): find them with WebSearch ("fertility clinic San Francisco nurse job", "IVF nurse Bay Area", "fertility RN Oakland", etc., mode "extended"). Networks to check include Kindbody, Spring Fertility, Pacific Fertility Center, CCRM, US Fertility / IntegraMed, Inception / Prelude (and its clinics), RMA, Shady Grove's parent, Golden Gate Fertility, Zouves, Laurel Fertility, Bay IVF, Reproductive Science Center of the SF Bay Area. Use each employer's careers page (Greenhouse, Lever, Workday, iCIMS, Paylocity, ADP, BambooHR, Rippling, etc.) when readable; otherwise Glassdoor/Indeed/Built In/Credenza listings with recent dates.
- RN roles only (exclude MAs, LVNs, embryologists, NPs, coordinators who are not RNs). Note if a role is mostly phone/triage vs. procedure/recovery.

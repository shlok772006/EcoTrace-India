# TASK_LIST.md — EcoTrace India
### Sprint-by-Sprint Implementation Plan

> Paste the CURRENT SPRINT section into Anti-Gravity at the start of each session.
> Check off tasks as you complete them.

---

## Anti-Gravity Session Starter (paste this EVERY session)

```
I am building EcoTrace India for Prompt Wars Virtual Challenge 3.
This is a carbon footprint awareness platform for Indian users.

Before writing any code, read these files in my project:
- SPEC.md — source of truth, do not deviate
- ARCHITECTURE.md — folder structure and API routes to follow exactly
- DATA_MODEL.md — use ONLY these emission factors, never invent your own numbers
- DESIGN.md — follow this color palette and component style exactly
- PROMPT_STRATEGY.md — use these Gemini prompts exactly as written

Critical rules:
- GEMINI_API_KEY must always come from os.environ.get("GEMINI_API_KEY") only
- Never hardcode any API keys or secrets anywhere
- All files must go in the folder structure defined in ARCHITECTURE.md
- Use Procfile for deployment: web: gunicorn --bind :8080 --workers 1 --threads 8 app:app
- Add Google Cloud Logging (google-cloud-logging library) to app.py
- Add type hints to all Python functions
- Do not change anything outside the current sprint's task list

Current sprint: [REPLACE WITH: SPRINT 1 / SPRINT 2 / SPRINT 3]
Today's tasks: [PASTE TASKS FROM CURRENT SPRINT BELOW]
```

---

## ===== SPRINT 1 — MVP (Submit TODAY for time multiplier) =====

**Goal:** Working calculator + AI insights + deployed on Cloud Run.
**Target score:** 75-85%

### Phase 1A — Project Setup
- [ ] Create folder structure exactly as defined in ARCHITECTURE.md
- [ ] Create `requirements.txt`:
  ```
  flask==3.0.3
  google-generativeai==0.7.2
  google-cloud-logging==3.11.3
  flask-limiter==3.7.0
  bleach==6.1.0
  python-dotenv==1.0.1
  gunicorn==22.0.0
  ```
- [ ] Create `.env.example` with `GEMINI_API_KEY=your_key_here`
- [ ] Create `.gitignore` (ignore .env, venv, __pycache__)
- [ ] Create `Procfile` with: `web: gunicorn --bind :8080 --workers 1 --threads 8 app:app`
- [ ] Create `Dockerfile`
- [ ] Create `data/emission_factors.json` from DATA_MODEL.md values

### Phase 1B — Calculator Backend
- [ ] Create `calculator.py` with:
  - [ ] `load_emission_factors()` — reads data/emission_factors.json
  - [ ] `calculate_footprint(user_data: dict) -> dict` — full formula from DATA_MODEL.md
  - [ ] `calculate_eco_score(total: float) -> dict` — grading formula from DATA_MODEL.md
  - [ ] `calculate_tree_offset(total: float) -> dict`
  - [ ] Type hints on all functions
- [ ] Create `gemini_client.py` with:
  - [ ] Gemini initialization from env variable
  - [ ] `get_insights(footprint_data: dict, language: str) -> dict`
  - [ ] All prompts from PROMPT_STRATEGY.md
  - [ ] Cloud Logging integration
- [ ] Create `app.py` with:
  - [ ] Cloud Logging initialization
  - [ ] All routes (pages + API endpoints from ARCHITECTURE.md)
  - [ ] `POST /api/calculate` endpoint
  - [ ] `POST /api/insights` endpoint
  - [ ] `GET /health` endpoint
  - [ ] Rate limiting on API endpoints
  - [ ] Input validation and bleach sanitization
  - [ ] Error handlers (404, 500)
  - [ ] Type hints on all functions

### Phase 1C — Frontend (Sprint 1 minimum)
- [ ] `templates/index.html` — landing page with hero, 3 feature cards, India stats
- [ ] `templates/calculator.html` — 4-step form (Energy/Transport/Diet/Waste)
  - [ ] Step progress indicator
  - [ ] Real-time running total
  - [ ] Back/Next navigation
- [ ] `templates/results.html` — Eco Score badge, breakdown, 3 AI insight cards
- [ ] `static/css/style.css` — full styles from DESIGN.md
- [ ] `static/js/app.js` — form logic, API calls, chart rendering

### Phase 1D — README
- [ ] Write README.md with: project description, features, Google services table,
      how to run locally, how to deploy, prompt strategy summary

### Phase 1E — Deploy
- [ ] Push all code to GitHub (main branch only)
- [ ] Open shell.cloud.google.com
- [ ] Clone repo: `git clone https://github.com/shlok772006/EcoTrace-India.git`
- [ ] Navigate: `cd EcoTrace-India`
- [ ] Verify Procfile exists: `cat Procfile`
- [ ] Deploy: `gcloud run deploy ecotrace-india --source . --region asia-south1 --allow-unauthenticated --set-env-vars GEMINI_API_KEY=YOUR_KEY,GOOGLE_CLOUD_PROJECT=new-project-shlok --min-instances 1`
- [ ] Test live URL in incognito

### Phase 1F — Submit
- [ ] Write LinkedIn Post 1 (tools, approach, what you built)
- [ ] Tag @Google for Developers and @Hack2Skill
- [ ] Submit: GitHub URL + Cloud Run URL + LinkedIn URL
- [ ] **Note score breakdown — especially which dimensions are weak**

---

## ===== SPRINT 2 — Features =====

**Goal:** Add action plan, tree calculator, tracker, multilingual support.
**Target score:** 88-93%

### Phase 2A — New Backend Features
- [ ] Add `get_action_plan(footprint_data, language)` to gemini_client.py
- [ ] Add `get_progress_message(prev, current, language)` to gemini_client.py
- [ ] Add `POST /api/action-plan` endpoint to app.py
- [ ] Add `POST /api/chat` endpoint to app.py

### Phase 2B — New Pages
- [ ] `templates/action_plan.html` — 4-week accordion plan
- [ ] `templates/tracker.html` — monthly progress chart (Chart.js line chart)
- [ ] `templates/chat.html` — floating AI chat

### Phase 2C — Enhance Calculator
- [ ] Add language selector to index.html (English/Hindi/Marathi/Tamil/Telugu)
- [ ] Pass language through all API calls
- [ ] Add city tier selector (Metro/Tier-2/Rural)

### Phase 2D — Enhance Results
- [ ] Add tree offset section to results.html
- [ ] Add "Save to Tracker" button
- [ ] Add Chart.js category breakdown chart

### Phase 2E — Code Quality
- [ ] Add `test_app.py` with pytest tests for all endpoints
- [ ] Verify all type hints are present
- [ ] Run through accessibility checklist from DESIGN.md

### Phase 2F — Deploy + Submit
- [ ] Push to GitHub
- [ ] Pull and redeploy in Cloud Shell:
  `cd EcoTrace-India && git pull origin main`
  `gcloud run deploy ecotrace-india --source . --region asia-south1 --allow-unauthenticated --set-env-vars GEMINI_API_KEY=YOUR_KEY,GOOGLE_CLOUD_PROJECT=new-project-shlok --min-instances 1`
- [ ] Test all new features in incognito
- [ ] Write LinkedIn Post 2
- [ ] Submit Attempt 2

---

## ===== SPRINT 3 — Polish & Final Submission =====

**Goal:** Perfect score across all dimensions. This is the FINAL submission.
**Target score:** 95%+

### Phase 3A — Eco Badge Feature
- [ ] Shareable Eco Score card on results page
- [ ] Confetti animation on A+ or A grade
- [ ] Badge shows: grade, total tonnes, top tip, India rank

### Phase 3B — Performance & Security
- [ ] Verify no API keys anywhere in source: `grep -r "AIza" . --exclude-dir=venv`
- [ ] Add Content Security Policy headers to Flask responses
- [ ] Add request ID logging for traceability
- [ ] Verify rate limiting is working

### Phase 3C — Testing
- [ ] Expand test_app.py to cover all edge cases:
  - [ ] Zero values in calculator
  - [ ] Maximum values in calculator
  - [ ] Invalid diet type
  - [ ] Missing required fields
  - [ ] Oversized inputs (XSS attempts)
- [ ] Run pytest and make sure all tests pass

### Phase 3D — Accessibility Audit
- [ ] Add aria-labels to all form inputs
- [ ] Verify keyboard navigation on all pages
- [ ] Check color contrast ratios
- [ ] Test with browser accessibility tools
- [ ] Add skip-to-main-content link

### Phase 3E — Final Documentation
- [ ] Update README with:
  - [ ] Live demo URL filled in
  - [ ] Complete Google services table
  - [ ] Mermaid architecture diagram
  - [ ] How to run locally section complete
- [ ] Update CHANGELOG.md with all three attempts

### Phase 3F — Final Checks
- [ ] Repo is public ✓
- [ ] Single branch (main) only ✓
- [ ] Repo size under 10 MB: `du -sh .` (exclude .git)
- [ ] Procfile exists ✓
- [ ] No .env file committed: `git status`
- [ ] Live URL works in incognito on phone ✓
- [ ] All 4 categories calculate correctly ✓
- [ ] AI insights return valid JSON ✓

### Phase 3G — Final Submit
- [ ] Write LinkedIn Post 3 (most detailed — full journey from Attempt 1 to 3)
- [ ] Tag @Google for Developers and @Hack2Skill
- [ ] Submit FINAL attempt

---

## Pre-Submission Checklist (run before EVERY attempt)

| Check | Status |
|---|---|
| No API key in any source file | ☐ |
| .env not in git: `git status` shows clean | ☐ |
| GitHub repo is public | ☐ |
| Only one branch exists (main) | ☐ |
| Repo under 10 MB | ☐ |
| Procfile exists at root | ☐ |
| Cloud Run URL opens in incognito | ☐ |
| Calculator gives correct result for test inputs | ☐ |
| AI insights load on results page | ☐ |
| README has Google services listed | ☐ |
| LinkedIn post published with both mandatory tags | ☐ |

---

## Quick Deploy Command (Cloud Shell — copy-paste ready)

```bash
cd ~/EcoTrace-India && git pull origin main && gcloud run deploy ecotrace-india --source . --region asia-south1 --allow-unauthenticated --set-env-vars GEMINI_API_KEY=YOUR_KEY_HERE,GOOGLE_CLOUD_PROJECT=new-project-shlok --min-instances 1
```

# CHANGELOG.md — EcoTrace India
### Submission Log

---

## Attempt 3 — 2026-06-11 — FINAL SUBMISSION
**Score:** [FILL AFTER EVALUATION]
**Rank:** [FILL AFTER EVALUATION]
**Render URL:** [FILL]
**LinkedIn Post:** [FILL]

### What changed from Attempt 2:
- [x] Redesigned Eco Badge to be a shareable card with score, total tonnes, and top tip.
- [x] Implemented Share button using Web Share API and Clipboard fallback.
- [x] Secured Flask with strict Content Security Policy (CSP) headers.
- [x] Added `REQUEST_ID` logging for better traceability.
- [x] Implemented comprehensive automated test suite (`pytest`) in `test_app.py` covering all edge cases (zero values, max values, missing fields, XSS).
- [x] Conducted accessibility audit: added skip-to-main-content link, focus-visible outlines, and verified aria-labels.
- [x] Added confetti library (Canvas-confetti) for A/A+ grade celebration.
- [x] Updated README with deployment instructions and architecture overview.

### Prompt changes:
- [Document here]

### Lessons learned:
- [Document here]

---

## Attempt 2 — 2026-06-10
**Score:** [FILL AFTER EVALUATION]
**Rank:** [FILL AFTER EVALUATION]
**Render URL:** [FILL]
**LinkedIn Post:** [FILL]

### What changed from Attempt 1:
- [x] Added 30-day action plan (Gemini)
- [x] Added tree offset calculator
- [x] Added monthly progress tracker
- [x] Added multilingual support
- [x] Added city tier personalization
- [x] Added Chart.js visualizations
- [x] Migrated from Cloud Run to Render
- [x] Upgraded to `google-genai` and `gemini-2.5-flash`

### Prompt changes:
- Added Prompt 3 (Action Plan)
- Added Prompt 5 (Progress Motivator)
- Refined Prompt 2: added city_tier injection
- Rewritten SDK calls to use `genai.Client()` syntax

### Lessons learned:
- Upgrading to `google-genai` is required to access newer models like `gemini-2.5-flash` reliably.
- Render offers a smoother automated deployment pipeline directly from GitHub compared to manual Cloud Run commands.

---

## Attempt 1 — 2026-06-08
**Score:** [FILL AFTER EVALUATION]
**Rank:** [FILL AFTER EVALUATION]
**Render URL:** [FILL]
**LinkedIn Post:** [FILL]

### What was built:
- Carbon calculator (4 categories)
- AI insights (3 personalized tips)
- India benchmark comparison
- Eco Score badge
- Cloud Run deployment

### Prompt changes:
- v1.0: Basic system prompt
- v1.1: Added India context
- v1.2: Added JSON enforcement
- v1.3: Added india_context field per tip

### Lessons learned:
- [Document here]

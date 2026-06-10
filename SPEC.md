# SPEC.md — EcoTrace India
### Software Requirements Specification (SRS)
> Version: 1.0 | Challenge: Prompt Wars Virtual – Challenge 3 | Carbon Footprint Awareness Platform

---

## <Objectives>

EcoTrace India is an AI-powered carbon footprint awareness platform that helps Indian
individuals understand, track, and reduce their carbon footprint through simple inputs,
personalized AI insights, and actionable reduction plans.

The platform aims to:
1. Calculate a user's annual carbon footprint using India-specific emission factors.
2. Compare their footprint against Indian and global benchmarks.
3. Identify which lifestyle category (energy/transport/food/waste) contributes most.
4. Provide Gemini-powered personalized reduction tips based on the user's actual data.
5. Generate a 30-day action plan tailored to the user's highest-impact areas.
6. Track progress over multiple months to show improvement over time.
7. Make climate awareness engaging through gamification and shareable badges.

**Target Users:** Urban Indian individuals, students, working professionals, and families
who want to understand their environmental impact and take meaningful action.

</Objectives>

---

## <Features>

### Feature List ###

#### F1 — Carbon Footprint Calculator (Core)
- Multi-step form collecting data across 4 categories:
  - Energy: monthly electricity (kWh or units), LPG cylinders per month
  - Transport: km per month by car (petrol/diesel), two-wheeler, train, domestic flight
  - Diet: vegan / vegetarian / non-vegetarian / heavy meat eater
  - Waste: approximate monthly waste in kg, recycling habits
- Real-time running total shown as user fills in the form.
- Results in tonnes CO2e per year.
- Uses India-specific emission factors defined in DATA_MODEL.md.
- Breakdown by category shown as a visual bar chart.

#### F2 — AI Insights (Gemini-powered)
- After calculation, Gemini analyzes the user's data.
- Returns exactly 3 personalized reduction tips targeting the user's top emission sources.
- Each tip includes: what to do, estimated CO2 saved per year, difficulty level (easy/medium/hard).
- Tips adapt to the user's city tier (metro/tier-2/rural) if provided.

#### F3 — India Benchmarks Comparison
- Visual comparison showing user's footprint vs:
  - National average: 2.0 tonnes/year
  - Urban average: 5.0 tonnes/year
  - Global average: 4.7 tonnes/year
  - Global 2050 target: 2.0 tonnes/year
- Color-coded: green (below average), amber (average), red (above average).
- Contextual message explaining what the number means in plain language.

#### F4 — 30-Day Action Plan Generator
- User clicks "Generate My Action Plan."
- Gemini creates a personalized week-by-week plan with specific daily actions.
- Actions are ranked by CO2 impact and ease of implementation.
- Downloadable as text or copyable.

#### F5 — Tree Offset Calculator
- Based on their total footprint, shows:
  - How many trees they need to plant to offset their emissions.
  - How many years it would take those trees to offset.
  - Equivalent in km of car driving they could eliminate instead.
- Formula: 1 tree absorbs 0.025 tonnes CO2 per year.

#### F6 — Monthly Progress Tracker
- Users can log their footprint each month.
- Line chart shows trend over time (stored in browser localStorage).
- Percentage change shown month over month.
- Motivational message from Gemini when improvement is detected.

#### F7 — Eco Score Badge
- After completing the calculator, user gets an Eco Score (A+ to F).
- Shareable card with their score, footprint, and top tip.
- Calculated as: score relative to India urban average.

#### F8 — AI Chat Assistant
- A floating chat button available on all pages.
- Users can ask any question about carbon footprint, climate change, or sustainability.
- Gemini answers in simple language, grounded in Indian context.
- Suggests relevant app features based on the conversation.

</Features>

---

## <Constraints>

### Technical Constraints
- **Deployment:** Google Cloud Run exclusively.
- **Repository:** Public GitHub repo, single branch (main), under 10 MB.
- **AI Model:** Gemini 1.5 Flash via Google Generative AI SDK.
- **API Key Security:** GEMINI_API_KEY must come from environment variable ONLY. Never hardcoded anywhere.
- **Backend:** Python 3.11 with Flask.
- **Frontend:** Vanilla HTML, CSS, JavaScript. No heavy frameworks.
- **Procfile:** Must exist at root: `web: gunicorn --bind :8080 --workers 1 --threads 8 app:app`
- **Dockerfile:** Must exist at root for Cloud Run compatibility.
- **State:** Browser localStorage for progress tracking. No external database needed.
- **Bundle Size:** All static assets under 5 MB total.
- **Cold Start:** min-instances set to 1 on Cloud Run.
- **Logging:** Google Cloud Logging via google-cloud-logging library.

### Content Constraints
- All emission factors must be India-specific (defined in DATA_MODEL.md).
- No political content about climate policy.
- All advice must be practical and achievable for an average Indian household.
- Never fabricate statistics — use only values defined in DATA_MODEL.md.

### Submission Constraints
- GitHub repository must be public.
- README.md must explain the project, Google services, and approach clearly.
- LinkedIn post must accompany each submission.
- Repo must have only one branch (main).

</Constraints>

---

## <UserPersonas>

### Persona 1 — Rohan, 24, Software Engineer, Bengaluru
Commutes by cab, eats non-veg, uses AC heavily. Has heard about carbon footprints
but never calculated his. Wants to know if he should switch to an EV.

### Persona 2 — Priya, 35, Teacher, Pune
Vegetarian, uses two-wheeler, concerned about her family's impact.
Wants practical tips that don't require spending money.

### Persona 3 — Arjun, 19, College Student, Tier-2 city
Uses public transport, curious about climate change.
Wants to understand the science and share his eco score with friends.

</UserPersonas>

---

## <GeminiSystemPrompts>

### Base System Prompt (All interactions)
```
You are EcoBot, a friendly and knowledgeable carbon footprint advisor
specialized in the Indian context. You help Indian individuals understand
and reduce their environmental impact through practical, achievable actions.

Your knowledge base: India-specific emission factors, Indian lifestyle patterns,
local transportation options, Indian dietary habits, and government sustainability
initiatives like Solar Rooftop scheme, PM e-DRIVE, and Green India Mission.

Always:
- Use India-specific data and examples.
- Give practical advice achievable within an Indian budget and lifestyle.
- Be encouraging — every small action matters.
- Respond in simple, clear language.
- Keep responses concise (under 200 words) unless asked for more.
- Respond in the user's chosen language: {language}.

Never:
- Fabricate emission statistics.
- Give advice that requires expensive purchases as the only option.
- Express political opinions about climate policy.
- Answer questions unrelated to carbon footprint and sustainability.
```

### Insights Prompt (after calculator)
See PROMPT_STRATEGY.md — Prompt 2

### Action Plan Prompt
See PROMPT_STRATEGY.md — Prompt 3

### Chat Prompt
See PROMPT_STRATEGY.md — Prompt 4

</GeminiSystemPrompts>

---

## <MilestonesPlan>

| Milestone | Goal | Attempt |
|---|---|---|
| M1 — MVP | Calculator + AI Insights + Benchmarks deployed | Attempt 1 (submit ASAP) |
| M2 — Features | Action Plan + Tree Calculator + Progress Tracker | Attempt 2 |
| M3 — Polish | Eco Badge + Chat + Tests + Accessibility + README | Attempt 3 (Final) |

</MilestonesPlan>

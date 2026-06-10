# ARCHITECTURE.md — EcoTrace India
### System Architecture & Folder Structure

---

## Folder Structure
```
EcoTrace-India/
├── app.py                        # Flask app, all routes and API endpoints
├── calculator.py                 # Pure calculation logic (no Flask dependency)
├── gemini_client.py              # All Gemini API calls and prompt building
├── requirements.txt              # Python dependencies (pinned versions)
├── Procfile                      # web: gunicorn --bind :8080 --workers 1 --threads 8 app:app
├── Dockerfile                    # Container config for Cloud Run
├── .env.example                  # Template — NEVER commit .env
├── .gitignore                    # Ignore .env, venv, __pycache__
├── test_app.py                   # pytest unit tests
├── static/
│   ├── css/
│   │   └── style.css             # All styles
│   └── js/
│       └── app.js                # Frontend logic, chart rendering, localStorage
├── templates/
│   ├── index.html                # Landing page
│   ├── calculator.html           # Multi-step carbon calculator form
│   ├── results.html              # Results, breakdown, benchmarks, eco score
│   ├── action_plan.html          # 30-day AI action plan
│   ├── tracker.html              # Monthly progress tracker
│   └── chat.html                 # AI chat assistant
├── data/
│   └── emission_factors.json     # All values from DATA_MODEL.md
├── SPEC.md
├── DATA_MODEL.md
├── ARCHITECTURE.md
├── TASK_LIST.md
├── DESIGN.md
├── PROMPT_STRATEGY.md
├── CHANGELOG.md
└── README.md
```

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      USER BROWSER                           │
│                                                             │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌────────────┐  │
│  │ Landing  │ │ Calculator │ │ Results  │ │  Tracker   │  │
│  │  Page    │ │   Form     │ │  Page    │ │   Page     │  │
│  └────┬─────┘ └─────┬──────┘ └────┬─────┘ └─────┬──────┘  │
│       └─────────────┴──────────────┴─────────────┘         │
│                      app.js + localStorage                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS REST API calls
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            GOOGLE CLOUD RUN (Flask + Gunicorn)              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   app.py (Flask)                     │  │
│  │                                                      │  │
│  │  GET  /                  → index.html                │  │
│  │  GET  /calculator        → calculator.html           │  │
│  │  GET  /results           → results.html              │  │
│  │  GET  /action-plan       → action_plan.html          │  │
│  │  GET  /tracker           → tracker.html              │  │
│  │  GET  /chat              → chat.html                 │  │
│  │                                                      │  │
│  │  POST /api/calculate     → run calculation           │  │
│  │  POST /api/insights      → Gemini insights           │  │
│  │  POST /api/action-plan   → Gemini action plan        │  │
│  │  POST /api/chat          → Gemini chat               │  │
│  │  GET  /health            → health check              │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│  ┌──────────────┴────────────────────────────────────────┐ │
│  │              calculator.py                            │ │
│  │  - calculate_footprint(user_data) → breakdown + total │ │
│  │  - calculate_eco_score(total)     → grade + label     │ │
│  │  - calculate_tree_offset(total)   → trees + equiv     │ │
│  │  - load_emission_factors()        → from JSON         │ │
│  └──────────────┬────────────────────────────────────────┘ │
│                 │                                           │
│  ┌──────────────┴────────────────────────────────────────┐ │
│  │              gemini_client.py                         │ │
│  │  - get_insights(footprint_data, language)             │ │
│  │  - get_action_plan(footprint_data, language)          │ │
│  │  - get_chat_response(message, history, language)      │ │
│  │  - Reads GEMINI_API_KEY from environment variable     │ │
│  └──────────────┬────────────────────────────────────────┘ │
│                 │                                           │
│  ┌──────────────┴────────────────────────────────────────┐ │
│  │              Google Cloud Logging                     │ │
│  │  All logs → GCP Cloud Logging dashboard               │ │
│  └───────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               GOOGLE GEMINI 1.5 FLASH API                   │
│  Model: gemini-1.5-flash                                    │
│  Auth: GEMINI_API_KEY (environment variable only)           │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### POST /api/calculate
**Input:**
```json
{
  "electricity_kwh": 150,
  "lpg_cylinders": 1.5,
  "petrol_car_km": 500,
  "two_wheeler_km": 200,
  "train_km": 100,
  "flight_km": 0,
  "diet_type": "non_vegetarian",
  "waste_kg": 20,
  "recycles": true,
  "composts": false,
  "city_tier": "metro",
  "language": "English"
}
```
**Output:** Full footprint result (see DATA_MODEL.md DataSchema)

---

### POST /api/insights
**Input:** Full footprint result from /api/calculate + language
**Output:**
```json
{
  "insights": [
    {
      "tip": "Switch to LED bulbs throughout your home",
      "co2_saved_kg": 120,
      "difficulty": "easy",
      "category": "energy"
    }
  ]
}
```

---

### POST /api/action-plan
**Input:** Full footprint result + language
**Output:**
```json
{
  "plan": {
    "week_1": ["Action 1", "Action 2"],
    "week_2": ["Action 3", "Action 4"],
    "week_3": ["Action 5", "Action 6"],
    "week_4": ["Action 7", "Action 8"]
  },
  "estimated_annual_saving": 0.8
}
```

---

### POST /api/chat
**Input:** message, chat_history, language
**Output:** AI response text

---

### GET /health
**Output:**
```json
{
  "status": "healthy",
  "services": ["gemini-api", "cloud-logging", "cloud-run"],
  "timestamp": "2025-05-01T10:00:00Z"
}
```

---

## Google Services Used

| Service | Role |
|---|---|
| Gemini 1.5 Flash API | All AI: insights, action plans, chat |
| Google Cloud Run | App hosting and serving |
| Google Cloud Logging | Structured application logging |
| Google Cloud Build | Container build during deployment |

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID for Cloud Logging | Yes |
| `PORT` | Port (auto-set by Cloud Run to 8080) | Auto |

---

## Security Architecture
- GEMINI_API_KEY never in source code — environment variable only
- All user inputs sanitized with bleach before processing
- Rate limiting: /api/insights 20 req/min, /api/chat 30 req/min
- Flask runs behind Cloud Run HTTPS termination
- Non-root user in Docker container
- No user data stored server-side (privacy by design)

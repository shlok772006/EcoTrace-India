# EcoTrace India 🌱
### AI-Powered Carbon Footprint Awareness Platform for India

> Built for **Prompt Wars Virtual – Challenge 3** | Powered by **Google Gemini API** | Deployed on **Google Cloud Run**

---

## What is EcoTrace India?

EcoTrace India helps every Indian citizen understand, track, and reduce their
carbon footprint through simple inputs, India-specific calculations, and
personalized AI-powered insights. Built specifically for Indian users with
India's emission factors, benchmarks, and lifestyle context.

**Live Demo:** `[YOUR CLOUD RUN URL HERE]`
**GitHub:** `https://github.com/shlok772006/EcoTrace-India`

---

## Features

| Feature | Description |
|---|---|
| 🧮 Carbon Calculator | 4-category calculator with India-specific emission factors |
| 🤖 AI Insights | 3 personalized Gemini-powered reduction tips |
| 📊 Benchmark Comparison | Compare against India national, urban, and global averages |
| 📅 30-Day Action Plan | Personalized AI-generated weekly action plan |
| 🌳 Tree Offset Calculator | How many trees to offset your footprint |
| 📈 Progress Tracker | Monthly footprint trend with AI motivation |
| 🏆 Eco Score Badge | Shareable A+ to F grade based on India urban average |
| 💬 AI Chat | Ask any sustainability question |

---

## Problem Statement Alignment

**Challenge 3 Goal:** Design a solution that helps individuals understand, track,
and reduce their carbon footprint through simple actions and personalized insights.

EcoTrace India addresses this by:
- Making calculation **simple** — a 4-step form anyone can complete in 3 minutes
- Using **India-specific data** — not generic Western calculators
- Providing **personalized AI insights** — based on the user's actual data, not generic tips
- Enabling **tracking** — monthly progress with trend visualization
- Giving **actionable plans** — a structured 30-day reduction roadmap

---

## Google Services Used

| Service | How It's Used |
|---|---|
| **Gemini 1.5 Flash API** | Powers AI insights, action plans, chat, and motivational messages |
| **Google Cloud Run** | Hosts and serves the entire application |
| **Google Cloud Logging** | Structured application logging and monitoring |
| **Google Cloud Build** | Builds Docker container on each deployment |

---

## India-Specific Emission Factors Used

| Category | Factor | Source |
|---|---|---|
| Electricity | 0.75 kg CO2/kWh | Central Electricity Authority India |
| LPG Cylinder | 37.68 kg CO2/cylinder | Ministry of Petroleum India |
| Petrol Car | 0.171 kg CO2/km | MORTH + IPCC |
| Two-Wheeler | 0.089 kg CO2/km | MORTH + IPCC |
| Indian Railways | 0.011 kg CO2/km | Indian Railways Sustainability Report |
| Domestic Flight | 0.255 kg CO2/km | ICAO Calculator |

---

## Project Structure

```
EcoTrace-India/
├── app.py              # Flask backend, all routes and API endpoints
├── calculator.py       # Pure calculation logic with India emission factors
├── gemini_client.py    # Gemini API integration and prompt management
├── requirements.txt    # Python dependencies
├── Procfile            # Cloud Run process definition
├── Dockerfile          # Container configuration
├── static/             # CSS and JavaScript
├── templates/          # HTML pages
├── data/               # Emission factors JSON
└── test_app.py         # pytest unit tests
```

---

## How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/shlok772006/EcoTrace-India.git
cd EcoTrace-India

# 2. Create virtual environment (Python 3.11 required)
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 5. Run
flask run
```

Visit `http://localhost:5000`

---

## Deploying to Google Cloud Run

```bash
# In Google Cloud Shell (shell.cloud.google.com)
git clone https://github.com/shlok772006/EcoTrace-India.git
cd EcoTrace-India

gcloud run deploy ecotrace-india \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key_here,GOOGLE_CLOUD_PROJECT=your_project_id \
  --min-instances 1
```

---

## Prompt Strategy

All Gemini prompts are documented in `PROMPT_STRATEGY.md`. Key principles:
- Real user data injected into every prompt (prevents generic advice)
- India-specific context enforced in system prompt
- Structured JSON output enforced for frontend parsing
- Guardrails against political content and fabricated statistics

---

## Architecture

```
User Browser → Flask on Cloud Run → Gemini 1.5 Flash API
                     ↓
              calculator.py (India emission factors)
              gemini_client.py (prompt management)
              Google Cloud Logging (monitoring)
```

---

*Built with ❤️ for a greener India | Prompt Wars Virtual 2025*

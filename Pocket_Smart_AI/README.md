# PocketSmart AI

Complete FastAPI + Jinja2 + SQLite + Gemini application.

## Features

- Registration, login and logout
- JWT authentication stored in an HTTP-only cookie
- Home Interior Planner
- Party Budget Planner
- Jewelry Planner with optional outfit image
- Gemini structured-output recommendations
- Local fallback recommendations when Gemini is unavailable
- Recommendation history
- Responsive HTML/CSS/JavaScript UI
- Platform search links for Amazon, Flipkart, IKEA, Swiggy, Zomato and OYO
- FastAPI Swagger docs at /docs

## Windows setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
# HireMind — Agentic AI Recruitment & Candidate Screening Platform

A polished final-year-project version of the original Streamlit prototype. The new version separates a **FastAPI backend** from a **React/Vite frontend**, keeps SQLite for zero-setup local persistence, supports PDF/DOCX/TXT resume analysis, structured scoring, AI-generated interviews and candidate ranking.

## Features
- Candidate + Recruiter authentication with JWT and hashed passwords
- Recruiter vacancy builder with skills, experience, location, salary, openings and deadline
- Candidate job discovery and application workflow
- Resume extraction from PDF, DOCX and TXT
- Explainable resume score using text similarity + skill match + experience fit
- 10-question role-specific interview agent
- Ollama-first offline LLM integration with deterministic fallback
- AI grading of interview answers
- Final fit score = 60% resume + 40% interview
- Recruiter ranked candidate leaderboard and status management
- Responsive, animated, multi-page React interface
- No Docker

## Folder structure
```
AI-Recruiter-Final/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── schemas.py
│   │   └── services/
│   │       ├── resume_service.py
│   │       └── ai_service.py
│   ├── data/
│   ├── uploads/
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── styles.css
│   │   ├── main.jsx
│   │   └── lib/api.js
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
└── README.md
```

## Windows setup — no Docker

### 1. Backend
Open a terminal in `backend`:
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```
API: http://127.0.0.1:8000  
Swagger docs: http://127.0.0.1:8000/docs

### 2. Frontend
Open a second terminal in `frontend`:
```powershell
npm install
npm run dev
```
Open the Vite URL, normally http://localhost:5173

## Ollama offline AI
Install Ollama, then pull a model:
```powershell
ollama pull llama3.2
```
Keep Ollama running. The backend defaults to:
```env
AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2
```
If Ollama is unavailable, the app still works using its local question bank and transparent fallback answer evaluator.

## Extending to a free API later
The AI service is isolated in `backend/app/services/ai_service.py`. Add another provider there and switch it using `AI_PROVIDER`. This keeps UI/business logic independent from the LLM vendor.

## Scoring model
Resume score:
- 45% job-description text similarity
- 40% required-skill match
- 15% experience fit

Final fit:
- 60% resume score
- 40% interview score

For a production hiring system, these scores should be treated as decision support, audited for bias, and reviewed by a human recruiter rather than used as an automatic employment decision.
"# Hiremind" 

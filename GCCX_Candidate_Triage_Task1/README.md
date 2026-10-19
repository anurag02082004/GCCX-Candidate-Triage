# GCCX Candidate Triage Tool — Task 1

A focused candidate-review workspace adapted from the supplied resume-screening starter project for the GCCX AI Full-Stack Engineer Intern case study.

## What is implemented

- **Candidate list:** loads all 48 mock candidates from the supplied `candidates.json` into a local SQLite database on first backend startup.
- **Search:** searches candidate name, target role, notes, and candidate ID.
- **Filters:** target role, source, skill, minimum/maximum years of experience, and shortlisted-only.
- **Shortlist:** add/remove a candidate from the shortlist; state persists in SQLite.
- **Tags:** add comma-separated recruiter tags; state persists in SQLite.
- **Real LLM feature:** asks Groq to generate a short, evidence-grounded fit summary from candidate notes and skills. Configure `GROQ_API_KEY` to enable it. If no key is configured or the API call fails, the UI explicitly explains that; it does not pretend a template is an AI result.
- **Responsive UI:** desktop and mobile layouts, loading/error/empty states, API health indicator.
- **Human-in-the-loop:** summaries are decision support only and should not be used as an automatic hiring decision.

## Python compatibility

The backend targets **Python 3.14.0** (not Python 4.14, which is not a released Python version). Verify it with `py -3.14 --version`. This Task 1 backend intentionally drops unused legacy ML dependencies from the original resume-screening project to keep the triage app lean and compatible. If a package has no compatible wheel on your machine, use Python 3.13 as a documented fallback rather than forcing an incompatible install.

## Stack

- Frontend: React 18 + Vite
- Backend: Python + FastAPI
- Database: SQLite
- AI: Groq API (`openai/gpt-oss-20b`) through the backend; the API key stays server-side

## Project layout

```text
backend/
  api/routes.py              # Existing API + candidate triage endpoints
  data/candidates.json       # Supplied 48-record dataset
  data/triage.sqlite3        # Created automatically at runtime
  services/triage_store.py   # SQLite seed, search/filter, shortlist and tags
  services/triage_ai.py      # Real Groq API integration
  main.py
frontend/
  src/App.jsx                # Candidate triage UI
  src/api.js                 # API calls
  src/styles.css
```

## Run locally (Windows PowerShell)

### 1. Backend

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and set `GROQ_API_KEY` to your own Groq key. Set `GROQ_MODEL` to `openai/gpt-oss-20b` unless you choose another model available to your Groq account. Do not commit `.env` or expose the key in frontend code.

Start the API:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs  
Health check: http://127.0.0.1:8000/health

### 2. Frontend (new terminal)

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally http://127.0.0.1:5173).

## API endpoints for Task 1

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/candidates` | List candidates; supports `search`, `role`, `source`, `skill`, `min_experience`, `max_experience`, `shortlisted_only` |
| GET | `/api/candidate-facets` | Filter options from the dataset |
| PATCH | `/api/candidates/{candidate_id}` | Update shortlist state and/or tags |
| POST | `/api/candidates/{candidate_id}/fit-summary` | Generate an evidence-grounded Groq fit summary |

Examples:

```text
GET /api/candidates?search=python&min_experience=2
GET /api/candidates?role=Platform%20Engineer&shortlisted_only=true
PATCH /api/candidates/cand_001
POST /api/candidates/cand_001/fit-summary
```

PATCH JSON example:

```json
{
  "is_shortlisted": true,
  "tags": ["strong ownership", "follow up"]
}
```

Fit-summary JSON example:

```json
{
  "job_role": "AI Full-Stack Engineer Intern"
}
```

## Data and assumptions

- The supplied starter kit describes these as **48 mock records**, not real candidate data.
- Original candidate fields are preserved: `id`, `name`, `target_role`, `years_experience`, `source`, `skills`, `notes`, and `applied_date`.
- Shortlist state and tags are application metadata stored in SQLite, separate from the source JSON.
- Filters are exact for role/source and case-insensitive substring matches for search/skill.
- The AI prompt is instructed to use only supplied candidate evidence, avoid inventing achievements, and identify a point to verify when supported.
- The fit summary is intentionally not represented as an objective score or hiring decision. The dataset is small and the notes are imperfect.
- The database seeds only when its candidate table is empty. To reset local state, stop the backend and delete `backend/data/triage.sqlite3`; it will be recreated from the JSON on next startup.

## Known limitations / next steps

- Add authentication and authorization before deploying beyond local evaluation.
- Add pagination if the dataset grows substantially.
- Consider request caching and rate limiting for the LLM endpoint.
- Add automated tests for API filters, tag validation, shortlist persistence, and AI provider errors.
- If deployed, use a managed secret store for `GROQ_API_KEY` and a persistent database volume.

## Interview demo flow (3–4 minutes)

1. Open the candidate list and explain that the source is the supplied 48-record JSON dataset.
2. Search for a skill/name, then filter by role, source, and experience.
3. Shortlist a candidate and save tags; refresh to show that state persists.
4. Generate a fit summary with Groq and explain that the API key is kept in the backend.
5. Close with the guardrail: AI supports triage but does not make hiring decisions.


## Acceptance checklist before submission

- [ ] `python -m pip check` reports no broken requirements.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] `http://127.0.0.1:8000/docs` opens and candidate endpoints respond.
- [ ] Search, every filter, shortlist and tag persistence are verified in the browser.
- [ ] Groq fit-summary returns `provider: "groq"` using your own valid API key. A missing key or API error must be shown clearly, never replaced with fake AI output.
- [ ] `npm run build` completes successfully.
- [ ] No real API key, `.env`, database, virtual environment or build artifacts are committed.
- [ ] AI collaboration log and judgment note are reviewed and personalized to match what you actually did.

## Scope and assumptions

- The supplied mock dataset is seeded only when the SQLite candidates table is empty. To reset local demo data, stop the backend, delete `backend/data/triage.sqlite3`, and restart it. This also resets saved shortlist/tag state.
- Skill filters use exact, case-insensitive matching. Search across free-text notes is intentionally simple substring search; semantic search is out of scope.
- AI fit summaries are optional decision support. Recruiters must verify source evidence and make all hiring decisions themselves.

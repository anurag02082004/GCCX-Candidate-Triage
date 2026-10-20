GCCX Candidate Triage
A candidate-triage project built as part of the GCCX engineering assessment. This repository brings together the Task 1 candidate-triage application and the Task 2 candidate-ranking/code-review work.
Note: Folder names and commands below are based on the current project context. Confirm them against the files in your repository before submitting.

Project Overview
Recruiters often need to review candidate profiles against a role's requirements. This project explores a workflow for organizing candidate information, producing AI-assisted summaries where configured, and ranking candidates by skill overlap.
Main components
- Task 1 — Candidate Triage Application
  - FastAPI backend.
  - Candidate data stored in JSON in the project's data directory.
  - AI-assisted summaries through a configured model provider (Gemini or Groq, depending on the active implementation and environment configuration).
  - Frontend application for interacting with the candidate-triage workflow.
- Task 2 — Candidate Ranking and Code Review
  - Candidate ranking based on overlap between candidate skill tags and required skills.
  - Focus on efficient lookups and ranking at larger candidate volumes.
  - Code review of a supplied JavaScript matching function, including identified defects, a minimal correction, and an explanation of the changes.
- Task 3 — AI Collaboration Log
  - Record the AI tools used, what they helped with, and real prompts used during development.
  - Include AI_COLLABORATION_LOG.md if that is the filename used for your log.
Repository Structure
The repository should resemble the structure below. Keep your actual folder names if they differ.
GCCX-Candidate-Triage/
├── GCCX_Candidate_Triage_Task1/
│   ├── backend/
│   │   ├── main.py
│   │   ├── data/
│   │   └── ...
│   ├── frontend/
│   │   └── ...
│   └── ...
├── task 2/
│   ├── app.py
│   ├── ranking.py
│   └── ...
├── AI_COLLABORATION_LOG.md
├── .gitignore
└── README.md
Technology Stack
- Backend: Python, FastAPI, Uvicorn
- AI integration: Gemini or Groq, depending on configuration
- Frontend: JavaScript and npm-based tooling
- Ranking / data processing: Python and Streamlit for the Task 2 interface, where applicable
- Version control: Git and GitHub
Prerequisites
Install the tools needed for the components you intend to run:
- Python compatible with the project's dependencies
- Node.js and npm for the frontend
- Git
- An API key for the AI provider if you want to use AI-generated summaries
Use the Python and package versions specified by the project files where available.
Setup and Run
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/GCCX-Candidate-Triage.git
cd GCCX-Candidate-Triage
Replace YOUR_USERNAME with the GitHub account that hosts the repository.
2. Run Task 1 — Backend
Open a terminal in the Task 1 backend directory. For the example layout above:
cd GCCX_Candidate_Triage_Task1/backend
python -m venv .venv
Activate the environment:

Windows PowerShell
.\.venv\Scripts\Activate.ps1
macOS / Linux
source .venv/bin/activate
Install dependencies if a requirements.txt file is present:
python -m pip install -r requirements.txt
Configure environment variables in a local .env file using the variable names expected by the code. For example, if the implementation uses Gemini:
GEMINI_API_KEY=your_gemini_api_key
If the implementation uses Groq instead, provide the variable name expected by your code (often GROQ_API_KEY) and configure the model name if required. Never commit .env or real API keys. Check the backend source and any .env.example file for the exact supported variable names.

Start the API:
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
When the server is running, open the interactive API documentation at:

http://127.0.0.1:8000/docs
3. Run Task 1 — Frontend
Open a second terminal in the Task 1 frontend directory:
cd GCCX_Candidate_Triage_Task1/frontend
npm install
Then use the script defined in package.json, commonly:
npm run dev
If the project defines a different start script, use the command listed in package.json. Configure the frontend API base URL, if required, to point to the running backend.
4. Run Task 2 — Candidate Ranking
Open a terminal in the Task 2 directory:
cd "task 2"
Create and activate a Python virtual environment if needed, then install dependencies specified by the Task 2 project. If a requirements.txt file exists:
python -m pip install -r requirements.txt
If the Streamlit entry point is app.py, launch it with:
python -m streamlit run app.py
If you only need to run or test the ranking logic, inspect ranking.py and follow any instructions included in that folder.
Candidate Ranking Approach
The ranking task compares a candidate's skill tags with the required skills for a search. A typical score is the number of distinct required skills that also appear in the candidate's skill set. Candidates can then be sorted from highest score to lowest.

For an implementation that builds a Set of required skills, membership checks are typically average O(1). With N candidates, S average skills per candidate, and R required skills, a common overall complexity is:
- Time: O(R + N × S + N log N) when all candidates are scored and sorted.
- Space: typically O(R + N) for the required-skill set and returned ranking records, excluding input storage and any temporary per-candidate structures.
Exact complexity depends on the submitted implementation, data structures, and whether candidate skills contain duplicates. Refer to the Task 2 code for the precise approach.
Configuration and Security
- Keep API keys and credentials in environment variables or a local .env file.
- Ensure .env, .venv/, node_modules/, Python cache files, and build outputs are excluded by .gitignore.
- Do not put private candidate data or confidential assessment data in a public repository.
- Use sample or anonymized data when sharing the project publicly.
- Do not publish logs containing secrets or personally identifiable information.
Known Setup Notes
- AI summaries may be unavailable until a valid API key and supported model configuration are provided.
- Exact model/provider environment variable names depend on the active implementation. Verify them in the backend source and local configuration example.
- Frontend commands depend on the scripts defined in package.json.
- Dependency installation commands assume the corresponding requirements.txt or package.json exists in that component.
Assessment Submission Checklist
- [ ] Task 1 source code and required configuration examples are included.
- [ ] Task 2 ranking implementation and code-review explanation are included.
- [ ] Task 3 AI collaboration log includes the tools used and real prompts required by the assessment.
- [ ] Setup instructions and dependency files are included.
- [ ] No API keys, .env files, virtual environments, node_modules, or private candidate data are committed.
- [ ] The GitHub repository link has the required access permissions.
Author
Candidate: Kanishk Raj

Built for the GCCX Candidate Triage engineering assessment.

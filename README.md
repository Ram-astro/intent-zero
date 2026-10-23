# INTENT ZERO — Phase 1: Intent → Workflow → Validation

A local-first starter implementation for the INTENT ZERO intelligence engine.

## What is implemented
- React + TypeScript + Vite command interface
- FastAPI backend
- Optional Ollama integration using `qwen3:8b` (configurable)
- Structured workflow generation
- Deterministic validation of workflow shape, task IDs, dependencies, cycles, and allowlisted action types
- API health check and clear reporting when Ollama is unavailable

## Important scope
This is a development prototype. The executor is deliberately not connected to real external services. "Validate" checks structural rules; it does not guarantee that a plan is factually correct or safe in every real-world context. The fallback planner is rule-based and clearly labelled. No external actions are taken.

## Requirements
- Python 3.10+
- Node.js 20+
- Ollama installed locally if you want model-backed planning

## 1. Start Ollama (optional, for AI-backed planning)
Install Ollama, then run:

```bash
ollama pull qwen3:8b
ollama serve
```

If Ollama is already running, just pull the model if needed.

## 2. Start the backend
Open a terminal in `backend/`:

Windows PowerShell:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

If PowerShell blocks activation, use:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Or skip virtual-environment activation and use:
```powershell
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

## 3. Start the frontend
Open another terminal in `frontend/`:

```bash
npm install
npm run dev
```

Open the URL printed by Vite, usually http://127.0.0.1:5173.

## Configuration
Backend environment variables are in `backend/.env.example`:
- `OLLAMA_BASE_URL` default `http://127.0.0.1:11434`
- `OLLAMA_MODEL` default `qwen3:8b`
- `OLLAMA_TIMEOUT_SECONDS` default `90`
- `FRONTEND_ORIGIN` default `http://127.0.0.1:5173`

If Ollama is unavailable, the backend returns a deterministic rule-based proposal and marks `planner_mode` as `fallback`. It does not silently claim the model generated it.

## API
- `GET /api/health`
- `POST /api/workflows/plan` with `{ "goal": "Create a 7-day DBMS study plan" }`
- `POST /api/workflows/validate` with a workflow object

## Next milestones
1. Add persistent SQLite workflow history.
2. Add domain-specific polymorphic handlers.
3. Add approval gates and a permissioned executor.
4. Add test coverage for malformed model responses and safety policies.
5. Connect real integrations only through explicitly allowlisted actions.

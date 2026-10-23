from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import FRONTEND_ORIGIN, OLLAMA_BASE_URL, OLLAMA_MODEL
from .models import PlanRequest, WorkflowPlan, ValidationResponse
from .planner import create_plan
from .validator import validate_workflow
import httpx

app = FastAPI(title="INTENT ZERO API", version="0.1.0",
              description="Local-first natural-language workflow planning and deterministic structure validation.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_ORIGIN.rstrip("/"),
        "https://intent-zero.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"name": "INTENT ZERO API", "version": "0.1.0", "docs": "/docs"}

@app.get("/api/health")
async def health():
    ollama = "offline"
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            r.raise_for_status()
            models = [m.get("name", "") for m in r.json().get("models", [])]
            ollama = "online" if any(OLLAMA_MODEL in m for m in models) else "online_model_missing"
    except Exception:
        pass
    return {"status": "ok", "service": "intent-zero-api", "ollama": ollama, "model": OLLAMA_MODEL}

@app.post("/api/workflows/plan", response_model=WorkflowPlan)
async def plan_workflow(request: PlanRequest):
    return await create_plan(request.goal.strip())

@app.post("/api/workflows/validate", response_model=ValidationResponse)
async def validate_plan(plan: WorkflowPlan):
    return validate_workflow(plan)

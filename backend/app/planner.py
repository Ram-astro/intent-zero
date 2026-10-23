import json
import re
import httpx
from .config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS
from .models import WorkflowPlan, WorkflowStep

SYSTEM_PROMPT = """You are the planning component of INTENT ZERO. Convert a user's goal into a reviewable workflow proposal.
Return ONLY a valid JSON object with keys: domain, summary, steps, assumptions.
steps must be an array of 3-7 objects. Each step object must contain:
id (simple unique string such as step_1), title, description, action_type, depends_on (array of step IDs), requires_approval (boolean).
Allowed action_type values: think, analyze, transform, prepare, review, notify, external_action.
Use external_action only when the plan truly involves an external side effect; set requires_approval true for those steps.
Do not claim that anything has been executed. Do not invent that tools, files, websites, or accounts are connected.
Prefer safe planning, transparent assumptions, and ordered dependencies."""

def _extract_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Model response did not contain a JSON object.")
    return json.loads(text[start:end + 1])

def fallback_plan(goal: str) -> WorkflowPlan:
    lower = goal.lower()
    if any(k in lower for k in ["study", "exam", "learn", "dbms", "college"]):
        domain = "Education"
        titles = [
            ("Clarify the learning target", "Identify the subject, deadline, available time, and expected outcome."),
            ("Break down the syllabus", "Group topics by importance, difficulty, and prerequisites."),
            ("Create a study sequence", "Arrange focused sessions with breaks and realistic daily workload."),
            ("Schedule revision and practice", "Add recall sessions, practice questions, and progress checkpoints."),
        ]
    elif any(k in lower for k in ["csv", "data", "dataset", "analy"]):
        domain = "Data Analysis"
        titles = [
            ("Define the analysis question", "Identify the dataset, target columns, and decision the analysis should support."),
            ("Inspect data quality", "Check types, missing values, duplicates, and obvious inconsistencies."),
            ("Analyze relevant patterns", "Choose summaries and comparisons appropriate to the question."),
            ("Prepare findings", "Summarize trends, caveats, and follow-up questions without overstating evidence."),
        ]
    elif any(k in lower for k in ["trip", "travel", "visit", "holiday"]):
        domain = "Travel"
        titles = [
            ("Capture trip constraints", "Identify destination, dates, budget, travellers, and preferences."),
            ("Compare available options", "List transport and accommodation choices for later verification."),
            ("Arrange an itinerary", "Sequence activities with travel time and contingency buffers."),
            ("Review costs and open decisions", "Estimate costs and flag any details that require current confirmation."),
        ]
    elif any(k in lower for k in ["code", "software", "app", "website", "build", "project"]):
        domain = "Software & Projects"
        titles = [
            ("Define requirements", "Turn the goal into clear features, constraints, and success criteria."),
            ("Design the implementation", "Choose components and identify dependencies before coding."),
            ("Implement in milestones", "Split work into small, testable tasks."),
            ("Test and review", "Define checks, known limitations, and a release checklist."),
        ]
    else:
        domain = "General Workflow"
        titles = [
            ("Define the outcome", "Clarify what success looks like and which constraints matter."),
            ("Identify inputs and unknowns", "List required information, resources, and unresolved questions."),
            ("Build an ordered plan", "Break the outcome into small steps with explicit dependencies."),
            ("Review risks and completion criteria", "Check assumptions, define done, and identify what needs human approval."),
        ]
    steps = []
    previous = []
    for i, (title, description) in enumerate(titles, 1):
        steps.append(WorkflowStep(id=f"step_{i}", title=title, description=description,
                                  action_type="think" if i == 1 else ("review" if i == len(titles) else "prepare"),
                                  depends_on=previous.copy(), requires_approval=False))
        previous = [f"step_{i}"]
    return WorkflowPlan(goal=goal, domain=domain,
                        summary="Rule-based starter proposal. Connect Ollama for model-backed interpretation.",
                        steps=steps, assumptions=["No external tools or data sources are connected."],
                        planner_mode="fallback")

async def create_plan(goal: str) -> WorkflowPlan:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Create a workflow proposal for this goal:\n{goal}"}
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()
            raw = response.json()["message"]["content"]
        obj = _extract_json(raw)
        obj["goal"] = goal
        obj["planner_mode"] = "ollama"
        # Validate the model output against the strict schema before returning.
        return WorkflowPlan.model_validate(obj)
    except Exception:
        # Explicit fallback mode makes model failures visible instead of pretending AI succeeded.
        return fallback_plan(goal)

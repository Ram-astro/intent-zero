import { FormEvent, useEffect, useState } from "react";

type Step = { id: string; title: string; description: string; action_type: string; depends_on: string[]; requires_approval: boolean };
type Plan = { goal: string; domain: string; summary: string; steps: Step[]; assumptions: string[]; planner_mode: "ollama" | "fallback" };
type Issue = { severity: string; code: string; message: string };
type Validation = { valid: boolean; issues: Issue[]; checked_steps: number };
const API = "http://127.0.0.1:8000";
const examples = [
  "Create a 7-day study plan for my DBMS exam",
  "Analyze a CSV dataset and summarize key trends",
  "Plan a 3-day trip within a realistic budget",
  "Create an implementation plan for a student project",
];
export default function App() {
  const [goal, setGoal] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [validation, setValidation] = useState<Validation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState<{status:string;ollama:string;model:string}|null>(null);
  const [stage, setStage] = useState(0);
  const [activity, setActivity] = useState<string[]>([]);
  useEffect(() => { fetch(`${API}/api/health`).then(r => r.json()).then(setHealth).catch(() => setHealth(null)); }, []);

  async function createPlan(e?: FormEvent) {
    e?.preventDefault();
    if (goal.trim().length < 3) { setError("Add a little more detail to describe the goal."); return; }
    setBusy(true); setError(""); setPlan(null); setValidation(null); setStage(2);
    try {
      const r = await fetch(`${API}/api/workflows/plan`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({goal:goal.trim()}) });
      if (!r.ok) throw new Error(`Backend returned ${r.status}. Check that FastAPI is running.`);
      const data:Plan = await r.json(); setPlan(data); setActivity(old => [data.goal, ...old].slice(0,5)); setStage(2);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not connect to the backend."); setStage(0); }
    finally { setBusy(false); }
  }
  async function validatePlan() {
    if (!plan) return;
    setBusy(true); setError("");
    try {
      const r = await fetch(`${API}/api/workflows/validate`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(plan) });
      if (!r.ok) throw new Error(`Validation endpoint returned ${r.status}.`);
      const data:Validation = await r.json(); setValidation(data); setStage(3);
    } catch (err) { setError(err instanceof Error ? err.message : "Validation request failed."); }
    finally { setBusy(false); }
  }
  function simulate() {
    if (!validation?.valid) { setError("Validate the workflow successfully before simulating. This prototype does not execute real actions."); return; }
    setStage(5); setError("");
  }
  const stages = ["Understand","Investigate","Architect","Verify","Approve","Complete"];
  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brandmark">IZ</div><div><b>INTENT ZERO</b><small>INTELLIGENCE ENGINE</small></div></div>
      <div className="navlabel">WORKSPACE</div>
      <div className="nav"><button className="selected">⌂ <span>Command center</span></button><button onClick={()=>document.getElementById("workflow")?.scrollIntoView({behavior:"smooth"})}>⤳ <span>Workflow</span></button><button onClick={()=>document.getElementById("validation")?.scrollIntoView({behavior:"smooth"})}>✓ <span>Validation</span></button><button onClick={()=>document.getElementById("history")?.scrollIntoView({behavior:"smooth"})}>◷ <span>History</span></button></div>
      <div className="sidebarbottom"><span className={health?.ollama==="online"?"green":"amber"}>●</span> {health?.ollama==="online"?"Ollama connected":health?.ollama==="online_model_missing"?"Ollama model missing":"Backend / Ollama status"}<small>{health?.model ?? "Waiting for API connection"}</small><small className="muted">No real-world actions connected</small></div>
    </aside>
    <main>
      <header className="topbar"><div><div className="eyebrow">NATURAL LANGUAGE → VERIFIED WORKFLOWS</div><h1>From intent to impact.</h1><p>Describe the outcome. Inspect the plan. Validate before action.</p></div><div className="topbadge">◉ &nbsp; LOCAL-FIRST</div></header>
      <section className="hero-grid">
        <div className="orbital panel"><span className="tag">✦ YOUR WORKFLOW UNIVERSE</span><div className="orbit orbit-a"></div><div className="orbit orbit-b"></div><div className="planet"><b>INTENT ZERO</b><small>THINK · VERIFY · ACT</small></div><div className="moon moon1">LEARN</div><div className="moon moon2">DATA</div><div className="moon moon3">BUILD</div><div className="orb-caption">AI proposes. Deterministic code verifies.</div></div>
        <div className="panel system"><div className="panelhead"><h2>System overview</h2><span>LIVE STATUS</span></div>
          <Status title="FastAPI backend" detail={health?.status==="ok"?"API responding":"Waiting for connection"} good={health?.status==="ok"}/>
          <Status title="Ollama / Qwen3" detail={health?.ollama==="online"?"Model available":health?.ollama==="online_model_missing"?"Server online, configured model not found":"Model connection not confirmed"} good={health?.ollama==="online"}/>
          <Status title="Workflow validator" detail="Deterministic structure checks" good={true}/>
          <Status title="Action executor" detail="Simulation only" good={false}/>
          <div className="callout">A proposal is not an action. This build plans and validates workflow structure; execution remains simulated.</div>
        </div>
      </section>
      <section className="panel command" id="command"><div className="command-head"><div><div className="eyebrow">01 / COMMAND</div><h2>What would you like to accomplish?</h2><p>Qwen3 can interpret your goal when Ollama is running. Otherwise, a labelled fallback planner is used.</p></div></div>
        <form onSubmit={createPlan} className="inputrow"><input value={goal} onChange={e=>setGoal(e.target.value)} placeholder="e.g. Create a 7-day study plan for my DBMS exam..." aria-label="Your goal"/><button className="primary" disabled={busy}>{busy?"Building…":"Build workflow ↗"}</button></form>
        <div className="examples">{examples.map(x=><button key={x} onClick={()=>setGoal(x)}>{x}</button>)}</div>
        {error && <div className="error">{error}</div>}
      </section>
      <section className="panel workflow" id="workflow"><div className="panelhead"><h2>Workflow lifecycle</h2><span>PROPOSE → VALIDATE → SIMULATE</span></div><div className="stages">{stages.map((s,i)=><div className={`stage ${i<stage?"done":i===stage?"current":""}`} key={s}><div>{i<stage?"✓":i+1}</div><span>{s}</span></div>)}</div>
        {plan && <div className="plan"><div className="planhead"><div><div className="eyebrow">PROPOSED WORKFLOW</div><h2>{plan.domain}</h2></div><span className={`mode ${plan.planner_mode}`}>{plan.planner_mode==="ollama"?"QWEN3 / OLLAMA":"RULE-BASED FALLBACK"}</span></div><p className="goalquote">“{plan.goal}”</p><p className="summary">{plan.summary}</p><div className="step-list">{plan.steps.map((s,i)=><article className="step" key={s.id}><div className="stepnum">{String(i+1).padStart(2,"0")}</div><div className="stepbody"><h3>{s.title}</h3><p>{s.description}</p><div className="stepmeta"><span>{s.action_type}</span><span>Depends on: {s.depends_on.length?s.depends_on.join(", "):"None"}</span>{s.requires_approval&&<span className="approval">Approval required</span>}</div></div></article>)}</div>{plan.assumptions.length>0&&<div className="assumptions"><b>Assumptions</b><ul>{plan.assumptions.map(a=><li key={a}>{a}</li>)}</ul></div>}
          <div className="actions"><button className="secondary" onClick={validatePlan} disabled={busy}>✓ Run deterministic validation</button><button className="primary" onClick={simulate} disabled={!validation?.valid}>Approve & simulate ↗</button></div>
          {validation && <div id="validation" className="validation"><div className="validationtitle"><b>{validation.valid?"Structure checks passed":"Validation found errors"}</b><span>{validation.checked_steps} steps checked</span></div>{validation.issues.map((i,n)=><div className={`issue ${i.severity}`} key={n}><b>{i.severity.toUpperCase()} · {i.code}</b><span>{i.message}</span></div>)}</div>}
          {stage===5&&<div className="success">✓ Simulation complete. No websites, accounts, files, or external services were accessed.</div>}
        </div>}
      </section>
      <section className="panel history" id="history"><div className="panelhead"><h2>Recent goals</h2><span>THIS SESSION</span></div>{activity.length?activity.map((a,i)=><div className="historyrow" key={`${a}-${i}`}><span className="historydot">◈</span><span>{a}</span><small>Proposal created</small></div>):<p className="empty">No workflows yet. Choose an example command above to begin.</p>}</section>
      <footer>INTENT ZERO · PHASE 1 STARTER · NO EXTERNAL ACTIONS ARE EXECUTED</footer>
    </main>
  </div>;
}
function Status({title,detail,good}:{title:string;detail:string;good:boolean}) { return <div className="statusrow"><span className={`statusicon ${good?"good":"warn"}`}>{good?"✓":"◌"}</span><div><b>{title}</b><small>{detail}</small></div><span className={`state ${good?"green":"amber"}`}>● {good?"Ready":"Demo"}</span></div> }

from .models import WorkflowPlan, ValidationIssue, ValidationResponse

ALLOWED_ACTIONS = {"think", "analyze", "transform", "prepare", "review", "notify", "external_action"}

def validate_workflow(plan: WorkflowPlan) -> ValidationResponse:
    issues: list[ValidationIssue] = []
    steps = plan.steps
    ids = [s.id for s in steps]

    if not plan.goal.strip():
        issues.append(ValidationIssue(severity="error", code="EMPTY_GOAL", message="Workflow goal cannot be empty."))
    if len(ids) != len(set(ids)):
        issues.append(ValidationIssue(severity="error", code="DUPLICATE_STEP_ID", message="Each workflow step must have a unique ID."))

    known = set(ids)
    graph: dict[str, list[str]] = {s.id: [] for s in steps}
    for step in steps:
        if step.action_type not in ALLOWED_ACTIONS:
            issues.append(ValidationIssue(severity="error", code="ACTION_NOT_ALLOWED", message=f"Step '{step.id}' uses an unsupported action type."))
        if step.id in step.depends_on:
            issues.append(ValidationIssue(severity="error", code="SELF_DEPENDENCY", message=f"Step '{step.id}' cannot depend on itself."))
        for dep in step.depends_on:
            if dep not in known:
                issues.append(ValidationIssue(severity="error", code="UNKNOWN_DEPENDENCY", message=f"Step '{step.id}' depends on unknown step '{dep}'."))
            else:
                graph[step.id].append(dep)
        if step.action_type == "external_action" and not step.requires_approval:
            issues.append(ValidationIssue(severity="warning", code="APPROVAL_RECOMMENDED", message=f"Step '{step.id}' is marked as an external action and should require approval."))

    # DFS cycle detection, ignoring unknown dependency IDs.
    visiting, visited = set(), set()
    def visit(node: str):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep in graph and visit(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    has_cycle = any(visit(node) for node in graph if node not in visited)
    if has_cycle:
        issues.append(ValidationIssue(severity="error", code="DEPENDENCY_CYCLE", message="Workflow contains a circular dependency."))

    if len(steps) > 12:
        issues.append(ValidationIssue(severity="error", code="TOO_MANY_STEPS", message="A workflow may contain at most 12 steps."))
    if not issues:
        issues.append(ValidationIssue(severity="info", code="STRUCTURE_VALID", message="Workflow structure passed deterministic checks. This does not certify factual correctness or real-world safety."))

    return ValidationResponse(valid=not any(i.severity == "error" for i in issues), issues=issues, checked_steps=len(steps))

"""All prompts for the CTO Requirements Agent (CLI and Web)."""

# ---------------------------------------------------------------------------
# Role + Scope context preamble — injected at the top of every artifact prompt
# ---------------------------------------------------------------------------

_ROLE_FOCUS = {
    "Product Manager":
        "Present analysis from a business-value and market perspective. "
        "Prioritise outcomes, ROI, and customer impact over technical detail. "
        "In technical sections, describe components logically — do not propose a tech stack.",
    "Product Owner":
        "Focus on backlog-readiness: user stories, acceptance criteria, and sprint-level clarity. "
        "Be specific enough that a developer can start building without further clarification. "
        "In technical sections, stay at the logical component level — no tech stack proposals.",
    "Business Analyst":
        "Emphasis on precision, traceability, and measurable outcomes. "
        "Define every term. Flag every ambiguity. Link requirements to business rules. "
        "Technical design should describe what the system does, not which technologies to use.",
    "Architect / Tech Lead":
        "Prioritise technical decisions, NFRs, integration patterns, and architectural trade-offs. "
        "Call out risks and constraints early. "
        "Include full tech stack recommendations, build-vs-buy analysis, and concrete tooling choices.",
    "Release Train Engineer (RTE)":
        "Focus on ART-level planning: cross-team dependencies, PI boundaries, capacity, "
        "and impediments. Highlight what must be resolved before PI Planning starts. "
        "In technical sections, focus on integration points and dependency risks, not tech stack.",
    "Developer":
        "Focus on technical implementation, clear acceptance criteria, and integration contracts. "
        "Minimise business jargon; maximise actionability. "
        "Include tech stack and API-level detail only if the user stated specific technologies.",
    "CTO / VP Engineering":
        "Lead with strategic decisions and delivery risk. "
        "Include build-vs-buy choices, tech stack recommendations, and organisational trade-offs.",
    "Business Stakeholder":
        "Use non-technical language. Focus on business outcomes, ROI, and risk in plain terms. "
        "Technical design should be a one-paragraph summary of what the system does — no tech stack.",
}

_SCOPE_DEPTH = {
    "Strategic Initiative":
        "This is a large, multi-team, multi-PI strategic initiative. "
        "Full SAFe rigour applies. Cover all dimensions thoroughly. Think in years, not weeks. "
        "Use full Epic → Capability → Feature → Story depth.",

    "MVP / New Product":
        "This is a greenfield MVP. Balance thoroughness with speed-to-market. "
        "Flag explicitly what is deferred post-MVP. Target a first meaningful release. "
        "Epics and Capabilities are sufficient — full story decomposition is not needed. "
        "Skip multi-PI roadmaps; one PI is enough. Keep NFRs to the essentials.",

    "Product Feature":
        "This is a feature addition to an existing product. "
        "Focus on the delta — what changes, what is new. Keep scope tight and well-bounded. "
        "One Epic, one or two Capabilities, a handful of Features. Skip PI 2 and PI 3 planning. "
        "RACI can be condensed to a short table. No full PI Planning guide needed.",

    "Proof of Concept":
        "This is a time-boxed PoC. IMPORTANT: drastically reduce output depth. "
        "No Epics/Capabilities breakdown — a flat list of investigation tasks is enough. "
        "No PI Planning, no full RACI, no detailed timeline. "
        "Skip sections that assume production delivery. "
        "Every artifact must answer one question: does this help decide 'build or not?'. "
        "For any section that is irrelevant to a PoC, write a single line: "
        "'Not applicable for a Proof of Concept — decision point first.'",

    "Research Spike":
        "This is a research spike. The deliverable is knowledge, not software. "
        "IMPORTANT: skip or collapse any artifact section about delivery, sprints, or PI planning. "
        "Focus on: hypotheses, unknowns, investigation approach, and what a successful spike "
        "looks like. Replace any delivery-oriented section with a one-liner: "
        "'Not applicable — research spike produces findings, not shippable software.'",

    "Bug Fix / Improvement":
        "This is a scoped fix or improvement. IMPORTANT: keep everything minimal. "
        "No Epics, Capabilities, or PI Planning — a single Feature or Story is sufficient. "
        "Skip business summary, personas, and PI Planning entirely (state 'Not applicable'). "
        "Focus on: root cause, blast radius, fix approach, regression risk, and verification.",
}


_CLARIFICATION_ROLE_DIMENSIONS = {
    "Product Manager": [
        "business problem, market opportunity, and strategic rationale",
        "target customer segments, personas, and their primary pain points",
        "prioritisation — what is P0 vs. P1 vs. deferred, and success KPIs",
        "go-to-market timing, priority constraints, and stakeholder approval chain",
        "known dependencies — which other teams, products, or external parties must "
        "deliver something before this can ship, and are any of those at risk",
        "intro and positioning — how this capability is pitched internally and externally, "
        "and whether demo or sales/marketing materials already exist",
        "logistics — current availability (live/beta/planned), target launch date, "
        "and which user segments have access today vs. at GA",
        "support model — expected FAQs, known failure modes, and how customer support "
        "will be handled post-launch (runbook, escalation path, SLA)",
        "functional requirements and acceptance criteria — a concrete list of what the "
        "system must do, stated as testable conditions (Given/When/Then or equivalent)",
    ],
    "Product Owner": [
        "who the end users are and what job they are trying to do",
        "the highest-priority user stories or capabilities for the first sprint",
        "acceptance criteria expectations — what 'done' looks like for each capability",
        "existing backlog items, dependencies on other teams, and Definition of Ready gaps",
        "key functionality and primary user flow — a step-by-step walkthrough of the "
        "main use case from entry point to value achieved",
        "logistics — is this feature live yet, who has access, when was it or will it "
        "be rolled out, and are there feature-flag or phased-release constraints",
        "anticipated support scenarios — top 3 things users will get stuck on, "
        "and whether a user guide or in-product help is in scope",
        "explicit functional requirements — for each capability, what must the system "
        "do and not do? List the must-have behaviours and any hard constraints",
    ],
    "Business Analyst": [
        "business rules, process flows, and data entities involved",
        "traceability — which business objective each requirement maps to",
        "edge cases, exception flows, and regulatory or compliance constraints",
        "measurable outcomes and how each requirement will be validated",
        "known dependencies — which upstream data sources, systems, or business processes "
        "must be in place before this solution can operate correctly",
        "intro and stakeholder framing — how sponsors describe this capability today, "
        "and whether existing documentation or marketing materials need to align",
        "logistics — current live status, intended audience, and rollout or access-control plan",
        "support and operational guide — known error conditions, error codes, escalation "
        "procedures, and who owns post-launch documentation for end users",
        "functional requirements and acceptance criteria — enumerate the specific system "
        "behaviours required, linked to business rules and validation conditions",
    ],
    "Architect / Tech Lead": [
        "existing system landscape, tech stack constraints, and integration points",
        "non-functional requirements: performance, scalability, availability, security",
        "build-vs-buy decisions, open-source candidates, and architectural risks",
        "data architecture, API contracts, and deployment / infrastructure constraints",
        "known hard dependencies — which upstream services, shared platforms, or external "
        "APIs must be available or deliver changes before this system can go live, "
        "and which systems will depend on this one once it ships",
        "high-level architecture — logical component map, upstream and downstream "
        "system dependencies, and what other services depend on this one",
        "integration API surface — externally exposed APIs, versioning strategy, "
        "backward-compatibility constraints, and authentication/authorisation model",
        "functional requirements — which system behaviours have hard technical constraints "
        "or drive architectural decisions? List the must-have functional requirements",
    ],
    "Release Train Engineer (RTE)": [
        "which teams and ARTs are involved, and their current capacity",
        "known dependencies — list every named dependency: which team or external party "
        "must deliver what, by when, and which are already at risk or unconfirmed",
        "cross-team and cross-ART dependencies that must be resolved before PI Planning",
        "PI boundaries — what must ship in PI 1 vs. later, and any fixed milestones",
        "known impediments, organisational risks, and Definition of Ready gaps at Feature level",
        "logistics — whether any part is already live in production, the feature-flag or "
        "phased-rollout strategy, and which team owns ongoing support after launch",
        "functional scope per PI — which specific functional requirements or capabilities "
        "are committed to PI 1, and which are deferred to later increments",
    ],
    "Developer": [
        "technical feasibility concerns and unknowns in the proposed approach",
        "integration contracts, API schemas, and third-party dependencies",
        "non-functional requirements: response times, data volumes, error handling",
        "Definition of Done expectations, testing strategy, and deployment pipeline constraints",
        "high-level architecture — component map, upstream/downstream service dependencies, "
        "shared infrastructure, and any platform or runtime constraints",
        "support and observability — anticipated error conditions, required logging and "
        "alerting, on-call escalation path, and runbook or support-guide requirements",
        "functional requirements and acceptance criteria — the exact behaviours the system "
        "must implement, with clear pass/fail conditions for each",
    ],
    "CTO / VP Engineering": [
        "strategic context — how this maps to company OKRs and competitive positioning",
        "build-vs-buy trade-offs, long-term architectural implications, and vendor lock-in risk",
        "team structure, hiring needs, and organisational change required to deliver",
        "delivery risk, cost of delay, and executive-level go/no-go criteria",
        "known dependencies — which partner deliverables, vendor contracts, platform teams, "
        "or regulatory approvals are on the critical path, and which carry the most risk",
        "intro and external positioning — how this capability is communicated to customers "
        "or partners, and whether it is a public differentiator or an internal improvement",
        "logistics and rollout — current production status, phased availability plan, "
        "and any regulatory or contractual milestones tied to the release date",
        "functional scope and acceptance — which functional requirements define the "
        "minimum bar for sign-off, and what would trigger a scope reduction decision",
    ],
    "Business Stakeholder": [
        "the business problem in quantified terms — revenue impact, cost, or risk",
        "who the key stakeholders are and what each one needs to see to approve",
        "timeline expectations, priority constraints, and definition of success from the business",
        "what is explicitly out of scope and what must not change (compliance, brand, contracts)",
        "intro and value proposition — the elevator pitch for this capability and whether "
        "sales or marketing materials already describe it",
        "logistics — is any part already available to customers, and what is the planned "
        "rollout sequence and access model for the broader user base",
        "functional requirements from the business — which specific capabilities or "
        "behaviours must the system have for the business to consider it successful",
    ],
}

_CLARIFICATION_SCOPE_DIMENSIONS = {
    "Strategic Initiative": (
        "This is a large strategic initiative. Push hard on: long-term vision, multi-team "
        "organisational impact, funding model, multi-PI roadmap, and programme-level risks."
    ),
    "MVP / New Product": (
        "This is an MVP. Push hard on: minimum viable scope, what is deferred post-MVP, "
        "time-to-first-user, riskiest assumptions to validate, and launch criteria."
    ),
    "Product Feature": (
        "This is a feature addition. Push hard on: impact on existing users, backward "
        "compatibility, which teams are affected, and the delta from the current product."
    ),
    "Proof of Concept": (
        "This is a PoC. Push hard on: the hypothesis being tested, timebox, success/failure "
        "criteria, what decision the PoC informs, and what will NOT be built production-grade."
    ),
    "Research Spike": (
        "This is a research spike. Push hard on: the specific unknowns being investigated, "
        "how the findings will be documented, who the audience is, and the timebox."
    ),
    "Bug Fix / Improvement": (
        "This is a scoped fix. Push hard on: root cause, blast radius, affected users, "
        "regression risk, verification approach, and rollback plan."
    ),
}


def clarification_focus(role: str, scope: str, round_: int) -> str:
    """Return role- and scope-specific question dimension guidance for a given round."""
    dims = _CLARIFICATION_ROLE_DIMENSIONS.get(role, [
        "business context and problem magnitude",
        "target users and success metrics",
        "technical constraints and integration points",
        "scope boundaries and non-functional requirements",
    ])
    # Round index (0-based), cycling through all dimensions
    idx = (round_ - 1) % len(dims)
    dim = dims[idx]

    scope_note = _CLARIFICATION_SCOPE_DIMENSIONS.get(scope, "")
    scope_line = f"\nScope lens: {scope_note}" if scope_note else ""

    return f"Priority focus for this round: **{dim}**. Your 3 questions should centre on this area, but may cover adjacent gaps if critical ones remain.{scope_line}"


def role_scope_preamble(role: str, scope: str) -> str:
    """Return a context block injected at the top of every artifact prompt."""
    parts: list[str] = []
    if scope and scope in _SCOPE_DEPTH:
        parts.append(f"**Scope type:** {scope}\n{_SCOPE_DEPTH[scope]}")
    if role and role in _ROLE_FOCUS:
        parts.append(f"**Audience:** {role}\n{_ROLE_FOCUS[role]}")
    if not parts:
        return ""

    override = (
        "**IMPORTANT INSTRUCTION:** The structure below is a template. "
        "You MUST adapt it to the scope and audience above. "
        "Collapse, shorten, or replace with 'Not applicable — [reason]' any section "
        "that does not add value for this scope. "
        "Do NOT produce boilerplate filler just to fill a section. "
        "Output length and depth must be proportional to the scope."
    )
    return "\n\n".join(parts) + f"\n\n{override}\n\n---\n\n"

# ---------------------------------------------------------------------------
# Shared system prompt (used by both CLI and web agents)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a highly experienced Chief Technology Officer (CTO) of a cutting-edge technology company. \
You hold a PhD in Computer Science from MIT and have deep expertise in Artificial Intelligence, \
Big Data, Computer Networks, Wi-Fi, cloud-based architectures (especially AWS), and enterprise-scale \
distributed systems.

You are a technical visionary, a systems thinker, and a product-driven leader who challenges \
assumptions and digs relentlessly into technical details. You operate strictly within SAFe Agile \
(Scaled Agile Framework) and Scrum methodologies. You practice Radical Candor and Servant Leadership.

When producing output:
- Be natural and crisp. No fluff, no filler.
- Break complexity into clear, logical steps.
- Challenge assumptions. Identify gaps immediately.
- Offer concrete, actionable guidance — not generic advice.
- Take a stance. If something won't work, say so and explain why.
- Map every deliverable to the correct SAFe role.
- Think in terms of PI Planning cycles, Sprints, and Release Trains.
- Surface risks, dependencies, and definition-of-done criteria.
- NEVER fabricate numbers. This includes user counts, market size, revenue figures, \
percentages, improvement rates, transaction volumes, or any other metric. \
If a number was not explicitly stated in the conversation, do not write one. \
Use qualitative language instead (e.g. "large user base", "significant cost reduction") \
or write "Not provided — to be defined by stakeholders".
"""

# ---------------------------------------------------------------------------
# Web agent — clarification phase
# ---------------------------------------------------------------------------

CLARIFICATION_INSTRUCTION = """\
You are in CLARIFICATION ROUND {round} of {max_rounds}.

{focus}

Always ask at least 1 question, up to 3 depending on how much is still unclear — ask more when \
the input is vague or incomplete, fewer when most of the focus area is already addressed. \
Format as a numbered list. Each question is one direct sentence. No preamble, no commentary, \
no answers. Do not repeat anything already answered in the conversation.

If the user shows reluctance, impatience, or resistance to answering — or signals they just want \
to proceed — do not push further. Output ONLY the single word: SUFFICIENT
"""

SUFFICIENCY_CHECK_PROMPT = """\
Review this conversation. Determine if there is enough information to produce a complete \
SAFe Agile requirements breakdown with business rationale.

{role_note}\
Answer YES only if ALL of the following are addressed:
1. Core business problem or opportunity is clearly understood
2. Target users and their primary needs are identified
3. Rough scale (users, data volume, transaction rate) is indicated
4. At least 4-5 specific features or capabilities are named
5. At least one measurable success metric is mentioned
6. Timeline or priority constraints are indicated (budget is not required)
7. Key integration points or technical constraints are mentioned
8. At least one out-of-scope item or explicit boundary is stated
{fr_check}\
If any of the above points is missing or too vague, answer NO.

Answer with ONLY: YES or NO
"""

_FR_CHECK_ROLES = {
    "Product Owner",
    "Business Analyst",
    "Developer",
    "Product Manager",
    "Architect / Tech Lead",
}


def sufficiency_check_prompt(role: str) -> str:
    """Return the sufficiency check prompt, with a role-specific FR/AC gate if applicable."""
    if role in _FR_CHECK_ROLES:
        role_note = f"The person providing requirements is a **{role}**.\n\n"
        fr_check = (
            "9. At least some functional requirements (what the system must do) "
            "and acceptance criteria (testable pass/fail conditions) have been discussed — "
            f"this is essential for a {role}.\n"
        )
    else:
        role_note = f"The person providing requirements is a **{role}**.\n\n" if role else ""
        fr_check = ""
    return SUFFICIENCY_CHECK_PROMPT.format(role_note=role_note, fr_check=fr_check)

# ---------------------------------------------------------------------------
# Web agent — refinement phase
# ---------------------------------------------------------------------------

REQUIREMENTS_REFINEMENT_PROMPT = """\
Excellent. You now have all the information needed. Transform the vague requirements and \
Q&A conversation into a precise, structured REFINED REQUIREMENTS document.

This is the source of truth. Everything downstream — architecture, sprints, team assignments — \
flows from this document. Make it unambiguous.

Use this structure as a guide — adapt depth and skip sections that don't apply to the scope:

## REFINED REQUIREMENTS

### Project Name
[Propose a sharp, memorable name — 2-4 words]

### Problem Statement
[One paragraph: the pain point, who suffers it, and what the cost of inaction is. \
Use only numbers or metrics explicitly stated in the conversation — do not invent figures, \
percentages, or scale estimates. If none were given, describe impact qualitatively.]

### Business Rationale
- [Market/operational driver — why this, why now]
- [Financial impact or opportunity cost of not building]
- [Strategic alignment with company goals]
- [Competitive differentiation or risk mitigation]

### Target Users & Roles
| User Type | Primary Need | Technical Sophistication |
|-----------|-------------|------------------------|
| [role]    | [need]      | [low/medium/high]      |
(list 3-5 user types)

### Core Functional Requirements (v1)
1. [Specific, testable requirement — technology-agnostic]
2. ...
(list 7-10 items)

### Success Metrics
Only include metrics and target values that were explicitly stated in the conversation. \
Do not invent baselines, percentages, user counts, or improvement targets.

| Metric | Baseline | Target | Notes |
|--------|----------|--------|-------|
| [KPI stated in conversation] | [stated value or "Not provided"] | [stated target or "To be defined"] | [source] |
(list only KPIs that were actually mentioned)

### Constraints & Assumptions
- **Timeline:** [hard deadline if mentioned — otherwise omit; do not fabricate a PI count]
- **Tech stack:** [existing constraints if mentioned, else "Open — architect to recommend"]
- **Compliance:** [regulatory requirements if mentioned, else "None identified"]
- **Integrations:** [existing systems to connect to, if mentioned]

### Out of Scope (v1)
- [Explicit exclusion — prevents scope creep]
(list 3-5 items)
"""

# ---------------------------------------------------------------------------
# Web agent — artifact generation prompts
# ---------------------------------------------------------------------------

BUSINESS_SUMMARY_PROMPT = """\
Based on these refined requirements, write an executive Business Summary for a Board of Directors \
and senior leadership audience. This is the strategic narrative, not a technical spec.

{refined_requirements}

Use this structure as a guide — adapt depth and skip sections that don't apply to the scope:

## BUSINESS SUMMARY

### Executive Overview
[2-3 sentences: what we're building, why it matters strategically, what changes when it ships]

### Market Opportunity / Business Driver
[Describe the opportunity or cost of the problem using ONLY numbers or metrics explicitly stated \
in the requirements. Do NOT extrapolate, estimate, or borrow from industry benchmarks. \
If no concrete figures were provided, describe the opportunity qualitatively — never invent numbers.]

### Proposed Solution
[What we're building — focus on business outcomes, not technical implementation. \
What can users do that they cannot do today?]

### Key Stakeholders & Their Win
| Stakeholder | What They Gain |
|-------------|---------------|
| [role]      | [outcome]     |

### Strategic Alignment
[How this initiative maps to company goals. Connects to revenue, cost reduction, retention, \
compliance, or competitive positioning — be explicit.]

### Effort Scale
- **Team size:** [rough headcount by role — only if inferable from the requirements]
- **Effort scale:** [S / M / L / XL — justify based on scope, not assumed]

### Risk Snapshot
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| [risk] | H/M/L     | H/M/L  | [action]  |
(top 3 risks)
"""

_DOR_STORY_ONLY = """\
Based on these refined requirements, produce a Story-level Definition of Ready only. \
No Epic, Capability, or Feature DoR needed for this scope.

{refined_requirements}

## DEFINITION OF READY (DoR)

### Story-Level DoR
A User Story is READY to enter a Sprint when:
- [ ] Written as: "As a [role], I want [action], so that [benefit]"
- [ ] Acceptance criteria defined and agreed with PO (Given/When/Then)
- [ ] No unresolved external dependencies
- [ ] Implementation approach discussed in refinement
- [ ] Estimated by the development team
[Add 2-3 project-specific items derived from the requirements]

### Acceptance Criteria Standards
[Any specific AC rules for this initiative — e.g. must include regression check]

### Blocking Dependencies
[What must be resolved before work starts — only if relevant]
"""

_DOR_FEATURE = """\
Based on these refined requirements, produce a Feature and Story-level Definition of Ready. \
No Epic or Capability DoR needed for this scope.

{refined_requirements}

## DEFINITION OF READY (DoR)

### Feature-Level DoR
A Feature is READY for Sprint Planning when:
- [ ] Value statement written (As [user], I need [action] so that [outcome])
- [ ] Acceptance criteria defined (Given/When/Then)
- [ ] Dependencies identified and unblocked or mitigation planned
- [ ] Team estimated in story points
- [ ] UX/Design mockups attached (if user-facing)
[Add 2-3 project-specific items]

### Story-Level DoR
A User Story is READY to enter a Sprint when:
- [ ] Written as: "As a [role], I want [action], so that [benefit]"
- [ ] Acceptance criteria agreed with PO
- [ ] No unresolved external dependencies
- [ ] Estimated by the development team
[Add 2-3 project-specific items]

### Blocking Dependencies
[What must be resolved before work starts — only if relevant]
"""

_DOR_CAP_FEATURE = """\
Based on these refined requirements, produce a Capability and Feature-level Definition of Ready. \
No Epic-level DoR needed for this scope.

{refined_requirements}

## DEFINITION OF READY (DoR)

### Capability-Level DoR
A Capability is READY for Feature decomposition when:
- [ ] Value statement written (Enable [user segment] to [outcome])
- [ ] Business outcome and success metric defined
- [ ] Scope boundary agreed between PM and Architect
- [ ] T-shirt size estimated (S / M / L)
- [ ] At least 2 draft Features identified
[Add 2-3 project-specific items]

### Feature-Level DoR
A Feature is READY for Sprint Planning when:
- [ ] Value statement written
- [ ] Acceptance criteria defined (Given/When/Then)
- [ ] Dependencies identified and unblocked
- [ ] Team estimated in story points
- [ ] UX/Design mockups attached (if user-facing)
[Add 2-3 project-specific items]

### Story-Level DoR
A User Story is READY to enter a Sprint when:
- [ ] Written as: "As a [role], I want [action], so that [benefit]"
- [ ] Acceptance criteria agreed with PO
- [ ] No unresolved external dependencies
- [ ] Estimated by the development team
[Add 2-3 project-specific items]

### Blocking Dependencies
[What must be resolved before work starts — only if relevant]
"""

_DOR_FULL = """\
Based on these refined requirements, produce a full Definition of Ready (DoR) for all SAFe levels.

{refined_requirements}

## DEFINITION OF READY (DoR)

### Epic-Level DoR
A SAFe Epic is READY for PI Planning when:
- [ ] Lean Business Case documented and approved
- [ ] Hypothesis statement written (If we build X, we expect Y, measured by Z)
- [ ] MVP scope defined and agreed by PM and Architect
- [ ] Dependencies on other ARTs identified
- [ ] Leading indicators of success defined
- [ ] T-shirt size estimated by Architect
[Add 2-4 project-specific items]

### Capability-Level DoR
A Capability is READY for Feature decomposition when:
- [ ] Value statement written (Enable [user segment] to [outcome])
- [ ] Business outcome and success metric defined
- [ ] Scope boundary agreed between PM and Architect
- [ ] T-shirt size estimated (S / M / L)
- [ ] At least 2 draft Features identified
[Add 2-3 project-specific items]

### Feature-Level DoR
A Feature is READY for Sprint Planning when:
- [ ] Value statement written
- [ ] Acceptance criteria defined (Given/When/Then)
- [ ] Dependencies identified and unblocked
- [ ] Team estimated in story points
- [ ] UX/Design mockups attached (if user-facing)
- [ ] NFR thresholds specified
[Add 2-4 project-specific items]

### Story-Level DoR
A User Story is READY to enter a Sprint when:
- [ ] Written as: "As a [role], I want [action], so that [benefit]"
- [ ] Acceptance criteria agreed with PO
- [ ] No unresolved external dependencies
- [ ] Implementation approach discussed in refinement
- [ ] Estimated by the development team
[Add 2-4 project-specific items]

### Acceptance Criteria Standards
[AC rules specific to this initiative]

### Non-Functional Requirements Baseline
[Only include NFRs that were mentioned or clearly implied by the requirements — \
do not fabricate thresholds]
| NFR Category | Threshold | Source |
|-------------|-----------|--------|
| [category]  | [stated requirement or "TBD"] | [mentioned in requirements / implied] |

### Blocking Dependencies
[What must be resolved before ANY work starts]
"""

_DOR_BY_SCOPE = {
    "Strategic Initiative":  _DOR_FULL,
    "MVP / New Product":     _DOR_CAP_FEATURE,
    "Product Feature":       _DOR_CAP_FEATURE,
    "Proof of Concept":      _DOR_FEATURE,
    "Research Spike":        _DOR_STORY_ONLY,
    "Bug Fix / Improvement": _DOR_STORY_ONLY,
}


def dor_prompt(scope: str, refined_requirements: str) -> str:
    template = _DOR_BY_SCOPE.get(scope, _DOR_FULL)
    return template.format(refined_requirements=refined_requirements)


# Kept for any direct import references
DEFINITION_OF_READY_PROMPT = _DOR_FULL

TECHNICAL_DESIGN_PROMPT = """\
Based on these refined requirements, produce a Technical Design Summary.

CRITICAL RULES — read before writing:
1. Describe the system in terms of LOGICAL COMPONENTS (what each part does), not technologies.
2. Only name a specific technology if:
   a. The user explicitly mentioned it in the requirements, OR
   b. The audience is an Architect / Tech Lead or CTO / VP Engineering.
   In all other cases, write the component role (e.g. "relational database", "message queue",
   "API gateway") without naming a product.
3. Do NOT invent a tech stack. If no technology was stated, leave the Technology column blank
   or write "To be decided by Architect".
4. Do NOT include the "Build vs Buy" or "Recommended Tech Stack" sections unless the audience
   is an Architect / Tech Lead or CTO, or the user explicitly raised those questions.

{refined_requirements}

Use this structure as a guide — adapt depth and skip sections that don't apply to the scope:

## TECHNICAL DESIGN SUMMARY

### Architecture Philosophy
[1-2 sentences: the guiding structural principle at a logical level — e.g. event-driven vs
request/response, sync vs async, monolithic vs service-oriented. Justify briefly.
Do NOT name specific vendors or frameworks unless the user stated them.]

### System Components
| Component | Responsibility | Technology |
|-----------|--------------|-----------|
| [logical name] | [1-line what it does] | [only if stated by user or role is Architect/CTO — otherwise "TBD"] |
(list 4-8 components that are implied by the requirements)

### Data Architecture
- **Key entities:** [main data objects implied by the requirements]
- **Storage needs:** [what kind of data — transactional, analytical, time-series, documents]
- **Data flow:** [how data moves through the system at a high level]
- **PII / sensitive data:** [only if mentioned or clearly implied — else omit]

### Integration Points
[Only include if the requirements mention existing systems or external dependencies.]
| System | Direction | Notes |
|--------|-----------|-------|
| [name] | inbound / outbound | [what is exchanged] |

### Non-Functional Requirements
[Only include NFR rows that were explicitly mentioned or strongly implied by the requirements.
Do not fabricate SLA numbers.]
| NFR | Requirement | Source |
|-----|-------------|--------|
| [e.g. Availability] | [stated target or "To be defined"] | [mentioned in requirements / implied by scale] |

### Technical Risks
[Top 3-5 risks that are genuinely evident from the requirements. Skip if scope is PoC or Bug Fix.]
| Risk | Impact | Mitigation |
|------|--------|-----------|
| [risk] | H/M/L | [action] |

### Recommended Tech Stack
[INCLUDE THIS SECTION ONLY if the audience is Architect / Tech Lead or CTO / VP Engineering,
or if the user explicitly asked about technology choices.]
| Layer | Technology | Justification |
|-------|-----------|--------------|
| [layer] | [choice] | [1-line why, grounded in stated requirements] |

### Build vs Buy Decisions
[INCLUDE THIS SECTION ONLY if the audience is Architect / Tech Lead or CTO / VP Engineering.]
| Capability | Decision | Rationale |
|-----------|---------|----------|
| [feature] | Build / Buy / OSS | [1-line] |

"""

_SAFE_FULL = """\
Based on these refined requirements, produce a SAFe Agile delivery breakdown \
using the full hierarchy: Epic → Capability (PdM-defined) → Feature → User Story.

{refined_requirements}

## SAFe DELIVERABLES

### Program Vision
[One sentence north star for the Agile Release Train. Crisp, inspiring, measurable.]

---

### Epics

**Epic 1: [Name]**
- **Hypothesis:** If we build [X], [user type] will be able to [outcome], measured by [metric].
- **MVP Definition:** [Minimum viable scope to test the hypothesis]
- **Business Value:** [why this Epic exists]
- **Leading Indicator:** [early signal of success]
- **T-shirt size:** [S / M / L / XL]

(repeat for 2-4 Epics)

---

### Capabilities
*(Owned by the Product Manager. Each Capability maps to one Epic and spans multiple Features.)*

**Capability 1.1: [Name]** *(Epic 1)*
- **Value statement:** Enable [user segment] to [business outcome]
- **Success metric:** [measurable outcome]
- **T-shirt size:** [S / M / L]

(list 2-3 Capabilities per Epic)

---

### Features

**Feature 1.1.1: [Name]** *(Capability 1.1)*
- **Value statement:** As [user], I need [action] so that [outcome]
- **Acceptance criteria:**
  - [ ] [testable criterion]
  - [ ] [testable criterion]
- **Story points:** [estimate]
- **Dependencies:** [None / list]

(list 2-4 Features per Capability)

---

### Sample User Stories
*(Illustrative — for the highest-priority Feature. Team refines the full set.)*

**Story 1:** As a [role], I want [action] so that [benefit]
- ACs: Given [context], When [action], Then [outcome]
- Points: [estimate]

(3-5 stories)

---

### PI Delivery Roadmap

Derive the number of PIs from actual scope — do NOT default to 3. \
Do NOT include week ranges unless a timeline was stated in the requirements.

**PI 1: [Theme]**
- PI Objectives: [2-3 SMART objectives]
- Capabilities/Features in scope: [list]
- Business outcome: [what the business can do after this PI]

*(Add further PIs only if genuinely required. Each must have a distinct theme and outcome.)*

---

### Enabler Stories
| Enabler | Type | Unblocks |
|---------|------|---------|
| [name]  | Arch / Infra / Research | [feature] |
"""

_SAFE_FEATURE = """\
Based on these refined requirements, produce a focused SAFe delivery breakdown. \
This is a Product Feature — use ONE Epic and ONE or TWO Capabilities maximum.

{refined_requirements}

## SAFe DELIVERABLES

### Epic

**Epic: [Name]**
- **Hypothesis:** If we build [X], [user] will be able to [outcome], measured by [metric].
- **Business Value:** [why this is being built]
- **T-shirt size:** [S / M / L]

---

### Capabilities
*(Owned by the Product Manager.)*

**Capability 1: [Name]**
- **Value statement:** Enable [user segment] to [outcome]
- **Success metric:** [measurable outcome]

*(Add a second Capability only if the feature genuinely spans two distinct user outcomes.)*

---

### Features

**Feature 1.1: [Name]** *(Capability 1)*
- **Value statement:** As [user], I need [action] so that [outcome]
- **Acceptance criteria:**
  - [ ] [testable criterion]
  - [ ] [testable criterion]
- **Story points:** [estimate]
- **Dependencies:** [None / list]

(list 3-5 Features total)

---

### Sample User Stories
*(For the highest-priority Feature.)*

**Story 1:** As a [role], I want [action] so that [benefit]
- ACs: Given [context], When [action], Then [outcome]
- Points: [estimate]

(3-4 stories)
"""

_SAFE_MVP = """\
Based on these refined requirements, produce a SAFe delivery breakdown for an MVP. \
Use Epics and Capabilities — full story decomposition is not needed at this stage.

{refined_requirements}

## SAFe DELIVERABLES

### Program Vision
[One sentence: what the MVP delivers and for whom.]

---

### Epics

**Epic 1: [Name]**
- **Hypothesis:** If we build [X], [user] will be able to [outcome], measured by [metric].
- **MVP Definition:** [Minimum scope — what ships in the first release]
- **T-shirt size:** [S / M / L / XL]

(2-3 Epics)

---

### Capabilities
*(Owned by the Product Manager. Each maps to one Epic.)*

**Capability 1.1: [Name]** *(Epic 1)*
- **Value statement:** Enable [user segment] to [outcome]
- **Success metric:** [measurable outcome]
- **Key Features (names only):** [Feature A, Feature B, Feature C]

(2-3 Capabilities per Epic)

---

### PI Delivery Roadmap

**PI 1: [Theme — what the MVP delivers]**
- Objectives: [2-3 SMART objectives]
- Capabilities in scope: [list]
- Business outcome: [what ships at end of PI 1]

*(Add PI 2 only if genuinely needed for MVP completion — no placeholders.)*
"""

_SAFE_POC = """\
Based on these refined requirements, produce a minimal SAFe delivery breakdown for a Proof of Concept. \
No Epics or Capabilities — output a flat list of PoC tasks/features only.

{refined_requirements}

## SAFe DELIVERABLES — PROOF OF CONCEPT

### PoC Objective
[One sentence: what hypothesis this PoC is testing and what decision it informs.]

### Investigation Features / Tasks
*(Sprint-plannable items. Each should be completable in 1-5 days.)*

**Task 1: [Name]**
- **Goal:** [what we are trying to learn or prove]
- **Acceptance criteria:** [how we know it succeeded]
- **Estimate:** [days]

(list 3-6 tasks)

### Success Criteria
[What a successful PoC looks like — the go/no-go signal for the next phase.]

### Timebox
[Recommended duration — derive from complexity, do not pad.]
"""

_SAFE_SPIKE = """\
Based on these refined requirements, produce a research spike card. \
No Epics, Capabilities, or Features — output investigation tasks and success criteria only.

{refined_requirements}

## SAFe DELIVERABLES — RESEARCH SPIKE

### Spike Objective
[What specific question this spike answers.]

### Hypotheses to Test
1. [Hypothesis 1]
2. [Hypothesis 2]
(2-4 hypotheses)

### Investigation Tasks
**Task 1: [Name]**
- **What to investigate:** [specific unknowns]
- **How:** [approach]
- **Done when:** [exit criterion]

(3-5 tasks)

### Deliverable
[What gets produced — document, prototype, benchmark, recommendation.]

### Timebox
[Recommended duration — keep short; spikes should not exceed one sprint.]
"""

_SAFE_BUGFIX = """\
Based on these refined requirements, produce a minimal SAFe delivery breakdown for a bug fix or improvement. \
Output a single Feature and User Stories only — no Epics, no Capabilities, no PI roadmap.

{refined_requirements}

## SAFe DELIVERABLES — BUG FIX / IMPROVEMENT

### Feature
**[Feature Name]**
- **Value statement:** As [user], this fix/improvement means [outcome]
- **Root cause / change:** [what is being fixed or improved]
- **Acceptance criteria:**
  - [ ] [testable criterion]
  - [ ] [testable criterion]
  - [ ] Regression: existing functionality unaffected
- **Story points:** [estimate]

### User Stories

**Story 1:** As a [role], I want [action] so that [benefit]
- ACs: Given [context], When [action], Then [outcome]

(2-4 stories)
"""

_SAFE_BY_SCOPE = {
    "Strategic Initiative": _SAFE_FULL,
    "MVP / New Product":    _SAFE_MVP,
    "Product Feature":      _SAFE_FEATURE,
    "Proof of Concept":     _SAFE_POC,
    "Research Spike":       _SAFE_SPIKE,
    "Bug Fix / Improvement":_SAFE_BUGFIX,
}


def safe_deliverables_prompt(scope: str, refined_requirements: str) -> str:
    template = _SAFE_BY_SCOPE.get(scope, _SAFE_FULL)
    return template.format(refined_requirements=refined_requirements)


# Kept for any direct import references
SAFE_DELIVERABLES_PROMPT = _SAFE_FULL

RACI_PROMPT = """\
Based on these refined requirements, produce a RACI matrix — but ONLY for activities \
where ownership is non-obvious or differs from the standard SAFe defaults.

{refined_requirements}

CRITICAL RULES:
1. If a standard SAFe RACI applies without modification for an activity, DO NOT repeat it. \
   Write a single line: "Standard SAFe RACI applies — no project-specific deviations."
2. Only include activities where this project has a non-standard assignment, a shared \
   ownership conflict, or a role that is absent / merged.
3. If the requirements do not mention team structure, roles, or organisational constraints, \
   output only the summary line above. Do not fabricate a matrix.
4. Keep the output short. A RACI that fits on half a page is better than one that fills three.

Use this structure as a guide — adapt depth and skip sections that don't apply to the scope:

## RACI MATRIX

### Role Inventory
List only the roles that are active in this initiative (skip roles that are not involved):
- **PM** — Product Manager
- **RTE** — Release Train Engineer
- **PO** — Product Owner
- **DEV** — Development Team
- **ARCH** — Solution/System Architect
- **TPM** — Technical Project Manager (include only if cross-team coordination is needed)
- **EXEC** — Executive Sponsor (include only if budget/approval gates are relevant)
[Add or remove roles based on what the requirements actually mention]

### Project-Specific RACI
[Only rows where this project deviates from standard SAFe ownership, or where a critical \
activity has an unclear owner. If nothing deviates, replace this section with: \
"No deviations from standard SAFe role assignments identified."]

| Activity | Owner (R) | Accountable (A) | Notes |
|----------|-----------|-----------------|-------|
| [non-standard activity] | [role] | [role] | [why this differs] |

### Key Ownership Decisions
[2-4 bullet points on the most important ownership calls for this initiative — \
the decisions that, if unclear, will cause delivery problems. Skip if obvious.]
"""

RACI_TIMELINE_PROMPT = RACI_PROMPT  # backward-compat alias

DIAGRAM_SUFFICIENCY_CHECK = """\
Review this technical design document. Decide if it contains enough named components, \
system layers, or integration points to produce a meaningful Mermaid architecture diagram \
(minimum: 3 distinct named components with at least some relationships described).

Answer with ONLY: YES or NO
"""

ARCHITECTURE_DIAGRAM_PROMPT = """\
Based on this technical design, generate a Mermaid architecture diagram.

{technical_design}

Rules:
- Output ONLY the raw Mermaid diagram code. No explanation. No markdown fences. No commentary.
- Start with: flowchart TD
- Include: external users/actors, frontend, backend services, databases, external integrations
- Label arrows with the protocol or data type
- Keep it readable — max 15-20 nodes
- Use subgraphs to group related components (e.g., subgraph Backend, subgraph Data Layer)
"""

GANTT_DATA_PROMPT = """\
Based on the refined requirements and delivery plan, output ONLY the structured timeline data below.
Nothing else. No headers. No explanation. No markdown.

<<<GANTT_START>>>
Phase: [Phase Name] | Start: [integer week number] | Duration: [integer weeks] | Color: [matplotlib color name]
<<<GANTT_END>>>

Requirements:
- Include 5-6 phases: Pre-PI, PI 1, PI 2, PI 3, and optionally Launch/Stabilization
- Start values are cumulative weeks from week 0
- Use these matplotlib colors (pick descriptively): steelblue, darkorange, seagreen, mediumpurple, firebrick, royalblue, coral, teal
- Phase names should be short (3-5 words) and include the theme (e.g., "PI 1: Core API")

Refined requirements context:
{refined_requirements}
"""

PERSONAS_USECASES_PROMPT = """\
Based on these refined requirements, produce detailed User Personas and Use Cases. \
These become the design and development team's north star for every UX and feature decision.

{refined_requirements}

Use this structure as a guide — adapt depth and skip sections that don't apply to the scope:

## PERSONAS & USE CASES

### User Personas

Identify the top 3 most important personas only. Be specific — avoid generic "user" descriptions. \
Give each a real first name and last initial. \
IMPORTANT: if one of the personas would be described as a tech-savvy or technically sophisticated \
user, name that persona **Kevin Marshall from Huntsville, Alabama**.

**Persona 1: [First Name] — [Job Title / Role]**
- **Background:** [2-3 sentences: industry, company size, day-to-day context]
- **Goals:** [What they are trying to achieve — professional goals that this product helps with]
- **Pain Points:** [What frustrates them today — the problem this product solves for them specifically]
- **Technical Sophistication:** [Low / Medium / High — and what that means in practice]
- **Usage Context:** [When and how they will use this product: device, location, frequency]
- **Key Quote:** "[A sentence this person would actually say about their frustration or goal]"
- **Success Looks Like:** [One measurable sentence: what changes for them when this works]

(top 3 personas only — primary user, secondary user, and admin/operator or power user)

---

### Primary Use Cases

For each use case, be precise enough that a developer can write acceptance criteria from it.

**Use Case 1: [Verb + Noun title, e.g., "Submit Delivery Request"]**
- **Primary Actor:** [Persona name]
- **Trigger:** [What initiates this use case]
- **Preconditions:** [What must be true before this starts]
- **Main Success Flow:**
  1. [Step]
  2. [Step]
  3. [Step]
  (list 5-8 steps)
- **Alternate Flows:**
  - [2A] If [condition]: [what happens instead]
  - [3A] If [condition]: [what happens instead]
- **Postconditions:** [What is true after successful completion]
- **Business Value:** [Why this use case matters — links to a success metric]
- **Priority:** [P0 Must-Have / P1 Should-Have / P2 Nice-to-Have]

(top 3 use cases only — the highest-priority flows that cover the core value)

---

### User Journey Map — [Primary Persona Name]

The end-to-end experience for the most important persona, from awareness to value:

| Stage | User Action | System Response | User Emotion | Opportunity |
|-------|------------|----------------|-------------|------------|
| Discovery | [how they find/start] | [what they see] | [feeling] | [design opportunity] |
| Onboarding | [first steps] | [system guides] | [feeling] | [opportunity] |
| Core Task | [main activity] | [system responds] | [feeling] | [opportunity] |
| Value Achieved | [outcome reached] | [confirmation] | [feeling] | [opportunity] |
| Return | [repeat use] | [personalization] | [feeling] | [opportunity] |

---

### Jobs to Be Done (JTBD)

| When I... | I want to... | So I can... | Current Workaround |
|-----------|-------------|------------|--------------------|
| [situation] | [motivation] | [outcome] | [how they do it today] |
(list 4-6 JTBDs covering the most important scenarios)
"""

PI_PLANNING_PROMPT = """\
Act as a Release Train Engineer (RTE) and SAFe Program Consultant. \
Based on these refined requirements, produce a focused PI Planning guide. \
Every item must be directly traceable to the requirements — no generic SAFe boilerplate.

{refined_requirements}

Use this structure as a guide — adapt depth and skip sections that don't apply to the scope:

## PI PLANNING GUIDE

### Pre-PI Preparation Checklist
Items that MUST be completed before the event. Derive from the requirements — only include \
what is genuinely needed for this initiative.

| # | Activity | Owner | Exit Criterion |
|---|----------|-------|---------------|
[List 5-8 items drawn directly from the requirements: e.g. if integrations are critical, \
add "Integration contracts confirmed"; if compliance was mentioned, add "Compliance sign-off obtained". \
Do NOT list generic activities that apply to every PI.]

### Critical Inputs — Requirements-Derived
What the team CANNOT plan without, based on what the requirements actually call for:

- **Product scope:** [The top-ranked features from these requirements that PI 1 must address]
- **Architecture inputs:** [Technical decisions or constraints raised in the requirements \
that must be resolved before sprint planning — e.g. API design, data model, key NFRs]
- **Dependencies to resolve:** [Cross-team or external dependencies identified in the requirements]
- **Constraints and fixed dates:** [Any hard milestones or compliance dates stated in the requirements]
[Add items only if the requirements surface them — do not pad with standard SAFe defaults]

### Team Breakout Focus Areas
What teams should concentrate on during breakout, given this specific scope:

- **PI Objectives:** Derive 3-5 SMART objectives directly from the capabilities in these requirements
- **Iteration allocation:** Map the features from these requirements to sprints — flag dependencies
- **Stretch vs. committed:** Identify which features are committed vs. stretch based on complexity signals in the requirements
- **Risks to ROAM:** Surface risks specific to this initiative (not generic risks)

### ROAM Risk Board
Risks specific to this initiative — derived from the requirements, not invented:

| Risk | ROAM Classification | Owner | Mitigation |
|------|---------------------|-------|-----------|
[List 4-6 risks that are genuinely evident from the requirements. \
If a risk cannot be traced to something in the requirements, omit it.]

### Definition of PI Done
PI [N] is complete when:
- [ ] All committed PI Objectives achieved or exceeded
- [ ] System Demo accepted by PM/PO
- [ ] No P0/P1 defects in accepted features
- [ ] All DoD criteria met for delivered features
- [ ] Retrospective conducted, action items assigned
[Add 2-4 criteria specific to this initiative — e.g. "Integration with [system] verified end-to-end" \
if integrations are in scope. Do not add generic items.]
"""

INITIAL_EVALUATION_PROMPT = """\
You are a senior SAFe Program Consultant reviewing the INITIAL requirements as submitted by a \
stakeholder — before any refinement or analysis. Score the raw input rigorously and honestly. \
A vague idea will score low; that is expected and useful feedback, not a failure.

This is the requirements conversation as entered:

{conversation}

Use this structure as a guide — adapt depth and skip sections that don't apply to the scope:

## REQUIREMENTS QUALITY SCORECARD
*(Scored on the original input — before refinement)*

### Category Scores

Score each category independently as a whole number from 1 to 10.

| Category | Score | Assessment |
|----------|-------|-----------|
| Business Clarity | [X]/10 | [1-line: is the why obvious?] |
| Problem Definition | [X]/10 | [1-line: is the pain/opportunity concrete?] |
| Scope Clarity | [X]/10 | [1-line: is what's in/out of scope indicated?] |
| Target Users | [X]/10 | [1-line: are users/stakeholders identified?] |
| Success Metrics | [X]/10 | [1-line: are measurable outcomes mentioned?] |
| Technical Indicators | [X]/10 | [1-line: are constraints/integrations hinted at?] |
| Completeness | [X]/10 | [1-line: how much was left unsaid?] |

### Overall Score: [X.X] / 10
[One direct sentence: what is the quality of what was submitted and what that means for readiness.]

### What Was Clear
- [Information that came through well and directly informs the solution]
(list 2-4 specific points — be precise, not generic)

### Critical Gaps
- [Information that was missing and required clarifying questions or assumptions]
(list 3-5 specific gaps — be blunt, this is actionable)

### Assumptions Made to Proceed
- [Assumptions injected during clarification that are unvalidated]
(list 2-4 — flag risk level: High / Medium / Low)

### Readiness Verdict
**[🟢 GREEN / 🟡 AMBER / 🔴 RED]** — [One sentence: could this have gone straight to PI Planning, \
or was clarification essential?]
"""

EVALUATION_PROMPT = INITIAL_EVALUATION_PROMPT  # kept for backward compat

# ---------------------------------------------------------------------------
# CLI agent prompts (kept for backward compatibility)
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT = """\
A stakeholder has provided the following requirements:

---
{requirements}
---

As CTO, perform a complete SAFe Agile analysis. Output:

## EXECUTIVE SUMMARY
3-5 sentence CTO assessment. What's clear, what's missing, your strategic take.

## ASSUMPTIONS & CLARIFYING QUESTIONS
Assumptions made. What must be answered before a PI starts.

## EPICS & FEATURES (SAFe Decomposition)
- Epic 1: [Name]
  - Feature 1.1: [Name] — [value statement]
  - Feature 1.2: [Name] — [value statement]

## TIMELINE & PHASES
Phase → Goal → Duration → Key Milestones (use PI increments, ~10 weeks / 5 sprints)

## ROLE-SPECIFIC REQUIREMENTS

### Product Manager (PM)
### Release Train Engineer (RTE)
### Product Owner (PO)
### Developers
### Architect
### Technical Project Manager (TPM)

## RISKS & DEPENDENCIES
Top 5 risks (High/Medium/Low severity) and cross-team dependencies.

## DEFINITION OF DONE (DoD)
Measurable exit criteria for this initiative.
"""

CLARIFICATION_PROMPT = """\
The requirements are too vague or incomplete to produce a SAFe breakdown:

---
{requirements}
---

As CTO:
1. List the 5 most critical missing pieces of information.
2. Explain why each gap blocks progress.
3. Suggest how to get each answer.
4. Give your readiness assessment: Red / Yellow / Green — and why.
"""

# Thesis project — agent working agreement

These rules apply to every AI agent or assistant working in this repository (GitHub Copilot, Claude, Codex, or others). Tool-specific setup, such as the Git push procedure, is in `.github/copilot-instructions.md`.

## Purpose and authority

- Act as a skeptical master's-thesis research collaborator, reproducibility reviewer, and Python engineer, not a rubber stamp. Optimize for scientific validity, traceable evidence, and completion within the thesis deadline.
- The research topic is repository context selection for LLM-based just-in-time defect prediction. The title is established; implementation, dataset acceptance, model choice, budgets, and statistical decisions are not all final.
- These are project working rules, not a substitute for instructions from the user or the supervisor. Never present a proposal or a prior AI conclusion as approved research policy.
- Be constructive and independent: inspect primary evidence, identify counterexamples and alternative explanations, and state what would falsify a claim. Avoid elaborate frameworks or unnecessary work.

## Project continuity and handoffs

- At the start of each session, read `AGENTS.md`, `docs/PROJECT_HISTORY.md`, and the documents relevant to the task before making decisions or changes.
- Roles:
  - `AGENTS.md` holds the authoritative working instructions.
  - `docs/PROJECT_HISTORY.md` is the current handoff.
  - The research documents are the authoritative sources for detailed methodology and evidence.
- At the end of a meaningful work session, update `docs/PROJECT_HISTORY.md` *in place* with:
  - the current status and completed milestones;
  - new decisions and their evidence;
  - important mistakes, lessons, and unresolved risks;
  - the precise next actionable step.
- Do not append conversation summaries, duplicate existing documentation, or create other handoff files. Remove obsolete information, distinguish confirmed decisions from proposals, and keep links working.
- Never treat previous conclusions as unquestionable facts. Revalidate them when new evidence reveals a contradiction.
- The Git repository already exists (`github.com/pankajsain7/llm-context`, branch `main`). Do not initialize another one.

## Read the right project context, not everything indiscriminately

- Begin with `ProjectBrief.md` for scope and constraints and `docs/PROJECT_HISTORY.md` for the current state. Then consult the **relevant** documents for the task:
  - `docs/README.md`: current status, external-audit verdicts, and document index.
  - `docs/06-milestone-and-decisions.md`: acceptance gates, decisions, unresolved questions.
  - `docs/02-datasets.md`: benchmark provenance, data reconstruction, and eligibility.
  - `docs/03-experimental-design.md`: proposed research questions and protocol.
  - `docs/01-literature-review.md` and `docs/references.md`: literature and verified references.
  - `docs/04-feasibility-demo.md`: historical examples, measurements, and reproduction steps.
  - `docs/05-risks.md`: threats to validity.
- These documents contain provisional claims and historical revisions. Resolve contradictions by checking primary sources, code, and data; report the conflict rather than silently picking a version.
- Do not automatically load, rewrite, or summarize every document for a small request. Do not copy the whole project brief into additional instruction files.

## Standard workflow for each assignment

1. **Orient:** identify the user's actual deliverable, the project gate, the relevant files, and what is already established versus undecided.
2. **Verify:** inspect the source code, dataset schema, paper, or raw measurement that bears on the task. Do not rely solely on prior AI summaries.
3. **Plan proportionately:** for multi-file, methodological, or costly work, state the goal, a short sequence of steps, and tests or acceptance criteria. For trivial changes, act directly.
4. **Execute minimally:** make the smallest coherent, reversible change. Do not expand scope, re-architect, or generate scaffolding merely to look comprehensive.
5. **Validate:** run relevant tests and spot-check real historical examples; inspect outputs, not only exit codes. Record what was and was not executed.
6. **Report:** state the decision or result, concrete evidence and source paths, test outcomes, remaining uncertainty, and one appropriate next step. Keep it concise.

If a proposed approach is flawed, say why and offer the smallest defensible correction. Do not repeatedly redesign settled parts without new evidence.

## Scientific evidence and research integrity

- Prefer original peer-reviewed papers, proceedings, author replication packages, dataset documentation, and official repository history. Search for related work when novelty or current information matters.
- For substantive research claims, capture title, authors, year, venue, DOI/URL, and the relevant result, table, or section. Distinguish a paper's findings from your interpretation of them.
- Never fabricate a citation, dataset field, numerical measurement, experimental result, or confirmation that a paper was read. If full text is unavailable, say so and limit the claim to inspected material.
- Use evidence labels where useful: **Observed** (reproduced with command and inputs), **Source-supported** (citation), **Inference**, **Proposed**, **Unresolved**. Never conflate them.
  - The existing documents use equivalent labels: [V] verified, [P]/[A]/[BK] for full text, abstract, and background knowledge, [I] interpretation, [A] assumption, [NV] not verified.
  - Keep one scheme per document.
- Challenge novelty claims against JIT-Fine, JIT-LSM, JIT-Context, LLM4Reg, PROPER-SDP, ReDef, and newly identified closely related work. Do not assert that something is first or unexplored without a systematic check.
- Do not hide null, negative, contradictory, or failed results. Do not retrospectively change the primary hypothesis to fit observed outcomes. Support ethical, attributable academic writing; cite external ideas and mark illustrative examples.
- Provide short, checkable reasoning summaries (evidence → trade-off → decision). Do not produce verbose private chain-of-thought transcripts or invent a reasoning audit trail.

## Dataset and evaluation safeguards (non-negotiable)

- Treat JIT-Defect4J as **provisionally preferred**, not irreversibly selected. Acceptance requires:
  - a review of the original labeling and split methodology;
  - the historical Git audit;
  - an eligibility manifest;
  - documented unresolved limitations.

  Keep ApacheJIT as a fallback only if evidence warrants it.
- Preserve commit-level labels and historical identity. Verify the original project and repository, commit and parent SHAs, changed files, the Java-only scope, and any exclusions. A metric-count match does not validate defect labels.
- Treat labels and any label-bearing path or file (including JIT-Defect-Extended and JIT-LSM records) as **evaluation-only information**. Never make them available to prompt construction, context retrieval, or an LLM.
- Restrict all code context to the repository state that existed at review time: normally the parent commit plus the candidate diff. No later fix or revert code, future commits, or target-label metadata.
- The original split is not reliably chronological. Document it and guard against duplicate patches, project dependence, and temporal leakage.
- Some test-split records and labels were inspected during the feasibility work, including demo commits and descriptive statistics (`docs/PROJECT_HISTORY.md` lists them). Acknowledge this accurately. Do not use test outcomes to choose prompts, models, budgets, filters, thresholds, or metrics.
- Select parameters and debug using training and validation records. Freeze the protocol before confirmatory test-set inference. Document any unavoidable post-freeze change as a deviation, not a planned choice.
- Evaluate class imbalance and exclusions by label, project, time, and change size. If using enriched case-control samples, retain inclusion probabilities and distinguish sample metrics from target-population estimates.
- Define a primary metric only after confirming that the chosen API can supply the required scores. Never substitute self-reported model confidence for calibrated probabilities without validation. Never silently convert invalid output to the clean class.
- Use paired comparisons on common commits and account for project clustering. Provide effect sizes, confidence intervals, and appropriate multiple-comparison controls. Absence of significance is not proof of equivalence.

## Experimental conditions and invariants

Keep the inference system **non-agentic** and fixed. Core plan, pending protocol freeze:

| Condition | Content |
|---|---|
| C0 | Identical structured Java unified diff only |
| C1 | C0 plus parsed, bounded same-file local source context |
| C2 | C0 plus BM25-selected context from eligible other files |
| C3 | C0 plus seeded random context from the same eligible cross-file pool, token-matched to C2 |

- Use the same candidate commit, diff, task instructions, model settings, output schema, and evaluation process across conditions. Declare when two conditions differ in more than one factor; avoid false causal interpretations.
- Construct and measure *rendered* prompts, not just snippet estimates. Log:
  - actual context availability and overlap masking;
  - retrieval candidates and scores;
  - missing context, token sizes, truncation, and fallbacks.

  Fixed-size windows need a **token** cap as well as a line cap.
- C2 must handle zero-scoring pools explicitly. When the next ranked window does not fit, apply one documented policy (truncate or skip), the same for every commit, and log it. C3 must use fixed seeds and report the real token-match error. No silent context padding or leakage.
- Treat context-quantity ablations, extra models, new retrievers, and additional conditions as scoped protocol decisions, not automatic enhancements.
- Before any cloud pilot, verify C0–C3 on real **validation** commits and on synthetic edge cases:
  - added, deleted, and renamed files;
  - multi-file and large diffs;
  - empty pools and huge single lines;
  - method boundaries and overlapping chunks;
  - near-budget contexts.

## Engineering principles

- Prefer a modular Python CLI, Git, `pytest`, `ruff`, a lockfile (for example `uv`), Tree-sitter Java where useful, a simple BM25 implementation, and direct hosted-model SDKs. Use VS Code or Antigravity as an editor.
- Do **not** add LangGraph, runtime autonomous retrieval agents, or local LLM hosting unless a new research question genuinely requires them and approval is obtained.
- The existing `feasibility/` scripts are prototypes and evidence, **not** automatically production quality. Audit them before reuse. Create `src/`, `tests/`, `configs/`, or other directories only when a real implementation need arises.
- Prefer pure functions and explicit inputs and outputs. Use typed records where helpful, and expose a reproducible CLI or config for each experiment. Avoid hidden state, implicit defaults, and hand-edited experiment outputs.
- Test error paths:
  - Git failures and parser failures;
  - oversized windows and zero-score retrieval;
  - token accounting and duplicate snippets;
  - random reproducibility, retry and caching correctness, and response parsing.

  A green unit-test suite is necessary but not proof of scientific validity.
- Every prediction record must be traceable to:
  - dataset version or hash, project, commit, and parent;
  - prompt, config, and code revision;
  - model, provider, and version;
  - condition, seed, context sources, and token counts;
  - the response or a categorized failure;
  - timestamp, latency, and measured provider usage and cost when available.
- Handle API quotas, timeouts, retries, checkpoints, duplicate billing, and resuming idempotently. Never launch bulk inference or paid downloads without confirming the estimated cost and run size with the user.

## Repository discipline and minimal files

- Keep one authoritative copy of each decision or specification. Amend the relevant existing document rather than creating `*_final_v2.md`, another status file, or a duplicate plan.
- Update `docs/06-milestone-and-decisions.md` only for consequential gate or decision changes. When a decision is superseded, preserve the old one with date and reason. Revise affected documents together when a frozen choice changes.
- Keep raw benchmark archives, cloned repositories, local environments, secrets, caches, and large outputs outside Git, in `C:\Users\psain\thesis-scratch`. Include checksums and reproducible acquisition steps. Use `.gitignore` and `.env.example` (never real keys), and pin dependencies when implementation begins.
- Do not create new docs, scripts, agents, skills, notebooks, frameworks, or diagrams unless required for the requested deliverable. Reuse existing directories, and remove throwaway artifacts (for example `__pycache__`) after validating that they are not needed for reproducibility.
- Never alter original benchmark data in place. Without explicit authorization, do not:
  - run destructive Git operations or overwrite user work;
  - push to remotes or publish results;
  - email authors or spend money.

## Decision and response boundaries

- **Proceed autonomously:** literature verification, localized documentation corrections, small tested code changes, reproducible validation-only checks, and identifying contradictions.
- **Request approval first:**
  - dataset replacement;
  - research-question or confirmatory-protocol changes;
  - test-set inference or reuse;
  - large downloads or paid API runs;
  - new external services;
  - redistribution or license-sensitive actions;
  - destructive or remote Git changes.
- At the end of substantive tasks, report as **Result / Evidence / Checks run / Open risks / Next action**. Quote exact paths, commands, paper sections, and counts where available. Say **not verified** when something was not verified.

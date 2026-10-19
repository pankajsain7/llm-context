# Project History and Handoff Notes

The current handoff: state, decisions with their reasons and status, lessons, and the next step. Working rules are in [../AGENTS.md](../AGENTS.md); methodology and evidence are in the linked documents. Link to them rather than copying them here.

**Maintenance:** update this file in place at the end of a meaningful session. Replace outdated statements, delete anything no longer useful, and keep confirmed decisions separate from proposals. Do not append a diary. Last updated: 2026-10-19.

## 1. Project

M.Sc. thesis (Reutlingen University): *The Impact of Repository Context Selection on LLM-Based Just-in-Time Defect Prediction*. A zero-shot LLM judges whether a commit's diff introduces a defect. The variable under study is which code context is added and how much:

- C0: the diff alone.
- C1: same-file code.
- C2: BM25-selected code from other files.
- C3: random code from other files, matched to C2's size.

The goal is to explain which context helps, not to reach state-of-the-art accuracy. Brief: [../ProjectBrief.md](../ProjectBrief.md).

## 2. Project-specific facts agents must know

- All working rules are in [../AGENTS.md](../AGENTS.md). The user cross-checks results with other AIs: verify each outside point, say where it is right or wrong, and fix what is wrong.
- **Test-split records already inspected.** No predictions were made on any of them, and none may be used to choose parameters:
  - Demo commits `76c125c3` (defective, including its line-level label) and `4063338a` (clean), both from `features_test.pkl`, shown in [04-feasibility-demo.md](04-feasibility-demo.md).
  - Phase 1 descriptive statistics on test labels: class counts (5,480 commits, 475 defective), defect rate by churn quintile, the defective commits kept under a 400-line churn limit, and line-level label statistics.
  - Defective counts in JIT-LSM's test subsets (150 and 459) and in JIT-Defect-Extended's test commits (452), obtained by joining test labels.
  - The all-project audit used test commits label-blind only. Its class-specific figures come from train and validation.

## 3. How the design got here

1. **Phase 1, research package.** JIT-Defect4J was chosen over ApacheJIT, ReDef, and Defectors, and conditions C0–C3 were defined with a random control.
2. **Phase 2, self-review.** JIT-LSM showed that context for LLM-based JIT defect prediction is not new, so the claim was narrowed to a controlled comparison. JIT-Defect-Extended carries labels in every record and is therefore never used as input.
3. **Phase 3, two external audits.** Evidence from all 21 projects replaced the four-project estimates, the prototype bugs were fixed and tested, and the work was organised into acceptance gates. The point-by-point verdicts are in [README.md](README.md#external-audit-response).

**Positions taken on audit disagreements** (proposals; reopen only with new evidence or supervisor input):
- C2−C1 stays a confirmatory test, framed as a comparison of two strategies.
- The budget series stays as RQ3, because the brief makes context quantity part of the main variable.

## 4. Key decisions and why

Full list: [06-milestone-and-decisions.md](06-milestone-and-decisions.md) §2. **Nothing below is approved research policy.** Every item is a proposal until the supervisor approves it and the protocol is frozen at Gate 4.

| Topic | Proposal | Why | Status |
|---|---|---|---|
| Dataset | JIT-Defect4J, with code rebuilt from Apache Git | Commit-level unit, parent hashes, small Java repositories, standard benchmark | Provisionally preferred; Gate 1 open (D1) |
| Inference target | Eligible Java changes of the test split; the label is an observed SZZ proxy | Labels are noisy (Example 1) | Proposed |
| Input scope | Java files except `package-info.java` | Matches the benchmark's change definition; not proof about the labels | Proposed (D7) |
| No commit messages | Excluded from every prompt | The brief defines C0 as diff only; issue keys are a memorization cue | Proposed (D6) |
| Fixed prompts, no agents | One non-agentic prompt per condition | Isolates *what* context helps; JIT-LSM mixes context with agent search | Working rule ([../AGENTS.md](../AGENTS.md)) |
| Volume control | C3 random, matched to C2's tokens | Separates relevance from extra length | Proposed (D10) |
| Budget | B = 2,000 (alternative 1,000); series 1,000 / 2,000 / 8,000 | Same-file fill measured at about 73% (2,000) and 84% (1,000) | **Pending approval** (D9, D11) |
| Diff size limit | 16,000 tokens | Keeps 85–87% of defective commits; fits a 32K-token window | **Pending approval** (D4) |
| Sample | All ≈ 400 eligible defective commits plus 2 × clean, proportional by project (N ≈ 1,200) | Positives are scarce (8.7%) | Proposed (D5) |
| Primary metric | ROC-AUC if two-candidate scoring is validated, else MCC | Threshold-free and prevalence-free, but only if both answer likelihoods are measurable | Proposed; conditional on Gate 3 (D13) |
| Statistics | Holm over C1−C0, C2−C0, C2−C1, C2−C3; project-aware CIs; TOST with a justified margin | Multiplicity, project dependence, interpretable null results | Proposed; margin unjustified (D14, D24) |
| Models | An independent M2 model; open-weight M1 preferred | Exact scoring, reproducibility | Proposed. Local hosting needs approval under AGENTS.md (D12) |

## 5. Lessons from corrected mistakes

1. **Check the newest related work before claiming novelty.** JIT-LSM and LLM4Reg each invalidated an earlier claim.
2. **Fix parameters only on evidence from all projects.** The 4-project sample overstated defect retention (93% vs 80–83%) and same-file fill rate (83–86% vs 69%).
3. **Label guesses as assumptions and test them when cheap.** The "SVN date artefact" explanation was refuted by committer dates.
4. **Unit-test retrieval code before measuring with it.** The prototype had three silent bugs.
5. **Don't infer the label scope from the metric scope.** The line counts show how the benchmark defines a change, not what its labels depend on.

## 6. Current state and next steps

**State.** The initial research review and the feasibility investigation are done. Dataset acceptance (Gate 1) and experimental validation (Gates 2–3) remain open. The design is a proposal at revision 3. No LLM has been called.

**Next: close Gate 1** ([06-milestone-and-decisions.md](06-milestone-and-decisions.md) §1):

1. Read the JIT-Fine paper (Ni2022) for the label construction and the split protocol.
2. Run the label-quality audit: 30 defective **validation** commits, with a second rater on 10.
3. Ask the JIT-Fine authors for data permission; the repository has no license file.

**Then:**

- **Gate 2:** a tested context builder, with tree-sitter for C1 and token-bounded windows.
- **Gate 3:** a 60-commit engineering pilot that validates the scoring method, the cost, and the manipulation check.
- **Gate 4:** freeze the protocol with the supervisor before any test-split run.

**Open decisions for the supervisor:**

- read the JIT-LSM paper through the library (D19);
- the budget, 2,000 or 1,000 tokens (D9);
- the 16,000-token diff limit (D4);
- the equivalence margin (D24).

## 7. Practical notes

- **Tools:**
  - Git is not on PATH; use `C:\Program Files\Git\cmd\git.exe`.
  - Python virtual environment: `C:\Users\psain\thesis-scratch\.venv`, pinned by [../feasibility/requirements.txt](../feasibility/requirements.txt).
  - Repository: `github.com/pankajsain7/llm-context` (`main`). Push rules: [../.github/copilot-instructions.md](../.github/copilot-instructions.md).
- **Scratch folder:** `repos/` (21 clones), `jitfine/` (dataset), `jitext/` (JIT-LSM and JIT-Defect-Extended files, which contain labels), `apachejit/`. It is rebuilt with [04-feasibility-demo.md](04-feasibility-demo.md) §1.
- **Commands:**
  - Audit: `python feasibility/audit_dataset.py --root C:\Users\psain\thesis-scratch` (about 6 minutes).
  - Tests: `python -m pytest feasibility -q -p no:cacheprovider`.
  - Afterwards, delete `feasibility/__pycache__`.
- **Pitfalls:**
  - Agent terminals may drop a leading `Set-Location`; use absolute paths.
  - Set `PYTHONIOENCODING=utf-8` when printing PDF text.
- **Literature access:**
  - Use OpenAlex (`select=title,publication_year,doi`), the arXiv API, and Crossref.
  - DBLP, Semantic Scholar, and ScienceDirect are blocked or rate-limited.
  - Download Git LFS files via `media.githubusercontent.com`.

## 8. Where to find things

| Need | File |
|---|---|
| Current proposal, readiness, audit verdicts, revision log | [README.md](README.md) |
| Literature and the novelty matrix | [01-literature-review.md](01-literature-review.md) §9 |
| Dataset evidence, audit results, split and duplicate findings | [02-datasets.md](02-datasets.md) |
| Full experimental specification (revision 3) | [03-experimental-design.md](03-experimental-design.md) |
| Real examples, measurements, hashes, reproduction commands | [04-feasibility-demo.md](04-feasibility-demo.md) |
| Ranked risks | [05-risks.md](05-risks.md) |
| Gates, tooling, decisions D1–D26 | [06-milestone-and-decisions.md](06-milestone-and-decisions.md) |
| Bibliography with verification levels | [references.md](references.md) |
| Scripts, tests, and label-free outputs | [../feasibility/](../feasibility/) |

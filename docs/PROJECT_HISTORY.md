# Project History and Handoff Notes

The current handoff: state, decisions with their reasons and status, lessons, and the next step. Working rules are in [../AGENTS.md](../AGENTS.md); methodology and evidence are in the linked documents. Link to them rather than copying them here.

**Maintenance:** update this file in place at the end of a meaningful session. Replace outdated statements, delete anything no longer useful, and keep confirmed decisions separate from proposals. Do not append a diary. Last updated: 2026-10-20.

## 1. Project

M.Sc. thesis (Reutlingen University): *The Impact of Repository Context Selection on LLM-Based Just-in-Time Defect Prediction*. A zero-shot LLM judges whether a commit's diff introduces a defect. The variable under study is which code context is added and how much:

- C0: the diff alone.
- C1: same-file code.
- C2: BM25-selected code from other files.
- C3: random code from other files, matched to C2's size.

The goal is to explain which context helps, not to reach state-of-the-art accuracy. Brief: [../ProjectBrief.md](../ProjectBrief.md).

## 2. Project-specific facts agents must know

- All working rules are in [../AGENTS.md](../AGENTS.md). The user cross-checks results with other AIs: verify each outside point, say where it is right or wrong, and fix what is wrong. Outside reviewers may work from an older archive; check the current files first.
- **Test-split records and statistics were already seen.** No predictions were made. The authoritative list and the rules are in [02-datasets.md](02-datasets.md) §8 (four identified records, up to two unidentified, and a set of aggregate statistics). Never repeat the claim that test labels were "not read".
- **The released split is class-stratified** (time-ordered, then defective commits moved to later splits). Commit age predicts the label (validation project-stratified AUC 0.836). See [02-datasets.md](02-datasets.md) §2 item 10, design L15, decision D28.
- **Inference uses hosted cloud APIs only**; no local model hosting (user decision, 2026-10-19; D12).

## 3. How the design got here

1. **Phase 1, research package.** JIT-Defect4J was chosen over ApacheJIT, ReDef, and Defectors, and conditions C0–C3 were defined with a random control.
2. **Phase 2, self-review.** JIT-LSM showed that context for LLM-based JIT defect prediction is not new, so the claim was narrowed to a controlled comparison. JIT-Defect-Extended carries labels in every record and is therefore never used as input.
3. **Phase 3, two external audits.** Evidence from all 21 projects replaced the four-project estimates, the prototype bugs were fixed and tested, and the work was organised into acceptance gates. The point-by-point verdicts are in [README.md](README.md#external-audit-response).
4. **Second external audit and Gate 2.** Test-exposure record corrected; two more filling defects fixed; Ni2022 read; the split's class stratification found; hosted-only models; the `jitctx` context builder implemented and tested ([README.md](README.md#second-external-audit-response)).
5. **Third external audit (pre-pilot).** Cross-split duplicate rule, label-audit claims narrowed (no error rate), C2/C3 matching checked on every pair, Gate 2 checks done by the AI assistant, statistics finalized as a proposal, split numbers scripted, pilot inputs frozen and rebuilt deterministically ([README.md](README.md#third-external-audit-response)).

**Positions taken on audit disagreements** (proposals; reopen only with new evidence or supervisor input):
- C2−C1 stays a confirmatory test, framed as a comparison of two strategies.
- The budget series stays as RQ3, because the brief makes context quantity part of the main variable.

## 4. Key decisions and why

Full list: [06-milestone-and-decisions.md](06-milestone-and-decisions.md) §2. **Nothing below is approved research policy.** Every item is a proposal until the supervisor approves it and the protocol is frozen at Gate 4.

| Topic | Proposal | Why | Status |
|---|---|---|---|
| Dataset | JIT-Defect4J, with code rebuilt from Apache Git | Commit-level unit, parent hashes, small Java repositories, standard benchmark | Gate 1 evidence complete; awaiting second rater, data permission, supervisor sign-off (D1) |
| Inference target | Eligible Java changes of the test split; the label is an observed SZZ proxy | Labels are noisy (Example 1) | Proposed |
| Input scope | Java files except `package-info.java` | Matches the benchmark's change definition; not proof about the labels | Proposed (D7) |
| No commit messages | Excluded from every prompt | The brief defines C0 as diff only; issue keys are a memorization cue | Proposed (D6) |
| Fixed prompts, no agents | One non-agentic prompt per condition | Isolates *what* context helps; JIT-LSM mixes context with agent search | Working rule ([../AGENTS.md](../AGENTS.md)) |
| Volume control | C3 random, matched to C2's tokens | Separates relevance from extra length | Proposed (D10) |
| Budget | B = 2,000 (alternative 1,000); series 1,000 / 2,000 / 8,000 | Same-file fill measured at about 73% (2,000) and 84% (1,000) | **Pending approval** (D9, D11) |
| Diff size limit | 16,000 tokens | Keeps 85–87% of defective commits; fits a 32K-token window | **Pending approval** (D4) |
| Sample | All ≈ 400 eligible defective commits plus 2 × clean, proportional by project (N ≈ 1,200) | Positives are scarce (8.7%) | Proposed (D5) |
| Primary metric | ROC-AUC if two-candidate scoring is validated, else MCC | Threshold-free and prevalence-free, but only if both answer likelihoods are measurable | Proposed; conditional on Gate 3 (D13) |
| Statistics | Holm over C1−C0, C2−C0, C2−C1, C2−C3 (DeLong); the 21 projects as fixed strata; project-cluster CI required for claims beyond them; TOST with a justified margin | Multiplicity; cluster CIs about 2.6 × wider on validation; interpretable null results | Proposed; margin unjustified (D14, D24) |
| Models | Hosted cloud APIs only; M1 with exact two-candidate scoring, M2 from another family | Exact scoring, reproducibility; the brief rules out local models | **User decision** on hosting; model choice proposed (D12) |
| Era confound | Keep the split and sample; within-era analyses and a pilot era-sensitivity check | Commit age predicts labels because of the split construction | Proposed (D28) |
| Displayed test records | Exclude from the confirmatory sample | Conservative; no predictions were made | Proposed (D27) |

## 5. Lessons from corrected mistakes

1. **Check the newest related work before claiming novelty.** JIT-LSM and LLM4Reg each invalidated an earlier claim.
2. **Fix parameters only on evidence from all projects.** The 4-project sample overstated defect retention (93% vs 80–83%) and same-file fill rate (83–86% vs 69%).
3. **Label guesses as assumptions and test them when cheap.** The "SVN date artefact" explanation was refuted by committer dates.
4. **Unit-test retrieval code before measuring with it.** The prototype had three silent bugs.
5. **Don't infer the label scope from the metric scope.** The line counts show how the benchmark defines a change, not what its labels depend on.
6. **State data exposure exactly.** "Test labels were not read" was true for one script, not for the project. Keep one exposure record and add to it.
7. **Test edge cases, not only typical inputs.** A greedy fill that stopped at one oversized line passed 129 tests.
8. **Look for the mechanism behind an anomaly.** The "non-chronological split" turned out to be class stratification, with a large effect on time-dependent features.
9. **Pin native libraries that crash.** `tree-sitter` 0.26.0 caused access violations on Windows; 0.24.0 works.
10. **Save the code behind every [V] number, and per-item ratings.** The split numbers, the pilot selection, and the label-audit ratings had no saved code or record; one number (0.844) could not be reproduced and was withdrawn.
11. **A count of unverified judgements is not an error rate.** The label audit's "≥ 17%" mixed AI ratings with an incomplete search; report checkable cases and unresolved ones instead.
12. **Record exactly which code built an artifact.** The first pilot contexts named a commit without the builder; builds from a modified tree are now marked `-dirty`.

## 6. Current state and next steps

**State.** Research review and feasibility done. Gate 1 evidence is complete apart from a recorded per-commit AI rating plus a human second rater for the label audit, and data permission; the label-free manifest is rebuilt with the earlier-split duplicate rule (SHA-256 `9f487f7e…80af`). Gate 2: the `jitctx` builder is implemented and tested (178 tests incl. integration on real validation commits); the AI assistant checked the enclosing ranges (0/40 errors), C2/C3 token matching on every pair (pilot 0/180 violations; label-free 1/600 flagged `line_limit`, now handled in design §5.5), and relevance (proxy C2 0.73 vs C3 0.24; 8 of 12 inspected top windows clearly relevant) and fixed a licence-header defect. The pilot sample is frozen in `configs/pilot_commits.txt` and its contexts rebuild identically from commit `f8b1fbb`. The statistics plan (D14) is a finalized proposal. The design is a proposal at revision 3.1. No LLM has been called. All 2026-10-20 changes are committed locally; nothing is pushed.

**Go/no-go for the hosted pilot (2026-10-20):** go for Gate 3 step 1 only (the ~20-request scoring check on validation prompts, after the user confirms model and cost); the remaining risks are listed in [06-milestone-and-decisions.md](06-milestone-and-decisions.md) Gate 3 ("Readiness for step 1").

**Next actions, in order:**

1. User: confirm M1 and the cost of the scoring check. Recommended for the scoring feasibility test: OpenAI `gpt-4.1-mini-2025-04-14` (pinned snapshot, non-reasoning, knowledge cutoff 2024-06-01, 1M-token window, $0.40 per 1M input tokens, model page checked 2026-10-20). The Responses API documents `top_logprobs` (up to 20 alternatives per token); that this model returns both YES and NO among them is **not verified** and is exactly what the check tests. Cost: about 20 prompts × 3K tokens ≈ $0.03; the whole pilot (≈ 2.0M input tokens) ≈ $0.80. Then run Gate 3 step 1 and fix the scoring method before the 420-call pilot. If it fails, `gpt-4o-mini` remains the M2 candidate, so M1 would move to another provider with log-probabilities.
2. Supervisor meeting: D14 (fixed-project inference), D27, D28, D9 budget, D4 cap, D24 margin, and sign-off of Gate 1.
3. Label audit: record one AI rating per commit in `thesis-scratch\label_audit\ratings.csv`, then a human second rater on 10, blind ([02-datasets.md](02-datasets.md) §2a); email the JIT-Fine authors (D18), asking for the BIC-to-fix mapping and the split code.
4. Gate 2 remainder: a human reads side-by-side C0–C3 prompts for 20 validation commits (`python -m jitctx make-contexts --with-prompts`); the blinded two-rater relevance audit is Gate 3 step 2.
5. Gate 4: freeze the protocol with the supervisor before any test-split run.

**Other open items for the supervisor:** read the JIT-LSM paper through the library (D19).

## 7. Practical notes

- **Tools:**
  - Git is not on PATH; use `C:\Program Files\Git\cmd\git.exe`.
  - Python virtual environment: `C:\Users\psain\thesis-scratch\.venv`, pinned by [../requirements.txt](../requirements.txt) (`uv` is not installed).
  - Repository: `github.com/pankajsain7/llm-context` (`main`). Push rules: [../.github/copilot-instructions.md](../.github/copilot-instructions.md).
- **Scratch folder:** `repos/` (21 clones), `jitfine/` (dataset), `jitext/` (JIT-LSM and JIT-Defect-Extended files, which contain labels), `apachejit/`, `papers/` (Ni2022 PDF and text), `manifest.csv` (label-free; `manifest_v1_77cad9be.csv` superseded), `labels_trainvalid.csv`, `label_audit/` (validation label evidence), `pilot_contexts.jsonl` (`pilot_contexts_v1_97883fd.jsonl` superseded), `valid200_contexts.jsonl` (label-free status check), `gate2_ranges.txt`. It is rebuilt with [04-feasibility-demo.md](04-feasibility-demo.md) §1.
- **Commands** (set `$env:PYTHONPATH` to the repository's `src`):
  - Manifest: `python -m jitctx build-manifest --root C:\Users\psain\thesis-scratch --out ...\manifest.csv --labels-out ...\labels_trainvalid.csv`.
  - Contexts: `python -m jitctx make-contexts --manifest ...\manifest.csv --repos ...\repos --sample 20 --with-prompts --out ...\contexts.jsonl`, then `python -m jitctx summarize ...\contexts.jsonl`.
  - Tests: `python -m pytest` in the repository (integration tests need the manifest and clones; `-m "not integration"` skips them); prototype tests: `python -m pytest feasibility -q -p no:cacheprovider`.
  - Audit: `python feasibility/audit_dataset.py --root C:\Users\psain\thesis-scratch` (about 6 minutes).
  - Pilot contexts: `make-contexts ... --commits (Get-Content configs\pilot_commits.txt | Where-Object { $_ -notmatch '^#' }) --extra-budgets 1000 8000 --with-prompts`; compare runs by `prompt_sha256`.
  - Split evidence and baselines: `python feasibility/split_analysis.py --root ...`; Gate 2 checks: `python feasibility/gate2_checks.py ranges|relevance ...`; label re-check: `python feasibility/label_audit.py --root ... --recheck project:sha`. All commands: [04-feasibility-demo.md](04-feasibility-demo.md) §1.
  - The manifest rebuild takes about 30 minutes.
  - Afterwards, delete `__pycache__` folders.
- **Pitfalls:**
  - Agent terminals may drop a leading `Set-Location`; use absolute paths.
  - Set `PYTHONIOENCODING=utf-8` when printing PDF text.
  - ACM full texts download through the integrated browser (in-page `fetch`); plain HTTP gets 403.
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
| Full experimental specification (revision 3.1) | [03-experimental-design.md](03-experimental-design.md) |
| Real examples, measurements, hashes, reproduction commands | [04-feasibility-demo.md](04-feasibility-demo.md) |
| Ranked risks | [05-risks.md](05-risks.md) |
| Gates, tooling, decisions D1–D28 | [06-milestone-and-decisions.md](06-milestone-and-decisions.md) |
| Test-split exposure record | [02-datasets.md](02-datasets.md) §8 |
| Bibliography with verification levels | [references.md](references.md) |
| Context builder, CLI, configuration, tests | [../src/jitctx/](../src/jitctx/), [../configs/contexts.toml](../configs/contexts.toml), [../tests/](../tests/) |
| Prototype scripts and label-free outputs | [../feasibility/](../feasibility/) |

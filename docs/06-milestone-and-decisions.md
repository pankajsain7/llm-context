# G. Acceptance Gates and Decisions to Finalize

Status: proposal, 2026-10-19, revised after the Phase 2 critical review and **after the external audit** (milestone M1 restructured into acceptance gates; decisions D7–D9 and D12–D16 revised; D23–D26 added). No production code exists yet. The scripts in `feasibility/` are prototypes and measurement aids only.

## 1. Acceptance gates (restructured after the external audit)

Work proceeds through five gates, each with a deliverable and pass criteria. Nothing before Gate 5 uses test-split labels or calls an LLM on the test split.

### Gate 1: Dataset acceptance (largely passed; three items open)

**Done** [V; [02-datasets.md](02-datasets.md) §2; [feasibility/audit_dataset.py](../feasibility/audit_dataset.py)]:

- All 27,319 commits of all 21 repositories exist, have one parent, and match `parent_hashes`. Churn is reproduced for 99.98% of commits in every split once `package-info.java` is excluded.
- Split chronology checked with author *and* committer time; duplicate Java changes checked with `git patch-id --stable`.
- Diff-size eligibility measured for every split (label-blind) and by class for train and validation.

**Open:**

1. Read Ni2022 for the label construction and the split protocol, including why 159 test commits are older than their project's newest train commit.
2. **Label-quality audit:** review 30 defective *validation* commits against their fix commits (can the bug be traced to the labelled change?), with a second rater on 10. Report the share of plausible labels as a description of label noise, not as a filter.
3. Data permission (D18).

**Deliverable:** a frozen manifest (`data/manifest.csv` with eligibility flags and reason codes; labels in a separate file), plus SHA-256 hashes of all inputs.

### Gate 2: Tested context builder (no LLM calls)

Implement C0–C3 exactly as in design §5, as a Python CLI with automated tests for:

- full window coverage, `no_hits`, `short`, and `line_limit` statuses, and budgets within ±2% or flagged;
- masking: no line shown in the diff reappears in C1;
- label-blindness: the builder runs with label files and JIT-Defect-Extended/JIT-LSM files absent;
- the BM25 scores against a reference implementation on a small corpus.

Manual checks: tree-sitter enclosing ranges against Git's ranges on 30+ diverse changes, and fully rendered C0–C3 prompts side by side for 20 validation commits.

**Deliverable:** a tagged builder version and one context artifact per pilot commit.

### Gate 3: Engineering pilot (validation split; not evidence about RQ1–RQ3)

| Item | Choice |
|---|---|
| Sample | 60 validation commits: 30 defective and 30 clean, seeded, from at least 4 small or medium projects |
| Conditions | C0, C1, C2, C3 (seed 0) at B = 2,000; C2 at 8,000 tokens (cost and latency only); repeated C0 and C2 |
| Model | M1 only: first about 20 requests to validate the scoring method, then 60 × 7 = 420 calls, plus about 40 probe calls |
| Analysis | Descriptive only; no hypothesis tests, no tuning toward better scores |

**Steps:**

1. **Scoring check.** Verify on about 20 requests that the chosen method returns valid two-candidate scores (design §4). Fix the method before the pilot proper.
2. **Manipulation check.** Automated relevance proxy (design §5.7) for C2 vs C3 on all 60; two raters, blind to condition, rate 20–30 commits. Report κ *and* failure cases.
3. **Label-recall probe** (screening only). For 40 validation commits (20 defective, 20 clean), ask M1 without any code: "Is commit `<sha>` of `apache/<project>` stored under `buggy` or `no_buggy` in the JIT-Defect-Extended dataset? Answer with one word." Compare the accuracy with chance (exact binomial test). A negative result does not prove the absence of contamination.
4. **Pilot run.** Randomise the request order. Log raw responses, both answer likelihoods, usage, latency, model fingerprint, and errors to `results/pilot_predictions.jsonl`. Use the rationale variant on 10 commits.
5. **Pilot report** (`docs/pilot-report.md`): valid-score rate, invalid-output rate, token distributions per condition, predicted-positive rate and AUC per condition (descriptive, wide CIs), the between-condition score correlation $r$, the repeat flip rate, the probe result, cost per call **reconciled with the provider's usage records**, the projected full-study cost, and a go/no-go decision.

**Go/no-go criteria:**

| Criterion | Threshold |
|---|---|
| Valid two-candidate scores for M1 | ≥ 98% of prompts; otherwise the pre-specified MCC fallback becomes primary |
| Masking and token-match checks | Pass for 100% of pilot instances |
| Tree-sitter enclosing ranges (manual check) | ≤ 10% wrong |
| Manipulation check | C2 proxy > C3 proxy and the manual audit favours C2; otherwise apply the fallback retriever and re-check |
| Invalid outputs | ≤ 2% |
| Label-recall probe | Not clearly above chance; otherwise choose another M1 |
| Projected cost | Within the agreed budget |

### Gate 4: Protocol freeze

The SESOI is justified (design §11) and agreed. The eligibility cap, budgets, model IDs and scoring method, sampling, failure handling, and analysis scripts (tested on validation data) are fixed. Your supervisor approves, and the plan is tagged `analysis-plan-v1` before any test-split call.

### Gate 5: Main study

Test-split runs and analysis exactly as frozen; every deviation is reported.

### Tooling (agreed with the audit)

| Need | Choice | Reason |
|---|---|---|
| Execution | A plain Python package with a CLI and YAML configs, for example `python -m thesis audit-dataset`, `build-manifest`, `make-contexts`, `validate-contexts`, `run`, `evaluate` | Explicit, testable, repeatable |
| Environment and checks | `uv` with a lock file; `pytest`; `ruff` | Exact versions; tests before any paid call |
| Java structure | `tree-sitter-java`, pinned | Enclosing methods for C1 |
| Retrieval | The project's own BM25, unit-tested and cross-checked against a reference implementation | Transparent and already specified |
| Model access | Provider SDKs directly; LiteLLM only if it preserves log-probabilities and usage | Exact scoring and cost |
| Outputs | Immutable JSONL or Parquet, a small SQLite run manifest, SHA-256 of every prompt and input | Audit trail |
| Version control | Git and GitHub for code, configs, and documents; data and clones outside Git and OneDrive | Reproducibility without syncing large files |
| Not used | LangGraph, LangChain, autonomous agents | They make inputs and cost vary per commit, which the fixed-prompt design forbids. Use them only if adaptive retrieval becomes a separate condition |

An AI coding assistant may help write and review code and tests; it is never part of the inference method.

## 2. Decisions to finalize before writing production experiment code

Status of every item: **Open.** Each needs a recommended default agreed with your supervisor. Record the outcome in the decision log (§3). Items marked *(rev. 2)* changed in the Phase 2 review and *(rev. 3)* after the external audit; the reasons are in the [revision log](README.md#revision-log).

| ID | Decision | Recommended default | Evidence or rationale | Depends on |
|---|---|---|---|---|
| D1 | Dataset *(rev. 3)* | JIT-Defect4J labels, splits, and IDs, with code reconstructed from the Apache Git repositories; **conditionally accepted** until Gate 1 closes. JIT-Defect-Extended only for cross-checks and comparability. Fallback: ApacheJIT 2010–2017 with Hadoop merged or excluded | [02-datasets.md](02-datasets.md) §6; all-project audit [V] | Gate 1 open items |
| D2 | Unit and label | Commit; `is_buggy_commit` | Verified schema | — |
| D3 | Split usage | Test = confirmatory only; validation = pilot and template development; train = baselines B1–B3 | Leakage control L6 | — |
| D4 | Eligibility *(rev. 3)* | Reconstruction passes (numstat over Java files except `package-info.java`); at least one in-scope change; **T(C0) ≤ 16K tokens** (o200k_base); unique patch ID. Inference target: eligible Java changes, benchmark label as observed proxy | All projects: 16K keeps 85–87% of defective and ~98% of clean train/validation commits (12K: 80–83% of defective); largest cap that fits 32K-token windows with the 8K RQ3 context [V] | Supervisor |
| D5 | Sampling *(rev. 3)* | All eligible defective + 2 × clean with the same sampling fraction in every project; N ≈ 1,200; weight 1/f for clean commits in prevalence-dependent metrics | Power; positives scarce (8.7%); AUC needs no weights | Gate 3 |
| D6 | Prompt inputs and format *(rev. 3)* | Diff of in-scope Java files plus one context block; no message or metadata; identical block header and order; single-token YES/NO; two-candidate likelihood score | Brief's C0 definition; benchmark change scope; contamination; Xiong2024 | Gate 3 valid-score rate |
| D7 | C0 diff *(rev. 3)* | `git diff -U3 -M <parent> <commit> -- '*.java' ':(exclude)*package-info.java'` | The benchmark's change metrics use this scope (99.98% match) [V]; a documented scope decision, not proof about the labels | — |
| D8 | C1 definition *(rev. 3)* | Separate block of same-file parent code; lines shown in the diff masked; lines of the enclosing method (tree-sitter-java) first, then nearest lines; filled to B. Git's `--function-context` as a cross-check | Brief's "same diff alongside local context, without duplication"; audit recommendation | Gate 2 manual check |
| D9 | C2 retriever and budget *(rev. 3)* | Pool = parent `.java` files minus changed files; license headers stripped; windows of at most 40 lines *and* a token bound (about 500), plus a final window; diff-identifier query; BM25 (k1 = 1.2, b = 0.75) over code lines only; only windows scoring above 0; **B = 2,000** (alternative: 1,000); fallback: `git grep`-anchored pool if the manipulation check fails | At 2,000 the same-file pool fills C1 for about 73% of sampled commits, at 1,000 for about 84% [V]; a 40-line window reached 5,813 tokens in the demo [V] | Gate 2 checks; Gate 3 manipulation check |
| D10 | C3 control | Same pool; seeded random; T(C3) = T(C2) ± 2%; seed 0 for all models, seeds 1–2 for M1 | Token matching; variability | — |
| D11 | Budget series and optional add-ons *(rev. 2)* | RQ3: C2 and C3 at 1K and 8K for M1, full sample (a subsample if the budget is tight). Message ablation, same-file BM25, and B5: exclude unless your supervisor asks for them | The brief makes quantity part of the primary independent variable | Budget |
| D12 | Models *(rev. 3)* | M1: exact two-candidate scoring (open weights preferred), pinned; a training cutoff before July 2025 is preferred but is not a contamination guarantee. M2: an independent second model with valid scoring (`gpt-4o-mini` if still offered). M3: optional frontier model on a subsample | SA1 robustness; contamination (Risk 4); scoring validity (Risk 6) | Availability, cutoffs, and prices on the run date |
| D13 | Metrics *(rev. 3)* | Primary: ROC-AUC (M1) if ≥ 98% of pilot prompts give valid two-candidate scores; otherwise MCC (IPW) on binary answers, decided before any test call. Key secondary: MCC (IPW); within-project and project-stratified AUC | Threshold-free and prevalence-free; audit findings on scoring validity and project dependence | Gate 3 |
| D14 | Statistics *(rev. 3)* | Holm over {C1−C0, C2−C0, C2−C1, C2−C3} on DeLong's test for M1, with C2−C1 on commits whose same-file pool can fill B; stratified paired bootstrap (10K) plus a project-cluster bootstrap; McNemar; TOST | DeLong1988, Dietterich1998, Lakens2017; audit | — |
| D15 | Failures and invalid outputs *(rev. 3)* | Retry only transient API failures (at most 2 identical retries). Content-invalid responses are never recoded; each contrast uses commits valid in both conditions; the invalid rate is reported per condition; S5 bounds the results by scoring invalid responses as YES and as NO. Every exclusion gets a reason code | Recoding invalid responses as NO would flatter a clean-majority sample | — |
| D16 | Contamination checks *(rev. 3)* | Document training cutoffs; label-recall probe per model as screening only; issue-key and future-fix flags in rationales; year stratification; S10; claims limited to public historical commits | Labels public since 2022 (JIT-Fine) and 2025 (JIT-Defect-Extended) [V] | — |
| D17 | Pre-registration and budget | Git tag `analysis-plan-v1` (optionally OSF) before test inference; hard USD cap per model | Wagner2025; cost model | Supervisor |
| D18 | Data permission | Email the JIT-Fine authors; publish manifests only | No LICENSE file in the repo | — |
| D19 | Positioning against JIT-LSM *(new)* | Read Huang2026 before freezing the RQs; claim novelty only for the five points in [01-literature-review.md](01-literature-review.md) §9 | Closest prior work; paper not yet read | Library access |
| D20 | Use of JIT-Defect-Extended and JIT-LSM files *(new)* | Commit IDs and cross-checks only; never read by the prompt builder; never redistributed | Labels embedded in records and paths; no license [V] | — |
| D21 | Comparability baseline B5 *(new)* | Run only if Huang2026 reports results on its 1,000-commit balanced subset | Without published per-subset numbers the comparison is empty | D19 |
| D22 | Supervised baseline B3 *(new)* | Re-run JITLine from the JIT-Fine package; time-box the effort and fall back to B1/B2 plus cited results if it does not run | `baselines/JITLine` exists in the package [V]; runnability not verified | — |
| D23 | Same-file BM25 condition C1b *(new, optional)* | Add only if the thesis is to make a causal claim about code *location*; otherwise C2−C1 stays a strategy comparison | C1 and C2 differ in pool and ranking (design §5.6) | Supervisor |
| D24 | SESOI *(new)* | Justify δ from validation-split evidence (for example the AUC gap between baselines B1 and B2) and the noise floor; 0.03 AUC is only a placeholder | Equivalence needs a defended margin (design §11) | Gate 3, supervisor |
| D25 | Tooling *(new)* | Python CLI package, `uv` lock, `pytest`, `ruff`, `tree-sitter-java`, provider SDKs; no LangGraph or agents in the inference path | Fixed-prompt design; audit (§1, Tooling) | — |
| D26 | Label-quality audit *(new)* | 30 defective validation commits reviewed against their fixes; second rater on 10 | Gate 1; Risk 1 | — |

## 3. Decision log template

Copy this block for each decision. Never edit a closed entry; supersede it with a new one.

```markdown
### D<ID> – <title>
- Date: YYYY-MM-DD
- Decision:
- Alternatives considered:
- Evidence (links to pilot results / papers):
- Consequences for validity:
- Approved by: <supervisor>
- Supersedes: —
```

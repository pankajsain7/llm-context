# Research & Feasibility Phase: Overview and Proposal

**Thesis:** *The Impact of Repository Context Selection on LLM-Based Just-in-Time Defect Prediction: An Empirical Study* (M.Sc. Professional Software Engineering, Reutlingen University)
**Phase:** literature and dataset feasibility review (Phase 1), a critical self-review (Phase 2), responses to two external audits (Phase 3), and the tested context builder (Gate 2), all 2026-10-19; the third audit response, 2026-10-20. No LLM has been called. Changes are listed in the [external audit response](#external-audit-response), the [second audit response](#second-external-audit-response), the [third audit response](#third-external-audit-response), and the [revision log](#revision-log).

## Readiness

| Item | Status |
|---|---|
| Research questions | Proposed (revision 3.1); to agree with your supervisor |
| Dataset | JIT-Defect4J: Gate 1 evidence complete. Ni2022 read; reconstruction, dates, duplicates verified on all 27,319 commits; the split is time-ordered and class-stratified, which makes commit age predictive of the label (D28). Open: per-commit AI rating and human second rater for the label audit, data permission, supervisor sign-off |
| Context construction | `jitctx` package with C0–C3, tree-sitter C1, token-bounded BM25 windows, rendered-token accounting; unit tests and integration tests on real validation commits; enclosing ranges checked (0/40 errors), C2/C3 matching checked on every pair, relevance proxy C2 > C3; pilot sample frozen and contexts rebuilt deterministically. Open: human reading of side-by-side prompts, blinded relevance rating (Gate 3) |
| LLM scoring | Specified (hosted APIs only), not validated; needs the engineering pilot (Gate 3) |
| Statistical protocol | Proposed: fixed-project inference with project-cluster CIs for generalisation (D14); the equivalence margin is not yet justified |
| Evidence limits | JIT-LSM paper unread (closed access); JIT-Context known from its abstract only. All numbers are reproducible with the scripts, hashes, and outputs in [../feasibility/](../feasibility/) and [../src/jitctx/](../src/jitctx/) |

## Proposal (revision 3)

### What to investigate

Which code context, if any, improves zero-shot LLM prediction of defect-inducing commits, and why. Prior work already adds context in other ways: JIT-LSM gives an *agent* same-file code, LLM4Reg gives a multi-stage pipeline cross-file code and varies its amount, PROPER-SDP adds project-evolution text, and JIT-Context learns structural context with a GNN ([01-literature-review.md](01-literature-review.md) §9). None compares sources at an equal budget or controls volume with random code. The thesis does that, with one fixed, non-agentic prompt per condition:

| Question | Contrast (primary model M1) |
|---|---|
| **RQ1 Effectiveness and strategy.** Does same-file (C1) or cross-file context (C2) help over the diff alone (C0)? Does the BM25 cross-file strategy beat the proximity same-file strategy at the same budget? | C1−C0, C2−C0; C2−C1 as a strategy comparison on commits whose same-file pool fills the budget |
| **RQ2 Relevance.** Is BM25-selected cross-file code better than random cross-file code of the same size? | C2−C3, with a manipulation check |
| **RQ3 Quantity and cost.** How do performance, tokens, cost, and latency change at 1,000 / 2,000 / 8,000 tokens of cross-file code? | Estimation |
| **SA1 Models** (secondary). Do the effects hold for an independent second model? | Sign consistency |

Negative, inconclusive, and equivalence results are planned outcomes, not failures.

### Which dataset

**JIT-Defect4J** (Ni2022): labels, splits, and commit IDs, with all code reconstructed from the original Apache Git repositories at the parent commit.

- All 27,319 commits exist with their recorded parent, and Git reproduces the benchmark's churn for 99.98% once the input scope matches the benchmark's (Java files except `package-info.java`) [V].
- The split is per project, time-ordered, and then class-stratified: defective commits were moved from earlier periods into later splits to equalise defect rates, so 159 test commits are older than their project's newest train commit and commit age predicts the label [V/P]. This matters for trained baselines and, through era cues, for absolute LLM performance (L15, D28).
- Inference target: eligible Java changes of the test split, with the SZZ-derived benchmark label as an observed proxy.
- **JIT-Defect-Extended** (released with JIT-LSM) is a subset of JIT-Defect4J with identical labels, embedded in every record and folder name [V]. It is used only for cross-checks, never as prompt input.
- Fallback: ApacheJIT (2010–2017, Hadoop merged or excluded). Details: [02-datasets.md](02-datasets.md).

### Which experiments

| Element | Choice |
|---|---|
| Conditions | C0 Java diff · C1 + same-file code (lines already in the diff masked) · C2 + BM25 cross-file windows · C3 + random cross-file windows matched to C2's rendered tokens. Shared budget 2,000 tokens for C1–C3 (alternative 1,000); series 1,000 / 8,000 for C2 and C3; windows bounded by lines *and* tokens |
| Sample | Test split; label-blind eligibility (diff ≤ 16,000 tokens); all ≈ 400 eligible defective commits plus 2 × clean, proportional by project (N ≈ 1,200) |
| Models | M1 with exact two-candidate scoring, M2 an independent second model, M3 optional; all through hosted cloud APIs, no local hosting |
| Metrics | Primary ROC-AUC if the pilot validates the scores (else MCC, fixed before any test call); MCC, within-project AUC, calibration, cost, tokens, latency |
| Statistics | Holm over four contrasts (DeLong), commit-level and project-cluster bootstrap CIs, TOST with a *justified* SESOI, noise floor |
| Baselines | Trivial; size-only and Kamei logistic regression; JITLine re-run (time-boxed); published results for context |
| First step | Gates 1–3: dataset acceptance, a tested context builder, a 60-commit engineering pilot ([06-milestone-and-decisions.md](06-milestone-and-decisions.md)) |

Full specification: [03-experimental-design.md](03-experimental-design.md).

### Why this is academically rigorous

- **One factor per contrast.** Every condition shows the identical diff; only the context block differs, and C1–C3 share one budget counted on the rendered text.
- **Volume is controlled** by a token-matched random block from the same pool. C2−C0 = (C2−C3) + (C3−C0) is read as an accounting identity, not as a causal decomposition.
- **The manipulation is checked** with a blinded human rating and a pre-specified fallback retriever before any test-split run.
- **Leakage controls:** parent-snapshot code only, label-blind eligibility, no messages or metadata, a documented input scope, and a locked, pre-registered test split.
- **Measurement is validated before use:** the scoring method must pass the pilot, and invalid responses are never recoded.
- **Null results are interpretable** through equivalence tests with a defended margin and a measured noise floor.
- **Contamination is reduced, not claimed absent:** documented cutoffs, a screening probe, year stratification, and cautious claims.

### Why it is feasible

- About 1,200 commits, deterministic Git plumbing, and BM25 in about a second per commit [V].
- About 69M input tokens for M1 and 21M per further model: roughly $14–$686 for M1, depending on the price per million tokens [I].
- Every expensive step sits behind a gate with explicit pass criteria.

### Open issues for your supervisor

1. **Read the JIT-LSM paper** through the library (closed access); it fixes how the thesis is positioned (D19).
2. **Equivalence margin and power.** The planning MDE is about 0.03–0.04 AUC (larger for C2−C1). Agree on a justified SESOI (D24).
3. **Budget and cap.** B = 2,000 vs 1,000 (D9) and the 16,000-token cap (D4).
4. **Data permission** for JIT-Defect4J, which has no license file (D18).
5. **Label noise** remains the top validity risk; the label-quality audit (D26) is the next concrete step.

## External audit response

Review of the two external audit reports (2026-10-19). Each point was checked against the sources, the code, or new measurements.

| # | Audit point | Verdict | Evidence found | Action |
|---|---|---|---|---|
| 1 | Numbers not reproducible from the shared archive | Correct | Data and clones are deliberately outside OneDrive, but hashes, versions, and raw outputs were missing | Added input hashes, `requirements.txt`, repository HEADs, and label-free outputs ([04-feasibility-demo.md](04-feasibility-demo.md) §1, §5.6) |
| 2 | Do not lock the dataset before an all-project audit | Correct | All 27,319 commits checked: parent 100%, churn 99.98% | Status "conditionally accepted"; Gate 1 lists the open items |
| 3 | Label reliability is unproven | Correct | Known (Risk 1); the label protocol is still unread | Label-quality audit added (D26); label treated as an observed proxy |
| 4 | The 4-project measurements are unrepresentative | Correct, and the bias was larger than expected | Defective commits kept at 12,000 tokens: 80–83%, not 93%. Same-file pool ≥ 2,000 tokens: 69%, not 83–86% | Cap raised to 16,000; budget trade-off documented; numbers replaced |
| 5 | The split explanation is speculative | Correct, and the explanation was wrong | The 159 inverted test commits are inverted by committer time too | Explanation withdrawn; baselines reported with and without them |
| 6 | Duplicates unchecked | Correct | 148 patch-id groups, none across train and test | Recorded; L8 keeps one per patch-id |
| 7 | JIT-Context and LLM4Reg missing; novelty matrix needed | Correct. LLM4Reg is even closer than stated: it uses JIT-Defects4J commits, cross-file context, and varies its amount | Both verified (abstract; preprint and README) | Claim-by-claim matrix; claims narrowed ([01-literature-review.md](01-literature-review.md) §9) |
| 8 | A pre-July-2025 cutoff does not rule out contamination; a negative probe proves nothing | Correct | JIT-Fine published the labels on 2022-08-30 | Contamination reworded as reduced, not excluded (L10, Risk 4, D16) |
| 9 | A Java-only numstat match verifies the metric, not the label scope | Correct | The match also requires excluding `package-info.java` | Input scope documented as a decision (D7, L14) |
| 10 | C1 vs C2 is a strategy comparison | Correct in substance; I disagree that it must be descriptive only | The design already said so (§5.6), but the RQ wording implied a location effect | H1c kept as a pre-specified *strategy* contrast; optional C1b if a location claim is wanted (D23) |
| 11 | Log-probability scoring is unvalidated; invalid outputs must not count as NO | Correct | A top-k list need not contain both answers | Exact two-candidate scoring, pilot gate, pre-specified MCC fallback, no recoding (D13, D15) |
| 12 | Project-aware uncertainty | Correct | Projects differ in base rate | Project-cluster bootstrap, within-project and project-stratified AUC |
| 13 | SESOI and power need justification | Correct | 0.03 AUC was a placeholder | Justification procedure (D24); power marked as a planning approximation |
| 14 | A 60-commit pilot is only an engineering test | Agree | It was already descriptive only | Renamed the engineering pilot (Gate 3) |
| 15 | BM25 scores are not proof of relevance | Agree | The fixed prototype's top window for Example 1 is Base64 test data | Blinded rating with failure cases; token-bounded windows |
| 16 | The decomposition is not causal | Correct | — | Reworded as an accounting identity |
| 17 | Model dependence should be secondary | Agree | — | RQ4 became secondary analysis SA1 |
| 18 | Code defects (window coverage, zero scores, token matching, path terms, sampling, pool ≠ prompt) | Correct; all reproduced | Old `chunk()` dropped up to 19 lines per file | Fixed with 129 tests; the C1 builder and prompt measurement move to Gate 2 |
| 19 | Use a plain Python CLI, not LangGraph or agents | Agree | Consistent with the fixed-prompt design | Tooling plan (D25); tree-sitter-java now primary for C1 |
| 20 | Budget series only as optional sensitivity | Partly disagree | The brief makes quantity part of the primary independent variable | RQ3 kept; the 8,000 level stays subject to cost |

**Found beyond the audits:** the benchmark's metrics omit `package-info.java`, and line-based windows do not bound tokens (one 40-line window held 5,813 tokens).

## Second external audit response

Review of the second external audit (2026-10-19), which checked an older archive of this repository. Each point was re-checked against the current files, the JIT-Fine paper, and new measurements.

| # | Audit point | Verdict | Evidence found | Action |
|---|---|---|---|---|
| 1 | The claim that test labels were never inspected is wrong | Correct. `verify_datasets.py`, ad-hoc scratch scripts, and the demo examples used test labels; the handoff already listed some of it, the dataset document still said "test labels were not read" | Four test records identified by position, up to two more unidentified; a list of aggregate test-label statistics | Authoritative record and rules in [02-datasets.md](02-datasets.md) §8; `verify_datasets.py` blanks test labels by default; D27 (exclude displayed records) |
| 2 | `fill()` stops at an oversized single-line window | Correct, reproduced | 4,505-token first window, 7-token second, budget 1,000: nothing selected | Skip and continue, in the prototype and in `jitctx`; tests for the exact case |
| 3 | Token matching is counted per snippet, not on the joined text | Correct | The prompt contains the joined block | Budgets and C3 matching now use the rendered block; tests assert equality |
| 4 | 129 passing tests do not establish correctness | Agree | The two defects above passed the old suite | Edge-case tests plus integration checks on real validation commits; still not a proof of methodological validity |
| 5 | The open-weight, locally scored M1 contradicts the brief | Correct in substance; local hosting was already approval-only | The brief rules out heavy local models | Hosted cloud APIs only (user decision; D12); MCC fallback if no hosted M1 gives valid scores |
| 6 | Stale 12,000-token cap and inconsistent contamination dates | Correct for two lines: the dataset recommendation still said "cap 12,000", and its trade-off list dated label exposure only to July 2025 (JIT-Defect-Extended), omitting the August 2022 JIT-Fine release that L10 and Risk 4 already named | — | Both lines corrected; superseded values marked as such |
| 7 | Read Ni2022; audit 30 defective validation commits; clarify the split's effect on baselines | Agree; done except the human second rater | The paper describes a per-project 80/20 time split that "keeps the distribution"; the released split is class-stratified; commit age predicts validation labels (AUC 0.836); Kamei baseline AUC 0.792 vs 0.771 in the chronological window | [02-datasets.md](02-datasets.md) §2 items 5 and 10, §2a; L11, L15, S11; D28 |
| 8 | Initialise Git | Already done before this audit (`github.com/pankajsain7/llm-context`) | — | `.gitignore` extended for data, labels, and outputs |
| 9 | Implement C0–C3 with tree-sitter and BM25 | Agree | — | [../src/jitctx/](../src/jitctx/), [../tests/](../tests/) |
| 10 | Prefer a project directory outside an employer-managed OneDrive | Partly: data, clones, and the environment are already outside OneDrive; the repository itself still sits in OneDrive | — | Left to the user; Git remote is the authoritative copy |

**Found beyond the audit:** the released split is class-stratified (the main threat to absolute results and baselines); `tree-sitter` 0.26.0 crashes on Windows; Python's `splitlines()` disagrees with Git's line numbering on form feeds.

## Third external audit response

Review of the remaining issues of the third independent audit before the hosted-LLM pilot (2026-10-20). No LLM was called and no test label was used.

| # | Audit point | Verdict | Evidence found | Action |
|---|---|---|---|---|
| 1 | Cross-split duplicate patches between supervised training and validation | Correct | 3 train–validation patch-id groups; 2 of the validation copies (gora) were eligible | Eligibility now excludes any commit whose patch occurs in an earlier split; unit test [../tests/test_manifest.py](../tests/test_manifest.py); manifest rebuilt (design §8 item 4) |
| 2 | The AI-assisted label audit overstates what it shows | Correct | The forward search had five limits that can hide the labelling fix; per-commit ratings were not saved; the "≥ 17%" interval was an error rate built on unverified ratings. An exhaustive re-check of the four named contradictions supports one mechanically, two by issue date plus move detection, one on reading only | [02-datasets.md](02-datasets.md) §2a rewritten; no error rate; `label_audit.py --recheck`; D26 revised |
| 3 | C2–C3 token matching must be verified for every status, with overlap | Correct; it passes, with one documented edge case | Pilot: 180 pairs, 0 violations, overlap mean 0.6% of C3's lines. 200 label-free validation commits: 1 of 600 pairs flagged `line_limit` (2.1% short; no snippet header fits the gap) | `jitctx summarize` checks every pair and reports overlap; unit test; handling of flagged pairs in design §5.5 and S3 |
| 4 | Gate 2 manual checks are open | Correct; done by the AI assistant (human reading of prompts still open) | Tree-sitter 0/40 errors against the design rule; relevance proxy C2 0.73 vs C3 0.24; inspection found a licence-header defect in default-package files | Fixed with a test; [06-milestone-and-decisions.md](06-milestone-and-decisions.md) Gate 2 |
| 5 | Project-aware statistics and the split interpretation | Correct | Cluster CIs about 2.6 × wider than commit-level CIs on validation; the split numbers had no script, and the within-project AUC 0.844 was not reproducible (now 0.836, defined) | Design §11 items 2–3 and D14; [../feasibility/split_analysis.py](../feasibility/split_analysis.py); observed vs inferred parts separated in [02-datasets.md](02-datasets.md) §2 item 10 |
| 6 | The pilot sample, seeds, and contexts must be reproducible | Correct; two gaps | The pilot selection code was not in the repository; the context artifacts recorded a commit that did not contain the builder | Frozen list [../configs/pilot_commits.txt](../configs/pilot_commits.txt) with its selection rule; `code_revision` now marks uncommitted builds; contexts rebuilt twice from a commit and compared |

## Revision log

Phase 2 critical review, 2026-10-19. Each row is a weakness, unsupported assumption, or missing piece of evidence in revision 1, with the evidence found and the change made. The external audit later corrected rows 4, 6, and 7, whose evidence came from four projects only; see the [external audit response](#external-audit-response).

| # | Finding in revision 1 | Evidence | Change |
|---|---|---|---|
| 1 | Novelty overstated: "no study varies repository context for LLM JIT-DP" | JIT-LSM gives an agentic LLM same-file context on JIT-Defect4J commits [V, code; paper not read] | Novelty narrowed to five specific points ([01-literature-review.md](01-literature-review.md) §9); design principle 6; decision D19 |
| 2 | JIT-Defect-Extended not assessed | A subset of JIT-Defect4J (27,155 commits, identical labels), with labels embedded in records and paths [V] | Used for cross-checks only; leakage control L2; contamination Risk 4 |
| 3 | Diff covered all files | `la/ld` match all-files numstat for 68.5% of commits but Java-only numstat for 100% [V] | Java-only inputs (D7, L14) |
| 4 | Assumed median diff of 1,500 tokens and 20–30 tokens per changed line | Measured medians: 696 tokens (random), 2,088 (defective); 34.4 and 18.9 tokens per line [V] | Cost model and eligibility recalculated |
| 5 | C1 replaced the diff and had no volume match; RQ1 lacked local vs repository | Brief asks whether relevant repository context beats *local* code | C1 is a separate, masked same-file block at the shared budget; new contrast C2−C1 (H1c); sensitivity S9 |
| 6 | Budget of 4,000 tokens | Same-file pool ≥ 4,000 tokens for only 63.5–75.2% of commits; ≥ 2,000 for 83.0–86.1% [V] | B = 2,000 |
| 7 | Size cap of 8,000 diff tokens | Keeps 85.1% of defective commits; 12,000 keeps 93.1% [V] | Cap 12,000 (D4); **superseded** by 16,000 after the all-project audit (external audit row 4) |
| 8 | Context quantity only an optional ablation | The brief makes quantity part of the primary variable | RQ3 budget series 1,000 / 2,000 / 8,000 |
| 9 | Primary metric MCC depends on an arbitrary threshold and on weights | Context can shift the YES rate without better discrimination | Primary ROC-AUC; MCC key secondary; power recomputed in AUC units |
| 10 | No supervised code-based baseline, no LLM reference | `baselines/JITLine` ships with JIT-Fine [V]; JIT-LSM evaluates on test-split subsets [V] | Baselines B3 (JITLine), B4 (published incl. JIT-LSM), optional B5 |
| 11 | No action if the manipulation check fails | — | Pre-specified `git grep`-anchored fallback retriever |
| 12 | Contamination considered only for code and messages | Labels for 27,155 commits public as JSON since July 2025 [V] | M1 cutoff before July 2025, label-recall probe, S10 |
| 13 | Calibration not motivated | JIT-DP models miscalibrated, ECE 2–35% (Shahini2025) [V, AB] | Calibration reported as a secondary metric |

**Unchanged after review:** the dataset choice, the parent-snapshot rule, BM25 against a token-matched random control, the exclusion of commit messages, equivalence testing, the noise floor, the locked test split, and the pilot-first plan.

## Document map

| Brief item | Document |
|---|---|
| A. Literature review | [01-literature-review.md](01-literature-review.md) |
| B. Dataset comparison and C. recommendation | [02-datasets.md](02-datasets.md) |
| D. Experimental design | [03-experimental-design.md](03-experimental-design.md) |
| E. Feasibility demonstration (real data) | [04-feasibility-demo.md](04-feasibility-demo.md) |
| F. Ranked research risks | [05-risks.md](05-risks.md) |
| G. First milestone and decisions to finalize | [06-milestone-and-decisions.md](06-milestone-and-decisions.md) |
| Bibliography with verification levels | [references.md](references.md) |
| Discussion history, decision rationale, and handoff notes | [PROJECT_HISTORY.md](PROJECT_HISTORY.md) |
| Working rules for every agent | [../AGENTS.md](../AGENTS.md) |
| Reproduction scripts (prototypes only) | [../feasibility/](../feasibility/) |

## Evidence conventions

- Every factual claim carries a label: **verified** (from the full text, abstract, or our own data), **background knowledge** (metadata verified, content not re-read), **interpretation**, or **assumption**. Each document defines its own labels.
- Each reference shows its verification level (FT, AB, MD, SEC, RP) in [references.md](references.md). Re-read MD and SEC sources before quoting their findings in the thesis.
- All examples are real records. Nothing is synthetic.

## Where the data lives

- Downloaded datasets, clones, and the Python virtual environment are in `C:\Users\psain\thesis-scratch`, **outside OneDrive**, to avoid syncing large repositories.
- `thesis-scratch\jitext` holds the JIT-LSM evaluation subsets and the JIT-Defect-Extended file list. Both contain labels, so prompt-building code must never read them (design control L2).
- To recreate everything, follow [04-feasibility-demo.md](04-feasibility-demo.md) §1.

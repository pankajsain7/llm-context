# G. Acceptance Gates and Decisions to Finalize

Status: proposal, 2026-10-19, revised after the Phase 2 critical review, the external audit (milestone M1 restructured into acceptance gates; D7–D9 and D12–D16 revised; D23–D26 added), and **the second external audit** (Gate 1 evidence completed except data permission; the Gate 2 builder implemented in [../src/jitctx/](../src/jitctx/); D12 hosted-only; D27–D28 added), and the third external audit (2026-10-20: duplicate rule, Gate 2 checks, D14 and D26 revised). The scripts in `feasibility/` remain prototypes and measurement aids.

## 1. Acceptance gates (restructured after the external audit)

Work proceeds through five gates, each with a deliverable and pass criteria. Nothing before Gate 5 uses test-split labels or calls an LLM on the test split. What was already seen of the test split, and the rules that follow, are in [02-datasets.md](02-datasets.md) §8.

### Gate 1: Dataset acceptance (evidence complete; data permission open; supervisor sign-off needed)

**Done** [V; [02-datasets.md](02-datasets.md) §2; [feasibility/audit_dataset.py](../feasibility/audit_dataset.py)]:

- All 27,319 commits of all 21 repositories exist, have one parent, and match `parent_hashes`. Churn is reproduced for 99.98% of commits in every split once `package-info.java` is excluded.
- Split chronology checked with author *and* committer time; duplicate Java changes checked with `git patch-id --stable`.
- Diff-size eligibility measured for every split (label-blind) and by class for train and validation.
- Ni2022 read in full: label protocol and split protocol documented; the split is time-ordered and then class-stratified, which makes commit age predictive of the label (§2 item 10).
- Label-quality audit of 30 defective validation commits, first rating ([02-datasets.md](02-datasets.md) §2a).
- Label-free manifest with eligibility flags: `python -m jitctx build-manifest` (kept in the scratch folder, labels in a separate train/validation file). Result [V, rebuilt 2026-10-20 with the earlier-split duplicate rule]: reconstruction 16,371 / 5,464 / 5,479 (train / valid / test), identical to the audit; eligible 15,694 / 5,296 / 5,237; one test commit excluded as a patch duplicate of a validation commit and two validation commits as duplicates of training commits; four displayed test records flagged. SHA-256 of `manifest.csv`: `9f487f7ee737a93db825924a95c614efe7d468067da647793ac18f9aa85480af` (supersedes `77cad9be…412a5`, kept as `manifest_v1_77cad9be.csv`; the only differences are the new `dup_earlier_split` column and the two gora flags). `labels_trainvalid.csv` is unchanged.

**Open:**

1. Second rater on 10 of the 30 audited commits (a human; the first rating was AI-assisted).
2. Data permission (D18).
3. Supervisor decisions D27 and D28.

**Deliverable:** the frozen manifest and its SHA-256, plus SHA-256 hashes of all inputs.

### Gate 2: Tested context builder (no LLM calls) — implemented; manual checks open

Implemented as the `jitctx` package ([../src/jitctx/](../src/jitctx/), CLI `python -m jitctx`), following design §5, with automated tests in [../tests/](../tests/) for:

- full window coverage with line *and* token bounds, `no_hits`, `short`, `line_limit`, and `empty_pool`; budgets counted on the rendered block; C3 within ±2% or flagged;
- the second audit's case: an unfittable top-ranked window is skipped and the next one used;
- masking: no line shown in the diff reappears in C1; tree-sitter enclosing ranges for methods, constructors, initializers, anonymous classes, and field-level changes;
- diff parsing: added, deleted, renamed, pure-rename, multi-file, missing final newline, and deleted lines that look like `---` headers;
- label-blindness: the builder never reads label files (a static check; only `manifest.py` opens the benchmark files);
- BM25 scores against a hand computation;
- integration on real validation commits: identical diff and template across conditions, verbatim parent code, no touched path in C2/C3, budgets, determinism.

**Manual checks (2026-10-20; performed by the AI assistant, not by a human rater)** [V for the measurements; the classifications are judgements], with [../feasibility/gate2_checks.py](../feasibility/gate2_checks.py):

- **Tree-sitter enclosing ranges vs `git diff -W`** (`ranges --n 40 --seed 7` on the current manifest; output kept as `thesis-scratch\gate2_ranges.txt`): 40 changes (Git function-context hunks) in 24 validation commits from 14 projects. 17 agree exactly (ignoring blank, comment, annotation, and brace lines). All 23 differences follow the design rule: 7 changes in the package/import block (no enclosing type, so tree-sitter returns nothing; Git shows the file head), 14 changes on fields, in javadoc, or on blank lines between members (type header and fields; Git attaches a neighbouring method; 8 inspected line by line), and 2 where Git's range runs on into the next method's signature. **No tree-sitter error (0/40; gate ≤ 10%).** An earlier run of the same check on the previous manifest (40 other changes, 28 commits, 13 projects) also found 0 errors and, in addition, 5 cases where Git's regex stopped at a method of an anonymous or nested class and tree-sitter had the correct enclosing method. Design caveat from that run: for a change inside an anonymous class, C1 starts with that inner method, not the outer one.
- **Token matching across every status** (`python -m jitctx summarize`, which now pairs every C3 record with its C2 record): 180 C2/C3 pairs in the 60 pilot commits (three budgets), status pairs `ok/ok` 177 and `no_hits/no_hits` 3, **0 violations** of "C3 within 2% below C2, or both empty". C3 shows lines that C2 also shows in 23 of 177 non-empty blocks (mean share of C3's lines 0.6%, maximum 14.1%). The pilot contains no `short` or `line_limit` C2 blocks; those statuses are covered by unit tests. **Label-free check** on 200 random eligible validation commits (`make-contexts --sample 200 --sample-seed 1 --extra-budgets 1000 8000`): 600 pairs, `ok/ok` 587, `no_hits/no_hits` 12, and 1 violation, a C3 flagged `line_limit` at 2.1% below C2 (opennlp, 1,000 tokens: the 21 tokens left were fewer than any snippet header); C3 lines also in C2 in 92 of 588 blocks (mean 0.9%, maximum 36%). Handling of such pairs: design §5.5.
- **Relevance, automated proxy** (design §5.7; `relevance`): share of snippets that contain a method or type name called or declared in the changed lines, 59 pilot commits with context: C2 0.733 vs C3 0.238 at 2,000 tokens (C2 higher in 51, equal in 7, lower in 1; exact sign test p = 2e-14); 1,000: 0.731 vs 0.181; 8,000: 0.674 vs 0.274. The proxy is lexical like BM25 itself, so it confirms the manipulation, not usefulness.
- **Relevance, inspection** of the top-ranked C2 window and the C3 windows in 12 pilot commits (seeded, first artifact): the C2 top window was clearly relevant in 8 (the class under test, a called type, a caller, or the unit test of the changed method), weak in 3 (an import block, a type's javadoc header, commented-out test code), and irrelevant in 1 (a licence block, see below); C3 windows were unrelated in all 12. Not blinded, one rater; the blinded two-rater audit of Gate 3 step 2 remains.
- **Defect found and fixed:** default-package files (no `package` line) kept their licence header, which BM25 then ranked first (`src/test/maxima/.../RealFunctionValidation.java`, commons-math). The header is now stripped there too (design §5.1; test in [../tests/test_java.py](../tests/test_java.py)).

**Still open:** side-by-side C0–C3 prompts for 20 validation commits, read by a human.

**Measured on the 60 pilot commits** (validation, 30 defective and 30 clean, seed 2027, 16 projects; no LLM call; rebuilt 2026-10-20 from commit `f8b1fbb`) [V]: C1 `ok` 47, `short` 10, `empty_pool` 3; C2 and C3 `ok` 59, `no_hits` 1 at every budget; largest C3 match error 2.0% (1,000: 1.9%; 8,000: 1.9%); median build time 0.9 s per commit (max 2.5 s). Integration tests on 24 further validation commits (20 random, 4 edge cases) pass.

**Reproducibility of the pilot inputs** [V, 2026-10-20]:

- *Sample.* The 60 commit IDs are frozen in [../configs/pilot_commits.txt](../configs/pilot_commits.txt). The selection code had not been saved; the rule in its header (stratified `pandas` sample, `random_state=2027`, from the first manifest and the validation labels) reproduces the set exactly. All 60 remain eligible under the new duplicate rule, so the sample is kept rather than redrawn.
- *Seeds.* C3 uses `sha256(commit + ":" + seed)`, seed 0 ([../src/jitctx/conditions.py](../src/jitctx/conditions.py)); the pilot has no other random step.
- *Contexts.* Two builds from commit `f8b1fbb` gave identical records (all fields except `build_seconds`; 480 records). Compared with the first artifact, 79 C2/C3 prompts of 21 commits changed, all in repositories with default-package Java files (the header fix changes their windows, hence BM25 statistics and the C3 permutation); C0 and C1 are unchanged. The first artifact recorded `code_revision` 97883fd, a commit that did not yet contain the builder; `code_revision` now ends in `-dirty` when `src/` or `configs/` differ from HEAD. Artifacts: `thesis-scratch\pilot_contexts.jsonl` (current) and `pilot_contexts_v1_97883fd.jsonl` (superseded). Compare runs by `prompt_sha256`, not by file hash, because each record stores its build time.

**Deliverable:** a tagged builder version and one context artifact per pilot commit.

### Gate 3: Engineering pilot (validation split; not evidence about RQ1–RQ3)

| Item | Choice |
|---|---|
| Sample | 60 validation commits: 30 defective and 30 clean, seeded, from at least 4 small or medium projects; frozen in [../configs/pilot_commits.txt](../configs/pilot_commits.txt) |
| Conditions | C0, C1, C2, C3 (seed 0) at B = 2,000; C2 at 8,000 tokens (cost and latency only); repeated C0 and C2 |
| Model | M1 only, through a hosted cloud API: first about 20 requests to validate the scoring method, then 60 × 7 = 420 calls, plus about 40 probe calls |
| Analysis | Descriptive only; no hypothesis tests, no tuning toward better scores |
| Size and cost | Measured rendered prompts for the 7 planned calls per commit: 1.93M input tokens in total (median prompt: C0 962, C1–C3 about 2,950, C2@8,000 8,948 tokens) [V]. With the scoring check and probes, about 2.0M input tokens: roughly $0.30 at $0.15 and $20 at $10 per million input tokens [I]. Context artifacts: `thesis-scratch\pilot_contexts.jsonl` |

**Steps:**

1. **Scoring check.** Verify on about 20 requests that the chosen API returns valid two-candidate scores (design §4). Fix the method before the pilot proper. Confirm the estimated cost of the pilot with the user before the first paid call.
2. **Manipulation check.** Automated relevance proxy (design §5.7) for C2 vs C3 on all 60; two raters, blind to condition, rate 20–30 commits. Report κ *and* failure cases.
3. **Label-recall probe** (screening only). For 40 validation commits (20 defective, 20 clean), ask M1 without any code: "Is commit `<sha>` of `apache/<project>` stored under `buggy` or `no_buggy` in the JIT-Defect-Extended dataset? Answer with one word." Compare the accuracy with chance (exact binomial test). A negative result does not prove the absence of contamination.
4. **Pilot run.** Randomise the request order. Log raw responses, both answer likelihoods, usage, latency, model fingerprint, and errors to `results/pilot_predictions.jsonl` (in the scratch folder). Use the rationale variant on 10 commits.
5. **Era sensitivity** (L15). Regress the score on the label and commit age, per condition, to see whether context makes the model more sensitive to the commit's era.
6. **Pilot report** (`docs/pilot-report.md`): valid-score rate, invalid-output rate, token distributions per condition, predicted-positive rate and AUC per condition (descriptive, wide CIs), the between-condition score correlation $r$, the repeat flip rate, the probe result, era sensitivity, cost per call **reconciled with the provider's usage records**, the projected full-study cost, and a go/no-go decision.

**Readiness for step 1 (2026-10-20)** [assessment]: go for the scoring check only. Inputs are frozen and reproducible, matching and masking pass, and the manipulation proxy favours C2. Remaining risks before the 420-call run: (1) two-candidate scores from the chosen API are unverified; (2) the relevance evidence is lexical plus one unblinded rater; (3) the prompt template (`draft-1`) has not been read side by side by a human; (4) labels remain a noisy proxy with only 4 checkable contradictions in 30; (5) the era confound (D28) can inflate absolute AUC, which the pilot measures but cannot remove.

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
| Environment and checks | Pinned [../requirements.txt](../requirements.txt) (`pip`; `uv` is not installed on this machine), `pyproject.toml`, `pytest`, `ruff` | Exact versions; tests before any paid call |
| Java structure | `tree-sitter` 0.24.0 with `tree-sitter-java` 0.23.5 (0.26.0 crashed with access violations on Windows) | Enclosing methods for C1 |
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
| D4 | Eligibility *(rev. 3)* | Reconstruction passes (numstat over Java files except `package-info.java`); at least one in-scope change; **T(C0) ≤ 16K tokens** (o200k_base); unique patch ID within the split, and no patch already in an earlier split (train < validation < test). Inference target: eligible Java changes, benchmark label as observed proxy | All projects: 16K keeps 85–87% of defective and ~98% of clean train/validation commits (12K: 80–83% of defective); largest cap that fits 32K-token windows with the 8K RQ3 context [V] | Supervisor |
| D5 | Sampling *(rev. 3)* | All eligible defective + 2 × clean with the same sampling fraction in every project; N ≈ 1,200; weight 1/f for clean commits in prevalence-dependent metrics | Power; positives scarce (8.7%); AUC needs no weights | Gate 3 |
| D6 | Prompt inputs and format *(rev. 3)* | Diff of in-scope Java files plus one context block; no message or metadata; identical block header and order; single-token YES/NO; two-candidate likelihood score | Brief's C0 definition; benchmark change scope; contamination; Xiong2024 | Gate 3 valid-score rate |
| D7 | C0 diff *(rev. 3)* | `git diff -U3 -M <parent> <commit> -- '*.java' ':(exclude)*package-info.java'` | The benchmark's change metrics use this scope (99.98% match) [V]; a documented scope decision, not proof about the labels | — |
| D8 | C1 definition *(rev. 3)* | Separate block of same-file parent code; lines shown in the diff masked; lines of the enclosing method (tree-sitter-java) first, then nearest lines; filled to B. Git's `--function-context` as a cross-check | Brief's "same diff alongside local context, without duplication"; audit recommendation | Gate 2 manual check |
| D9 | C2 retriever and budget *(rev. 3)* | Pool = parent `.java` files minus changed files; license headers stripped; windows of at most 40 lines *and* a token bound (about 500), plus a final window; diff-identifier query; BM25 (k1 = 1.2, b = 0.75) over code lines only; only windows scoring above 0; **B = 2,000** (alternative: 1,000); fallback: `git grep`-anchored pool if the manipulation check fails | At 2,000 the same-file pool fills C1 for about 73% of sampled commits, at 1,000 for about 84% [V]; a 40-line window reached 5,813 tokens in the demo [V] | Gate 2 checks; Gate 3 manipulation check |
| D10 | C3 control | Same pool; seeded random; T(C3) = T(C2) ± 2%; seed 0 for all models, seeds 1–2 for M1 | Token matching; variability | — |
| D11 | Budget series and optional add-ons *(rev. 2)* | RQ3: C2 and C3 at 1K and 8K for M1, full sample (a subsample if the budget is tight). Message ablation, same-file BM25, and B5: exclude unless your supervisor asks for them | The brief makes quantity part of the primary independent variable | Budget |
| D12 | Models *(rev. 3.1)* | **Hosted cloud APIs only; no local model hosting, no fine-tuning** (user decision, 2026-10-19). M1: a pinned hosted model with exact two-candidate scoring; a training cutoff before July 2025 is preferred but is not a contamination guarantee. M2: a hosted model from another family or provider with valid scoring (`gpt-4o-mini` if still offered). M3: optional frontier model on a subsample. If no hosted M1 passes the scoring check, MCC becomes primary (D13) | SA1 robustness; contamination (Risk 4); scoring validity (Risk 6); the brief rules out heavy local models | Availability, cutoffs, log-probability support, and prices on the run date |
| D13 | Metrics *(rev. 3)* | Primary: ROC-AUC (M1) if ≥ 98% of pilot prompts give valid two-candidate scores; otherwise MCC (IPW) on binary answers, decided before any test call. Key secondary: MCC (IPW); within-project and project-stratified AUC | Threshold-free and prevalence-free; audit findings on scoring validity and project dependence | Gate 3 |
| D14 | Statistics *(rev. 3; finalized proposal 2026-10-20)* | Holm over {C1−C0, C2−C0, C2−C1, C2−C3} on DeLong's test for M1, with C2−C1 on commits whose same-file pool can fill B. The 21 projects are fixed strata: the confirmatory test and the primary CI (paired bootstrap stratified by project × label, 10K) condition on them. Generalising to other projects additionally requires the project-cluster bootstrap CI to exclude 0; S4 alongside. McNemar; TOST | DeLong1988, Dietterich1998, Lakens2017; audit. Validation: the cluster CI of a paired ΔAUC is about 2.6 × wider than the commit-level CI [V, design §11 item 2] | Supervisor |
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
| D26 | Label-quality audit *(new; revised 2026-10-20)* | 30 defective validation commits reviewed against their fixes. Report contradictions with checkable evidence and unresolved cases separately; no error-rate estimate. Record one AI rating per commit, then a human second rater on 10, blind | Gate 1; Risk 1; [02-datasets.md](02-datasets.md) §2a | — |
| D27 | Displayed test records *(new, second audit)* | Exclude the test records displayed during feasibility work ([02-datasets.md](02-datasets.md) §8) from the confirmatory sample by a rule fixed now; report the exclusion. Optionally identify the two unidentified commons-codec records by re-running the earlier selection once (it reads test labels but would output only commit IDs), if the supervisor approves | Conservative; the exposure involved no predictions | Supervisor |
| D28 | Split-era confound *(new, second audit)* | (a) Keep the original test split and the planned sample, add within-era analyses (S11) and the pilot's era-sensitivity check; or (b) sample clean test commits time-matched to the defective ones within each project. Recommended: (a), because (b) is limited by the few clean test commits from early periods and changes the inference target; revisit if the pilot shows era sensitivity | Commit age predicts validation labels with project-stratified AUC 0.836 [V] | Gate 3, supervisor |

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

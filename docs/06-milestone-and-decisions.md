# G. Acceptance Gates and Decisions to Finalize

Status: **pre-pilot revision 3.2 proposal, 2026-10-20**. The user authorized the confirmed code corrections and making C2−C3 primary. Methodological choices below still require Prof. Höll's approval before Gate 4; no approval, model access or inference result is implied. The scripts in `feasibility/` remain measurement aids. Superseded proposals and reasons are preserved in §3.

## 1. Acceptance gates (restructured after the external audit)

Work proceeds through five gates, each with a deliverable and pass criteria. Nothing before Gate 5 uses test-split labels or calls an LLM on the test split. What was already seen of the test split, and the rules that follow, are in [02-datasets.md](02-datasets.md) §8.

### Gate 1: Dataset acceptance (historical reconstruction complete; bounded human audit and permission open)

**Done** [V; [02-datasets.md](02-datasets.md) §2; [feasibility/audit_dataset.py](../feasibility/audit_dataset.py)]:

- All 27,319 commits of all 21 repositories exist, have one parent, and match `parent_hashes`. Churn is reproduced for 99.98% of commits in every split once `package-info.java` is excluded.
- Split chronology checked with author *and* committer time; duplicate Java changes checked with `git patch-id --stable`.
- Diff-size eligibility measured for every split (label-blind) and by class for train and validation.
- Ni2022 read in full: label/split descriptions documented. Released records show a strong age/label artifact; time-ordering followed by label redistribution is an inference, not a verified construction algorithm (§2 item 10).
- Label-quality audit of 30 defective validation commits, first rating ([02-datasets.md](02-datasets.md) §2a).
- Historical all-split manifest/audit: reconstruction 16,371 / 5,464 / 5,479 (train / valid / test); eligible 15,694 / 5,296 / 5,237; duplicate/displayed-record rules recorded in datasets §2. Legacy `manifest.csv` SHA-256 `9f487f7e…80af` lacks the required cap/tokenizer metadata and must not be used for inference.
- **Current train+validation manifest rebuilt [V, 2026-10-20]:** `manifest_trainvalid.csv`, 21,839 rows, SHA-256 `87da666f42247e70be6620de780512a2d1504577a49091872f26a453ff203a21`. Reconstruction/eligibility counts for these splits agree with the historical audit. Only exact train/validation pickles were allowed; no test file was opened and no label output was written. Input hashes, access guard and checks: [04-feasibility-demo.md](04-feasibility-demo.md) §7. Existing label files and original benchmark data are unchanged.

**Open:**

1. Retained per-case ratings for the fixed 30 positive validation commits and an independent human second rating on 10 (datasets §2a). Blank, independently verified packets are ready in scratch `pre_inference_human_audits\label`; **no ratings are completed**. The first AI pass cannot serve as a completed agreement study because individual ratings were not saved.
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

**Current correction and regeneration status (2026-10-20) [V].** BM25 uses sorted-term `math.fsum`; parser recovery/errors are recorded with nearest-line C1 fallback; cross-file `package-info.java` exclusion and fail-closed manifest/config/token checks are implemented. Earlier `f8b1fbb` artifacts/measurements above are historical. The fixed 60 validation IDs have now been regenerated into **two persisted 240-record builds**, hash seeds 1/31, B = 2,000, seed 0. All record fields except build time agree, normalized prompt SHA-256 `62665b4847a142d450a0324ba67210ab158eab90f19672083d0630a8239b924f`; max prompt 14,873 reference tokens, 0/60 match violations, 164 clean parses. Parent-source/masking checks cover all 60 saved cases. **348 tests pass**; Ruff and diff checks pass. Evidence and exact hashes: feasibility §7. Blinded 20-case relevance packets are ready with blank ratings. Human prompt reading and both audits remain open; do not count automated checks as human validation.

### Gate 3: Engineering pilot (validation split; not evidence about RQ1–RQ3)

| Item | Choice |
|---|---|
| Sample | 60 validation commits: 30 defective and 30 clean, seeded, from at least 4 small or medium projects; frozen in [../configs/pilot_commits.txt](../configs/pilot_commits.txt) |
| Conditions | C0–C3 (seed 0), B = 2,000; repeat C0, C2 and C3 independently: 60 × 7 = 420 calls. This supersedes C2@8,000 in the engineering pilot so the primary pair is repeated without increasing calls |
| Model | GPT-6 Luna through Copilot SDK is a feasibility candidate, not an implemented or account-verified backend. No direct API credentials/access are assumed |
| Analysis | Engineering/descriptive only; no confirmatory hypothesis tests or tuning for higher prediction scores |
| Size and cost | Measured corrected seven-call schedule: **1,574,501 canonical input reference tokens** across 420 calls; excludes provider wrapping, reasoning, outputs, retries and capability calls. The former 1.93M figure is superseded. Copilot allowance, reasoning/cache usage, rate limits and billable overage are account-specific and unverified; obtain a capped estimate before any model call |

**Steps:**

1. **No-inference access preflight, partly complete.** Compatible pinned SDK/runtime and protocol verified below. Historical local probes reported false authentication and model/quota queries returned `Not authenticated`. **The user has since confirmed Copilot access and asked to defer this issue.** No further login action is requested in this phase. SDK authentication, exact account Luna ID/reasoning options and quota/billing checks are deferred to execution setup; user-confirmed access is not an independently observed SDK result.
2. **Local input/audit prerequisites, automated part complete.** Metadata-bearing train+validation manifest and both frozen prompt builds pass the checks above. Have independent raters complete the prepared 20-commit blinded relevance and bounded label audits. Lock blinded relevance ratings before a human reads identified side-by-side C0–C3 prompts for 20 validation commits (or assign another reviewer). Use the coordinator key to locate these same 20 in `pilot_contexts_hash1.jsonl`; no test access is required.
3. **Access-control feasibility.** Verify SDK `mode="empty"`, system-message replacement, explicit empty tools/MCP, disabled discovery/memory/skills/session store/compaction, fresh sessions, deny-all permissions and complete event capture with the compatible runtime. Do not implement a provider based only on source signatures. SDK/CLI metadata may establish configuration support; only an approved capped model capability check can establish runtime behavior and observability.
4. **Capped capability check (requires user-approved cost/run size).** About 20 requests, covering all four conditions on validation prompts, to check exact supplied messages, output parsing, model selection, extra calls/tool attempts, usage and isolation. Reject unaccounted context/tool calls/model switching; preserve failures. If likelihoods are absent, propose emitted-answer IPW MCC (D13); do not fabricate probabilities or silently change the metric. Twenty calls do not validate a 98% reliability rate.
5. **Engineering pilot (separate authorization).** After the access and metric decisions, implement/test the single verified backend with resume/retry/request-identity caching. Run the 420 calls in seeded random order (2027), fresh session per request, including independently repeated C0/C2/C3. Log all raw events/responses, failures, exposed settings, usage and model identities; cached first calls must not satisfy independent repeats. Rationale/probe calls are optional separately counted additions, not hidden inside 420.
6. **Pilot report in the existing Gate 3 record.** Record per-condition answer/score validity, intended/common-pair counts, repeat flips, context/token/latency distributions, cost reconciled with available account telemetry, paired project uncertainty, and project/time support (design §11 S11). AUC only if valid scores exist; no prevalence calibration claims on this balanced sample. Report unresolved telemetry/isolation limits and the go/no-go for protocol freeze.

**Readiness (2026-10-20): NO-GO for the 20-request capability check at present.** Local inputs and SDK/runtime handshake pass. Copilot access is user-confirmed; further SDK authentication/model/effort/quota checks are deferred to execution setup. Human reviews and explicit authorization for a concrete maximum of 20 requests and cost remain open. No provider is implemented. Effective session isolation, supplied/effective-message observability and actual usage are deliberately **not yet verified**: the capability check is intended to test them, and no session was created in this preflight. Full confirmatory protocol approval is Gate 4; it is not a completed prerequisite for a technical capability check. The label/era risks apply even if engineering checks pass.

**Copilot SDK feasibility evidence (2026-10-20; source-supported unless marked observed):**

| Requirement | Evidence and limit |
|---|---|
| Stable source identity | Python `github-copilot-sdk==1.0.22`, tag commit `ffd25c775742f73e13a492093be0287d7885123f`; [release](https://github.com/github/copilot-sdk/releases/tag/v1.0.22), [PyPI](https://pypi.org/project/github-copilot-sdk/1.0.22/). **Observed:** published wheel installed in isolated scratch `copilot_preflight\sdk`, SHA-256 `a3abdcf5145e096eebbfe3ab04179b0ce03922431e62eb6c52b6cfcb70bad948`; project requirements/environment unchanged |
| Non-agentic input control | Tagged and installed [client](https://github.com/github/copilot-sdk/blob/v1.0.22/python/copilot/client.py) and [empty-mode implementation](https://github.com/github/copilot-sdk/blob/v1.0.22/python/copilot/_mode.py) support system replacement and disabling environment/discovery, memory, skills, session store and plugins. Client startup in empty mode with isolated storage passed. Explicit empty tool/MCP lists, fresh sessions, disabled compaction and deny-all permissions are still required; **no session was created**, so effective session/runtime isolation is unverified |
| Model and decoding | GitHub [supported-client table](https://github.com/github/docs/blob/main/data/tables/copilot/model-supported-clients.yml) lists Luna for CLI. The inspected SDK exposes model/reasoning selection but no temperature, top-p, sampling seed or token log-probability surface. Do not claim temperature 0, valid YES+NO scores, or an immutable upstream snapshot |
| Usage and observability | [Usage/billing](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/usage-and-billing), [events](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/streaming-events) and [OpenTelemetry](https://docs.github.com/en/copilot/how-tos/copilot-sdk/observability/opentelemetry) document telemetry. Capture events live; complete final-provider messages, actual charges and optional usage fields remain unverified. Missing usage is not zero |
| Local execution/authentication [observed] | Existing npm CLI 1.0.36 remains unchanged; help/login-help work with the required sandbox access (earlier restricted `spawn EPERM` is superseded). SDK probes in normal and isolated empty modes both return `is_authenticated=false`. Actual `models.list` and `account.getQuota` calls fail JSON-RPC −32603, `Not authenticated`; this does **not** establish that Luna is unavailable. SDK session/model request count: **0** |
| Runtime compatibility [observed] | Published wheel pins runtime **1.0.98**. Archive SHA-256 `10516fec874797519e2ece05e90bcd627327c42c688aa21f44b7d13fa1130036`; runtime reports version 1.0.98, protocol **3**, handshakes pass in both modes. Initial downloader rename failed; the same checksum-verified archive was extracted into isolated `runtime`, and probes used its explicit path. Compatibility does not depend on old global CLI 1.0.36 |
| Decision | Plausible **binary-output** technical-pilot route once account/cost/human prerequisites pass; **not established for likelihood-based AUC**. No provider or direct-API fallback added. Prof. Höll must accept binary metric, unexposed decoding defaults and alias-drift limits if this route is used |

Observed evidence is in scratch `copilot_preflight\metadata_result.json` and `metadata_queries_result.json`; source scripts `metadata_preflight.py` and `metadata_queries.py` allow metadata RPCs only. SDK/archive hashes and dependency versions are retained there. No credentials, device codes or repository Git token were reused. The user's later confirmation of access is recorded separately from these historical failed-auth results. Preserve those results when metadata checks are eventually resumed; no further sign-in request is part of the current phase.

**Go/no-go criteria:**

| Criterion | Threshold |
|---|---|
| Access/isolation | Compatible pinned SDK/runtime, account Luna access, supplied/effective context audit, no unaccounted model/tool calls; unresolved controls must be decided before proceeding |
| Valid two-candidate scores for M1 | ≥ 98% in each core condition for AUC; otherwise D13's proposed binary MCC route, approved before test inference |
| Masking and token-match checks | No masking violation; every match within tolerance or explicitly flagged `line_limit` with the prespecified sensitivity (no silent pass) |
| Tree-sitter enclosing ranges (manual check) | ≤ 10% wrong |
| Relevance audit | Fixed 20 commits, retained blinded ratings, both raters' mean paired rating difference favours C2; if not, review implementation and restrict the claim or obtain a documented protocol revision (§5.7) |
| Invalid outputs | ≤ 2% |
| Label-recall probe (optional screening) | Above-chance recall is a warning; negative recall never establishes absence of contamination or automatically passes a validity gate |
| Projected cost | Within the agreed budget |

### Gate 4: Protocol freeze

The eligibility cap, budgets, access route/model identity limits, metric, sampling/weights, failure handling and analysis scripts (tested on synthetic/validation data) are fixed. A practical margin is justified and agreed **if equivalence is claimed**; otherwise the plan explicitly omits equivalence. Prof. Höll approves, and the plan is tagged `analysis-plan-v1` before any test-split call. SDK feasibility alone is not protocol approval.

### Gate 5: Main study

Test-split runs and analysis exactly as frozen; every deviation is reported.

### Tooling (agreed with the audit)

| Need | Choice | Reason |
|---|---|---|
| Execution | Existing `python -m jitctx` CLI with TOML config: `build-manifest`, `make-contexts`, `summarize`; runner/evaluation commands are not implemented | Explicit, testable, repeatable |
| Environment and checks | Pinned [../requirements.txt](../requirements.txt) (`pip`; `uv` is not installed on this machine), `pyproject.toml`, `pytest`, `ruff` | Exact versions; tests before any paid call |
| Java structure | `tree-sitter` 0.24.0 with `tree-sitter-java` 0.23.5 (0.26.0 crashed with access violations on Windows) | Enclosing methods for C1 |
| Retrieval | The project's own BM25, unit-tested and cross-checked against a reference implementation | Transparent and already specified |
| Model access | Assess Copilot SDK first as requested; implement one backend only after Gate 3 access/control feasibility. No direct-API access or provider is assumed | Controlled inputs, traceable usage, explicit metric capability |
| Outputs | Immutable JSONL or Parquet, a small SQLite run manifest, SHA-256 of every prompt and input | Audit trail |
| Version control | Git and GitHub for code, configs, and documents; data and clones outside Git and OneDrive | Reproducibility without syncing large files |
| Not used | LangGraph, LangChain, autonomous agents | They make inputs and cost vary per commit, which the fixed-prompt design forbids. Use them only if adaptive retrieval becomes a separate condition |

An AI coding assistant may help develop the experiment. During inference, any SDK/runtime must be reduced to the fixed-input non-agentic controls verified at Gate 3; its normal coding-agent behavior is not an experimental condition.

## 2. Decisions to finalize before writing production experiment code

Status of every item: **Open.** Each needs a recommended default agreed with your supervisor. Record the outcome in the decision log (§3). Items marked *(rev. 2)* changed in the Phase 2 review and *(rev. 3)* after the external audit; the reasons are in the [revision log](README.md#revision-log).

| ID | Decision | Recommended default | Evidence or rationale | Depends on |
|---|---|---|---|---|
| D1 | Dataset *(rev. 3)* | JIT-Defect4J labels, splits, and IDs, with code reconstructed from the Apache Git repositories; **conditionally accepted** until Gate 1 closes. JIT-Defect-Extended only for cross-checks and comparability. Fallback: ApacheJIT 2010–2017 with Hadoop merged or excluded | [02-datasets.md](02-datasets.md) §6; all-project audit [V] | Gate 1 open items |
| D2 | Unit and label | Commit; `is_buggy_commit` | Verified schema | — |
| D3 | Split usage | Test = confirmatory only; validation = pilot and template development; train = baselines B1–B3 | Leakage control L6 | — |
| D4 | Eligibility *(rev. 3)* | Reconstruction passes (numstat over Java files except `package-info.java`); at least one in-scope change; **T(C0) ≤ 16K tokens** (o200k_base); unique patch ID within the split, and no patch already in an earlier split (train < validation < test). Inference target: eligible Java changes, benchmark label as observed proxy | All projects: 16K keeps 85–87% of defective and ~98% of clean train/validation commits (12K: 80–83% of defective); largest cap that fits 32K-token windows with the 8K RQ3 context [V] | Supervisor |
| D5 | Sampling *(rev. 3.2)* | All eligible defective + about 2 × clean proportional by project, N ≈ 1,200. Retain exact inclusion probabilities after integer allocation; weight 1/f_p for clean records and use weighted AUC if within-class fractions differ | Scarce positives; enriched sample is not natural prevalence (design §8) | Gate 3, Prof. Höll |
| D6 | Prompt/output *(rev. 3.2)* | Identical Java diff plus context block/header/order; no message or metadata. Emit YES/NO; tokenization and two-answer scores only if the verified route exposes them. Score and emitted-answer validity are separate | Design §4; no verbal confidence substitution | Gate 3, D13 |
| D7 | C0 diff *(rev. 3)* | `git diff -U3 -M <parent> <commit> -- '*.java' ':(exclude)*package-info.java'` | The benchmark's change metrics use this scope (99.98% match) [V]; a documented scope decision, not proof about the labels | — |
| D8 | C1 definition *(rev. 3.2)* | Parent same-file source, diff lines masked; enclosing lines first then nearest. Log parser recovery/exception and use nearest-line fallback without untrusted boundaries; preserve source/masking | Confirmed code correction; design §5.2 | Human prompt check |
| D9 | C2 retriever and budget *(rev. 3.2)* | Existing BM25, parent Java pool excluding changed files and package-info, token/line-bounded windows; B = 2,000 (alternative 1,000). Bounded blinded relevance audit; failed audit means narrower operational claim or supervisor-approved revision, not automatic retriever substitution | Design §5.7; historical fill rates require updated artifact checks | Gate 2 checks; Prof. Höll |
| D10 | C3 control | Same pool; seeded random; T(C3) = T(C2) ± 2%; seed 0 for all models, seeds 1–2 for M1 | Token matching; variability | — |
| D11 | Budget series/add-ons *(rev. 3.2)* | RQ3 1K/8K estimates, extra C3 seeds/models and JITLine are optional scoped extensions after core feasibility, not pilot prerequisites. Fix any extension sample before test outcomes; no additional conditions | Preserve completion scope and one primary comparison | Budget/time, Prof. Höll |
| D12 | Model/access *(rev. 3.2)* | Hosted inference only. GPT-6 Luna via Copilot SDK is an unverified candidate; check published SDK/runtime compatibility, account access, isolated effective inputs, telemetry, unexposed decoding settings and model-alias drift before adding a backend. One primary model; additional models optional | Gate 3 dated feasibility matrix; no provider implemented or direct API access assumed | No-inference preflight, Prof. Höll; user approves paid run |
| D13 | Metrics *(rev. 3.2)* | ROC-AUC only with valid two-answer scores in ≥98% of each core condition; otherwise proposed IPW MCC on emitted answers. AUC/PR-AUC/calibration unavailable for binary-only SDK access. Decide and approve before test calls; retain invalid answers/scores separately | Design §§4, 10; Copilot likelihood scores not exposed in inspected interface | Gate 3, Prof. Höll |
| D14 | Primary comparison/statistics *(rev. 3.2)* | Sole primary C2−C3, M1/B=2,000/seed0, two-sided paired project-cluster bootstrap 95% interval (10K, analysis seed2027), leave-one-project-out and required era sensitivity. Other core contrasts are secondary estimates with pointwise intervals, not significance claims. DeLong/McNemar conditional diagnostics only; no representativeness claim from 21 Apache projects | User-requested primary contrast; independent audit; design §11 supersedes old four-test DeLong/Holm proposal (§3) | Prof. Höll before Gate 4 |
| D15 | Failures *(rev. 3.2)* | Transport retries ≤2, identical request, every attempt logged; separate score/answer validity, common-pair denominators and categorized failures. All-YES/NO and extreme-score S5 scenarios are sensitivity stresses, not sharp bounds. Never recode invalid to clean | Design §11.6; missingness may differ by condition | Gate 3, Prof. Höll |
| D16 | Contamination *(rev. 3.2)* | Cutoff/source disclosure, optional label-recall/rationale screening, required S11 project/era sensitivity. No negative probe establishes absence, and C2−C3 may trigger different memorized associations | Public labels/code predate candidate models; design L10/L15 | Prof. Höll accepts residual limitation |
| D17 | Pre-registration and budget | Git tag `analysis-plan-v1` (optionally OSF) before test inference; hard USD cap per model | Wagner2025; cost model | Supervisor |
| D18 | Data permission | Email the JIT-Fine authors; publish manifests only | No LICENSE file in the repo | — |
| D19 | Positioning against JIT-LSM | Read its full context experiment before freeze; retain the bounded contribution in literature §9, with no universal first claim | Closest prior work; full paper not yet read | Library access |
| D20 | Use of JIT-Defect-Extended and JIT-LSM files *(new)* | Commit IDs and cross-checks only; never read by the prompt builder; never redistributed | Labels embedded in records and paths; no license [V] | — |
| D21 | Comparability baseline B5 *(new)* | Run only if Huang2026 reports results on its 1,000-commit balanced subset | Without published per-subset numbers the comparison is empty | D19 |
| D22 | Supervised baseline B3 | JITLine remains optional and time-boxed after core feasibility; B1/B2 are sufficient pilot anchors | Package exists, runnability unverified | Budget/time |
| D23 | Pure location contrast | No C1b: keep the user's four conditions. C2−C1 compares strategies; a pure source-location claim is outside current scope | C1/C2 differ in pool, ranking and chunking | No change authorized |
| D24 | SESOI *(rev. 3.2)* | Justify practical δ for the chosen metric substantively before test inference; do not derive it solely from a split-biased baseline gap, API noise or attainable power. Without approval, no equivalence claim | Design §11; old raw-score-correlation MDEs withdrawn | Gate 3, Prof. Höll |
| D25 | Tooling | Existing Python CLI/TOML, pinned requirements, pytest/Ruff, tree-sitter; one backend after feasibility. No new framework/provider dependency added here | Fixed-input architecture retained | Gate 3 |
| D26 | Bounded label audit *(rev. 3.2)* | Fixed 30 positive validation IDs, retained first ratings; human second rater on 10 selected by seed2027, blind to first ratings/predictions, 20-minute/case limit. Preserve evidence, search limits, original ratings and adjudication; report agreement/κ with caveats, no dataset error rate or primary relabelling | Gate 1; authoritative plan in datasets §2a. Human completion remains open | Human rater, Prof. Höll accepts limitation |
| D27 | Displayed test records | Proposed confirmatory exclusion of known displayed IDs; currently flagged, not enforced in eligibility. If approved, implement/test the exclusion before freeze. No reidentification of unknown records or additional test-label access in this work | Exposure record in datasets §8; no predictions made | Prof. Höll; separate user authorization for any new test access |
| D28 | Temporal scope *(rev. 3.2)* | Retain original split for qualified historical SZZ-benchmark comparison; required project×era sensitivity using training-time tertiles, supported-cell counts and coverage (design §11 S11). No C2−C3 immunity claim. Weak overlap/conflicting effects constrain interpretation; prospective deployment claims would need a separately approved design | Age AUC 0.836; actual chronological Kamei refit 0.752, not old filtered-window 0.771 | Prof. Höll before Gate 4 |

## 3. Decision log template

**2026-10-20, pre-freeze revision (approval pending).** At the user's request, the independent audit supersedes these **proposals**, not approved decisions: D14's four DeLong/Holm tests and commit-primary CI become one primary C2−C3 with paired project uncertainty; secondary contrasts become estimation-only. D9's automatic `git grep` fallback is withdrawn to avoid changing the manipulation solely because a relevance check fails. D12's assumed direct-API scoring route is replaced by Copilot SDK feasibility assessment; no provider is selected. D24's raw-score-correlation MDE/benchmark-gap justification is withdrawn. Reasons and current alternatives are in design §§5.7, 7–11 and Gate 3 above. Prof. Höll's approval has not been obtained; historical audit responses describe the prior state.

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

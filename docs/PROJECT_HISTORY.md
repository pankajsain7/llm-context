# Project History and Handoff Notes

The current handoff: state, decisions with their reasons and status, lessons, and the next step. Working rules are in [../AGENTS.md](../AGENTS.md); methodology and evidence are in the linked documents. Link to them rather than copying them here.

**Maintenance:** update this file in place at the end of a meaningful session. Replace outdated statements, delete anything no longer useful, and keep confirmed decisions separate from proposals. Do not append a diary. Last updated: 2026-10-21.

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
- **The released split has a verified age/label artifact** (validation project-stratified age AUC 0.836). Label redistribution is an inference; construction code is unavailable. No context contrast, including C2−C3, is immune. See datasets §2 item 10, design L15 and D28.
- **Hosted inference only; no local hosting** (user decision, 2026-10-19). GPT-6 Luna/Copilot SDK is now the requested feasibility candidate; direct API access is not assumed. No backend is implemented or account-verified (D12).

## 3. How the design got here

1. **Phase 1, research package.** JIT-Defect4J was chosen over ApacheJIT, ReDef, and Defectors, and conditions C0–C3 were defined with a random control.
2. **Phase 2, self-review.** JIT-LSM showed that context for LLM-based JIT defect prediction is not new, so the claim was narrowed to a controlled comparison. JIT-Defect-Extended carries labels in every record and is therefore never used as input.
3. **Phase 3, two external audits.** Evidence from all 21 projects replaced the four-project estimates, the prototype bugs were fixed and tested, and the work was organised into acceptance gates. The point-by-point verdicts are in [README.md](README.md#external-audit-response).
4. **Second external audit and Gate 2.** Test-exposure record corrected; two more filling defects fixed; Ni2022 read; the split's class stratification found; hosted-only models; the `jitctx` context builder implemented and tested ([README.md](README.md#second-external-audit-response)).
5. **Third external audit (pre-pilot).** Cross-split duplicate rule, label-audit claims narrowed (no error rate), C2/C3 matching checked on every pair, Gate 2 checks done by the AI assistant, statistics finalized as a proposal, split numbers scripted, pilot inputs frozen and rebuilt deterministically ([README.md](README.md#third-external-audit-response)).

**Current priority (user-requested, 2026-10-20):** C2−C3 is the sole primary contrast. Other core comparisons are secondary estimates; budget/model extensions are optional scope. This supersedes the earlier proposal to retain four confirmatory tests. The updated methodology remains subject to Prof. Höll's approval, not retroactive approval of earlier AI decisions.

## 4. Key decisions and why

Full list: [06-milestone-and-decisions.md](06-milestone-and-decisions.md) §2. **Nothing below is approved research policy.** Every item is a proposal until the supervisor approves it and the protocol is frozen at Gate 4.

| Topic | Proposal | Why | Status |
|---|---|---|---|
| Dataset | Retain JIT-Defect4J and four conditions (user constraint); scientific acceptance remains conditional | Historical reconstruction works; labels/split remain limited | Human audit, permission and supervisor acceptance open |
| Inference target | Eligible Java changes of the test split; the label is an observed SZZ proxy | Labels are noisy (Example 1) | Proposed |
| Input scope | Java files except `package-info.java` | Matches the benchmark's change definition; not proof about the labels | Proposed (D7) |
| No commit messages | Excluded from every prompt | The brief defines C0 as diff only; issue keys are a memorization cue | Proposed (D6) |
| Fixed prompts, no agents | One non-agentic prompt per condition | Isolates *what* context helps; JIT-LSM mixes context with agent search | Working rule ([../AGENTS.md](../AGENTS.md)) |
| Volume control | C2 versus token-matched C3 is primary | Operational selection-policy contrast; not isolated semantic relevance | User-requested priority; protocol approval pending |
| Budget | B = 2,000 (alternative 1,000); series 1,000 / 2,000 / 8,000 | Same-file fill measured at about 73% (2,000) and 84% (1,000) | **Pending approval** (D9, D11) |
| Diff size limit | 16,000 tokens | Keeps 85–87% of defective commits; fits a 32K-token window | **Pending approval** (D4) |
| Sample | All ≈ 400 eligible defective commits plus 2 × clean, proportional by project (N ≈ 1,200) | Positives are scarce (8.7%) | Proposed (D5) |
| Primary metric | ROC-AUC if two-candidate scoring is validated, else MCC | Threshold-free and prevalence-free, but only if both answer likelihoods are measurable | Proposed; conditional on Gate 3 (D13) |
| Statistics | Paired project-bootstrap intervals for primary C2−C3; other contrasts estimation-only; required project×training-era sensitivity | Fixed-project terminology does not remove dependence; old raw-score-correlation MDEs withdrawn | Proposed D14/D28; Prof. Höll approval pending |
| Models | One primary hosted model; assess GPT-6 Luna/Copilot SDK before provider implementation | Isolated SDK/runtime protocol verified; access user-confirmed, further SDK account/model/quota checks deferred to execution setup; session isolation/telemetry unverified, no likelihood surface found | D12/D13 pending; no direct API assumption |
| Era confound | Retain released split only for qualified SZZ-benchmark target; required supported-cell/coverage reporting | Age AUC 0.836; true chronological Kamei refit 0.752, old 0.771 only a filtered window | Proposed D28 |
| Displayed test records | Exclude from the confirmatory sample | Conservative; no predictions were made | Proposed (D27) |

## 5. Lessons from corrected mistakes

1. **Check the newest related work before claiming novelty.** JIT-LSM and LLM4Reg each invalidated an earlier claim.
2. **Fix parameters only on evidence from all projects.** The 4-project sample overstated defect retention (93% vs 80–83%) and same-file fill rate (83–86% vs 69%).
3. **Label guesses as assumptions and test them when cheap.** The "SVN date artefact" explanation was refuted by committer dates.
4. **Unit-test retrieval code before measuring with it.** The prototype had three silent bugs.
5. **Don't infer the label scope from the metric scope.** The line counts show how the benchmark defines a change, not what its labels depend on.
6. **State data exposure exactly.** "Test labels were not read" was true for one script, not for the project. Keep one exposure record and add to it.
7. **Test edge cases, not only typical inputs.** A greedy fill that stopped at one oversized line passed 129 tests.
8. **Separate observation from mechanism.** Label/era associations are observed; class redistribution explains them plausibly, but the split code is unavailable and the exact construction remains inferred.
9. **Pin native libraries that crash.** `tree-sitter` 0.26.0 caused access violations on Windows; 0.24.0 works.
10. **Save the code behind every [V] number, and per-item ratings.** The split numbers, the pilot selection, and the label-audit ratings had no saved code or record; one number (0.844) could not be reproduced and was withdrawn.
11. **A count of unverified judgements is not an error rate.** The label audit's "≥ 17%" mixed AI ratings with an incomplete search; report checkable cases and unresolved ones instead.
12. **Record exactly which code built an artifact.** The first pilot contexts named a commit without the builder; builds from a modified tree are now marked `-dirty`.

## 6. Current state and next steps

**Implemented (2026-10-20).** Sorted-term `math.fsum` BM25; explicit parser ERROR/MISSING/exception diagnostics with deterministic nearest-line fallback; cross-file `package-info.java` exclusion; manifest cap/tokenizer metadata and fail-closed config/token checks. Chronology diagnostics refuse the test pickle and perform a real author-time/SHA repartition with training-only refits. Existing feasibility scripts now generate reproducible blank human audit packets and refuse overwriting ratings. No provider or project dependency added; the SDK is isolated outside the thesis environment.

**Observed inputs/checks.** Train+validation manifest regenerated: 21,839 rows, eligible 15,694/5,296, SHA-256 `87da666f…3a21`; exact input-pickle access guard, no test file. Frozen 60 validation IDs persisted in two fresh hash-seed 1/31 builds: 240 records each, identical except build time; normalized prompt digest `62665b48…924f`, 0/60 match violations, max prompt 14,873 reference tokens, 164 clean parses. All 60 saved cases pass candidate/parent, exact-prompt, parent-source, masking and budget checks with evaluation-file access blocked. **348 tests pass** (203 current, 145 feasibility); Ruff and diff checks pass. Full hashes, source identity, commands and scratch verification scripts/reports: [04-feasibility-demo.md](04-feasibility-demo.md) §7. Revised 420-call schedule totals 1,574,501 canonical input reference tokens, not provider usage/cost. Earlier chronology refit remains 0.752/0.591/0.767 (Kamei/history/size). No model requests, paid inference, pilot or new test-data access occurred.

**Protocol/human work.** Revision **3.2 proposal** remains unapproved: sole primary C2−C3, paired project uncertainty, required project/time sensitivity and bounded audits. Scratch `pre_inference_human_audits\label` contains original 30 and independent 10 evidence packets; `relevance\rater1` and `rater2` contain 20 blinded cases. Integrity/seed checks pass (242 output hashes, 111 candidate/linked Java patches); **all ratings are blank**, no human results invented. Keep `relevance\coordinator_only` private. Lock blinded relevance ratings before showing identified C0–C3 prompts to the same people, or assign a separate technical reviewer. SZZ uncertainty, temporal artifacts and project dependence remain; equivalence requires an approved substantive margin.

**Inference status.** Isolated scratch `copilot_preflight`: published Python SDK **1.0.22**, wheel-pinned runtime **1.0.98**, protocol **3** verified in normal and isolated empty modes. Downloader rename failed; the same checksum-verified archive was extracted into isolated `runtime`, then used by explicit path. Historical auth probes reported false; model-list/quota calls returned `Not authenticated`. **The user subsequently confirmed Copilot access and asked to defer this issue; do not request login again in this phase.** SDK authentication/model/quota checks are deferred to execution setup, not marked independently verified. Existing global CLI 1.0.36 is unchanged. No sessions/model requests created. Exact Luna ID/reasoning choices, usage limits/cost and effective session controls/telemetry remain unverified. No temperature/top-p/seed/logprobs surface found. Binary MCC and alias/default-setting limitations need supervisor acceptance. Evidence is in Gate 3.

**Go/no-go:** **NO-GO for the 20-request capability check at present:** human prerequisites and explicit capped run/cost authorization remain open. Access is user-confirmed; outstanding SDK metadata checks are deferred to execution setup. SDK metadata support is not effective-session proof; that is the capability check's purpose. Do not implement a provider solely from signatures. Confirmatory approval remains Gate 4, before test inference.

**Next actions, in order:**

1. Distribute only participant audit folders: label primary30 to one rater, independent10 to an independent human; relevance rater1/rater2 to independent raters (at least one human). Retain original submissions and adjudicate separately. No AI may fill human ratings. After blinded ratings are locked, have a human review the same 20 identified C0–C3 prompts using the coordinator key and saved JSONL. Record issues without tuning against prediction results.
2. Defer SDK authentication/account metadata checks until execution setup, following the user's instruction. At that stage verify exact Luna ID/reasoning choices, quota and applicable pricing/overage cap with metadata only, preserving historical failed-auth evidence. Do not reopen the sign-in request during current audit preparation.
3. Use the regenerated manifest and inputs already verified; no further rebuild is needed unless code/config changes. Legacy `manifest.csv` is rejected and remains historical. Later-fix evidence is evaluation-only and never enters inference.
4. Prof. Höll: approve D12/D13 access/metric limits, D14 primary/uncertainty, D28 temporal scope, D4/D5/D9 cap/sample/budget, D26 label limitations, D27 displayed-record exclusion, and D24 only if equivalence is claimed. D18 permission and D19 full JIT-LSM reading remain open.
5. Obtain user approval for the capped capability check (~20 requests), then verify runtime behavior before implementing/testing one backend. The 420-call validation engineering pilot requires separate run/cost authorization. No test inference before Gate 4.

## 7. Practical notes

- **Tools:**
  - Git is not on PATH; use `C:\Program Files\Git\cmd\git.exe`.
  - Python virtual environment: `C:\Users\psain\thesis-scratch\.venv`, pinned by [../requirements.txt](../requirements.txt) (`uv` is not installed).
  - Repository: `github.com/pankajsain7/llm-context` (`main`). Push rules: [../.github/copilot-instructions.md](../.github/copilot-instructions.md).
- **Scratch folder:** current `manifest_trainvalid.csv`, `pilot_contexts_hash1.jsonl`/`hash31.jsonl`, access/provenance reports, `pre_inference_validation.json`, `pre_inference_recheck.json`, `human_audit_validation.json`, `pre_inference_human_audits/`, `copilot_preflight/`; exact evidence/commands in feasibility §7. Existing `repos/` (21 clones), `jitfine/`, `jitext/` (label-bearing), `apachejit/`, `papers/`, `labels_trainvalid.csv`, `label_audit/`, legacy `manifest.csv` and old pilot/valid200/range artifacts remain. Do not overwrite historical evidence or submitted ratings.
- **Commands** (set `$env:PYTHONPATH` to the repository's `src`):
  - Manifest: `python -m jitctx build-manifest --root C:\Users\psain\thesis-scratch --splits train valid --config configs/contexts.toml --out ...\manifest_trainvalid.csv`. Do not add test to the pre-pilot rebuild.
  - Contexts: `python -m jitctx make-contexts --manifest ...\manifest_trainvalid.csv --repos ...\repos --sample 20 --with-prompts --out ...\contexts.jsonl`, then `python -m jitctx summarize ...\contexts.jsonl`.
  - Tests: `python -m pytest` in the repository (integration tests need the manifest and clones; `-m "not integration"` skips them); prototype tests: `python -m pytest feasibility -q -p no:cacheprovider`.
  - Historical full audit (not a routine pre-pilot check): `python feasibility/audit_dataset.py --root ...`; it deserializes test data, so do not rerun under the current no-new-test-access constraint.
  - Pilot input regeneration and normalized hash comparison: feasibility §7. Extra budgets are optional scope, not a required engineering-pilot rebuild.
  - Split evidence and baselines: `python feasibility/split_analysis.py --root ...`; Gate 2 checks: `python feasibility/gate2_checks.py ranges|relevance ...`; label re-check: `python feasibility/label_audit.py --root ... --recheck project:sha`. All commands: [04-feasibility-demo.md](04-feasibility-demo.md) §1.
  - The manifest rebuild takes about 30 minutes.
  - Use `-B`/`PYTHONDONTWRITEBYTECODE=1` and no pytest/Ruff cache; do not generate throwaway artifacts.
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
| Full experimental specification (revision 3.2 proposal) | [03-experimental-design.md](03-experimental-design.md) |
| Real examples, measurements, hashes, reproduction commands | [04-feasibility-demo.md](04-feasibility-demo.md) |
| Ranked risks | [05-risks.md](05-risks.md) |
| Gates, tooling, decisions D1–D28 | [06-milestone-and-decisions.md](06-milestone-and-decisions.md) |
| Test-split exposure record | [02-datasets.md](02-datasets.md) §8 |
| Bibliography with verification levels | [references.md](references.md) |
| Context builder, CLI, configuration, tests | [../src/jitctx/](../src/jitctx/), [../configs/contexts.toml](../configs/contexts.toml), [../tests/](../tests/) |
| Prototype scripts and label-free outputs | [../feasibility/](../feasibility/) |

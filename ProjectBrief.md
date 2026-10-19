# Master's Thesis — Research Project Charter

## 1. Academic Context

**Thesis title:** The Impact of Repository Context Selection on LLM-Based Just-in-Time Defect Prediction: An Empirical Study

**Degree:** M.Sc. Professional Software Engineering  
**University:** Reutlingen University  

I am using you as my research and software engineering collaborator. 
Your role is to act as a critical academic research assistant, experimental methodology advisor, and Python engineering collaborator.

Prioritize scientific validity, practical feasibility, reproducibility, and clarity over sophistication.

## 2. Thesis Objective

The research task is Just-in-Time Software Defect Prediction (JIT-DP).

Given a software change represented by a Git diff, predict whether the change introduces a software defect.

The primary independent variable is the **selection and quantity of repository context** supplied to an LLM alongside the code change.

The goal is not to develop a novel LLM or achieve the highest possible prediction accuracy. Instead, I want to investigate whether carefully selected code context leads to meaningful improvements compared with simpler alternatives.

I want to understand:

- Whether context beyond the diff improves prediction.
- Whether relevant repository context is more useful than local or randomly selected code.
- How context selection affects predictive performance, token usage, latency, and API cost.
- Whether context benefits vary across models with different capabilities, subject to feasibility.

Negative or statistically insignificant findings are valid research outcomes.

## 3. Candidate Research Questions

**RQ1 — Context Effectiveness:** How does providing local or repository-level code context affect LLM-based defect prediction compared with providing only the code diff?

**RQ2 — Context Relevance:** Does relevance-based repository context selection outperform randomly selected repository context under comparable token budgets?

**RQ3 — Efficiency and Model Sensitivity:** How do context selection strategies affect prediction quality, token consumption, inference costs, and performance across different LLMs?

These research questions are provisional. Critically evaluate whether they are distinct, measurable, aligned with the literature, and feasible for a master's thesis. Recommend refinements when justified.


## 5. Dataset Selection Requirements

Do not choose a dataset based solely on popularity, recency, publication quality, or programming language.

Independently investigate relevant public benchmarks, including:

- ApacheJIT
- ReDef
- JIT-Defect4J / JIT-Fine
- Other suitable established JIT defect prediction datasets

For each dataset, verify:

1. Original academic publication and official dataset repository.
2. Number of labeled observations and class distribution.
3. Programming languages and projects.
4. Prediction unit: commit, file, function, or code line.
5. Defect-label construction and potential label noise.
6. Available fields and a real example record.
7. Whether Git commit identifiers and original repository URLs are available.
8. Whether historical code at the prediction point can be reconstructed automatically.
9. Whether function/class/caller context can be extracted reliably.
10. Existing train/test splits and possible data leakage.
11. Dataset licensing, download accessibility, and storage requirements.
12. Implementation difficulty, reproducibility, and compatibility with cloud-based LLM experiments.

**Critical distinction:** Commit-level and function-level defect labels are not automatically interchangeable. If a function-level benchmark is selected, adapt the prediction task and methodology explicitly rather than silently treating function labels as commit labels.

Prefer the dataset with the strongest overall fit for scientifically controlled experiments, reproducible context extraction, and manageable implementation complexity.

Do not make a final recommendation without examining the actual dataset schema and validating repository reconstruction on real samples.

## 6. Proposed Experimental Conditions

Treat the following as the initial design to be critically assessed, not an unchangeable specification.

**C0 — Diff Only (Baseline)**

Provide the code change as a proper unified Git diff, preserving additions, deletions, and relevant diff structure.

Do not simplify the diff into only added lines.

**C1 — Diff + Local Context**

Provide the same diff alongside bounded local code context, such as the surrounding function or enclosing class.

Define exactly how local context is extracted, which snapshot is used, and how duplication is prevented.

**C2 — Diff + Relevant Repository Context**

Provide the diff alongside code selected automatically from the relevant repository snapshot.

Initially investigate a simple, reproducible retrieval strategy such as BM25, rather than immediately introducing complex agentic or LLM-based retrieval.

Specify indexing, candidate selection, ranking, filtering, token limits, and fallback behavior.

**C3 — Diff + Random Repository Context**

Provide the same diff alongside randomly selected repository code.

Use the same eligible repository snapshot and match C2's context token budget as closely as possible.

Use fixed random seeds and consider multiple random samples to assess variability.

Evaluate whether additional controls or token-budget ablations are scientifically necessary, but avoid unnecessary experimental complexity.

## 7. Experimental Validity

The experiment must prevent label leakage and unfair comparisons.

- Retrieve code from a historically valid Git snapshot.
- A conservative default is the parent commit, combined with the candidate diff.
- Never use later bug fixes, revert commits, or future repository states as prediction input.
- Prevent dataset labels or labeling metadata from entering prompts or retrieval queries.
- Ensure all conditions use the same examples and model configurations.
- Keep instructions and response formats consistent across conditions.
- Define deterministic truncation and exclusion rules for oversized changes.
- Avoid selecting experimental parameters using held-out test results.
- Account for duplicated or closely related changes and project/time leakage.
- Ensure any random controls are appropriately matched.
- Document missing commits, failed API calls, retrieval failures, and excluded records.

Separate differences caused by context relevance from differences caused merely by additional input tokens.

## 8. Evaluation

Recommend a primary metric appropriate for the dataset's actual class distribution and the research question.

Consider:

- Precision, recall, F1, and balanced accuracy.
- PR-AUC and ROC-AUC where meaningful prediction scores are available.
- Matthews correlation coefficient.
- Per-project performance.
- Paired comparisons and confidence intervals.
- Input/output token consumption.
- API cost and latency.
- Invalid outputs and failure rates.

If an LLM returns subjective confidence values, evaluate their suitability before treating them as calibrated defect probabilities.

Report meaningful effect sizes and uncertainty, not only numerical improvements or p-values.


## 10. Research Integrity Rules

1. Prioritize peer-reviewed research, original papers, official dataset repositories, and replication packages.
2. Provide verifiable paper titles, authors, publication years, URLs, and DOIs where available.
3. Do not invent citations, experimental results, repository structures, or dataset characteristics.
4. Distinguish verified findings, interpretations, assumptions, and recommendations.
5. Explicitly state when source code, papers, or datasets cannot be accessed.
6. Critically challenge my assumptions and your previous recommendations.
7. Prefer simpler approaches when they answer the same research question with fewer confounding factors.
8. Do not present illustrative examples as actual dataset records.
9. Document major methodology decisions and the reasons for them.
10. Do not prioritize generating code before validating the research methodology.

## 11. Initial Assignment — Research and Feasibility Phase

Do not implement the entire thesis pipeline immediately.

First, conduct a focused literature and dataset feasibility review and provide:

**A. Literature review:** The most relevant foundational and recent papers available up to October 2026, including how my thesis differs from existing studies.

**B. Dataset comparison:** A verified comparison of candidate benchmarks, including dataset fields, labels, Git reconstruction feasibility, and limitations.

**C. Dataset recommendation:** One preferred dataset, one fallback, and an evidence-based explanation of the tradeoffs. Clearly identify any checks that remain incomplete.

**D. Experimental design proposal:** Refined research questions, context conditions, baselines, leakage controls, model options, sampling strategy, metrics, and statistical analysis.

**E. Feasibility demonstration:** A real, verifiable dataset example where possible, showing its label, diff, Git snapshot, and possible context sources. Mark any synthetic demonstration as synthetic.

**F. Research risks:** The strongest threats to validity and practical implementation, ranked by importance.

**G. First implementation milestone:** The smallest reproducible experiment needed to establish whether the proposed dataset and context extraction strategy actually work.

Organize findings so they can be saved directly into version-controlled Markdown documents.

Identify decisions that should be finalized before writing production experiment code.
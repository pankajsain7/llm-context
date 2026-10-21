# A. Literature Review

Status: research phase, 2026-10-19; **revised after the Phase 2 critical review** (JIT-LSM and JIT-Defect-Extended added, novelty statement narrowed) and **after the external audit** (JIT-Context and LLM4Reg added, PROPER-SDP read in full, novelty matrix in §9). Citation keys refer to [references.md](references.md), which also records how deeply each source was verified (FT, AB, MD, SEC, RP).

**Evidence labels used in this document**

- **[V]** Verified in this review, either from the full text or abstract, or from data we inspected ourselves.
- **[BK]** Background knowledge about a paper whose metadata is verified. Read the full text before you cite the claim.
- **[I]** My interpretation or synthesis.

## 1. Search method and its limits

- **Sources.** I searched the OpenAlex API (title and full-text search), the arXiv API (abstract search, sorted by date), arXiv HTML full texts, GitHub, Zenodo, and figshare records. The searches ran on 2026-10-19.
- **Queries.** I combined just-in-time / defect prediction / bug-inducing / risky changes with LLM / large language model, and context / repository / retrieval with code review / vulnerability / defect. I also searched the exact title of every candidate dataset paper.
- **Coverage gaps.** DBLP was blocked by a bot-protection page and Semantic Scholar returned HTTP 429, so I could not use either. Google Scholar, IEEE Xplore, and ACM DL full-text search were not used. Only two papers were read in full (ReDef, ApacheJIT). For the rest I read abstracts or verified metadata only.
- **Next step.** Snowball backward and forward from ReDef (Nam2026), CodeFlowLM (Monteiro2025), JIT-Fine (Ni2022), and JIT-LSM (Huang2026) in Google Scholar before you write the related-work chapter. 2026 venues (FSE/ICSE/ASE 2026) may contain directly competing work that has not yet been indexed.
- **Phase 2 search pass (2026-10-19).**
  - Date-sorted arXiv sweeps: just-in-time / bug-inducing / defect-inducing / risky changes combined with LLM and context / repository / agent, and all titles containing "defect prediction" combined with LLM.
  - Crossref metadata and the reference list of Huang2026; GitHub repositories and Git LFS data of JIT-LSM and JIT-Defect-Extended.
  - ScienceDirect returned HTTP 403, so **the JIT-LSM paper itself was not read**. Its design is described here from its replication code, which was inspected directly.
  - No other study was found that varies code context for LLM-based JIT-DP. Closed-access and not-yet-indexed venues remain a residual risk.

## 2. Foundations of JIT defect prediction

- **Task origin.** Predicting the risk of an individual change goes back to Mockus2000. Kim2008 framed it as clean-or-buggy change classification. Kamei2013 named it "just-in-time quality assurance" and introduced the 14 change metrics (size, diffusion, history, experience) that later datasets still ship. [BK; the Kamei metric set is [V] as the column set of ApacheJIT and JIT-Defect4J]
- **Size is a strong signal.** [V, our data] Defect rates rise steeply with churn:
  - JIT-Defect4J: from 2.1% in the lowest churn quintile to 20.2% in the highest.
  - ApacheJIT: from 7.2% to 52.9%.

  Any LLM result therefore has to be compared against a size-only baseline. Zeng2021 is commonly cited for showing that a logistic regression on added lines (LApredict) is competitive with deep JIT models [BK]. The JIT-Fine replication package ships LApredict as a baseline [V].
- **Time-aware evaluation.** McIntosh2018 (fix-inducing changes as a moving target), Tan2015 (online prediction), and Cabral2019 (class-imbalance evolution and verification latency) argue that random cross-validation overstates performance and that labels for recent commits are immature [BK]. We observe the expected label decay in ApacheJIT: the positive rate is 21.0% in 2018 and 10.2% in 2019, against 26.5% overall [V].

## 3. Label construction and label noise

- **SZZ is the default.** Most JIT datasets derive labels with SZZ (Sliwerski2005). SZZ blames the last modification of lines that a later bug-fixing commit changed. Filtering heuristics (daCosta2017), refactoring-aware variants (Neto2018), and developer-informed oracles (Rosa2021) were proposed because blame produces false positives and false negatives [BK].
- **Measured error rates.** Herbold2022a reported that only about half of SZZ-identified bug-inducing commits were correct. Lyu2024 evaluated SZZ variants against more than 76K developer-labelled Linux commits and found substantial recall loss and "ghost" commits. [V, as summarised in the ReDef full text]
- **Effect on models.** Fan2021 showed that mislabelled changes affect JIT-DP results [BK]. Guo2024 (TOSEM) and the 2026 preprint Bludau2026 study the uncertainty and evaluation bias that SZZ introduces [MD, titles only].
- **Recent SZZ work also uses context.** LLM4SZZ (Tang2025) uses "context-enhanced" LLM assessment. AgentSZZ (Lyu2026) and AgenticSZZ (Shi2026) let agents explore the repository. Both report that cross-file and "ghost" cases are untraceable by `git blame` alone [V, AB]. The parallel matters here: context helps even the labelling problem.
- **Observed in our data.** [V] JIT-Defect4J labels commons-codec commit `76c125c3` as bug-inducing. Its message is *"Checkstyle, javadoc and formatting fixes."* Its only labelled bug line is a re-wrapped `return` statement. The later fix (CODEC-184, a NullPointerException for empty strings) addresses behaviour that already existed at the parent commit. See [04-feasibility-demo.md](04-feasibility-demo.md).

  [I] This is a textbook SZZ false positive. More importantly, it shows how *more context could raise measured performance for the wrong reason*: a model that sees the callee may flag the pre-existing NPE risk and "agree" with a noisy label.

## 4. Learned and semantic JIT-DP

- **Pre-LLM line of work.** DeepJIT (Hoang2019) and CC2Vec (Hoang2020) learned representations from added and removed lines. JITLine (Pornprasit2021) offered a simpler and stronger alternative. JIT-Fine (Ni2022) combined CodeBERT semantics with expert features and introduced the line-labelled **JIT-Defect4J** dataset. JIT-Smart (Chen2024), CCT5 (Lin2023), Zhou2024, Guo2023, Jiang2025, and Monteiro2026 continue this line. [MD/BK]
- **JIT-Defect4J is the de facto benchmark** for semantic JIT-DP and is still used in 2025–2026 LLM work. JIT-LSM (Huang2026) evaluates on JIT-Defect4J test commits and republished the dataset with per-file code as JIT-Defect-Extended [V, RP; see [02-datasets.md](02-datasets.md) §2]. CodeFlowLM (Monteiro2025) benchmarked GPT-5, Claude Sonnet 4.5, and Gemini 2.5 Pro for JIT defect *localization* on JIT-Defects4J. Its error analysis attributes most false positives to:
  1. a "human-like conservative bias";
  2. "insufficient contextual information in diff-based prompts";
  3. possible mislabelling in JIT-Defects4J.

  [V, AB] This is the most direct published motivation for this thesis.
- **Prior encodings were diff-centric.** These models consume diffs (added and removed lines), sometimes with the commit message and expert metrics. None systematically varies *repository* context. [I, based on abstracts and titles; confirm in full texts]

## 5. LLMs for JIT-DP and change risk

| Work | What it shows | Relevance |
|---|---|---|
| **ReDef** (Nam2026, FSE 2026) [V, FT] | A revert-anchored, function-level benchmark (C/C++). Fine-tuned CLMs (CodeBERT, CodeT5+, UniXcoder, Qwen2.5-7B) score best with compact diff-style inputs. Whole-function inputs are worse, which the authors attribute to truncation and "distracting context". Qwen2.5 and UniXcoder did better at 512 than at 1,024 tokens. Zero-shot Qwen2.5 performed poorly (after-only encoding F1 < 0.1). Counterfactual perturbations, such as swapping added and deleted code, barely changed F1, which suggests reliance on surface cues | **Strongest prior evidence that more context can hurt**, though for small fine-tuned models and function-level inputs. The thesis can test whether this holds for instruction-tuned LLMs with *selected* repository context |
| Meta DRS (Abreu2024) [V, AB] | Generative LLMs (iCodeLlama-34B, iDiffLlama-13B), once "risk-aligned", capture more SEV-causing diffs than logistic regression in production. Follow-ups: Liu2026 (attention-based explanations), Adams2026 (RADAR deployment) | Industrial evidence that LLM-based diff risk scoring works. Its inputs are diff-centric |
| Prime Video (Kurup2026) [V, AB] | Uses LLMs as feature extractors on ApacheJIT and internal data. Reports that "change-level volume metrics … are noisy predictors" while structural complexity is a stronger signal | ApacheJIT is still used in 2026 industrial studies |
| CodeFlowLM (Monteiro2025) [V, AB] | Points to insufficient context in diff-only prompts as an LLM error source | Direct motivation |
| **JIT-LSM** (Huang2026, IST, October 2026) [paper: MD, closed access; code and data: RP] | Combines LLMs with the small model JIT-Smart for JIT defect prediction and localization on JIT-Defect4J commits. In the replication code, a main LLM agent makes up to 15 function calls. It reads commit info (message, author, date, file counts) and added lines, and can start an assistant LLM per file. The assistant fetches the enclosing snippet of an added line (before or after the change) and same-file functions by name. A checker LLM decides whether more calls are needed. **No tool retrieves code from other files.** The README names gpt-3.5-turbo, gpt-4o-mini, qwen-turbo, and gemini-2.0-flash, and says its RQ3 compares context configurations, "validating the effectiveness of contextual information". Evaluation subsets: 1,730 test commits (8.7% defective) and 1,000 (45.9%) | **Closest prior work; narrows the novelty claim (§9).** LLM JIT-DP with same-file context is published. Its context effect is entangled with agentic search, assistant and checker LLMs, commit-message input, and small-model assistance. It has no token-matched control and no cross-file retrieval |
| PROPER-SDP (Yeo2026, J. Web Eng.) [V, FT] | Zero-shot LLM prediction for four Go edge-cloud projects (EdgeX, KubeEdge, OpenShift installer, Traefik) from the GHPR dataset. The unit is a *function version* (buggy before a fix vs clean after it), not a bug-inducing commit, and the buggy class was augmented to balance the data. The prompt holds the PR title and description, the function before and after, and *project evolution* context: main and local README changes and local file-structure changes. Models: gpt-3.5-turbo (best), gpt-4o-mini, gemini-2.0-flash(-lite), binary output, F1. Removing any evolution component lowers F1 (local README most). Cost per 1,000 predictions and latency are reported per model | Prompt context for JIT-DP is studied, but as documentation and project history, with ablation by removal and no volume control. Different unit, labels, and language |
| **JIT-Context** (Deng2026, ICSME 2026) [V, AB] | A graph neural network learns structural context of a change from control-flow and control/data-dependency graphs. Evaluated on JIT-Defects4J (21 projects); reported to outperform deep-learning baselines *and LLMs*, with about 37% higher F1, plus weakly supervised localization | Structural code context helps *learned* JIT-DP models on the same benchmark. It also signals that zero-shot LLMs are not the state of the art there, which fits this thesis's explanatory aim |
| **LLM4Reg** (Song2026, ICSE 2026) [V, FT preprint + RP] | Characterizes 280 regression bugs in Java projects, then detects regression bug-inducing commits with an LLM pipeline: sub-commit decomposition, a staged prompt workflow, and *repository context* from change-impact analysis (top-k impacted methods) and frequently co-changed files. The evaluation set has the 280 bug-inducing commits plus **2,800 non-bug-inducing commits sampled from JIT-Defects4J**. DeepSeek-V3 was the best of 7 LLMs. The README reports F1 rising from 0.386 (k = 1) to 0.487 (k = 7) and falling to 0.403 (k = 20) impacted methods, and peaking at k = 3 co-changed files. Ablation removes decomposition, workflow, or co-change components | **Closest evidence that cross-file context helps LLM detection of defect-inducing changes, and that its quantity matters (inverted U).** Only regression bugs; positives and negatives come from different collections; the context comes bundled with a multi-stage pipeline; no token-matched random control; where k was tuned is not stated in the README |
| Shahini2025 (MSR 2025) [V, AB] | Three JIT-DP models are miscalibrated (ECE 2–35%), and post-hoc calibration does not consistently help | Report calibration; do not treat raw scores as probabilities |
| Kim2025 (TSE) [MD, title only]; Boughriou2026 [RP; paper not located] | A reflection on change classification in the LLM era; a benchmark of LLMs versus ML for JIT-DP | Read Kim2025; locate the Boughriou paper |

## 6. Context selection for LLMs in other code tasks

- **Code completion.** Repository context is well studied here: RLPG (Shrivastava2023), RepoCoder (Zhang2023), CrossCodeEval (Ding2023) [BK]. Lexical retrieval such as BM25 or Jaccard is a standard, reproducible baseline in this line of work [BK]. This supports the brief's choice of BM25 as the first C2 operationalization.
- **Code review.** The direction and size of context effects depend on the context type and the model [V, AB]:
  - ContextCRBench (Hu2025): *textual* context (issues/PRs) "yields greater performance gains than code context alone".
  - AACR-Bench (Zhang2026): "the granularity/level of context and the choice of retrieval methods significantly impact" review performance, and the effect varies by LLM, language, and agentic versus non-agentic use.
  - Sun2026: compared neighbouring, LSP-based semantic, and IR-based "similar co-change" context for Go reviews. Neighbouring plus similar co-change context worked best.
  - Lu2025: uses code slicing to extract review context.
- **Vulnerability detection.** This is the closest analogue to defect prediction. Risse2025 argues that function-level benchmarks are ill-posed without context [MD/BK]. VulEval (Wen2024) and JitVul (Yildiz2025) move to repository-level and commit-anchored evaluation [MD]. CORRECT (Li2025) reports that beliefs about LLM unreliability are "artifacts of context-deprived evaluations"; with sufficient context, state-of-the-art LLMs reach about 0.7 F1 on key CWEs [V, AB].

## 7. Long-context behaviour (why a random-context control is mandatory)

- Shi2023 shows that irrelevant context distracts LLMs [title-level V; details BK].
- Liu2024 reports position effects ("lost in the middle") [BK].
- Levy2024 reports that reasoning performance degrades as input length grows, even with irrelevant padding [BK].
- Ding2024 (TOSEM), cited by JIT-LSM, asks whether code summarization models "process too much information" and suggests that a function signature "may be all that is needed" [SEC, title only]. More code is not automatically better in neighbouring tasks either.

[I] Adding context therefore has at least two opposing effects: an *information* effect and a *length/distraction* effect. Only a token-matched control such as C3 separates them. ReDef's 512-versus-1,024 result [V] is consistent with a length penalty.

## 8. Methodological guidance for LLM-based empirical SE

- **Threats.** Sallou2024 lists closed-model, data-leakage, and non-determinism threats. Wagner2025 proposes evaluation guidelines: report model versions and configuration, use baselines, report non-determinism, and release artifacts [MD/BK].
- **Non-determinism.** Ouyang2025: temperature 0 "does not guarantee determinism" [V, AB].
- **Memorization.** Ramos2025 found memorization evidence for widely used bug benchmarks such as Defects4J, which varies by model [V, AB]. Our candidate datasets come from public Apache repositories from 2001–2019, so the same risk applies.
- **Verbalized confidence.** Xiong2024: LLMs are overconfident when they verbalize confidence [V, AB]. Self-reported confidence should therefore not be treated as a calibrated probability. Prefer token log-probabilities where the API exposes them.
- **Metrics and tests.** MCC is recommended for imbalanced defect data (Yao2020, Chicco2020) [BK]. DeLong/McNemar address paired predictions but do not automatically handle project clustering; Obuchowski1997 establishes the need for clustered ROC methods [A]. The proposed project-bootstrap analysis and conditional metric choice are specified in design §§10–11. Equivalence requires a justified practical margin; non-significance alone is not equivalence.

## 9. Synthesis: what is known, what is not, and how this thesis differs

| Question | State of evidence | Thesis contribution |
|---|---|---|
| Does context beyond the diff help LLM-based change risk prediction? | **Conflicting.** It hurts or does not help fine-tuned CLMs on function-level inputs (Nam2026, V). It helps in vulnerability detection and code review (Li2025, Zhang2026, Sun2026, V AB). LLM error analysis blames missing context (Monteiro2025, V AB). JIT-LSM's README states that its RQ3 validates "the effectiveness of contextual information" in an *agentic* system (Huang2026; README only, paper not read) | Controlled, non-agentic, commit-level test for instruction-tuned LLMs at a fixed token budget |
| Does *cross-file* repository context help, and is it better than local context? | LLM4Reg reports that impacted methods and co-changed files help an LLM pipeline detect regression bug-inducing commits (Song2026, V FT). JIT-LSM's tools are same-file only (V, code). No study compares the two at an equal budget | C2−C0 and the strategy comparison C2−C1 at an equal budget |
| Is *relevance* or *quantity* responsible? | Not isolated for JIT-DP. Long-context literature predicts length penalties (Levy2024, Shi2023, BK) | Token-matched random control (C3) and the decomposition C2−C0 = (C2−C3) + (C3−C0) |
| How much context is worth adding? | ReDef: longer inputs were worse for fine-tuned CLMs (V). LLM4Reg: F1 rises and then falls as more impacted methods or co-changed files are added (V, README) | Budget series of 1,000 / 2,000 / 8,000 tokens with a random control and cost at each level (RQ3) |
| Does the effect depend on the model? | AACR-Bench reports model-dependent context effects (V AB). ReDef reports inverse scale effects for fine-tuned models (V) | Model as a factor, tested as an interaction |
| What does context cost? | Rarely reported | Tokens, cost, and latency per condition; cost-effectiveness |
| Do label artifacts drive apparent gains? | SZZ noise is well documented (Herbold2022a, Lyu2024). Its interaction with context has not been studied (I) | Sensitivity analyses on high-confidence subsets |

**Novelty matrix (revised after the external audit)** [V for each row's evidence level; I for the conclusions]:

| Work | Unit and data | Predictor | Code context given | Selection of context | Volume-matched random control | Amount varied | Cost per condition |
|---|---|---|---|---|---|---|---|
| JIT-LSM (Huang2026) [RP; paper unread] | Commit; JIT-Defect4J test subsets | LLM agent + small model | Same-file snippets and functions; plus message and metadata | Chosen by the agent | No | No | Unknown |
| LLM4Reg (Song2026) [FT] | Commit; 280 regression BICs + 2,800 JIT-Defects4J non-BICs | Multi-stage LLM pipeline | Cross-file: impacted methods, co-changed files | Change-impact analysis, co-change frequency | No | Yes, k = 1–20 methods and 1–10 files | Not reported in the README |
| PROPER-SDP (Yeo2026) [FT] | Function version; 4 Go projects | Zero-shot LLM | Function before/after; README and file-structure changes | Fixed components | No (ablation by removal) | No | Per model, not per context |
| JIT-Context (Deng2026) [AB] | Commit; JIT-Defects4J | Trained GNN | Control-flow and dependency graphs | Program analysis | Not applicable | Not stated | Not stated |
| ReDef (Nam2026) [FT] | Function modification; C/C++ | Fine-tuned CLMs | Diff vs whole function | Fixed encodings | No | 512 vs 1,024 tokens | No |
| **This thesis** | Commit; JIT-Defect4J test split | Zero-shot LLM, one fixed prompt per condition | Same-file (C1) or cross-file (C2, C3) code at the parent commit | Proximity, BM25, random | **Yes (C3)** | **1,000 / 2,000 / 8,000 tokens** | **Yes** |

**Questions the prior work leaves open** (the thesis's claimed contribution):

1. **Primary:** how does the fixed BM25 policy differ from random selection from the same snapshot at approximately matched volume? The inspected work did not establish this exact control; full JIT-LSM reading remains open. The estimand is a policy effect against historical SZZ labels, not semantic relevance or defect understanding in isolation.
2. How do same-file and cross-file strategies compare at an equal token budget? JIT-LSM uses only same-file code and LLM4Reg only cross-file code, and neither fixes the amount of text.
3. **Optional secondary scope:** how does performance change with the amount of repository code and at what cost? LLM4Reg already varies quantity, so this is not a standalone novelty claim; the controlled random comparison is the central contribution. Current prioritization is in design revision 3.2, pending Prof. Höll's approval.

**Claims the thesis will not make:** that context augmentation for LLM-based JIT-DP is new (JIT-LSM, PROPER-SDP); that cross-file context for LLM detection of bug-inducing changes is new (LLM4Reg); or state-of-the-art accuracy (JIT-Context reports beating LLMs on this benchmark). Leakage controls and multi-model checks are methodological qualities, not novelty claims.

## 10. Items to read in full before writing the thesis chapter

1. **Huang2026 (JIT-LSM), through library access:** its RQ3 context ablation, results per evaluation subset, how the subsets were sampled, and whether commit messages were ablated. This is the most important open reading item, because it determines how the thesis is positioned.
2. **Deng2026 (JIT-Context) and Song2026 (LLM4Reg):** for JIT-Context, the LLM baselines and their prompts; for LLM4Reg, on which data k was chosen, and its prompt sizes and cost.
3. Ni2022 (JIT-Fine): the exact JIT-Defect4J construction, the SZZ variant, the split protocol, and the reported baselines.
4. Monteiro2025 (CodeFlowLM): the prompting setup and context findings.
5. Chen2024 (JIT-Smart) and Kim2025: check for overlap with this thesis.
6. Zhang2026 (AACR-Bench) and Sun2026: how they operationalized context types and retrieval.
7. Levy2024, Liu2024, Shi2023, Ding2024: cite their exact findings on length, position, and amount of context.
8. Yildiz2025 (JitVul) and Li2025 (CORRECT): their context construction and leakage controls.
9. Locate the paper behind Boughriou2026, which compares LLMs with ML for JIT-DP.

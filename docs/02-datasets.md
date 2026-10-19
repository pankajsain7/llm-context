# B. Dataset Comparison and C. Recommendation

Status: research phase, 2026-10-19; revised after the Phase 2 critical review and **after the external audit** (all-project audit of all 27,319 commits; split explanation corrected; dataset decision now *conditionally accepted* pending Gate 1). Evidence labels: **[V]** verified from real files or Git in this review, **[P]** taken from the paper (full text read), **[A]** taken from an abstract or dataset record only, **[NV]** not verified. Numbers can be reproduced with [feasibility/verify_datasets.py](../feasibility/verify_datasets.py), [feasibility/measure_inputs.py](../feasibility/measure_inputs.py), and [feasibility/audit_dataset.py](../feasibility/audit_dataset.py); label-free outputs are in [feasibility/outputs/](../feasibility/outputs/); the setup is described in [04-feasibility-demo.md](04-feasibility-demo.md).

## 1. Summary comparison

| Criterion | **JIT-Defect4J** (Ni2022) | JIT-Defect-Extended (with Huang2026) | **ApacheJIT** (Keshavarz2022) | **ReDef** (Nam2026) | Defectors (Mahbub2023) |
|---|---|---|---|---|---|
| Unit | Commit, plus line labels for defective test commits [V] | Commit, plus line labels (`added_buggy`) [V] | Commit [V] | **Function-level modification** (single-file, single-function commits) [P] | Source file within a commit [A] |
| Size and positives | 27,319 commits; 2,332 defective (**8.54%**) [V] | 27,155; 2,269 defective (8.36%); a **strict subset of JIT-Defect4J** [V] | 106,674; 28,239 buggy (**26.47%**) [V] | 13,432; 3,164 defective (23.6%) [P] | ≈213K files; ≈93K defective [A] |
| Language and projects | Java, 21 Apache projects (Commons, Ivy, Giraph, Gora, OpenNLP, Parquet) [V] | Same 21 projects [V] | Java-touching commits, 14 Apache projects (15 values in the `project` column) [V/P] | C/C++, 22 projects, concentrated in **Linux and Chromium** [P] | Python, 24–25 projects [A] |
| Labels | Manually validated bug-fix *lines* (LLTC4J), then blame-based bug-inducing commits [V, construction figure] | Identical to JIT-Defect4J for all 27,155 shared commits [V] | PyDriller SZZ plus filters, JIRA bugs from 2010–2019 [P] | Revert-anchored, GPT-4o 3-vote triage; positive precision 0.92 in a 100-sample audit [P] | SZZ fix→BIC maps [A] |
| Commit ID / parent / repo | hash + **parent hash** + project [V] | hash (file name), GitHub URL, all JIT-Defect4J fields [V] | hash + project; no parent [V] | Not inspected [NV] | `repo_links.yaml` [A] |
| Git reconstruction | **Verified for all 27,319 commits**: all exist with the recorded parent; churn reproduced for 99.98% with Java files except `package-info.java` [V] | Not needed for changed files (pre-extracted whole-file diff view); still needed for cross-file context [V] | **Verified** on 2 ZooKeeper commits [V]; Hadoop mapping caveat [V] | Not attempted [NV] | Not attempted [NV] |
| Repository size, for context retrieval | Small (commons-codec pack 8.4 MiB; about 100 Java files per snapshot) [V] | Same repositories | Medium to large (Hadoop, Camel, Flink, Ignite, Spark) [P] | Very large (Linux, Chromium) [P] | Mixed [NV] |
| Provided split | Per project ≈60/20/20, roughly chronological per project (2.9% of test commits are older than the project's last train commit) [V] | None in the layout; recoverable by joining with JIT-Defect4J [V] | Time-based: balanced train 2003–2016, test 2017–2019 [V/P] | Per-repository chronological 80/10/10 [P] | [NV] |
| License and access | **No LICENSE file** in the GitHub repo; `data.zip` is 75 MB [V] | **No LICENSE file**; ≈288 MB Git pack, ≈1.94 GB of JSON [V] | CC BY 4.0; CSV 16.5 MB [V] | Anonymous figshare link; page needs JavaScript; schema not inspected [NV] | CC BY 4.0; 2.2 GB zip [A] |
| Fit for this thesis | **Best overall fit** | Cross-checks and comparability with JIT-LSM only | **Fallback** | Robustness only, needs task reformulation | Not recommended |

## 2. JIT-Defect4J (primary candidate)

1. **Publication and repository.** Ni et al., ESEC/FSE 2022 (JIT-Fine), DOI 10.1145/3540250.3549165. Data is in `data.zip` at <https://github.com/jacknichao/JIT-Fine>. [V]
2. **Observations and class distribution** [V]:

   | Split | Commits | Defective | Rate | Author dates |
   |---|---|---|---|---|
   | train | 16,374 | 1,390 | 8.49% | 2001-09 to 2015-09 |
   | valid | 5,465 | 467 | 8.55% | 2006-10 to 2018-01 |
   | test | 5,480 | 475 | 8.67% | 2001-03 to 2019-04 |

   Per-project defect rates range from 1.8% (commons-digester) to 19.3% (giraph). The largest test projects are commons-math (806 commits) and commons-lang (595).
3. **Languages and projects.** All Java. ant-ivy, commons-{bcel, beanutils, codec, collections, compress, configuration, dbcp, digester, io, jcs, lang, math, net, scxml, validator, vfs}, giraph, gora, opennlp, parquet-mr. `git ls-remote` reaches all 21 at `github.com/apache/<project>`. [V]
4. **Prediction unit.** Commit (`is_buggy_commit`). Line-level labels cover the 475 defective *test* commits: 26,104 changed lines, of which 7.89% are labelled buggy. [V]
5. **Label construction and noise.** The construction figure in the replication package shows four steps [V]:
   1. Participant line labelling of bug-fixing commits (from LLTC4J, Herbold2022b).
   2. Line-level agreement.
   3. Filtering of fix lines.
   4. Bug-inducing commits identified via Git.

   Clean commits are non-bug-fixing commits that were not identified as bug-inducing. The fix side is therefore validated, but **bug-inducing attribution is still blame-based** (SZZ-style). We found a formatting-only commit labelled defective; see the example in [04-feasibility-demo.md](04-feasibility-demo.md). [V] Read the paper text to confirm the SZZ variant and whether bug-fixing commits are excluded from the clean class. [NV]
6. **Fields** [V]:
   - `features_{split}.pkl` (pandas DataFrame, 25 columns): `project, parent_hashes, commit_hash, author_name, author_email, author_date, author_date_unix_timestamp, commit_message, la, ld, fileschanged, nf, ns, nd, entropy, ndev, lt, nuc, age, exp, rexp, sexp, classification, fix, is_buggy_commit`.
   - `changes_{split}.pkl`: `[commit_ids, labels, tokenized_messages, {added_code, removed_code}]`. The code is **normalised and tokenised, not a unified diff**, so diffs must be regenerated from Git.
   - Labels agree 100% between the two files.

   A real record (test split, abbreviated):
   ```json
   {"project": "commons-codec",
    "commit_hash": "76c125c3b74a390a39cdcd6666cf7e9cea0e5c1d",
    "parent_hashes": "09f58fbc8956b05aec9cdc7ce9d153639917f24d",
    "author_date": "Wed Aug 29 21:02:47 2012 +0000",
    "la": "86", "ld": "133", "nf": "1",
    "fileschanged": "src/main/java/org/apache/commons/codec/language/DoubleMetaphone.java,CAS_DELIMITER",
    "classification": "Corrective", "is_buggy_commit": 1.0,
    "commit_message": "Checkstyle , javadoc and formatting fixes ."}
   ```
7. **Commit IDs and repository URLs.** The full SHA, the parent SHA, and the project name are present. There are no merge commits: all 27,319 have exactly one parent. The repository URL is not stored but follows deterministically from the project name. [V]
8. **Historical reconstruction.** For `76c125c3` and `4063338a` (commons-codec), the commit exists, `<sha>^` equals `parent_hashes`, and `git show --numstat` reproduces `la/ld/nf` exactly (86/133/1 and 55/55/1). [V]

   **Full audit after the external review** [V; all 27,319 commits in all 21 repositories; [feasibility/audit_dataset.py](../feasibility/audit_dataset.py)]:
   - Every commit exists, has exactly one parent, and that parent equals `parent_hashes`.
   - **Churn scope.** Git reproduces `la/ld` for 99.98% of commits in every split (train 16,371/16,374; valid 5,464/5,465; test 5,479/5,480) when counting `.java` files *except* `package-info.java`. Counting every `.java` file left 195 commits unmatched; in 190 of them the only difference was `package-info.java` files, which the benchmark's metrics and `fileschanged` lists omit (368 of the 380 omitted files). Counting all files matched only 68.5% of a 200-commit validation sample. Five commits stay unexplained (giraph 3, opennlp 1, parquet-mr 1).
   - These checks verify how the benchmark defines its *change metrics*. They do not prove that non-Java changes are irrelevant to the labels, so the Java-only input is a documented scope decision ([03-experimental-design.md](03-experimental-design.md) §4).
9. **Function, class, and caller context.** All 21 repos are Java, so the following work: `git diff --function-context` with Git's built-in `java` diff driver, `git grep -w <identifier> <parent>` for callers, and tree-sitter-java if needed. The commons-codec parent snapshot has 102–114 Java files (≈315–365K tokens), which makes full-snapshot BM25 indexing trivial. [V]
10. **Splits and leakage** [V, all commits; the protocol itself is NV until Ni2022 is read].
    - The split is per project, not global. The dataset's author times equal Git's for 100% of commits.
    - **The split is not strictly chronological.** 159 test commits (2.9%, in 11 projects) are older than their project's newest train commit, by author time *and identically by committer time*. 92 of them are older than the project's *oldest* train commit; the median gap is 3,032 days. Revision 1 attributed this to "SVN-era author-date artefacts"; the committer-time check refutes that guess. The same holds for 10.4% of validation commits, and 20.3% of train commits are newer than their project's oldest test commit.
    - Consequences: zero-shot LLM inference has no training-time leakage, but trained baselines (B1–B3) can learn from commits newer than some test commits. Report baselines with and without these 159 commits, and do not call the split "time-based".
    - **Duplicates** (`git patch-id --stable` on the Java diff): 312 commits share a patch with another commit, in 148 groups: 122 within train, 13 within valid, 9 within test, 3 across train and valid, 1 across test and valid, none across train and test. Two commits have no Java change.
11. **License, access, storage.** There is **no license file** in the JIT-Fine repository [V]. The upstream code is Apache-2.0. Before redistributing derived data, ask the authors and confirm the data-availability statement in the paper. Storage: 75 MB zip, and small clones.
12. **Difficulty.** Low to moderate. The pickles load with pandas 3.0.6 (with deprecation warnings only) [V].

**Size effects** [V]: the defect rate rises from 2.1% to 20.2% across churn quintiles, so any size limit removes defective commits disproportionately. Measured in tokens of the Java diff across all 21 projects:

| Diff tokens ≤ | Test, all commits (label-blind) | Train defective | Validation defective | Train + validation clean |
|---|---|---|---|---|
| 8,000 | 90.9% | 72.1% | 76.2% | 93.3–95.3% |
| 12,000 | 94.3% | 80.1% | 83.1% | 96.2–97.2% |
| 16,000 | 95.7% | 85.4% | 86.9% | 97.7–98.1% |

The 4-project estimate from Phase 2 (93.1% of defective commits kept at 12,000) was too optimistic. Class-specific figures are reported for train and validation only; test labels were not read.

### JIT-Defect-Extended: a derivative published with JIT-LSM

1. **Publication and repository.** Released with JIT-LSM (Huang2026, IST 198:108244, October 2026; the paper is closed access and was not read). Data: <https://github.com/JIT-LSM/JIT-Defect-Extended>, created July 2025 [V].
2. **Layout** [V]: one JSON file per commit, `dataset/{buggy,no_buggy}/<project>/<sha>.json`. **The folder name is the label.**
3. **Relation to JIT-Defect4J** [V, joined on commit hash]:
   - 27,155 commits (2,269 defective, 8.36%), all of them JIT-Defect4J commits. 164 JIT-Defect4J commits are missing (101 clean, 63 defective; 46 of them in the test split). No reason is documented.
   - Labels agree for 100% of shared commits.
   - Test-split coverage: 5,434 commits, 452 defective.
   - "Extended" therefore means **richer per-commit content, not more commits, projects, or a later period**.
4. **Record schema** [V, two records inspected]:
   - `expert_features`: all 25 JIT-Defect4J fields, including `commit_message`, `classification`, `fix`, and `is_buggy_commit`.
   - `change_message.url` (the GitHub repository), `paths` (changed Java files), and `commit_info` (message, git-svn-id, author, date, changed-file counts).
   - Per changed file: `summary`; `code`, a whole-file diff view in which every line is prefixed with two spaces, `+ `, or `- `; `added_lines` and `deleted_lines`; and **`added_buggy`, the line labels**.
   - For `76c125c3`, `code` has 1,193 lines (974 unchanged, 133 deleted, 86 added), consistent with numstat. `added_lines`/`deleted_lines` hold only 51/63 lines, and for `4063338a` 35/0 against numstat 55/55, so these lists are filtered in an undocumented way.
5. **JIT-LSM's evaluation subsets** (Git LFS files in <https://github.com/JIT-LSM/JIT_LSM>, `LargeModel/data/`) [V]:
   - `unbalanced_dataset_1730.json`: 1,730 test-split commits, 150 defective (8.7%).
   - `balanced_dataset_1000.json`: 1,000 test-split commits, 459 defective (45.9%), i.e. almost every defective test commit.
   - 691 commits are in both. 4 and 12 commits respectively are absent from the published JIT-Defect-Extended.
   - The records carry the same per-file fields, including `added_buggy`. How the subsets were sampled is not documented in the repository.
6. **Assessment** [I]:
   - **No new labels or commits.** It cannot widen external validity or relieve the 8.5% prevalence.
   - **Ready-made same-file content** (the whole-file diff view), which is useful to cross-check our own reconstruction. Cross-file context still requires the Git snapshots.
   - **Leakage hazard.** Labels sit inside every record and in every path. If a pipeline serialised a record or a path into a prompt, it would leak the label.
   - **Contamination vector.** Code plus labels for these commits have been public as plain JSON since July 2025 (see [05-risks.md](05-risks.md), Risk 4).
   - No license file, so redistribution terms are unclear.

## 3. ApacheJIT (fallback candidate)

1. **Publication and repository.** Keshavarz & Nagappan, MSR 2022 Data Showcase, arXiv:2203.00101. Data on Zenodo 10.5281/zenodo.5907001 (CC BY 4.0) and GitHub `hosseinkshvrz/apachejit`. [V]
2. **Size and distribution.** 106,674 commits, 28,239 buggy (26.47%); matches the paper exactly [V]. Positive rates by year [V]:
   - 2003–2009: 5.8%–26.2%
   - 2010–2017: 27%–40%
   - 2018: 21.0%
   - 2019: 10.2%
3. **Projects.** ActiveMQ, Camel, Cassandra, Flink, Groovy, Hadoop (HDFS, MapReduce), HBase, Hive, Ignite, Kafka, Spark, Zeppelin, ZooKeeper. Commits that do not touch Java are filtered out. [P]
4. **Unit.** Commit. [V]
5. **Labels** [P]: JIRA bug reports created 2010-01-01 to 2019-12-31 with status Closed/Resolved and resolution Fixed (56,929 issues). The *latest* matching commit per issue is taken as the fix, which the authors acknowledge yields more false negatives. PyDriller SZZ (annotate deleted lines) is then applied with filters:
   1. bug-inducing commit after the issue date;
   2. fix-count above mean + SD;
   3. bug-count above mean + SD;
   4. more than 100 files or more than 10,000 changed lines;
   5. no Java change;
   6. GumTree-trivial changes.

   Clean commits are all other commits between 2003-09-11 and 2019-12-26, after filters 4–5.

   **[I] Consequences:**
   - *Left censoring*: bugs reported before 2010 were never traced, which explains the low early-year rates.
   - *Right censoring*: bugs not yet reported by the end of 2019.
6. **Fields.** 18 columns: `commit_id, project, buggy, fix, year, author_date, la, ld, nf, nd, ns, ent, ndev, age, nuc, aexp, arexp, asexp`. There is no code, message, or parent hash. A real row [V]: `7b8480744ea6e6fb41efd4329bb470c8f3c763db, apache/groovy, buggy=False, fix=False, 2003, 1070355653, la=372, ld=23, nf=8, nd=3, ns=3, ent=2.6697, ndev=0.25, age=3.625, nuc=2.125, aexp=243, arexp=243.0, asexp=0.6836`.
7. **Hadoop anomaly** [V]:
   - `apache/hadoop` has 11,964 rows with **0 buggy**.
   - `apache/hadoop-hdfs` has 2,907 rows, 76.4% buggy.
   - `apache/hadoop-mapreduce` has 1,321 rows, 63.4% buggy.
   - The paper (Table 2) reports HDFS at 21% and MapReduce at 15%. Its totals (10,359 + 5,833 = 16,192) equal the sum of the three CSV groups.
   - Commit `5a0051f4…`, labelled `apache/hadoop-hdfs`, exists in GitHub **`apache/hadoop`** (HDFS-7681) and not in `apache/hadoop-hdfs` (HTTP 422).

   So the `project` field is label-correlated for Hadoop and does not identify the Git repository. [I] It must not be used as a feature, and Hadoop should be analysed as a single repository or excluded.
8. **Reconstruction.** A partial clone (`--filter=blob:none`) of `apache/zookeeper` resolves `1061ac27` (buggy) and `925c425a` (clean), and numstat reproduces la/ld/nf exactly (11/10/3 and 8/8/2). [V]
9. **Context extraction.** Feasible with partial clones and `git cat-file --batch`. Large snapshots (Hadoop, Camel, Ignite) make BM25 indexing per commit costlier; pre-filter with `git grep` or cache indexes per snapshot. [I]
10. **Splits.** Time-based files are provided; the train file is balanced by undersampling. [V/P]
11. **License and storage.** CC BY 4.0; 16.5 MB CSV; 94.7 MB replication zip. [V]
12. **Difficulty.** Moderate, because of larger repositories and the repo-mapping caveat.

## 4. ReDef (not recommended as primary)

- **Data** [P]. 22 C/C++ projects, dominated by Linux and Chromium. Only single-file, single-function commits are included. Defective cases are anchored by revert commits and triaged by **GPT-4o (three unanimous votes)**. Clean cases are function changes with no fix/revert keywords in the next five commits that touch the function, also GPT-triaged. Manual audit: positive precision 0.92 (92/100). Split: per-repository chronological 80/10/10 (10,744 / 1,344 / 1,344).
- **Why not primary** [I]:
  1. **The unit is a function-level modification, not a commit.** Using it would require reformulating the task explicitly. Commit-level results cannot be inferred from function labels.
  2. Repository-level retrieval over Linux and Chromium snapshots is expensive for a master's thesis.
  3. Labels were filtered by a GPT-family model. Evaluating GPT-family models on GPT-curated labels risks circularity (a selection effect toward "LLM-explainable" defects).
  4. The schema was not inspected.
- **Where it helps.** ReDef is the most label-reliable resource. Consider an *optional* robustness study (C0 vs C1) on its test split, explicitly reformulated as "is this single-function modification defective?".

## 5. Other candidates (not inspected in depth)

- **Defectors** [A]: Python, file-level units, 2.2 GB, SZZ maps. It does not match the commit-level unit and was not downloaded.
- **McIntosh & Kamei Qt/OpenStack** [P, via the ApacheJIT paper]: 25,150 Qt changes (8% bug-inducing) and 12,374 OpenStack changes (13%). Widely used by DeepJIT, CC2Vec, and JITLine. Older, distributed in preprocessed form, with large repositories. Not inspected.
- **Not public:** the Kamei2013 dataset, according to the ApacheJIT paper [P].

## 6. Recommendation (re-validated in Phase 2; status after the external audit: conditionally accepted)

**Status.** JIT-Defect4J passes the Gate 1 checks that can be run without reading the paper or labels: reconstruction, parent integrity, dates, and duplicates. It is *conditionally accepted* until three items close: the label-construction and split protocol in Ni2022, a 30-commit label-quality audit on validation data, and data permission ([06-milestone-and-decisions.md](06-milestone-and-decisions.md), Gate 1). The inference target is "eligible Java changes in the JIT-Defect4J test split, with the benchmark label as an observed, SZZ-derived proxy".

**Preferred: JIT-Defect4J labels, splits, and commit IDs, with all code reconstructed from the original Apache Git repositories at the parent commit.** Evidence:

1. The unit matches the thesis task (commit diff → defect-inducing?).
2. Parent hashes are included, and reconstruction reproduces the parent for all 27,319 commits and the churn for 99.98% [V].
3. Its small Java repositories make full-snapshot context extraction cheap, deterministic, and reproducible: building the BM25 pool and ranking takes about one second per commit [V].
4. Fix lines are manually validated, and line-level labels allow diagnostic analysis (does the context or rationale touch the labelled lines?).
5. It is the standard benchmark in semantic and LLM-era JIT-DP: JIT-Fine [V], CodeFlowLM [A], and JIT-LSM, whose data and evaluation subsets are JIT-Defect4J commits [V]. JIT-Smart is commonly reported to use it, but this was not verified. This aids comparability.

**Why not JIT-Defect-Extended as the primary source** [I]: it adds no labels or commits; it lacks 46 test commits; its `added_lines` lists are filtered in an undocumented way; it has no license file; it embeds the label in every record and path; and it cannot provide cross-file context. Use it only to cross-check reconstructed same-file content on a sample and to identify JIT-LSM's evaluation subsets (optional baseline B5 in [03-experimental-design.md](03-experimental-design.md) §9).

**What the Phase 2 review changed and what it did not.** The choice of dataset stands. Three things changed: inputs are restricted to `.java` files, eligibility is measured in tokens (cap 12,000), and the newer public derivative is treated as a leakage and contamination risk rather than as a data source.

**Trade-offs you accept:**

- Low prevalence (8.5%), which calls for enriched sampling.
- Residual SZZ noise, which calls for sensitivity analyses.
- An unclear license, which calls for contacting the authors.
- Pre-2020 code, and labels that have been public as JSON since July 2025, which raise contamination risk (see [05-risks.md](05-risks.md), Risk 4).

**Fallback: ApacheJIT.** Choose it if JIT-Defect4J licensing blocks use, or if more positives or projects are needed. Accept plain-SZZ labels with two-sided censoring, the Hadoop field anomaly, and costlier retrieval. Recommended handling:

- Use 2010–2017 commits only.
- Merge or exclude the Hadoop groups.
- Map project to repository explicitly and verify every hash.

**When to switch.** Switch to the fallback if any of the following happens:

- Automated reconstruction fails for more than 2% of sampled JIT-Defect4J commits.
- The authors decline data reuse.
- Fewer than 300 eligible defective test commits remain after the token limits.

## 7. Checks still incomplete

| # | Check | How to close it |
|---|---|---|
| 1 | Read the JIT-Fine paper: SZZ variant, clean-set definition, split protocol (why 159 test commits are older than the newest train commit) | Read Ni2022 §3 |
| 2 | JIT-Defect4J license and redistribution terms | Email the authors; cite the data-availability statement |
| 3 | ~~Reconstruction across all projects~~ **Closed:** 99.98% of all 27,319 commits | [feasibility/audit_dataset.py](../feasibility/audit_dataset.py) |
| 4 | ~~Token distributions across all projects~~ **Closed** for diff sizes (all splits) and same-file pools (validation) | Same script |
| 4a | Label quality of defective commits | Gate 1: review 30 defective validation commits against their fixes |
| 5 | Accuracy of enclosing-method boundaries | Gate 2: manual check of 30+ changes (tree-sitter vs Git) |
| 5a | Why 164 commits are missing from JIT-Defect-Extended, and how JIT-LSM sampled its subsets | Read Huang2026 (library access) or ask its authors |
| 6 | ~~Duplicated or cherry-picked diffs~~ **Closed:** 148 patch-id groups, none across train and test | Same script; near-duplicates (not identical patches) are still unchecked |
| 7 | ReDef schema, license, availability of commit IDs | Download figshare data manually (only if the robustness study is adopted) |
| 8 | Contamination exposure of the chosen LLMs | Document training cutoffs; label-recall probe in the engineering pilot (Gate 3); issue-key mention check and year stratification |
| 9 | Explanation of the ApacheJIT Hadoop anomaly | Only needed if the fallback is used: inspect the replication notebooks |

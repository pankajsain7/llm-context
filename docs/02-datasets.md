# B. Dataset Comparison and C. Recommendation

Status: research phase, 2026-10-19; revised after the Phase 2 critical review, the external audit, and **the second external audit** (JIT-Fine paper read in full; split protocol reconstructed; test-split exposure recorded in §8). Evidence labels: **[V]** verified from real files or Git in this review, **[P]** taken from the paper (full text read), **[A]** taken from an abstract or dataset record only, **[I]** interpretation, **[NV]** not verified. Numbers can be reproduced with [feasibility/verify_datasets.py](../feasibility/verify_datasets.py), [feasibility/measure_inputs.py](../feasibility/measure_inputs.py), and [feasibility/audit_dataset.py](../feasibility/audit_dataset.py); label-free outputs are in [feasibility/outputs/](../feasibility/outputs/); the setup is described in [04-feasibility-demo.md](04-feasibility-demo.md).

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
| Provided split | Per project ≈60/20/20, time-ordered and then **class-stratified**: 94.8% of commits sit where a strict time split puts them; the rest were swapped to equalise defect rates (§2, item 10) [V/P] | None in the layout; recoverable by joining with JIT-Defect4J [V] | Time-based: balanced train 2003–2016, test 2017–2019 [V/P] | Per-repository chronological 80/10/10 [P] | [NV] |
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
5. **Label construction and noise** (Ni2022 §4 and §6.3, full text read [P]):
   1. LLTC4J (Herbold2022b): 2,328 bugs in 28 Java projects, manually validated, fixed by 3,498 commits. Four participants labelled every changed line of each fixing commit; a line label needs agreement of at least three.
   2. A fixing commit is a candidate if at least one line is agreed as "contributing to the bug-fixing".
   3. For every such line, `git blame` (via PyDriller) on the fixing commit's parent names the bug-inducing commit (BIC). The blamed lines become the buggy lines of the BIC.
   4. Every other commit is clean, so **bug-fixing commits that are not BICs stay in the clean class** [P; the paper names no exclusion].
   5. Filters: Java files only, non-functional changes (for example comments) removed, commits changing more than 10,000 lines or 100 files dropped, commits without added lines dropped. Five projects were dropped for lack of raters and two because many commits were missing from GitHub, leaving 21.
   6. Kamei features come from CommitGuru.

   So the **fix side is manually validated, but the BIC side is plain blame**. The paper names no issue-date filter and no whitespace-, comment-, or refactoring-aware blame [P]. Whether its code used such options was not checked [NV]. We found a formatting-only commit labelled defective (Example 1 in [04-feasibility-demo.md](04-feasibility-demo.md)) [V]. The label-quality audit is in §2a.
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
10. **Splits and leakage.**
    - **What the paper says** [P, Ni2022 §6.1]: per project, commits are sorted by timestamp; the first 80% are training data and the remaining 20% test data; "we also keep the distribution as same as the original ones in training and testing data". The released files split ≈60/20/20; the paper does not describe the validation split.
    - **What the data shows** [V, all commits; class figures from train and validation only]:
      - The split is per project. The dataset's author times equal Git's for 100% of commits.
      - 94.8% of all commits sit exactly where a strict per-project 60/20/20 time split would put them (97.5% for test against an 80/20 split; author and committer time give identical results).
      - Within train plus validation, 652 commits are out of time order. The 326 moved into validation are **94.2% defective**; the 326 moved into train are 5.8% defective. Per-project defect rates of train and validation differ by 0.15 percentage points on average, against 1.7 points expected under a random split (2,000 permutations, none as close).
      - [I] So the authors equalised each project's defect rate by swapping commits between periods. The validation period's own defect rate was only 3.1%, presumably because recent defects had not yet been fixed (right censoring), so 307 of the 467 defective validation commits were taken from the training period.
      - Test, label-blind: 342 test commits lie before their project's 80th time percentile, and 614 are older than their project's newest validation commit; 159 are older than the newest train commit. By analogy they are probably mostly defective [I]. **This was not checked and must not be checked with test labels.**
    - **Consequences:**
      - *Commit age predicts the label.* On validation, author time alone reaches a within-project AUC of 0.844 (pooled 0.688) [V].
      - *Supervised baselines.* Logistic regression trained on train, scored on validation: 14 Kamei features AUC 0.792 overall vs 0.768 inside the chronological window; history and experience features alone 0.689 vs 0.579; size only 0.761 vs 0.773 [V]. Time-dependent features are inflated by the split; published JIT-Defect4J baseline results probably are too [I]. Report baselines on the original split (for comparability) *and* in a strictly chronological re-split of train plus validation (test stays locked), and never call the original split "time-based".
      - *Zero-shot LLMs.* There is no training leakage, but in the evaluation split the commit's era carries label information. Any cue for the era (old Java idioms, library versions, code from the parent snapshot) can raise absolute performance without defect knowledge, and C1–C3 show more snapshot code than C0. C2−C3 is protected because both draw on the same snapshot; C1−C0 and C2−C0 are not. Handling is decision D28 ([03-experimental-design.md](03-experimental-design.md) L15).
    - **Duplicates** (`git patch-id --stable` on the Java diff): 312 commits share a patch with another commit, in 148 groups: 122 within train, 13 within valid, 9 within test, 3 across train and valid, 1 across test and valid, none across train and test. Two commits have no Java change.
11. **License, access, storage.** There is **no license file** in the JIT-Fine repository [V]. The upstream code is Apache-2.0. Before redistributing derived data, ask the authors and confirm the data-availability statement in the paper. Storage: 75 MB zip, and small clones.
12. **Difficulty.** Low to moderate. The pickles load with pandas 3.0.6 (with deprecation warnings only) [V].

**Size effects** [V]: the defect rate rises from 2.1% to 20.2% across churn quintiles, so any size limit removes defective commits disproportionately. Measured in tokens of the Java diff across all 21 projects:

| Diff tokens ≤ | Test, all commits (label-blind) | Train defective | Validation defective | Train + validation clean |
|---|---|---|---|---|
| 8,000 | 90.9% | 72.1% | 76.2% | 93.3–95.3% |
| 12,000 | 94.3% | 80.1% | 83.1% | 96.2–97.2% |
| 16,000 | 95.7% | 85.4% | 86.9% | 97.7–98.1% |

The 4-project estimate from Phase 2 (93.1% of defective commits kept at 12,000) was too optimistic. Class-specific figures here come from train and validation; test labels were not used for them. Earlier test-label exposure is listed in §8.

### 2a. Label-quality audit of 30 defective validation commits (Gate 1, D26)

**Method.** 30 defective validation commits, sampled with seed 2026 ([feasibility/label_audit.py](../feasibility/label_audit.py); evidence files in `thesis-scratch\label_audit\`, outside Git because they reveal labels). The dataset does not publish which fixing commit produced each label, so the script searches *forward*: later commits (up to 2019, at most 30 files each, no merges, renames not followed) whose deleted lines `git blame` back to the candidate, at most five per candidate, with the Jira type and creation date of every issue key they mention. Two mechanical flags: the candidate is newer than every linked issue report, and every substantive linked line already existed before the candidate (reformatted or moved code). Each case was then rated P (the candidate wrote the code a later bug fix corrects), F (the fix touches code the candidate only reformatted, moved, or refactored), T (the fix's bug was reported before the candidate existed), N (no bug fix among the links), or U (unclear).

**First rating (AI-assisted, not yet checked by a human)** [V for the evidence; the ratings are judgements]:

| Rating | Count | Examples |
|---|---|---|
| P, plausible | 8 | `13bbcec2` (commons-vfs) cast to the wrong type, fixed five days later as a ClassCastException; `dd713684` (commons-compress) timestamp handling, fixed under COMPRESS-289 (Bug) |
| F, pre-existing fault | 3 | `297ac27a` (ant-ivy) and `20126201` (commons-vfs) are reformatting or checkstyle commits |
| T, bug reported before the candidate | 2 | `ca7a127a` and `dbcf7dd6` (commons-math) merge `*Impl` classes into their interfaces on 2011-11-26; the linked fix is for MATH-692 (Bug), reported 2011-10-18. They moved code that was already faulty |
| N, not traceable with this evidence | 14 | Four candidates are themselves fixes (for example `9c95a92a`, "avoid CCE in equals", VFS-138), and their only later links are package renames or checkstyle sweeps |
| U, unclear | 3 | `178136b6` (commons-net) changed the call that the NET-579 fix later replaced, but the missing hostname check predates it |

**Reading.** The mechanical flags were weak: "newer than every linked report" fired for 4 of 30 (two became T on reading; in the other two the linked issue was not a bug the candidate could have caused), and "pre-existing lines" fired for none, because reformatting that joins or splits lines escapes a whitespace-normalised comparison (as in Example 1). At least 5 of 30 labels (17%; 95% Wilson interval 7–34%) have direct evidence against them (F or T). Only 8 (27%) could be confirmed. Most cases cannot be resolved without the dataset's own fix-to-BIC mapping. This agrees with Herbold2022a's finding that blame-based bug-inducing labels are often wrong, and with Example 1. Two repeated AI ratings of the same evidence disagreed on several cases, so these counts are a **low-reliability first pass**.

**Consequences.** The label stays an observed SZZ proxy (no relabelling and no filtering in the primary analysis). S8 (high-confidence subset) gains weight. The audit can only become precise with the LLTC4J fix list (SmartSHARK release) or the JIT-Fine authors' BIC-to-fix mapping; ask for the mapping in the data-permission email (D18). A human second rater still has to rate 10 of the 30 (D26).

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

**What the Phase 2 review changed and what it did not.** The choice of dataset stands. Three things changed: inputs are restricted to `.java` files, eligibility is measured in tokens (cap 12,000 in Phase 2, raised to **16,000** after the all-project audit, D4), and the newer public derivative is treated as a leakage and contamination risk rather than as a data source.

**Trade-offs you accept:**

- Low prevalence (8.5%), which calls for enriched sampling.
- Residual SZZ noise, which calls for sensitivity analyses.
- An unclear license, which calls for contacting the authors.
- Pre-2020 code, and labels that have been public since August 2022 (JIT-Fine `data.zip`) and as plain JSON with code since July 2025 (JIT-Defect-Extended), which raise contamination risk (see [05-risks.md](05-risks.md), Risk 4).

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
| 1 | ~~Read the JIT-Fine paper~~ **Closed:** label protocol and split protocol in §2 items 5 and 10 | Ni2022 §4, §6.1 |
| 2 | JIT-Defect4J license and redistribution terms | Email the authors; cite the data-availability statement |
| 3 | ~~Reconstruction across all projects~~ **Closed:** 99.98% of all 27,319 commits | [feasibility/audit_dataset.py](../feasibility/audit_dataset.py) |
| 4 | ~~Token distributions across all projects~~ **Closed** for diff sizes (all splits) and same-file pools (validation) | Same script |
| 4a | Label quality of defective commits | First pass done (§2a): ≥ 17% contradicted, 27% confirmed, the rest untraceable. Open: human second rater on 10; the dataset's BIC-to-fix mapping from the authors or SmartSHARK |
| 5 | Accuracy of enclosing-method boundaries | Gate 2: manual check of 30+ changes (tree-sitter vs Git) |
| 5a | Why 164 commits are missing from JIT-Defect-Extended, and how JIT-LSM sampled its subsets | Read Huang2026 (library access) or ask its authors |
| 6 | ~~Duplicated or cherry-picked diffs~~ **Closed:** 148 patch-id groups, none across train and test | Same script; near-duplicates (not identical patches) are still unchecked |
| 7 | ReDef schema, license, availability of commit IDs | Download figshare data manually (only if the robustness study is adopted) |
| 8 | Contamination exposure of the chosen LLMs | Document training cutoffs; label-recall probe in the engineering pilot (Gate 3); issue-key mention check and year stratification |
| 9 | Explanation of the ApacheJIT Hadoop anomaly | Only needed if the fallback is used: inspect the replication notebooks |

## 8. Test-split exposure (authoritative record)

Earlier documents said that test labels were "not read". That was true only of the all-project audit and of class-specific size figures. The second external audit pointed this out; the complete record follows [V, from the scripts in the repository and the ad-hoc scripts in `C:\Users\psain\thesis-scratch\*.py`]. **No LLM was called on any test commit, and no prediction of any kind was made on the test split.**

**Individual test records displayed with their labels or label-bearing data:**

| Commit | How | Shown |
|---|---|---|
| `76c125c3b74a…` (commons-codec) | Demo Example 1; selected as the earliest defective commons-codec test commit | Label (defective), message, line-level label, later fix (analysis) |
| `4063338a3c8c…` (commons-codec) | Demo Example 2; first clean commons-codec test commit with at most two files | Label (clean), message |
| `6e710a1f78a4…` | First row of `features_test.pkl`, `changes_test.pkl`, and the line-level file, displayed by a schema inspection | Label (defective) and two line-level rows |
| `1f73722ffb37…` | Second row of `features_test.pkl` in the same inspection | The row was printed truncated; whether the label column was visible is unknown |
| up to 2 unidentified commons-codec records | `split_check.py` printed the two earliest defective commons-codec test commits (one is `76c125c3`) and the earliest clean one with at most two files (possibly `4063338a`) | Labels and messages |

The rows were identified by position only, without printing labels again (2026-10-19). Identifying the two unidentified records would need another test-label lookup; that is left to the supervisor (D27).

**Aggregate test-label statistics computed in Phase 1 and Phase 2:** split sizes and defect counts (5,480 commits, 475 defective); per-project defect rates over all splits; the defect rate by churn quintile over all splits; defective commits kept under churn limits of 200, 400, and 600 lines; the defect rate of small test commits (at most 5 files and 200 changed lines) vs the rest; the line-level label rate (26,104 lines, 7.89% buggy); defective counts in JIT-LSM's test subsets (150 and 459) and in JIT-Defect-Extended's test commits (452).

**Label-blind test information (allowed):** existence, parents, churn reconstruction, dates, patch IDs, diff sizes, and time-order positions (the all-project audit and the manifest). `feasibility/audit_dataset.py` and `python -m jitctx build-manifest` load `features_test.pkl` for its label-free columns and discard the label column without using it.

**Influence on the design.** Revision 1 chose its size limit from test-split churn statistics. That limit was replaced: the current 16,000-token cap (D4) was chosen from train and validation class figures plus label-blind test retention. No other design parameter is known to depend on test labels; the per-project prevalence is published in Ni2022 Table 2 anyway.

**Rules from now on** (also [../AGENTS.md](../AGENTS.md)):

1. Test labels and label-bearing test files are not opened before Gate 5. `verify_datasets.py` blanks test labels unless `--allow-test-labels` is given, which only reproduces the figures above; `jitctx make-contexts` refuses the test split without `--allow-test` (after the Gate 4 freeze).
2. Every design choice (prompt, model, budget, chunking, filters, thresholds, metric) is made on train or validation data and recorded in [06-milestone-and-decisions.md](06-milestone-and-decisions.md).
3. The displayed test records are excluded from the confirmatory sample if D27 is approved; the exclusion is reported.
4. Any further unavoidable test access is recorded here with date, purpose, and output.

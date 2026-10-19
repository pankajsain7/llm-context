# E. Feasibility Demonstration (real data)

Status: executed 2026-10-19; §5 added in the Phase 2 review; **updated after the external audit** (prototype defects fixed and tested, demo re-run, all-project audit in §5.6, label-free outputs in [feasibility/outputs/](../feasibility/outputs/)). **Every example below is a real dataset record and real Git output. Nothing is synthetic.** Commands that look at *later* history (marked "analysis only") were used to judge label quality. Such information must never enter prompts.

## 1. Environment and reproduction

- Windows, PowerShell 5.1, Git 2.55.0.windows.5 (not on PATH; called from `C:\Program Files\Git\cmd`), Python 3.12.2. Exact package versions: [feasibility/requirements.txt](../feasibility/requirements.txt).
- Data and clones live in `C:\Users\psain\thesis-scratch`, **outside OneDrive**. Repositories and datasets should not be synced. The HEAD of every clone used is listed in [feasibility/outputs/repository_heads.txt](../feasibility/outputs/repository_heads.txt).
- SHA-256 of the inputs, so that others can check they use the same files:

  | File | SHA-256 |
  |---|---|
  | `data.zip` (JIT-Fine) | `9e5ca1a393b70ee7e87c410b162005958775f3f3732f9f83da9dd24a7dfe2b47` |
  | `features_train.pkl` | `0b9992d77cd07f45a71bd327a3d408ed3f0ab7a907ffdc10f9916a8f226dc42a` |
  | `features_valid.pkl` | `e2ee48d5cd9e7f59bea726d4f6a71ef58712ae58d3388d8195a798369cf0d2cf` |
  | `features_test.pkl` | `136eebbb1c1719bffbfed8f0d686e3c015c5756a7b3c43d6f700a07687ab58fa` |

```powershell
$env:Path = "C:\Program Files\Git\cmd;" + $env:Path
New-Item -ItemType Directory -Force C:\Users\psain\thesis-scratch | Out-Null
Set-Location C:\Users\psain\thesis-scratch
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r "$env:USERPROFILE\OneDrive - mhp-group.com\Desktop\LLM-Context\feasibility\requirements.txt"
New-Item -ItemType Directory -Force apachejit, jitfine, repos | Out-Null
Invoke-WebRequest https://raw.githubusercontent.com/hosseinkshvrz/apachejit/master/dataset/apachejit_total.csv -OutFile apachejit\apachejit_total.csv
Invoke-WebRequest https://github.com/jacknichao/JIT-Fine/raw/master/data.zip -OutFile jitfine\data.zip
Expand-Archive jitfine\data.zip -DestinationPath jitfine\data
git clone https://github.com/apache/commons-codec.git repos/commons-codec
git clone --filter=blob:none --no-checkout https://github.com/apache/zookeeper.git repos/zookeeper

$fs = "$env:USERPROFILE\OneDrive - mhp-group.com\Desktop\LLM-Context\feasibility"
.\.venv\Scripts\python.exe "$fs\verify_datasets.py" --root .
.\.venv\Scripts\python.exe "$fs\context_demo.py" repos\commons-codec 76c125c3b74a390a39cdcd6666cf7e9cea0e5c1d 2000 0

# Phase 2 additions (sample measurements, superseded by the full audit below)
foreach ($p in "commons-io", "commons-lang", "ant-ivy") { git clone "https://github.com/apache/$p.git" "repos/$p" }
$projects = "commons-codec", "commons-io", "commons-lang", "ant-ivy"
.\.venv\Scripts\python.exe "$fs\measure_inputs.py" --root . --split valid --projects $projects --per-project 50 --bm25-timing 5
.\.venv\Scripts\python.exe "$fs\measure_inputs.py" --root . --split valid --projects $projects --per-project 50 --bm25-timing 0 --defective-only

# After the external audit: all 21 repositories, full audit (about 6 minutes), prototype tests
$all = "ant-ivy","commons-bcel","commons-beanutils","commons-codec","commons-collections","commons-compress","commons-configuration","commons-dbcp","commons-digester","commons-io","commons-jcs","commons-lang","commons-math","commons-net","commons-scxml","commons-validator","commons-vfs","giraph","gora","opennlp","parquet-mr"
foreach ($p in $all) { if (-not (Test-Path "repos/$p")) { git clone --no-checkout "https://github.com/apache/$p.git" "repos/$p" } }
.\.venv\Scripts\python.exe "$fs\audit_dataset.py" --root .
.\.venv\Scripts\python.exe -m pytest $fs -q -p no:cacheprovider
# Optional: JIT-LSM evaluation subsets (Git LFS objects, about 270 MB)
New-Item -ItemType Directory -Force jitext | Out-Null
foreach ($f in "balanced_dataset_1000.json", "unbalanced_dataset_1730.json") {
  Invoke-WebRequest "https://media.githubusercontent.com/media/JIT-LSM/JIT_LSM/main/LargeModel/data/$f" -OutFile "jitext\$f"
}
```

The scripts are [feasibility/verify_datasets.py](../feasibility/verify_datasets.py) (dataset statistics), [feasibility/context_demo.py](../feasibility/context_demo.py) (a prototype of the C0 diff and the C2/C3 blocks, not the experiment pipeline), [feasibility/measure_inputs.py](../feasibility/measure_inputs.py) (Phase 2 sample measurements), [feasibility/audit_dataset.py](../feasibility/audit_dataset.py) (the all-project audit), and [feasibility/test_context_demo.py](../feasibility/test_context_demo.py) (129 tests). The `--defective-only` run reads validation labels; both measurement scripts refuse to read test labels.

## 2. Example 1: a defective-labelled JIT-Defect4J commit

**Dataset record** (`features_test.pkl`):

| Field | Value |
|---|---|
| project | commons-codec |
| commit_hash | `76c125c3b74a390a39cdcd6666cf7e9cea0e5c1d` |
| parent_hashes | `09f58fbc8956b05aec9cdc7ce9d153639917f24d` |
| author_date | Wed Aug 29 21:02:47 2012 +0000 |
| la / ld / nf | 86 / 133 / 1 |
| fileschanged | `src/main/java/org/apache/commons/codec/language/DoubleMetaphone.java` |
| is_buggy_commit | **1.0 (defective)** |
| commit_message (tokenised in the dataset) | "Checkstyle , javadoc and formatting fixes ." |

**Git reconstruction.** The commit exists. `76c125c3^` resolves to `09f58fbc…`, which matches `parent_hashes`. `git show --stat` reports "1 file changed, 86 insertions(+), 133 deletions(-)", which matches la/ld/nf. ✔

**Line-level label.** The line-level file has 114 changed lines for this commit. **Exactly one** is labelled buggy: the added line `return doubleMetaphone(value1, alternate).equals(doubleMetaphone(value2, alternate));`.

**The diff hunk that contains it** (real `git show` output):

```diff
@@ -241,11 +240,8 @@ public class DoubleMetaphone implements StringEncoder {
      * @return {@code true} if the encoded <code>String</code>s are equal;
      *          {@code false} otherwise.
      */
-    public boolean isDoubleMetaphoneEqual(String value1,
-                                          String value2,
-                                          boolean alternate) {
-        return doubleMetaphone(value1, alternate).equals(doubleMetaphone
-                                                         (value2, alternate));
+    public boolean isDoubleMetaphoneEqual(String value1, String value2, boolean alternate) {
+        return doubleMetaphone(value1, alternate).equals(doubleMetaphone(value2, alternate));
     }
 
     /**
```

**Analysis only (uses future history; never a model input):**

- `git log -S"doubleMetaphone(value1, alternate).equals"` shows that the expression was later removed by `37ba197e` (2014-04-10), whose change-log entry reads *"CODEC-184 … NullPointerException in DoubleMetaPhone.isDoubleMetaphoneEqual when using empty strings"*.
- At the **parent** snapshot, the callee already returns `null` for inputs that `cleanInput` rejects:

  ```java
  public String doubleMetaphone(String value, boolean alternate) {
      value = cleanInput(value);
      if (value == null) {
          return null;
      }
  ```

**Interpretation [I].** The labelled change is a pure line re-wrap. The defect (an NPE on empty input) existed before this commit. SZZ blamed the last commit that touched the line, so the label is very likely a **false positive**. Two consequences for the thesis:

1. Label noise caps the measurable accuracy.
2. Context can raise scores *for the wrong reason*. A model shown the callee might flag the pre-existing NPE and match the noisy label.

Hence sensitivity analysis S2 (exclude formatting-only commits) and S8 (high-confidence subset) in [03-experimental-design.md](03-experimental-design.md).

**Possible context sources, built from the parent snapshot only.** Re-run after the audit fixes (`context_demo.py`, B = 2,000, seed 0, `o200k_base`, license headers stripped, BM25 over code lines only, zero-score windows excluded):

| Condition | Content | Tokens |
|---|---|---|
| C0 | Java-only `git diff -U3 -M` (41 hunks over the file) | 6,466 |
| Pool | 102 `.java` files (changed file excluded), 1,143 windows, 1,068 of them scoring above 0 | 297,506 |
| C2 | Status `line_limit`: the top-ranked window, `Base64Codec13Test.java` 98–137, holds 5,813 tokens of Base64 test strings, so it was cut to lines 98–111 and nothing else fit | 1,884 |
| C3 | Random windows: PhoneticEngine 238–277 and 458–497, HexTest 138–177, Base32Test 39–78, UnixCrypt 217–256, Sha2Crypt 197–202 (cut) | 1,872 (99.4% of C2), status `ok` |

[I] The fixed code works as specified, and that exposes a design weakness: 40-line windows do not bound tokens (median 385, maximum 18,761 tokens in this pool), so one data-heavy window can take the whole budget. Gate 2 must bound windows by tokens as well ([03-experimental-design.md](03-experimental-design.md) §5.6). The revision 1 numbers previously shown here (B = 4,000) came from the defective prototype and are withdrawn.

- **Callers at the parent** (`git grep -w isDoubleMetaphoneEqual 09f58fbc -- "*.java"`): one same-file overload (line 231) and 14 call sites in `DoubleMetaphoneTest.java`.
- **What-if: changed file kept in the pool** (hunk windows excluded; measured with the revision 1 prototype). BM25 ranked three same-file windows first (`DoubleMetaphone.java` 161–200, 101–140, 201–240; scores 61.3, 54.2, 39.4). C2 would then collapse into local context, so the design excludes changed files from the C2 pool. The callee window was not available in either variant because the 41 formatting hunks overlap most of the file.

## 3. Example 2: a clean JIT-Defect4J commit

- **Record:** commons-codec `4063338a3c8c87657a75c3c45a8b69560fee0e57`, parent `c5154bc584847d19e75c421b71e2f3499164d2a9`, 2014-11-10, "Sort test methods .", la/ld/nf = 55/55/1, `src/test/java/org/apache/commons/codec/binary/HexTest.java`, `is_buggy_commit = 0`.
- **Git:** the parent matches, and `git show --stat` gives 55 insertions and 55 deletions. ✔
- **Context** (re-run after the audit fixes, B = 2,000, seed 0):
  - C0: 1,850 tokens.
  - Pool: 114 files, 1,386 windows (1,197 scoring above 0), 346,279 tokens.
  - C2 (1,974 tokens, `ok`): four `Base64Test` windows (98–137, 1198–1237, 518–557, 1158–1196).
  - C3 (1,965 tokens, 99.5% of C2, `ok`): Base64Test 638–677, Base32InputStreamTest 18–57, DoubleMetaphoneTest 578–617 and 818–830, HmacUtils 218–257.
- **Interpretation [I].** BM25 retrieved *lexically similar sibling tests*, not the class under test (`Hex.java`). This is why the design makes a manipulation check (relevance proxy plus manual audit) a precondition for interpreting RQ2.

## 4. Example 3: ApacheJIT reconstruction and a data anomaly

- **ZooKeeper** (partial clone, blobs fetched on demand):

  | Commit | Label | Parent | Message | numstat | Dataset la/ld/nf |
  |---|---|---|---|---|---|
  | `1061ac279cd4785951219c1c1631c4156de913fc` | buggy | `efa6ab6e…` | "Use int32_t vs int for all integer data fields in the generated C code" | 3+1+7 / 2+1+7 over 3 files | 11/10/3 ✔ |
  | `925c425a73910bab9e40bc044329136379adadaa` | clean | `7563bfe9…` | (logging and trace fixes) | 8/8, 2 files | 8/8/2 ✔ |

- **Hadoop.** Commit `5a0051f4da6e102846d795a7965a6a18216d74f7` is labelled `apache/hadoop-hdfs` (buggy, 2015). The GitHub API resolves it in **`apache/hadoop`** (HDFS-7681, parent `cff05bff…`, 15 additions and 6 deletions over 4 files); `apache/hadoop-hdfs` returns HTTP 422. In the CSV, `apache/hadoop` has 11,964 rows and **0 buggy**. The project field therefore does not identify the repository and is label-correlated. Details are in [02-datasets.md](02-datasets.md) §3.

## 5. Phase 2 measurements (validation split, label-blind unless stated)

**Sample.** 200 random validation commits (seed 1; 50 each from commons-codec, commons-io, commons-lang, and ant-ivy), plus 101 *defective* validation commits from the same projects (all of them, capped at 50 per project). Tokens are `o200k_base`. The label-free per-commit results are in [feasibility/outputs/measure_valid.csv](../feasibility/outputs/measure_valid.csv).

**Caveat (external audit).** Four projects with equal allocation are not a proportional sample of the dataset, and the pool figures below were measured before license headers were stripped. Where §5.6 has all-project figures, they **supersede** §5.1–5.2.

### 5.1 Reconstruction

| Check | Random (n = 200) | Defective (n = 101) |
|---|---|---|
| Commit resolves, and `<sha>^` equals `parent_hashes` | 100% | 100% |
| Numstat over **all** files equals `la/ld` | 68.5% | not measured |
| Numstat over `.java` files (`-- '*.java'`) equals `la/ld` | **100%** | **100%** |

So JIT-Defect4J's churn covers Java files only, and §5.6 shows that it also leaves out `package-info.java`. This verifies the benchmark's *metric* definition; restricting the model's input to the same files is a scope decision.

### 5.2 Input sizes

| Quantity (tokens) | Random: median / p90 / p95 | Defective: median / p90 / p95 |
|---|---|---|
| T(C0), Java-only `git diff -U3 -M` | 696 / 4,077 / 5,928 | 2,088 / 10,539 / 13,634 |
| `git diff --function-context` (revision 1's C1) | 1,372 / 6,986 / 11,407 | 3,865 / 15,698 / 30,842 |
| Enclosing-method lines, diff lines masked | 634 / 3,406 / 6,108 | 1,103 / 8,821 / 12,202 |
| Same-file pool, diff lines masked | 6,048 / 51,675 / 66,010 | 9,591 / 79,617 / 106,037 |

| Share of commits | Random | Defective |
|---|---|---|
| T(C0) ≤ 8,000 | 96.5% | 85.1% |
| T(C0) ≤ 12,000 | 97.0% | 93.1% |
| Same-file pool ≥ 1,000 / 2,000 / 4,000 | 90.5% / 83.0% / 63.5% | 89.1% / 86.1% / 75.2% |
| Empty same-file pool (only new files, or every parent line already shown in the diff) | 3.5% | 5.0% |

Other figures: the median is 34.4 diff tokens per changed line for random commits and 18.9 for defective commits; the mean T(C0) of eligible commits (≤ 12,000) is 1,302 (random) and 3,028 (defective). Revision 1 had *assumed* a median T(C0) of 1,500 and 20–30 tokens per changed line. Pool sizes were measured before license headers are stripped, so they slightly overstate the usable pool.

**Same-file pool of the two demo commits** (diff lines masked): `76c125c3` has 1,107 lines at the parent, of which the diff shows 447. The masked pool is 5,499 tokens, 3,657 of them inside enclosing methods. `4063338a`: 453 lines, 117 shown, pool 2,776 tokens, 268 inside enclosing methods.

### 5.3 Retrieval cost

Building the cross-file pool from the parent snapshot and ranking it with BM25 took a median of 0.9 s per commit (maximum 1.7 s) for 20 commits; the median pool held 2,703 windows.

### 5.4 JIT-Defect-Extended record for Example 1

The record `dataset/buggy/commons-codec/76c125c3b74a390a39cdcd6666cf7e9cea0e5c1d.json` exists in <https://github.com/JIT-LSM/JIT-Defect-Extended>, with the same label as JIT-Defect4J. Its structure, with values abbreviated:

```text
expert_features: the 25 JIT-Defect4J fields, including commit_message and is_buggy_commit
change_message:
  url: https://github.com/apache/commons-codec
  paths: [src/main/java/org/apache/commons/codec/language/DoubleMetaphone.java]
  commit_info: message, git-svn-id, author, date, "Java Files Changed"
  <path>:
    summary, code (1,193 lines: 974 unchanged, 133 "- ", 86 "+ "),
    added_lines (51), deleted_lines (63), added_buggy (line labels)
```

The whole-file `code` view agrees with Git (86 added, 133 deleted), but the `added_lines`/`deleted_lines` lists are filtered. The label is visible in the path, in `expert_features`, and in `added_buggy`, which is why the prompt builder must never read these files (design L2).

### 5.5 JIT-LSM evaluation subsets

Both files from `JIT_LSM/LargeModel/data/` were downloaded and joined with JIT-Defect4J by commit hash:

| File | Commits | Split | Defective | Median churn (max) |
|---|---|---|---|---|
| `unbalanced_dataset_1730.json` | 1,730 | all test | 150 (8.7%) | 30 (7,160) |
| `balanced_dataset_1000.json` | 1,000 | all test | 459 (45.9%) | 52 (7,160) |

691 commits are in both files. The balanced file contains 459 of the 475 defective test commits. 4 and 12 commits respectively are absent from the published JIT-Defect-Extended. The commit-level label is not stored as a field in these files; it was taken from JIT-Defect4J, and it agrees with which records have non-empty `added_buggy` lists (150 and 459).

### 5.6 All-project audit (after the external review)

[feasibility/audit_dataset.py](../feasibility/audit_dataset.py) checked all 27,319 commits against the 21 repositories in about six minutes. It never loads test labels; class-specific figures use train and validation only. Outputs: [feasibility/outputs/audit_summary.txt](../feasibility/outputs/audit_summary.txt) and the label-free per-commit file [feasibility/outputs/audit_commits.csv](../feasibility/outputs/audit_commits.csv).

| Check | Train | Validation | Test |
|---|---|---|---|
| Commit exists, one parent, parent matches | 100% | 100% | 100% |
| Numstat (Java files except `package-info.java`) equals `la/ld` | 16,371 / 16,374 | 5,464 / 5,465 | 5,479 / 5,480 |
| Diff ≤ 8,000 / 12,000 / 16,000 tokens (label-blind) | 91.5 / 94.8 / 96.7% | 93.7 / 96.0 / 97.1% | 90.9 / 94.3 / 95.7% |
| Median / p90 / p95 diff tokens | 930 / 6,976 / 12,360 | 805 / 5,382 / 10,015 | 881 / 7,353 / 13,700 |

- **`package-info.java`.** With every `.java` file counted, 195 commits did not match. In 190 of them the only difference was `package-info.java` files, which the benchmark's metrics and file lists leave out (368 of the 380 omitted files). Five commits stay unexplained (giraph 3, opennlp 1, parquet-mr 1).
- **Dates.** The dataset's author times equal Git's for every commit. 159 test commits (2.9%, 11 projects) are older than their project's newest train commit, by author and identically by committer time; 92 are older than the project's oldest train commit (median gap 3,032 days). 10.4% of validation commits behave the same way.
- **Duplicates.** 312 commits share a Java patch-id in 148 groups; 4 groups cross splits (3 train–validation, 1 test–validation), none train–test.
- **By class** (train / validation): defective commits fit 16,000 tokens in 85.4% / 86.9% of cases, 12,000 in 80.1% / 83.1%; clean commits in 97.7% / 98.1% and 96.2% / 97.2%.
- **Same-file pool** (validation, license header stripped, diff lines masked): at least 1,000 / 2,000 / 4,000 tokens for 81.2% / 69.4% / 52.4% of commits (defective 89.9% / 83.5% / 69.2%; clean 80.4% / 68.1% / 50.8%); empty for 5.1%.
- **Mean diff size under a 16,000-token cap** (train and validation): 1,777 tokens for clean and 3,860 for defective commits.

**Prototype defects reported by the audit, reproduced and fixed** ([feasibility/test_context_demo.py](../feasibility/test_context_demo.py), 129 tests pass):

| Defect | Reproduction | Fix |
|---|---|---|
| `chunk()` skipped trailing lines | Files of 41 / 50 / 59 / 79 / 99 lines lost 1 / 10 / 19 / 19 / 19 lines | A final window ending at the last line; coverage tested for 0–120 lines |
| Zero-score windows were selected | A query with no overlap still returned windows | Only windows scoring above 0; `no_hits` status |
| Token matching not enforced | C3 reached 95.5% of C2 in the old demo | Line-boundary cut of the next unit, statuses, tests at 500–4,000 tokens |
| Path headers were indexed | File names acted as query matches | BM25 indexes code lines only |
| License headers were not stripped | Boilerplate windows in the pool | Stripped before `package`, original line numbers kept |

## 6. What this demonstrates, and what it does not

**Demonstrated:**

- Real records can be joined to exact Git snapshots for both candidate datasets. For JIT-Defect4J this holds for all 27,319 commits (parent) and 99.98% (churn), once the input scope matches the benchmark's definition.
- Cross-file context can be built from the parent snapshot without checkouts, deterministically, in about a second per commit for Commons-size repositories; the corrected prototype meets the ±2% token match in both demo commits.
- Token sizes, pool sizes, and their shares under candidate caps are measured across all projects rather than assumed.
- BM25 behaves predictably but is not automatically "relevant", and line-based windows can be dominated by data-heavy code.
- At least one real label is a formatting-commit artefact.

**Not demonstrated:**

- Any LLM prediction. No model was called.
- The masked same-file C1 block and the final prompt builder (Gate 2), enclosing-method accuracy, retrieval relevance, scoring validity, and LLM behaviour ([06-milestone-and-decisions.md](06-milestone-and-decisions.md), Gates 2–3).

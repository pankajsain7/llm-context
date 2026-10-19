# Project instructions

**`AGENTS.md` (repository root) is the authoritative working agreement for every agent. Read and follow it.** This file adds only Copilot-specific setup. If the two ever conflict, `AGENTS.md` wins; report the conflict.

Essentials, in case `AGENTS.md` is not loaded:

- At the start of a session, read `AGENTS.md`, `docs/PROJECT_HISTORY.md` (current state and next step), and only the documents relevant to the task.
- No main implementation, LLM calls, test-split inference, or test-label use without explicit user approval. Labels and label-bearing files never reach prompts or retrieval.
- Never fabricate citations, data, or results. Mark what was observed, cited, inferred, or proposed, and say "not verified" when something was not verified.
- Proposals in the docs are not approved policy. Decisions become final only through `docs/06-milestone-and-decisions.md` and the supervisor.
- Data, clones, and the Python environment stay outside the repo in `C:\Users\psain\thesis-scratch`. Never commit them, labels, or `.env`.
- The repository already exists (`github.com/pankajsain7/llm-context`, `main`). Do not initialize another one.

# Git push instructions

The repo owner has authorized pushing to `origin` using the token in `.env` (`GITHUB_PAT`). Push only when the user asks; when asked, do it.

- Commits: always author as `pankajsain7 <techypankaj@gmail.com>`. Verify with `git -C <repo> config user.name` and `user.email` before committing.
- Never commit `.env`. It is listed in `.gitignore`; confirm `git status` does not show it before committing.
- Never write the token into the remote URL, git config, credential store, or any tracked file.
- Push with a one-off auth header read from `.env`:

```powershell
$repo = 'C:\Users\psain\OneDrive - mhp-group.com\Desktop\LLM-Context'
$t = ((Get-Content "$repo\.env" | Where-Object { $_ -like 'GITHUB_PAT=*' }) -replace '^GITHUB_PAT=', '').Trim()
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("x-access-token:$t"))
git -C $repo -c credential.helper= -c "http.extraheader=AUTHORIZATION: basic $b64" push -u origin main
Remove-Variable t, b64
```

- If the push returns 401/403, the token is expired or revoked; tell the user to update `GITHUB_PAT` in `.env`.

"""Prompt template (design §4). Draft; it may change only on validation data before the protocol freeze."""
import hashlib

PROMPT_VERSION = "draft-1"
SYSTEM = ("You are an experienced Java engineer reviewing a commit. Decide whether the code change "
          "introduces a defect, i.e. a bug that will later have to be fixed.")
USER = """### Additional code from the repository (read-only; version BEFORE the change; may be irrelevant)
{context}

### Code change (unified diff of .java files, parent -> commit)
{diff}

### Answer
Answer with exactly one word: YES if the change introduces a defect, otherwise NO."""


def build_prompt(context: str, diff: str) -> dict[str, str]:
    """Every condition uses this template; only `context` differs, and C0 renders it as "(none)"."""
    return {"system": SYSTEM, "user": USER.format(context=context or "(none)", diff=diff.rstrip("\n"))}


def prompt_text(prompt: dict[str, str]) -> str:
    """Canonical serialisation for token counting and hashing (chat-format overhead is not included)."""
    return prompt["system"] + "\n\n" + prompt["user"]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

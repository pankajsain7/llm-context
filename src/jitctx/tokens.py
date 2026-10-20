"""Reference tokenizer for every budget and match (design §5.1). Provider token counts are logged separately."""
from functools import lru_cache

import tiktoken

TOKENIZER = "o200k_base"
_enc = tiktoken.get_encoding(TOKENIZER)


def count_tokens(text: str) -> int:
    return len(_enc.encode(text, disallowed_special=()))


@lru_cache(maxsize=200_000)
def line_tokens(line: str) -> int:
    return count_tokens(line)

import re
import pandas as pd

def count_keywords(s: str, keywords: list):
    count = 0
    for kw in keywords:
        res = re.search(kw, s)
        if res is not None:
            count += 1
    return count

def count_newlines(s: str):
    s = re.sub(r"\n+", "\n", s)
    s = re.sub(r"(.?\n\s?)+", "\n", s).strip("\n")
    return len(re.findall("\n", s))

def get_k2_score(text: str, keywords: list) -> int:
    kw_count = count_keywords(text, keywords) # Количество ключевых слов
    nlines_count = count_newlines(text) # Количество абзацев (новых строк)
    
    if (nlines_count >= 6) and (nlines_count < 9) and (kw_count < 6):
        return 2
    if (nlines_count >= 9) and (kw_count <= 5):
        return 0
    else:
        return 1

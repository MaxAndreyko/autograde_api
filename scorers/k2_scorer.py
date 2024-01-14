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

def get_k2_score(df: pd.DataFrame, answer_col:str, keywords: list) -> int:
    s = str(df[answer_col])
    kw_count = count_keywords(s, keywords) # Количество ключевых слов
    nlines_count = count_newlines(s) # Количество абзацев (новых строк)
    
    if (nlines_count >= 6) and (nlines_count < 9) and (kw_count < 6):
        return str(2)
    if (nlines_count >= 9) and (kw_count <= 5):
        return str(0)
    else:
        return str(1)

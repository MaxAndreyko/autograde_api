import pandas as pd
from langdetect import detect

from autograde_api.scorers.k2_scorer import get_k2_score
from autograde_api.scorers.k3_scorer import (
    count_lexical_and_grammatical_errors,
    count_punctuation_errors,
    count_unique_spelling_errors,
    get_changed_sentences,
)
from autograde_api.data.analyse import count_words_in_paragraphs


# Функция для оценки текста
def evaluate_text(
    text: str,
    query: str,
    k1_model = None,
    k3_model = None,
    keywords = None,
    multi_scorer = None,
    generate_comments = False):
    comments = ""
    
    # Проверка объема текста
    num_words = count_words_in_paragraphs(text)
    if num_words < 90:
        return {
            "total": 0,
            "k1": 0,
            "k2": 0,
            "k3": 0,
            "comments": "Ответ не соответствует требуемому объёму",
        }
    elif num_words > 154:
        words = words[:140]
        text = " ".join(words)

    # Проверка языка текста
    if detect(text) != "en":
        return {
            "total": 0,
            "k1": 0,
            "k2": 0,
            "k3": 0,
            "comments": "Текст не соответствует условиям задания",
        }

    if k1_model is not None:
        # Оценка k1
        k1 = k1_model.predict(pd.DataFrame(text))

    if keywords is not None:
        # Оценка k2
        k2 = get_k2_score(text, keywords)

    if k3_model is not None:
        # Оценка k3 и формирование комментариев
        text = text.replace("\\r\\n", " ").replace("\\r", " ").replace("\n", " ")
        corrected_text = k3_model(text)[0]["generated_text"]
        punctuation_errors = count_punctuation_errors(text, corrected_text)
        spelling_errors, unique_spelling_mistakes = count_unique_spelling_errors(text)
        mistakes_spell_punct = punctuation_errors + spelling_errors
        lexical_and_grammatical_errors = (
            count_lexical_and_grammatical_errors(text, corrected_text)
            - mistakes_spell_punct
        )

        if lexical_and_grammatical_errors <= 2 or mistakes_spell_punct <= 2:
            k3 = 2
        elif lexical_and_grammatical_errors <= 4 or mistakes_spell_punct <= 4:
            k3 = 1
        else:
            k3 = 0
    
        if generate_comments:
            changed_sentences = get_changed_sentences(text, corrected_text)
            changed_sentences_str = "\n".join(changed_sentences)
            comments = f"Количество орфографических ошибок: {spelling_errors}. Вот они: {list(unique_spelling_mistakes)}.\nКоличество пунктуационных ошибок: {punctuation_errors}.\nКоличество лексических и грамматических ошибок: {lexical_and_grammatical_errors}.\nЧтобы избежать ошибок и сделать текст более естественным, вы можете исправить следующие предложения:\n{changed_sentences_str}"
    
    if multi_scorer is not None:
        k1, k2, k3 = multi_scorer(query, text)
    
    if k1 == 0:
        k2 = 0
        k3 = 0
        comments = 'По критерию "Решение коммуникативной задачи" выставлено 0 баллов, ответ на задание оценивается в 0 баллов по всем критериям'
        
    total = k1 + k2 + k3
    return {"total": total, "k1": k1, "k2": k2, "k3": k3, "comments": comments}

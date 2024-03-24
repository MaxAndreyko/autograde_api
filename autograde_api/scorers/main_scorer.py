from langdetect import detect

from autograde_api.scorers.k2_scorer import get_k2_score
from autograde_api.scorers.k3_scorer import (
    count_lexical_and_grammatical_errors,
    count_punctuation_errors,
    count_unique_spelling_errors,
    get_changed_sentences,
)


# Функция для оценки текста
def evaluate_text(df, answer_col, k1_model, k3_model, keywords):
    text = str(df.loc[0, answer_col])
    # Проверка объема текста
    words = text.split()
    if len(words) < 90:
        return {
            "total": 0,
            "k1": 0,
            "k2": 0,
            "k3": 0,
            "comments": "Ответ не соответствует требуемому объёму",
        }
    elif len(words) > 154:
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

    # Оценка k1
    k1 = k1_model.predict(df)

    # Оценка k2
    k2 = get_k2_score(text, keywords)

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

    changed_sentences = get_changed_sentences(text, corrected_text)
    changed_sentences_str = "\n".join(changed_sentences)
    comments = f"Количество орфографических ошибок: {spelling_errors}. Вот они: {list(unique_spelling_mistakes)}.\nКоличество пунктуационных ошибок: {punctuation_errors}.\nКоличество лексических и грамматических ошибок: {lexical_and_grammatical_errors}.\nЧтобы избежать ошибок и сделать текст более естественным, вы можете исправить следующие предложения:\n{changed_sentences_str}"
    total = k1 + k2 + k3
    return {"total": total, "k1": k1, "k2": k2, "k3": k3, "comments": comments}

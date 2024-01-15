import language_tool_python
import difflib
from nltk.tokenize import sent_tokenize

# Функция для подсчета пунктуационных ошибок
def count_punctuation_errors(original_text: str, corrected_text: str) -> int:
    original_punctuation_count = original_text.count(',')
    corrected_punctuation_count = corrected_text.count(',')
    return abs(original_punctuation_count - corrected_punctuation_count)

# Функция для подсчета орфографических ошибок
def count_unique_spelling_errors(text):
    # убираем имя, потому что обычно оно воспринимается как ошибка
    text_without_name = " ".join(text.split()[:-1])
    # global unique_spelling_mistakes
    tool = language_tool_python.LanguageTool('en-GB', config={'cacheSize': 1000, 'pipelineCaching': True})
    mistakes = tool.check(text_without_name)
    # выбираем только уникальные ошибки
    unique_spelling_mistakes = set(tuple(mistake.replacements) for mistake in mistakes if mistake.ruleIssueType == 'misspelling')
    tool.close()
    return len(unique_spelling_mistakes), unique_spelling_mistakes

# Функция для подсчета лексических и грамматических ошибок
def count_lexical_and_grammatical_errors(original_text, corrected_text):
    original_sentences = sent_tokenize(original_text)
    corrected_sentences = sent_tokenize(corrected_text)
    errors = sum(1 for original, corrected in zip(original_sentences, corrected_sentences) if original != corrected)
    return errors

# Определяем изменившиеся предложения, чтобы потом отправить их в комментарии
def get_changed_sentences(original, corrected):
    original_sents = sent_tokenize(original)
    corrected_sents = sent_tokenize(corrected)
    matcher = difflib.SequenceMatcher(None, original_sents, corrected_sents)
    changed_sentences = [corrected_sents[i] for i, op in enumerate(matcher.get_opcodes()) if op[0] != 'equal']
    return changed_sentences  


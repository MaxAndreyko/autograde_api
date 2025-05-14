def count_words_in_paragraphs(text: str):
    paragraphs = text.split("\n")
    all_words = []
    for para in paragraphs:
        words = para.split()
        all_words.extend(words)
    return len(all_words)
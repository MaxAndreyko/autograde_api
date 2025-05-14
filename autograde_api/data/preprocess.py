def truncate_words(text, num_words=10):
    paragraphs = text.split("\n")
    all_words = []
    para_indices = []
    for para in paragraphs:
        words = para.split()
        all_words.extend(words)
        para_indices.append(len(all_words))  # Track cumulative word count per paragraph

    truncated_words = all_words[:num_words]
    result = []
    current_para_start = 0

    for _, para_end in enumerate(para_indices):
        para_words = truncated_words[current_para_start:para_end]
        if para_words:
            result.append(" ".join(para_words))
        current_para_start = para_end
        if current_para_start >= len(truncated_words):
            break
    return "\n".join(result)
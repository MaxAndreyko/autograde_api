import re
import pandas as pd
import matplotlib.pyplot as plt

with open('k2_words_unique.txt', 'r') as file:
    text = file.read().lower()
    keywords = text.split(',')


dataset = pd.read_excel("dataset.xlsx")
dataset["tokenized"] = dataset["Text"].apply(lambda x: re.findall(r'\b\w+\b', x.lower()))
dataset["words_count"] = dataset["tokenized"].apply(lambda x: len(set(x) & set(keywords)))

plt.plot(dataset["words_count"], dataset["Text structure"])
plt.xlabel("Words count")
plt.ylabel("K2-score")
plt.show()
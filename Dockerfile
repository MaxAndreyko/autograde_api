FROM python:3.9-slim-bullseye

WORKDIR /app
COPY . .

RUN mkdir -p /usr/share/nltk_data/tokenizers/
RUN mv /app/punkt /usr/share/nltk_data/tokenizers/

# Install OpenJDK-11
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless && \
    apt-get clean;

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD [ "python", "main.py" ]
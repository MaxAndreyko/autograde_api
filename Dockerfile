FROM python:3.9-slim-bullseye

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD [ "python", "main.py" ]
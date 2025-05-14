FROM python:3.10-slim-bullseye
COPY /src .
WORKDIR /autograde_api
COPY . .

# Install OpenJDK-11
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless && \
    apt-get clean;

RUN pip install --no-cache-dir --upgrade -r /autograde_api/requirements.txt

CMD [ "python", "main.py" ]

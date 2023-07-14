FROM python:3.9-slim

RUN apt-get update && apt-get install build-essential -y

WORKDIR /app

COPY . .
COPY credentials.json credentials.json

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=api/index.py

CMD ["flask", "run", "--host=0.0.0.0"]

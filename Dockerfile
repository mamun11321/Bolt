FROM python:3.11-alpine

RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    wget \
    curl

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir selenium python-telegram-bot

COPY bolt.py .

CMD ["python", "bolt.py"]
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# bolt.py কপি করুন
COPY bolt.py .

# প্যাকেজ ইনস্টল করুন
RUN pip install selenium python-telegram-bot webdriver-manager

CMD ["python", "bolt.py"]
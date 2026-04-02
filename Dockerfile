FROM python:3.11-slim

# Chrome এবং ChromeDriver ইনস্টল করুন
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver ইনস্টল করুন
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f1) && \
    wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/$(google-chrome --version | awk '{print $3}')/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bolt.py .

CMD ["python3", "bolt.py"]
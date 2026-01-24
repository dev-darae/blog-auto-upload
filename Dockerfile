
# Use an official Python runtime with Chrome support
# Since Selenium needs Chrome, we can use a base image or install it manually.
# 'python:3.9-slim' is lightweight, but we need to add Chrome.

FROM python:3.9-slim

# Install system dependencies (Chrome, fonts, etc.)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    --no-install-recommends

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install Korean Fonts (Nanum) to prevent broken text in screenshots/rendering
RUN apt-get install -y fonts-nanum

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Environment Variables (Defaults, override in Render Dashboard)
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99 

# Run the application
CMD ["python", "main.py"]

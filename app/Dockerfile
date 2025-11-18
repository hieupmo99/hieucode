FROM python:3.9-slim

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome/Chromium and ChromeDriver (works for both amd64 and arm64)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg && \
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
        apt-get update && \
        apt-get install -y google-chrome-stable && \
        CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) && \
        CHROMEDRIVER_VERSION=$(curl -sS "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}" 2>/dev/null || echo "latest") && \
        wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
        unzip -q /tmp/chromedriver.zip -d /tmp/ && \
        mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
        chmod +x /usr/local/bin/chromedriver && \
        rm -rf /tmp/chromedriver*; \
    elif [ "$ARCH" = "arm64" ]; then \
        apt-get update && \
        apt-get install -y chromium chromium-driver && \
        ln -sf /usr/bin/chromium /usr/bin/google-chrome-stable && \
        ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver; \
    fi && \
    rm -rf /var/lib/apt/lists/*

# Create symlink for ChromeDriver at expected path (/opt/homebrew/bin/chromedriver)
# This allows the code to find ChromeDriver at the hardcoded path
RUN mkdir -p /opt/homebrew/bin && \
    (ln -sf /usr/bin/chromedriver /opt/homebrew/bin/chromedriver 2>/dev/null || \
     ln -sf /usr/local/bin/chromedriver /opt/homebrew/bin/chromedriver 2>/dev/null || \
     true) && \
    chmod +x /opt/homebrew/bin/chromedriver 2>/dev/null || true && \
    ls -la /opt/homebrew/bin/chromedriver || echo "Symlink creation check"

WORKDIR /opt/app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (includes entrypoint.sh)
COPY . .

# Move entrypoint script to a location that won't be overwritten by volume mount
RUN mv /opt/app/entrypoint.sh /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint.sh && \
    ls -la /usr/local/bin/entrypoint.sh

# Set Chrome options for headless mode in Docker
ENV CHROME_BIN=/usr/bin/google-chrome-stable
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Use entrypoint to setup ChromeDriver before Python runs
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["mass_crawling.py"]

FROM python:3.11-slim-bullseye

# Install Java 17 (required for Spark)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk-headless curl ca-certificates build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Make src/ available for imports
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Set working directory
WORKDIR /app

# Copy and install runtime Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ETL code and data
COPY src/ ./src/
COPY data/ ./data/

CMD ["python", "src/zephyr/main.py"]

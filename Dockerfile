FROM python:3.11-slim

WORKDIR /app

# sounddevice needs PortAudio's system library, not just the Python package.
RUN apt-get update && apt-get install -y --no-install-recommends libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY evals/ evals/

CMD ["python", "-m", "src.cli"]

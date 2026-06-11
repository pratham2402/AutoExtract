FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    unrar \
    p7zip-full \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir -e .

RUN mkdir -p /watch /output

VOLUME ["/watch", "/output", "/etc/autoextract"]

ENTRYPOINT ["python", "-m", "autoextract"]

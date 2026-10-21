FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates iverilog verilator \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest pandas duckdb
RUN useradd -m -u 1000 -s /bin/bash student
WORKDIR /work
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh
USER student
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

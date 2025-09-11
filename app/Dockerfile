FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*
# install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# copy application code
COPY app/ ./app/

# ensure script is executable and strip CRLF if present
RUN chmod +x app/start.sh && sed -i 's/\r$//' app/start.sh

EXPOSE 8000
CMD ["/bin/bash","-lc","/app/app/start.sh"]


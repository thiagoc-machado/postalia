FROM python:3.13-slim

WORKDIR /app

ENV HF_HOME=/data/.hf
ENV TRANSFORMERS_CACHE=/data/.hf
ENV DIFFUSERS_CACHE=/data/.hf

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY deploy/requirements-api.txt /app/requirements-api.txt
RUN pip install --no-cache-dir -r requirements-api.txt && useradd --uid 10001 --create-home stats && mkdir /data && chown stats:stats /data
COPY public_server.py ui_server.py demo.py /app/
COPY stat_assistant /app/stat_assistant
COPY ui /app/ui
USER 10001:10001
EXPOSE 8082
CMD ["python", "public_server.py"]

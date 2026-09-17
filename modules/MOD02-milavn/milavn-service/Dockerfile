# syntax=docker/dockerfile:1.7
# Milavn service — production image (linux/amd64, linux/arm64).
# Build context: this folder. Deployment kit: deploy/README.md (repo root).
# The service lives at /srv/milavn/milavn-service so settings.py's relative
# paths (../07a-db-implementation/.env, ./.local-media) resolve as in the repo;
# in a container every value comes from environment variables instead.
#
# Run exactly ONE process per deployment: chat fan-out (WebSocket hub) and the
# reminder / circle-suggestion jobs live in process memory.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8001

WORKDIR /srv/milavn/milavn-service

COPY pyproject.toml ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > /tmp/requirements.txt \
 && pip install -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app \
 && mkdir -p .local-media && chown app:app .local-media

COPY app ./app

USER app
EXPOSE 8001
# Uploaded covers, chat photos, moments and profile photos. Mount a persistent volume here.
VOLUME ["/srv/milavn/milavn-service/.local-media"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request as u; u.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8001'), timeout=4)" || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"$PORT\" --workers 1 --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-127.0.0.1}\" --root-path \"${ROOT_PATH:-}\" --no-server-header"]

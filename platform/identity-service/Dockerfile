# syntax=docker/dockerfile:1.7
# ForKhatri Identity & Trust Service — production image (linux/amd64, linux/arm64).
# Build context: this folder. Deployment kit: deploy/README.md.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8100

WORKDIR /srv/platform/identity-service

# Runtime dependencies only, straight from pyproject.toml (one pinned baseline).
COPY pyproject.toml ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > /tmp/requirements.txt \
 && pip install -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app

COPY app ./app
COPY db ./db
COPY scripts ./scripts

USER app
EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request as u; u.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8100'), timeout=4)" || exit 1

# ROOT_PATH is the public prefix the edge strips (/api/identity), so generated
# URLs and redirects stay correct. FORWARDED_ALLOW_IPS trusts X-Forwarded-For
# only from the private network the edge proxy lives on.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"$PORT\" --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-127.0.0.1}\" --root-path \"${ROOT_PATH:-}\" --no-server-header"]

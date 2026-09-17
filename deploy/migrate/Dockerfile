# syntax=docker/dockerfile:1.7
# ForKhatri migration job (deploy/migrate/migrate.py). One-shot; exits when done.
# Build context: the repository root. Deploy/migrate/Dockerfile.dockerignore
# admits only the migration files, dev seeds and this runner.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FORKHATRI_REPO_ROOT=/opt/forkhatri

# asyncpg for migrations; argon2-cffi for the explicit development seed only.
RUN pip install asyncpg==0.31.0 argon2-cffi==25.1.0 \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app

WORKDIR /opt/forkhatri
COPY platform/identity-service/db/migrations platform/identity-service/db/migrations
COPY platform/identity-service/scripts/import_module_identities.py platform/identity-service/scripts/seed_dev_members.py platform/identity-service/scripts/
COPY modules/MOD03-mangaly/07a-db-implementation/migrations modules/MOD03-mangaly/07a-db-implementation/migrations
COPY modules/MOD02-milavn/07a-db-implementation/migrations modules/MOD02-milavn/07a-db-implementation/migrations
COPY modules/MOD02-milavn/07a-db-implementation/seeds.sql modules/MOD02-milavn/07a-db-implementation/seeds-dev.sql modules/MOD02-milavn/07a-db-implementation/
COPY modules/MOD02-milavn/milavn-service/app/config/dev_identities.json modules/MOD02-milavn/milavn-service/app/config/
COPY deploy/migrate deploy/migrate

USER app
ENTRYPOINT ["python", "/opt/forkhatri/deploy/migrate/migrate.py"]

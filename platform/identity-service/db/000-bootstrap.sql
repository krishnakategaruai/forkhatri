-- =============================================================================
-- ForKhatri Identity & Trust Service — cluster bootstrap (run once as a superuser)
--
-- Creates the two roles and the isolated database this service owns
-- (ARCHITECTURE.md ADR-002/ADR-004). The runtime role never owns a table
-- (MODULE-ARCHITECTURE-STANDARD §4). Passwords below are development
-- placeholders; every deployed environment sets its own.
--
--   psql -h localhost -p 5433 -U postgres -f db/000-bootstrap.sql
-- =============================================================================

SELECT 'CREATE ROLE identity_owner LOGIN PASSWORD ''identity_owner_dev_password'''
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'identity_owner') \gexec

SELECT 'CREATE ROLE identity_app LOGIN PASSWORD ''identity_app_dev_password'''
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'identity_app') \gexec

SELECT 'CREATE DATABASE forkhatri_identity OWNER identity_owner'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'forkhatri_identity') \gexec

REVOKE ALL ON DATABASE forkhatri_identity FROM PUBLIC;
GRANT CONNECT ON DATABASE forkhatri_identity TO identity_owner, identity_app;

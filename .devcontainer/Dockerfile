# The Codespace image for Scio: everything scripts/dev-up.sh expects to find.
#
# Node and Python come from devcontainer features (see devcontainer.json).
# PostgreSQL does not: dev-up.sh runs a real PostgreSQL 16 *process* — initdb,
# pg_ctl, its own PGDATA — rather than a container, so the binaries have to be
# in this image.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# pgvector is not optional: the api's first migration begins
# CREATE EXTENSION "vector", so without it 0001_init fails on its second line.
RUN install -d /usr/share/postgresql-common/pgdg \
 && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
      -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
 && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(. /etc/os-release && echo "$VERSION_CODENAME")-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      postgresql-16 postgresql-16-pgvector postgresql-client-16 \
 && rm -rf /var/lib/apt/lists/*

# PGDATA lives outside the repo on purpose (Postgres refuses to run as root and
# the directory must belong to the postgres user), which also means a database
# can never end up in a commit.
RUN install -d -o postgres -g postgres -m 700 /var/lib/postgresql/scio-dev

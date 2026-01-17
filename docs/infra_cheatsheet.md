# GC‑Game Infrastructure Cheat Sheet

This document is a **practical reference** for common tasks involving **Docker, Alembic, and Postgres** in the Galactic Conquest project.

It is written for day‑to‑day use. No theory, no fluff.

---

## Assumptions (Your Actual Setup)

- Repo root: `~/dev/gc-game`
- Compose files: `~/dev/gc-game/infra/docker-compose.yml`
- Backend service name: `backend`
- Backend container name: `gc_backend`
- Backend working directory (inside container): `/app`
- Postgres service name: `postgres`
- Postgres container name: `gc_postgres`
- Postgres user: `gc_user`
- Database name: `galactic_conquest`
- Alembic config: `/app/alembic.ini`

---

# 1. Docker & Docker Compose

## Show running services

```bash
docker compose -f infra/docker-compose.yml ps
```

## List service names (important for `exec`)

```bash
docker compose -f infra/docker-compose.yml config --services
```

## Exec into the backend container (recommended)

```bash
docker compose -f infra/docker-compose.yml exec backend sh
```

## Exec into Postgres

```bash
docker compose -f infra/docker-compose.yml exec postgres sh
```

## Bypass Compose (use container names directly)

Backend:
```bash
docker exec -it gc_backend sh
```

Postgres:
```bash
docker exec -it gc_postgres sh
```

---

# 2. Alembic – Everyday Commands

All Alembic commands are run **inside the backend container**.

## Verify Alembic files exist

```bash
docker compose -f infra/docker-compose.yml exec backend \
  sh -lc 'pwd; ls alembic.ini alembic/ alembic/versions'
```

Expected:
- `/app/alembic.ini`
- `/app/alembic/env.py`
- `/app/alembic/versions/*.py`

---

## Check current DB revision

```bash
docker compose -f infra/docker-compose.yml exec backend alembic current
```

## Show latest revision(s)

```bash
docker compose -f infra/docker-compose.yml exec backend alembic heads
```

## Show full migration history

```bash
docker compose -f infra/docker-compose.yml exec backend alembic history --verbose
```

---

## Apply migrations

### Normal case (single head)

```bash
docker compose -f infra/docker-compose.yml exec backend alembic upgrade head
```

### Apply all heads (only if intentional)

```bash
docker compose -f infra/docker-compose.yml exec backend alembic upgrade heads
```

---

## Create a new migration

```bash
docker compose -f infra/docker-compose.yml exec backend \
  alembic revision -m "<message>"
```

After creation, **always verify** in the new file:

```python
revision = "<new_id>"
down_revision = "<previous_id>"  # MUST be quoted
```

If `down_revision` is `None` by mistake, you will create a second head.

---

## Fix: multiple Alembic heads (common)

### See heads

```bash
docker compose -f infra/docker-compose.yml exec backend alembic heads
```

### If accidental (most cases)
- Edit the newest migration
- Set `down_revision` to the latest real revision ID
- IDs **must be strings**

```python
down_revision = "091a15f1f5a0"
```

### If branches are real and must be unified

```bash
docker compose -f infra/docker-compose.yml exec backend \
  alembic merge -m "Merge heads" <HEAD1> <HEAD2>
```

---

# 3. Postgres – Verifying the Database

## List tables

```bash
docker exec -it gc_postgres \
  psql -U gc_user -d galactic_conquest -c "\\dt"
```

## Inspect a table

```bash
docker exec -it gc_postgres \
  psql -U gc_user -d galactic_conquest -c "\\d systems"
```

## Verify Alembic version table

```bash
docker exec -it gc_postgres \
  psql -U gc_user -d galactic_conquest \
  -c "select * from alembic_version;"
```

Expected:
- One row
- `version_num` = latest revision (e.g. `gc_mvp_001`)

---

## Interactive psql session

```bash
docker exec -it gc_postgres psql -U gc_user
```

Inside `psql`:
```sql
\l            -- list databases
\c <db>       -- connect to db
\dt           -- list tables
\q            -- quit
```

---

# 4. Git – Infra & Migration Safety Checks

## See unstaged changes

```bash
git diff infra/docker-compose.yml
```

## See commit history for a file

```bash
git log --oneline -- infra/docker-compose.yml
```

## Commit an intentional infra change

```bash
git add infra/docker-compose.yml
git commit -m "Update docker-compose configuration"
```

---

# 5. Known-Good Verification Sequence

When something feels off, run these **in order**:

```bash
docker compose -f infra/docker-compose.yml exec backend alembic heads
docker compose -f infra/docker-compose.yml exec backend alembic current

docker exec -it gc_postgres \
  psql -U gc_user -d galactic_conquest -c "select * from alembic_version;"
```

If these three agree, your schema and migration state are correct.

---

**This file is meant to be copied, not memorized.**


Below is the **final, corrected Markdown file** you can copy directly into your repo as:

```
docs/hex_utils_gc_mvp_004_impl.md
```

It is written to **match your existing architecture**, uses **only Python + Docker**, and **does not assume pytest exists**.

---

````md
# Hex Utilities – Implementation & Verification (gc_mvp_004)

## Overview

This document describes the implementation, verification, and testing process for **Step 4: Hex Utilities** in Milestone A1.

This project’s backend container (`gc_backend`) does **not** include external test frameworks such as `pytest`.  
All verification in this step is therefore performed using **plain Python scripts executed inside the existing container**.

No schema, models, or migrations are modified in this step.

---

## Files Added

| Path | Description |
|-----|-------------|
| `backend/app/hex_utils.py` | Core hex utility functions and data structures |
| `backend/tests/smoke_hex_utils_gc_mvp_004.py` | Primary smoke test (plain Python) |
| `backend/tests/test_hex_utils_gc_mvp_004.py` | Unit-style tests (plain Python, no pytest) |
| `docs/hex_utils_gc_mvp_004.md` | Design and reference documentation |
| `docs/hex_utils_gc_mvp_004_impl.md` | This implementation and verification guide |

---

## Preconditions

Ensure the backend container is running:

```bash
docker compose ps
````

If not running:

```bash
docker compose up -d --build
```

---

## Basic Import Verification

Confirm the module imports correctly inside the container:

```bash
docker exec -it gc_backend python -c "from app.hex_utils import Hex, MapBounds; print(Hex(0, 0))"
```

**Expected output:**

```
Hex(q=0, r=0)
```

---

## Smoke Test (PRIMARY VERIFICATION)

The smoke test is the **authoritative verification method** for this step.

Run:

```bash
docker exec -i gc_backend python - < backend/tests/smoke_hex_utils_gc_mvp_004.py
```

**Expected behavior:**

* Script completes with exit code `0`
* Final output includes `SMOKE OK`

If this passes, Step 4 is considered functionally correct.

---

## Unit-Style Tests (Plain Python)

A more detailed test script is provided but **does not use pytest**.

Run:

```bash
docker exec -i gc_backend python - < backend/tests/test_hex_utils_gc_mvp_004.py
```

**Expected behavior:**

* Script completes with exit code `0`
* Final output includes `TESTS OK`

> Note: These tests use standard `assert` statements and explicit exceptions.
> No test runner or external framework is required.

---

## Syntax Verification

Optional but recommended:

```bash
docker exec -it gc_backend python -m py_compile backend/app/hex_utils.py
```

**Expected:** no output, exit code `0`

---

## What Is NOT Required in This Step

* ❌ `pytest`
* ❌ Alembic migrations
* ❌ `alembic check`
* ❌ Database access
* ❌ API endpoints

This step is **pure utility code**.

---

## Common Errors and Fixes

### `pytest: executable file not found in $PATH`

This is expected.

Do **not** run:

```bash
docker exec -it gc_backend pytest ...
```

Instead, always use:

```bash
docker exec -i gc_backend python - < backend/tests/smoke_hex_utils_gc_mvp_004.py
```

or

```bash
docker exec -i gc_backend python - < backend/tests/test_hex_utils_gc_mvp_004.py
```

---

### `ModuleNotFoundError: No module named 'app'`

You are likely running Python outside the container.

Ensure all tests are executed via `docker exec` as shown above.

---

## Git Commands

### Check status

```bash
git status
```

### Stage files

```bash
git add backend/app/hex_utils.py
git add backend/tests/smoke_hex_utils_gc_mvp_004.py
git add backend/tests/test_hex_utils_gc_mvp_004.py
git add docs/hex_utils_gc_mvp_004.md
git add docs/hex_utils_gc_mvp_004_impl.md
```

### Commit

```bash
git commit -m "A1 Step 4: Add hex utilities with smoke-based verification

- Implement global axial hex utilities
- Add bounds-aware neighbors and rings
- Add sextant coordinate helpers
- Add plain-Python smoke and unit-style tests
- Document design and verification workflow"
```

### Push

```bash
git push origin main
```

---

## Completion Criteria

Step 4 is complete when:

* [ ] `hex_utils.py` imports without error
* [ ] Smoke test prints `SMOKE OK`
* [ ] Unit-style test script completes successfully
* [ ] No new dependencies were introduced
* [ ] Changes are committed to git

---

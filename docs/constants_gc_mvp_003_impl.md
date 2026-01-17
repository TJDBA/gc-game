# Constants Module Implementation: gc_mvp_003

## Overview

This document provides implementation details, verification steps, and testing instructions for the constants module created in Step 3 of Milestone A1.

---

## Files Created/Modified

### New Files

| Path | Purpose |
|------|---------|
| `backend/app/constants.py` | Game constants module |
| `backend/tests/smoke_constants_gc_mvp_003.py` | Smoke test for constants |
| `docs/constants_gc_mvp_003.md` | Design/reference documentation |
| `docs/constants_gc_mvp_003_impl.md` | This file (implementation/testing) |

### Files NOT Modified

- `backend/app/models.py` — No changes (enums remain in models)
- `backend/app/main.py` — No changes (constants not wired to endpoints yet)
- Migrations — No schema changes in this step

---

## Docker-Based Run Instructions

### Prerequisites

Ensure containers are running:

```bash
docker compose -f infra/docker-compose.dev.yml ps
```

If not running:

```bash
docker compose -f infra/docker-compose.dev.yml up -d --build
```

### Verify Module Loads

Test that the constants module imports without errors:

```bash
docker exec -it gc_backend python -c "from app.constants import SEXTANT_SIZE; print(f'SEXTANT_SIZE = {SEXTANT_SIZE}')"
```

**Expected output:**
```
SEXTANT_SIZE = 20
```

---

## Smoke Test Execution

### Run the Smoke Test

The smoke test is a file in the repo (not pasted code). Run it with:

```bash
docker exec -i gc_backend python - < backend/tests/smoke_constants_gc_mvp_003.py
```

**⚠️ Mac Terminal Note:** If you experience issues with the `<` redirect, you can also run:

```bash
docker exec -it gc_backend python /app/tests/smoke_constants_gc_mvp_003.py
```

Or copy the file into the container first:

```bash
docker cp backend/tests/smoke_constants_gc_mvp_003.py gc_backend:/app/tests/
docker exec -it gc_backend python /app/tests/smoke_constants_gc_mvp_003.py
```

### Expected Output

```
==================================================
SMOKE TEST: constants_gc_mvp_003
==================================================
Testing scan math...
  Scan math OK
Testing faction colors...
  Faction colors OK
Testing key constants...
  Key constants OK
Testing ship stats...
  Ship stats OK
Testing system RP ranges...
  System RP ranges OK
Testing tech costs...
  Tech costs OK
==================================================
SMOKE OK - All constants validated
==================================================
```

Exit code should be `0` (success).

---

## Additional Verification Steps

### 1. Python Syntax Check

Verify the constants file has valid Python syntax:

```bash
docker exec -it gc_backend python -m py_compile /app/app/constants.py
echo "py_compile exit code: $?"
```

**Expected:** Exit code 0, no output (silence = success).

### 2. Import All Constants

Test importing all public constants:

```bash
docker exec -it gc_backend python -c "
from app.constants import (
    MIN_PLAYERS, MAX_PLAYERS, JOIN_CODE_LENGTH,
    TURN_NUMBER_START, CURRENT_TURN_START, DEFAULT_TURN_TIMEOUT_SECONDS,
    STARTING_RP, STARTING_POP_TENTHS, POP_TENTHS_PER_POP, MIN_RP,
    MIN_TECH_LEVEL, MAX_TECH_LEVEL, STARTING_TECH_LEVEL, TECH_COSTS,
    SCAN_BAND_PRIORITY, calc_scan_base, calc_long_range, calc_medium_range, calc_short_range,
    SHIP_STATS, STARTING_SHIPS,
    SYSTEM_RP_RANGES, SEXTANT_SYSTEM_COUNTS,
    CONTROL_MIN_POP_TENTHS, CONTROL_RATIO,
    SEXTANT_SIZE, MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS, AXIAL_DIRECTIONS,
    TAX_TURN_INTERVAL, TAX_COST_PER_POP_TENTH,
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE,
    FACTION_COLORS, FACTION_COLOR_HEX_CODES, FACTION_COLOR_NAMES,
    get_faction_color, get_faction_color_name,
)
print('All imports successful')
"
```

**Expected output:**
```
All imports successful
```

### 3. Scan Math Verification

Verify scan formulas at key tech levels:

```bash
docker exec -it gc_backend python -c "
from app.constants import calc_short_range, calc_medium_range, calc_long_range

print('Tech 0: SHORT={}, MEDIUM={}, LONG={}'.format(
    calc_short_range(0), calc_medium_range(0), calc_long_range(0)))
print('Tech 1: SHORT={}, MEDIUM={}, LONG={}'.format(
    calc_short_range(1), calc_medium_range(1), calc_long_range(1)))
print('Tech 5: SHORT={}, MEDIUM={}, LONG={}'.format(
    calc_short_range(5), calc_medium_range(5), calc_long_range(5)))
"
```

**Expected output:**
```
Tech 0: SHORT=0, MEDIUM=0, LONG=0
Tech 1: SHORT=0, MEDIUM=1, LONG=2
Tech 5: SHORT=2, MEDIUM=5, LONG=10
```

### 4. Faction Color Count

```bash
docker exec -it gc_backend python -c "
from app.constants import FACTION_COLORS, MAX_PLAYERS
assert len(FACTION_COLORS) == MAX_PLAYERS == 24
print(f'Faction colors: {len(FACTION_COLORS)} (matches MAX_PLAYERS={MAX_PLAYERS})')
"
```

**Expected output:**
```
Faction colors: 24 (matches MAX_PLAYERS=24)
```

---

## Health Check

After implementation, verify the backend still works:

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"ok":true}
```

---

## Git Commands

### Check Status

```bash
git status
```

**Expected new files:**
```
Untracked files:
  backend/app/constants.py
  backend/tests/smoke_constants_gc_mvp_003.py
  docs/constants_gc_mvp_003.md
  docs/constants_gc_mvp_003_impl.md
```

### Stage Files

```bash
git add backend/app/constants.py
git add backend/tests/smoke_constants_gc_mvp_003.py
git add docs/constants_gc_mvp_003.md
git add docs/constants_gc_mvp_003_impl.md
```

### Commit

```bash
git commit -m "A1 Step 3: Add game constants module

- Create backend/app/constants.py with all gameplay constants
- Scan math uses no +1: LONG=tech*2, MEDIUM=tech, SHORT=tech//2
- 24 faction colors to support MAX_PLAYERS
- Starting tech level set to 1
- Add smoke test for validation
- Add documentation (design + implementation)"
```

### Push

```bash
git push origin main
```

---

## Troubleshooting

### Import Error: `ModuleNotFoundError: No module named 'app'`

The smoke test adds `/app` to `sys.path`. If running outside Docker, ensure you're in the correct directory or adjust the path.

### Smoke Test Fails on Assertion

Check the specific assertion message. Common issues:
- Scan math formulas changed (should use no +1)
- Faction color count ≠ 24
- Missing or misnamed constants

### Permission Denied on File Operations

If Docker file operations fail, check volume mounts in `docker-compose.dev.yml`.

---

## Next Steps

After completing Step 3, proceed to:

**Step 4: Hex Utilities** (`backend/app/hex.py`)
- Will import: `SEXTANT_SIZE`, `AXIAL_DIRECTIONS`
- Creates: `Hex` class, distance calculations, ring generation, sextant conversion

---

## Reminder

**Mac Terminal Paste Limits:** The smoke test is intentionally a file in the repository, not code to paste. This avoids Terminal buffer issues with large code blocks.

**Replace Placeholders:** When running commands that reference `GAME_ID` or similar, use actual UUIDs from your database.

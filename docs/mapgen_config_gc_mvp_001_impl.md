# Map Config Implementation: gc_mvp_001_impl

## Overview

This document provides implementation details, verification steps, and testing instructions for the map config contract created in Task T1 of Milestone A1b.

---

## Files Created

| Path | Purpose |
|------|---------|
| `backend/app/mapgen.py` | Map config validation + geometry derivation |
| `backend/tests/smoke_mapgen_config_gc_mvp_001.py` | Standalone smoke test |
| `docs/mapgen_config_gc_mvp_001.md` | Design/reference documentation |
| `docs/mapgen_config_gc_mvp_001_impl.md` | This implementation guide |

---

## Files NOT Modified

- `backend/app/models.py` — No changes (no new models needed)
- `backend/app/main.py` — No changes (not wired to endpoints yet)
- `backend/app/constants.py` — No changes (uses existing constants)
- Migrations — No schema changes

---

## Prerequisites

Ensure containers are running:

```bash
docker compose -f infra/docker-compose.dev.yml ps
```

If not running:

```bash
docker compose -f infra/docker-compose.dev.yml up -d --build
```

---

## Verification Steps

### 1. Syntax Check

Verify the mapgen module has valid Python syntax:

```bash
docker exec -it gc_backend python -m py_compile /app/app/mapgen.py
echo "Exit code: $?"
```

**Expected:** Exit code 0, no output.

### 2. Import Check

Verify the module imports correctly:

```bash
docker exec -it gc_backend python -c "
from app.mapgen import validate_map_config, derive_map_geometry
print('Imports OK')
"
```

**Expected output:**
```
Imports OK
```

### 3. Quick Validation Test

Test validation with a simple config:

```bash
docker exec -it gc_backend python -c "
from app.mapgen import validate_map_config, derive_map_geometry

config = {'map_sextants_w': 3, 'map_sextants_h': 4}
validated = validate_map_config(config)
print(f'Validated: {validated}')

geometry = derive_map_geometry(validated)
print(f'Geometry: {geometry}')
"
```

**Expected output:**
```
Validated: {'map_sextants_w': 3, 'map_sextants_h': 4}
Geometry: {'sextants_w': 3, 'sextants_h': 4, 'sextant_size': 20, 'min_q': 0, 'max_q': 59, 'min_r': 0, 'max_r': 79}
```

---

## Smoke Test Execution

### Run the Smoke Test

The smoke test is a standalone script. Run it via:

```bash
docker exec -i gc_backend python - < backend/tests/smoke_mapgen_config_gc_mvp_001.py
```

Or if copied into the container:

```bash
docker cp backend/tests/smoke_mapgen_config_gc_mvp_001.py gc_backend:/app/tests/
docker exec -it gc_backend python /app/tests/smoke_mapgen_config_gc_mvp_001.py
```

### Expected Output

```
============================================================
SMOKE TEST: smoke_mapgen_config_gc_mvp_001
============================================================

Constants: SEXTANT_SIZE=20, MIN=2, MAX=6

Testing validate_map_config (valid inputs)...
  test_valid_min_size OK
  test_valid_max_size OK
  test_valid_mixed_sizes OK
  test_unknown_keys_ignored OK

Testing validate_map_config (missing keys)...
  test_missing_width_key OK
  test_missing_height_key OK
  test_missing_both_keys OK

Testing validate_map_config (type errors)...
  test_non_int_width_string OK
  test_non_int_width_float OK
  test_non_int_height_string OK
  test_non_int_height_none OK

Testing validate_map_config (range errors)...
  test_width_below_min OK
  test_width_above_max OK
  test_height_below_min OK
  test_height_above_max OK

Testing derive_map_geometry...
  test_geometry_sextant_size OK
  test_geometry_min_config OK
  test_geometry_max_config OK
  test_geometry_asymmetric OK
  test_geometry_bounds_ordering OK
  test_geometry_bounds_monotonic OK
  test_no_floats_in_geometry OK

Testing helper functions...
  test_is_hex_in_bounds OK
  test_sextant_coords OK
  test_local_coords OK
  test_global_from_sextant_local OK

============================================================
SMOKE OK - All mapgen config tests passed
============================================================
```

Exit code: `0` (success)

---

## Test Coverage Summary

### Validation Tests

| Test | Validates |
|------|-----------|
| `test_valid_min_size` | Min sextant size (2×2) accepts |
| `test_valid_max_size` | Max sextant size (6×6) accepts |
| `test_valid_mixed_sizes` | Different w/h values accept |
| `test_unknown_keys_ignored` | Unknown keys don't cause errors |
| `test_missing_width_key` | Missing width key raises clear error |
| `test_missing_height_key` | Missing height key raises clear error |
| `test_missing_both_keys` | Empty config raises error on first key |
| `test_non_int_width_string` | String width raises type error |
| `test_non_int_width_float` | Float width raises type error |
| `test_non_int_height_string` | String height raises type error |
| `test_non_int_height_none` | None height raises type error |
| `test_width_below_min` | Width < 2 raises range error |
| `test_width_above_max` | Width > 6 raises range error |
| `test_height_below_min` | Height < 2 raises range error |
| `test_height_above_max` | Height > 6 raises range error |

### Geometry Tests

| Test | Validates |
|------|-----------|
| `test_geometry_sextant_size` | sextant_size = SEXTANT_SIZE constant |
| `test_geometry_min_config` | 2×2 produces max_q=39, max_r=39 |
| `test_geometry_max_config` | 6×6 produces max_q=119, max_r=119 |
| `test_geometry_asymmetric` | 3×4 produces max_q=59, max_r=79 |
| `test_geometry_bounds_ordering` | All configs have min < max |
| `test_geometry_bounds_monotonic` | Larger sextant counts = larger bounds |
| `test_no_floats_in_geometry` | All geometry values are int |

### Helper Function Tests

| Test | Validates |
|------|-----------|
| `test_is_hex_in_bounds` | Boundary checking works correctly |
| `test_sextant_coords` | Global→sextant conversion correct |
| `test_local_coords` | Global→local conversion correct |
| `test_global_from_sextant_local` | Sextant+local→global conversion + roundtrip |

---

## Integration with Existing Code

### Constants Used

From `backend/app/constants.py`:

| Constant | Value | Usage |
|----------|-------|-------|
| `SEXTANT_SIZE` | 20 | Hexes per sextant side |
| `MAP_SIZE_MIN_SEXTANTS` | 2 | Minimum map dimension |
| `MAP_SIZE_MAX_SEXTANTS` | 6 | Maximum map dimension |

### Future Integration Points

| Module | Will Use |
|--------|----------|
| `mapgen.py` (T2-T6) | All functions from this task |
| `main.py` | `validate_map_config` for game creation |
| `hex_utils.py` | Coordinates are compatible |

---

## Git Commands

### Check Status

```bash
git status
```

**Expected new files:**
```
backend/app/mapgen.py
backend/tests/smoke_mapgen_config_gc_mvp_001.py
docs/mapgen_config_gc_mvp_001.md
docs/mapgen_config_gc_mvp_001_impl.md
```

### Stage Files

```bash
git add backend/app/mapgen.py
git add backend/tests/smoke_mapgen_config_gc_mvp_001.py
git add docs/mapgen_config_gc_mvp_001.md
git add docs/mapgen_config_gc_mvp_001_impl.md
```

### Commit

```bash
git commit -m "A1b T1: Add map config validation and geometry derivation

- Create backend/app/mapgen.py with MapConfig and MapGeometry TypedDicts
- Implement validate_map_config() with clear error messages
- Implement derive_map_geometry() for coordinate bounds
- Add helper functions: is_hex_in_bounds, sextant/local coord conversion
- Add comprehensive smoke test (no pytest)
- Add design + implementation documentation

Invariants maintained:
- Pure functions (no RNG, no side effects)
- No floats (all integers)
- Global axial (q, r) only
- No schema changes"
```

---

## Troubleshooting

### Import Error: `ModuleNotFoundError: No module named 'app'`

The smoke test adds `/app` to `sys.path`. If running outside Docker, ensure you're in the correct directory.

### Smoke Test Fails on Assertion

Check the specific assertion message. Common issues:
- Constants changed in `constants.py`
- Function signatures modified
- Bounds calculation error

### Permission Denied

Check Docker volume mounts in `docker-compose.dev.yml`.

---

## Completion Criteria

Task T1 is complete when:

- [ ] `mapgen.py` imports without error
- [ ] Smoke test prints `SMOKE OK`
- [ ] All 24 individual tests pass
- [ ] No new dependencies introduced
- [ ] Changes committed to git

---

## Next Task

**T2: Sextant Grid + Coordinate Mapping**

- Define sextant layout for N players
- Choose home sextants using spiral placement
- Integrate with Player.home_sextant_q/r

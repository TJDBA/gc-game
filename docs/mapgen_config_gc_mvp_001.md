# Map Config Contract: gc_mvp_001

## Overview

**File:** `backend/app/mapgen.py`

This module provides map configuration validation and geometry derivation for Galactic Conquest MVP. It is the first component of the map generation system, responsible for validating user-provided config and computing derived coordinate bounds.

**Milestone:** A1b (Map Generation)  
**Task:** T1 (Map Config Contract + Derived Geometry)

---

## Purpose

The mapgen config module:

1. **Validates input config** — Ensures map_sextants_w and map_sextants_h are valid integers within bounds
2. **Normalizes config** — Returns a clean TypedDict with only recognized fields
3. **Derives geometry** — Computes coordinate bounds from config + constants
4. **Provides helpers** — Utility functions for sextant/local coordinate conversion

---

## Type Definitions

### MapConfig

```python
class MapConfig(TypedDict, total=False):
    map_sextants_w: int  # Width in sextants (required)
    map_sextants_h: int  # Height in sextants (required)
```

**Constraints:**
- `map_sextants_w` in [MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS] = [2, 6]
- `map_sextants_h` in [MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS] = [2, 6]

### MapGeometry

```python
class MapGeometry(TypedDict):
    sextants_w: int      # Width in sextants (from config)
    sextants_h: int      # Height in sextants (from config)
    sextant_size: int    # Size of each sextant (from constants, always 20)
    min_q: int           # Minimum valid q coordinate (always 0)
    max_q: int           # Maximum valid q coordinate (inclusive)
    min_r: int           # Minimum valid r coordinate (always 0)
    max_r: int           # Maximum valid r coordinate (inclusive)
```

---

## Bounds Calculation

### Formula

Given:
- `W` = map_sextants_w (number of sextant columns)
- `H` = map_sextants_h (number of sextant rows)
- `S` = SEXTANT_SIZE = 20 (hexes per sextant side)

Bounds are computed as:
- `min_q = 0`
- `max_q = W × S - 1` (inclusive)
- `min_r = 0`
- `max_r = H × S - 1` (inclusive)

### Examples

| Config | Width (hexes) | Height (hexes) | q range | r range |
|--------|---------------|----------------|---------|---------|
| 2×2 | 40 | 40 | 0-39 | 0-39 |
| 3×3 | 60 | 60 | 0-59 | 0-59 |
| 6×6 | 120 | 120 | 0-119 | 0-119 |
| 3×4 | 60 | 80 | 0-59 | 0-79 |

### What Bounds Guarantee

The bounds define a conservative rectangular region in global axial coordinates that contains all valid hex positions for system/fleet placement. Any hex with:
```
min_q <= q <= max_q AND min_r <= r <= max_r
```
is considered within the map boundary.

### What Bounds Do NOT Guarantee

- **Hex-shape exactness** — This is a rectangular bounding box, not a hexagonal region
- **Sextant membership** — A hex within bounds may straddle sextant boundaries; use sextant conversion functions for exact membership

---

## Coordinate System

### Global Axial Coordinates

All coordinates are global axial `(q, r)`:
- `q` increases East
- `r` increases Southeast
- Origin `(0, 0)` is the top-left corner of sextant `(0, 0)`

### Sextant Coordinates

Sextants are indexed by `(sextant_q, sextant_r)`:
- Sextant `(0, 0)` covers global q: 0-19, r: 0-19
- Sextant `(1, 0)` covers global q: 20-39, r: 0-19
- Sextant `(0, 1)` covers global q: 0-19, r: 20-39

### Conversion Formulas

**Global to Sextant:**
```
sextant_q = q // SEXTANT_SIZE
sextant_r = r // SEXTANT_SIZE
```

**Global to Local (within sextant):**
```
local_q = q % SEXTANT_SIZE
local_r = r % SEXTANT_SIZE
```

**Sextant+Local to Global:**
```
global_q = sextant_q × SEXTANT_SIZE + local_q
global_r = sextant_r × SEXTANT_SIZE + local_r
```

---

## API Reference

### validate_map_config(map_config: Dict[str, Any]) -> MapConfig

Validates and normalizes a map configuration dictionary.

**Args:**
- `map_config`: Raw configuration dictionary (typically from JSON)

**Returns:**
- Validated `MapConfig` with only recognized fields

**Raises:**
- `ValueError`: If validation fails (message pinpoints the offending key/value)

**Behavior:**
1. Checks `map_sextants_w` exists and is an int within [2, 6]
2. Checks `map_sextants_h` exists and is an int within [2, 6]
3. Returns normalized config (unknown keys ignored)

### derive_map_geometry(map_config: MapConfig) -> MapGeometry

Computes derived map geometry from a validated configuration.

**Args:**
- `map_config`: Validated `MapConfig` (call validate_map_config first)

**Returns:**
- `MapGeometry` with all derived fields populated

### Helper Functions

| Function | Description |
|----------|-------------|
| `is_hex_in_bounds(q, r, geometry)` | Check if (q, r) is within map bounds |
| `get_sextant_coords(q, r)` | Get sextant (sq, sr) for a global position |
| `get_local_coords(q, r)` | Get local (lq, lr) within sextant |
| `global_from_sextant_local(sq, sr, lq, lr)` | Convert sextant+local to global |

---

## Error Messages

Validation errors are specific and actionable:

| Error Condition | Example Message |
|----------------|-----------------|
| Missing key | `map_config missing required key: 'map_sextants_w'` |
| Wrong type | `map_config['map_sextants_w'] must be int, got str: '2'` |
| Below min | `map_config['map_sextants_w'] must be >= 2, got 1` |
| Above max | `map_config['map_sextants_h'] must be <= 6, got 7` |

---

## Invariants

Repeated per project constitution:

1. **Determinism** — All functions are pure and deterministic (no RNG)
2. **No floats** — All values are integers
3. **Global axial only** — Coordinates use (q, r) axial system
4. **No schema changes** — Uses existing ORM models only

---

## Future Extensions

This module will be extended with:

| Task | Functions |
|------|-----------|
| T2: Sextant Grid | Home sextant assignment, layout planning |
| T3: Home Systems | System placement at sextant centers |
| T4: Non-Home Systems | Class-based system distribution |
| T5: RP Assignment | Deterministic RP value assignment |
| T6: Starting State | Population, fleet, ship creation |

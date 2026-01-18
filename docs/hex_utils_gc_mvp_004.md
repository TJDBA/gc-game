# Hex Utilities Module: gc_mvp_004

## Overview

**File:** `backend/app/hex_utils.py`

This module provides hex grid utilities for Galactic Conquest MVP using global axial coordinates. It serves as the foundation for map generation, visibility/scanning, and spatial game logic.

**Milestone:** A1 (Schema + Map Generation)  
**Step:** 4 (Hex Utilities)

---

## Purpose

The hex_utils module:

1. **Defines coordinate system** — Global axial (q, r) coordinates across the entire map
2. **Encapsulates hex math** — Distance, neighbors, rings, and bounds checking
3. **Supports sextant logic** — Derives sextant membership from global coordinates
4. **Enables bounds filtering** — Rectangular map bounds for edge handling
5. **Prepares for client mirroring** — Clean APIs that can be replicated in Godot

---

## Coordinate System

### Global Axial Coordinates

The game uses **global axial coordinates** `(q, r)` where:
- `q` increases **East**
- `r` increases **Southeast**
- Third axis `s = -q - r` (implicit, used in distance calculations)

This is a standard "pointy-top" hex orientation.

```
        (-1, -1)   (0, -1)
              \     /
     (-1, 0) — (0,0) — (1, 0)
              /     \
         (0, 1)   (1, 1)
```

### Sextants

Sextants are **logical 20×20 groupings** of hexes, not separate coordinate systems.

A hex's sextant is derived from its global coordinates:
- `sextant_q = q // SEXTANT_SIZE`
- `sextant_r = r // SEXTANT_SIZE`

Local coordinates within a sextant:
- `local_q = q % SEXTANT_SIZE`
- `local_r = r % SEXTANT_SIZE`

**Why sextants?**
- Map generation creates systems per sextant
- Home systems are placed at sextant centers
- UI can navigate by sextant

### Map Bounds

The map is a **rectangle** in (q, r) space:
- `q_min = 0`
- `r_min = 0`
- `q_max = sextants_w × SEXTANT_SIZE - 1`
- `r_max = sextants_h × SEXTANT_SIZE - 1`

For a 3×2 sextant map:
- q: 0 to 59 (3 × 20 - 1)
- r: 0 to 39 (2 × 20 - 1)

---

## API Reference

### Data Classes

#### `Hex`

Immutable hex coordinate.

```python
@dataclass(frozen=True, slots=True)
class Hex:
    q: int
    r: int
```

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `sextant_q` | int | Q coordinate of containing sextant |
| `sextant_r` | int | R coordinate of containing sextant |
| `local_q` | int | Q position within sextant (0 to 19) |
| `local_r` | int | R position within sextant (0 to 19) |

**Methods:**
| Method | Return | Description |
|--------|--------|-------------|
| `to_tuple()` | tuple[int, int] | Returns `(q, r)` |

**Example:**
```python
h = Hex(25, 35)
h.sextant_q  # 1
h.sextant_r  # 1
h.local_q    # 5
h.local_r    # 15
h.to_tuple() # (25, 35)
```

#### `MapBounds`

Rectangular map bounds derived from sextant dimensions.

```python
@dataclass(frozen=True, slots=True)
class MapBounds:
    sextants_w: int
    sextants_h: int
```

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `q_min` | int | Always 0 |
| `r_min` | int | Always 0 |
| `q_max` | int | `sextants_w × SEXTANT_SIZE - 1` |
| `r_max` | int | `sextants_h × SEXTANT_SIZE - 1` |

**Methods:**
| Method | Return | Description |
|--------|--------|-------------|
| `contains(q, r)` | bool | True if (q, r) is within bounds |

**Example:**
```python
bounds = MapBounds(3, 2)
bounds.q_max        # 59
bounds.r_max        # 39
bounds.contains(30, 20)  # True
bounds.contains(60, 0)   # False
```

### Functions

#### `axial_distance(a: Hex, b: Hex) -> int`

Calculate distance between two hexes.

**Formula:** `max(|dq|, |dr|, |dq + dr|)`

This equals `(|dq| + |dr| + |ds|) / 2` where `s = -q - r`.

**Examples:**
```python
axial_distance(Hex(0, 0), Hex(0, 0))  # 0
axial_distance(Hex(0, 0), Hex(1, 0))  # 1
axial_distance(Hex(0, 0), Hex(2, 1))  # 3
```

#### `in_bounds(h: Hex, bounds: MapBounds) -> bool`

Check if a hex is within map bounds.

```python
bounds = MapBounds(2, 2)
in_bounds(Hex(10, 10), bounds)  # True
in_bounds(Hex(-1, 0), bounds)   # False
```

#### `neighbors(h: Hex, bounds: MapBounds | None = None) -> list[Hex]`

Get all neighbors of a hex.

Returns up to 6 hexes in AXIAL_DIRECTIONS order (E, NE, NW, W, SW, SE).
If bounds provided, filters out-of-bounds neighbors.

```python
neighbors(Hex(10, 10))           # 6 hexes
neighbors(Hex(0, 0), bounds)     # Fewer (corner filtering)
```

#### `ring(center: Hex, radius: int, bounds: MapBounds | None = None) -> list[Hex]`

Get all hexes at exactly the specified distance from center.

| Radius | Count (unbounded) |
|--------|-------------------|
| 0 | 1 (just center) |
| 1 | 6 |
| 2 | 12 |
| n | 6 × n |

If bounds provided, filters out-of-bounds hexes.

```python
ring(Hex(10, 10), 0)   # [Hex(10, 10)]
ring(Hex(10, 10), 1)   # 6 hexes at distance 1
ring(Hex(10, 10), 2)   # 12 hexes at distance 2
ring(Hex(0, 0), 1, bounds)  # Fewer (edge filtering)
```

#### `hexes_in_range(center: Hex, radius: int, bounds: MapBounds | None = None) -> list[Hex]`

Get all hexes within the specified distance (inclusive).

| Radius | Count (unbounded) | Formula |
|--------|-------------------|---------|
| 0 | 1 | 1 |
| 1 | 7 | 1 + 6 |
| 2 | 19 | 1 + 6 + 12 |
| n | 1 + 3n(n+1) | Sum of rings 0..n |

```python
hexes_in_range(Hex(10, 10), 0)  # 1 hex
hexes_in_range(Hex(10, 10), 1)  # 7 hexes
hexes_in_range(Hex(10, 10), 2)  # 19 hexes
```

#### `hex_from_sextant_local(sextant_q, sextant_r, local_q, local_r) -> Hex`

Create a Hex from sextant and local coordinates.

Inverse of `Hex.sextant_q/r` and `local_q/r` properties.

```python
h = hex_from_sextant_local(1, 2, 5, 10)
h.q  # 25 (1 * 20 + 5)
h.r  # 50 (2 * 20 + 10)
```

#### `sextant_center(sextant_q, sextant_r) -> Hex`

Get the center hex of a sextant.

Center is at local `(SEXTANT_SIZE // 2, SEXTANT_SIZE // 2)` = `(10, 10)`.

```python
sextant_center(0, 0)  # Hex(10, 10)
sextant_center(1, 1)  # Hex(30, 30)
```

#### `validate_hex_in_bounds(h: Hex, bounds: MapBounds) -> None`

Raises `ValueError` if hex is out of bounds.

#### `validate_sextant_in_bounds(sextant_q, sextant_r, bounds: MapBounds) -> None`

Raises `ValueError` if sextant is out of bounds.

---

## Constants Used

From `app.constants` (Step 3):

| Constant | Value | Usage |
|----------|-------|-------|
| `SEXTANT_SIZE` | 20 | Hexes per sextant side |
| `AXIAL_DIRECTIONS` | [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)] | Neighbor offsets |

---

## Design Decisions

### Why Global Coordinates?

Alternative: Separate coordinate systems per sextant with conversion.

Chosen approach: Single global coordinate space because:
1. **Simpler math** — No coordinate system conversions
2. **Cleaner API** — All functions work with Hex directly
3. **Future-proof** — Movement/scanning across sextant boundaries is trivial

### Why Rectangular Bounds?

Alternative: Hex-shaped map boundaries.

Chosen approach: Rectangular bounds because:
1. **Sextant alignment** — Map is always whole sextants
2. **Simple checks** — Just min/max comparisons
3. **Consistent** — No special cases for map shape

### Why No Caching?

Alternative: Cache neighbors, rings, etc.

Chosen approach: No caching because:
1. **Clarity** — Functions are straightforward
2. **Memory** — Avoid unbounded cache growth
3. **Correctness** — No cache invalidation complexity
4. **Performance** — These operations are fast enough

### Why Frozen Dataclass?

Hex is `frozen=True` and `slots=True` because:
1. **Immutability** — Prevents accidental modification
2. **Hashability** — Can use in sets and as dict keys
3. **Memory** — Slots reduce per-instance overhead
4. **Equality** — Automatic `__eq__` and `__hash__`

---

## Future Usage

This module will be used by:

| Module | Usage |
|--------|-------|
| **mapgen.py** (Step 6) | Generate systems per sextant, place home systems |
| **scanning.py** (A6) | Calculate visibility ranges, build scan snapshots |
| **turn_processor.py** (A5+) | Validate movement, detect combat zones |
| **API endpoints** | Return hex coordinates in responses |
| **Godot client** | Mirror module for client-side calculations |

---

## Examples

### Basic Usage

```python
from app.hex_utils import Hex, MapBounds, axial_distance, neighbors, ring

# Create hexes
h1 = Hex(10, 10)
h2 = Hex(15, 12)

# Calculate distance
dist = axial_distance(h1, h2)  # 7

# Get neighbors
ns = neighbors(h1)  # 6 hexes

# Generate ring
r2 = ring(h1, 2)  # 12 hexes at distance 2
```

### Bounded Operations

```python
from app.hex_utils import Hex, MapBounds, neighbors, ring, in_bounds

# 2x2 sextant map (40x40 hexes)
bounds = MapBounds(2, 2)

# Check bounds
in_bounds(Hex(10, 10), bounds)  # True
in_bounds(Hex(50, 10), bounds)  # False

# Corner has fewer neighbors
corner_ns = neighbors(Hex(0, 0), bounds)  # 2 hexes

# Ring filtering
edge_ring = ring(Hex(0, 0), 3, bounds)  # Only in-bounds hexes
```

### Sextant Operations

```python
from app.hex_utils import Hex, hex_from_sextant_local, sextant_center

# Get hex from sextant + local
h = hex_from_sextant_local(1, 2, 5, 10)
# h.q = 25, h.r = 50

# Get sextant center for home system placement
center = sextant_center(0, 0)  # Hex(10, 10)
```

---

## Notes

- **No line interpolation** — Not implemented in this step per requirements
- **No pathfinding** — Out of scope; use distance for range validation only
- **Godot mirroring** — Keep APIs deterministic and well-documented for client replication

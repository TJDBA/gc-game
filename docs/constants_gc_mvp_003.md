# Constants Module: gc_mvp_003

## Overview

**File:** `backend/app/constants.py`

This module centralizes all invariant gameplay constants for Galactic Conquest MVP. It serves as the single source of truth for numeric values, configuration defaults, and game balance parameters.

**Milestone:** A1 (Schema + Map Generation)  
**Step:** 3 (Game Constants)

---

## Purpose

The constants module:

1. **Eliminates magic numbers** — All gameplay values are named and documented
2. **Centralizes configuration** — Single location for game balance tuning
3. **Enables consistent imports** — Other modules import from one place
4. **Separates concerns** — Numeric constants here; type enums in `models.py`

---

## File Placement Rationale

**Chosen path:** `backend/app/constants.py`

This location was selected because:

1. **Milestone specification** — `003_milestone_a1_implementation.md` explicitly specifies this path
2. **Sibling to models** — Lives alongside `models.py`, `db.py`, `main.py` for easy discovery
3. **Import convenience** — `from app.constants import X` works from any backend module
4. **No circular dependencies** — Constants have no imports from other app modules

Alternative considered: `backend/app/game/constants.py` — Rejected because it would require creating a new subpackage and the milestone doc specifies the flat structure.

---

## Constants Reference

### Players & Games

| Constant | Value | Purpose |
|----------|-------|---------|
| `MIN_PLAYERS` | 2 | Minimum players to start a game |
| `MAX_PLAYERS` | 24 | Maximum players per game |
| `JOIN_CODE_LENGTH` | 4 | Length of game join codes |

### Turns

| Constant | Value | Purpose |
|----------|-------|---------|
| `TURN_NUMBER_START` | 1 | Initial turn number |
| `CURRENT_TURN_START` | 1 | Initial `game.current_turn` value |
| `DEFAULT_TURN_TIMEOUT_SECONDS` | 36288000 | ~420 days (effectively no timeout) |

### Resources & Population

| Constant | Value | Purpose |
|----------|-------|---------|
| `STARTING_RP` | 10 | RP given at game start |
| `STARTING_POP_TENTHS` | 10 | Starting home system population (1.0) |
| `POP_TENTHS_PER_POP` | 10 | Conversion: 10 tenths = 1.0 pop |
| `MIN_RP` | 0 | Minimum RP (no maximum) |

### Technology

| Constant | Value | Purpose |
|----------|-------|---------|
| `MIN_TECH_LEVEL` | 0 | Minimum tech level |
| `MAX_TECH_LEVEL` | 5 | Maximum tech level |
| `STARTING_TECH_LEVEL` | 1 | Initial tech level for all types |
| `TECH_COSTS` | [5, 10, 15, 20, 25] | Cost to upgrade each level |

### Scanning

**Critical: No +1 anywhere in scan math.**

| Formula | Description |
|---------|-------------|
| `scan_base = scanning_tech` | Base value (NOT 1 + scanning_tech) |
| `LONG = scan_base * 2` | Presence-only range |
| `MEDIUM = scan_base` | Partial details range |
| `SHORT = floor(scanning_tech / 2)` | Full details range (0 = same-hex only) |

**Band Priority:** SHORT > MEDIUM > LONG (SHORT is best/most detailed)

Example at tech level 1:
- SHORT: 0 hexes (same-hex only)
- MEDIUM: 1 hex
- LONG: 2 hexes

**Functions provided:**
- `calc_scan_base(scanning_tech)` — Returns scanning_tech
- `calc_long_range(scanning_tech)` — Returns scan_base * 2 + 2
- `calc_medium_range(scanning_tech)` — Returns scan_base
- `calc_short_range(scanning_tech)` — Returns scanning_tech // 2

### Ships

`SHIP_STATS` dictionary:

| Type | Cost | CV | Max Range | Cargo |
|------|------|----|-----------|-------|
| SCOUT | 1 | 1 | 6 | 0 |
| CRUISER | 5 | 5 | 4 | 0 |
| BATTLESHIP | 10 | 10 | 3 | 0 |
| TRANSPORT | 5 | 0 | 4 | 10 |

`STARTING_SHIPS`: `["SCOUT", "SCOUT", "CRUISER", "TRANSPORT"]`

### Systems

`SYSTEM_RP_RANGES` — RP value ranges by class:

| Class | RP Range | Notes |
|-------|----------|-------|
| A | 8-12 | Rare, home sextants only |
| B | 5-8 | Uncommon |
| C | 3-5 | Common |
| D | 1-3 | Common |
| E | 0-1 | Common |

`SEXTANT_SYSTEM_COUNTS` — Systems per sextant by class:

| Class | Count Range |
|-------|-------------|
| A | 0-1 |
| B | 1-3 |
| C | 2-5 |
| D | 3-6 |
| E | 2-4 |

### Control

| Constant | Value | Purpose |
|----------|-------|---------|
| `CONTROL_MIN_POP_TENTHS` | 5 | Min pop for control (0.5) |
| `CONTROL_RATIO` | 2 | Must have 2× other factions combined |

### Map & Hex Grid

| Constant | Value | Purpose |
|----------|-------|---------|
| `SEXTANT_SIZE` | 20 | Hexes per sextant dimension (20×20) |
| `MAP_SIZE_MIN_SEXTANTS` | 2 | Minimum map size (2×2 sextants) |
| `MAP_SIZE_MAX_SEXTANTS` | 6 | Maximum map size (6×6 sextants) |
| `AXIAL_DIRECTIONS` | [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)] | Neighbor directions |

### Taxes

| Constant | Value | Purpose |
|----------|-------|---------|
| `TAX_TURN_INTERVAL` | 10 | Taxes every 10th turn |
| `TAX_COST_PER_POP_TENTH` | 1 | 1 RP per 0.1 population |

### API Pagination

| Constant | Value | Purpose |
|----------|-------|---------|
| `DEFAULT_PAGE_SIZE` | 50 | Default items per page |
| `MAX_PAGE_SIZE` | 200 | Maximum items per page |

### Faction Colors

24 named colors to support `MAX_PLAYERS`:

| # | Name | Hex |
|---|------|-----|
| 1 | Crimson | #D32F2F |
| 2 | Azure | #1976D2 |
| 3 | Emerald | #2E7D32 |
| 4 | Gold | #F9A825 |
| 5 | Violet | #7B1FA2 |
| 6 | Amber | #FF8F00 |
| 7 | Teal | #00796B |
| 8 | Scarlet | #E53935 |
| 9 | Indigo | #303F9F |
| 10 | Jade | #43A047 |
| 11 | Silver | #9E9E9E |
| 12 | Obsidian | #212121 |
| 13 | Cobalt | #1565C0 |
| 14 | Copper | #B87333 |
| 15 | Magenta | #C2185B |
| 16 | Sapphire | #0D47A1 |
| 17 | Chartreuse | #7CB342 |
| 18 | Coral | #FF7043 |
| 19 | Slate | #546E7A |
| 20 | Ivory | #F5F5DC |
| 21 | Maroon | #6D1B1B |
| 22 | Turquoise | #00ACC1 |
| 23 | Bronze | #8D6E63 |
| 24 | Onyx | #000000 |

**Helper functions:**
- `get_faction_color(player_index)` — Returns hex code
- `get_faction_color_name(player_index)` — Returns color name

Colors wrap around if player_index ≥ 24.

---

## Future Step Consumption

| Step/Module | Constants Used |
|-------------|---------------|
| **Step 4: Hex Utilities** | `SEXTANT_SIZE`, `AXIAL_DIRECTIONS` |
| **Step 5: Map Generator** | `SEXTANT_SIZE`, `SYSTEM_RP_RANGES`, `SEXTANT_SYSTEM_COUNTS`, `STARTING_*`, `get_faction_color()` |
| **A2: Game Start** | `STARTING_RP`, `STARTING_POP_TENTHS`, `STARTING_SHIPS`, `STARTING_TECH_LEVEL`, `MIN_PLAYERS` |
| **A3: Orders CRUD** | `SHIP_STATS` (for validation) |
| **A5: Turn Processor** | All ship/combat constants |
| **A6: Scanning & Fog** | `calc_*_range()`, `SCAN_BAND_PRIORITY` |
| **B8: Economy** | `SYSTEM_RP_RANGES`, `CONTROL_*` |
| **C11: Taxes** | `TAX_*` constants |
| **API Endpoints** | `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE` |

---

## Design Decisions

### Why not use model enums here?

Model enums (`GameStatus`, `ShipType`, etc.) are defined in `models.py` because:
1. They're tightly coupled to ORM column definitions
2. Duplicating them would create sync issues
3. `constants.py` can import from `models.py` if needed (but currently doesn't)

### Why functions for scan math?

Functions (`calc_long_range`, etc.) instead of static values because:
1. Scan ranges depend on current tech level
2. Encapsulates the formula in one place
3. Future-proofs against formula changes

### Why named tuples for colors?

`FACTION_COLORS` uses `(name, hex)` tuples to:
1. Support display of color names in UI
2. Enable validation that names and codes are unique
3. Provide both lookup patterns (`FACTION_COLOR_HEX_CODES[i]` and `dict(FACTION_COLORS)[name]`)

---

## Notes

- **Replace `GAME_ID`** — Any commands or examples using `GAME_ID` should use an actual UUID from your database.
- **Starting tech level** — Set to 1 (not 0) per hard constraints. Init logic applies this in a later step.
- **Scan math override** — The "no +1 anywhere" rule overrides the formula in previous milestone docs.

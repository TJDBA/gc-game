# Migration: gc_mvp_001_full_schema

## Overview

This migration creates the complete database schema for Galactic Conquest MVP. It adds ten new tables and updates three existing tables to support the full game mechanics including star systems, fleets, ships, populations, technology, diplomacy, and event logging.

**File:** `backend/alembic/versions/gc_mvp_001_full_schema.py`

---

## Tables Modified

### games

The games table is updated to track game state more precisely:

| Column | Type | Change | Purpose |
|--------|------|--------|---------|
| `status` | VARCHAR(20) | **Added** | Replaces `started` boolean. Values: `LOBBY`, `ACTIVE`, `FINISHED` |
| `rng_seed` | BIGINT | **Added** | Seed for deterministic map generation. Ensures identical maps for replay/debugging |
| `started` | BOOLEAN | **Removed** | Replaced by `status` enum for more granular state tracking |

**Why the change:** A boolean `started` can't distinguish between an active game and a finished one. The `status` enum allows proper game lifecycle management.

### players

The players table is extended with game-relevant attributes:

| Column | Type | Change | Purpose |
|--------|------|--------|---------|
| `faction_color` | VARCHAR(7) | **Added** | Hex color code (e.g., `#E63946`) for UI display |
| `banked_rp` | INTEGER | **Added** | Resource Points accumulated by the player |
| `home_sextant_q` | INTEGER | **Added** | Q coordinate of player's home sextant |
| `home_sextant_r` | INTEGER | **Added** | R coordinate of player's home sextant |
| `is_eliminated` | BOOLEAN | **Added** | True if player has been knocked out of the game |

**Why these additions:** These fields track the player's in-game state. Faction colors are auto-assigned at join time. Sextant coordinates are set when the game starts and map is generated.

### turns

The turns table gains determinism support:

| Column | Type | Change | Purpose |
|--------|------|--------|---------|
| `rng_seed` | BIGINT | **Added** | Seed for deterministic turn resolution. Derived from game seed + turn number |

**Why this addition:** Deterministic RNG allows identical turn resolution for debugging and potential replay features.

---

## New Tables

### systems

Represents star systems on the hex map.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique system identifier |
| `game_id` | UUID | FK → games, NOT NULL | Which game this system belongs to |
| `hex_q` | INTEGER | NOT NULL | Q coordinate in axial hex grid |
| `hex_r` | INTEGER | NOT NULL | R coordinate in axial hex grid |
| `system_class` | VARCHAR(1) | NOT NULL, CHECK (A-E) | Star class determining base RP value |
| `rp_value` | INTEGER | NOT NULL | Resource Points generated when controlled |
| `neutral_pop_tenths` | INTEGER | DEFAULT 0 | Neutral population (in 0.1 units) |
| `neutral_disposition` | VARCHAR(20) | NULLABLE | How neutrals behave: `HOSTILE`, `FRIENDLY`, `DEFENSIVE` |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |

**Relationships:**
- Belongs to a Game
- Has many Populations (player populations at this system)

**Constraints:**
- `uq_systems_game_hex`: Unique constraint on (game_id, hex_q, hex_r) - one system per hex per game
- `ck_systems_class`: Check constraint ensuring class is A, B, C, D, or E

**System Classes:**

| Class | RP Range | Rarity | Notes |
|-------|----------|--------|-------|
| A | 8-12 | Rare | Only in home sextants |
| B | 5-8 | Uncommon | Good secondary targets |
| C | 3-5 | Common | Average systems |
| D | 1-3 | Common | Low-value systems |
| E | 0-1 | Common | Nearly worthless |

### fleets

Container for player-owned ships at a location.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique fleet identifier |
| `game_id` | UUID | FK → games, NOT NULL | Which game this fleet belongs to |
| `player_id` | UUID | FK → players, NOT NULL | Fleet owner |
| `hex_q` | INTEGER | NOT NULL | Current Q position |
| `hex_r` | INTEGER | NOT NULL | Current R position |
| `cargo_pop_tenths` | INTEGER | DEFAULT 0 | Population being transported (in 0.1 units) |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |

**Relationships:**
- Belongs to a Game
- Belongs to a Player
- Has many Ships

**Design Notes:**
- Fleets are containers - they can be empty (after all ships destroyed)
- Empty fleets should be cleaned up by turn processing
- Cargo represents population loaded onto transports
- Fleet movement range is determined by slowest ship + tech level

### ships

Individual ships within fleets.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique ship identifier |
| `fleet_id` | UUID | FK → fleets, NOT NULL | Parent fleet |
| `ship_type` | VARCHAR(20) | NOT NULL, CHECK | Ship class |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |

**Ship Types:**

| Type | Cost | Combat Value | Max Range | Cargo Capacity |
|------|------|--------------|-----------|----------------|
| SCOUT | 1 RP | 1 | 6 hexes | 0 |
| CRUISER | 5 RP | 5 | 4 hexes | 0 |
| BATTLESHIP | 10 RP | 10 | 3 hexes | 0 |
| TRANSPORT | 5 RP | 0 | 4 hexes | 10 (1.0 pop) |

**Design Notes:**
- Ships are never moved individually - only via fleet operations
- Ship destruction is recorded in event_log
- The `fleet_split` order moves ships between fleets

### populations

Player population at a star system.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique population record identifier |
| `system_id` | UUID | FK → systems, NOT NULL | Which system |
| `player_id` | UUID | FK → players, NOT NULL | Population owner |
| `pop_tenths` | INTEGER | NOT NULL | Population in 0.1 units (10 = 1.0 pop) |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |
| `updated_at` | TIMESTAMP | AUTO UPDATE | Last modification time |

**Control Rules:**
A player controls a system if:
1. They have population ≥ 0.5 (5 tenths)
2. Their population ≥ 2× all other factions combined

Otherwise the system is **contested** (no income).

**Why tenths?** Using integer tenths (pop_tenths) instead of floats avoids floating-point precision issues. 10 tenths = 1.0 population.

### tech_levels

Technology progression for each player.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique record identifier |
| `player_id` | UUID | FK → players, UNIQUE, NOT NULL | One record per player |
| `movement_tech` | INTEGER | DEFAULT 0, CHECK (0-5) | Movement technology level |
| `combat_tech` | INTEGER | DEFAULT 0, CHECK (0-5) | Combat technology level |
| `scanning_tech` | INTEGER | DEFAULT 0, CHECK (0-5) | Scanning technology level |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |
| `updated_at` | TIMESTAMP | AUTO UPDATE | Last modification time |

**Tech Effects:**

| Tech | Level 0 | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|------|---------|---------|---------|---------|---------|---------|
| Movement | Base+2 range | +1 | +2 | +3 | +4 | +5 |
| Combat | Base CV | +10% | +20% | +30% | +40% | +50% |
| Scanning | Base scan | +1 | +2 | +3 | +4 | +5 |

**Upgrade Costs:**

| From → To | Cost |
|-----------|------|
| 0 → 1 | 5 RP |
| 1 → 2 | 10 RP |
| 2 → 3 | 15 RP |
| 3 → 4 | 20 RP |
| 4 → 5 | 25 RP |

### stances

Diplomatic stance between players.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique record identifier |
| `player_id` | UUID | FK → players, NOT NULL | Player setting the stance |
| `target_player_id` | UUID | FK → players, NULLABLE | Target player (NULL = default stance) |
| `stance` | VARCHAR(20) | DEFAULT 'NEUTRAL' | The stance: `HOSTILE`, `NEUTRAL`, `FRIENDLY` |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |
| `updated_at` | TIMESTAMP | AUTO UPDATE | Last modification time |

**Stance Effects:**

| Stance | Combat Trigger | Shared Visibility | Notes |
|--------|----------------|-------------------|-------|
| HOSTILE | Yes | No | Fleets will fight on encounter |
| NEUTRAL | No | No | Default - fleets coexist |
| FRIENDLY | No | Yes | Allies can see each other's units |

**Design Notes:**
- `target_player_id = NULL` sets the default stance for all unknown players
- Stances are one-directional (player A can be FRIENDLY to B while B is HOSTILE to A)
- Combat only triggers if at least one side is HOSTILE

### first_contacts

Tracks when players first encounter each other.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique record identifier |
| `game_id` | UUID | FK → games, NOT NULL | Which game |
| `player_id` | UUID | FK → players, NOT NULL | First player in encounter |
| `other_player_id` | UUID | FK → players, NOT NULL | Second player in encounter |
| `turn_number` | INTEGER | NOT NULL | When contact occurred |
| `hex_q` | INTEGER | NOT NULL | Where contact occurred |
| `hex_r` | INTEGER | NOT NULL | Where contact occurred |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |

**Purpose:** Used for event logging and potentially for mechanics like "fog of war reveals" or diplomatic events on first contact.

### scan_snapshots

Records the complete state of each scanned hex at the end of each turn. This is the authoritative game state history - one record per hex per turn regardless of how many players scanned it.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique snapshot identifier |
| `turn_id` | UUID | FK → turns, NOT NULL | Which turn this snapshot is from |
| `hex_q` | INTEGER | NOT NULL | Hex Q coordinate |
| `hex_r` | INTEGER | NOT NULL | Hex R coordinate |
| `contents` | JSONB | NOT NULL | Full state of the hex at turn end |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |

**Contents JSONB structure (example):**
```json
{
  "system": {
    "id": "uuid",
    "system_class": "B",
    "rp_value": 7,
    "controller_id": "player-uuid",
    "contested": false,
    "populations": [
      {"player_id": "uuid", "pop_tenths": 15}
    ],
    "neutral_pop_tenths": 0
  },
  "fleets": [
    {
      "id": "uuid",
      "player_id": "uuid",
      "ships": [
        {"id": "uuid", "ship_type": "CRUISER"},
        {"id": "uuid", "ship_type": "SCOUT"}
      ],
      "cargo_pop_tenths": 0
    }
  ]
}
```

**Constraints:**
- `uq_scan_snapshots_turn_hex`: Unique constraint on (turn_id, hex_q, hex_r) - one snapshot per hex per turn

**Design Notes:**
- Contains the FULL state of the hex, not filtered by visibility
- Visibility filtering is done at query time using scan_visibility table
- Enables complete game replay and debugging
- Hexes with no system and no fleets are not recorded (empty space)

### scan_visibility

Lookup table linking players to hex snapshots with their best scan band. When multiple scan sources (fleets, controlled systems) can see the same hex, only the best band is recorded.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique record identifier |
| `scan_snapshot_id` | UUID | FK → scan_snapshots, NOT NULL | Which hex snapshot |
| `player_id` | UUID | FK → players, NOT NULL | Which player can see this hex |
| `scan_band` | VARCHAR(10) | NOT NULL, CHECK | Best visibility: `SHORT`, `MEDIUM`, `LONG` |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |

**Scan Band Priority (best to worst):**
1. SHORT - Full details
2. MEDIUM - Partial details
3. LONG - Presence only

**Constraints:**
- `uq_scan_visibility_snapshot_player`: Unique constraint on (scan_snapshot_id, player_id) - one band per player per hex

**How it works:**
1. At turn end, generate scan_snapshots for all hexes containing systems or fleets
2. For each player, calculate which hexes they can see from all their scan sources
3. For each visible hex, record only the BEST scan band in scan_visibility
4. Query fog of war by joining scan_visibility → scan_snapshots, filter contents based on band

**Example query for player's fog of war:**
```sql
SELECT 
  ss.hex_q, ss.hex_r, ss.contents,
  sv.scan_band
FROM scan_snapshots ss
JOIN scan_visibility sv ON sv.scan_snapshot_id = ss.id
JOIN turns t ON ss.turn_id = t.id
WHERE sv.player_id = :player_id
  AND t.game_id = :game_id
  AND t.number = :turn_number;
```

**Visibility filtering by band:**

| Field | SHORT | MEDIUM | LONG |
|-------|-------|--------|------|
| system_class | ✓ | ✓ | ✓ |
| rp_value | ✓ | band* | ✗ |
| controller_id | ✓ | ✓ | ✗ |
| contested | ✓ | ✓ | ✗ |
| populations | ✓ | ✗ | ✗ |
| fleet player_id | ✓ | ✓ | ✓ |
| fleet ships | ✓ | ✗ | ✗ |
| fleet strength_band | ✗ | ✓ | ✗ |
| fleet cargo | ✓ | ✗ | ✗ |

*MEDIUM shows RP as a band (LOW/MED/HIGH) rather than exact value

**Scan Band Range Formulas:**

| Band | Range Formula | Example (scanning_tech=2) |
|------|---------------|---------------------------|
| SHORT | floor(scanning_tech / 2) | 1 hex |
| MEDIUM | 1 + scanning_tech | 3 hexes |
| LONG | (1 + scanning_tech) × 2 | 6 hexes |

### event_log

Records all game events for replay and debugging.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PK | Unique event identifier |
| `game_id` | UUID | FK → games, NOT NULL | Which game |
| `turn_number` | INTEGER | NOT NULL | When event occurred |
| `event_type` | VARCHAR(50) | NOT NULL, CHECK | Type of event |
| `event_data` | JSONB | NOT NULL | Event-specific payload |
| `player_id` | UUID | FK → players, NULLABLE | Actor, if applicable |
| `visibility` | VARCHAR(20) | DEFAULT 'PUBLIC' | Who can see this event |
| `hex_q` | INTEGER | NULLABLE | Event location Q (if applicable) |
| `hex_r` | INTEGER | NULLABLE | Event location R (if applicable) |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |

**Event Types:**

| Event Type | Description | Typical event_data |
|------------|-------------|-------------------|
| GAME_STARTED | Game transitioned to ACTIVE | `{player_count: 2}` |
| TURN_RESOLVED | Turn processing completed | `{turn_number: 1}` |
| FLEET_MOVED | Fleet changed position | `{fleet_id, from_q, from_r, to_q, to_r}` |
| COMBAT_OCCURRED | Battle resolved | `{hex_q, hex_r, combatants: [...], winner_id, losses: [...]}` |
| SYSTEM_CAPTURED | Control changed hands | `{system_id, old_controller, new_controller}` |
| POPULATION_CHANGED | Pop grew/shrunk | `{system_id, player_id, old_pop, new_pop}` |
| TECH_PURCHASED | Tech upgraded | `{player_id, tech_type, new_level}` |
| PLAYER_ELIMINATED | Player knocked out | `{player_id}` |
| FIRST_CONTACT | Players met | `{player_id, other_player_id, hex_q, hex_r}` |

---

## Entity Relationships Diagram

```
┌──────────────┐
│    Game      │
└──────┬───────┘
       │
       ├────────────────┬────────────────┬────────────────┐
       │                │                │                │
       ▼                ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    Player    │  │    Turn      │  │   System     │  │  EventLog    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────────────┘
       │                 │                 │
       ├────────┬────────┤                 │
       │        │        │                 │
       ▼        ▼        ▼                 ▼
┌──────────┐ ┌────────┐ ┌───────────────┐ ┌──────────────┐
│  Fleet   │ │TechLvl │ │ ScanSnapshot  │ │  Population  │
└────┬─────┘ └────────┘ └───────┬───────┘ └──────────────┘
     │                          │
     ▼                          ▼
┌──────────┐              ┌────────────────┐
│   Ship   │              │ ScanVisibility │◄── Player
└──────────┘              └────────────────┘

Player ←→ Player relationships:
┌──────────┐     ┌────────────────┐
│  Stance  │     │  FirstContact  │
└──────────┘     └────────────────┘
```

---

## How to Apply This Migration

### Prerequisites
- Backend container running
- Database accessible
- Previous migrations already applied

### Steps

1. **Update `down_revision`** in the migration file to point to your actual previous migration revision ID.

2. **Run the migration:**
```bash
docker exec -it gc_backend alembic upgrade head
```

3. **Verify tables exist:**
```bash
docker exec -it gc_postgres psql -U gc_user -d galactic_conquest -c "\dt"
```

Expected output should include:
```
 Schema |       Name       | Type  |  Owner
--------+------------------+-------+---------
 public | event_log        | table | gc_user
 public | first_contacts   | table | gc_user
 public | fleets           | table | gc_user
 public | games            | table | gc_user
 public | orders           | table | gc_user
 public | players          | table | gc_user
 public | populations      | table | gc_user
 public | scan_snapshots   | table | gc_user
 public | scan_visibility  | table | gc_user
 public | sessions         | table | gc_user
 public | ships            | table | gc_user
 public | stances          | table | gc_user
 public | systems          | table | gc_user
 public | tech_levels      | table | gc_user
 public | turn_submissions | table | gc_user
 public | turns            | table | gc_user
 public | users            | table | gc_user
```

4. **Verify constraints:**
```bash
docker exec -it gc_postgres psql -U gc_user -d galactic_conquest -c "\d systems"
```

### Rollback

To revert this migration:
```bash
docker exec -it gc_backend alembic downgrade -1
```

**Warning:** This will drop all new tables and their data. Only run in development.

---

## Integration with Game Architecture

This schema supports the following game mechanics:

### Map Generation (on game start)
1. Generate sextants based on player count
2. Create System records for each star system
3. Create Fleet records for starting fleets
4. Create Ship records for starting ships
5. Create Population records for home systems
6. Create TechLevels records (all at 0)

### Turn Processing (on process trigger)
1. Read Orders for current turn
2. Update Fleet positions (hex_q, hex_r)
3. Resolve combat (delete Ships, update Fleets)
4. Transfer Populations
5. Update control (based on Population records)
6. Generate income (update Player.banked_rp)
7. Create EventLog records for all actions
8. Generate scan_snapshots for all hexes with systems or fleets
9. Calculate visibility for each player from all scan sources
10. Create scan_visibility records with best band per player per hex

### API Queries
- `/games/{id}/map` - Query Systems + Populations, filter by scan_visibility for current player
- `/games/{id}/fleets` - Query Fleets + Ships, filter contents by scan_band from scan_visibility
- `/games/{id}/me` - Query Player record
- `/games/{id}/tech` - Query TechLevels record

---

## Next Steps

After applying this migration, proceed to:
1. **Step 2:** Update SQLAlchemy models (`models.py`) to match this schema (including ScanSnapshot and ScanVisibility)
2. **Step 3:** Create game constants (`constants.py`)
3. **Step 4:** Create hex utilities (`hex.py`)

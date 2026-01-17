"""
Game constants for Galactic Conquest MVP.

This module centralizes all invariant gameplay constants used across the backend.
Constants are organized by category and should be imported by other modules
(hex utils, map generator, turn processing, etc.) rather than hardcoding values.

Note: Model enums (GameStatus, ShipType, etc.) are defined in models.py.
This module contains numeric/config constants only to avoid duplication.

Created: Step 3 of Milestone A1 (Schema + Map Generation)
"""

from typing import Dict, List, Tuple

# =============================================================================
# PLAYERS & GAMES
# =============================================================================

MIN_PLAYERS: int = 2
"""Minimum number of players required to start a game."""

MAX_PLAYERS: int = 24
"""Maximum number of players allowed in a single game."""

JOIN_CODE_LENGTH: int = 4
"""Length of the join code for games."""

# =============================================================================
# TURNS
# =============================================================================

TURN_NUMBER_START: int = 1
"""Initial turn number when a game starts."""

CURRENT_TURN_START: int = 1
"""Initial value for game.current_turn when a game starts."""

DEFAULT_TURN_TIMEOUT_SECONDS: int = 36288000
"""Default turn timeout in seconds (~420 days, effectively no timeout)."""

# =============================================================================
# RESOURCES & POPULATION
# =============================================================================

STARTING_RP: int = 10
"""Resource Points given to each player at game start."""

STARTING_POP_TENTHS: int = 10
"""Starting population at home system in tenths (10 = 1.0 pop)."""

POP_TENTHS_PER_POP: int = 10
"""Conversion factor: 10 tenths = 1.0 population."""

MIN_RP: int = 0
"""Minimum RP a player can have (no maximum defined)."""

# =============================================================================
# TECHNOLOGY
# =============================================================================

MIN_TECH_LEVEL: int = 0
"""Minimum technology level."""

MAX_TECH_LEVEL: int = 5
"""Maximum technology level."""

STARTING_TECH_LEVEL: int = 1
"""Initial tech level for all three tech types at game start."""

TECH_COSTS: List[int] = [5, 10, 15, 20, 25]
"""
Cost to upgrade each tech level.
Index = current level, value = cost to reach next level.
  0→1: 5 RP
  1→2: 10 RP
  2→3: 15 RP
  3→4: 20 RP
  4→5: 25 RP
"""

# =============================================================================
# SCANNING
# =============================================================================

# Scan range formulas (no +1 anywhere):
#   scan_base = scanning_tech
#   LONG range  = scan_base * 2
#   MEDIUM range = scan_base
#   SHORT range = floor(scanning_tech / 2)  (0 means same-hex only)
#
# Best-band ordering: SHORT > MEDIUM > LONG (SHORT is most detailed)

SCAN_BAND_PRIORITY: Dict[str, int] = {
    "SHORT": 3,   # Best/most detailed
    "MEDIUM": 2,
    "LONG": 1,    # Least detailed
}
"""
Priority values for scan bands. Higher = better detail.
Used to determine which band to store when multiple sources scan the same hex.
"""


def calc_scan_base(scanning_tech: int) -> int:
    """Calculate scan base from scanning tech level (no +1)."""
    return scanning_tech


def calc_long_range(scanning_tech: int) -> int:
    """Calculate LONG scan range: scan_base * 2 + 2. Base Rang of 4 hexes"""
    return calc_scan_base(scanning_tech) * 2 + 2


def calc_medium_range(scanning_tech: int) -> int:
    """Calculate MEDIUM scan range: scan_base."""
    return calc_scan_base(scanning_tech)


def calc_short_range(scanning_tech: int) -> int:
    """Calculate SHORT scan range: floor(scanning_tech / 2). 0 = same-hex only."""
    return scanning_tech // 2


# =============================================================================
# SHIPS
# =============================================================================

SHIP_STATS: Dict[str, Dict[str, int]] = {
    "SCOUT": {
        "cost": 1,
        "cv": 1,
        "max_range": 6,
        "cargo": 0,
    },
    "CRUISER": {
        "cost": 5,
        "cv": 5,
        "max_range": 4,
        "cargo": 0,
    },
    "BATTLESHIP": {
        "cost": 10,
        "cv": 10,
        "max_range": 3,
        "cargo": 0,
    },
    "TRANSPORT": {
        "cost": 5,
        "cv": 0,
        "max_range": 4,
        "cargo": 10,
    },
}
"""
Ship statistics by type.
  cost: RP cost to build
  cv: Combat Value
  max_range: Maximum movement range in hexes
  cargo: Population cargo capacity in tenths (10 = 1.0 pop)
"""

STARTING_SHIPS: List[str] = ["SCOUT", "SCOUT", "CRUISER", "TRANSPORT"]
"""Ships given to each player in their starting fleet."""

# =============================================================================
# SYSTEMS
# =============================================================================

SYSTEM_RP_RANGES: Dict[str, Tuple[int, int]] = {
    "A": (8, 12),
    "B": (5, 8),
    "C": (3, 5),
    "D": (1, 3),
    "E": (0, 1),
}
"""
RP value ranges by system class.
Tuple is (min_rp, max_rp) inclusive.
Class A is best (rare), Class E is worst (common).
"""

# Systems per sextant by class (min, max)
SEXTANT_SYSTEM_COUNTS: Dict[str, Tuple[int, int]] = {
    "A": (0, 1),   # 0-1 class A (only in home sextants)
    "B": (1, 3),
    "C": (2, 5),
    "D": (3, 6),
    "E": (2, 4),
}
"""
Number of systems to generate per sextant by class.
Tuple is (min_count, max_count) inclusive.
Class A systems only appear in home sextants.
"""

# =============================================================================
# CONTROL
# =============================================================================

CONTROL_MIN_POP_TENTHS: int = 5
"""Minimum population (in tenths) required to control a system (0.5 pop)."""

CONTROL_RATIO: int = 2
"""
Population ratio required for control.
Controller's pop must be >= CONTROL_RATIO * sum(all other factions' pop).
"""

# =============================================================================
# MAP & HEX GRID
# =============================================================================

SEXTANT_SIZE: int = 20
"""Size of a sextant in hexes (20x20 grid)."""

MAP_SIZE_MIN_SEXTANTS: int = 2
"""Minimum map size in sextants (2x2)."""

MAP_SIZE_MAX_SEXTANTS: int = 6
"""Maximum map size in sextants (6x6)."""

AXIAL_DIRECTIONS: List[Tuple[int, int]] = [
    (1, 0),    # East
    (1, -1),   # Northeast
    (0, -1),   # Northwest
    (-1, 0),   # West
    (-1, 1),   # Southwest
    (0, 1),    # Southeast
]
"""
Axial coordinate directions for hex grid neighbors.
Order: E, NE, NW, W, SW, SE (clockwise from East).
"""

# =============================================================================
# TAXES
# =============================================================================

TAX_TURN_INTERVAL: int = 10
"""Taxes are collected every N turns (10, 20, 30, ...)."""

TAX_COST_PER_POP_TENTH: int = 1
"""RP cost per 0.1 population during tax turns."""

# =============================================================================
# API PAGINATION
# =============================================================================

DEFAULT_PAGE_SIZE: int = 50
"""Default number of items per page for paginated endpoints."""

MAX_PAGE_SIZE: int = 200
"""Maximum allowed page size for paginated endpoints."""

# =============================================================================
# FACTION COLORS
# =============================================================================

# Named tuple-style for clarity: (name, hex_code)
FACTION_COLORS: List[Tuple[str, str]] = [
    ("Crimson", "#D32F2F"),
    ("Azure", "#1976D2"),
    ("Emerald", "#2E7D32"),
    ("Gold", "#F9A825"),
    ("Violet", "#7B1FA2"),
    ("Amber", "#FF8F00"),
    ("Teal", "#00796B"),
    ("Scarlet", "#E53935"),
    ("Indigo", "#303F9F"),
    ("Jade", "#43A047"),
    ("Silver", "#9E9E9E"),
    ("Obsidian", "#212121"),
    ("Cobalt", "#1565C0"),
    ("Copper", "#B87333"),
    ("Magenta", "#C2185B"),
    ("Sapphire", "#0D47A1"),
    ("Chartreuse", "#7CB342"),
    ("Coral", "#FF7043"),
    ("Slate", "#546E7A"),
    ("Ivory", "#F5F5DC"),
    ("Maroon", "#6D1B1B"),
    ("Turquoise", "#00ACC1"),
    ("Bronze", "#8D6E63"),
    ("Onyx", "#000000"),
]
"""
Faction colors with names. 24 total colors to support MAX_PLAYERS.
Colors are assigned in order when players join a game.
Each tuple is (color_name, hex_code).
"""

FACTION_COLOR_HEX_CODES: List[str] = [color[1] for color in FACTION_COLORS]
"""List of faction color hex codes only (for quick lookup by index)."""

FACTION_COLOR_NAMES: List[str] = [color[0] for color in FACTION_COLORS]
"""List of faction color names only (for display)."""


def get_faction_color(player_index: int) -> str:
    """
    Get faction color hex code for a player by their join order index.
    
    Args:
        player_index: 0-based index of player join order
        
    Returns:
        Hex color code (e.g., "#D32F2F")
    """
    return FACTION_COLOR_HEX_CODES[player_index % len(FACTION_COLOR_HEX_CODES)]


def get_faction_color_name(player_index: int) -> str:
    """
    Get faction color name for a player by their join order index.
    
    Args:
        player_index: 0-based index of player join order
        
    Returns:
        Color name (e.g., "Crimson")
    """
    return FACTION_COLOR_NAMES[player_index % len(FACTION_COLOR_NAMES)]

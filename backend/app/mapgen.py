"""
Map generation for Galactic Conquest MVP.

This module provides map configuration validation, geometry derivation,
and (in future tasks) system/fleet/population generation.

Invariants (repeated per project constitution):
- Determinism: all functions in this module are pure and deterministic.
- Grid: global axial (q, r) coordinates only. No offset coords.
- No floats: all values are integers.
- No schema changes: uses existing ORM models only.

Created: Milestone A1b Task 1 (Map Config Contract + Derived Geometry)
"""

from typing import Any, Dict

# Use typing_extensions for Python 3.11+ TypedDict features if needed
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from .constants import (
    SEXTANT_SIZE,
    MAP_SIZE_MIN_SEXTANTS,
    MAP_SIZE_MAX_SEXTANTS,
)


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class MapConfig(TypedDict, total=False):
    """
    Validated map configuration.
    
    Required fields:
        map_sextants_w: Width of map in sextants (number of sextant columns).
        map_sextants_h: Height of map in sextants (number of sextant rows).
    
    Optional fields (future-proofing, not required yet):
        system_count_overrides: Per-class system count overrides.
    
    Constraints:
        - map_sextants_w in [MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS]
        - map_sextants_h in [MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS]
    """
    map_sextants_w: int
    map_sextants_h: int
    # Future: system_count_overrides: Dict[str, Any]


class MapGeometry(TypedDict):
    """
    Derived map geometry computed from MapConfig.
    
    This is a pure derivation with no randomness.
    
    Fields:
        sextants_w: Width in sextants (from config).
        sextants_h: Height in sextants (from config).
        sextant_size: Size of each sextant in hexes (from constants).
        min_q: Minimum valid q coordinate (inclusive).
        max_q: Maximum valid q coordinate (inclusive).
        min_r: Minimum valid r coordinate (inclusive).
        max_r: Maximum valid r coordinate (inclusive).
    
    Bounds Guarantee:
        The (min_q, max_q, min_r, max_r) bounds define a conservative rectangular
        region in global axial coordinates that contains all valid hex positions
        for system/fleet placement. Any hex with:
            min_q <= q <= max_q AND min_r <= r <= max_r
        is considered within the map boundary.
    
    Bounds Do NOT Guarantee:
        - Hex-shape exactness: This is a rectangular bounding box, not a hexagonal
          region. Some corner hexes may be geometrically outside the "true" hex map
          shape, but we use rectangular bounds for simplicity.
        - Sextant membership: A hex within bounds may straddle sextant boundaries;
          use sextant conversion functions for exact membership.
    """
    sextants_w: int
    sextants_h: int
    sextant_size: int
    min_q: int
    max_q: int
    min_r: int
    max_r: int


# =============================================================================
# VALIDATION
# =============================================================================

def validate_map_config(map_config: Dict[str, Any]) -> MapConfig:
    """
    Validate and normalize a map configuration dictionary.
    
    This function ensures the input config meets all requirements for map
    generation. It is pure and deterministic (no RNG, no side effects).
    
    Args:
        map_config: Raw configuration dictionary, typically from JSON.
    
    Returns:
        Validated MapConfig with only recognized fields.
    
    Raises:
        ValueError: If validation fails. Message pinpoints the offending key/value.
    
    Invariants:
        - Pure function: no side effects, no randomness.
        - No floats: all validated values are integers.
    """
    # Validate map_sextants_w
    if "map_sextants_w" not in map_config:
        raise ValueError("map_config missing required key: 'map_sextants_w'")
    
    sextants_w = map_config["map_sextants_w"]
    
    if not isinstance(sextants_w, int):
        raise ValueError(
            f"map_config['map_sextants_w'] must be int, got {type(sextants_w).__name__}: {sextants_w!r}"
        )
    
    if sextants_w < MAP_SIZE_MIN_SEXTANTS:
        raise ValueError(
            f"map_config['map_sextants_w'] must be >= {MAP_SIZE_MIN_SEXTANTS}, got {sextants_w}"
        )
    
    if sextants_w > MAP_SIZE_MAX_SEXTANTS:
        raise ValueError(
            f"map_config['map_sextants_w'] must be <= {MAP_SIZE_MAX_SEXTANTS}, got {sextants_w}"
        )
    
    # Validate map_sextants_h
    if "map_sextants_h" not in map_config:
        raise ValueError("map_config missing required key: 'map_sextants_h'")
    
    sextants_h = map_config["map_sextants_h"]
    
    if not isinstance(sextants_h, int):
        raise ValueError(
            f"map_config['map_sextants_h'] must be int, got {type(sextants_h).__name__}: {sextants_h!r}"
        )
    
    if sextants_h < MAP_SIZE_MIN_SEXTANTS:
        raise ValueError(
            f"map_config['map_sextants_h'] must be >= {MAP_SIZE_MIN_SEXTANTS}, got {sextants_h}"
        )
    
    if sextants_h > MAP_SIZE_MAX_SEXTANTS:
        raise ValueError(
            f"map_config['map_sextants_h'] must be <= {MAP_SIZE_MAX_SEXTANTS}, got {sextants_h}"
        )
    
    # Return normalized config with only validated fields
    # Unknown keys are ignored (forward compatibility)
    result: MapConfig = {
        "map_sextants_w": sextants_w,
        "map_sextants_h": sextants_h,
    }
    
    return result


# =============================================================================
# GEOMETRY DERIVATION
# =============================================================================

def derive_map_geometry(map_config: MapConfig) -> MapGeometry:
    """
    Compute derived map geometry from a validated configuration.
    
    This function calculates the global coordinate bounds and other geometry
    parameters needed for map generation. It is pure and deterministic.
    
    Args:
        map_config: Validated MapConfig (call validate_map_config first).
    
    Returns:
        MapGeometry with all derived fields populated.
    
    Bounds Calculation:
        Given W sextants wide and H sextants tall, with SEXTANT_SIZE hexes per side:
        - min_q = 0
        - max_q = W * SEXTANT_SIZE - 1  (inclusive)
        - min_r = 0
        - max_r = H * SEXTANT_SIZE - 1  (inclusive)
        
        Example: 2x2 sextants with SEXTANT_SIZE=20:
        - q range: 0 to 39 (40 hexes wide)
        - r range: 0 to 39 (40 hexes tall)
    
    Invariants:
        - Pure function: no side effects, no randomness.
        - No floats: all values are integers.
        - Global axial (q, r) only.
    """
    sextants_w: int = map_config["map_sextants_w"]
    sextants_h: int = map_config["map_sextants_h"]
    
    # Compute inclusive bounds
    # Each sextant is SEXTANT_SIZE x SEXTANT_SIZE hexes
    # Total width in hexes = sextants_w * SEXTANT_SIZE
    # Valid q range: 0 to (total_width - 1) inclusive
    max_q: int = sextants_w * SEXTANT_SIZE - 1
    max_r: int = sextants_h * SEXTANT_SIZE - 1
    
    result: MapGeometry = {
        "sextants_w": sextants_w,
        "sextants_h": sextants_h,
        "sextant_size": SEXTANT_SIZE,
        "min_q": 0,
        "max_q": max_q,
        "min_r": 0,
        "max_r": max_r,
    }
    
    return result


# =============================================================================
# HELPER FUNCTIONS (for future tasks)
# =============================================================================

def is_hex_in_bounds(q: int, r: int, geometry: MapGeometry) -> bool:
    """
    Check if a hex coordinate is within map bounds.
    
    Args:
        q: Hex q coordinate.
        r: Hex r coordinate.
        geometry: Map geometry with bounds.
    
    Returns:
        True if (q, r) is within bounds (inclusive), False otherwise.
    
    Invariants:
        - Pure function.
        - No floats.
    """
    return (
        geometry["min_q"] <= q <= geometry["max_q"]
        and geometry["min_r"] <= r <= geometry["max_r"]
    )


def get_sextant_coords(q: int, r: int) -> tuple[int, int]:
    """
    Get the sextant coordinates for a global hex position.
    
    Args:
        q: Global hex q coordinate.
        r: Global hex r coordinate.
    
    Returns:
        Tuple of (sextant_q, sextant_r).
    
    Invariants:
        - Pure function.
        - No floats (uses integer division).
    """
    sextant_q = q // SEXTANT_SIZE
    sextant_r = r // SEXTANT_SIZE
    return (sextant_q, sextant_r)


def get_local_coords(q: int, r: int) -> tuple[int, int]:
    """
    Get the local coordinates within a sextant for a global hex position.
    
    Args:
        q: Global hex q coordinate.
        r: Global hex r coordinate.
    
    Returns:
        Tuple of (local_q, local_r) within the sextant (0 to SEXTANT_SIZE-1).
    
    Invariants:
        - Pure function.
        - No floats.
    """
    local_q = q % SEXTANT_SIZE
    local_r = r % SEXTANT_SIZE
    return (local_q, local_r)


def global_from_sextant_local(
    sextant_q: int, sextant_r: int, local_q: int, local_r: int
) -> tuple[int, int]:
    """
    Convert sextant + local coordinates to global hex coordinates.
    
    Args:
        sextant_q: Sextant q coordinate.
        sextant_r: Sextant r coordinate.
        local_q: Local q coordinate within sextant (0 to SEXTANT_SIZE-1).
        local_r: Local r coordinate within sextant (0 to SEXTANT_SIZE-1).
    
    Returns:
        Tuple of (global_q, global_r).
    
    Invariants:
        - Pure function.
        - No floats.
    """
    global_q = sextant_q * SEXTANT_SIZE + local_q
    global_r = sextant_r * SEXTANT_SIZE + local_r
    return (global_q, global_r)

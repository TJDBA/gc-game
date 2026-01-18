"""
Hex grid utilities for Galactic Conquest MVP.

This module provides:
- Hex: Immutable dataclass for axial hex coordinates
- MapBounds: Rectangular bounds for the game map
- Utility functions: distance, neighbors, ring generation

Coordinate System:
- Global axial coordinates (q, r) across the whole map
- Sextants are 20x20 logical groupings (not separate coordinate systems)
- q increases East, r increases Southeast
- Third axis s = -q - r (implicit, used in distance calculation)

Design Principles:
- Clarity over micro-optimization (no caching)
- Clean APIs for future Godot client mirroring
- Bounds-aware helpers for map edge handling

Created: Step 4 of Milestone A1 (Schema + Map Generation)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from .constants import SEXTANT_SIZE, AXIAL_DIRECTIONS


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass(frozen=True, slots=True)
class Hex:
    """
    Immutable hex coordinate in global axial (q, r) space.
    
    Sextant membership is computed on-demand from coordinates.
    No redundant state is stored.
    
    Attributes:
        q: Axial q coordinate (increases East)
        r: Axial r coordinate (increases Southeast)
    
    Properties:
        sextant_q: Q coordinate of containing sextant
        sextant_r: R coordinate of containing sextant
        local_q: Q position within sextant (0 to SEXTANT_SIZE-1)
        local_r: R position within sextant (0 to SEXTANT_SIZE-1)
    """
    q: int
    r: int
    
    @property
    def sextant_q(self) -> int:
        """Q coordinate of the sextant containing this hex."""
        return self.q // SEXTANT_SIZE
    
    @property
    def sextant_r(self) -> int:
        """R coordinate of the sextant containing this hex."""
        return self.r // SEXTANT_SIZE
    
    @property
    def local_q(self) -> int:
        """Q coordinate within the sextant (0 to SEXTANT_SIZE-1)."""
        return self.q % SEXTANT_SIZE
    
    @property
    def local_r(self) -> int:
        """R coordinate within the sextant (0 to SEXTANT_SIZE-1)."""
        return self.r % SEXTANT_SIZE
    
    def to_tuple(self) -> tuple[int, int]:
        """Return coordinates as a (q, r) tuple."""
        return (self.q, self.r)
    
    def __repr__(self) -> str:
        """Readable string representation."""
        return f"Hex({self.q}, {self.r})"


@dataclass(frozen=True, slots=True)
class MapBounds:
    """
    Rectangular bounds for the game map, derived from sextant grid dimensions.
    
    The map spans from (0, 0) to (q_max, r_max) inclusive.
    All hexes outside this rectangle are considered out of bounds.
    
    Attributes:
        sextants_w: Number of sextants in q direction (width)
        sextants_h: Number of sextants in r direction (height)
    
    Properties:
        q_min: Minimum q coordinate (always 0)
        r_min: Minimum r coordinate (always 0)
        q_max: Maximum q coordinate (inclusive)
        r_max: Maximum r coordinate (inclusive)
    """
    sextants_w: int
    sextants_h: int
    
    @property
    def q_min(self) -> int:
        """Minimum q coordinate (always 0)."""
        return 0
    
    @property
    def r_min(self) -> int:
        """Minimum r coordinate (always 0)."""
        return 0
    
    @property
    def q_max(self) -> int:
        """Maximum q coordinate (inclusive)."""
        return self.sextants_w * SEXTANT_SIZE - 1
    
    @property
    def r_max(self) -> int:
        """Maximum r coordinate (inclusive)."""
        return self.sextants_h * SEXTANT_SIZE - 1
    
    def contains(self, q: int, r: int) -> bool:
        """
        Check if coordinates are within bounds.
        
        Args:
            q: Q coordinate to check
            r: R coordinate to check
            
        Returns:
            True if (q, r) is within the map bounds
        """
        return (self.q_min <= q <= self.q_max and 
                self.r_min <= r <= self.r_max)
    
    def __repr__(self) -> str:
        """Readable string representation."""
        return f"MapBounds({self.sextants_w}x{self.sextants_h}, q=0..{self.q_max}, r=0..{self.r_max})"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def axial_distance(a: Hex, b: Hex) -> int:
    """
    Calculate the distance between two hexes in axial coordinates.
    
    Uses the formula: max(|dq|, |dr|, |dq + dr|)
    
    This is mathematically equivalent to (|dq| + |dr| + |ds|) / 2 
    where s = -q - r (the implicit third cube coordinate).
    
    Args:
        a: First hex
        b: Second hex
        
    Returns:
        Number of hex steps between a and b (always >= 0)
    
    Examples:
        >>> axial_distance(Hex(0, 0), Hex(0, 0))
        0
        >>> axial_distance(Hex(0, 0), Hex(1, 0))
        1
        >>> axial_distance(Hex(0, 0), Hex(2, -1))
        2
    """
    dq = a.q - b.q
    dr = a.r - b.r
    return max(abs(dq), abs(dr), abs(dq + dr))


def in_bounds(h: Hex, bounds: MapBounds) -> bool:
    """
    Check if a hex is within the map bounds.
    
    Args:
        h: Hex to check
        bounds: Map bounds to check against
        
    Returns:
        True if hex coordinates are within bounds
    """
    return bounds.contains(h.q, h.r)


def neighbors(h: Hex, bounds: Optional[MapBounds] = None) -> List[Hex]:
    """
    Get all neighbors of a hex.
    
    Neighbors are the 6 hexes adjacent to h, in the order defined
    by AXIAL_DIRECTIONS: E, NE, NW, W, SW, SE.
    
    Args:
        h: Center hex
        bounds: If provided, filters out-of-bounds neighbors
        
    Returns:
        List of neighboring hexes (up to 6, fewer if bounds filtering applied)
    
    Examples:
        >>> len(neighbors(Hex(10, 10)))  # Center of map, no bounds
        6
        >>> len(neighbors(Hex(0, 0), MapBounds(2, 2)))  # Corner, bounded
        2
    """
    result = []
    for dq, dr in AXIAL_DIRECTIONS:
        neighbor = Hex(h.q + dq, h.r + dr)
        if bounds is None or in_bounds(neighbor, bounds):
            result.append(neighbor)
    return result


def ring(center: Hex, radius: int, bounds: Optional[MapBounds] = None) -> List[Hex]:
    """
    Get all hexes at exactly the specified distance from center.
    
    This generates the "ring" of hexes around the center at a given radius.
    The ring is traversed in a consistent clockwise order starting from
    the southwest corner.
    
    Args:
        center: Center hex of the ring
        radius: Distance from center (must be >= 0)
        bounds: If provided, filters out-of-bounds hexes
        
    Returns:
        List of hexes forming the ring:
        - radius 0: [center] if in bounds, else []
        - radius > 0: up to 6*radius hexes (fewer with bounds filtering)
        - radius < 0: [] (empty list)
    
    Algorithm:
        1. Start at center + direction[4] * radius (southwest corner)
        2. Walk around the ring using all 6 directions in order
        3. Each direction is walked for `radius` steps
    
    Examples:
        >>> len(ring(Hex(10, 10), 0))
        1
        >>> len(ring(Hex(10, 10), 1))
        6
        >>> len(ring(Hex(10, 10), 2))
        12
    """
    if radius < 0:
        return []
    
    if radius == 0:
        if bounds is None or in_bounds(center, bounds):
            return [center]
        return []
    
    result = []
    
    # Start at the hex that is `radius` steps in direction[4] from center
    # direction[4] = (-1, 1), so we start at (center.q - radius, center.r + radius)
    start_dq, start_dr = AXIAL_DIRECTIONS[4]
    current = Hex(
        center.q + start_dq * radius,
        center.r + start_dr * radius
    )
    
    # Walk around the ring using all 6 directions
    # Each direction is walked for `radius` steps
    for i in range(6):
        dq, dr = AXIAL_DIRECTIONS[i]
        for _ in range(radius):
            if bounds is None or in_bounds(current, bounds):
                result.append(current)
            current = Hex(current.q + dq, current.r + dr)
    
    return result


def hexes_in_range(center: Hex, radius: int, bounds: Optional[MapBounds] = None) -> List[Hex]:
    """
    Get all hexes within the specified distance from center (inclusive).
    
    This returns all hexes at distance 0, 1, 2, ... up to radius.
    Equivalent to the union of ring(center, r) for r in 0..radius.
    
    Args:
        center: Center hex
        radius: Maximum distance from center (must be >= 0)
        bounds: If provided, filters out-of-bounds hexes
        
    Returns:
        List of all hexes within radius distance from center.
        - radius 0: [center] if in bounds
        - radius r: 1 + 6*(1 + 2 + ... + r) = 1 + 3*r*(r+1) hexes (before filtering)
        - radius < 0: []
    
    Examples:
        >>> len(hexes_in_range(Hex(10, 10), 0))  # Just center
        1
        >>> len(hexes_in_range(Hex(10, 10), 1))  # Center + 6 neighbors
        7
        >>> len(hexes_in_range(Hex(10, 10), 2))  # 1 + 6 + 12
        19
    """
    if radius < 0:
        return []
    
    result = []
    for r in range(radius + 1):
        result.extend(ring(center, r, bounds))
    return result


def hex_from_sextant_local(sextant_q: int, sextant_r: int, 
                           local_q: int, local_r: int) -> Hex:
    """
    Create a Hex from sextant and local coordinates.
    
    This is the inverse of the Hex.sextant_q/r and local_q/r properties.
    
    Args:
        sextant_q: Sextant Q coordinate
        sextant_r: Sextant R coordinate
        local_q: Local Q within sextant (0 to SEXTANT_SIZE-1)
        local_r: Local R within sextant (0 to SEXTANT_SIZE-1)
        
    Returns:
        Hex at the global position
    
    Examples:
        >>> h = hex_from_sextant_local(1, 2, 5, 10)
        >>> h.q
        25
        >>> h.r
        50
        >>> h.sextant_q
        1
        >>> h.sextant_r
        2
    """
    return Hex(
        sextant_q * SEXTANT_SIZE + local_q,
        sextant_r * SEXTANT_SIZE + local_r
    )


def sextant_center(sextant_q: int, sextant_r: int) -> Hex:
    """
    Get the center hex of a sextant.
    
    The center is at local coordinates (SEXTANT_SIZE // 2, SEXTANT_SIZE // 2).
    For SEXTANT_SIZE = 20, this is local (10, 10).
    
    Args:
        sextant_q: Sextant Q coordinate
        sextant_r: Sextant R coordinate
        
    Returns:
        Hex at the center of the sextant
    
    Examples:
        >>> h = sextant_center(0, 0)
        >>> h.to_tuple()
        (10, 10)
        >>> h = sextant_center(1, 1)
        >>> h.to_tuple()
        (30, 30)
    """
    center_offset = SEXTANT_SIZE // 2
    return Hex(
        sextant_q * SEXTANT_SIZE + center_offset,
        sextant_r * SEXTANT_SIZE + center_offset
    )


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_hex_in_bounds(h: Hex, bounds: MapBounds) -> None:
    """
    Raise ValueError if hex is out of bounds.
    
    Args:
        h: Hex to validate
        bounds: Map bounds to check against
        
    Raises:
        ValueError: If hex is outside the map bounds
    """
    if not in_bounds(h, bounds):
        raise ValueError(
            f"Hex {h} is out of bounds "
            f"(q must be 0..{bounds.q_max}, r must be 0..{bounds.r_max})"
        )


def validate_sextant_in_bounds(sextant_q: int, sextant_r: int, bounds: MapBounds) -> None:
    """
    Raise ValueError if sextant is out of bounds.
    
    Args:
        sextant_q: Sextant Q coordinate
        sextant_r: Sextant R coordinate
        bounds: Map bounds to check against
        
    Raises:
        ValueError: If sextant is outside the map
    """
    if not (0 <= sextant_q < bounds.sextants_w and 0 <= sextant_r < bounds.sextants_h):
        raise ValueError(
            f"Sextant ({sextant_q}, {sextant_r}) is out of bounds "
            f"(must be 0..{bounds.sextants_w - 1}, 0..{bounds.sextants_h - 1})"
        )

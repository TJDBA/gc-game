#!/usr/bin/env python3
"""
Smoke test for hex_utils module (Step 4 of Milestone A1).

This script validates that the hex utilities module:
1. Imports correctly
2. Uses constants from Step 3
3. Core functions produce expected results

Run with:
    docker exec -i gc_backend python - < backend/tests/smoke_hex_utils_gc_mvp_004.py

Or:
    docker exec -it gc_backend python /app/tests/smoke_hex_utils_gc_mvp_004.py

Exit codes:
    0 = Success
    1 = Failure
"""

import sys

# Add /app to path for Docker environment
if "/app" not in sys.path:
    sys.path.insert(0, "/app")


def main() -> int:
    """Run smoke tests and return exit code."""
    print("=" * 60)
    print("SMOKE TEST: hex_utils_gc_mvp_004")
    print("=" * 60)
    
    try:
        # Test 1: Import hex_utils module
        print("\nTesting imports...")
        from app.hex_utils import (
            Hex,
            MapBounds,
            axial_distance,
            in_bounds,
            neighbors,
            ring,
            hexes_in_range,
            hex_from_sextant_local,
            sextant_center,
        )
        print("  hex_utils imports OK")
        
        # Test 2: Import constants from Step 3
        from app.constants import SEXTANT_SIZE, AXIAL_DIRECTIONS
        print("  constants imports OK")
        
        # Verify constants values match expected
        assert SEXTANT_SIZE == 20, f"SEXTANT_SIZE should be 20, got {SEXTANT_SIZE}"
        assert len(AXIAL_DIRECTIONS) == 6, f"AXIAL_DIRECTIONS should have 6 elements"
        assert AXIAL_DIRECTIONS[0] == (1, 0), "First direction should be (1, 0) / East"
        print("  constants values OK")
        
        # Test 3: Hex creation and properties
        print("\nTesting Hex dataclass...")
        h = Hex(25, 35)
        assert h.q == 25, "Hex q coordinate"
        assert h.r == 35, "Hex r coordinate"
        assert h.sextant_q == 1, f"Sextant q should be 1, got {h.sextant_q}"
        assert h.sextant_r == 1, f"Sextant r should be 1, got {h.sextant_r}"
        assert h.local_q == 5, f"Local q should be 5, got {h.local_q}"
        assert h.local_r == 15, f"Local r should be 15, got {h.local_r}"
        assert h.to_tuple() == (25, 35), "to_tuple method"
        print("  Hex dataclass OK")
        
        # Test 4: MapBounds
        print("\nTesting MapBounds...")
        bounds = MapBounds(2, 3)
        assert bounds.q_min == 0, "q_min should be 0"
        assert bounds.r_min == 0, "r_min should be 0"
        assert bounds.q_max == 39, f"q_max should be 39, got {bounds.q_max}"
        assert bounds.r_max == 59, f"r_max should be 59, got {bounds.r_max}"
        assert bounds.contains(0, 0) is True, "origin should be in bounds"
        assert bounds.contains(39, 59) is True, "max corner should be in bounds"
        assert bounds.contains(40, 0) is False, "outside q should be out of bounds"
        assert bounds.contains(-1, 0) is False, "negative q should be out of bounds"
        print("  MapBounds OK")
        
        # Test 5: Distance calculations
        print("\nTesting axial_distance...")
        origin = Hex(0, 0)
        assert axial_distance(origin, origin) == 0, "distance to self is 0"
        assert axial_distance(origin, Hex(1, 0)) == 1, "distance to neighbor is 1"
        assert axial_distance(origin, Hex(2, 0)) == 2, "distance 2 along q"
        assert axial_distance(origin, Hex(1, 1)) == 2, "distance 2 diagonal"
        assert axial_distance(origin, Hex(-2, 1)) == 2, "distance 2 mixed"
        # Verify formula: max(|dq|, |dr|, |dq+dr|)
        h1 = Hex(5, 10)
        h2 = Hex(12, 3)
        dq, dr = 5 - 12, 10 - 3
        expected = max(abs(dq), abs(dr), abs(dq + dr))
        assert axial_distance(h1, h2) == expected, "formula verification"
        print("  axial_distance OK")
        
        # Test 6: Neighbors
        print("\nTesting neighbors...")
        center = Hex(10, 10)
        ns = neighbors(center)
        assert len(ns) == 6, f"unbounded center has 6 neighbors, got {len(ns)}"
        for n in ns:
            d = axial_distance(center, n)
            assert d == 1, f"neighbor at distance {d}, expected 1"
        
        # Test bounded neighbors
        bounds2x2 = MapBounds(2, 2)
        corner_ns = neighbors(Hex(0, 0), bounds2x2)
        assert len(corner_ns) < 6, "corner should have fewer than 6 neighbors when bounded"
        assert all(in_bounds(n, bounds2x2) for n in corner_ns), "all bounded neighbors in bounds"
        print("  neighbors OK")
        
        # Test 7: Ring generation
        print("\nTesting ring...")
        assert ring(center, 0) == [center], "ring radius 0 is [center]"
        assert ring(center, -1) == [], "ring negative radius is []"
        
        ring1 = ring(center, 1)
        assert len(ring1) == 6, f"ring radius 1 has 6 hexes, got {len(ring1)}"
        assert all(axial_distance(center, h) == 1 for h in ring1), "all ring1 at distance 1"
        
        ring2 = ring(center, 2)
        assert len(ring2) == 12, f"ring radius 2 has 12 hexes, got {len(ring2)}"
        assert all(axial_distance(center, h) == 2 for h in ring2), "all ring2 at distance 2"
        
        ring3 = ring(center, 3)
        assert len(ring3) == 18, f"ring radius 3 has 18 hexes, got {len(ring3)}"
        
        # Test bounded ring
        corner_ring = ring(Hex(0, 0), 1, bounds2x2)
        assert len(corner_ring) < 6, "corner ring should be filtered"
        assert all(in_bounds(h, bounds2x2) for h in corner_ring), "bounded ring all in bounds"
        print("  ring OK")
        
        # Test 8: hexes_in_range
        print("\nTesting hexes_in_range...")
        assert len(hexes_in_range(center, 0)) == 1, "range 0 = 1 hex"
        assert len(hexes_in_range(center, 1)) == 7, "range 1 = 7 hexes"
        assert len(hexes_in_range(center, 2)) == 19, "range 2 = 19 hexes"
        
        # Formula: 1 + 3*r*(r+1)
        for r in range(5):
            expected_count = 1 + 3 * r * (r + 1)
            actual = len(hexes_in_range(center, r))
            assert actual == expected_count, f"range {r}: expected {expected_count}, got {actual}"
        print("  hexes_in_range OK")
        
        # Test 9: Sextant helpers
        print("\nTesting sextant helpers...")
        reconstructed = hex_from_sextant_local(1, 2, 5, 10)
        assert reconstructed.q == 25, f"hex_from_sextant_local q: expected 25, got {reconstructed.q}"
        assert reconstructed.r == 50, f"hex_from_sextant_local r: expected 50, got {reconstructed.r}"
        
        sc = sextant_center(0, 0)
        assert sc.q == 10, f"sextant_center q: expected 10, got {sc.q}"
        assert sc.r == 10, f"sextant_center r: expected 10, got {sc.r}"
        print("  sextant helpers OK")
        
        # Test 10: in_bounds function
        print("\nTesting in_bounds...")
        assert in_bounds(Hex(10, 10), bounds2x2) is True, "inside returns True"
        assert in_bounds(Hex(-1, 0), bounds2x2) is False, "outside returns False"
        print("  in_bounds OK")
        
        print("\n" + "=" * 60)
        print("SMOKE OK - All hex_utils tests passed")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n** ASSERTION FAILED: {e}")
        return 1
    except ImportError as e:
        print(f"\n** IMPORT ERROR: {e}")
        return 1
    except Exception as e:
        print(f"\n** UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

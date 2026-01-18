"""
Plain-Python unit-style tests for Step 4 Hex Utilities (gc_mvp_004).

This file intentionally does NOT use pytest so it can run inside the existing
gc_backend container without adding new dependencies.

Run:
  docker exec -i gc_backend python - < backend/tests/test_hex_utils_gc_mvp_004.py
"""

from __future__ import annotations

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
    validate_hex_in_bounds,
    validate_sextant_in_bounds,
)


def _assert_raises(exc_type, fn, *args, **kwargs) -> None:
    """Minimal replacement for pytest.raises."""
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    except Exception as e:  # wrong exception
        raise AssertionError(f"Expected {exc_type.__name__}, got {type(e).__name__}: {e}") from e
    raise AssertionError(f"Expected {exc_type.__name__} to be raised, but no exception occurred")


def test_hex_dataclass_and_properties() -> None:
    h = Hex(21, 42)

    # Frozen: should not allow mutation
    try:
        h.q = 999  # type: ignore[attr-defined]
        raise AssertionError("Expected AttributeError when mutating frozen Hex")
    except AttributeError:
        pass

    assert h.to_tuple() == (21, 42)

    # Sextant/local properties (SEXTANT_SIZE=20 assumed via module/constants)
    assert h.sextant_q == 1
    assert h.sextant_r == 2
    assert h.local_q == 1
    assert h.local_r == 2


def test_map_bounds_derived_limits_and_contains() -> None:
    b = MapBounds(sextants_w=2, sextants_h=2)  # q/r in [0..39]
    assert b.q_min == 0 and b.r_min == 0
    assert b.q_max == 39 and b.r_max == 39

    assert b.contains(0, 0) is True
    assert b.contains(39, 39) is True
    assert b.contains(40, 0) is False
    assert b.contains(0, 40) is False
    assert b.contains(-1, 0) is False
    assert b.contains(0, -1) is False


def test_in_bounds_helper() -> None:
    b = MapBounds(sextants_w=2, sextants_h=2)
    assert in_bounds(Hex(0, 0), b) is True
    assert in_bounds(Hex(39, 39), b) is True
    assert in_bounds(Hex(40, 0), b) is False
    assert in_bounds(Hex(0, 40), b) is False


def test_validate_hex_in_bounds() -> None:
    b = MapBounds(sextants_w=2, sextants_h=2)
    validate_hex_in_bounds(Hex(0, 0), b)
    validate_hex_in_bounds(Hex(39, 39), b)
    _assert_raises(ValueError, validate_hex_in_bounds, Hex(-1, 0), b)
    _assert_raises(ValueError, validate_hex_in_bounds, Hex(0, -1), b)
    _assert_raises(ValueError, validate_hex_in_bounds, Hex(40, 0), b)
    _assert_raises(ValueError, validate_hex_in_bounds, Hex(0, 40), b)


def test_validate_sextant_in_bounds() -> None:
    b = MapBounds(sextants_w=2, sextants_h=2)
    validate_sextant_in_bounds(0, 0, b)
    validate_sextant_in_bounds(1, 1, b)
    _assert_raises(ValueError, validate_sextant_in_bounds, -1, 0, b)
    _assert_raises(ValueError, validate_sextant_in_bounds, 0, -1, b)
    _assert_raises(ValueError, validate_sextant_in_bounds, 2, 0, b)
    _assert_raises(ValueError, validate_sextant_in_bounds, 0, 2, b)


def test_axial_distance_examples() -> None:
    a = Hex(0, 0)
    assert axial_distance(a, a) == 0

    # One-step neighbors are distance 1
    assert axial_distance(a, Hex(1, 0)) == 1
    assert axial_distance(a, Hex(1, -1)) == 1
    assert axial_distance(a, Hex(0, -1)) == 1
    assert axial_distance(a, Hex(-1, 0)) == 1
    assert axial_distance(a, Hex(-1, 1)) == 1
    assert axial_distance(a, Hex(0, 1)) == 1

    # A few known axial distances
    assert axial_distance(Hex(0, 0), Hex(2, 0)) == 2
    assert axial_distance(Hex(0, 0), Hex(2, -2)) == 2
    assert axial_distance(Hex(5, 5), Hex(8, 3)) == 3  # dq=-3, dr=2, dq+dr=-1 -> max=3


def test_neighbors_unbounded_count() -> None:
    h = Hex(10, 10)
    ns = neighbors(h, bounds=None)
    assert len(ns) == 6
    assert all(isinstance(x, Hex) for x in ns)


def test_neighbors_bounded_counts() -> None:
    b = MapBounds(sextants_w=2, sextants_h=2)  # q/r in [0..39]

    center = Hex(10, 10)
    assert len(neighbors(center, b)) == 6

    edge = Hex(0, 10)
    # On left edge, neighbors that go to q=-1 should be filtered.
    assert len(neighbors(edge, b)) < 6
    assert all(in_bounds(n, b) for n in neighbors(edge, b))

    corner = Hex(0, 0)
    assert len(neighbors(corner, b)) < len(neighbors(edge, b))
    assert all(in_bounds(n, b) for n in neighbors(corner, b))


def test_ring_radius_zero() -> None:
    b = MapBounds(sextants_w=2, sextants_h=2)
    c = Hex(10, 10)
    r0 = ring(c, 0, bounds=None)
    assert r0 == [c]

    r0b = ring(c, 0, bounds=b)
    assert r0b == [c]


def test_ring_size_unbounded_small_radii() -> None:
    c = Hex(10, 10)
    for rad in (1, 2, 3):
        cells = ring(c, rad, bounds=None)
        # Ring size on hex grid is 6*radius
        assert len(cells) == 6 * rad
        # Every cell returned is exactly at that distance
        assert all(axial_distance(c, h) == rad for h in cells)


def test_ring_bounded_filters_out_of_bounds() -> None:
    b = MapBounds(sextants_w=2, sextants_h=2)  # q/r in [0..39]
    c = Hex(0, 0)
    cells = ring(c, 2, bounds=b)
    # Near corner, many would fall outside and should be filtered
    assert 0 < len(cells) < 12
    assert all(in_bounds(h, b) for h in cells)
    assert all(axial_distance(c, h) == 2 for h in cells)


def test_hexes_in_range_unbounded() -> None:
    c = Hex(10, 10)
    # Range 0 -> 1 cell
    assert hexes_in_range(c, 0, bounds=None) == [c]

    # Range 1 -> 1 + 6 = 7 cells
    r1 = hexes_in_range(c, 1, bounds=None)
    assert len(r1) == 7
    assert c in r1
    assert all(axial_distance(c, h) <= 1 for h in r1)

    # Range 2 -> 1 + 6 + 12 = 19
    r2 = hexes_in_range(c, 2, bounds=None)
    assert len(r2) == 19
    assert all(axial_distance(c, h) <= 2 for h in r2)


def test_hexes_in_range_bounded() -> None:
    b = MapBounds(sextants_w=2, sextants_h=2)
    c = Hex(0, 0)
    r2 = hexes_in_range(c, 2, bounds=b)
    assert all(in_bounds(h, b) for h in r2)
    assert all(axial_distance(c, h) <= 2 for h in r2)


def test_sextant_helpers() -> None:
    b = MapBounds(sextants_w=6, sextants_h=6)

    # local (0,0) in sextant (0,0) -> global (0,0)
    h00 = hex_from_sextant_local(0, 0, 0, 0)
    assert h00 == Hex(0, 0)

    # local (19,19) in sextant (0,0) -> global (19,19)
    h1919 = hex_from_sextant_local(0, 0, 19, 19)
    assert h1919 == Hex(19, 19)

    # sextant (1,2) local (0,0) -> global (20,40)
    h = hex_from_sextant_local(1, 2, 0, 0)
    assert h == Hex(20, 40)

    # sextant center should be within bounds
    sc = sextant_center(1, 2)
    assert sc.sextant_q == 1
    assert sc.sextant_r == 2
    assert in_bounds(sc, b) is True

    # validation: sextant out of bounds
    _assert_raises(ValueError, validate_sextant_in_bounds, 6, 0, b)


def main() -> None:
    # Run all tests in this module (simple explicit runner).
    tests = [
        test_hex_dataclass_and_properties,
        test_map_bounds_derived_limits_and_contains,
        test_in_bounds_helper,
        test_validate_hex_in_bounds,
        test_validate_sextant_in_bounds,
        test_axial_distance_examples,
        test_neighbors_unbounded_count,
        test_neighbors_bounded_counts,
        test_ring_radius_zero,
        test_ring_size_unbounded_small_radii,
        test_ring_bounded_filters_out_of_bounds,
        test_hexes_in_range_unbounded,
        test_hexes_in_range_bounded,
        test_sextant_helpers,
    ]

    for t in tests:
        t()

    print("TESTS OK")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Smoke test for mapgen config validation and geometry derivation.

Run via:
    docker exec -i gc_backend python - < backend/tests/smoke_mapgen_config_gc_mvp_001.py

Or if file is copied into container:
    docker exec -it gc_backend python /app/tests/smoke_mapgen_config_gc_mvp_001.py

Exit code 0 = all tests pass
Exit code 1 = test failure

This is a standalone script (no pytest required).
"""

import sys

# Ensure app is importable
sys.path.insert(0, "/app")

from app.mapgen import (
    validate_map_config,
    derive_map_geometry,
    is_hex_in_bounds,
    get_sextant_coords,
    get_local_coords,
    global_from_sextant_local,
    MapConfig,
    MapGeometry,
)
from app.constants import (
    SEXTANT_SIZE,
    MAP_SIZE_MIN_SEXTANTS,
    MAP_SIZE_MAX_SEXTANTS,
)


def test_valid_min_size():
    """Test validation passes for minimum valid sextant sizes."""
    config = {
        "map_sextants_w": MAP_SIZE_MIN_SEXTANTS,
        "map_sextants_h": MAP_SIZE_MIN_SEXTANTS,
    }
    result = validate_map_config(config)
    assert result["map_sextants_w"] == MAP_SIZE_MIN_SEXTANTS, "min width mismatch"
    assert result["map_sextants_h"] == MAP_SIZE_MIN_SEXTANTS, "min height mismatch"
    print("  test_valid_min_size OK")


def test_valid_max_size():
    """Test validation passes for maximum valid sextant sizes."""
    config = {
        "map_sextants_w": MAP_SIZE_MAX_SEXTANTS,
        "map_sextants_h": MAP_SIZE_MAX_SEXTANTS,
    }
    result = validate_map_config(config)
    assert result["map_sextants_w"] == MAP_SIZE_MAX_SEXTANTS, "max width mismatch"
    assert result["map_sextants_h"] == MAP_SIZE_MAX_SEXTANTS, "max height mismatch"
    print("  test_valid_max_size OK")


def test_valid_mixed_sizes():
    """Test validation passes for different w and h values."""
    config = {
        "map_sextants_w": 3,
        "map_sextants_h": 4,
    }
    result = validate_map_config(config)
    assert result["map_sextants_w"] == 3, "mixed width mismatch"
    assert result["map_sextants_h"] == 4, "mixed height mismatch"
    print("  test_valid_mixed_sizes OK")


def test_missing_width_key():
    """Test validation fails with clear error when width key is missing."""
    config = {"map_sextants_h": 2}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for missing width key")
    except ValueError as e:
        assert "map_sextants_w" in str(e), f"Error should mention map_sextants_w: {e}"
        assert "missing" in str(e).lower(), f"Error should say 'missing': {e}"
    print("  test_missing_width_key OK")


def test_missing_height_key():
    """Test validation fails with clear error when height key is missing."""
    config = {"map_sextants_w": 2}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for missing height key")
    except ValueError as e:
        assert "map_sextants_h" in str(e), f"Error should mention map_sextants_h: {e}"
        assert "missing" in str(e).lower(), f"Error should say 'missing': {e}"
    print("  test_missing_height_key OK")


def test_missing_both_keys():
    """Test validation fails when both keys are missing."""
    config = {}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for empty config")
    except ValueError as e:
        # Should fail on first missing key (width)
        assert "map_sextants_w" in str(e), f"Error should mention first missing key: {e}"
    print("  test_missing_both_keys OK")


def test_non_int_width_string():
    """Test validation fails when width is a string."""
    config = {"map_sextants_w": "2", "map_sextants_h": 2}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for string width")
    except ValueError as e:
        assert "map_sextants_w" in str(e), f"Error should mention map_sextants_w: {e}"
        assert "int" in str(e).lower(), f"Error should mention int: {e}"
    print("  test_non_int_width_string OK")


def test_non_int_width_float():
    """Test validation fails when width is a float."""
    config = {"map_sextants_w": 2.5, "map_sextants_h": 2}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for float width")
    except ValueError as e:
        assert "map_sextants_w" in str(e), f"Error should mention map_sextants_w: {e}"
        assert "int" in str(e).lower(), f"Error should mention int: {e}"
    print("  test_non_int_width_float OK")


def test_non_int_height_string():
    """Test validation fails when height is a string."""
    config = {"map_sextants_w": 2, "map_sextants_h": "3"}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for string height")
    except ValueError as e:
        assert "map_sextants_h" in str(e), f"Error should mention map_sextants_h: {e}"
        assert "int" in str(e).lower(), f"Error should mention int: {e}"
    print("  test_non_int_height_string OK")


def test_non_int_height_none():
    """Test validation fails when height is None."""
    config = {"map_sextants_w": 2, "map_sextants_h": None}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for None height")
    except ValueError as e:
        assert "map_sextants_h" in str(e), f"Error should mention map_sextants_h: {e}"
        assert "int" in str(e).lower(), f"Error should mention int: {e}"
    print("  test_non_int_height_none OK")


def test_width_below_min():
    """Test validation fails when width is below minimum."""
    config = {"map_sextants_w": MAP_SIZE_MIN_SEXTANTS - 1, "map_sextants_h": 2}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for width below min")
    except ValueError as e:
        assert "map_sextants_w" in str(e), f"Error should mention map_sextants_w: {e}"
        assert str(MAP_SIZE_MIN_SEXTANTS) in str(e), f"Error should mention min value: {e}"
    print("  test_width_below_min OK")


def test_width_above_max():
    """Test validation fails when width is above maximum."""
    config = {"map_sextants_w": MAP_SIZE_MAX_SEXTANTS + 1, "map_sextants_h": 2}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for width above max")
    except ValueError as e:
        assert "map_sextants_w" in str(e), f"Error should mention map_sextants_w: {e}"
        assert str(MAP_SIZE_MAX_SEXTANTS) in str(e), f"Error should mention max value: {e}"
    print("  test_width_above_max OK")


def test_height_below_min():
    """Test validation fails when height is below minimum."""
    config = {"map_sextants_w": 2, "map_sextants_h": MAP_SIZE_MIN_SEXTANTS - 1}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for height below min")
    except ValueError as e:
        assert "map_sextants_h" in str(e), f"Error should mention map_sextants_h: {e}"
        assert str(MAP_SIZE_MIN_SEXTANTS) in str(e), f"Error should mention min value: {e}"
    print("  test_height_below_min OK")


def test_height_above_max():
    """Test validation fails when height is above maximum."""
    config = {"map_sextants_w": 2, "map_sextants_h": MAP_SIZE_MAX_SEXTANTS + 1}
    try:
        validate_map_config(config)
        raise AssertionError("Expected ValueError for height above max")
    except ValueError as e:
        assert "map_sextants_h" in str(e), f"Error should mention map_sextants_h: {e}"
        assert str(MAP_SIZE_MAX_SEXTANTS) in str(e), f"Error should mention max value: {e}"
    print("  test_height_above_max OK")


def test_unknown_keys_ignored():
    """Test that unknown keys are silently ignored (forward compatibility)."""
    config = {
        "map_sextants_w": 3,
        "map_sextants_h": 3,
        "unknown_future_key": "some_value",
        "another_unknown": 42,
    }
    result = validate_map_config(config)
    assert "unknown_future_key" not in result, "Unknown keys should not be in result"
    assert "another_unknown" not in result, "Unknown keys should not be in result"
    assert result["map_sextants_w"] == 3
    assert result["map_sextants_h"] == 3
    print("  test_unknown_keys_ignored OK")


def test_geometry_sextant_size():
    """Test derived geometry includes correct sextant_size from constants."""
    config: MapConfig = {"map_sextants_w": 2, "map_sextants_h": 2}
    geometry = derive_map_geometry(config)
    assert geometry["sextant_size"] == SEXTANT_SIZE, f"Expected sextant_size={SEXTANT_SIZE}"
    print("  test_geometry_sextant_size OK")


def test_geometry_min_config():
    """Test derived geometry for minimum configuration."""
    config: MapConfig = {
        "map_sextants_w": MAP_SIZE_MIN_SEXTANTS,
        "map_sextants_h": MAP_SIZE_MIN_SEXTANTS,
    }
    geometry = derive_map_geometry(config)
    
    assert geometry["sextants_w"] == MAP_SIZE_MIN_SEXTANTS
    assert geometry["sextants_h"] == MAP_SIZE_MIN_SEXTANTS
    assert geometry["min_q"] == 0
    assert geometry["min_r"] == 0
    
    # For 2x2 sextants with SEXTANT_SIZE=20: max_q = 2*20-1 = 39
    expected_max_q = MAP_SIZE_MIN_SEXTANTS * SEXTANT_SIZE - 1
    expected_max_r = MAP_SIZE_MIN_SEXTANTS * SEXTANT_SIZE - 1
    assert geometry["max_q"] == expected_max_q, f"Expected max_q={expected_max_q}"
    assert geometry["max_r"] == expected_max_r, f"Expected max_r={expected_max_r}"
    print("  test_geometry_min_config OK")


def test_geometry_max_config():
    """Test derived geometry for maximum configuration."""
    config: MapConfig = {
        "map_sextants_w": MAP_SIZE_MAX_SEXTANTS,
        "map_sextants_h": MAP_SIZE_MAX_SEXTANTS,
    }
    geometry = derive_map_geometry(config)
    
    assert geometry["sextants_w"] == MAP_SIZE_MAX_SEXTANTS
    assert geometry["sextants_h"] == MAP_SIZE_MAX_SEXTANTS
    assert geometry["min_q"] == 0
    assert geometry["min_r"] == 0
    
    # For 6x6 sextants with SEXTANT_SIZE=20: max_q = 6*20-1 = 119
    expected_max_q = MAP_SIZE_MAX_SEXTANTS * SEXTANT_SIZE - 1
    expected_max_r = MAP_SIZE_MAX_SEXTANTS * SEXTANT_SIZE - 1
    assert geometry["max_q"] == expected_max_q, f"Expected max_q={expected_max_q}"
    assert geometry["max_r"] == expected_max_r, f"Expected max_r={expected_max_r}"
    print("  test_geometry_max_config OK")


def test_geometry_asymmetric():
    """Test derived geometry for asymmetric configuration."""
    config: MapConfig = {"map_sextants_w": 3, "map_sextants_h": 4}
    geometry = derive_map_geometry(config)
    
    assert geometry["sextants_w"] == 3
    assert geometry["sextants_h"] == 4
    
    # 3 wide: max_q = 3*20-1 = 59
    # 4 tall: max_r = 4*20-1 = 79
    assert geometry["max_q"] == 59, f"Expected max_q=59, got {geometry['max_q']}"
    assert geometry["max_r"] == 79, f"Expected max_r=79, got {geometry['max_r']}"
    print("  test_geometry_asymmetric OK")


def test_geometry_bounds_ordering():
    """Test that derived bounds have correct ordering (min < max)."""
    for w in range(MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS + 1):
        for h in range(MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS + 1):
            config: MapConfig = {"map_sextants_w": w, "map_sextants_h": h}
            geometry = derive_map_geometry(config)
            
            assert geometry["min_q"] < geometry["max_q"], f"min_q >= max_q for {w}x{h}"
            assert geometry["min_r"] < geometry["max_r"], f"min_r >= max_r for {w}x{h}"
    print("  test_geometry_bounds_ordering OK")


def test_geometry_bounds_monotonic():
    """Test that bounds grow monotonically with sextant count."""
    prev_max_q = -1
    for w in range(MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS + 1):
        config: MapConfig = {"map_sextants_w": w, "map_sextants_h": 2}
        geometry = derive_map_geometry(config)
        assert geometry["max_q"] > prev_max_q, f"max_q not monotonic at w={w}"
        prev_max_q = geometry["max_q"]
    
    prev_max_r = -1
    for h in range(MAP_SIZE_MIN_SEXTANTS, MAP_SIZE_MAX_SEXTANTS + 1):
        config: MapConfig = {"map_sextants_w": 2, "map_sextants_h": h}
        geometry = derive_map_geometry(config)
        assert geometry["max_r"] > prev_max_r, f"max_r not monotonic at h={h}"
        prev_max_r = geometry["max_r"]
    print("  test_geometry_bounds_monotonic OK")


def test_is_hex_in_bounds():
    """Test is_hex_in_bounds helper function."""
    config: MapConfig = {"map_sextants_w": 2, "map_sextants_h": 2}
    geometry = derive_map_geometry(config)
    
    # Corners should be in bounds
    assert is_hex_in_bounds(0, 0, geometry), "Origin should be in bounds"
    assert is_hex_in_bounds(39, 0, geometry), "Top-right should be in bounds"
    assert is_hex_in_bounds(0, 39, geometry), "Bottom-left should be in bounds"
    assert is_hex_in_bounds(39, 39, geometry), "Bottom-right should be in bounds"
    
    # Just outside should be out of bounds
    assert not is_hex_in_bounds(-1, 0, geometry), "Negative q should be out"
    assert not is_hex_in_bounds(0, -1, geometry), "Negative r should be out"
    assert not is_hex_in_bounds(40, 0, geometry), "q=40 should be out"
    assert not is_hex_in_bounds(0, 40, geometry), "r=40 should be out"
    print("  test_is_hex_in_bounds OK")


def test_sextant_coords():
    """Test get_sextant_coords helper function."""
    # First sextant (0, 0)
    assert get_sextant_coords(0, 0) == (0, 0)
    assert get_sextant_coords(19, 19) == (0, 0)
    
    # Second column sextant (1, 0)
    assert get_sextant_coords(20, 0) == (1, 0)
    assert get_sextant_coords(39, 19) == (1, 0)
    
    # Second row sextant (0, 1)
    assert get_sextant_coords(0, 20) == (0, 1)
    assert get_sextant_coords(19, 39) == (0, 1)
    
    # Diagonal sextant (1, 1)
    assert get_sextant_coords(20, 20) == (1, 1)
    assert get_sextant_coords(30, 30) == (1, 1)
    print("  test_sextant_coords OK")


def test_local_coords():
    """Test get_local_coords helper function."""
    # Origin of first sextant
    assert get_local_coords(0, 0) == (0, 0)
    
    # End of first sextant
    assert get_local_coords(19, 19) == (19, 19)
    
    # Start of second sextant (column)
    assert get_local_coords(20, 0) == (0, 0)
    
    # Middle of second sextant
    assert get_local_coords(30, 10) == (10, 10)
    print("  test_local_coords OK")


def test_global_from_sextant_local():
    """Test global_from_sextant_local helper function."""
    # First sextant origin
    assert global_from_sextant_local(0, 0, 0, 0) == (0, 0)
    
    # First sextant corner
    assert global_from_sextant_local(0, 0, 19, 19) == (19, 19)
    
    # Second sextant (1, 0) origin
    assert global_from_sextant_local(1, 0, 0, 0) == (20, 0)
    
    # Sextant (1, 1) with local (5, 10)
    assert global_from_sextant_local(1, 1, 5, 10) == (25, 30)
    
    # Roundtrip test
    for sq, sr, lq, lr in [(0, 0, 0, 0), (1, 2, 5, 10), (3, 4, 19, 19)]:
        gq, gr = global_from_sextant_local(sq, sr, lq, lr)
        assert get_sextant_coords(gq, gr) == (sq, sr)
        assert get_local_coords(gq, gr) == (lq, lr)
    print("  test_global_from_sextant_local OK")


def test_no_floats_in_geometry():
    """Test that geometry contains no float values."""
    config: MapConfig = {"map_sextants_w": 3, "map_sextants_h": 4}
    geometry = derive_map_geometry(config)
    
    for key, value in geometry.items():
        assert isinstance(value, int), f"geometry['{key}'] should be int, got {type(value)}"
    print("  test_no_floats_in_geometry OK")


def main():
    print("=" * 60)
    print("SMOKE TEST: smoke_mapgen_config_gc_mvp_001")
    print("=" * 60)
    
    print(f"\nConstants: SEXTANT_SIZE={SEXTANT_SIZE}, "
          f"MIN={MAP_SIZE_MIN_SEXTANTS}, MAX={MAP_SIZE_MAX_SEXTANTS}")
    
    print("\nTesting validate_map_config (valid inputs)...")
    test_valid_min_size()
    test_valid_max_size()
    test_valid_mixed_sizes()
    test_unknown_keys_ignored()
    
    print("\nTesting validate_map_config (missing keys)...")
    test_missing_width_key()
    test_missing_height_key()
    test_missing_both_keys()
    
    print("\nTesting validate_map_config (type errors)...")
    test_non_int_width_string()
    test_non_int_width_float()
    test_non_int_height_string()
    test_non_int_height_none()
    
    print("\nTesting validate_map_config (range errors)...")
    test_width_below_min()
    test_width_above_max()
    test_height_below_min()
    test_height_above_max()
    
    print("\nTesting derive_map_geometry...")
    test_geometry_sextant_size()
    test_geometry_min_config()
    test_geometry_max_config()
    test_geometry_asymmetric()
    test_geometry_bounds_ordering()
    test_geometry_bounds_monotonic()
    test_no_floats_in_geometry()
    
    print("\nTesting helper functions...")
    test_is_hex_in_bounds()
    test_sextant_coords()
    test_local_coords()
    test_global_from_sextant_local()
    
    print("\n" + "=" * 60)
    print("SMOKE OK - All mapgen config tests passed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

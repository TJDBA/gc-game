#!/usr/bin/env python3
"""
Smoke test for mapgen deterministic RNG.

Run via:
    docker exec -i gc_backend python - < backend/tests/smoke_mapgen_rng_gc_mvp_001.py

Or if file is copied into container:
    docker exec -it gc_backend python /app/tests/smoke_mapgen_rng_gc_mvp_001.py

Exit code 0 = all tests pass
Exit code 1 = test failure

This is a standalone script (no pytest required, no database required).
"""

from __future__ import annotations

import sys

# Ensure app is importable
sys.path.insert(0, "/app")

from app.mapgen import (
    normalize_seed_64,
    make_map_rng,
    MapRng,
    _derive_phase_seed,
    _SEED_MAX,
)


def test_normalize_negative_one():
    """Test that normalize_seed_64(-1) returns a valid non-negative value."""
    result = normalize_seed_64(-1)
    assert result >= 0, f"normalize_seed_64(-1) should be non-negative, got {result}"
    assert result < _SEED_MAX, f"normalize_seed_64(-1) should be < 2**63, got {result}"
    # -1 % (2**63) = 2**63 - 1 in Python
    expected = _SEED_MAX - 1
    assert result == expected, f"normalize_seed_64(-1) should be {expected}, got {result}"
    print("  test_normalize_negative_one OK")


def test_normalize_large_positive():
    """Test that very large positive seeds normalize correctly."""
    huge_seed = 2**100 + 42
    result = normalize_seed_64(huge_seed)
    assert result >= 0, f"normalize should return non-negative, got {result}"
    assert result < _SEED_MAX, f"normalize should return < 2**63, got {result}"
    # Verify consistency
    result2 = normalize_seed_64(huge_seed)
    assert result == result2, "normalize should be deterministic"
    print("  test_normalize_large_positive OK")


def test_normalize_large_negative():
    """Test that very large negative seeds normalize correctly."""
    huge_negative = -(2**100 + 42)
    result = normalize_seed_64(huge_negative)
    assert result >= 0, f"normalize should return non-negative, got {result}"
    assert result < _SEED_MAX, f"normalize should return < 2**63, got {result}"
    print("  test_normalize_large_negative OK")


def test_normalize_zero():
    """Test that zero normalizes to zero."""
    result = normalize_seed_64(0)
    assert result == 0, f"normalize_seed_64(0) should be 0, got {result}"
    print("  test_normalize_zero OK")


def test_normalize_max_minus_one():
    """Test boundary value at 2**63 - 1."""
    result = normalize_seed_64(_SEED_MAX - 1)
    assert result == _SEED_MAX - 1, f"Expected {_SEED_MAX - 1}, got {result}"
    print("  test_normalize_max_minus_one OK")


def test_normalize_exact_max():
    """Test that exactly 2**63 wraps to 0."""
    result = normalize_seed_64(_SEED_MAX)
    assert result == 0, f"normalize_seed_64(2**63) should wrap to 0, got {result}"
    print("  test_normalize_exact_max OK")


def test_make_map_rng_normalizes():
    """Test that make_map_rng normalizes the seed."""
    rng1 = make_map_rng(123)
    rng2 = make_map_rng(-1)
    
    assert rng1.root_seed == 123, f"Expected 123, got {rng1.root_seed}"
    assert rng2.root_seed == _SEED_MAX - 1, f"Expected {_SEED_MAX - 1}, got {rng2.root_seed}"
    print("  test_make_map_rng_normalizes OK")


def test_stability_same_seed_same_stream():
    """Test that same seed produces same RNG stream within one run."""
    rng = make_map_rng(123)
    
    # Get first 20 integers from phase_x
    rng_a1 = rng.rng_for("phase_x")
    stream1 = [rng_a1.randint(0, 10000) for _ in range(20)]
    
    # Get another instance for the same phase
    rng_a2 = rng.rng_for("phase_x")
    stream2 = [rng_a2.randint(0, 10000) for _ in range(20)]
    
    assert stream1 == stream2, f"Same phase should produce identical streams:\n  {stream1}\n  {stream2}"
    print("  test_stability_same_seed_same_stream OK")


def test_phase_independence_consume_a_check_b():
    """Test that consuming from phase A doesn't affect phase B."""
    rng = make_map_rng(456)
    
    # First, get the expected stream for phase B without touching A
    rng_b_expected = rng.rng_for("phase_B")
    expected_b = [rng_b_expected.randint(0, 10000) for _ in range(10)]
    
    # Now create a fresh MapRng (same seed) and consume 100 values from A
    rng2 = make_map_rng(456)
    rng_a = rng2.rng_for("phase_A")
    _ = [rng_a.randint(0, 10000) for _ in range(100)]  # Consume from A
    
    # Now get phase B and verify it matches expected
    rng_b_actual = rng2.rng_for("phase_B")
    actual_b = [rng_b_actual.randint(0, 10000) for _ in range(10)]
    
    assert expected_b == actual_b, (
        f"Phase B should be independent of phase A consumption:\n"
        f"  Expected: {expected_b}\n"
        f"  Actual:   {actual_b}"
    )
    print("  test_phase_independence_consume_a_check_b OK")


def test_phase_independence_different_phases_different_streams():
    """Test that different phases produce different streams."""
    rng = make_map_rng(789)
    
    stream_a = [rng.rng_for("phase_A").randint(0, 10000) for _ in range(10)]
    stream_b = [rng.rng_for("phase_B").randint(0, 10000) for _ in range(10)]
    
    # They should be different (extremely unlikely to match by chance)
    assert stream_a != stream_b, f"Different phases should produce different streams"
    print("  test_phase_independence_different_phases_different_streams OK")


def test_repeatability_two_instances():
    """Test that two MapRng instances with same seed produce identical sequences."""
    rng1 = MapRng(root_seed=12345)
    rng2 = MapRng(root_seed=12345)
    
    # Test multiple phases
    for phase in ["home_systems", "non_home_systems", "rp_assignment"]:
        stream1 = [rng1.rng_for(phase).randint(0, 10000) for _ in range(15)]
        stream2 = [rng2.rng_for(phase).randint(0, 10000) for _ in range(15)]
        assert stream1 == stream2, f"Phase {phase} should be identical across instances"
    
    print("  test_repeatability_two_instances OK")


def test_derive_phase_seed_deterministic():
    """Test that _derive_phase_seed is deterministic."""
    seed1 = _derive_phase_seed(999, "test_phase")
    seed2 = _derive_phase_seed(999, "test_phase")
    
    assert seed1 == seed2, f"Phase seed derivation should be deterministic"
    assert seed1 >= 0, "Phase seed should be non-negative"
    assert seed1 < _SEED_MAX, "Phase seed should be < 2**63"
    print("  test_derive_phase_seed_deterministic OK")


def test_derive_phase_seed_different_phases():
    """Test that different phases produce different seeds."""
    seed_a = _derive_phase_seed(999, "phase_a")
    seed_b = _derive_phase_seed(999, "phase_b")
    
    assert seed_a != seed_b, "Different phases should produce different seeds"
    print("  test_derive_phase_seed_different_phases OK")


def test_derive_phase_seed_different_roots():
    """Test that different root seeds produce different phase seeds."""
    seed1 = _derive_phase_seed(111, "same_phase")
    seed2 = _derive_phase_seed(222, "same_phase")
    
    assert seed1 != seed2, "Different root seeds should produce different phase seeds"
    print("  test_derive_phase_seed_different_roots OK")


def test_no_global_state_mutation():
    """Test that RNG operations don't affect global random state."""
    import random
    
    # Set global state to known value
    random.seed(99999)
    expected_global = [random.randint(0, 10000) for _ in range(5)]
    
    # Reset and do MapRng operations
    random.seed(99999)
    rng = make_map_rng(12345)
    _ = rng.rng_for("test").randint(0, 10000)
    _ = rng.rng_for("test2").randint(0, 10000)
    
    # Check global state is unaffected
    actual_global = [random.randint(0, 10000) for _ in range(5)]
    
    assert expected_global == actual_global, (
        f"MapRng should not affect global random state:\n"
        f"  Expected: {expected_global}\n"
        f"  Actual:   {actual_global}"
    )
    print("  test_no_global_state_mutation OK")


def test_rng_for_returns_random_instance():
    """Test that rng_for returns a proper random.Random instance."""
    import random
    
    rng = make_map_rng(42)
    phase_rng = rng.rng_for("test")
    
    assert isinstance(phase_rng, random.Random), f"Expected random.Random, got {type(phase_rng)}"
    
    # Should have standard methods
    _ = phase_rng.randint(0, 100)
    _ = phase_rng.random()
    _ = phase_rng.choice([1, 2, 3])
    _ = phase_rng.shuffle([1, 2, 3])
    
    print("  test_rng_for_returns_random_instance OK")


def test_frozen_dataclass():
    """Test that MapRng is immutable."""
    rng = MapRng(root_seed=123)
    
    try:
        rng.root_seed = 456  # type: ignore
        raise AssertionError("MapRng should be immutable (frozen)")
    except AttributeError:
        pass  # Expected
    
    print("  test_frozen_dataclass OK")


def test_extended_stream_consistency():
    """Test consistency over a longer stream (1000 values)."""
    rng1 = make_map_rng(777)
    rng2 = make_map_rng(777)
    
    phase_rng1 = rng1.rng_for("extended_test")
    phase_rng2 = rng2.rng_for("extended_test")
    
    for i in range(1000):
        v1 = phase_rng1.randint(0, 1000000)
        v2 = phase_rng2.randint(0, 1000000)
        assert v1 == v2, f"Mismatch at position {i}: {v1} != {v2}"
    
    print("  test_extended_stream_consistency OK")


def main():
    print("=" * 60)
    print("SMOKE TEST: smoke_mapgen_rng_gc_mvp_001")
    print("=" * 60)
    
    print(f"\nConstants: _SEED_MAX = 2**63 = {_SEED_MAX}")
    
    print("\nTesting normalize_seed_64...")
    test_normalize_negative_one()
    test_normalize_large_positive()
    test_normalize_large_negative()
    test_normalize_zero()
    test_normalize_max_minus_one()
    test_normalize_exact_max()
    
    print("\nTesting make_map_rng...")
    test_make_map_rng_normalizes()
    
    print("\nTesting stability (same seed = same stream)...")
    test_stability_same_seed_same_stream()
    
    print("\nTesting phase independence...")
    test_phase_independence_consume_a_check_b()
    test_phase_independence_different_phases_different_streams()
    
    print("\nTesting repeatability...")
    test_repeatability_two_instances()
    
    print("\nTesting _derive_phase_seed internals...")
    test_derive_phase_seed_deterministic()
    test_derive_phase_seed_different_phases()
    test_derive_phase_seed_different_roots()
    
    print("\nTesting isolation and types...")
    test_no_global_state_mutation()
    test_rng_for_returns_random_instance()
    test_frozen_dataclass()
    
    print("\nTesting extended consistency...")
    test_extended_stream_consistency()
    
    print("\n" + "=" * 60)
    print("SMOKE OK - All mapgen RNG tests passed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

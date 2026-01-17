#!/usr/bin/env python3
"""
Smoke test for constants module (gc_mvp_003).

Validates:
- Scan math constants and functions match required formulas
- Faction color list has exactly 24 items
- All faction color hex codes are unique and valid format
- Key constants have expected values

Run with:
    docker exec -i gc_backend python - < backend/tests/smoke_constants_gc_mvp_003.py

Or from within container:
    python backend/tests/smoke_constants_gc_mvp_003.py
"""

import re
import sys

# Add app to path if running directly
sys.path.insert(0, '/app')

from app.constants import (
    # Player/Game
    MIN_PLAYERS,
    MAX_PLAYERS,
    JOIN_CODE_LENGTH,
    # Turns
    TURN_NUMBER_START,
    CURRENT_TURN_START,
    DEFAULT_TURN_TIMEOUT_SECONDS,
    # Resources
    STARTING_RP,
    STARTING_POP_TENTHS,
    POP_TENTHS_PER_POP,
    MIN_RP,
    # Tech
    MIN_TECH_LEVEL,
    MAX_TECH_LEVEL,
    STARTING_TECH_LEVEL,
    TECH_COSTS,
    # Scanning
    SCAN_BAND_PRIORITY,
    calc_scan_base,
    calc_long_range,
    calc_medium_range,
    calc_short_range,
    # Ships
    SHIP_STATS,
    STARTING_SHIPS,
    # Systems
    SYSTEM_RP_RANGES,
    SEXTANT_SYSTEM_COUNTS,
    # Control
    CONTROL_MIN_POP_TENTHS,
    CONTROL_RATIO,
    # Map
    SEXTANT_SIZE,
    MAP_SIZE_MIN_SEXTANTS,
    MAP_SIZE_MAX_SEXTANTS,
    AXIAL_DIRECTIONS,
    # API
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    # Colors
    FACTION_COLORS,
    FACTION_COLOR_HEX_CODES,
    FACTION_COLOR_NAMES,
    get_faction_color,
    get_faction_color_name,
)


def test_scan_math():
    """Verify scan math formulas: no +1 anywhere."""
    print("Testing scan math...")
    
    # Test scan_base = scanning_tech (no +1)
    for tech in range(6):
        assert calc_scan_base(tech) == tech, f"scan_base({tech}) should be {tech}"
    
    # Test LONG = scan_base * 2
    for tech in range(6):
        expected = tech * 2
        actual = calc_long_range(tech)
        assert actual == expected, f"long_range({tech}) = {actual}, expected {expected}"
    
    # Test MEDIUM = scan_base
    for tech in range(6):
        expected = tech
        actual = calc_medium_range(tech)
        assert actual == expected, f"medium_range({tech}) = {actual}, expected {expected}"
    
    # Test SHORT = floor(scanning_tech / 2)
    for tech in range(6):
        expected = tech // 2
        actual = calc_short_range(tech)
        assert actual == expected, f"short_range({tech}) = {actual}, expected {expected}"
    
    # At starting tech level 1:
    #   LONG = 2, MEDIUM = 1, SHORT = 0 (same-hex only)
    assert calc_long_range(1) == 2, "At tech 1, LONG should be 2"
    assert calc_medium_range(1) == 1, "At tech 1, MEDIUM should be 1"
    assert calc_short_range(1) == 0, "At tech 1, SHORT should be 0 (same-hex only)"
    
    # Verify band priority ordering: SHORT > MEDIUM > LONG
    assert SCAN_BAND_PRIORITY["SHORT"] > SCAN_BAND_PRIORITY["MEDIUM"], \
        "SHORT should have higher priority than MEDIUM"
    assert SCAN_BAND_PRIORITY["MEDIUM"] > SCAN_BAND_PRIORITY["LONG"], \
        "MEDIUM should have higher priority than LONG"
    
    print("  Scan math OK")


def test_faction_colors():
    """Verify faction colors: exactly 24, all unique, valid hex format."""
    print("Testing faction colors...")
    
    # Must have exactly 24 colors
    assert len(FACTION_COLORS) == 24, \
        f"Expected 24 faction colors, got {len(FACTION_COLORS)}"
    assert len(FACTION_COLOR_HEX_CODES) == 24, \
        f"Expected 24 hex codes, got {len(FACTION_COLOR_HEX_CODES)}"
    assert len(FACTION_COLOR_NAMES) == 24, \
        f"Expected 24 color names, got {len(FACTION_COLOR_NAMES)}"
    
    # All hex codes must be unique
    unique_codes = set(FACTION_COLOR_HEX_CODES)
    assert len(unique_codes) == 24, \
        f"Faction color hex codes not unique: {24 - len(unique_codes)} duplicates"
    
    # All hex codes must be valid format (#RRGGBB)
    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
    for i, code in enumerate(FACTION_COLOR_HEX_CODES):
        assert hex_pattern.match(code), \
            f"Invalid hex format for color {i}: {code}"
    
    # All color names must be unique
    unique_names = set(FACTION_COLOR_NAMES)
    assert len(unique_names) == 24, \
        f"Faction color names not unique: {24 - len(unique_names)} duplicates"
    
    # Test helper functions
    assert get_faction_color(0) == "#D32F2F", "First color should be Crimson"
    assert get_faction_color_name(0) == "Crimson", "First color name should be Crimson"
    
    # Test wraparound (player 24 should get first color)
    assert get_faction_color(24) == get_faction_color(0), \
        "Color should wrap around after 24"
    
    # Verify specific required colors (spot check)
    expected_colors = {
        "Crimson": "#D32F2F",
        "Azure": "#1976D2",
        "Onyx": "#000000",
        "Ivory": "#F5F5DC",
    }
    color_dict = dict(FACTION_COLORS)
    for name, hex_code in expected_colors.items():
        assert name in color_dict, f"Missing required color: {name}"
        assert color_dict[name] == hex_code, \
            f"Color {name} has wrong hex: expected {hex_code}, got {color_dict[name]}"
    
    print("  Faction colors OK")


def test_key_constants():
    """Verify key constants have expected values from hard constraints."""
    print("Testing key constants...")
    
    # Player limits
    assert MIN_PLAYERS == 2, f"MIN_PLAYERS should be 2, got {MIN_PLAYERS}"
    assert MAX_PLAYERS == 24, f"MAX_PLAYERS should be 24, got {MAX_PLAYERS}"
    
    # Join code
    assert JOIN_CODE_LENGTH == 4, f"JOIN_CODE_LENGTH should be 4, got {JOIN_CODE_LENGTH}"
    
    # Turn defaults
    assert TURN_NUMBER_START == 1, f"TURN_NUMBER_START should be 1, got {TURN_NUMBER_START}"
    assert CURRENT_TURN_START == 1, f"CURRENT_TURN_START should be 1, got {CURRENT_TURN_START}"
    assert DEFAULT_TURN_TIMEOUT_SECONDS == 36288000, \
        f"DEFAULT_TURN_TIMEOUT_SECONDS should be 36288000, got {DEFAULT_TURN_TIMEOUT_SECONDS}"
    
    # Population
    assert POP_TENTHS_PER_POP == 10, f"POP_TENTHS_PER_POP should be 10, got {POP_TENTHS_PER_POP}"
    assert MIN_RP == 0, f"MIN_RP should be 0, got {MIN_RP}"
    
    # Tech
    assert STARTING_TECH_LEVEL == 1, f"STARTING_TECH_LEVEL should be 1, got {STARTING_TECH_LEVEL}"
    
    # Map sizing
    assert SEXTANT_SIZE == 20, f"SEXTANT_SIZE should be 20, got {SEXTANT_SIZE}"
    assert MAP_SIZE_MIN_SEXTANTS == 2, \
        f"MAP_SIZE_MIN_SEXTANTS should be 2, got {MAP_SIZE_MIN_SEXTANTS}"
    assert MAP_SIZE_MAX_SEXTANTS == 6, \
        f"MAP_SIZE_MAX_SEXTANTS should be 6, got {MAP_SIZE_MAX_SEXTANTS}"
    
    # Axial directions
    expected_directions = [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)]
    assert AXIAL_DIRECTIONS == expected_directions, \
        f"AXIAL_DIRECTIONS mismatch: expected {expected_directions}, got {AXIAL_DIRECTIONS}"
    
    # API pagination
    assert DEFAULT_PAGE_SIZE == 50, f"DEFAULT_PAGE_SIZE should be 50, got {DEFAULT_PAGE_SIZE}"
    assert MAX_PAGE_SIZE == 200, f"MAX_PAGE_SIZE should be 200, got {MAX_PAGE_SIZE}"
    
    print("  Key constants OK")


def test_ship_stats():
    """Verify ship stats match milestone spec."""
    print("Testing ship stats...")
    
    expected_ships = {"SCOUT", "CRUISER", "BATTLESHIP", "TRANSPORT"}
    assert set(SHIP_STATS.keys()) == expected_ships, \
        f"Ship types mismatch: expected {expected_ships}, got {set(SHIP_STATS.keys())}"
    
    # Spot check values from milestone doc
    assert SHIP_STATS["SCOUT"]["cost"] == 1
    assert SHIP_STATS["SCOUT"]["cv"] == 1
    assert SHIP_STATS["SCOUT"]["max_range"] == 6
    
    assert SHIP_STATS["BATTLESHIP"]["cost"] == 10
    assert SHIP_STATS["BATTLESHIP"]["cv"] == 10
    assert SHIP_STATS["BATTLESHIP"]["max_range"] == 3
    
    assert SHIP_STATS["TRANSPORT"]["cv"] == 0
    assert SHIP_STATS["TRANSPORT"]["cargo"] == 10
    
    # Starting ships
    assert STARTING_SHIPS == ["SCOUT", "SCOUT", "CRUISER", "TRANSPORT"], \
        f"STARTING_SHIPS mismatch: {STARTING_SHIPS}"
    
    print("  Ship stats OK")


def test_system_ranges():
    """Verify system RP ranges match milestone spec."""
    print("Testing system RP ranges...")
    
    expected_classes = {"A", "B", "C", "D", "E"}
    assert set(SYSTEM_RP_RANGES.keys()) == expected_classes
    
    # Spot check
    assert SYSTEM_RP_RANGES["A"] == (8, 12), f"Class A RP range wrong: {SYSTEM_RP_RANGES['A']}"
    assert SYSTEM_RP_RANGES["E"] == (0, 1), f"Class E RP range wrong: {SYSTEM_RP_RANGES['E']}"
    
    print("  System RP ranges OK")


def test_tech_costs():
    """Verify tech upgrade costs."""
    print("Testing tech costs...")
    
    assert TECH_COSTS == [5, 10, 15, 20, 25], f"TECH_COSTS mismatch: {TECH_COSTS}"
    assert len(TECH_COSTS) == 5, "Should have 5 tech cost entries (0→1 through 4→5)"
    
    print("  Tech costs OK")


def main():
    """Run all smoke tests."""
    print("=" * 50)
    print("SMOKE TEST: constants_gc_mvp_003")
    print("=" * 50)
    
    try:
        test_scan_math()
        test_faction_colors()
        test_key_constants()
        test_ship_stats()
        test_system_ranges()
        test_tech_costs()
        
        print("=" * 50)
        print("SMOKE OK - All constants validated")
        print("=" * 50)
        return 0
        
    except AssertionError as e:
        print(f"\nSMOKE FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\nSMOKE ERROR: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

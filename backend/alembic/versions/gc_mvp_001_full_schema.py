"""Galactic Conquest MVP full schema

Revision ID: gc_mvp_001
Revises: 0fc31956c3c4
Create Date: 2025-01-16

This migration adds all tables needed for the Galactic Conquest MVP:
- Systems: Star systems on the hex map
- Fleets: Player-owned fleet containers
- Ships: Individual ships within fleets
- Populations: Player population at systems
- TechLevels: Technology progression per player
- Stances: Diplomatic stances between players
- FirstContacts: Tracking player encounters
- ScanSnapshots: Turn-based hex state history (one record per hex per turn)
- ScanVisibility: Lookup table linking players to snapshots with scan band
- EventLog: Game event history

It also updates existing tables:
- Game: Replace 'started' boolean with 'status' enum, add 'rng_seed'
- Player: Add faction_color, banked_rp, home_sextant coordinates, is_eliminated
- Turn: Add rng_seed for deterministic resolution
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'gc_mvp_001'
down_revision = "091a15f1f5a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # UPDATE EXISTING TABLES
    # =========================================================================
    
    # --- Update games table ---
    # Remove the 'started' column and replace with 'status' enum
    op.add_column('games', sa.Column('status', sa.String(20), nullable=False, server_default='LOBBY'))
    op.add_column('games', sa.Column('rng_seed', sa.BigInteger(), nullable=False, server_default='0'))
    
    # Remove default after adding column
    op.alter_column('games', 'status', server_default=None)
    op.alter_column('games', 'rng_seed', server_default=None)
    
    # Drop the old 'started' column if it exists
    # Note: This will fail if column doesn't exist - adjust based on your actual schema
    try:
        op.drop_column('games', 'started')
    except Exception:
        pass  # Column may not exist
    
    # Add check constraint for valid game statuses
    op.create_check_constraint(
        'ck_games_status',
        'games',
        "status IN ('LOBBY', 'ACTIVE', 'FINISHED')"
    )
    
    # --- Update players table ---
    op.add_column('players', sa.Column('faction_color', sa.String(7), nullable=False, server_default='#FFFFFF'))
    op.add_column('players', sa.Column('banked_rp', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('players', sa.Column('home_sextant_q', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('home_sextant_r', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('is_eliminated', sa.Boolean(), nullable=False, server_default='false'))
    
    # Remove defaults after adding columns
    op.alter_column('players', 'faction_color', server_default=None)
    op.alter_column('players', 'banked_rp', server_default=None)
    op.alter_column('players', 'is_eliminated', server_default=None)
    
    # --- Update turns table ---
    op.add_column('turns', sa.Column('rng_seed', sa.BigInteger(), nullable=False, server_default='0'))
    op.alter_column('turns', 'rng_seed', server_default=None)
    
    # =========================================================================
    # CREATE NEW TABLES
    # =========================================================================
    
    # --- Systems table ---
    # Represents star systems on the hex map
    op.create_table(
        'systems',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('game_id', UUID(as_uuid=True), sa.ForeignKey('games.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hex_q', sa.Integer(), nullable=False),
        sa.Column('hex_r', sa.Integer(), nullable=False),
        sa.Column('system_class', sa.String(1), nullable=False),  # A, B, C, D, E
        sa.Column('rp_value', sa.Integer(), nullable=False),
        sa.Column('neutral_pop_tenths', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('neutral_disposition', sa.String(20), nullable=True),  # HOSTILE, FRIENDLY, DEFENSIVE
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Composite unique constraint: one system per hex per game
    op.create_unique_constraint('uq_systems_game_hex', 'systems', ['game_id', 'hex_q', 'hex_r'])
    
    # Index for efficient hex lookups
    op.create_index('ix_systems_game_hex', 'systems', ['game_id', 'hex_q', 'hex_r'])
    
    # Check constraint for valid system classes
    op.create_check_constraint(
        'ck_systems_class',
        'systems',
        "system_class IN ('A', 'B', 'C', 'D', 'E')"
    )
    
    # --- Fleets table ---
    # Container for ships owned by a player
    op.create_table(
        'fleets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('game_id', UUID(as_uuid=True), sa.ForeignKey('games.id', ondelete='CASCADE'), nullable=False),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hex_q', sa.Integer(), nullable=False),
        sa.Column('hex_r', sa.Integer(), nullable=False),
        sa.Column('cargo_pop_tenths', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Index for efficient lookups by player and position
    op.create_index('ix_fleets_game_player', 'fleets', ['game_id', 'player_id'])
    op.create_index('ix_fleets_game_hex', 'fleets', ['game_id', 'hex_q', 'hex_r'])
    
    # --- Ships table ---
    # Individual ships within fleets
    op.create_table(
        'ships',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('fleet_id', UUID(as_uuid=True), sa.ForeignKey('fleets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ship_type', sa.String(20), nullable=False),  # SCOUT, CRUISER, BATTLESHIP, TRANSPORT
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Index for efficient fleet ship lookups
    op.create_index('ix_ships_fleet', 'ships', ['fleet_id'])
    
    # Check constraint for valid ship types
    op.create_check_constraint(
        'ck_ships_type',
        'ships',
        "ship_type IN ('SCOUT', 'CRUISER', 'BATTLESHIP', 'TRANSPORT')"
    )
    
    # --- Populations table ---
    # Player population at a system
    op.create_table(
        'populations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('system_id', UUID(as_uuid=True), sa.ForeignKey('systems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pop_tenths', sa.Integer(), nullable=False),  # Population in 0.1 units
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Composite unique constraint: one population record per player per system
    op.create_unique_constraint('uq_populations_system_player', 'populations', ['system_id', 'player_id'])
    
    # Index for efficient lookups
    op.create_index('ix_populations_system', 'populations', ['system_id'])
    op.create_index('ix_populations_player', 'populations', ['player_id'])
    
    # --- Tech Levels table ---
    # Technology progression for each player
    op.create_table(
        'tech_levels',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('movement_tech', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('combat_tech', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scanning_tech', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Check constraints for valid tech levels (0-5)
    op.create_check_constraint('ck_tech_movement', 'tech_levels', 'movement_tech >= 0 AND movement_tech <= 5')
    op.create_check_constraint('ck_tech_combat', 'tech_levels', 'combat_tech >= 0 AND combat_tech <= 5')
    op.create_check_constraint('ck_tech_scanning', 'tech_levels', 'scanning_tech >= 0 AND scanning_tech <= 5')
    
    # --- Stances table ---
    # Diplomatic stance between players
    op.create_table(
        'stances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=True),  # NULL = default stance
        sa.Column('stance', sa.String(20), nullable=False, server_default='NEUTRAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Composite unique constraint: one stance per player pair
    op.create_unique_constraint('uq_stances_player_target', 'stances', ['player_id', 'target_player_id'])
    
    # Check constraint for valid stances
    op.create_check_constraint(
        'ck_stances_stance',
        'stances',
        "stance IN ('HOSTILE', 'NEUTRAL', 'FRIENDLY')"
    )
    
    # Index for lookups
    op.create_index('ix_stances_player', 'stances', ['player_id'])
    
    # --- First Contacts table ---
    # Tracks when players first encounter each other
    op.create_table(
        'first_contacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('game_id', UUID(as_uuid=True), sa.ForeignKey('games.id', ondelete='CASCADE'), nullable=False),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('other_player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('hex_q', sa.Integer(), nullable=False),
        sa.Column('hex_r', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Composite unique constraint: one first contact record per player pair per game
    op.create_unique_constraint(
        'uq_first_contacts_players',
        'first_contacts',
        ['game_id', 'player_id', 'other_player_id']
    )
    
    # --- Scan Snapshots table ---
    # Records the state of each scanned hex at the end of each turn
    # This is the authoritative game state history - one record per hex per turn
    op.create_table(
        'scan_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('turn_id', UUID(as_uuid=True), sa.ForeignKey('turns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hex_q', sa.Integer(), nullable=False),
        sa.Column('hex_r', sa.Integer(), nullable=False),
        sa.Column('contents', JSONB, nullable=False),  # Full state of hex at turn end
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Composite unique constraint: one snapshot per hex per turn
    op.create_unique_constraint('uq_scan_snapshots_turn_hex', 'scan_snapshots', ['turn_id', 'hex_q', 'hex_r'])
    
    # Index for efficient turn lookups
    op.create_index('ix_scan_snapshots_turn', 'scan_snapshots', ['turn_id'])
    op.create_index('ix_scan_snapshots_turn_hex', 'scan_snapshots', ['turn_id', 'hex_q', 'hex_r'])
    
    # --- Scan Visibility table ---
    # Lookup table linking players to hex snapshots with their best scan band
    # Multiple sources may scan the same hex; only the best band is recorded
    op.create_table(
        'scan_visibility',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('scan_snapshot_id', UUID(as_uuid=True), sa.ForeignKey('scan_snapshots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scan_band', sa.String(10), nullable=False),  # SHORT, MEDIUM, LONG (best band for this player)
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Composite unique constraint: one visibility record per player per snapshot
    op.create_unique_constraint('uq_scan_visibility_snapshot_player', 'scan_visibility', ['scan_snapshot_id', 'player_id'])
    
    # Indexes for efficient lookups
    op.create_index('ix_scan_visibility_snapshot', 'scan_visibility', ['scan_snapshot_id'])
    op.create_index('ix_scan_visibility_player', 'scan_visibility', ['player_id'])
    
    # Check constraint for valid scan bands
    op.create_check_constraint(
        'ck_scan_visibility_band',
        'scan_visibility',
        "scan_band IN ('SHORT', 'MEDIUM', 'LONG')"
    )
    
    # --- Event Log table ---
    # Records all game events for replay and debugging
    op.create_table(
        'event_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('game_id', UUID(as_uuid=True), sa.ForeignKey('games.id', ondelete='CASCADE'), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', JSONB, nullable=False),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='SET NULL'), nullable=True),  # Actor, if applicable
        sa.Column('visibility', sa.String(20), nullable=False, server_default='PUBLIC'),  # PUBLIC, PRIVATE, PLAYER_ONLY
        sa.Column('hex_q', sa.Integer(), nullable=True),  # Location of event, if applicable
        sa.Column('hex_r', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Index for efficient game/turn lookups
    op.create_index('ix_event_log_game_turn', 'event_log', ['game_id', 'turn_number'])
    op.create_index('ix_event_log_game_type', 'event_log', ['game_id', 'event_type'])
    
    # Check constraint for valid event types
    op.create_check_constraint(
        'ck_event_log_type',
        'event_log',
        "event_type IN ('GAME_STARTED', 'TURN_RESOLVED', 'FLEET_MOVED', 'COMBAT_OCCURRED', "
        "'SYSTEM_CAPTURED', 'POPULATION_CHANGED', 'TECH_PURCHASED', 'PLAYER_ELIMINATED', "
        "'FIRST_CONTACT', 'FLEET_SPLIT', 'FLEET_MERGED', 'SHIP_BUILT', 'POPULATION_LOADED', "
        "'POPULATION_UNLOADED', 'STANCE_CHANGED', 'TAXES_PAID', 'POPULATION_REDUCED')"
    )


def downgrade() -> None:
    # Drop new tables in reverse order (respecting foreign keys)
    op.drop_table('event_log')
    op.drop_table('scan_visibility')
    op.drop_table('scan_snapshots')
    op.drop_table('first_contacts')
    op.drop_table('stances')
    op.drop_table('tech_levels')
    op.drop_table('populations')
    op.drop_table('ships')
    op.drop_table('fleets')
    op.drop_table('systems')
    
    # Revert turns table changes
    op.drop_column('turns', 'rng_seed')
    
    # Revert players table changes
    op.drop_column('players', 'is_eliminated')
    op.drop_column('players', 'home_sextant_r')
    op.drop_column('players', 'home_sextant_q')
    op.drop_column('players', 'banked_rp')
    op.drop_column('players', 'faction_color')
    
    # Revert games table changes
    op.drop_constraint('ck_games_status', 'games', type_='check')
    op.drop_column('games', 'rng_seed')
    op.drop_column('games', 'status')
    op.add_column('games', sa.Column('started', sa.Boolean(), nullable=False, server_default='false'))

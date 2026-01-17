"""gc_mvp_002 alignment

Revision ID: gc_mvp_002
Revises: gc_mvp_001
Create Date: 2026-01-17

This migration aligns the database schema with the SQLAlchemy ORM metadata:

1. Sets timestamp columns to NOT NULL where server_default=now() exists
2. Adds ON DELETE CASCADE to foreign keys for proper cascade behavior

This migration does NOT:
- Drop any indexes (all Step 1 indexes are preserved)
- Drop orders.target_type column
- Change orders.target_id nullability (remains NOT NULL)

The goal is to make `alembic check` pass with no drift.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'gc_mvp_002'
down_revision = 'gc_mvp_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply alignment changes."""
    
    # =========================================================================
    # PART 1: Set timestamp columns to NOT NULL
    # These columns have server_default=now() so NOT NULL is safe
    # =========================================================================
    
    # event_log.created_at
    op.alter_column('event_log', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # first_contacts.created_at
    op.alter_column('first_contacts', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # fleets.created_at
    op.alter_column('fleets', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # populations.created_at
    op.alter_column('populations', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # populations.updated_at
    op.alter_column('populations', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # scan_snapshots.created_at
    op.alter_column('scan_snapshots', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # scan_visibility.created_at
    op.alter_column('scan_visibility', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # ships.created_at
    op.alter_column('ships', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # stances.created_at
    op.alter_column('stances', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # stances.updated_at
    op.alter_column('stances', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # systems.created_at
    op.alter_column('systems', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # tech_levels.created_at
    op.alter_column('tech_levels', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # tech_levels.updated_at
    op.alter_column('tech_levels', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    
    # =========================================================================
    # PART 2: Add ON DELETE CASCADE to foreign keys
    # Drop existing FK constraints and recreate with CASCADE
    # Using explicit constraint names for stability
    # =========================================================================
    
    # --- sessions.user_id ---
    op.drop_constraint('sessions_user_id_fkey', 'sessions', type_='foreignkey')
    op.create_foreign_key(
        'sessions_user_id_fkey',
        'sessions', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # --- players.game_id ---
    op.drop_constraint('players_game_id_fkey', 'players', type_='foreignkey')
    op.create_foreign_key(
        'players_game_id_fkey',
        'players', 'games',
        ['game_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # --- turns.game_id ---
    op.drop_constraint('turns_game_id_fkey', 'turns', type_='foreignkey')
    op.create_foreign_key(
        'turns_game_id_fkey',
        'turns', 'games',
        ['game_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # --- turn_submissions.game_id ---
    op.drop_constraint('turn_submissions_game_id_fkey', 'turn_submissions', type_='foreignkey')
    op.create_foreign_key(
        'turn_submissions_game_id_fkey',
        'turn_submissions', 'games',
        ['game_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # --- turn_submissions.turn_id ---
    op.drop_constraint('turn_submissions_turn_id_fkey', 'turn_submissions', type_='foreignkey')
    op.create_foreign_key(
        'turn_submissions_turn_id_fkey',
        'turn_submissions', 'turns',
        ['turn_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # --- turn_submissions.player_id ---
    op.drop_constraint('turn_submissions_player_id_fkey', 'turn_submissions', type_='foreignkey')
    op.create_foreign_key(
        'turn_submissions_player_id_fkey',
        'turn_submissions', 'players',
        ['player_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # --- orders.game_id ---
    op.drop_constraint('orders_game_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key(
        'orders_game_id_fkey',
        'orders', 'games',
        ['game_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # --- orders.turn_id ---
    op.drop_constraint('orders_turn_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key(
        'orders_turn_id_fkey',
        'orders', 'turns',
        ['turn_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # --- orders.player_id ---
    op.drop_constraint('orders_player_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key(
        'orders_player_id_fkey',
        'orders', 'players',
        ['player_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Revert alignment changes."""
    
    # =========================================================================
    # Revert FK changes (remove CASCADE)
    # =========================================================================
    
    # --- orders.player_id ---
    op.drop_constraint('orders_player_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key(
        'orders_player_id_fkey',
        'orders', 'players',
        ['player_id'], ['id']
    )
    
    # --- orders.turn_id ---
    op.drop_constraint('orders_turn_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key(
        'orders_turn_id_fkey',
        'orders', 'turns',
        ['turn_id'], ['id']
    )
    
    # --- orders.game_id ---
    op.drop_constraint('orders_game_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key(
        'orders_game_id_fkey',
        'orders', 'games',
        ['game_id'], ['id']
    )
    
    # --- turn_submissions.player_id ---
    op.drop_constraint('turn_submissions_player_id_fkey', 'turn_submissions', type_='foreignkey')
    op.create_foreign_key(
        'turn_submissions_player_id_fkey',
        'turn_submissions', 'players',
        ['player_id'], ['id']
    )
    
    # --- turn_submissions.turn_id ---
    op.drop_constraint('turn_submissions_turn_id_fkey', 'turn_submissions', type_='foreignkey')
    op.create_foreign_key(
        'turn_submissions_turn_id_fkey',
        'turn_submissions', 'turns',
        ['turn_id'], ['id']
    )
    
    # --- turn_submissions.game_id ---
    op.drop_constraint('turn_submissions_game_id_fkey', 'turn_submissions', type_='foreignkey')
    op.create_foreign_key(
        'turn_submissions_game_id_fkey',
        'turn_submissions', 'games',
        ['game_id'], ['id']
    )
    
    # --- turns.game_id ---
    op.drop_constraint('turns_game_id_fkey', 'turns', type_='foreignkey')
    op.create_foreign_key(
        'turns_game_id_fkey',
        'turns', 'games',
        ['game_id'], ['id']
    )
    
    # --- players.game_id ---
    op.drop_constraint('players_game_id_fkey', 'players', type_='foreignkey')
    op.create_foreign_key(
        'players_game_id_fkey',
        'players', 'games',
        ['game_id'], ['id']
    )
    
    # --- sessions.user_id ---
    op.drop_constraint('sessions_user_id_fkey', 'sessions', type_='foreignkey')
    op.create_foreign_key(
        'sessions_user_id_fkey',
        'sessions', 'users',
        ['user_id'], ['id']
    )
    
    # =========================================================================
    # Revert timestamp NOT NULL changes
    # =========================================================================
    
    op.alter_column('tech_levels', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('tech_levels', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('systems', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('stances', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('stances', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('ships', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('scan_visibility', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('scan_snapshots', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('populations', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('populations', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('fleets', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('first_contacts', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    
    op.alter_column('event_log', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))

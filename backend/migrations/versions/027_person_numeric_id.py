"""Add numeric CRBCL Person ID, durable photo reference, and sequence tracking.

Revision ID: 027_person_numeric_id
Revises: 026_board_dashboard_publication_controls
Create Date: 2026-09-12 09:00:00.000000

Note on Person ID Starting Base:
STARTING_BASE = 1100000000 is an implementation-selected starting point chosen to generate
10-digit numeric identifiers matching client examples (e.g. 1123840557) while reserving
the lower namespace and keeping identifiers opaque. It is not an official CRBCL allocation policy.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "027_person_numeric_id"
down_revision: str | None = "026_board_dashboard_publication_controls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STARTING_BASE: int = 1100000000
MAX_CAPACITY: int = 9999999999


def upgrade() -> None:
    # ── 1. Create person_sequences table ─────────────────────────
    op.create_table(
        "person_sequences",
        sa.Column("sequence_name", sa.String(50), primary_key=True),
        sa.Column("last_value", sa.BigInteger(), nullable=False, server_default=sa.text(str(STARTING_BASE))),
    )

    # ── 2. Add person_id_number and photo_document_id to persons ─
    op.add_column(
        "persons",
        sa.Column("person_id_number", sa.String(10), nullable=True),
    )
    op.add_column(
        "persons",
        sa.Column("photo_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_persons_photo_document_id", "persons", ["photo_document_id"])
    op.create_foreign_key(
        "fk_persons_photo_document_id",
        "persons",
        "documents",
        ["photo_document_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── 3. Backfill existing records with capacity protection ────
    connection = op.get_bind()
    persons_table = sa.table(
        "persons",
        sa.Column("id", sa.String()),
        sa.Column("person_id_number", sa.String()),
        sa.Column("created_at", sa.DateTime()),
    )
    result = connection.execute(
        sa.select(persons_table.c.id)
        .where(persons_table.c.person_id_number.is_(None))
        .order_by(persons_table.c.created_at.asc().nulls_last(), persons_table.c.id.asc())
    ).fetchall()

    unassigned_count = len(result)
    available_capacity = MAX_CAPACITY - STARTING_BASE
    if unassigned_count > available_capacity:
        raise ValueError(
            f"Cannot backfill Person records: existing unassigned count ({unassigned_count}) "
            f"exceeds available 10-digit namespace capacity ({available_capacity}) "
            f"from starting base {STARTING_BASE}. Migration aborted before assigning IDs."
        )

    current_val = STARTING_BASE
    for row in result:
        current_val += 1
        if current_val > MAX_CAPACITY:
            raise ValueError(
                f"Person ID allocation {current_val} exceeds maximum 10-digit capacity {MAX_CAPACITY}."
            )
        connection.execute(
            persons_table.update()
            .where(persons_table.c.id == row[0])
            .values(person_id_number=str(current_val))
        )

    # Insert sequence tracking row initialized to final backfilled value
    # (or STARTING_BASE if database had no existing records)
    seq_table = sa.table(
        "person_sequences",
        sa.Column("sequence_name", sa.String()),
        sa.Column("last_value", sa.BigInteger()),
    )
    connection.execute(
        seq_table.insert().values(
            sequence_name="person_id",
            last_value=current_val,
        )
    )

    # ── 4. Enforce non-nullable, unique index, and 10-digit constraint
    op.alter_column("persons", "person_id_number", nullable=False)
    op.create_index("ix_persons_person_id_number", "persons", ["person_id_number"], unique=True)
    op.create_check_constraint(
        "ck_persons_person_id_number_numeric_10",
        "persons",
        "length(person_id_number) = 10 AND person_id_number ~ '^[0-9]{10}$'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_persons_person_id_number_numeric_10", table_name="persons", type_="check")
    op.drop_index("ix_persons_person_id_number", table_name="persons")
    op.drop_column("persons", "person_id_number")
    op.drop_constraint("fk_persons_photo_document_id", table_name="persons", type_="foreignkey")
    op.drop_index("ix_persons_photo_document_id", table_name="persons")
    op.drop_column("persons", "photo_document_id")
    op.drop_table("person_sequences")

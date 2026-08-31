"""002 — People, Families, Households, Providers, Schools, and Medical Profiles.

Revision ID: 002_people_families
Revises: 001_platform_foundation
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_people_families"
down_revision: str | None = "001_platform_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Persons Table ─────────────────────────────────────
    op.create_table(
        "persons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("first_name", sa.String(200), nullable=False),
        sa.Column("middle_name", sa.String(200), nullable=True),
        sa.Column("last_name", sa.String(200), nullable=False),
        sa.Column("preferred_name", sa.String(200), nullable=True),
        sa.Column("aliases", sa.String(500), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("gender", sa.String(50), nullable=True),
        sa.Column("photo_url", sa.String(1000), nullable=True),
        sa.Column("place_of_birth", sa.String(200), nullable=True),
        sa.Column("preferred_language", sa.String(100), nullable=False, server_default="English"),
        sa.Column("languages_spoken", sa.String(300), nullable=True),
        sa.Column("treaty_number", sa.String(100), nullable=True),
        sa.Column("band_nation", sa.String(200), nullable=True),
        sa.Column("indigenous_identity", sa.String(100), nullable=True),
        sa.Column("health_card_number", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("emergency_contact_name", sa.String(200), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(50), nullable=True),
        sa.Column("source_of_income", sa.String(200), nullable=True),
        sa.Column("employment_status", sa.String(100), nullable=True),
        sa.Column("employer", sa.String(200), nullable=True),
        sa.Column("employment_details", sa.Text, nullable=True),
        sa.Column("social_media_handles", postgresql.JSONB, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_persons_name_trgm", "persons", ["first_name", "last_name"])
    op.create_index("ix_persons_dob", "persons", ["date_of_birth"])
    op.create_index("ix_persons_treaty", "persons", ["treaty_number"])
    op.create_index("ix_persons_health_card", "persons", ["health_card_number"])
    op.execute("CREATE INDEX ix_persons_first_name_trgm ON persons USING gin (first_name gin_trgm_ops)")
    op.execute("CREATE INDEX ix_persons_last_name_trgm ON persons USING gin (last_name gin_trgm_ops)")

    # ── 2. Add person_id to clients ──────────────────────────
    op.add_column(
        "clients",
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
        ),
    )
    op.create_index("ix_clients_person_id", "clients", ["person_id"])

    # ── 3. Person Addresses ──────────────────────────────────
    op.create_table(
        "person_addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("address_type", sa.String(50), nullable=False, server_default="Residential"),
        sa.Column("address_line_1", sa.String(500), nullable=False),
        sa.Column("address_line_2", sa.String(500), nullable=True),
        sa.Column("city", sa.String(200), nullable=False, server_default="Regina"),
        sa.Column("province", sa.String(100), nullable=False, server_default="Saskatchewan"),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="Canada"),
        sa.Column("on_reserve", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("valid_from", sa.Date, nullable=True),
        sa.Column("valid_to", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_person_addresses_person_id", "person_addresses", ["person_id"])

    # ── 4. Person Contacts ───────────────────────────────────
    op.create_table(
        "person_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("contact_type", sa.String(50), nullable=False),
        sa.Column("value", sa.String(320), nullable=False),
        sa.Column("label", sa.String(100), nullable=False, server_default="Primary"),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_person_contacts_person_id", "person_contacts", ["person_id"])

    # ── 5. Person Physical Descriptions ──────────────────────
    op.create_table(
        "person_physical_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("eye_colour", sa.String(50), nullable=True),
        sa.Column("hair_colour", sa.String(50), nullable=True),
        sa.Column("height_cm", sa.Float, nullable=True),
        sa.Column("weight_kg", sa.Float, nullable=True),
        sa.Column("tattoos", sa.Text, nullable=True),
        sa.Column("piercings", sa.Text, nullable=True),
        sa.Column("birthmarks", sa.Text, nullable=True),
        sa.Column("scars", sa.Text, nullable=True),
        sa.Column("distinguishing_marks", sa.Text, nullable=True),
        sa.Column("glasses", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("contact_lenses", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── 6. Person Cultural Profiles ──────────────────────────
    op.create_table(
        "person_cultural_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("cultural_connections", sa.Text, nullable=True),
        sa.Column("ceremonies", sa.Text, nullable=True),
        sa.Column("elders_connected", sa.Text, nullable=True),
        sa.Column("land_based_activities", sa.Text, nullable=True),
        sa.Column("language_goals", sa.Text, nullable=True),
        sa.Column("dietary_preferences", sa.Text, nullable=True),
        sa.Column("extracurricular_activities", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── 7. Person Strengths & Challenges ─────────────────────
    op.create_table(
        "person_strengths",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("lookup_value_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_person_strengths_person_id", "person_strengths", ["person_id"])

    op.create_table(
        "person_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("lookup_value_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="Moderate"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_person_challenges_person_id", "person_challenges", ["person_id"])

    # ── 8. Person Merges Audit ───────────────────────────────
    op.create_table(
        "person_merges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("merged_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("ix_person_merges_source", "person_merges", ["source_person_id"])
    op.create_index("ix_person_merges_target", "person_merges", ["target_person_id"])

    # ── 9. Medical Profiles, Allergies, Conditions, Medications
    op.create_table(
        "client_medical_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("dental_notes", sa.Text, nullable=True),
        sa.Column("mental_health_notes", sa.Text, nullable=True),
        sa.Column("chemical_dependency_history", sa.Text, nullable=True),
        sa.Column("general_notes", sa.Text, nullable=True),
        sa.Column("primary_physician_name", sa.String(200), nullable=True),
        sa.Column("primary_physician_phone", sa.String(50), nullable=True),
        sa.Column("primary_physician_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "client_allergies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("allergen", sa.String(200), nullable=False),
        sa.Column("reaction", sa.String(300), nullable=False, server_default=""),
        sa.Column("severity", sa.String(50), nullable=False, server_default="Moderate"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_client_allergies_client_id", "client_allergies", ["client_id"])

    op.create_table(
        "client_medical_conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("condition_name", sa.String(300), nullable=False),
        sa.Column("diagnosed_date", sa.Date, nullable=True),
        sa.Column("is_chronic", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("treatment_plan", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_client_medical_conditions_client_id", "client_medical_conditions", ["client_id"])

    op.create_table(
        "client_medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("medication_name", sa.String(300), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(100), nullable=False),
        sa.Column("route", sa.String(100), nullable=False, server_default="Oral"),
        sa.Column("prescriber_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prescriber_name", sa.String(200), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="Active"),
        sa.Column("instructions", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_client_medications_client_id", "client_medications", ["client_id"])

    # ── 10. Providers Pool ───────────────────────────────────
    op.create_table(
        "providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("provider_type", sa.String(100), nullable=False),
        sa.Column("organization_name", sa.String(300), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "provider_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("address_line_1", sa.String(500), nullable=False),
        sa.Column("city", sa.String(200), nullable=False, server_default="Regina"),
        sa.Column("province", sa.String(100), nullable=False, server_default="Saskatchewan"),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_provider_locations_provider_id", "provider_locations", ["provider_id"])

    op.create_table(
        "provider_specialties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("specialty", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_provider_specialties_provider_id", "provider_specialties", ["provider_id"])

    op.create_table(
        "client_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(100), nullable=False, server_default="Primary Care"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_client_providers_client_id", "client_providers", ["client_id"])
    op.create_index("ix_client_providers_provider_id", "client_providers", ["provider_id"])

    # ── 11. Schools & Enrolments ─────────────────────────────
    op.create_table(
        "schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("school_type", sa.String(100), nullable=False, server_default="Elementary"),
        sa.Column("district", sa.String(200), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("city", sa.String(200), nullable=False, server_default="Regina"),
        sa.Column("province", sa.String(100), nullable=False, server_default="Saskatchewan"),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("principal_name", sa.String(200), nullable=True),
        sa.Column("contact_email", sa.String(320), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "client_school_enrolments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("grade_level", sa.String(50), nullable=False, server_default="Grade 1"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("has_iep", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("iep_details", sa.Text, nullable=True),
        sa.Column("school_contact_person", sa.String(200), nullable=True),
        sa.Column("attendance_concerns", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_client_school_enrolments_client_id", "client_school_enrolments", ["client_id"])
    op.create_index("ix_client_school_enrolments_school_id", "client_school_enrolments", ["school_id"])

    # ── 12. Family Members & Relationships ───────────────────
    op.create_table(
        "family_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("families.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("role", sa.String(100), nullable=False, server_default="Member"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_family_members_family_person", "family_members", ["family_id", "person_id"])

    op.create_table(
        "family_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("families.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column(
            "person_a_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_b_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_family_relationships_pair", "family_relationships", ["person_a_id", "person_b_id"])

    # ── 13. Households & Memberships ─────────────────────────
    op.create_table(
        "households",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("address_line_1", sa.String(500), nullable=False),
        sa.Column("address_line_2", sa.String(500), nullable=True),
        sa.Column("city", sa.String(200), nullable=False, server_default="Regina"),
        sa.Column("province", sa.String(100), nullable=False, server_default="Saskatchewan"),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("on_reserve", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "household_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "household_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("role", sa.String(100), nullable=False, server_default="Resident"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_household_memberships_h_p", "household_memberships", ["household_id", "person_id"])


def downgrade() -> None:
    tables = [
        "household_memberships",
        "households",
        "family_relationships",
        "family_members",
        "client_school_enrolments",
        "schools",
        "client_providers",
        "provider_specialties",
        "provider_locations",
        "providers",
        "client_medications",
        "client_medical_conditions",
        "client_allergies",
        "client_medical_profiles",
        "person_merges",
        "person_challenges",
        "person_strengths",
        "person_cultural_profiles",
        "person_physical_descriptions",
        "person_contacts",
        "person_addresses",
    ]
    for table in tables:
        op.drop_table(table)

    op.drop_column("clients", "person_id")
    op.drop_table("persons")

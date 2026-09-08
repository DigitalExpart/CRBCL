# backend/app/constants/department.py
"""Backend source of truth for department names.
Only used for validation of the optional `department` field on user creation / update.
The list mirrors `src/constants/departments.js`.
"""

DEPARTMENTS = [
    "Resource Team",
    "Growing Up Well (Protection Services)",
    "Enhancement & Preservation (Prevention Services)",
    "Post-Majority (Young Adults)",
    "Culture & Traditional Healing",
    "Early Learning / Daycare",
    "Sacred Wolf Lodge",
    "Policy & Data",
    "Finance & Administration",
    "Human Resources",
    "Operations & Facilities",
    "Housing (Home Fire)",
    "IT & Systems",
    "Communications",
    "Governance & Executive Leadership",
    # Legacy aliases retained for backward-compatible test data
    "Case Management",
    "Administration",
]

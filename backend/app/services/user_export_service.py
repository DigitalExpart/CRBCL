"""CRBCL User Directory Excel Export Service.

Implements authoritative Excel (.xlsx) export of the CRBCL User directory
matching the approved format, with freeze panes, autofilter, column width
tuning, formula injection mitigation, and authoritative last-login timestamps.

Schema mapping limitations
--------------------------
The CRBCL ``User`` table stores authentication credentials only.  It does not
have discrete ``username``, ``first_name``, or ``last_name`` columns.

* **Username** — mapped from ``User.email`` because email is the sole
  authentication identity in the current CRBCL system.  No separate username
  field exists.

* **First Name / Last Name** — derived presentation fields parsed from the
  single ``User.full_name`` column by splitting on the first whitespace.  These
  are *not* authoritative separate identity attributes; they are a convenience
  transformation for the spreadsheet consumer.

  An ``Employee`` record (``org_ops.Employee``) exists with canonical
  ``first_name``/``last_name`` columns linked via a *nullable* FK
  (``Employee.user_id``).  That join is not safe for a full user export because
  it is not guaranteed to be populated for every User (service accounts,
  IT-admin-created accounts, legacy users, etc.).  Introducing it without an
  approved schema migration or data-quality gate could silently blank name
  columns for a subset of users.  A future migration may add
  ``first_name``/``last_name`` directly to the ``User`` table and back-fill
  from ``Employee``; that requires explicit CRBCL approval.
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.models.user import User

USER_EXPORT_COLUMNS: list[str] = [
    "Username",
    "First Name",
    "Last Name",
    "Status",
    "Email",
    "Last Login",
]

FORMULA_TRIGGERS: tuple[str, ...] = ("=", "+", "-", "@", "\t", "\r")


def sanitize_cell_value(val: Any) -> Any:
    """Protect against Excel formula injection (CSV/Formula Injection / CWE-1236).

    If a text value begins with formula trigger characters (=, +, -, @, tab, CR),
    prepend a single quote (') so spreadsheet engines treat it strictly as literal text.
    """
    if not isinstance(val, str):
        return val
    stripped = val.lstrip()
    if stripped and stripped.startswith(FORMULA_TRIGGERS):
        return f"'{val}"
    return val


def extract_user_row(user: User) -> dict[str, Any]:
    """Extract and format user fields according to the export specification.

    Columns:
    - Username  — User.email (email is the authentication identity; no
                  separate username column exists on User).
    - First Name — derived by splitting User.full_name on first whitespace.
                   NOT an authoritative identity attribute.
    - Last Name  — remainder after the first-name split; empty string for
                   single-name entries.  NOT authoritative.
    - Status    — "Active" / "Inactive" from User.is_active.
    - Email     — User.email.
    - Last Login — User.last_login_at (authoritative successful-login
                   timestamp).  None → blank cell.  Never substitutes
                   created_at, updated_at, or export time.

    Authoritative source for Last Login: User.last_login_at
    Must not substitute: created_at, updated_at, token-refresh time, export time.
    """
    # 1. Username = email — no separate username column exists on User.
    username = sanitize_cell_value(user.email or "")

    # 2 & 3. First Name & Last Name — derived from full_name.
    #   NOTE: These are NOT authoritative separate identity attributes.
    #   The Employee model has canonical first_name/last_name but its user_id
    #   FK is nullable; a join would produce blank names for users without an
    #   Employee record (service accounts, admin-created users, etc.).
    #   Splitting full_name is a best-effort presentation convenience only.
    full_name = (user.full_name or "").strip()
    if full_name:
        parts = full_name.split(maxsplit=1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
    else:
        first_name = ""
        last_name = ""

    first_name = sanitize_cell_value(first_name)
    last_name = sanitize_cell_value(last_name)


    # 4. Status: Human-readable Active or Inactive
    status = "Active" if bool(user.is_active) else "Inactive"

    # 5. Email
    email = sanitize_cell_value(user.email or "")

    # 6. Last Login: authoritative successful-login timestamp (last_login_at).
    #    Never-logged-in users receive None (blank cell in Excel).
    #    Do NOT substitute created_at, updated_at, or any other timestamp.
    raw_last_login = user.last_login_at
    if raw_last_login is not None:
        last_login_dt = (
            raw_last_login.astimezone(UTC).replace(tzinfo=None)
            if raw_last_login.tzinfo is not None
            else raw_last_login
        )
    else:
        last_login_dt = None

    return {
        "Username": username,
        "First Name": first_name,
        "Last Name": last_name,
        "Status": status,
        "Email": email,
        "Last Login": last_login_dt,
    }


def generate_user_excel_export(users: Sequence[User]) -> bytes:
    """Generate an authoritative .xlsx workbook for the CRBCL user directory."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CRBCL Users"

    # Append Header Row
    ws.append(USER_EXPORT_COLUMNS)

    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # CRBCL Navy
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="left", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    ws.row_dimensions[1].height = 26

    for col_idx in range(1, len(USER_EXPORT_COLUMNS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border

    data_font = Font(name="Calibri", size=10)
    data_alignment = Alignment(vertical="center")

    for row_idx, user in enumerate(users, start=2):
        row_data = extract_user_row(user)
        ws.row_dimensions[row_idx].height = 20

        col_values = [
            row_data["Username"],
            row_data["First Name"],
            row_data["Last Name"],
            row_data["Status"],
            row_data["Email"],
            row_data["Last Login"],
        ]

        for col_idx, val in enumerate(col_values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = data_font
            cell.alignment = data_alignment
            cell.border = thin_border
            if isinstance(val, datetime | date):
                cell.number_format = "yyyy-mm-dd hh:mm:ss"

    # Frozen header row
    ws.freeze_panes = "A2"

    # Autofilter across the header row and data
    total_rows = max(ws.max_row, 1)
    ws.auto_filter.ref = f"A1:F{total_rows}"

    # Set readable column widths based on content with robust minimums
    min_widths: dict[int, int] = {
        1: 28,  # Username
        2: 18,  # First Name
        3: 18,  # Last Name
        4: 14,  # Status
        5: 30,  # Email
        6: 22,  # Last Login
    }

    for col_idx in range(1, 7):
        col_letter = get_column_letter(col_idx)
        max_len = 0
        for cell in ws[col_letter]:
            if cell.value is not None:
                if isinstance(cell.value, datetime | date):
                    max_len = max(max_len, 19)
                else:
                    max_len = max(max_len, len(str(cell.value)))
        base_width = min_widths.get(col_idx, 16)
        ws.column_dimensions[col_letter].width = max(max_len + 4, base_width)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

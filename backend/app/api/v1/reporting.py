"""Reporting API Router (Phase 11)."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import get_current_user_permissions, require_permission
from app.repositories.reporting_qa_repo import ReportingQARepository
from app.schemas.reporting_qa import AdHocReportRequest, ReportExportRequest, SavedReportCreate, SavedReportResponse
from app.services.reporting_service import ReportingService
from app.services.resource_reports_service import ResourceReportsService

router = APIRouter(prefix="/reports", tags=["Reporting & Analytics"])


@router.get(
    "/catalogue",
    dependencies=[Depends(require_permission(Permissions.REPORT_READ))],
)
async def get_reporting_catalogue(
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    """Return authorized metadata catalogue of datasets and reportable fields."""
    return ReportingService.get_catalogue_metadata(user_perms)


# ── Canned Reports ─────────────────────────────────────────────
@router.get(
    "/canned/intake-monthly",
    dependencies=[Depends(require_permission(Permissions.REPORT_READ))],
)
async def get_intake_monthly_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    can_reporters = Permissions.INTAKE_REPORTER_READ in user_perms or "admin.configuration.manage" in user_perms
    return await ReportingService.run_intake_monthly_report(
        db, start_date=start_date, end_date=end_date, can_read_reporters=can_reporters
    )


@router.get(
    "/canned/active-cases-worker",
    dependencies=[Depends(require_permission(Permissions.REPORT_READ))],
)
async def get_active_cases_by_worker(
    db: AsyncSession = Depends(get_db),
):
    return await ReportingService.run_active_cases_by_worker(db)


@router.get(
    "/canned/cases-type-status",
    dependencies=[Depends(require_permission(Permissions.REPORT_READ))],
)
async def get_cases_by_type_status(
    db: AsyncSession = Depends(get_db),
):
    return await ReportingService.run_cases_by_type_status(db)


@router.get(
    "/canned/children-placement",
    dependencies=[Depends(require_permission(Permissions.REPORT_READ))],
)
async def get_children_in_placement_report(
    db: AsyncSession = Depends(get_db),
):
    return await ReportingService.run_children_in_placement_report(db)


@router.get(
    "/canned/financial-summary",
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_READ))],
)
async def get_financial_summary_report(
    db: AsyncSession = Depends(get_db),
):
    return await ReportingService.run_financial_summary_report(db)


# ── Resource Unit Canned Reports (Sprint 3) ────────────────────
@router.get("/canned/resource-directory")
async def get_resource_directory_report(
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    can_contact = bool(
        user_perms
        & {
            Permissions.RESOURCE_HOME_READ,
            Permissions.PLACEMENT_HOME_READ,
            Permissions.PLACEMENT_HOME_CONTACT_READ,
        }
    )
    return await ResourceReportsService.run_home_directory_report(db, can_read_contact=can_contact)


@router.get("/canned/resource-capacity")
async def get_resource_capacity_report(
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    return await ResourceReportsService.run_available_capacity_report(db)


@router.get("/canned/resource-recruitment")
async def get_resource_recruitment_report(
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    return await ResourceReportsService.run_recruitment_conversion_report(db)


@router.get("/canned/resource-compliance-expiring")
async def get_resource_compliance_expiring_report(
    days_ahead: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    return await ResourceReportsService.run_compliance_expiring_report(db, days_ahead=days_ahead)


@router.get("/canned/resource-training-compliance")
async def get_resource_training_compliance_report(
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    return await ResourceReportsService.run_caregiver_training_report(db)


@router.get("/canned/resource-licensing-renewal")
async def get_resource_licensing_renewal_report(
    days_ahead: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    return await ResourceReportsService.run_licensing_renewal_report(db, days_ahead=days_ahead)


@router.get("/canned/resource-monitoring")
async def get_resource_monitoring_report(
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    return await ResourceReportsService.run_home_monitoring_report(db)


@router.get("/canned/resource-complaints")
async def get_resource_complaints_report(
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    can_sensitive = Permissions.RESOURCE_COMPLAINT_SENSITIVE_READ in user_perms
    return await ResourceReportsService.run_complaints_report(db, can_read_sensitive=can_sensitive)


@router.get("/canned/resource-supports")
async def get_resource_supports_report(
    db: AsyncSession = Depends(get_db),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    if Permissions.RESOURCE_REPORTING_READ not in user_perms and Permissions.REPORT_READ not in user_perms:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resource reporting permission required.")
    can_financial = bool(
        user_perms & {Permissions.FINANCE_REQUEST_READ, Permissions.FINANCE_INVOICE_READ}
    )
    return await ResourceReportsService.run_caregiver_supports_report(db, can_read_financial=can_financial)



# ── Ad-Hoc Report Engine ───────────────────────────────────────
@router.post(
    "/adhoc",
    dependencies=[Depends(require_permission(Permissions.REPORT_READ))],
)
async def run_adhoc_report(
    payload: AdHocReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.REPORT_READ)),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    return await ReportingService.run_adhoc_report(
        db,
        dataset_key=payload.dataset_key,
        user_id=current_user.id,
        user_permissions=user_perms,
        fields=payload.fields,
        filters=payload.filters,
        group_by=payload.group_by,
        limit=payload.limit,
        offset=payload.offset,
    )


# ── Saved Reports ──────────────────────────────────────────────
@router.get(
    "/saved",
    response_model=list[SavedReportResponse],
    dependencies=[Depends(require_permission(Permissions.REPORT_READ))],
)
async def list_saved_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.REPORT_READ)),
):
    return await ReportingQARepository.get_saved_reports(db, user_id=current_user.id)


@router.post(
    "/saved",
    response_model=SavedReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.REPORT_SAVE))],
)
async def create_saved_report(
    payload: SavedReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.REPORT_SAVE)),
):
    return await ReportingService.create_saved_report(db, payload.model_dump(), current_user.id)


@router.post(
    "/saved/{report_id}/run",
    dependencies=[Depends(require_permission(Permissions.REPORT_READ))],
)
async def run_saved_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.REPORT_READ)),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    return await ReportingService.run_saved_report(
        db, report_id=report_id, user_id=current_user.id, user_permissions=user_perms
    )


@router.delete(
    "/saved/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permissions.REPORT_SAVE))],
)
async def delete_saved_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.REPORT_SAVE)),
):
    report = await ReportingQARepository.get_saved_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved report not found")
    if report.owner_user_id != current_user.id and "admin.configuration.manage" not in current_user.permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete other user's report")

    await ReportingQARepository.delete_saved_report(db, report, current_user.id)


# ── Report Export ──────────────────────────────────────────────
@router.post(
    "/export",
    dependencies=[Depends(require_permission(Permissions.REPORT_EXPORT))],
)
async def export_report(
    payload: ReportExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.REPORT_EXPORT)),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    res_data = await ReportingService.run_adhoc_report(
        db,
        dataset_key=payload.dataset_key,
        user_id=current_user.id,
        user_permissions=user_perms,
        fields=payload.fields,
        filters=payload.filters,
        limit=5000,
    )

    fmt = (payload.export_format or "XLSX").upper()
    if fmt == "CSV":
        content = ReportingService.generate_csv_export(res_data)
        media_type = "text/csv"
        filename = f"crbcl-report-{payload.dataset_key}-{date.today()}.csv"
    else:
        content = ReportingService.generate_xlsx_export(res_data)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"crbcl-report-{payload.dataset_key}-{date.today()}.xlsx"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

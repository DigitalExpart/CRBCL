"""API v1 router bundle."""

from fastapi import APIRouter

from app.api.v1.active_efforts import router as active_efforts_router
from app.api.v1.assessment_templates import router as assessment_templates_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.background_checks import router as background_checks_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.case_notes import router as case_notes_router
from app.api.v1.cases import router as cases_router
from app.api.v1.clients import router as clients_router
from app.api.v1.court_events import router as court_events_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.families import router as families_router
from app.api.v1.finance import router as finance_router
from app.api.v1.fleet import router as fleet_router
from app.api.v1.health import router as health_router
from app.api.v1.households import router as households_router
from app.api.v1.lookups import router as lookups_router
from app.api.v1.notification_preferences import router as notification_preferences_router
from app.api.v1.notification_templates import router as notification_templates_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.passports import router as passports_router
from app.api.v1.permanency_plans import router as permanency_plans_router
from app.api.v1.placement_homes import router as placement_homes_router
from app.api.v1.placements import router as placements_router
from app.api.v1.plans import router as plans_router
from app.api.v1.providers import router as providers_router
from app.api.v1.qa import router as qa_router
from app.api.v1.referrals import router as referrals_router
from app.api.v1.removals import router as removals_router
from app.api.v1.reporting import router as reporting_router
from app.api.v1.schools import router as schools_router
from app.api.v1.staffing import router as staffing_router
from app.api.v1.teams import router as teams_router
from app.api.v1.users import router as users_router
from app.auth.router import router as auth_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(referrals_router)
api_v1_router.include_router(clients_router)
api_v1_router.include_router(families_router)
api_v1_router.include_router(households_router)
api_v1_router.include_router(providers_router)
api_v1_router.include_router(schools_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(case_notes_router)
api_v1_router.include_router(assessment_templates_router)
api_v1_router.include_router(assessments_router)
api_v1_router.include_router(plans_router)
api_v1_router.include_router(active_efforts_router)
api_v1_router.include_router(background_checks_router)
api_v1_router.include_router(court_events_router)
api_v1_router.include_router(permanency_plans_router)
api_v1_router.include_router(placement_homes_router)
api_v1_router.include_router(placements_router)
api_v1_router.include_router(removals_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(teams_router)
api_v1_router.include_router(lookups_router)
api_v1_router.include_router(calendar_router)
api_v1_router.include_router(staffing_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(notification_preferences_router)
api_v1_router.include_router(notification_templates_router)
api_v1_router.include_router(finance_router)
api_v1_router.include_router(reporting_router)
api_v1_router.include_router(qa_router)
api_v1_router.include_router(passports_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(fleet_router)


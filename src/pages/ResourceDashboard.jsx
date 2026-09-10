import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Home,
  Users,
  Bed,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  PlusCircle,
  Calendar,
  Layers,
  Sparkles,
  ShieldAlert,
  GraduationCap,
  Wrench,
  Search,
  HeartHandshake,
  DollarSign,
  TrendingUp,
  FileWarning,
} from 'lucide-react';
import resourceRecruitmentApi from '../api/resourceRecruitment';

export default function ResourceDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const res = await resourceRecruitmentApi.getDashboard();
        setMetrics(res.data);
      } catch (err) {
        console.error('Failed to load Resource Team dashboard:', err);
        setError('Unable to load authoritative Resource Unit metrics.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const stageOrder = [
    { key: 'INQUIRY', label: 'Inquiry', color: 'bg-blue-50 text-blue-700 border-blue-200' },
    { key: 'ORIENTATION', label: 'Orientation', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
    { key: 'APPLICATION', label: 'Application', color: 'bg-purple-50 text-purple-700 border-purple-200' },
    { key: 'ASSESSMENT', label: 'Assessment', color: 'bg-amber-50 text-amber-700 border-amber-200' },
    { key: 'APPROVAL_REVIEW', label: 'Approval Review', color: 'bg-orange-50 text-orange-700 border-orange-200' },
    { key: 'APPROVED', label: 'Approved', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    { key: 'ON_HOLD', label: 'On Hold', color: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
    { key: 'DECLINED', label: 'Declined', color: 'bg-rose-50 text-rose-700 border-rose-200' },
    { key: 'WITHDRAWN', label: 'Withdrawn', color: 'bg-slate-50 text-slate-700 border-slate-200' },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Resource Team Operational Dashboard</h1>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              <Sparkles className="w-3 h-3" /> Live Telemetry
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Authoritative resource home capacity, caregiver recruitment pipeline, and renewal monitoring.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/resource-team/matching"
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <Search className="w-4 h-4" />
            Placement Matching
          </Link>
          <Link
            to="/resource-team/recruitment/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            New Inquiry / Application
          </Link>
          <Link
            to="/resource-team/recruitment"
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <Layers className="w-4 h-4" />
            Recruitment Pipeline
          </Link>
          <Link
            to="/placement-homes"
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <Home className="w-4 h-4" />
            Resource Homes
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-500 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 animate-pulse">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-gray-100 dark:bg-gray-800 rounded-xl" />
          ))}
        </div>
      ) : metrics ? (
        <>
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Active Homes */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Active Resource Homes</span>
                <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600">
                  <Home className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-bold text-gray-900 dark:text-white">
                  {metrics.active_resource_homes}
                </span>
                <span className="text-xs text-gray-500">homes in service</span>
              </div>
              <p className="text-xs text-gray-400 mt-2">Authoritative PlacementHome records</p>
            </div>

            {/* Available Beds */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Available Beds</span>
                <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600">
                  <Bed className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-bold text-emerald-600">
                  {metrics.available_beds}
                </span>
                <span className="text-xs text-gray-500">
                  / {metrics.total_capacity} total capacity
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Derived: {metrics.active_placements} active placement{metrics.active_placements !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Awaiting Review */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Awaiting Action/Review</span>
                <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-900/30 text-amber-600">
                  <Clock className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-bold text-amber-600">
                  {metrics.applications_awaiting_review}
                </span>
                <span className="text-xs text-gray-500">applications</span>
              </div>
              <p className="text-xs text-gray-400 mt-2">Application, assessment & review stages</p>
            </div>

            {/* Upcoming Renewals */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Upcoming Renewals</span>
                <div className="p-2 rounded-lg bg-rose-50 dark:bg-rose-900/30 text-rose-600">
                  <Calendar className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-bold text-rose-600">
                  {metrics.upcoming_home_renewals}
                </span>
                <span className="text-xs text-gray-500">licenses expiring in 90 days</span>
              </div>
              <p className="text-xs text-gray-400 mt-2">Placement home licensing audit</p>
            </div>
          </div>

          {/* Sprint 2: Authoritative Compliance Telemetry */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white">Resource Home Compliance Telemetry</h2>
                  {metrics.non_compliant_homes_count > 0 ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
                      <AlertTriangle className="w-3 h-3 text-rose-600" /> {metrics.non_compliant_homes_count} Non-Compliant Home{metrics.non_compliant_homes_count !== 1 ? 's' : ''}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> All Active Homes Fully Compliant
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  Live monitoring of caregiver background clearances, mandatory training certifications, annual inspections, and corrective actions.
                </p>
              </div>
              <Link
                to="/placement-homes"
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700"
              >
                Inspect Homes <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Screening & Clearances */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">Clearances & Screenings</span>
                  <div className={`p-1.5 rounded-lg ${metrics.clearances_expired > 0 ? 'bg-rose-100 text-rose-700' : 'bg-slate-200 text-slate-700'}`}>
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <div>
                    <span className="text-2xl font-bold text-slate-900 dark:text-white">{metrics.clearances_expiring_30_days}</span>
                    <span className="text-xs text-slate-500 ml-1.5">due in 30d</span>
                  </div>
                  {metrics.clearances_expired > 0 && (
                    <span className="text-xs font-bold text-rose-600 bg-rose-50 dark:bg-rose-900/30 px-2 py-0.5 rounded">
                      {metrics.clearances_expired} expired
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500">CRC, VSC, CARC, Driver Abstract</p>
              </div>

              {/* Caregiver Training */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">Training Certifications</span>
                  <div className={`p-1.5 rounded-lg ${metrics.training_expired > 0 ? 'bg-rose-100 text-rose-700' : 'bg-slate-200 text-slate-700'}`}>
                    <GraduationCap className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <div>
                    <span className="text-2xl font-bold text-slate-900 dark:text-white">{metrics.training_due_30_days}</span>
                    <span className="text-xs text-slate-500 ml-1.5">due in 30d</span>
                  </div>
                  {metrics.training_expired > 0 && (
                    <span className="text-xs font-bold text-rose-600 bg-rose-50 dark:bg-rose-900/30 px-2 py-0.5 rounded">
                      {metrics.training_expired} expired
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500">PRIDE, CPR/First Aid, Trauma, Cultural Safety</p>
              </div>

              {/* Inspections Overdue */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">Home Inspections</span>
                  <div className={`p-1.5 rounded-lg ${metrics.inspections_overdue > 0 ? 'bg-amber-100 text-amber-700' : 'bg-slate-200 text-slate-700'}`}>
                    <Calendar className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <div>
                    <span className={`text-2xl font-bold ${metrics.inspections_overdue > 0 ? 'text-amber-600' : 'text-slate-900 dark:text-white'}`}>
                      {metrics.inspections_overdue}
                    </span>
                    <span className="text-xs text-slate-500 ml-1.5">overdue</span>
                  </div>
                  <span className="text-xs text-slate-400">Annual review</span>
                </div>
                <p className="text-[11px] text-slate-500">Physical safety & environment inspection</p>
              </div>

              {/* Outstanding Corrective Actions */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">Corrective Actions</span>
                  <div className={`p-1.5 rounded-lg ${metrics.outstanding_corrective_actions > 0 ? 'bg-rose-100 text-rose-700' : 'bg-slate-200 text-slate-700'}`}>
                    <Wrench className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <div>
                    <span className={`text-2xl font-bold ${metrics.outstanding_corrective_actions > 0 ? 'text-rose-600' : 'text-slate-900 dark:text-white'}`}>
                      {metrics.outstanding_corrective_actions}
                    </span>
                    <span className="text-xs text-slate-500 ml-1.5">pending</span>
                  </div>
                  <span className="text-xs text-slate-400">Deficiencies</span>
                </div>
                <p className="text-[11px] text-slate-500">Remediation plans requiring resolution</p>
              </div>
            </div>
          </div>

          {/* Sprint 3: Care Quality, Monitoring & Safeguards Telemetry */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white">Resource Home Safeguards & Caregiver Support</h2>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
                    Continuous Monitoring & Safeguards
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  Periodic home monitoring visits, complaints management, active caregiver supports, and placement stability.
                </p>
              </div>
              <Link
                to="/resource-team/matching"
                className="inline-flex items-center gap-1 text-sm font-medium text-emerald-600 hover:text-emerald-700"
              >
                Placement Matching Engine <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Monitoring Visits */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">Periodic Monitoring</span>
                  <div className={`p-1.5 rounded-lg ${metrics.monitoring_overdue > 0 ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                    <Calendar className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <div>
                    <span className="text-2xl font-bold text-slate-900 dark:text-white">{metrics.monitoring_due_30_days ?? 0}</span>
                    <span className="text-xs text-slate-500 ml-1.5">due in 30d</span>
                  </div>
                  {metrics.monitoring_overdue > 0 && (
                    <span className="text-xs font-bold text-rose-600 bg-rose-50 dark:bg-rose-900/30 px-2 py-0.5 rounded">
                      {metrics.monitoring_overdue} overdue
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500">Monthly/quarterly ongoing caregiver contact</p>
              </div>

              {/* Complaints & Investigations */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">Complaints & Inquiries</span>
                  <div className={`p-1.5 rounded-lg ${(metrics.open_complaints_count || 0) > 0 ? 'bg-rose-100 text-rose-700' : 'bg-slate-200 text-slate-700'}`}>
                    <FileWarning className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <div>
                    <span className="text-2xl font-bold text-slate-900 dark:text-white">{metrics.open_complaints_count ?? 0}</span>
                    <span className="text-xs text-slate-500 ml-1.5">open complaints</span>
                  </div>
                  {(metrics.active_investigations_count || 0) > 0 && (
                    <span className="text-xs font-bold text-amber-700 bg-amber-50 dark:bg-amber-900/30 px-2 py-0.5 rounded">
                      {metrics.active_investigations_count} under investigation
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500">Privileged records & privacy-protected workflow</p>
              </div>

              {/* Caregiver Supports */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">Caregiver Supports</span>
                  <div className="p-1.5 rounded-lg bg-indigo-100 text-indigo-700">
                    <HeartHandshake className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <div>
                    <span className="text-2xl font-bold text-slate-900 dark:text-white">{metrics.caregiver_supports_active ?? 0}</span>
                    <span className="text-xs text-slate-500 ml-1.5">active provisions</span>
                  </div>
                  <span className="text-xs text-indigo-600 font-medium">Respite & Clinical</span>
                </div>
                <p className="text-[11px] text-slate-500">Linked to Finance Service Requests</p>
              </div>

              {/* Retention & Stability */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">Stability & Longevity</span>
                  <div className="p-1.5 rounded-lg bg-emerald-100 text-emerald-700">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <div>
                    <span className="text-2xl font-bold text-emerald-600">{metrics.placement_stability_pct ?? 100}%</span>
                    <span className="text-xs text-slate-500 ml-1.5">stability</span>
                  </div>
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    {metrics.active_home_longevity_over_one_year_pct != null
                      ? `${metrics.active_home_longevity_over_one_year_pct}% longevity (>1yr)`
                      : "Longevity: N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-[11px] text-slate-500">
                  <span>Conversion: {metrics.recruitment_conversion_rate_pct ?? 0}%</span>
                  <span className="italic">Cohort Retention: Unavailable</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sprint 3: Authorized Finance View (Rendered only if authorized) */}
          {metrics.finance_summary && (
            <div className="bg-white dark:bg-gray-800 border border-emerald-200 dark:border-emerald-800/50 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700">
                    <DollarSign className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-bold text-gray-900 dark:text-white">Resource Financial Operations</h2>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                        Authorized Finance Role View
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">
                      Authoritative financial ledger integration for foster maintenance rates, invoices, and service requests.
                    </p>
                  </div>
                </div>
                <Link
                  to="/finance"
                  className="inline-flex items-center gap-1 text-sm font-medium text-emerald-600 hover:text-emerald-700"
                >
                  Finance Module <ArrowRight className="w-4 h-4" />
                </Link>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
                <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Active Rate Schedules</div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                    {metrics.finance_summary.active_rates_count} active rates
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">Placement home maintenance per diems</div>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Resource Home Invoices</div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                    ${Number(metrics.finance_summary.total_invoiced_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-[11px] text-amber-600 mt-1">
                    {metrics.finance_summary.unpaid_invoices_count} unpaid / pending approval
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Active Support Service Requests</div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                    ${Number(metrics.finance_summary.total_service_requests_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {metrics.finance_summary.active_service_requests_count} approved service request allocations
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Pipeline Breakdown */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Recruitment Pipeline by Stage</h2>
                <p className="text-xs text-gray-500">
                  Sequential progression: Inquiry &rarr; Orientation &rarr; Application &rarr; Assessment &rarr; Approval Review &rarr; Approved
                </p>
              </div>
              <Link
                to="/resource-team/recruitment"
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700"
              >
                View Pipeline Grid <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-9 gap-3">
              {stageOrder.map((st) => {
                const count = metrics.applications_by_stage?.[st.key] || 0;
                return (
                  <Link
                    key={st.key}
                    to={`/resource-team/recruitment?state=${st.key}`}
                    className={`p-3 rounded-lg border text-center transition-all hover:shadow-md ${st.color}`}
                  >
                    <div className="text-xs font-semibold">{st.label}</div>
                    <div className="text-2xl font-bold mt-1">{count}</div>
                  </Link>
                );
              })}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

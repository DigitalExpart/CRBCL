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
  Sparkles
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

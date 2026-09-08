import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Layers,
  ArrowLeft,
  User,
  Home,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  ShieldCheck,
  Send,
  PauseCircle,
  XCircle,
  Check,
  Info
} from 'lucide-react';
import resourceRecruitmentApi from '../api/resourceRecruitment';
import placementHomesApi from '../api/placementHomes';

export default function RecruitmentDetail() {
  const { id } = useParams();
  const [recruitment, setRecruitment] = useState(null);
  const [homes, setHomes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Transition form modal/state
  const [selectedTargetState, setSelectedTargetState] = useState('');
  const [transitionNotes, setTransitionNotes] = useState('');
  const [selectedHomeId, setSelectedHomeId] = useState('');

  const loadDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await resourceRecruitmentApi.get(id);
      setRecruitment(res.data);

      // Load placement homes for allocation option
      try {
        const homesRes = await placementHomesApi.list({ limit: 100 });
        setHomes(homesRes.data?.items || homesRes.data || []);
      } catch (hErr) {
        console.warn('Failed to load placement homes list:', hErr);
      }
    } catch (err) {
      console.error('Failed to load recruitment application:', err);
      setError('Unable to load recruitment application details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [id]);

  const progressionMap = {
    INQUIRY: 'ORIENTATION',
    ORIENTATION: 'APPLICATION',
    APPLICATION: 'ASSESSMENT',
    ASSESSMENT: 'APPROVAL_REVIEW',
    APPROVAL_REVIEW: 'APPROVED',
  };

  const handleTransition = async (targetState) => {
    try {
      setSubmitting(true);
      setError(null);
      setSuccessMsg(null);

      const payload = {
        to_state: targetState,
        notes: transitionNotes || undefined,
        resource_home_id: selectedHomeId || undefined,
      };

      const res = await resourceRecruitmentApi.transition(id, payload);
      setRecruitment(res.data);
      setSelectedTargetState('');
      setTransitionNotes('');
      setSelectedHomeId('');
      setSuccessMsg(`Successfully transitioned application to ${targetState}.`);
    } catch (err) {
      console.error('State transition failed:', err);
      const msg = err.response?.data?.detail || 'Failed to execute transition. Verify allowed progression.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  };

  const getStateBadge = (st) => {
    const map = {
      INQUIRY: 'bg-blue-100 text-blue-800 border-blue-300',
      ORIENTATION: 'bg-indigo-100 text-indigo-800 border-indigo-300',
      APPLICATION: 'bg-purple-100 text-purple-800 border-purple-300',
      ASSESSMENT: 'bg-amber-100 text-amber-800 border-amber-300',
      APPROVAL_REVIEW: 'bg-orange-100 text-orange-800 border-orange-300',
      APPROVED: 'bg-emerald-100 text-emerald-800 border-emerald-300',
      ON_HOLD: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      DECLINED: 'bg-rose-100 text-rose-800 border-rose-300',
      WITHDRAWN: 'bg-slate-100 text-slate-800 border-slate-300',
    };
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold border ${map[st] || 'bg-gray-100 text-gray-800'}`}>
        {st}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="space-y-4 p-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3" />
        <div className="h-40 bg-gray-100 rounded-xl" />
      </div>
    );
  }

  if (error && !recruitment) {
    return (
      <div className="p-6">
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-500" />
          <span>{error}</span>
        </div>
        <div className="mt-4">
          <Link to="/resource-team/recruitment" className="text-sm text-indigo-600 hover:underline">
            &larr; Back to Pipeline
          </Link>
        </div>
      </div>
    );
  }

  const current = recruitment.current_state;
  const isTerminal = current === 'DECLINED' || current === 'WITHDRAWN';
  const isApproved = current === 'APPROVED';
  const nextSequentialState = progressionMap[current];

  return (
    <div className="space-y-6 pb-16">
      {/* Back Link */}
      <div>
        <Link
          to="/resource-team/recruitment"
          className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Recruitment Pipeline
        </Link>
      </div>

      {/* Header Banner */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Recruitment Application
              </h1>
              {getStateBadge(current)}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Application ID: <span className="font-mono text-gray-700 dark:text-gray-300">{recruitment.id}</span> &bull; Initiated {new Date(recruitment.created_at).toLocaleDateString()}
            </p>
          </div>

          {/* Linked Resource Home Status */}
          {recruitment.resource_home_code ? (
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-lg flex items-center gap-3">
              <Home className="w-5 h-5 text-emerald-600" />
              <div>
                <div className="text-xs font-semibold text-emerald-900 dark:text-emerald-300">
                  Allocated Resource Home
                </div>
                <Link
                  to={`/placement-homes/${recruitment.resource_home_id}`}
                  className="text-sm font-bold text-emerald-700 hover:underline"
                >
                  {recruitment.resource_home_code} {recruitment.resource_home_name ? `(${recruitment.resource_home_name})` : ''}
                </Link>
              </div>
            </div>
          ) : (
            <div className="p-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg flex items-center gap-3">
              <Home className="w-5 h-5 text-gray-400" />
              <div className="text-xs text-gray-500">
                Placement Home will be allocated upon approval.
              </div>
            </div>
          )}
        </div>

        {/* Feedback alerts */}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Transition Action Bar */}
        {!isTerminal && !isApproved && (
          <div className="mt-6 pt-5 border-t border-gray-100 dark:border-gray-700">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
              Workflow Actions
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Advance along normal progression */}
              {nextSequentialState && (
                <button
                  disabled={submitting}
                  onClick={() => setSelectedTargetState(nextSequentialState)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                >
                  <Send className="w-3.5 h-3.5" />
                  Advance to {nextSequentialState}
                </button>
              )}

              {/* Resume from ON_HOLD */}
              {current === 'ON_HOLD' && recruitment.previous_state && (
                <button
                  disabled={submitting}
                  onClick={() => setSelectedTargetState(recruitment.previous_state)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                >
                  <Clock className="w-3.5 h-3.5" />
                  Resume to {recruitment.previous_state}
                </button>
              )}

              {/* Place ON_HOLD */}
              {current !== 'ON_HOLD' && (
                <button
                  disabled={submitting}
                  onClick={() => setSelectedTargetState('ON_HOLD')}
                  className="inline-flex items-center gap-1.5 px-3 py-2 border border-yellow-300 bg-yellow-50 hover:bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-lg transition-colors"
                >
                  <PauseCircle className="w-3.5 h-3.5 text-yellow-600" />
                  Place On Hold
                </button>
              )}

              {/* Terminal: DECLINED */}
              <button
                disabled={submitting}
                onClick={() => setSelectedTargetState('DECLINED')}
                className="inline-flex items-center gap-1.5 px-3 py-2 border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold rounded-lg transition-colors"
              >
                <XCircle className="w-3.5 h-3.5 text-rose-600" />
                Decline
              </button>

              {/* Terminal: WITHDRAWN */}
              <button
                disabled={submitting}
                onClick={() => setSelectedTargetState('WITHDRAWN')}
                className="inline-flex items-center gap-1.5 px-3 py-2 border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
              >
                <XCircle className="w-3.5 h-3.5 text-slate-500" />
                Withdraw
              </button>
            </div>

            {/* Transition execution panel */}
            {selectedTargetState && (
              <div className="mt-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-900 border border-indigo-200 dark:border-indigo-800 space-y-3">
                <div className="text-xs font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                  <Info className="w-4 h-4 text-indigo-600" />
                  Confirm transition from <span className="underline">{current}</span> &rarr;{' '}
                  <span className="text-indigo-600 font-extrabold">{selectedTargetState}</span>
                </div>

                {selectedTargetState === 'APPROVED' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Link / Allocate to Placement Home (Optional):
                    </label>
                    <select
                      value={selectedHomeId}
                      onChange={(e) => setSelectedHomeId(e.target.value)}
                      className="w-full text-xs p-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="">-- Allocate existing Placement Home --</option>
                      {homes.map((h) => (
                        <option key={h.id} value={h.id}>
                          {h.home_code} - {h.name} ({h.city})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Transition Notes / Justification:
                  </label>
                  <textarea
                    rows={2}
                    value={transitionNotes}
                    onChange={(e) => setTransitionNotes(e.target.value)}
                    placeholder="Enter reason or notes for this lifecycle event..."
                    className="w-full text-xs p-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <button
                    disabled={submitting}
                    onClick={() => handleTransition(selectedTargetState)}
                    className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded shadow-sm"
                  >
                    {submitting ? 'Applying Transition...' : `Confirm & Move to ${selectedTargetState}`}
                  </button>
                  <button
                    disabled={submitting}
                    onClick={() => {
                      setSelectedTargetState('');
                      setTransitionNotes('');
                    }}
                    className="px-3 py-1.5 border border-gray-300 text-xs text-gray-600 rounded hover:bg-gray-100"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Grid: Applicants & Audit History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Applicants (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
            <h2 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-indigo-600" />
              Applicant Caregiver Profiles
            </h2>

            {recruitment.applicants && recruitment.applicants.length > 0 ? (
              <div className="space-y-4">
                {recruitment.applicants.map((app) => (
                  <div
                    key={app.id}
                    className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30 flex flex-col md:flex-row md:items-center md:justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-gray-900 dark:text-white">
                          {app.person_name || 'Person ID: ' + app.person_id}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-100 text-indigo-800">
                          {app.role === 'PRIMARY_APPLICANT' ? 'Primary Applicant' : 'Co-Applicant'}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Canonical Person ID: <span className="font-mono text-gray-600">{app.person_id}</span>
                      </div>

                      {app.snapshot && (
                        <div className="mt-2 text-xs text-gray-600 dark:text-gray-400 grid grid-cols-2 gap-x-4 gap-y-1">
                          {app.snapshot.phone && <div>Phone: {app.snapshot.phone}</div>}
                          {app.snapshot.email && <div>Email: {app.snapshot.email}</div>}
                          {app.snapshot.date_of_birth && <div>DOB: {app.snapshot.date_of_birth}</div>}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-gray-400 italic">No applicants attached.</div>
            )}
          </div>

          {/* Notes Card */}
          {recruitment.notes && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-2">
                <FileText className="w-5 h-5 text-indigo-600" />
                Recruitment Notes & Criteria
              </h2>
              <p className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {recruitment.notes}
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Append-Only History (1 col) */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
            <h2 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              Append-Only Audit Trail
            </h2>

            {recruitment.history && recruitment.history.length > 0 ? (
              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200 dark:before:bg-gray-700">
                {recruitment.history.map((h, idx) => (
                  <div key={h.id} className="relative">
                    <div className="absolute -left-[29px] top-1 w-3 h-3 rounded-full bg-indigo-600 border-2 border-white dark:border-gray-900" />
                    <div>
                      <div className="text-xs font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                        <span>{h.from_state}</span>
                        <span className="text-gray-400">&rarr;</span>
                        <span className="text-indigo-600">{h.to_state}</span>
                      </div>
                      <div className="text-[11px] text-gray-500 mt-0.5">
                        {new Date(h.changed_at).toLocaleString()}
                        {h.changed_by_name && ` by ${h.changed_by_name}`}
                      </div>
                      {h.notes && (
                        <div className="mt-1 p-2 rounded bg-gray-50 dark:bg-gray-900 text-[11px] text-gray-700 dark:text-gray-300 border border-gray-100 dark:border-gray-800">
                          {h.notes}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-gray-400 italic">No transition history logged.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

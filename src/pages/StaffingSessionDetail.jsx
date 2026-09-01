import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { staffingApi } from '../api/staffing';
import { casesApi } from '../api/cases';
import { usersApi } from '../api/users';
import {
  Users,
  Calendar,
  Clock,
  MapPin,
  CheckCircle2,
  AlertCircle,
  Plus,
  ArrowLeft,
  UserCheck,
  UserX,
  UserMinus,
  FileText,
  Shield,
  Save,
  Check,
  X,
  RefreshCw,
  FolderOpen,
  Send
} from 'lucide-react';

export default function StaffingSessionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCase, setSelectedCase] = useState(null);
  const [isAddCaseOpen, setIsAddCaseOpen] = useState(false);
  const [isAddAttendeeOpen, setIsAddAttendeeOpen] = useState(false);
  const [isCompleteOpen, setIsCompleteOpen] = useState(false);
  const [availableCases, setAvailableCases] = useState([]);
  const [availableUsers, setAvailableUsers] = useState([]);

  // Case Review Form state
  const [reviewForm, setReviewForm] = useState({
    review_status: 'REVIEWED',
    discussion_summary: '',
    follow_up_required: false,
    follow_up_date: '',
    assigned_worker_id: '',
  });
  const [savingReview, setSavingReview] = useState(false);

  useEffect(() => {
    loadSession();
  }, [id]);

  const loadSession = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await staffingApi.getSession(id);
      setSession(data);
      if (data.cases && data.cases.length > 0 && !selectedCase) {
        handleSelectCase(data.cases[0]);
      }
    } catch (err) {
      console.error('Failed to load session:', err);
      setError('Unable to load staffing session details.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCase = (sc) => {
    setSelectedCase(sc);
    setReviewForm({
      review_status: sc.review_status || 'REVIEWED',
      discussion_summary: sc.discussion_summary || '',
      follow_up_required: !!sc.follow_up_required,
      follow_up_date: sc.follow_up_date || '',
      assigned_worker_id: sc.assigned_worker_id || '',
    });
  };

  const handleUpdateReview = async (e) => {
    e.preventDefault();
    if (!selectedCase) return;
    setSavingReview(true);
    try {
      const updated = await staffingApi.updateCaseReview(session.id, selectedCase.case_id, reviewForm);
      setSession(prev => ({
        ...prev,
        cases: prev.cases.map(c => c.id === updated.id ? updated : c),
      }));
      setSelectedCase(updated);
    } catch (err) {
      console.error('Failed to save review:', err);
      alert('Failed to save case review.');
    } finally {
      setSavingReview(false);
    }
  };

  const handleToggleAttendance = async (attendee, newStatus) => {
    try {
      const updated = await staffingApi.addAttendee(session.id, {
        user_id: attendee.user_id,
        attendance_status: newStatus,
      });
      setSession(prev => ({
        ...prev,
        attendees: prev.attendees.map(a => a.id === updated.id ? updated : a),
      }));
    } catch (err) {
      console.error('Failed to update attendance:', err);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-500 text-sm flex flex-col items-center gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-500/80" />
        <span>Loading staffing conference console...</span>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-3xl">
        <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white mb-2">{error || 'Session Not Found'}</h3>
        <button
          onClick={() => navigate('/staffing')}
          className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700"
        >
          Return to Staffing Hub
        </button>
      </div>
    );
  }

  const isCompleted = session.status === 'COMPLETED';

  return (
    <div className="space-y-6">
      {/* Back Button & Banner */}
      <button
        type="button"
        onClick={() => navigate('/staffing')}
        className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Staffing Facilitator</span>
      </button>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-slate-900/60 p-6 rounded-3xl border border-slate-800 backdrop-blur-xl shadow-xl">
        <div className="flex items-start gap-4">
          <div className="p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0 mt-1">
            <Users className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-white tracking-tight">{session.title}</h1>
              <span className={`px-3 py-0.5 rounded-full text-xs font-bold ${
                isCompleted ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' :
                session.status === 'IN_PROGRESS' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' :
                'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
              }`}>
                {session.status}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs text-slate-400 mt-2">
              <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                <Calendar className="w-4 h-4 text-slate-500" />
                {new Date(session.session_date).toLocaleString([], { dateStyle: 'full', timeStyle: 'short' })}
              </span>
              {session.location && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-4 h-4 text-slate-500" />
                  {session.location}
                </span>
              )}
              {session.facilitator_name && (
                <span>Facilitator: <strong className="text-slate-200">{session.facilitator_name}</strong></span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!isCompleted && (
            <button
              type="button"
              onClick={() => setIsCompleteOpen(true)}
              className="px-5 py-2.5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Finalize &amp; Complete Session</span>
            </button>
          )}
        </div>
      </div>

      {/* Main 2-Column Console */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Attendee Roll Call + Case Roster */}
        <div className="lg:col-span-5 space-y-6">
          {/* Attendee Roster Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-indigo-400" />
                <span>Attendee Roll Call ({session.attendees?.length || 0})</span>
              </h3>
              {!isCompleted && (
                <button
                  type="button"
                  onClick={async () => {
                    const uRes = await usersApi.listUsers({ is_active: true, page_size: 100 }).catch(() => ({ items: [] }));
                    setAvailableUsers(uRes.items || uRes || []);
                    setIsAddAttendeeOpen(true);
                  }}
                  className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Attendee</span>
                </button>
              )}
            </div>

            <div className="divide-y divide-slate-800/60 max-h-56 overflow-y-auto">
              {session.attendees?.map((att) => (
                <div key={att.id} className="py-2.5 flex items-center justify-between gap-2 text-xs">
                  <div>
                    <span className="font-semibold text-white block">{att.user_name || att.user_email}</span>
                    <span className="text-[10px] text-slate-500">{att.notes || 'Multi-disciplinary participant'}</span>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      disabled={isCompleted}
                      onClick={() => handleToggleAttendance(att, 'ATTENDED')}
                      title="Mark Attended"
                      className={`p-1.5 rounded-lg text-xs transition-colors ${
                        att.attendance_status === 'ATTENDED'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'text-slate-500 hover:bg-slate-800'
                      }`}
                    >
                      <UserCheck className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      disabled={isCompleted}
                      onClick={() => handleToggleAttendance(att, 'ABSENT')}
                      title="Mark Absent"
                      className={`p-1.5 rounded-lg text-xs transition-colors ${
                        att.attendance_status === 'ABSENT'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'text-slate-500 hover:bg-slate-800'
                      }`}
                    >
                      <UserX className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      disabled={isCompleted}
                      onClick={() => handleToggleAttendance(att, 'EXCUSED')}
                      title="Mark Excused"
                      className={`p-1.5 rounded-lg text-xs transition-colors ${
                        att.attendance_status === 'EXCUSED'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'text-slate-500 hover:bg-slate-800'
                      }`}
                    >
                      <UserMinus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Case Review Queue */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-amber-400" />
                <span>Case Review Roster ({session.cases?.length || 0})</span>
              </h3>
              {!isCompleted && (
                <button
                  type="button"
                  onClick={async () => {
                    const cRes = await casesApi.listCases({ page: 1, page_size: 50 });
                    setAvailableCases(cRes.items || []);
                    setIsAddCaseOpen(true);
                  }}
                  className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Case</span>
                </button>
              )}
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {session.cases?.map((sc) => {
                const isSelected = selectedCase?.id === sc.id;
                return (
                  <div
                    key={sc.id}
                    onClick={() => handleSelectCase(sc)}
                    className={`p-3.5 rounded-2xl border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-amber-500/10 border-amber-500/40 ring-1 ring-amber-500/20'
                        : 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="font-mono font-bold text-amber-400">{sc.case_number}</span>
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                        sc.review_status === 'REVIEWED' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' :
                        sc.review_status === 'ESCALATED' ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30' :
                        'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}>
                        {sc.review_status}
                      </span>
                    </div>
                    <p className="font-semibold text-white truncate">{sc.case_title}</p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1.5">
                      <span>Worker: {sc.assigned_worker_name || 'Unassigned'}</span>
                      {sc.follow_up_required && (
                        <span className="text-amber-400 font-semibold">Follow-up set</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Active Case Review Workbench */}
        <div className="lg:col-span-7">
          {selectedCase ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-6">
              <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-amber-400">{selectedCase.case_number}</span>
                    <span className="text-sm font-bold text-white">{selectedCase.case_title}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">Record conference deliberations, safety assessments, and assigned actions</p>
                </div>
                <button
                  type="button"
                  onClick={() => navigate(`/cases/${selectedCase.case_id}`)}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-semibold transition-colors flex items-center gap-1"
                >
                  <FolderOpen className="w-3.5 h-3.5" />
                  <span>Open Full Case</span>
                </button>
              </div>

              <form onSubmit={handleUpdateReview} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Review Disposition *</label>
                    <select
                      disabled={isCompleted}
                      value={reviewForm.review_status}
                      onChange={(e) => setReviewForm({ ...reviewForm, review_status: e.target.value })}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40"
                    >
                      <option value="REVIEWED">Reviewed &amp; Approved</option>
                      <option value="PENDING">Pending Deliberation</option>
                      <option value="DEFERRED">Deferred (Need Documentation)</option>
                      <option value="ESCALATED">Escalated to Director</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Follow-Up Date</label>
                    <input
                      type="date"
                      disabled={isCompleted || !reviewForm.follow_up_required}
                      value={reviewForm.follow_up_date}
                      onChange={(e) => setReviewForm({ ...reviewForm, follow_up_date: e.target.value })}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40 disabled:opacity-40"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="follow_up_required"
                    disabled={isCompleted}
                    checked={reviewForm.follow_up_required}
                    onChange={(e) => setReviewForm({ ...reviewForm, follow_up_required: e.target.checked })}
                    className="w-4 h-4 rounded text-amber-500 bg-slate-800 border-slate-700 focus:ring-amber-500/40"
                  />
                  <label htmlFor="follow_up_required" className="text-xs font-medium text-slate-300 cursor-pointer">
                    Mandatory Follow-up Action Required
                  </label>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Discussion &amp; Safety Review Summary *</label>
                  <textarea
                    rows={6}
                    disabled={isCompleted}
                    value={reviewForm.discussion_summary}
                    onChange={(e) => setReviewForm({ ...reviewForm, discussion_summary: e.target.value })}
                    placeholder="Document child wellness, safety plan efficacy, cultural connection progress, and next steps..."
                    className="w-full px-4 py-3 rounded-2xl bg-slate-800 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/40 resize-none leading-relaxed"
                  />
                </div>

                {!isCompleted && (
                  <div className="flex justify-end pt-2">
                    <button
                      type="submit"
                      disabled={savingReview}
                      className="px-5 py-2.5 rounded-2xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-amber-500/20 flex items-center gap-2 disabled:opacity-50"
                    >
                      <Save className="w-4 h-4" />
                      <span>{savingReview ? 'Saving...' : 'Save Case Review'}</span>
                    </button>
                  </div>
                )}
              </form>
            </div>
          ) : (
            <div className="py-24 text-center bg-slate-900/40 border border-slate-800 rounded-3xl p-8 flex flex-col items-center gap-3">
              <FileText className="w-12 h-12 text-slate-700" />
              <h4 className="text-sm font-semibold text-slate-300">No Case Selected</h4>
              <p className="text-xs text-slate-500">Select a case from the review roster on the left to document deliberations.</p>
            </div>
          )}
        </div>
      </div>

      {/* Complete Session Modal */}
      {isCompleteOpen && (
        <CompleteStaffingModal
          session={session}
          onClose={() => setIsCompleteOpen(false)}
          onCompleted={(updated) => {
            setSession(updated);
            setIsCompleteOpen(false);
          }}
        />
      )}

      {/* Add Case Modal */}
      {isAddCaseOpen && (
        <AddCaseModal
          isOpen={isAddCaseOpen}
          sessionId={session.id}
          cases={availableCases}
          onClose={() => setIsAddCaseOpen(false)}
          onAdded={(newSc) => {
            setSession(prev => ({ ...prev, cases: [...(prev.cases || []), newSc] }));
            setIsAddCaseOpen(false);
          }}
        />
      )}

      {/* Add Attendee Modal */}
      {isAddAttendeeOpen && (
        <AddAttendeeModal
          isOpen={isAddAttendeeOpen}
          sessionId={session.id}
          users={availableUsers}
          onClose={() => setIsAddAttendeeOpen(false)}
          onAdded={(newAtt) => {
            setSession(prev => ({ ...prev, attendees: [...(prev.attendees || []), newAtt] }));
            setIsAddAttendeeOpen(false);
          }}
        />
      )}
    </div>
  );
}

function CompleteStaffingModal({ session, onClose, onCompleted }) {
  const [minutes, setMinutes] = useState(session.minutes || '');
  const [submitting, setSubmitting] = useState(false);

  const handleComplete = async () => {
    setSubmitting(true);
    try {
      const res = await staffingApi.completeSession(session.id, minutes);
      onCompleted(res);
    } catch (err) {
      console.error('Failed to complete session:', err);
      alert('Failed to finalize staffing session.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Finalize Staffing Conference</h3>
            <p className="text-xs text-slate-400">Lock reviews and update derived last-staffed metrics</p>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Formal Conference Minutes</label>
          <textarea
            rows={4}
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            placeholder="Record general notes, attendance remarks, and conference adjournment time..."
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/40 resize-none"
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={handleComplete}
            className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-emerald-500/20"
          >
            {submitting ? 'Finalizing...' : 'Confirm & Complete'}
          </button>
        </div>
      </div>
    </div>
  );
}

function AddCaseModal({ isOpen, sessionId, cases, onClose, onAdded }) {
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleAdd = async () => {
    if (!selectedCaseId) return;
    setSubmitting(true);
    try {
      const res = await staffingApi.addCase(sessionId, {
        case_id: selectedCaseId,
        review_status: 'PENDING',
      });
      onAdded(res);
    } catch (err) {
      console.error('Failed to add case to session:', err);
      alert('Failed to add case to roster.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md shadow-2xl p-6 space-y-4">
        <h3 className="text-base font-bold text-white">Add Case to Review Roster</h3>
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Select Case</label>
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          >
            <option value="">Choose Case...</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.case_number} - {c.title?.substring(0, 30)}...
              </option>
            ))}
          </select>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700">
            Cancel
          </button>
          <button
            type="button"
            disabled={!selectedCaseId || submitting}
            onClick={handleAdd}
            className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold disabled:opacity-50"
          >
            {submitting ? 'Adding...' : 'Add to Roster'}
          </button>
        </div>
      </div>
    </div>
  );
}

function AddAttendeeModal({ isOpen, sessionId, users, onClose, onAdded }) {
  const [selectedUserId, setSelectedUserId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleAdd = async () => {
    if (!selectedUserId) return;
    setSubmitting(true);
    try {
      const res = await staffingApi.addAttendee(sessionId, {
        user_id: selectedUserId,
        attendance_status: 'PENDING',
      });
      onAdded(res);
    } catch (err) {
      console.error('Failed to add attendee:', err);
      alert('Failed to add attendee.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md shadow-2xl p-6 space-y-4">
        <h3 className="text-base font-bold text-white">Add Staffing Participant</h3>
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Select User / Staff Member</label>
          <select
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          >
            <option value="">Choose Staff Member...</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name || u.email}
              </option>
            ))}
          </select>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700">
            Cancel
          </button>
          <button
            type="button"
            disabled={!selectedUserId || submitting}
            onClick={handleAdd}
            className="px-5 py-2 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-bold disabled:opacity-50"
          >
            {submitting ? 'Adding...' : 'Add Participant'}
          </button>
        </div>
      </div>
    </div>
  );
}

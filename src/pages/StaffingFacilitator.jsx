import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { staffingApi } from '../api/staffing';
import { teamsApi } from '../api/teams';
import { usersApi } from '../api/users';
import {
  Users,
  Calendar,
  AlertTriangle,
  Clock,
  Flame,
  FileWarning,
  Plus,
  ChevronRight,
  X,
  RefreshCw
} from 'lucide-react';

export default function StaffingFacilitator() {
  const navigate = useNavigate();
  const [buckets, setBuckets] = useState({
    not_staffed_90_days: [],
    open_12_months: [],
    high_risk: [],
    missing_recent_note: [],
  });
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('triage'); // 'triage' or 'sessions'
  const [selectedBucket, setSelectedBucket] = useState('not_staffed_90_days');
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [teams, setTeams] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedTeamId, setSelectedTeamId] = useState('');

  useEffect(() => {
    loadData();
  }, [selectedTeamId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [bucketsRes, sessionsRes, teamsRes, usersRes] = await Promise.all([
        staffingApi.getCaseBuckets(selectedTeamId || null),
        staffingApi.listSessions({ team_id: selectedTeamId || null, page_size: 20 }),
        teamsApi.listTeams().catch(() => ({ items: [] })),
        usersApi.listUsers({ is_active: true, page_size: 100 }).catch(() => ({ items: [] })),
      ]);

      setBuckets(bucketsRes || {});
      setSessions(sessionsRes.items || []);
      setTeams(teamsRes.items || teamsRes || []);
      setUsers(usersRes.items || usersRes || []);
    } catch (err) {
      console.error('Failed to load staffing data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getBucketCount = (key) => buckets[key]?.length || 0;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-card p-6 rounded-2xl border border-border shadow-sm">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Staffing Facilitator</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 flex items-center gap-1">
              <Users className="w-3 h-3" /> Multi-Disciplinary Case Review
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Automated compliance triage, high-risk case prioritization, and structured conference facilitation
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedTeamId}
            onChange={(e) => setSelectedTeamId(e.target.value)}
            className="px-3.5 py-2.5 rounded-xl bg-background border border-input text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Teams &amp; Units</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={() => setIsScheduleModalOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-bold transition-all shadow-sm flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Schedule Staffing Session</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('triage')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'triage'
              ? 'bg-secondary text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Automated Triage Buckets
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('sessions')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'sessions'
              ? 'bg-secondary text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Staffing Sessions ({sessions.length})
        </button>
      </div>

      {loading ? (
        <div className="py-24 text-center text-muted-foreground text-sm flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-primary" />
          <span>Evaluating automated case triage criteria...</span>
        </div>
      ) : activeTab === 'triage' ? (
        <div className="space-y-6">
          {/* 4 Automated Triage Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Bucket 1 */}
            <div
              onClick={() => setSelectedBucket('not_staffed_90_days')}
              className={`p-5 rounded-2xl border cursor-pointer transition-all shadow-sm ${
                selectedBucket === 'not_staffed_90_days'
                  ? 'bg-amber-500/10 border-amber-500/50 ring-1 ring-amber-500/30'
                  : 'bg-card border-border hover:border-primary/40'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                  <Clock className="w-5 h-5" />
                </span>
                <span className="text-2xl font-bold text-foreground font-mono">
                  {getBucketCount('not_staffed_90_days')}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-foreground">Not Staffed 90+ Days</h4>
              <p className="text-xs text-muted-foreground mt-1">Cases open &gt;90 days without recent formal staffing review</p>
            </div>

            {/* Bucket 2 */}
            <div
              onClick={() => setSelectedBucket('high_risk')}
              className={`p-5 rounded-2xl border cursor-pointer transition-all shadow-sm ${
                selectedBucket === 'high_risk'
                  ? 'bg-rose-500/10 border-rose-500/50 ring-1 ring-rose-500/30'
                  : 'bg-card border-border hover:border-rose-500/40'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="p-2.5 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                  <Flame className="w-5 h-5" />
                </span>
                <span className="text-2xl font-bold text-rose-600 dark:text-rose-400 font-mono">
                  {getBucketCount('high_risk')}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-foreground">High Risk / Safety</h4>
              <p className="text-xs text-muted-foreground mt-1">Immediate safety concerns and elevated risk level</p>
            </div>

            {/* Bucket 3 */}
            <div
              onClick={() => setSelectedBucket('open_12_months')}
              className={`p-5 rounded-2xl border cursor-pointer transition-all shadow-sm ${
                selectedBucket === 'open_12_months'
                  ? 'bg-indigo-500/10 border-indigo-500/50 ring-1 ring-indigo-500/30'
                  : 'bg-card border-border hover:border-indigo-500/40'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                  <AlertTriangle className="w-5 h-5" />
                </span>
                <span className="text-2xl font-bold text-foreground font-mono">
                  {getBucketCount('open_12_months')}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-foreground">Open 12+ Months</h4>
              <p className="text-xs text-muted-foreground mt-1">Long-term matters requiring permanency review</p>
            </div>

            {/* Bucket 4 */}
            <div
              onClick={() => setSelectedBucket('missing_recent_note')}
              className={`p-5 rounded-2xl border cursor-pointer transition-all shadow-sm ${
                selectedBucket === 'missing_recent_note'
                  ? 'bg-sky-500/10 border-sky-500/50 ring-1 ring-sky-500/30'
                  : 'bg-card border-border hover:border-sky-500/40'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="p-2.5 rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20">
                  <FileWarning className="w-5 h-5" />
                </span>
                <span className="text-2xl font-bold text-foreground font-mono">
                  {getBucketCount('missing_recent_note')}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-foreground">Missing Recent Note</h4>
              <p className="text-xs text-muted-foreground mt-1">No progress notes recorded in 30+ days</p>
            </div>
          </div>

          {/* Bucket Cases Table */}
          <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
              <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
                Flagged Cases ({buckets[selectedBucket]?.length || 0})
              </h3>
            </div>

            {(!buckets[selectedBucket] || buckets[selectedBucket].length === 0) ? (
              <div className="py-16 text-center text-muted-foreground text-xs">
                No cases currently flagged in this bucket.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/40 text-muted-foreground border-b border-border">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Case Number</th>
                      <th className="py-3 px-4 font-semibold">Case Title</th>
                      <th className="py-3 px-4 font-semibold">Assigned Worker</th>
                      <th className="py-3 px-4 font-semibold">Stage</th>
                      <th className="py-3 px-4 font-semibold">Last Staffed</th>
                      <th className="py-3 px-4 font-semibold">Risk Level</th>
                      <th className="py-3 px-4 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border text-foreground">
                    {buckets[selectedBucket].map((c) => (
                      <tr key={c.case_id} className="hover:bg-muted/50 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-bold text-primary">
                          {c.case_number}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-foreground max-w-xs truncate">
                          {c.case_title}
                        </td>
                        <td className="py-3.5 px-4 text-muted-foreground">
                          {c.assigned_worker_name || 'Unassigned'}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 rounded-md bg-secondary text-secondary-foreground border border-border text-[10px]">
                            {c.stage}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          {c.last_staffed_date ? (
                            <span className="text-foreground">
                              {new Date(c.last_staffed_date).toLocaleDateString()} ({c.days_since_last_staffed}d ago)
                            </span>
                          ) : (
                            <span className="text-amber-600 dark:text-amber-400 font-medium">Never Staffed</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                            c.risk_level === 'High' ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30' :
                            c.risk_level === 'Medium' ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30' :
                            'bg-secondary text-secondary-foreground'
                          }`}>
                            {c.risk_level || 'Standard'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={() => navigate(`/cases/${c.case_id}`)}
                            className="px-3 py-1 rounded-lg bg-secondary hover:bg-secondary/80 text-secondary-foreground text-[11px] font-medium transition-colors"
                          >
                            View Case
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Sessions List View */
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
              Scheduled &amp; Past Staffing Conferences
            </h3>
          </div>

          {sessions.length === 0 ? (
            <div className="py-16 text-center text-muted-foreground text-xs">
              No staffing sessions scheduled. Click "Schedule Staffing Session" to organize a review.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {sessions.map((sess) => (
                <div
                  key={sess.id}
                  onClick={() => navigate(`/staffing/${sess.id}`)}
                  className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 shrink-0">
                      <Users className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-base font-bold text-foreground">{sess.title}</span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          sess.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' :
                          sess.status === 'IN_PROGRESS' ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20' :
                          'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20'
                        }`}>
                          {sess.status}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground mt-1.5">
                        <span className="flex items-center gap-1 font-semibold text-foreground">
                          <Calendar className="w-3.5 h-3.5 text-muted-foreground" />
                          {new Date(sess.session_date).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                        </span>
                        {sess.facilitator_name && (
                          <span>Facilitator: {sess.facilitator_name}</span>
                        )}
                        <span>{sess.attendees?.length || 0} Attendees</span>
                        <span className="font-semibold text-primary">{sess.cases?.length || 0} Cases in Roster</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="px-3 py-1.5 rounded-xl bg-secondary text-secondary-foreground text-xs font-medium hover:bg-secondary/80 transition-colors flex items-center gap-1"
                    >
                      <span>Open Console</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Schedule Session Modal */}
      {isScheduleModalOpen && (
        <ScheduleSessionModal
          isOpen={isScheduleModalOpen}
          teams={teams}
          users={users}
          onClose={() => setIsScheduleModalOpen(false)}
          onCreated={() => {
            setIsScheduleModalOpen(false);
            loadData();
          }}
        />
      )}
    </div>
  );
}

function ScheduleSessionModal({ isOpen, teams, users, onClose, onCreated }) {
  const [formData, setFormData] = useState({
    title: 'Bi-Weekly Team Staffing Conference',
    session_date: new Date().toISOString().split('T')[0],
    session_time: '10:00',
    team_id: '',
    facilitator_id: '',
    cadence: 'BIWEEKLY',
    location: 'Family Wellness Centre Boardroom',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const dt = new Date(`${formData.session_date}T${formData.session_time}:00`);
      const payload = {
        title: formData.title,
        session_date: dt.toISOString(),
        team_id: formData.team_id || null,
        facilitator_id: formData.facilitator_id || null,
        cadence: formData.cadence,
        location: formData.location,
        status: 'SCHEDULED',
      };

      await staffingApi.createSession(payload);
      onCreated();
    } catch (err) {
      console.error('Failed to create session:', err);
      setError(err.response?.data?.detail || 'Failed to schedule session.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-card border border-border rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="px-6 py-5 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-foreground">Schedule Staffing Session</h3>
              <p className="text-xs text-muted-foreground">Initialize multi-disciplinary review conference</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-300 text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-foreground mb-1">Session Title *</label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-background border border-input text-foreground text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1">Date</label>
              <input
                type="date"
                required
                value={formData.session_date}
                onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-background border border-input text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground mb-1">Start Time</label>
              <input
                type="time"
                required
                value={formData.session_time}
                onChange={(e) => setFormData({ ...formData, session_time: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-background border border-input text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1">Team Unit</label>
              <select
                value={formData.team_id}
                onChange={(e) => setFormData({ ...formData, team_id: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-background border border-input text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">General Unit</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1">Facilitator</label>
              <select
                value={formData.facilitator_id}
                onChange={(e) => setFormData({ ...formData, facilitator_id: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-background border border-input text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Select Supervisor / Lead</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name || u.email}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1">Location / Virtual Meeting</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="e.g., Boardroom 2 / Microsoft Teams"
              className="w-full px-3.5 py-2.5 rounded-xl bg-background border border-input text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-bold transition-all shadow-sm disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Schedule Session'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { reportingApi } from '../api/reporting';
import {
  ClipboardCheck,
  AlertTriangle,
  Clock,
  CheckCircle2,
  FileX,
  Users,
  Plus,
  ArrowRight,
  ShieldCheck,
  Calendar,
} from 'lucide-react';

export default function QADashboard() {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState(null);
  const [tickler, setTickler] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tickler'); // tickler, no_notes

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [mRes, tRes] = await Promise.all([
        reportingApi.getQADashboard(),
        reportingApi.getAuditTickler(),
      ]);
      setMetrics(mRes.data);
      setTickler(tRes.data);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading Quality Assurance Dashboard...</div>;
  }

  const ticklerSummary = tickler?.summary || { ok_count: 0, due_soon_count: 0, overdue_count: 0 };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Quality Assurance & Audit Tickler</h1>
          <p className="text-sm text-muted-foreground">
            Monitor case compliance, review due dates, and track 30+ day case note gaps.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/qa/audits/new')}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Conduct Case Audit
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between text-rose-500">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Overdue Audits
            </span>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="text-3xl font-extrabold text-foreground">{ticklerSummary.overdue_count}</div>
          <div className="text-xs text-muted-foreground">Requires immediate supervisor audit</div>
        </div>

        <div className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between text-amber-500">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Audits Due Soon
            </span>
            <Clock className="w-5 h-5" />
          </div>
          <div className="text-3xl font-extrabold text-foreground">{ticklerSummary.due_soon_count}</div>
          <div className="text-xs text-muted-foreground">Due within the next 14 days</div>
        </div>

        <div className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between text-amber-600">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Cases Without Notes (30d+)
            </span>
            <FileX className="w-5 h-5" />
          </div>
          <div className="text-3xl font-extrabold text-foreground">
            {metrics?.cases_without_notes_count || 0}
          </div>
          <div className="text-xs text-muted-foreground">No completed case notes in 30+ days</div>
        </div>

        <div className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between text-blue-500">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Avg Caseload / Worker
            </span>
            <Users className="w-5 h-5" />
          </div>
          <div className="text-3xl font-extrabold text-foreground">
            {metrics?.average_caseload_per_worker || 0}
          </div>
          <div className="text-xs text-muted-foreground">Active cases per assigned caseworker</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border gap-6">
        <button
          onClick={() => setActiveTab('tickler')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'tickler'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Audit Tickler Status List
        </button>
        <button
          onClick={() => setActiveTab('no_notes')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'no_notes'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Cases Without Notes (30d+)
          {metrics?.cases_without_notes_count > 0 && (
            <span className="px-2 py-0.5 bg-rose-500/10 text-rose-600 rounded-full text-xs font-bold">
              {metrics.cases_without_notes_count}
            </span>
          )}
        </button>
      </div>

      {/* Audit Tickler Table */}
      {activeTab === 'tickler' && (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 bg-muted/30 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-foreground text-sm">
              Quarterly & Monthly Case Audit Cadence Tracker
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/50 text-muted-foreground font-medium border-b border-border text-xs uppercase">
                <tr>
                  <th className="p-4">Case Details</th>
                  <th className="p-4">Last Audit Date</th>
                  <th className="p-4">Next Due Date</th>
                  <th className="p-4">Tickler Status</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {/* Overdue */}
                {tickler?.overdue?.map((c) => (
                  <tr key={c.case_id} className="hover:bg-muted/30 transition-colors bg-rose-500/5">
                    <td className="p-4">
                      <div className="font-bold text-foreground">{c.case_number}</div>
                      <div className="text-xs text-muted-foreground">{c.title}</div>
                    </td>
                    <td className="p-4 text-muted-foreground">{c.last_audit_date || 'Never Audited'}</td>
                    <td className="p-4 font-semibold text-rose-600 dark:text-rose-400">{c.next_due_date}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 bg-rose-500/10 text-rose-600 rounded-full text-xs font-bold inline-flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> OVERDUE ({c.days_overdue || 0}d)
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => navigate('/qa/audits/new')}
                        className="px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:bg-primary/90 transition-colors"
                      >
                        Audit Now
                      </button>
                    </td>
                  </tr>
                ))}

                {/* Due Soon */}
                {tickler?.due_soon?.map((c) => (
                  <tr key={c.case_id} className="hover:bg-muted/30 transition-colors bg-amber-500/5">
                    <td className="p-4">
                      <div className="font-bold text-foreground">{c.case_number}</div>
                      <div className="text-xs text-muted-foreground">{c.title}</div>
                    </td>
                    <td className="p-4 text-muted-foreground">{c.last_audit_date}</td>
                    <td className="p-4 font-semibold text-amber-600 dark:text-amber-400">{c.next_due_date}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 bg-amber-500/10 text-amber-600 rounded-full text-xs font-bold inline-flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" /> DUE SOON ({c.days_until_due}d)
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => navigate('/qa/audits/new')}
                        className="px-3 py-1.5 border border-border text-foreground rounded-md text-xs font-medium hover:bg-muted transition-colors"
                      >
                        Start Audit
                      </button>
                    </td>
                  </tr>
                ))}

                {/* OK */}
                {tickler?.ok?.map((c) => (
                  <tr key={c.case_id} className="hover:bg-muted/30 transition-colors">
                    <td className="p-4">
                      <div className="font-bold text-foreground">{c.case_number}</div>
                      <div className="text-xs text-muted-foreground">{c.title}</div>
                    </td>
                    <td className="p-4 text-muted-foreground">{c.last_audit_date}</td>
                    <td className="p-4 text-muted-foreground">{c.next_due_date}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-600 rounded-full text-xs font-bold inline-flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> OK
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => navigate('/qa/audits')}
                        className="px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
                      >
                        History
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Cases Without Notes Tab */}
      {activeTab === 'no_notes' && (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-foreground text-base">Cases Without Notes (30+ Days Gap)</h3>
          <p className="text-xs text-muted-foreground">
            The following open cases have no locked or completed case notes logged within the last 30 calendar days.
          </p>

          {metrics?.cases_without_notes?.length > 0 ? (
            <div className="divide-y divide-border border border-border rounded-lg">
              {metrics.cases_without_notes.map((c) => (
                <div key={c.case_id} className="p-4 flex items-center justify-between hover:bg-muted/30">
                  <div>
                    <div className="font-bold text-foreground">{c.case_number}</div>
                    <div className="text-xs text-muted-foreground">{c.title}</div>
                  </div>
                  <button
                    onClick={() => navigate(`/cases/${c.case_id}`)}
                    className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                  >
                    View Case <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-emerald-600 dark:text-emerald-400 font-medium text-sm">
              All active cases have recent case notes logged!
            </div>
          )}
        </div>
      )}
    </div>
  );
}

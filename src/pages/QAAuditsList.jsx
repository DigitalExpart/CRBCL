import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { reportingApi } from '../api/reporting';
import { ClipboardCheck, Plus, ArrowLeft, CheckCircle2, Clock } from 'lucide-react';

export default function QAAuditsList() {
  const navigate = useNavigate();
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadAudits();
  }, [statusFilter]);

  const loadAudits = async () => {
    setLoading(true);
    try {
      const res = await reportingApi.getQAAudits({
        status: statusFilter !== 'all' ? statusFilter : undefined,
      });
      setAudits(res.data.items || []);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/qa')}
            className="p-2 border border-border rounded-lg text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Case Quality Assurance Audits</h1>
            <p className="text-sm text-muted-foreground">
              Review completed and pending case audit compliance reviews.
            </p>
          </div>
        </div>

        <button
          onClick={() => navigate('/qa/audits/new')}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" /> Conduct New Audit
        </button>
      </div>

      <div className="flex items-center gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-border rounded-lg text-xs text-foreground focus:outline-none"
        >
          <option value="all">All Audit Statuses</option>
          <option value="DRAFT">Draft Reviews</option>
          <option value="COMPLETED">Completed Audits</option>
        </select>
      </div>

      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">Loading audit records...</div>
        ) : audits.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">No case audits found matching filter.</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/50 text-muted-foreground font-medium border-b border-border text-xs uppercase">
              <tr>
                <th className="p-4">Case Number</th>
                <th className="p-4">Review Date</th>
                <th className="p-4">Reviewer</th>
                <th className="p-4">Status</th>
                <th className="p-4">Compliance Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {audits.map((a) => (
                <tr key={a.id} className="hover:bg-muted/30 transition-colors">
                  <td className="p-4 font-bold text-foreground">{a.case_id.slice(0, 8)}...</td>
                  <td className="p-4 text-muted-foreground">{a.review_date}</td>
                  <td className="p-4 text-muted-foreground">{a.reviewer_id.slice(0, 8)}</td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        a.status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-600'
                          : 'bg-amber-500/10 text-amber-600'
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="p-4 font-extrabold text-primary">
                    {a.overall_score !== null ? `${a.overall_score}%` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

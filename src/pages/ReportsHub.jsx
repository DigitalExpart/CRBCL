import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { reportingApi } from '../api/reporting';
import {
  FileText,
  Plus,
  Play,
  Trash2,
  BarChart3,
  Download,
  Users,
  Building,
  DollarSign,
  Briefcase,
  AlertCircle,
} from 'lucide-react';

export default function ReportsHub() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('canned'); // canned, saved
  const [savedReports, setSavedReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reportResult, setReportResult] = useState(null);
  const [activeCanned, setActiveCanned] = useState(null);

  useEffect(() => {
    if (activeTab === 'saved') {
      loadSavedReports();
    }
  }, [activeTab]);

  const loadSavedReports = async () => {
    setLoading(true);
    try {
      const res = await reportingApi.getSavedReports();
      setSavedReports(res.data || []);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  const handleRunCanned = async (type) => {
    setLoading(true);
    setActiveCanned(type);
    try {
      let res;
      if (type === 'active_cases') {
        res = await reportingApi.getCannedActiveCasesWorker();
      } else if (type === 'cases_type_status') {
        res = await reportingApi.getCannedCasesTypeStatus();
      } else if (type === 'children_placement') {
        res = await reportingApi.getCannedChildrenPlacement();
      } else if (type === 'financial_summary') {
        res = await reportingApi.getCannedFinancialSummary();
      }
      setReportResult(res.data);
    } catch {
      alert('Failed to execute report.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunSaved = async (reportId) => {
    setLoading(true);
    try {
      const res = await reportingApi.runSavedReport(reportId);
      setReportResult(res.data);
      setActiveCanned('saved');
    } catch {
      alert('Failed to execute saved report.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSaved = async (reportId) => {
    if (!confirm('Are you sure you want to delete this saved report?')) return;
    try {
      await reportingApi.deleteSavedReport(reportId);
      loadSavedReports();
    } catch {
      alert('Failed to delete report.');
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Reporting & Analytics Hub</h1>
          <p className="text-sm text-muted-foreground">
            Execute canned organization reports or launch the metadata ad-hoc query builder.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/reports/builder')}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Ad-Hoc Report Builder
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border gap-6">
        <button
          onClick={() => { setActiveTab('canned'); setReportResult(null); }}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'canned'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Canned Standard Reports
        </button>
        <button
          onClick={() => { setActiveTab('saved'); setReportResult(null); }}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'saved'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          My Saved Reports
        </button>
      </div>

      {/* Canned Reports Grid */}
      {activeTab === 'canned' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            onClick={() => handleRunCanned('active_cases')}
            className="p-5 bg-card border border-border rounded-xl hover:border-primary cursor-pointer transition-all shadow-sm space-y-3 group"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-500 group-hover:scale-105 transition-transform">
                <Users className="w-5 h-5" />
              </div>
              <Play className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Active Cases by Worker</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Current active caseload distribution grouped by assigned caseworker.
              </p>
            </div>
          </div>

          <div
            onClick={() => handleRunCanned('cases_type_status')}
            className="p-5 bg-card border border-border rounded-xl hover:border-primary cursor-pointer transition-all shadow-sm space-y-3 group"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-500 group-hover:scale-105 transition-transform">
                <Briefcase className="w-5 h-5" />
              </div>
              <Play className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Cases by Type & Status</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Cross-tabulation matrix of protection, voluntary, and prevention cases.
              </p>
            </div>
          </div>

          <div
            onClick={() => handleRunCanned('children_placement')}
            className="p-5 bg-card border border-border rounded-xl hover:border-primary cursor-pointer transition-all shadow-sm space-y-3 group"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-500 group-hover:scale-105 transition-transform">
                <Building className="w-5 h-5" />
              </div>
              <Play className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Children in Placement</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Active non-discharged children in foster, group, or kinship placements.
              </p>
            </div>
          </div>

          <div
            onClick={() => handleRunCanned('financial_summary')}
            className="p-5 bg-card border border-border rounded-xl hover:border-primary cursor-pointer transition-all shadow-sm space-y-3 group"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-500 group-hover:scale-105 transition-transform">
                <DollarSign className="w-5 h-5" />
              </div>
              <Play className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Financial Summary</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Approved POs, reimbursements, budget lines, and placement billing.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Saved Reports Tab */}
      {activeTab === 'saved' && (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading saved reports...</div>
          ) : savedReports.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No saved reports yet. Create one using the Ad-Hoc Report Builder!
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/50 text-muted-foreground font-medium border-b border-border">
                <tr>
                  <th className="p-4">Report Name</th>
                  <th className="p-4">Dataset</th>
                  <th className="p-4">Visibility</th>
                  <th className="p-4">Created Date</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {savedReports.map((report) => (
                  <tr key={report.id} className="hover:bg-muted/30 transition-colors">
                    <td className="p-4 font-medium text-foreground">{report.name}</td>
                    <td className="p-4 text-muted-foreground uppercase text-xs font-semibold">{report.dataset_key}</td>
                    <td className="p-4">
                      <span className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs">
                        {report.visibility}
                      </span>
                    </td>
                    <td className="p-4 text-muted-foreground">
                      {new Date(report.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-4 text-right space-x-2">
                      <button
                        onClick={() => handleRunSaved(report.id)}
                        className="px-3 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 rounded-md text-xs font-medium transition-colors inline-flex items-center gap-1"
                      >
                        <Play className="w-3.5 h-3.5" /> Run
                      </button>
                      <button
                        onClick={() => handleDeleteSaved(report.id)}
                        className="px-2.5 py-1.5 text-destructive hover:bg-destructive/10 rounded-md text-xs transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Report Result Preview Card */}
      {reportResult && (
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div>
              <h2 className="text-lg font-bold text-foreground">
                {reportResult.report_name || `Dataset: ${reportResult.dataset}`}
              </h2>
              <p className="text-xs text-muted-foreground">
                Total records: {reportResult.total_count || reportResult.total_active_assignments || reportResult.total_placed_children || (reportResult.items ? reportResult.items.length : 0)}
              </p>
            </div>
            <button
              onClick={() => setReportResult(null)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Close Results
            </button>
          </div>

          <pre className="p-4 bg-muted/40 text-foreground text-xs rounded-lg overflow-x-auto max-h-96">
            {JSON.stringify(reportResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

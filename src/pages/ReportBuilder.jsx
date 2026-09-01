import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { reportingApi } from '../api/reporting';
import {
  FileSpreadsheet,
  Download,
  Save,
  Play,
  ArrowLeft,
  CheckSquare,
  Square,
  Filter,
  Layers,
} from 'lucide-react';

export default function ReportBuilder() {
  const navigate = useNavigate();
  const [catalogue, setCatalogue] = useState(null);
  const [selectedDataset, setSelectedDataset] = useState('cases');
  const [selectedFields, setSelectedFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reportResult, setReportResult] = useState(null);

  // Save Modal State
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveDescription, setSaveDescription] = useState('');
  const [saveVisibility, setSaveVisibility] = useState('PRIVATE');

  useEffect(() => {
    loadCatalogue();
  }, []);

  const loadCatalogue = async () => {
    try {
      const res = await reportingApi.getCatalogue();
      setCatalogue(res.data);
      if (res.data && res.data.cases) {
        setSelectedFields(Object.keys(res.data.cases.fields));
      }
    } catch {
      // Handled
    }
  };

  const handleDatasetChange = (dsKey) => {
    setSelectedDataset(dsKey);
    if (catalogue && catalogue[dsKey]) {
      setSelectedFields(Object.keys(catalogue[dsKey].fields));
    } else {
      setSelectedFields([]);
    }
    setReportResult(null);
  };

  const toggleField = (fieldKey) => {
    if (selectedFields.includes(fieldKey)) {
      setSelectedFields(selectedFields.filter((f) => f !== fieldKey));
    } else {
      setSelectedFields([...selectedFields, fieldKey]);
    }
  };

  const handleRunReport = async () => {
    if (!selectedDataset || selectedFields.length === 0) {
      alert('Please select at least one field to query.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        dataset_key: selectedDataset,
        fields: selectedFields,
        limit: 100,
      };
      const res = await reportingApi.runAdhocReport(payload);
      setReportResult(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to run report.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportXlsx = async () => {
    try {
      const blob = await reportingApi.exportReport({
        dataset_key: selectedDataset,
        export_format: 'XLSX',
        fields: selectedFields,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `crbcl-report-${selectedDataset}-${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Export failed. Please try again.');
    }
  };

  const handleSaveReport = async (e) => {
    e.preventDefault();
    if (!saveName.trim()) return;

    try {
      await reportingApi.createSavedReport({
        name: saveName,
        description: saveDescription,
        dataset_key: selectedDataset,
        visibility: saveVisibility,
        configuration: {
          fields: selectedFields,
        },
      });
      setShowSaveModal(false);
      alert('Report configuration saved successfully!');
    } catch {
      alert('Failed to save report configuration.');
    }
  };

  const currentDsInfo = catalogue ? catalogue[selectedDataset] : null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/reports')}
            className="p-2 border border-border rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Metadata Ad-Hoc Report Builder</h1>
            <p className="text-sm text-muted-foreground">
              Select server-whitelisted datasets and fields for safe, real-time database query execution.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {reportResult && (
            <button
              onClick={handleExportXlsx}
              className="flex items-center gap-2 px-4 py-2 border border-border text-foreground rounded-lg text-sm font-medium hover:bg-muted transition-colors"
            >
              <Download className="w-4 h-4" />
              Export XLSX
            </button>
          )}
          <button
            onClick={() => setShowSaveModal(true)}
            className="flex items-center gap-2 px-4 py-2 border border-border text-foreground rounded-lg text-sm font-medium hover:bg-muted transition-colors"
          >
            <Save className="w-4 h-4" />
            Save Report
          </button>
          <button
            onClick={handleRunReport}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {loading ? 'Running Query...' : 'Run Report'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Dataset Selector Column */}
        <div className="bg-card border border-border rounded-xl p-4 space-y-3 shadow-sm">
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            1. Select Dataset
          </h2>
          <div className="space-y-1">
            {catalogue &&
              Object.keys(catalogue).map((dsKey) => (
                <button
                  key={dsKey}
                  onClick={() => handleDatasetChange(dsKey)}
                  className={`w-full text-left p-3 rounded-lg text-sm font-medium transition-colors ${
                    selectedDataset === dsKey
                      ? 'bg-primary/10 text-primary border border-primary/20'
                      : 'text-foreground hover:bg-muted/50'
                  }`}
                >
                  <div className="font-semibold">{catalogue[dsKey].label}</div>
                  <div className="text-xs text-muted-foreground truncate">
                    {catalogue[dsKey].description}
                  </div>
                </button>
              ))}
          </div>
        </div>

        {/* Field Whitelist Column */}
        <div className="md:col-span-3 bg-card border border-border rounded-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div>
              <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                2. Select Fields to Include
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Only server-approved fields for dataset '{selectedDataset}' are displayed.
              </p>
            </div>

            {currentDsInfo && (
              <button
                onClick={() => {
                  const allF = Object.keys(currentDsInfo.fields);
                  setSelectedFields(selectedFields.length === allF.length ? [] : allF);
                }}
                className="text-xs text-primary font-medium hover:underline"
              >
                {selectedFields.length === Object.keys(currentDsInfo.fields).length
                  ? 'Deselect All'
                  : 'Select All'}
              </button>
            )}
          </div>

          {currentDsInfo ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(currentDsInfo.fields).map(([fKey, fVal]) => {
                const isChecked = selectedFields.includes(fKey);
                return (
                  <div
                    key={fKey}
                    onClick={() => toggleField(fKey)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
                      isChecked
                        ? 'border-primary bg-primary/5 text-foreground'
                        : 'border-border text-muted-foreground hover:border-muted-foreground/30'
                    }`}
                  >
                    <div>
                      <div className="text-sm font-medium">{fVal.label}</div>
                      <div className="text-[10px] text-muted-foreground uppercase">{fVal.type}</div>
                    </div>
                    {isChecked ? (
                      <CheckSquare className="w-4 h-4 text-primary" />
                    ) : (
                      <Square className="w-4 h-4 text-muted-foreground/50" />
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">Loading catalogue fields...</div>
          )}
        </div>
      </div>

      {/* Results Table */}
      {reportResult && (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm space-y-2">
          <div className="p-4 bg-muted/30 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-foreground text-sm">
              Query Results ({reportResult.data ? reportResult.data.length : 0} rows)
            </h3>
          </div>

          {reportResult.data && reportResult.data.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground font-medium border-b border-border uppercase">
                  <tr>
                    {reportResult.selected_fields.map((f) => (
                      <th key={f} className="p-3">
                        {f.replace('_', ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {reportResult.data.map((row, idx) => (
                    <tr key={idx} className="hover:bg-muted/30 transition-colors">
                      {reportResult.selected_fields.map((f) => (
                        <td key={f} className="p-3 text-foreground">
                          {row[f] !== null && row[f] !== undefined ? String(row[f]) : '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground text-sm">
              No matching records found for this query.
            </div>
          )}
        </div>
      )}

      {/* Save Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 space-y-4 shadow-lg">
            <h3 className="text-lg font-bold text-foreground">Save Report Configuration</h3>

            <form onSubmit={handleSaveReport} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Report Name *
                </label>
                <input
                  type="text"
                  required
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="e.g. Monthly Case Overview"
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Description
                </label>
                <textarea
                  value={saveDescription}
                  onChange={(e) => setSaveDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1">
                  Sharing Visibility
                </label>
                <select
                  value={saveVisibility}
                  onChange={(e) => setSaveVisibility(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                >
                  <option value="PRIVATE">Private (Only Me)</option>
                  <option value="TEAM">Team Shared</option>
                  <option value="AUTHORIZED_SHARED">Authorized Shared</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-border pt-4">
                <button
                  type="button"
                  onClick={() => setShowSaveModal(false)}
                  className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
                >
                  Save Definition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  PlusCircle, 
  Building2, 
  DollarSign, 
  Calendar, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';
import financeApi from '../api/finance';

export default function FinanceBudgetLines() {
  const [budgetLines, setBudgetLines] = useState([]);
  const [fundingSources, setFundingSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // New Budget Line Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    code: '',
    name: '',
    program_category: 'CHILD_MAINTENANCE',
    fiscal_year: '2025-2026',
    allocated_amount: '',
    funding_source_id: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [lines, sources] = await Promise.all([
        financeApi.getBudgetLines(),
        financeApi.getFundingSources(),
      ]);
      setBudgetLines(lines || []);
      setFundingSources(sources || []);
      if (sources?.length > 0) {
        setForm((prev) => ({ ...prev, funding_source_id: sources[0].id }));
      }
    } catch (err) {
      console.error('Failed to load budget lines:', err);
      setError('Unable to load budget lines and funding sources.');
    } finally {
      setLoading(false);
    }
  }

  const formatCAD = (val) => {
    const num = parseFloat(val || 0);
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
    }).format(num);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      setCreating(true);
      setError(null);
      await financeApi.createBudgetLine({
        code: form.code.trim().toUpperCase(),
        name: form.name.trim(),
        program_category: form.program_category,
        fiscal_year: form.fiscal_year.trim(),
        allocated_amount: form.allocated_amount,
        funding_source_id: form.funding_source_id || undefined,
        is_active: true,
      });
      setCreateModalOpen(false);
      setForm({
        code: '',
        name: '',
        program_category: 'CHILD_MAINTENANCE',
        fiscal_year: '2025-2026',
        allocated_amount: '',
        funding_source_id: fundingSources[0]?.id || '',
      });
      await loadData();
    } catch (err) {
      console.error('Failed to create budget line:', err);
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to create budget line.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Funding Sources & Budget Lines</h1>
          <p className="text-sm text-gray-500 mt-1">
            ISC grant agreements, provincial transfers, and departmental cost-center allocations.
          </p>
        </div>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <PlusCircle className="w-4 h-4" />
          Add Budget Line
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Funding Sources Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {fundingSources.map((fs) => (
          <div key={fs.id} className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex items-start justify-between">
            <div>
              <span className="font-mono text-xs font-semibold text-indigo-600 px-2 py-0.5 bg-indigo-50 rounded">
                {fs.code}
              </span>
              <h3 className="font-bold text-gray-900 text-sm mt-2">{fs.name}</h3>
              <p className="text-xs text-gray-500 mt-1">{fs.source_type} • {fs.currency}</p>
            </div>
            <span className="p-2 bg-gray-50 text-gray-500 rounded-lg">
              <Building2 className="w-4 h-4" />
            </span>
          </div>
        ))}
      </div>

      {/* Budget Lines Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-500">Loading budget allocations...</div>
        ) : budgetLines.length === 0 ? (
          <div className="p-12 text-center">
            <Layers className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-gray-900">No budget lines configured</h3>
            <p className="text-xs text-gray-500 mt-1">
              Add cost center budget lines to allocate purchase order expenditures.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3.5">Budget Code</th>
                  <th className="px-6 py-3.5">Name & Category</th>
                  <th className="px-6 py-3.5">Fiscal Year</th>
                  <th className="px-6 py-3.5">Funding Source</th>
                  <th className="px-6 py-3.5 text-right">Allocated Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {budgetLines.map((bl) => (
                  <tr key={bl.id} className="hover:bg-gray-50/75 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-xs text-gray-900">
                      {bl.code}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{bl.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{bl.program_category}</div>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-700">{bl.fiscal_year}</td>
                    <td className="px-6 py-4 text-xs text-gray-600">
                      {bl.funding_source?.name || '—'}
                    </td>
                    <td className="px-6 py-4 text-right font-bold text-gray-900">
                      {formatCAD(bl.allocated_amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleCreate} className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900">Add Budget Line</h3>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Budget Code *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BL-PREV-01"
                  value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs uppercase focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Fiscal Year *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 2025-2026"
                  value={form.fiscal_year}
                  onChange={(e) => setForm({ ...form, fiscal_year: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Budget Line Name *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Family Prevention & Cultural Support"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Program Category *
                </label>
                <select
                  value={form.program_category}
                  onChange={(e) => setForm({ ...form, program_category: e.target.value })}
                  className="w-full px-2.5 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs text-gray-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="PREVENTION">Prevention</option>
                  <option value="CHILD_MAINTENANCE">Child Maintenance</option>
                  <option value="SPECIALIZED_SERVICES">Specialized Services</option>
                  <option value="OPERATIONS">Operations</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Funding Source
                </label>
                <select
                  value={form.funding_source_id}
                  onChange={(e) => setForm({ ...form, funding_source_id: e.target.value })}
                  className="w-full px-2.5 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs text-gray-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">None</option>
                  {fundingSources.map((fs) => (
                    <option key={fs.id} value={fs.id}>
                      {fs.code} ({fs.name})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Allocated Amount (CAD) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.00"
                required
                placeholder="e.g. 250000.00"
                value={form.allocated_amount}
                onChange={(e) => setForm({ ...form, allocated_amount: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setCreateModalOpen(false)}
                className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                {creating ? 'Saving...' : 'Create Budget Line'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

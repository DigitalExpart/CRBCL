import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Receipt, 
  PlusCircle, 
  Calendar, 
  Home, 
  CheckCircle2, 
  Clock, 
  Ban, 
  ChevronRight, 
  AlertCircle,
  ShieldCheck
} from 'lucide-react';
import financeApi from '../api/finance';
import placementHomesApi from '../api/placementHomes';

export default function FinanceInvoices() {
  const [invoices, setInvoices] = useState([]);
  const [homes, setHomes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Generate Modal state
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
  const [selectedHomeId, setSelectedHomeId] = useState('');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadInvoices();
    loadHomes();
  }, []);

  async function loadInvoices() {
    try {
      setLoading(true);
      const res = await financeApi.getInvoices();
      setInvoices(res.items || []);
    } catch (err) {
      console.error('Failed to load invoices:', err);
      setError('Unable to load invoices.');
    } finally {
      setLoading(false);
    }
  }

  async function loadHomes() {
    try {
      const res = await placementHomesApi.getHomes();
      const list = res.items || (Array.isArray(res) ? res : []);
      setHomes(list);
      if (list.length > 0) setSelectedHomeId(list[0].id);
    } catch (err) {
      console.error('Failed to load placement homes:', err);
    }
  }

  const formatCAD = (val) => {
    const num = parseFloat(val || 0);
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
    }).format(num);
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    try {
      setGenerating(true);
      setError(null);
      await financeApi.generateDraftInvoice({
        placement_home_id: selectedHomeId,
        billing_period_start: periodStart,
        billing_period_end: periodEnd,
      });
      setGenerateModalOpen(false);
      await loadInvoices();
    } catch (err) {
      console.error('Failed to generate invoice:', err);
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to generate invoice.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setGenerating(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'FINALIZED':
      case 'PAID':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" /> Finalized & Locked
          </span>
        );
      case 'VOID':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            <Ban className="w-3.5 h-3.5" /> Voided
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3.5 h-3.5" /> Draft
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Placement Billing & Invoices</h1>
          <p className="text-sm text-gray-500 mt-1">
            Automated per-diem calculations with versioned rates and immutable billing snapshots.
          </p>
        </div>
        <button
          onClick={() => {
            // Default current month start/end
            const now = new Date();
            const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
            const end = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
            setPeriodStart(start);
            setPeriodEnd(end);
            setGenerateModalOpen(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <PlusCircle className="w-4 h-4" />
          Generate Statement
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Invoices List Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-500">Loading invoices...</div>
        ) : invoices.length === 0 ? (
          <div className="p-12 text-center">
            <Receipt className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-gray-900">No invoices found</h3>
            <p className="text-xs text-gray-500 mt-1">
              Click Generate Statement to run monthly placement per-diem billing calculations.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3.5">Invoice #</th>
                  <th className="px-6 py-3.5">Placement Home</th>
                  <th className="px-6 py-3.5">Billing Period</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Total (CAD)</th>
                  <th className="px-6 py-3.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50/75 transition-colors group">
                    <td className="px-6 py-4 font-mono font-medium text-xs text-gray-900">
                      {inv.invoice_number}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{inv.placement_home?.name || 'Home'}</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {inv.items?.length || 0} child placement(s) billed
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-600">
                      {inv.billing_period_start} to {inv.billing_period_end}
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(inv.status)}</td>
                    <td className="px-6 py-4 text-right font-semibold text-gray-900">
                      {formatCAD(inv.total_amount)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/finance/invoices/${inv.id}`}
                        className="inline-flex items-center text-xs font-medium text-indigo-600 hover:text-indigo-800"
                      >
                        Statement <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Generate Modal */}
      {generateModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleGenerate} className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900">Generate Placement Statement</h3>
            <p className="text-xs text-gray-500">
              Select the placement home and billing period. The billing engine will automatically intersect episode days and apply versioned rates.
            </p>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Placement Home *
              </label>
              <select
                required
                value={selectedHomeId}
                onChange={(e) => setSelectedHomeId(e.target.value)}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm text-gray-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {homes.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name} ({h.home_type})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Period Start *
                </label>
                <input
                  type="date"
                  required
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Period End *
                </label>
                <input
                  type="date"
                  required
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setGenerateModalOpen(false)}
                className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={generating || !selectedHomeId}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                {generating ? 'Calculating...' : 'Run Billing Engine'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

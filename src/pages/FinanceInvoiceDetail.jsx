import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Receipt, 
  Lock, 
  Ban, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  Calendar, 
  Home, 
  User,
  Info
} from 'lucide-react';
import financeApi from '../api/finance';

export default function FinanceInvoiceDetail() {
  const { id } = useParams();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Void modal
  const [voidModalOpen, setVoidModalOpen] = useState(false);
  const [voidReason, setVoidReason] = useState('');

  useEffect(() => {
    loadInvoice();
  }, [id]);

  async function loadInvoice() {
    try {
      setLoading(true);
      setError(null);
      const data = await financeApi.getInvoiceById(id);
      setInvoice(data);
    } catch (err) {
      console.error('Failed to load invoice:', err);
      setError('Unable to load placement invoice.');
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

  const handleFinalize = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await financeApi.finalizeInvoice(invoice.id);
      await loadInvoice();
    } catch (err) {
      console.error('Finalize failed:', err);
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Finalize failed.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setActionLoading(false);
    }
  };

  const handleVoid = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await financeApi.voidInvoice(invoice.id, voidReason);
      setVoidModalOpen(false);
      setVoidReason('');
      await loadInvoice();
    } catch (err) {
      console.error('Void failed:', err);
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Void failed.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-sm text-gray-500">Loading placement statement...</div>;
  }

  if (!invoice) {
    return (
      <div className="p-8 text-center text-sm text-gray-500">
        Invoice not found. <Link to="/finance/invoices" className="text-indigo-600">Go back</Link>
      </div>
    );
  }

  const isFinalized = invoice.status === 'FINALIZED' || invoice.status === 'PAID';
  const isDraft = invoice.status === 'DRAFT' || invoice.status === 'GENERATED' || invoice.status === 'REVIEWED';
  const isVoid = invoice.status === 'VOID';

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Back Link & Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/finance/invoices"
            className="p-2 text-gray-500 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-800">
                {invoice.invoice_number}
              </span>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                isFinalized ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                isVoid ? 'bg-red-50 text-red-700 border border-red-200' :
                'bg-amber-50 text-amber-700 border border-amber-200'
              }`}>
                {invoice.status}
              </span>
            </div>
            <h1 className="text-xl font-bold text-gray-900 mt-1">
              {invoice.placement_home?.name || 'Placement Home Statement'}
            </h1>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {isDraft && (
            <button
              onClick={handleFinalize}
              disabled={actionLoading}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              <Lock className="w-4 h-4" /> Lock & Finalize
            </button>
          )}

          {!isVoid && (
            <button
              onClick={() => setVoidModalOpen(true)}
              disabled={actionLoading}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-red-50 text-red-700 border border-red-200 text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              <Ban className="w-4 h-4 text-red-600" /> Void Statement
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isVoid && invoice.void_reason && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 text-red-900 text-sm">
          <Ban className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Statement Voided</div>
            <p className="mt-0.5 text-xs text-red-800">{invoice.void_reason}</p>
          </div>
        </div>
      )}

      {/* Summary Box */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-gray-500 block">Placement Facility</span>
            <span className="font-semibold text-gray-900 mt-0.5 block">
              {invoice.placement_home?.name || '—'}
            </span>
          </div>

          <div>
            <span className="text-gray-500 block">Billing Period</span>
            <span className="font-semibold text-gray-900 mt-0.5 block">
              {invoice.billing_period_start} to {invoice.billing_period_end}
            </span>
          </div>

          <div>
            <span className="text-gray-500 block">Currency</span>
            <span className="font-semibold text-gray-900 mt-0.5 block">{invoice.currency}</span>
          </div>

          <div>
            <span className="text-gray-500 block">Generated Date</span>
            <span className="font-semibold text-gray-900 mt-0.5 block">
              {new Date(invoice.generated_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Calculation Snapshot Table (ADR-025) */}
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900 text-sm">Per-Diem Itemized Calculation Snapshot</h3>
            {isFinalized && (
              <span className="inline-flex items-center gap-1 text-xs text-emerald-700 bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5" /> Immutably Locked
              </span>
            )}
          </div>

          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-500 font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2.5">Child Name</th>
                  <th className="px-4 py-2.5">Service Interval</th>
                  <th className="px-4 py-2.5">Rate Band</th>
                  <th className="px-4 py-2.5 text-right">Days</th>
                  <th className="px-4 py-2.5 text-right">Daily Rate</th>
                  <th className="px-4 py-2.5 text-right">Line Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {(!invoice.items || invoice.items.length === 0) ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-6 text-center text-gray-500">
                      No billable child placements found in this billing period interval.
                    </td>
                  </tr>
                ) : (
                  invoice.items.map((it) => (
                    <tr key={it.id}>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{it.child_name}</div>
                        <div className="text-[11px] text-gray-400">Age at service: {it.age_at_service}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {it.service_start_date} to {it.service_end_date}
                      </td>
                      <td className="px-4 py-3 text-gray-500">{it.rate_band_label}</td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">{it.billable_days}</td>
                      <td className="px-4 py-3 text-right text-gray-700">{formatCAD(it.daily_rate)}</td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-900">
                        {formatCAD(it.line_total)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Statement Total */}
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200 flex flex-col items-end space-y-1 text-xs text-gray-600">
            <div className="flex justify-between w-48 text-sm font-bold text-gray-900">
              <span>Statement Total:</span>
              <span className="text-indigo-600">{formatCAD(invoice.total_amount)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Void Modal */}
      {voidModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900 text-red-600">Void Placement Statement</h3>
            <p className="text-xs text-gray-500">
              Voiding an invoice unlocks the billing period allowing a replacement statement to be generated. A mandatory reason is required for audit logs.
            </p>
            <textarea
              rows={3}
              required
              placeholder="e.g. Administrative adjustment required for corrected admission date..."
              value={voidReason}
              onChange={(e) => setVoidReason(e.target.value)}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-red-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setVoidModalOpen(false)}
                className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!voidReason.trim() || actionLoading}
                onClick={handleVoid}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                Confirm Void
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

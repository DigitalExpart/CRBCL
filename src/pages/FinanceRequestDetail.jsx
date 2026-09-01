import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Send, 
  CheckCircle2, 
  RotateCcw, 
  XCircle, 
  Clock, 
  Building, 
  User, 
  FileText, 
  AlertCircle,
  ShieldCheck,
  Calendar,
  MessageSquare
} from 'lucide-react';
import financeApi from '../api/finance';

export default function FinanceRequestDetail() {
  const { id } = useParams();
  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Modals state
  const [returnModalOpen, setReturnModalOpen] = useState(false);
  const [returnReason, setReturnReason] = useState('');
  const [denyModalOpen, setDenyModalOpen] = useState(false);
  const [denyReason, setDenyReason] = useState('');
  const [approveComments, setApproveComments] = useState('');
  const [approveModalOpen, setApproveModalOpen] = useState(false);

  useEffect(() => {
    loadRequest();
  }, [id]);

  async function loadRequest() {
    try {
      setLoading(true);
      setError(null);
      const data = await financeApi.getServiceRequestById(id);
      setRequest(data);
    } catch (err) {
      console.error('Failed to load request:', err);
      setError('Unable to load service request.');
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

  const handleAction = async (actionFn, onSuccess) => {
    try {
      setActionLoading(true);
      setError(null);
      await actionFn();
      await loadRequest();
      if (onSuccess) onSuccess();
    } catch (err) {
      console.error('Action failed:', err);
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Action failed.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-sm text-gray-500">Loading service request...</div>;
  }

  if (!request) {
    return (
      <div className="p-8 text-center text-sm text-gray-500">
        Service request not found. <Link to="/finance/requests" className="text-indigo-600">Go back</Link>
      </div>
    );
  }

  const isPending = request.status === 'PENDING_APPROVAL';
  const isDraftOrReturned = request.status === 'DRAFT' || request.status === 'RETURNED';

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Back Link & Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/finance/requests"
            className="p-2 text-gray-500 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-800">
                {request.request_number}
              </span>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                request.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                request.status === 'PENDING_APPROVAL' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                request.status === 'RETURNED' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                request.status === 'DENIED' ? 'bg-red-50 text-red-700 border border-red-200' :
                'bg-gray-100 text-gray-700'
              }`}>
                {request.status}
              </span>
            </div>
            <h1 className="text-xl font-bold text-gray-900 mt-1">{request.title}</h1>
          </div>
        </div>

        {/* Workflow Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {isDraftOrReturned && (
            <button
              onClick={() => handleAction(() => financeApi.submitServiceRequest(request.id))}
              disabled={actionLoading}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              <Send className="w-4 h-4" /> Submit for Approval
            </button>
          )}

          {isPending && (
            <>
              <button
                onClick={() => setApproveModalOpen(true)}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" /> Approve
              </button>

              <button
                onClick={() => setReturnModalOpen(true)}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                <RotateCcw className="w-4 h-4 text-blue-600" /> Return for Edit
              </button>

              <button
                onClick={() => setDenyModalOpen(true)}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-red-50 text-red-700 border border-red-200 text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                <XCircle className="w-4 h-4 text-red-600" /> Deny
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Return / Denial Banner if applicable */}
      {request.status === 'RETURNED' && request.return_reason && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-start gap-3 text-blue-900 text-sm">
          <RotateCcw className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Returned for Amendment</div>
            <p className="mt-0.5 text-xs text-blue-800">{request.return_reason}</p>
          </div>
        </div>
      )}

      {request.status === 'DENIED' && request.denial_reason && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 text-red-900 text-sm">
          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Request Denied</div>
            <p className="mt-0.5 text-xs text-red-800">{request.denial_reason}</p>
          </div>
        </div>
      )}

      {/* Details Grid */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-gray-500 block">Request Type</span>
            <span className="font-semibold text-gray-900 mt-0.5 block">
              {request.request_type === 'PURCHASE_ORDER' ? 'Purchase Order' : 'Staff Reimbursement'}
            </span>
          </div>

          <div>
            <span className="text-gray-500 block">Vendor / Payee</span>
            <span className="font-semibold text-gray-900 mt-0.5 block">
              {request.vendor_name || request.payee_name || '—'}
            </span>
          </div>

          <div>
            <span className="text-gray-500 block">Currency</span>
            <span className="font-semibold text-gray-900 mt-0.5 block">{request.currency}</span>
          </div>

          <div>
            <span className="text-gray-500 block">Created At</span>
            <span className="font-semibold text-gray-900 mt-0.5 block">
              {new Date(request.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {request.description && (
          <div className="pt-4 border-t border-gray-100 text-xs">
            <span className="text-gray-500 block font-medium mb-1">Description & Justification</span>
            <p className="text-gray-800 leading-relaxed bg-gray-50 p-3 rounded-lg border border-gray-200">
              {request.description}
            </p>
          </div>
        )}

        {/* Line Items Table */}
        <div className="pt-4 border-t border-gray-200">
          <h3 className="font-semibold text-gray-900 text-sm mb-3">Itemized Line Breakdown</h3>
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-500 font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2.5">Item Description</th>
                  <th className="px-4 py-2.5">Budget Line</th>
                  <th className="px-4 py-2.5 text-right">Qty</th>
                  <th className="px-4 py-2.5 text-right">Unit Price</th>
                  <th className="px-4 py-2.5 text-right">Line Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {request.items?.map((it) => (
                  <tr key={it.id}>
                    <td className="px-4 py-3 text-gray-900 font-medium">{it.description}</td>
                    <td className="px-4 py-3 text-gray-500 font-mono">
                      {it.budget_line?.code || '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-700">{it.quantity}</td>
                    <td className="px-4 py-3 text-right text-gray-700">{formatCAD(it.unit_price)}</td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">
                      {formatCAD(it.line_total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Totals Summary */}
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200 flex flex-col items-end space-y-1 text-xs text-gray-600">
            <div className="flex justify-between w-48">
              <span>Subtotal:</span>
              <span className="font-semibold text-gray-900">{formatCAD(request.subtotal)}</span>
            </div>
            <div className="flex justify-between w-48">
              <span>Tax:</span>
              <span className="font-semibold text-gray-900">{formatCAD(request.tax_amount)}</span>
            </div>
            <div className="flex justify-between w-48 pt-1.5 border-t border-gray-300 text-sm font-bold text-gray-900">
              <span>Total Amount:</span>
              <span className="text-indigo-600">{formatCAD(request.total_amount)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Preserved Approval History Audit Trail (ADR-023) */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h3 className="font-semibold text-gray-900 text-sm mb-4 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-indigo-600" />
          Approval & Decision Audit Trail
        </h3>

        {(!request.approvals || request.approvals.length === 0) ? (
          <p className="text-xs text-gray-500">No decision events recorded yet.</p>
        ) : (
          <div className="space-y-4 relative before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200">
            {request.approvals.map((step, idx) => (
              <div key={step.id || idx} className="flex items-start gap-4 relative">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold ring-4 ring-white ${
                  step.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-700' :
                  step.status === 'RETURNED' ? 'bg-blue-100 text-blue-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {idx + 1}
                </div>
                <div className="flex-1 bg-gray-50 p-3.5 rounded-lg border border-gray-200 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-gray-900">
                      Decision: {step.status}
                    </span>
                    <span className="text-gray-400 text-[11px]">
                      {new Date(step.decided_at || step.created_at).toLocaleString()}
                    </span>
                  </div>
                  {step.comments && (
                    <p className="mt-1 text-gray-700 italic bg-white p-2 rounded border border-gray-100">
                      "{step.comments}"
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Return Modal */}
      {returnModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900">Return Request for Amendment</h3>
            <p className="text-xs text-gray-500">
              Provide instructions to the requester explaining what changes or documentation are needed.
            </p>
            <textarea
              rows={3}
              required
              placeholder="e.g. Please attach itemized store receipts before resubmitting..."
              value={returnReason}
              onChange={(e) => setReturnReason(e.target.value)}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setReturnModalOpen(false)}
                className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!returnReason.trim() || actionLoading}
                onClick={() =>
                  handleAction(
                    () => financeApi.returnServiceRequest(request.id, returnReason),
                    () => {
                      setReturnModalOpen(false);
                      setReturnReason('');
                    }
                  )
                }
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                Confirm Return
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deny Modal */}
      {denyModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900 text-red-600">Deny Financial Request</h3>
            <p className="text-xs text-gray-500">
              Provide an official explanation for denying this financial commitment.
            </p>
            <textarea
              rows={3}
              required
              placeholder="e.g. Request outside of current program funding allocation..."
              value={denyReason}
              onChange={(e) => setDenyReason(e.target.value)}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-red-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDenyModalOpen(false)}
                className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!denyReason.trim() || actionLoading}
                onClick={() =>
                  handleAction(
                    () => financeApi.denyServiceRequest(request.id, denyReason),
                    () => {
                      setDenyModalOpen(false);
                      setDenyReason('');
                    }
                  )
                }
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                Confirm Denial
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Approve Modal */}
      {approveModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900">Authorize Service Request</h3>
            <p className="text-xs text-gray-500">
              Confirm approval for {formatCAD(request.total_amount)}. Note: Requesters cannot approve their own requests under Segregation of Duties rules.
            </p>
            <textarea
              rows={2}
              placeholder="Optional approval notes or allocation remarks..."
              value={approveComments}
              onChange={(e) => setApproveComments(e.target.value)}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setApproveModalOpen(false)}
                className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={actionLoading}
                onClick={() =>
                  handleAction(
                    () => financeApi.approveServiceRequest(request.id, approveComments),
                    () => {
                      setApproveModalOpen(false);
                      setApproveComments('');
                    }
                  )
                }
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                Confirm Approval
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

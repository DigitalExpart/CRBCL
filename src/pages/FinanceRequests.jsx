import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Receipt, 
  PlusCircle, 
  Search, 
  Filter, 
  CheckCircle2, 
  Clock, 
  XCircle, 
  RotateCcw, 
  ChevronRight,
  AlertCircle
} from 'lucide-react';
import financeApi from '../api/finance';

export default function FinanceRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadRequests();
  }, [typeFilter, statusFilter]);

  async function loadRequests() {
    try {
      setLoading(true);
      const params = {};
      if (typeFilter) params.request_type = typeFilter;
      if (statusFilter) params.status = statusFilter;
      const res = await financeApi.getServiceRequests(params);
      setRequests(res.items || []);
    } catch (err) {
      console.error('Failed to load service requests:', err);
      setError('Unable to load service requests.');
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

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" /> Approved
          </span>
        );
      case 'PENDING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3.5 h-3.5" /> Pending Approval
          </span>
        );
      case 'RETURNED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <RotateCcw className="w-3.5 h-3.5" /> Returned for Edit
          </span>
        );
      case 'DENIED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            <XCircle className="w-3.5 h-3.5" /> Denied
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-200">
            Draft
          </span>
        );
    }
  };

  const filteredRequests = requests.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.request_number?.toLowerCase().includes(q) ||
      r.title?.toLowerCase().includes(q) ||
      r.vendor_name?.toLowerCase().includes(q) ||
      r.payee_name?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Purchase Orders & Claims</h1>
          <p className="text-sm text-gray-500 mt-1">
            Track purchase orders and worker reimbursement requests through approval workflows.
          </p>
        </div>
        <Link
          to="/finance/requests/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <PlusCircle className="w-4 h-4" />
          Create Request
        </Link>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Controls */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by request #, title, vendor, or payee..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Types</option>
            <option value="PURCHASE_ORDER">Purchase Orders</option>
            <option value="REIMBURSEMENT">Reimbursements</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="PENDING_APPROVAL">Pending Approval</option>
            <option value="APPROVED">Approved</option>
            <option value="RETURNED">Returned</option>
            <option value="DENIED">Denied</option>
          </select>
        </div>
      </div>

      {/* Requests Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-500">Loading requests...</div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-gray-900">No service requests found</h3>
            <p className="text-xs text-gray-500 mt-1">
              Create a new purchase order or submit an expense claim to get started.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3.5">Request #</th>
                  <th className="px-6 py-3.5">Type & Title</th>
                  <th className="px-6 py-3.5">Vendor / Payee</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Amount (CAD)</th>
                  <th className="px-6 py-3.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredRequests.map((req) => (
                  <tr key={req.id} className="hover:bg-gray-50/75 transition-colors group">
                    <td className="px-6 py-4 font-mono font-medium text-xs text-gray-900">
                      {req.request_number}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{req.title}</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {req.request_type === 'PURCHASE_ORDER' ? 'Purchase Order' : 'Staff Reimbursement'} •{' '}
                        {req.items?.length || 0} line item(s)
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {req.vendor_name || req.payee_name || '—'}
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(req.status)}</td>
                    <td className="px-6 py-4 text-right font-semibold text-gray-900">
                      {formatCAD(req.total_amount)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/finance/requests/${req.id}`}
                        className="inline-flex items-center text-xs font-medium text-indigo-600 hover:text-indigo-800"
                      >
                        Details <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

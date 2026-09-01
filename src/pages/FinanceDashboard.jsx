import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  DollarSign, 
  FileText, 
  Receipt, 
  Layers, 
  TrendingUp, 
  PlusCircle, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import financeApi from '../api/finance';

export default function FinanceDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await financeApi.getDashboardMetrics();
        setMetrics(data);
      } catch (err) {
        console.error('Failed to load finance metrics:', err);
        setError('Unable to load financial dashboard metrics.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const formatCAD = (val) => {
    const num = parseFloat(val || 0);
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
    }).format(num);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Finance & Billing Workbench</h1>
          <p className="text-sm text-gray-500 mt-1">
            Purchase orders, staff reimbursements, placement per-diem billing, and fiscal controls.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/finance/requests/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            New Service Request
          </Link>
          <Link
            to="/finance/invoices"
            className="inline-flex items-center gap-2 px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <Receipt className="w-4 h-4 text-gray-500" />
            Generate Invoices
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Pending Approvals</span>
            <span className="p-2 bg-amber-50 text-amber-600 rounded-lg">
              <Clock className="w-5 h-5" />
            </span>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-gray-900">
              {loading ? '...' : formatCAD(metrics?.pending_requests_value)}
            </div>
            <div className="text-xs text-amber-700 font-medium mt-1">
              {loading ? '...' : `${metrics?.pending_requests_count || 0} requests awaiting review`}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Approved Service Commitments</span>
            <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <CheckCircle2 className="w-5 h-5" />
            </span>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-gray-900">
              {loading ? '...' : formatCAD(metrics?.approved_requests_value)}
            </div>
            <div className="text-xs text-emerald-700 font-medium mt-1">
              {loading ? '...' : `${metrics?.approved_requests_count || 0} active approved commitments`}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Finalized Placement Invoices</span>
            <span className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <Receipt className="w-5 h-5" />
            </span>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-gray-900">
              {loading ? '...' : formatCAD(metrics?.finalized_invoices_value)}
            </div>
            <div className="text-xs text-indigo-700 font-medium mt-1">
              {loading ? '...' : `${metrics?.finalized_invoices_count || 0} billing statements closed`}
            </div>
          </div>
        </div>
      </div>

      {/* Module Directory Navigation */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Link
          to="/finance/requests"
          className="group p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:border-indigo-400 hover:shadow-md transition-all flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">
              Purchase Orders & Claims
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              Manage client support purchase orders and worker expense reimbursements.
            </p>
          </div>
          <div className="mt-4 flex items-center text-xs font-medium text-indigo-600 group-hover:translate-x-1 transition-transform">
            View Requests <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </div>
        </Link>

        <Link
          to="/finance/invoices"
          className="group p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:border-indigo-400 hover:shadow-md transition-all flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Receipt className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-gray-900 group-hover:text-emerald-600 transition-colors">
              Placement Billing & Invoices
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              Generate per-diem foster & facility invoices with date-intersection calculations.
            </p>
          </div>
          <div className="mt-4 flex items-center text-xs font-medium text-emerald-600 group-hover:translate-x-1 transition-transform">
            Manage Invoices <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </div>
        </Link>

        <Link
          to="/finance/rates"
          className="group p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:border-indigo-400 hover:shadow-md transition-all flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">
              Rate Schedules & Age Bands
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              Configure versioned per-diem rates by home type and child age bands.
            </p>
          </div>
          <div className="mt-4 flex items-center text-xs font-medium text-purple-600 group-hover:translate-x-1 transition-transform">
            View Rates <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </div>
        </Link>

        <Link
          to="/finance/budget-lines"
          className="group p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:border-indigo-400 hover:shadow-md transition-all flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
              Funding & Budget Lines
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              Track ISC and Provincial grant allocations across program budget lines.
            </p>
          </div>
          <div className="mt-4 flex items-center text-xs font-medium text-blue-600 group-hover:translate-x-1 transition-transform">
            View Allocations <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </div>
        </Link>
      </div>

      {/* Internal Controls Note */}
      <div className="bg-gradient-to-r from-gray-50 to-indigo-50/30 p-5 rounded-xl border border-gray-200 flex items-start gap-4">
        <div className="p-2 bg-indigo-100 text-indigo-700 rounded-lg mt-0.5">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-semibold text-gray-900 text-sm">Financial Integrity & Governance Controls</h4>
          <p className="text-xs text-gray-600 mt-1 leading-relaxed">
            All monetary amounts are maintained with exact DECIMAL arithmetic (CAD). 
            Segregation of duties enforces that staff cannot approve their own financial requests. 
            Finalized placement invoices permanently lock calculation snapshots against historical tampering.
          </p>
        </div>
      </div>
    </div>
  );
}

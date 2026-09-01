import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  Search,
  Download,
  Calendar,
  Filter,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  DollarSign,
  AlertCircle,
  BarChart3,
  Layers,
  FileText,
  Receipt,
} from 'lucide-react';
import { financeApi } from '@/api/finance';

const STATUS_COLORS = {
  APPROVED: 'bg-green-100 text-green-800',
  PAID:     'bg-green-100 text-green-800',
  SUBMITTED: 'bg-blue-100 text-blue-800',
  PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',
  FINALIZED: 'bg-teal-100 text-teal-800',
  RETURNED: 'bg-orange-100 text-orange-800',
  DENIED:   'bg-red-100 text-red-800',
  VOID:     'bg-gray-200 text-gray-600',
  DRAFT:    'bg-gray-100 text-gray-600',
};

function fmt(amount, currency = 'CAD') {
  if (amount == null) return '\u2014';
  return new Intl.NumberFormat('en-CA', { style: 'currency', currency }).format(Number(amount));
}

function fmtDate(ds) {
  if (!ds) return '\u2014';
  return new Date(ds).toLocaleDateString('en-CA', { year: 'numeric', month: 'short', day: 'numeric' });
}

export default function FinanceLedger() {
  const [entries, setEntries] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 25;

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [ledger, dash] = await Promise.all([
          financeApi.getLedger({ limit: 500 }),
          financeApi.getDashboardMetrics(),
        ]);
        setEntries(ledger?.items ?? []);
        setMetrics(dash);
      } catch (e) {
        setError(e?.response?.data?.error?.message || e?.message || 'Failed to load ledger');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const totals = React.useMemo(() => {
    const approved = entries.filter(e => ['APPROVED', 'PAID', 'FINALIZED'].includes(e.status));
    return {
      count: entries.length,
      approvedAmount: approved.reduce((s, e) => s + Number(e.total_amount ?? e.amount ?? 0), 0),
      pendingCount: entries.filter(e => ['SUBMITTED', 'PENDING_APPROVAL'].includes(e.status)).length,
    };
  }, [entries]);

  const filtered = React.useMemo(() => {
    let list = entries;
    if (typeFilter !== 'all') list = list.filter(e => (e.record_type || e.type || '').toLowerCase() === typeFilter);
    if (statusFilter !== 'all') list = list.filter(e => e.status === statusFilter);
    if (dateFrom) list = list.filter(e => (e.created_at || e.submitted_at || '') >= dateFrom);
    if (dateTo) list = list.filter(e => (e.created_at || e.submitted_at || '') <= dateTo + 'T23:59:59');
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(e =>
        (e.request_number || e.invoice_number || e.number || '').toLowerCase().includes(q) ||
        (e.title || e.description || '').toLowerCase().includes(q) ||
        (e.vendor_name || e.payee_name || '').toLowerCase().includes(q)
      );
    }
    return list;
  }, [entries, typeFilter, statusFilter, dateFrom, dateTo, search]);

  const pageCount = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleExport = async () => {
    try {
      const blob = await financeApi.exportLedger({ status: statusFilter !== 'all' ? statusFilter : undefined });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `crbcl-ledger-${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Export failed. Please try again.');
    }
  };


  const resetFilters = () => {
    setSearch(''); setTypeFilter('all'); setStatusFilter('all');
    setDateFrom(''); setDateTo(''); setPage(1);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-primary" />
            Financial Ledger
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Unified audit trail of all Purchase Orders, Reimbursements, and Placement Invoices
          </p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Download className="w-4 h-4" />
          Export XLSX
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-4 space-y-1">
          <p className="text-xs text-muted-foreground flex items-center gap-1"><BarChart3 className="w-3.5 h-3.5" /> Total Records</p>
          <p className="text-2xl font-bold text-foreground">{totals.count}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 space-y-1">
          <p className="text-xs text-muted-foreground flex items-center gap-1"><TrendingUp className="w-3.5 h-3.5 text-green-600" /> Approved Value</p>
          <p className="text-2xl font-bold text-green-600">{fmt(totals.approvedAmount)}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 space-y-1">
          <p className="text-xs text-muted-foreground flex items-center gap-1"><TrendingDown className="w-3.5 h-3.5 text-yellow-600" /> Pending Items</p>
          <p className="text-2xl font-bold text-yellow-600">{totals.pendingCount}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 space-y-1">
          <p className="text-xs text-muted-foreground flex items-center gap-1"><DollarSign className="w-3.5 h-3.5 text-blue-600" /> YTD Spend</p>
          <p className="text-2xl font-bold text-blue-600">
            {metrics ? fmt(metrics.ytd_spend ?? metrics.total_approved ?? 0) : '\u2014'}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-48">
            <label className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1">
              <Search className="w-3 h-3" /> Search
            </label>
            <input
              type="text"
              placeholder="Number, title, vendor..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1">
              <Layers className="w-3 h-3" /> Type
            </label>
            <select
              value={typeFilter}
              onChange={e => { setTypeFilter(e.target.value); setPage(1); }}
              className="border border-border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="all">All Types</option>
              <option value="purchase_order">Purchase Order</option>
              <option value="reimbursement">Reimbursement</option>
              <option value="invoice">Placement Invoice</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1">
              <Filter className="w-3 h-3" /> Status
            </label>
            <select
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
              className="border border-border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="all">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="APPROVED">Approved</option>
              <option value="RETURNED">Returned</option>
              <option value="DENIED">Denied</option>
              <option value="FINALIZED">Finalized</option>
              <option value="PAID">Paid</option>
              <option value="VOID">Void</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1">
              <Calendar className="w-3 h-3" /> From
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={e => { setDateFrom(e.target.value); setPage(1); }}
              className="border border-border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1">
              <Calendar className="w-3 h-3" /> To
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={e => { setDateTo(e.target.value); setPage(1); }}
              className="border border-border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          {(search || typeFilter !== 'all' || statusFilter !== 'all' || dateFrom || dateTo) && (
            <button onClick={resetFilters} className="text-xs text-muted-foreground hover:text-destructive underline self-end pb-2">
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive rounded-xl text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">Loading ledger...</p>
          </div>
        ) : paged.length === 0 ? (
          <div className="p-12 text-center">
            <BookOpen className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No ledger entries found</p>
            <p className="text-xs text-muted-foreground mt-1">Adjust filters or create new financial records</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 border-b border-border">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Number</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Title / Description</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Date</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider">Amount</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {paged.map((entry, i) => {
                  const num = entry.request_number || entry.invoice_number || entry.number || `#${i + 1}`;
                  const title = entry.title || entry.description || '\u2014';
                  const type = (entry.record_type || entry.type || entry.request_type || '').replace(/_/g, ' ');
                  const amount = entry.total_amount ?? entry.amount ?? 0;
                  const date = entry.submitted_at || entry.created_at || entry.generated_at;
                  const isInvoice = type.toLowerCase().includes('invoice');
                  const href = isInvoice ? `/finance/invoices/${entry.id}` : `/finance/requests/${entry.id}`;
                  return (
                    <tr key={entry.id ?? i} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs font-medium text-primary">{num}</td>
                      <td className="px-4 py-3 max-w-xs">
                        <p className="truncate font-medium text-foreground">{title}</p>
                        {(entry.vendor_name || entry.payee_name) && (
                          <p className="text-xs text-muted-foreground truncate">{entry.vendor_name || entry.payee_name}</p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="flex items-center gap-1 text-xs text-muted-foreground capitalize">
                          {isInvoice ? <Receipt className="w-3.5 h-3.5" /> : <FileText className="w-3.5 h-3.5" />}
                          {type || '\u2014'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[entry.status] ?? 'bg-muted text-muted-foreground'}`}>
                          {entry.status?.replace(/_/g, ' ') ?? '\u2014'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">{fmtDate(date)}</td>
                      <td className="px-4 py-3 text-right font-medium">{amount ? fmt(amount) : '\u2014'}</td>
                      <td className="px-4 py-3">
                        <Link to={href} className="flex items-center gap-0.5 text-xs text-primary hover:underline whitespace-nowrap">
                          View <ChevronRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {pageCount > 1 && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-muted-foreground">
            Showing {(page - 1) * PAGE_SIZE + 1}&#8211;{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length} entries
          </p>
          <div className="flex gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 border border-border rounded-lg disabled:opacity-40 hover:bg-muted transition-colors"
            >
              Previous
            </button>
            <span className="px-3 py-1.5 text-muted-foreground">{page} / {pageCount}</span>
            <button
              disabled={page === pageCount}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 border border-border rounded-lg disabled:opacity-40 hover:bg-muted transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Plus, 
  Trash2, 
  ArrowLeft, 
  Save, 
  Send, 
  AlertCircle,
  Building,
  User,
  Layers,
  DollarSign
} from 'lucide-react';
import financeApi from '../api/finance';

export default function FinanceRequestNew() {
  const navigate = useNavigate();
  const [budgetLines, setBudgetLines] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    request_type: 'PURCHASE_ORDER',
    title: '',
    description: '',
    vendor_name: '',
    payee_name: '',
    notes: '',
    tax_rate: '0.05',
  });

  const [items, setItems] = useState([
    {
      description: '',
      quantity: '1.00',
      unit_price: '0.00',
      budget_line_id: '',
    },
  ]);

  useEffect(() => {
    async function loadBudgetLines() {
      try {
        const lines = await financeApi.getBudgetLines();
        setBudgetLines(lines || []);
        if (lines?.length > 0) {
          setItems((prev) =>
            prev.map((it) => ({ ...it, budget_line_id: it.budget_line_id || lines[0].id }))
          );
        }
      } catch (err) {
        console.error('Failed to load budget lines:', err);
      }
    }
    loadBudgetLines();
  }, []);

  const handleItemChange = (index, field, value) => {
    const next = [...items];
    next[index][field] = value;
    setItems(next);
  };

  const addItem = () => {
    setItems([
      ...items,
      {
        description: '',
        quantity: '1.00',
        unit_price: '0.00',
        budget_line_id: budgetLines[0]?.id || '',
      },
    ]);
  };

  const removeItem = (index) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, idx) => idx !== index));
  };

  // Compute estimate totals (authoritative calculations happen on server)
  const subtotal = items.reduce((acc, it) => {
    const qty = parseFloat(it.quantity) || 0;
    const price = parseFloat(it.unit_price) || 0;
    return acc + qty * price;
  }, 0);

  const taxAmount = form.request_type === 'PURCHASE_ORDER' ? subtotal * (parseFloat(form.tax_rate) || 0) : 0;
  const totalAmount = subtotal + taxAmount;

  const formatCAD = (val) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
    }).format(val);
  };

  const handleSubmit = async (submitForApproval = false) => {
    try {
      setSubmitting(true);
      setError(null);

      if (!form.title.trim()) {
        setError('Please enter a request title.');
        setSubmitting(false);
        return;
      }

      if (items.some((it) => !it.description.trim())) {
        setError('All line items require a description.');
        setSubmitting(false);
        return;
      }

      const payload = {
        request_type: form.request_type,
        title: form.title.trim(),
        description: form.description.trim() || undefined,
        vendor_name: form.request_type === 'PURCHASE_ORDER' ? form.vendor_name.trim() || undefined : undefined,
        payee_name: form.request_type === 'REIMBURSEMENT' ? form.payee_name.trim() || undefined : undefined,
        notes: form.notes.trim() || undefined,
        tax_rate: form.request_type === 'PURCHASE_ORDER' ? form.tax_rate : '0.00',
        currency: 'CAD',
        items: items.map((it) => ({
          description: it.description.trim(),
          quantity: it.quantity,
          unit_price: it.unit_price,
          budget_line_id: it.budget_line_id || undefined,
        })),
      };

      const created = await financeApi.createServiceRequest(payload);

      if (submitForApproval && created?.id) {
        await financeApi.submitServiceRequest(created.id);
      }

      navigate(`/finance/requests/${created.id}`);
    } catch (err) {
      console.error('Failed to create service request:', err);
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to create service request.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Back Link & Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/finance/requests"
          className="p-2 text-gray-500 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">New Financial Request</h1>
          <p className="text-sm text-gray-500">
            Create a purchase order for vendor fulfillment or a staff reimbursement claim.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Form Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        {/* Request Type Selector */}
        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
            Request Type
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setForm({ ...form, request_type: 'PURCHASE_ORDER' })}
              className={`p-4 rounded-lg border text-left transition-all flex items-center gap-3 ${
                form.request_type === 'PURCHASE_ORDER'
                  ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 ring-2 ring-indigo-500/20'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }`}
            >
              <Building className="w-5 h-5 text-indigo-600" />
              <div>
                <div className="font-semibold text-sm">Purchase Order</div>
                <div className="text-xs text-gray-500">Vendor supplies & services</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setForm({ ...form, request_type: 'REIMBURSEMENT' })}
              className={`p-4 rounded-lg border text-left transition-all flex items-center gap-3 ${
                form.request_type === 'REIMBURSEMENT'
                  ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 ring-2 ring-indigo-500/20'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }`}
            >
              <User className="w-5 h-5 text-indigo-600" />
              <div>
                <div className="font-semibold text-sm">Staff Reimbursement</div>
                <div className="text-xs text-gray-500">Out-of-pocket expenses</div>
              </div>
            </button>
          </div>
        </div>

        {/* General Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
              Title / Subject *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Winter Clothing Support for Bear Family Kinship"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {form.request_type === 'PURCHASE_ORDER' ? (
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Vendor Name
              </label>
              <input
                type="text"
                placeholder="e.g. Northern Store / Walmart"
                value={form.vendor_name}
                onChange={(e) => setForm({ ...form, vendor_name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Payee / Staff Member Name
              </label>
              <input
                type="text"
                placeholder="e.g. Jane Worker"
                value={form.payee_name}
                onChange={(e) => setForm({ ...form, payee_name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}

          {form.request_type === 'PURCHASE_ORDER' && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Applicable Tax Rate (GST/PST)
              </label>
              <select
                value={form.tax_rate}
                onChange={(e) => setForm({ ...form, tax_rate: e.target.value })}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="0.00">0% (Tax Exempt / Treaty Exempt)</option>
                <option value="0.05">5% (GST Only)</option>
                <option value="0.11">11% (GST + SK PST)</option>
              </select>
            </div>
          )}

          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
              Description / Business Justification
            </label>
            <textarea
              rows={2}
              placeholder="Provide background details and program justification..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Line Items Section */}
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900 text-sm">Itemized Line Breakdown</h3>
            <button
              type="button"
              onClick={addItem}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> Add Line
            </button>
          </div>

          <div className="space-y-3">
            {items.map((it, idx) => {
              const lineEst = (parseFloat(it.quantity) || 0) * (parseFloat(it.unit_price) || 0);
              return (
                <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-200 grid grid-cols-12 gap-3 items-center">
                  <div className="col-span-12 md:col-span-4">
                    <input
                      type="text"
                      required
                      placeholder="Item description *"
                      value={it.description}
                      onChange={(e) => handleItemChange(idx, 'description', e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div className="col-span-6 md:col-span-3">
                    <select
                      value={it.budget_line_id}
                      onChange={(e) => handleItemChange(idx, 'budget_line_id', e.target.value)}
                      className="w-full px-2 py-1.5 bg-white border border-gray-300 rounded text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">No Budget Line</option>
                      {budgetLines.map((bl) => (
                        <option key={bl.id} value={bl.id}>
                          {bl.code} - {bl.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="col-span-3 md:col-span-2">
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      placeholder="Qty"
                      value={it.quantity}
                      onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                      className="w-full px-2 py-1.5 bg-white border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div className="col-span-3 md:col-span-2">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="Unit Price"
                      value={it.unit_price}
                      onChange={(e) => handleItemChange(idx, 'unit_price', e.target.value)}
                      className="w-full px-2 py-1.5 bg-white border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div className="col-span-12 md:col-span-1 flex items-center justify-between md:justify-end gap-2">
                    <span className="text-xs font-semibold text-gray-700 md:hidden">Line Total:</span>
                    <span className="text-xs font-medium text-gray-900">{formatCAD(lineEst)}</span>
                    <button
                      type="button"
                      onClick={() => removeItem(idx)}
                      disabled={items.length <= 1}
                      className="text-gray-400 hover:text-red-600 disabled:opacity-30 transition-colors p-1"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Totals Summary */}
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200 flex flex-col items-end space-y-1.5 text-xs text-gray-600">
            <div className="flex justify-between w-48">
              <span>Subtotal:</span>
              <span className="font-semibold text-gray-900">{formatCAD(subtotal)}</span>
            </div>
            {form.request_type === 'PURCHASE_ORDER' && (
              <div className="flex justify-between w-48">
                <span>Estimated Tax:</span>
                <span className="font-semibold text-gray-900">{formatCAD(taxAmount)}</span>
              </div>
            )}
            <div className="flex justify-between w-48 pt-1.5 border-t border-gray-300 text-sm font-bold text-gray-900">
              <span>Total:</span>
              <span className="text-indigo-600">{formatCAD(totalAmount)}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            disabled={submitting}
            onClick={() => handleSubmit(false)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4 text-gray-500" />
            Save as Draft
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => handleSubmit(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            Submit for Approval
          </button>
        </div>
      </div>
    </div>
  );
}

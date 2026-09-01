import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  PlusCircle, 
  Calendar, 
  Layers, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';
import financeApi from '../api/finance';

export default function FinanceRates() {
  const [rates, setRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // New Rate Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    home_type: 'FOSTER_HOME',
    level_of_care: '',
    age_min: '0',
    age_max: '17',
    daily_rate: '',
    effective_from: '',
    effective_to: '',
  });

  useEffect(() => {
    loadRates();
  }, []);

  async function loadRates() {
    try {
      setLoading(true);
      const data = await financeApi.getBillingRates(null, false);
      setRates(data || []);
    } catch (err) {
      console.error('Failed to load billing rates:', err);
      setError('Unable to load billing rate schedules.');
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
      await financeApi.createBillingRate({
        home_type: form.home_type,
        level_of_care: form.level_of_care.trim() || undefined,
        age_min: parseInt(form.age_min, 10),
        age_max: parseInt(form.age_max, 10),
        daily_rate: form.daily_rate,
        effective_from: form.effective_from,
        effective_to: form.effective_to || undefined,
        is_active: true,
      });
      setCreateModalOpen(false);
      setForm({
        home_type: 'FOSTER_HOME',
        level_of_care: '',
        age_min: '0',
        age_max: '17',
        daily_rate: '',
        effective_from: '',
        effective_to: '',
      });
      await loadRates();
    } catch (err) {
      console.error('Failed to create billing rate:', err);
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to create rate.';
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
          <h1 className="text-2xl font-bold text-gray-900">Per-Diem Rate Schedules</h1>
          <p className="text-sm text-gray-500 mt-1">
            Temporal rate versioning by facility type and age brackets for placement billing.
          </p>
        </div>
        <button
          onClick={() => {
            const today = new Date().toISOString().split('T')[0];
            setForm((prev) => ({ ...prev, effective_from: today }));
            setCreateModalOpen(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <PlusCircle className="w-4 h-4" />
          Add Rate Schedule
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Rates Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-500">Loading rate schedules...</div>
        ) : rates.length === 0 ? (
          <div className="p-12 text-center">
            <TrendingUp className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-gray-900">No rate schedules configured</h3>
            <p className="text-xs text-gray-500 mt-1">
              Add foster care and group home per-diem rates to enable automatic placement billing.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3.5">Facility / Home Type</th>
                  <th className="px-6 py-3.5">Age Bracket</th>
                  <th className="px-6 py-3.5">Effective Window</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Per-Diem Rate (CAD)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {rates.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50/75 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {r.home_type} {r.level_of_care ? `• ${r.level_of_care}` : ''}
                    </td>
                    <td className="px-6 py-4 text-gray-600 text-xs">
                      {r.age_min} to {r.age_max} years
                    </td>
                    <td className="px-6 py-4 text-gray-600 text-xs">
                      {r.effective_from} to {r.effective_to || 'Present (Open)'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        r.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {r.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-bold text-gray-900">
                      {formatCAD(r.daily_rate)} <span className="text-xs font-normal text-gray-500">/ day</span>
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
            <h3 className="text-lg font-bold text-gray-900">Add Rate Schedule</h3>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Facility / Home Type *
              </label>
              <select
                value={form.home_type}
                onChange={(e) => setForm({ ...form, home_type: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm text-gray-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="FOSTER_HOME">Foster Home</option>
                <option value="KINSHIP_HOME">Kinship Home</option>
                <option value="GROUP_HOME">Group Home</option>
                <option value="TREATMENT_FACILITY">Treatment Facility</option>
                <option value="EMERGENCY_SHELTER">Emergency Shelter</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Age Min (Years) *
                </label>
                <input
                  type="number"
                  min="0"
                  max="18"
                  required
                  value={form.age_min}
                  onChange={(e) => setForm({ ...form, age_min: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Age Max (Years) *
                </label>
                <input
                  type="number"
                  min="0"
                  max="18"
                  required
                  value={form.age_max}
                  onChange={(e) => setForm({ ...form, age_max: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Daily Per-Diem Rate (CAD) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                placeholder="e.g. 75.50"
                value={form.daily_rate}
                onChange={(e) => setForm({ ...form, daily_rate: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Effective From *
                </label>
                <input
                  type="date"
                  required
                  value={form.effective_from}
                  onChange={(e) => setForm({ ...form, effective_from: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Effective To (Optional)
                </label>
                <input
                  type="date"
                  value={form.effective_to}
                  onChange={(e) => setForm({ ...form, effective_to: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
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
                {creating ? 'Saving...' : 'Save Rate'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

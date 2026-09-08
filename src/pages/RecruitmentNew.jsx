import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  UserPlus,
  Plus,
  Trash2,
  AlertTriangle,
  Send,
  User
} from 'lucide-react';
import resourceRecruitmentApi from '../api/resourceRecruitment';
import { api } from '../api/client';

export default function RecruitmentNew() {
  const navigate = useNavigate();
  const [persons, setPersons] = useState([]);
  const [loadingPersons, setLoadingPersons] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [primaryPersonId, setPrimaryPersonId] = useState('');
  const [hasSecondary, setHasSecondary] = useState(false);
  const [secondaryPersonId, setSecondaryPersonId] = useState('');
  const [initialState, setInitialState] = useState('INQUIRY');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    async function loadPersons() {
      try {
        setLoadingPersons(true);
        // Attempt to fetch clients / persons for convenient dropdown
        const res = await api.get('/clients', { params: { limit: 100 } });
        const list = res.data?.items || res.data || [];
        setPersons(list);
      } catch (err) {
        console.warn('Could not pre-load persons:', err);
      } finally {
        setLoadingPersons(false);
      }
    }
    loadPersons();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!primaryPersonId.trim()) {
      setError('A valid Primary Applicant Person UUID is required.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const applicants = [
        {
          person_id: primaryPersonId.trim(),
          role: 'PRIMARY_APPLICANT',
        },
      ];

      if (hasSecondary && secondaryPersonId.trim()) {
        applicants.push({
          person_id: secondaryPersonId.trim(),
          role: 'SECONDARY_APPLICANT',
        });
      }

      const payload = {
        applicants,
        initial_state: initialState,
        notes: notes || undefined,
      };

      const res = await resourceRecruitmentApi.create(payload);
      navigate(`/resource-team/recruitment/${res.data.id}`);
    } catch (err) {
      console.error('Failed to create recruitment inquiry:', err);
      const msg = err.response?.data?.detail || 'Failed to create recruitment record. Verify Person UUIDs.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-16">
      <div>
        <Link
          to="/resource-team/recruitment"
          className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Pipeline
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-3 border-b border-gray-200 dark:border-gray-700 pb-4">
          <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
            <UserPlus className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              New Caregiver Inquiry / Application
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Initiate an authoritative recruitment application linked to canonical Person records.
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-6">
          {/* Primary Applicant */}
          <div className="space-y-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
              Primary Applicant (Required)
            </label>

            {persons.length > 0 && (
              <div>
                <label className="block text-xs text-gray-500 mb-1">Select from Known Persons / Clients:</label>
                <select
                  value={primaryPersonId}
                  onChange={(e) => setPrimaryPersonId(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="">-- Select Person --</option>
                  {persons.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.first_name} {p.last_name} ({p.id})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Or Enter Canonical Person UUID:
              </label>
              <input
                type="text"
                required
                value={primaryPersonId}
                onChange={(e) => setPrimaryPersonId(e.target.value)}
                placeholder="e.g. a0000000-0000-0000-0000-000000000001"
                className="w-full text-xs p-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 font-mono text-gray-900 dark:text-white"
              />
            </div>
          </div>

          {/* Secondary Applicant Toggle */}
          <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-bold text-gray-900 dark:text-white">Co-Applicant / Secondary Caregiver</div>
                <div className="text-[11px] text-gray-500">Include spouse, partner, or secondary caregiver on this application</div>
              </div>
              <button
                type="button"
                onClick={() => setHasSecondary(!hasSecondary)}
                className={`px-3 py-1 text-xs font-semibold rounded-md border transition-colors ${
                  hasSecondary
                    ? 'bg-rose-50 border-rose-200 text-rose-700'
                    : 'bg-indigo-50 border-indigo-200 text-indigo-700'
                }`}
              >
                {hasSecondary ? 'Remove Co-Applicant' : '+ Add Co-Applicant'}
              </button>
            </div>

            {hasSecondary && (
              <div className="mt-4 space-y-3 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                {persons.length > 0 && (
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Select Co-Applicant from Known Persons:</label>
                    <select
                      value={secondaryPersonId}
                      onChange={(e) => setSecondaryPersonId(e.target.value)}
                      className="w-full text-xs p-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="">-- Select Person --</option>
                      {persons.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.first_name} {p.last_name} ({p.id})
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Co-Applicant Person UUID:</label>
                  <input
                    type="text"
                    value={secondaryPersonId}
                    onChange={(e) => setSecondaryPersonId(e.target.value)}
                    placeholder="e.g. b0000000-0000-0000-0000-000000000002"
                    className="w-full text-xs p-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 font-mono text-gray-900 dark:text-white"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Initial Stage */}
          <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-1">
              Initial Recruitment Stage
            </label>
            <select
              value={initialState}
              onChange={(e) => setInitialState(e.target.value)}
              className="w-full text-xs p-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="INQUIRY">INQUIRY (Default - Initial contact & interest)</option>
              <option value="ORIENTATION">ORIENTATION (Information session attended)</option>
              <option value="APPLICATION">APPLICATION (Formal application submitted)</option>
            </select>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-1">
              Inquiry Notes & Household Background
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record initial outreach, cultural connection, preferred home type, or special considerations..."
              className="w-full text-xs p-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Link
              to="/resource-team/recruitment"
              className="px-4 py-2 border border-gray-300 text-xs font-semibold text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm"
            >
              <Send className="w-3.5 h-3.5" />
              {submitting ? 'Creating...' : 'Initiate Application'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

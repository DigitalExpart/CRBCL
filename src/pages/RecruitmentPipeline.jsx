import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Layers,
  PlusCircle,
  Search,
  Filter,
  ArrowRight,
  User,
  Home,
  Clock,
  AlertTriangle,
  ChevronRight
} from 'lucide-react';
import resourceRecruitmentApi from '../api/resourceRecruitment';

export default function RecruitmentPipeline() {
  const [searchParams, setSearchParams] = useSearchParams();
  const stateFilter = searchParams.get('state') || '';

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const stages = [
    { key: '', label: 'All Stages' },
    { key: 'INQUIRY', label: 'Inquiry' },
    { key: 'ORIENTATION', label: 'Orientation' },
    { key: 'APPLICATION', label: 'Application' },
    { key: 'ASSESSMENT', label: 'Assessment' },
    { key: 'APPROVAL_REVIEW', label: 'Approval Review' },
    { key: 'APPROVED', label: 'Approved' },
    { key: 'ON_HOLD', label: 'On Hold' },
    { key: 'DECLINED', label: 'Declined' },
    { key: 'WITHDRAWN', label: 'Withdrawn' },
  ];

  useEffect(() => {
    async function loadRecruitments() {
      try {
        setLoading(true);
        const params = {};
        if (stateFilter) {
          params.state = stateFilter;
        }
        const res = await resourceRecruitmentApi.list(params);
        setItems(res.data || []);
      } catch (err) {
        console.error('Failed to load recruitment pipeline:', err);
        setError('Unable to load recruitment applications.');
      } finally {
        setLoading(false);
      }
    }
    loadRecruitments();
  }, [stateFilter]);

  const getStateBadge = (st) => {
    const map = {
      INQUIRY: 'bg-blue-50 text-blue-700 border-blue-200',
      ORIENTATION: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      APPLICATION: 'bg-purple-50 text-purple-700 border-purple-200',
      ASSESSMENT: 'bg-amber-50 text-amber-700 border-amber-200',
      APPROVAL_REVIEW: 'bg-orange-50 text-orange-700 border-orange-200',
      APPROVED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      ON_HOLD: 'bg-yellow-50 text-yellow-700 border-yellow-200',
      DECLINED: 'bg-rose-50 text-rose-700 border-rose-200',
      WITHDRAWN: 'bg-slate-50 text-slate-700 border-slate-200',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${map[st] || 'bg-gray-100 text-gray-800'}`}>
        {st}
      </span>
    );
  };

  const filteredItems = items.filter((item) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (item.primary_applicant_name && item.primary_applicant_name.toLowerCase().includes(term)) ||
      (item.resource_home_code && item.resource_home_code.toLowerCase().includes(term)) ||
      (item.resource_home_name && item.resource_home_name.toLowerCase().includes(term)) ||
      (item.notes && item.notes.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Caregiver Recruitment Pipeline</h1>
          <p className="text-sm text-gray-500 mt-1">
            Track inquiries, orientations, assessments, and approvals for resource homes.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/resource-team/recruitment/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            New Inquiry / Application
          </Link>
          <Link
            to="/resource-team"
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            Dashboard
          </Link>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {stages.map((st) => (
          <button
            key={st.key}
            onClick={() => {
              if (st.key) {
                setSearchParams({ state: st.key });
              } else {
                setSearchParams({});
              }
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
              stateFilter === st.key
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {st.label}
          </button>
        ))}
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-2 shadow-sm">
        <Search className="w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search applicants, resource home ID, or notes..."
          className="w-full text-sm bg-transparent focus:outline-none text-gray-900 dark:text-white"
        />
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-500" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Table / List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl">
          <Layers className="w-12 h-12 mx-auto text-gray-300" />
          <h3 className="mt-3 text-sm font-semibold text-gray-900 dark:text-white">No recruitment applications found</h3>
          <p className="mt-1 text-xs text-gray-500">
            {stateFilter ? `No applications currently in stage '${stateFilter}'.` : 'Get started by creating a new inquiry.'}
          </p>
          <div className="mt-4">
            <Link
              to="/resource-team/recruitment/new"
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-md bg-indigo-600 text-white hover:bg-indigo-700"
            >
              <PlusCircle className="w-3.5 h-3.5" /> Create Application
            </Link>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Primary Applicant / Household
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Stage
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Allocated Resource Home
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Created / Updated
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 flex items-center justify-center font-semibold text-xs">
                        <User className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-gray-900 dark:text-white">
                          {item.primary_applicant_name || 'Anonymous Applicant'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {item.applicant_count} applicant{item.applicant_count !== 1 ? 's' : ''}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStateBadge(item.current_state)}
                    {item.previous_state && item.current_state === 'ON_HOLD' && (
                      <span className="block text-[10px] text-gray-500 mt-0.5">
                        resumes to: {item.previous_state}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {item.resource_home_code ? (
                      <Link
                        to={`/placement-homes/${item.resource_home_id}`}
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:underline"
                      >
                        <Home className="w-3.5 h-3.5" />
                        {item.resource_home_code} {item.resource_home_name ? `(${item.resource_home_name})` : ''}
                      </Link>
                    ) : (
                      <span className="text-xs text-gray-400 italic">Not allocated yet</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                    <div>{new Date(item.created_at).toLocaleDateString()}</div>
                    <div className="text-[10px] text-gray-400">
                      Updated: {new Date(item.updated_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                    <Link
                      to={`/resource-team/recruitment/${item.id}`}
                      className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 font-semibold"
                    >
                      View Application <ChevronRight className="w-4 h-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

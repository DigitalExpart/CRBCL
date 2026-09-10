import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Users,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Info,
  Bed,
  MapPin,
  HeartHandshake,
  ArrowRight,
  Filter,
} from 'lucide-react';
import placementHomesApi from '../api/placementHomes';
import { toast } from '../components/ui/use-toast';

export default function PlacementMatching() {
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState({
    age: 6,
    gender: 'FEMALE',
    sibling_group_size: 1,
    primary_language: 'English',
    indigenous_community: '',
    medical_complexity: false,
    behavioural_needs: false,
    accessibility_needs: false,
    preferred_location: '',
    preferred_home_types: ['LICENSED_FOSTER'],
  });

  const [results, setResults] = useState(null);

  const handleEvaluate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await placementHomesApi.evaluateMatches({
        ...profile,
        age: parseInt(profile.age, 10),
        sibling_group_size: parseInt(profile.sibling_group_size, 10),
      });
      setResults(res.data);
      toast({
        title: 'Matching Evaluation Complete',
        description: `Evaluated ${res.data.total_homes_evaluated} homes: ${res.data.eligible_candidates.length} eligible.`,
      });
    } catch (err) {
      console.error('Matching evaluation error:', err);
      toast({
        variant: 'destructive',
        title: 'Evaluation Failed',
        description: err.response?.data?.detail || 'Failed to evaluate placement matches.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-800 pb-5">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Placement Matching Decision Support</h1>
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
            <Sparkles className="w-3 h-3" /> Assistive Intelligence
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Explainable, transparent matching evaluation. Decision-support only; final placements are determined by caseworkers.
        </p>
      </div>

      {/* Mandatory Regulatory Disclaimer */}
      <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-3">
        <Info className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
        <div>
          <span className="font-semibold">Professional Casework Authority Invariant:</span> This matching tool provides assistive decision-support factors. The software never autonomously places children or locks beds without human caseworker initiation through formal PlacementEpisode workflow.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Criteria Form */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
            <Filter className="w-4 h-4 text-indigo-600" />
            <h2 className="text-base font-bold text-gray-900 dark:text-white">Child Profile & Needs</h2>
          </div>

          <form onSubmit={handleEvaluate} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Child Age</label>
                <input
                  type="number"
                  min="0"
                  max="21"
                  required
                  value={profile.age}
                  onChange={(e) => setProfile({ ...profile, age: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg text-sm border-gray-300 dark:border-gray-700 dark:bg-gray-900"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Sibling Group Size</label>
                <input
                  type="number"
                  min="1"
                  max="8"
                  required
                  value={profile.sibling_group_size}
                  onChange={(e) => setProfile({ ...profile, sibling_group_size: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-lg text-sm border-gray-300 dark:border-gray-700 dark:bg-gray-900"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Indigenous Nation / Community</label>
              <input
                type="text"
                placeholder="e.g. Cowessess, Kahkewistahaw, Ochapowace"
                value={profile.indigenous_community}
                onChange={(e) => setProfile({ ...profile, indigenous_community: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border rounded-lg text-sm border-gray-300 dark:border-gray-700 dark:bg-gray-900"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Preferred Location / City</label>
              <input
                type="text"
                placeholder="e.g. Regina, Broadview, Yorkton"
                value={profile.preferred_location}
                onChange={(e) => setProfile({ ...profile, preferred_location: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border rounded-lg text-sm border-gray-300 dark:border-gray-700 dark:bg-gray-900"
              />
            </div>

            <div className="space-y-2 pt-2 border-t border-gray-100">
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300 block">Specific Care Needs</span>
              <label className="flex items-center gap-2 text-xs text-gray-700 dark:text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.medical_complexity}
                  onChange={(e) => setProfile({ ...profile, medical_complexity: e.target.checked })}
                  className="rounded border-gray-300 text-indigo-600"
                />
                Specialized Medical Complexity
              </label>
              <label className="flex items-center gap-2 text-xs text-gray-700 dark:text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.behavioural_needs}
                  onChange={(e) => setProfile({ ...profile, behavioural_needs: e.target.checked })}
                  className="rounded border-gray-300 text-indigo-600"
                />
                Intensive Behavioural Support
              </label>
              <label className="flex items-center gap-2 text-xs text-gray-700 dark:text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.accessibility_needs}
                  onChange={(e) => setProfile({ ...profile, accessibility_needs: e.target.checked })}
                  className="rounded border-gray-300 text-indigo-600"
                />
                Physical Accessibility / Wheelchair Ramp
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg shadow-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                'Evaluating Matches...'
              ) : (
                <>
                  <Sparkles className="w-4 h-4" /> Evaluate Compatible Homes
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-2 space-y-4">
          {!results && !loading && (
            <div className="bg-white dark:bg-gray-800 border border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-12 text-center text-gray-500">
              <HeartHandshake className="w-12 h-12 mx-auto text-gray-400 mb-3" />
              <h3 className="text-base font-semibold text-gray-700 dark:text-gray-300">Ready to Match</h3>
              <p className="text-xs mt-1 max-w-sm mx-auto">
                Configure the child's criteria on the left and click "Evaluate Compatible Homes" to see explainable matches.
              </p>
            </div>
          )}

          {results && (
            <div className="space-y-4">
              {/* Summary Stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-white dark:bg-gray-800 border rounded-lg text-center">
                  <div className="text-xs text-gray-500">Evaluated Homes</div>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">{results.total_homes_evaluated}</div>
                </div>
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-center">
                  <div className="text-xs text-emerald-700 font-medium">Eligible Candidates</div>
                  <div className="text-xl font-bold text-emerald-800">{results.eligible_candidates.length}</div>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
                  <div className="text-xs text-slate-600 font-medium">Excluded / Ineligible</div>
                  <div className="text-xl font-bold text-slate-700">{results.excluded_candidates.length}</div>
                </div>
              </div>

              {/* Eligible Candidates */}
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Compatible Resource Homes ({results.eligible_candidates.length})
                </h3>

                {results.eligible_candidates.length === 0 ? (
                  <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-800">
                    No eligible homes found matching all mandatory criteria (active capacity, licensing, clearances).
                  </div>
                ) : (
                  results.eligible_candidates.map((candidate) => (
                    <div
                      key={candidate.home_id}
                      className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm space-y-3"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-base text-gray-900 dark:text-white">{candidate.home_name}</span>
                            <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 border">{candidate.home_code}</span>
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                                candidate.compatibility_level === 'HIGH'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : candidate.compatibility_level === 'MODERATE'
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {candidate.compatibility_level} MATCH
                            </span>
                          </div>
                          <div className="text-xs text-gray-500 mt-1 flex items-center gap-4">
                            <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {candidate.city} {candidate.community ? `(${candidate.community})` : ''}</span>
                            <span className="flex items-center gap-1"><Bed className="w-3 h-3" /> {candidate.available_beds} beds available (cap: {candidate.total_capacity})</span>
                            <span className="flex items-center gap-1"><Users className="w-3 h-3" /> Primary: {candidate.primary_caregiver_name || '—'}</span>
                          </div>
                        </div>
                        <Link
                          to={`/placement-homes/${candidate.home_id}`}
                          className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold flex items-center gap-1"
                        >
                          View Home <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>

                      {/* Compatibility Highlights */}
                      {candidate.compatibility_notes.length > 0 && (
                        <div className="text-xs space-y-1 bg-emerald-50/70 p-2.5 rounded-lg border border-emerald-100 text-emerald-900">
                          {candidate.compatibility_notes.map((note, i) => (
                            <div key={i} className="flex items-center gap-1.5">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" /> {note}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Warnings if any */}
                      {candidate.warnings.length > 0 && (
                        <div className="text-xs space-y-1 bg-amber-50/70 p-2.5 rounded-lg border border-amber-100 text-amber-900">
                          {candidate.warnings.map((warn, i) => (
                            <div key={i} className="flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" /> {warn}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>

              {/* Excluded Candidates with Explanations */}
              {results.excluded_candidates.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-gray-200">
                  <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-rose-500" /> Excluded Homes ({results.excluded_candidates.length})
                  </h3>
                  <div className="space-y-2">
                    {results.excluded_candidates.map((cand) => (
                      <div
                        key={cand.home_id}
                        className="p-3 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-lg text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-gray-800 dark:text-gray-200">{cand.home_name} ({cand.home_code})</span>
                          <span className="text-rose-600 font-medium">Ineligible</span>
                        </div>
                        <ul className="list-disc pl-4 text-rose-700 space-y-0.5">
                          {cand.exclusion_reasons.map((reason, idx) => (
                            <li key={idx}>{reason}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

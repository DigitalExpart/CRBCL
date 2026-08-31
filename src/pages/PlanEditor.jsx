import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ChevronLeft,
  FileText,
  Shield,
  Plus,
  Trash2,
  Save,
  AlertTriangle,
  Users,
  Heart,
  Target,
  Calendar,
  MapPin,
} from 'lucide-react';
import { plansApi } from '../api/plans';

export default function PlanEditor() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [title, setTitle] = useState('');
  const [meetingDate, setMeetingDate] = useState('');
  const [meetingLocation, setMeetingLocation] = useState('');
  const [narrative, setNarrative] = useState('');
  const [planType, setPlanType] = useState('SAFETY_PLAN');
  const [planNumber, setPlanNumber] = useState('');
  const [caseId, setCaseId] = useState('');

  useEffect(() => {
    if (id) {
      plansApi
        .get(id)
        .then((plan) => {
          setTitle(plan.title);
          setPlanNumber(plan.plan_number);
          setPlanType(plan.plan_type);
          setCaseId(plan.case_id);

          const currV = plan.current_version;
          if (currV) {
            setMeetingDate(currV.meeting_date || '');
            setMeetingLocation(currV.meeting_location || '');
            setNarrative(currV.narrative || '');
          }
        })
        .catch((err) => setError(err.message || 'Failed to load plan'))
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleSave = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Plan Title is required.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await plansApi.update(id, {
        title: title.trim(),
        meeting_date: meetingDate || null,
        meeting_location: meetingLocation.trim() || null,
        narrative: narrative.trim() || null,
      });

      navigate(`/plans/${id}`);
    } catch (err) {
      setError(err.message || 'Failed to update plan.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-muted-foreground text-sm">
        Loading Plan Editor...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200 pb-16">
      {/* Navigation */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Link to={`/plans/${id}`} className="hover:text-primary flex items-center gap-1 font-medium">
          <ChevronLeft className="w-4 h-4" /> Back to Plan
        </Link>
        <span>/</span>
        <span className="font-mono text-foreground">{planNumber} (Editor)</span>
      </div>

      <div className="p-6 bg-card border border-border rounded-2xl shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b pb-4">
          <div className="flex items-center gap-3">
            <div
              className={`p-2.5 rounded-xl ${
                planType === 'SAFETY_PLAN'
                  ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                  : 'bg-purple-500/10 text-purple-600 dark:text-purple-400'
              }`}
            >
              {planType === 'SAFETY_PLAN' ? <Shield className="w-6 h-6" /> : <FileText className="w-6 h-6" />}
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Edit Plan Details</h1>
              <p className="text-xs text-muted-foreground font-mono">{planNumber}</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">Plan Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 bg-background border rounded-lg text-sm focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-muted-foreground" /> Meeting Date
              </label>
              <input
                type="date"
                value={meetingDate}
                onChange={(e) => setMeetingDate(e.target.value)}
                className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-muted-foreground" /> Meeting Location
              </label>
              <input
                type="text"
                value={meetingLocation}
                onChange={(e) => setMeetingLocation(e.target.value)}
                placeholder="e.g. Lodge Room 3, Family Home"
                className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">Clinical Narrative & Context</label>
            <textarea
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
              rows={4}
              placeholder="Clinical context, background discussion, consensus items..."
              className="w-full px-3 py-2 bg-background border rounded-lg text-sm focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="pt-4 border-t flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate(`/plans/${id}`)}
              className="px-4 py-2 border rounded-xl text-sm font-medium text-muted-foreground hover:bg-muted transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-sm shadow-md hover:bg-primary/90 transition flex items-center gap-2"
            >
              {saving ? <span>Saving...</span> : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Plan Changes</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

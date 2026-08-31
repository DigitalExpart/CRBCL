import React, { useState } from 'react';
import { X, Copy, Calendar, MapPin, Check, AlertTriangle } from 'lucide-react';
import { plansApi } from '../../api/plans';

export default function PlanCloneModal({ isOpen, onClose, plan, onCloned }) {
  if (!isOpen || !plan) return null;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newTitle, setNewTitle] = useState(`Copy of ${plan.title}`);
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().split('T')[0]);
  const [meetingLocation, setMeetingLocation] = useState(
    plan.current_version?.meeting_location || 'CRBCL Wellness Centre'
  );
  const [includeCompletedGoals, setIncludeCompletedGoals] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      setError('Please provide a new Plan Title.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        new_title: newTitle.trim(),
        meeting_date: meetingDate || null,
        meeting_location: meetingLocation.trim() || null,
        include_completed_goals: includeCompletedGoals,
      };

      const cloned = await plansApi.clone(plan.id, payload);
      onCloned(cloned);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to clone plan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-border flex items-center justify-between bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Copy className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">Clone Plan Blueprint</h2>
              <p className="text-xs text-muted-foreground">
                Duplicate structure from {plan.plan_number} into a new active draft
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">New Plan Title *</label>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="w-full px-3 py-2 bg-background border rounded-lg text-sm focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground flex items-center gap-1">
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
              <label className="text-xs font-medium text-foreground flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-muted-foreground" /> Location
              </label>
              <input
                type="text"
                value={meetingLocation}
                onChange={(e) => setMeetingLocation(e.target.value)}
                className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="p-4 bg-muted/20 border rounded-xl space-y-2">
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={includeCompletedGoals}
                onChange={(e) => setIncludeCompletedGoals(e.target.checked)}
                className="mt-0.5 rounded text-primary"
              />
              <div>
                <span className="text-xs font-semibold text-foreground">Carry Over Completed Goals</span>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  By default, only active and in-progress goals/activities are carried over into the new plan.
                </p>
              </div>
            </label>
          </div>

          <div className="pt-3 border-t flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-xl text-sm font-medium text-muted-foreground hover:bg-muted transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-sm shadow-md hover:bg-primary/90 transition flex items-center gap-2"
            >
              {loading ? <span>Cloning...</span> : (
                <>
                  <Check className="w-4 h-4" />
                  <span>Clone into New Plan</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { fleetApi } from '@/api/fleet';
import { X, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function TripCheckinModal({ trip, isOpen, onClose, onSuccess }) {
  const [endOdometer, setEndOdometer] = useState(trip?.start_odometer || 0);
  const [checkinCondition, setCheckinCondition] = useState('GOOD');
  const [hasDamageFlag, setHasDamageFlag] = useState(false);
  const [hasMaintenanceIssue, setHasMaintenanceIssue] = useState(false);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen || !trip) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        end_odometer: parseFloat(endOdometer),
        checkin_condition: checkinCondition,
        has_damage_flag: hasDamageFlag,
        has_maintenance_issue: hasMaintenanceIssue,
        notes,
      };
      await fleetApi.checkinVehicle(trip.id, payload);
      onSuccess();
      onClose();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to check in vehicle.');
    } finally {
      setSubmitting(false);
    }
  };

  const calculatedDistance = Math.max(0, (parseFloat(endOdometer) || 0) - trip.start_odometer);

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div>
            <h3 className="text-lg font-bold text-foreground">Vehicle Check-In</h3>
            <p className="text-xs text-muted-foreground">
              Trip #{trip.id.slice(0, 8)} • Start Odometer: {trip.start_odometer} km
            </p>
          </div>
          <button onClick={onClose} className="p-1 text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Ending Odometer (km) *
              </label>
              <input
                type="number"
                step="0.1"
                required
                min={trip.start_odometer}
                value={endOdometer}
                onChange={(e) => setEndOdometer(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Distance Traveled
              </label>
              <div className="px-3 py-2 bg-muted/40 border border-border rounded-lg text-sm font-bold text-primary">
                {calculatedDistance.toFixed(1)} km
              </div>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1">
              Return Condition
            </label>
            <select
              value={checkinCondition}
              onChange={(e) => setCheckinCondition(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
            >
              <option value="EXCELLENT">Clean / Excellent</option>
              <option value="GOOD">Good</option>
              <option value="FAIR">Fair</option>
              <option value="NEEDS_CLEANING">Needs Cleaning</option>
              <option value="MINOR_DAMAGES">Minor Body Damage</option>
              <option value="MECHANICAL_ISSUE">Mechanical Issue</option>
            </select>
          </div>

          <div className="space-y-2 pt-2 border-t border-border">
            <label className="flex items-center gap-2 text-xs font-medium text-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={hasDamageFlag}
                onChange={(e) => setHasDamageFlag(e.target.checked)}
                className="rounded border-border text-primary focus:ring-primary"
              />
              Flag Vehicle Body Damage
            </label>

            <label className="flex items-center gap-2 text-xs font-medium text-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={hasMaintenanceIssue}
                onChange={(e) => setHasMaintenanceIssue(e.target.checked)}
                className="rounded border-border text-primary focus:ring-primary"
              />
              Flag Mechanical Issue (Sends to Maintenance)
            </label>
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1">
              Check-In Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Return notes or maintenance issue details..."
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-border pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? 'Checking In...' : 'Complete Check-In'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

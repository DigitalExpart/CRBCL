import React, { useState } from 'react';
import { fleetApi } from '@/api/fleet';
import { X, Navigation, Gauge, FileText } from 'lucide-react';

export default function TripCheckoutModal({ vehicle, isOpen, onClose, onSuccess }) {
  const [purpose, setPurpose] = useState('');
  const [destination, setDestination] = useState('');
  const [startOdometer, setStartOdometer] = useState(vehicle?.odometer_km || 0);
  const [checkoutCondition, setCheckoutCondition] = useState('GOOD');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen || !vehicle) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        driver_id: vehicle.current_driver_id || '00000000-0000-0000-0000-000000000000', // Replaced by caller or active user
        purpose,
        destination,
        start_odometer: parseFloat(startOdometer),
        checkout_condition: checkoutCondition,
        notes,
      };
      await fleetApi.checkoutVehicle(vehicle.id, payload);
      onSuccess();
      onClose();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to check out vehicle.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div>
            <h3 className="text-lg font-bold text-foreground">
              Check-Out Vehicle {vehicle.vehicle_internal_id}
            </h3>
            <p className="text-xs text-muted-foreground">
              {vehicle.make} {vehicle.model} • Current Odometer: {vehicle.odometer_km} km
            </p>
          </div>
          <button onClick={onClose} className="p-1 text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1">
              Trip Purpose *
            </label>
            <input
              type="text"
              required
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              placeholder="e.g. Client Family Transport / Home Visit"
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1">
              Destination *
            </label>
            <input
              type="text"
              required
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Fort Qu'Appelle Community Center"
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Starting Odometer (km) *
              </label>
              <input
                type="number"
                step="0.1"
                required
                min={vehicle.odometer_km}
                value={startOdometer}
                onChange={(e) => setStartOdometer(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Initial Condition
              </label>
              <select
                value={checkoutCondition}
                onChange={(e) => setCheckoutCondition(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
              >
                <option value="EXCELLENT">Excellent</option>
                <option value="GOOD">Good</option>
                <option value="FAIR">Fair</option>
                <option value="NEEDS_CLEANING">Needs Cleaning</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground block mb-1">
              Check-Out Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional check-out observations or vehicle condition notes..."
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
              {submitting ? 'Checking Out...' : 'Confirm Check-Out'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fleetApi } from '@/api/fleet';
import { Wrench, Plus, ArrowLeft, CheckCircle2, Clock } from 'lucide-react';

export default function FleetMaintenance() {
  const navigate = useNavigate();
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  // New Maintenance Schedule State
  const [showModal, setShowModal] = useState(false);
  const [vehicleId, setVehicleId] = useState('');
  const [maintType, setMaintType] = useState('OIL_CHANGE');
  const [scheduledDate, setScheduledDate] = useState('');
  const [providerName, setProviderName] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const vRes = await fleetApi.getVehicles();
      setVehicles(vRes.data || []);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  const handleSchedule = async (e) => {
    e.preventDefault();
    try {
      await fleetApi.scheduleMaintenance({
        vehicle_id: vehicleId,
        maintenance_type: maintType,
        scheduled_date: scheduledDate || undefined,
        provider_name: providerName || undefined,
        description,
      });
      setShowModal(false);
      alert('Maintenance successfully scheduled!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to schedule maintenance.');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/fleet')}
            className="p-2 border border-border rounded-lg text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Fleet Maintenance & Service</h1>
            <p className="text-sm text-muted-foreground">
              Schedule oil changes, tire rotations, inspections, and repair work.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" /> Schedule Maintenance
        </button>
      </div>

      <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
        <h3 className="font-bold text-foreground text-base">Agency Fleet Service Overview</h3>
        <p className="text-xs text-muted-foreground">
          Vehicles flagged with maintenance issues during trip check-in or scheduled for preventive maintenance appear here.
        </p>

        {loading ? (
          <div className="p-6 text-center text-muted-foreground text-xs">Loading fleet maintenance data...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vehicles.map((v) => (
              <div key={v.id} className="p-4 bg-muted/30 border border-border rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-foreground text-sm">{v.vehicle_internal_id}</span>
                  <span className="text-xs px-2 py-0.5 rounded font-bold bg-primary/10 text-primary">
                    {v.status}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {v.make} {v.model} • {v.odometer_km} km
                </div>
                <div className="text-xs text-muted-foreground pt-1 border-t border-border flex justify-between">
                  <span>Next Date: {v.next_maintenance_date || 'None'}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Schedule Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-foreground">Schedule Vehicle Maintenance</h3>

            <form onSubmit={handleSchedule} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Select Vehicle *</label>
                <select
                  required
                  value={vehicleId}
                  onChange={(e) => setVehicleId(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                >
                  <option value="">Select a vehicle...</option>
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.vehicle_internal_id} ({v.make} {v.model})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">Service Type *</label>
                  <select
                    value={maintType}
                    onChange={(e) => setMaintType(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none"
                  >
                    <option value="OIL_CHANGE">Oil Change</option>
                    <option value="TIRE_ROTATION">Tire Rotation</option>
                    <option value="BRAKE_INSPECTION">Brake Inspection</option>
                    <option value="ANNUAL_INSPECTION">Annual Safety</option>
                    <option value="REPAIR">Mechanical Repair</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">Scheduled Date</label>
                  <input
                    type="date"
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Service Provider</label>
                <input
                  type="text"
                  value={providerName}
                  onChange={(e) => setProviderName(e.target.value)}
                  placeholder="e.g. Regina Fleet Maintenance"
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Description *</label>
                <textarea
                  rows={2}
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Details of service to be performed..."
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                />
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-border pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
                >
                  Confirm Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

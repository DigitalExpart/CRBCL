import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fleetApi } from '@/api/fleet';
import TripCheckoutModal from '@/components/fleet/TripCheckoutModal';
import TripCheckinModal from '@/components/fleet/TripCheckinModal';
import FleetMap from '@/components/fleet/FleetMap';
import {
  ArrowLeft,
  Truck,
  Gauge,
  Calendar,
  ShieldCheck,
  Wrench,
  Navigation,
  Trash2,
  MapPin,
} from 'lucide-react';

export default function VehicleDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check out / Check in modals
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [showCheckinModal, setShowCheckinModal] = useState(false);

  useEffect(() => {
    loadVehicleDetail();
  }, [id]);

  const loadVehicleDetail = async () => {
    setLoading(true);
    try {
      const res = await fleetApi.getVehicleDetail(id);
      setData(res.data);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  const handleArchive = async () => {
    if (!confirm('Are you sure you want to retire and archive this vehicle asset?')) return;
    try {
      await fleetApi.archiveVehicle(id);
      loadVehicleDetail();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to archive vehicle.');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading vehicle profile...</div>;
  }

  if (!data || !data.vehicle) {
    return <div className="p-8 text-center text-muted-foreground">Vehicle not found.</div>;
  }

  const { vehicle, latest_location, is_location_stale } = data;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/fleet/vehicles')}
            className="p-2 border border-border rounded-lg text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-foreground">{vehicle.vehicle_internal_id}</h1>
              <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-primary/10 text-primary uppercase">
                {vehicle.status}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {vehicle.make} {vehicle.model} ({vehicle.year}) • Licence Plate: {vehicle.licence_plate}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {vehicle.status === 'AVAILABLE' && (
            <button
              onClick={() => setShowCheckoutModal(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
            >
              Check Out Vehicle
            </button>
          )}

          {vehicle.status !== 'RETIRED' && (
            <button
              onClick={handleArchive}
              className="p-2 border border-border text-rose-500 hover:bg-rose-500/10 rounded-lg text-xs font-medium"
              title="Archive Vehicle"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Specs & Info Panel */}
        <div className="bg-card border border-border rounded-xl p-5 space-y-4 shadow-sm">
          <h3 className="font-bold text-foreground text-base border-b border-border pb-2">
            Asset Specifications
          </h3>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Vehicle Type</span>
              <span className="font-semibold text-foreground uppercase">{vehicle.vehicle_type}</span>
            </div>

            <div className="flex justify-between">
              <span className="text-muted-foreground">Current Odometer</span>
              <span className="font-bold text-primary">{vehicle.odometer_km} km</span>
            </div>

            <div className="flex justify-between">
              <span className="text-muted-foreground">Insurance Expiry</span>
              <span className="font-medium text-foreground">
                {vehicle.insurance_expiry ? new Date(vehicle.insurance_expiry).toLocaleDateString() : 'N/A'}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-muted-foreground">Next Maintenance</span>
              <span className="font-medium text-foreground">
                {vehicle.next_maintenance_date ? new Date(vehicle.next_maintenance_date).toLocaleDateString() : 'None Scheduled'}
              </span>
            </div>

            {vehicle.notes && (
              <div className="pt-2 border-t border-border">
                <span className="text-xs font-semibold text-muted-foreground block mb-1">Notes</span>
                <p className="text-xs text-foreground bg-muted/40 p-2 rounded border border-border">
                  {vehicle.notes}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Live GPS Map Panel */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="font-bold text-foreground text-base">Current GPS Location</h3>
          <FleetMap vehicles={[{ vehicle, latest_location, is_location_stale }]} height="380px" />
        </div>
      </div>

      {/* Check Out Modal */}
      {showCheckoutModal && (
        <TripCheckoutModal
          vehicle={vehicle}
          isOpen={showCheckoutModal}
          onClose={() => setShowCheckoutModal(false)}
          onSuccess={loadVehicleDetail}
        />
      )}
    </div>
  );
}

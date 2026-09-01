import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fleetApi } from '@/api/fleet';
import TripCheckoutModal from '@/components/fleet/TripCheckoutModal';
import {
  Truck,
  Plus,
  Search,
  ArrowLeft,
  CheckCircle2,
  Navigation,
  Wrench,
  AlertTriangle,
  FileText,
} from 'lucide-react';

export default function VehiclesList() {
  const navigate = useNavigate();
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Checkout Modal State
  const [selectedVehicleForCheckout, setSelectedVehicleForCheckout] = useState(null);

  // New Vehicle Modal State
  const [showNewModal, setShowNewModal] = useState(false);
  const [newInternalId, setNewInternalId] = useState('');
  const [newMake, setNewMake] = useState('');
  const [newModel, setNewModel] = useState('');
  const [newYear, setNewYear] = useState(new Date().getFullYear());
  const [newPlate, setNewPlate] = useState('');
  const [newType, setNewType] = useState('CAR');
  const [newOdometer, setNewOdometer] = useState(0);

  useEffect(() => {
    loadVehicles();
  }, [statusFilter, typeFilter, searchTerm]);

  const loadVehicles = async () => {
    setLoading(true);
    try {
      const res = await fleetApi.getVehicles({
        status: statusFilter || undefined,
        vehicle_type: typeFilter || undefined,
        search: searchTerm || undefined,
      });
      setVehicles(res.data || []);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVehicle = async (e) => {
    e.preventDefault();
    try {
      await fleetApi.createVehicle({
        vehicle_internal_id: newInternalId,
        make: newMake,
        model: newModel,
        year: parseInt(newYear),
        licence_plate: newPlate,
        vehicle_type: newType,
        odometer_km: parseFloat(newOdometer),
      });
      setShowNewModal(false);
      loadVehicles();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create vehicle.');
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/fleet')}
            className="p-2 border border-border rounded-lg text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Agency Vehicle Directory</h1>
            <p className="text-sm text-muted-foreground">
              Browse vehicle assets, inspect current mileage, and perform trip check-outs.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowNewModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" /> Register Vehicle
        </button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by vehicle ID, plate, make, or model..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 bg-background border border-border rounded-lg text-xs text-foreground focus:outline-none"
        >
          <option value="">All Statuses</option>
          <option value="AVAILABLE">Available</option>
          <option value="IN_USE">In Use</option>
          <option value="MAINTENANCE">Maintenance</option>
          <option value="OUT_OF_SERVICE">Out of Service</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 bg-background border border-border rounded-lg text-xs text-foreground focus:outline-none"
        >
          <option value="">All Vehicle Types</option>
          <option value="CAR">Car</option>
          <option value="VAN">Van</option>
          <option value="SUV">SUV</option>
          <option value="TRUCK">Truck</option>
        </select>
      </div>

      {/* Vehicles Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">Loading vehicle directory...</div>
        ) : vehicles.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">No vehicles found matching filter criteria.</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/50 text-muted-foreground font-medium border-b border-border text-xs uppercase">
              <tr>
                <th className="p-4">Vehicle ID</th>
                <th className="p-4">Make / Model / Year</th>
                <th className="p-4">Licence Plate</th>
                <th className="p-4">Type</th>
                <th className="p-4">Odometer (km)</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {vehicles.map((v) => (
                <tr key={v.id} className="hover:bg-muted/30 transition-colors">
                  <td className="p-4 font-bold text-foreground">{v.vehicle_internal_id}</td>
                  <td className="p-4 text-foreground">
                    {v.make} {v.model} ({v.year})
                  </td>
                  <td className="p-4 font-semibold text-muted-foreground">{v.licence_plate}</td>
                  <td className="p-4 text-xs font-semibold text-muted-foreground uppercase">{v.vehicle_type}</td>
                  <td className="p-4 font-bold text-primary">{v.odometer_km} km</td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-bold ${
                        v.status === 'AVAILABLE'
                          ? 'bg-emerald-500/10 text-emerald-600'
                          : v.status === 'IN_USE'
                          ? 'bg-amber-500/10 text-amber-600'
                          : 'bg-rose-500/10 text-rose-600'
                      }`}
                    >
                      {v.status}
                    </span>
                  </td>
                  <td className="p-4 text-right space-x-2">
                    {v.status === 'AVAILABLE' && (
                      <button
                        onClick={() => setSelectedVehicleForCheckout(v)}
                        className="px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:bg-primary/90 transition-colors"
                      >
                        Check Out
                      </button>
                    )}
                    <button
                      onClick={() => navigate(`/fleet/vehicles/${v.id}`)}
                      className="px-3 py-1.5 border border-border text-foreground rounded-md text-xs font-medium hover:bg-muted transition-colors"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Check Out Modal */}
      {selectedVehicleForCheckout && (
        <TripCheckoutModal
          vehicle={selectedVehicleForCheckout}
          isOpen={!!selectedVehicleForCheckout}
          onClose={() => setSelectedVehicleForCheckout(null)}
          onSuccess={loadVehicles}
        />
      )}

      {/* Register Vehicle Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-foreground">Register New Vehicle Asset</h3>

            <form onSubmit={handleCreateVehicle} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Vehicle Internal ID *
                </label>
                <input
                  type="text"
                  required
                  value={newInternalId}
                  onChange={(e) => setNewInternalId(e.target.value)}
                  placeholder="e.g. VAN-105"
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">Make *</label>
                  <input
                    type="text"
                    required
                    value={newMake}
                    onChange={(e) => setNewMake(e.target.value)}
                    placeholder="e.g. Dodge"
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">Model *</label>
                  <input
                    type="text"
                    required
                    value={newModel}
                    onChange={(e) => setNewModel(e.target.value)}
                    placeholder="e.g. Caravan"
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">Year *</label>
                  <input
                    type="number"
                    required
                    value={newYear}
                    onChange={(e) => setNewYear(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">Plate *</label>
                  <input
                    type="text"
                    required
                    value={newPlate}
                    onChange={(e) => setNewPlate(e.target.value)}
                    placeholder="SK-123"
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">Type *</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none"
                  >
                    <option value="CAR">Car</option>
                    <option value="VAN">Van</option>
                    <option value="SUV">SUV</option>
                    <option value="TRUCK">Truck</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Initial Odometer (km)</label>
                <input
                  type="number"
                  step="0.1"
                  value={newOdometer}
                  onChange={(e) => setNewOdometer(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
                />
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-border pt-4">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
                >
                  Save Vehicle
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

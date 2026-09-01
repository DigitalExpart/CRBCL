import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fleetApi } from '@/api/fleet';
import FleetMap from '@/components/fleet/FleetMap';
import {
  Truck,
  CheckCircle2,
  Navigation,
  Wrench,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Plus,
  ArrowRight,
} from 'lucide-react';

export default function FleetDashboard() {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFleetData();
  }, []);

  const loadFleetData = async () => {
    setLoading(true);
    try {
      const [mRes, vRes] = await Promise.all([
        fleetApi.getFleetDashboard(),
        fleetApi.getVehicles({ limit: 50 }),
      ]);
      setMetrics(mRes.data);

      // Fetch detail with locations for mapping
      const detailedVehicles = await Promise.all(
        (vRes.data || []).map(async (v) => {
          try {
            const d = await fleetApi.getVehicleDetail(v.id);
            return d.data;
          } catch {
            return { vehicle: v, latest_location: null, is_location_stale: false };
          }
        })
      );
      setVehicles(detailedVehicles);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading Fleet Operations Center...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Fleet Operations & Asset Center</h1>
          <p className="text-sm text-muted-foreground">
            Vehicle availability, active driver check-outs, maintenance, insurance, and live GPS mapping.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/fleet/vehicles')}
            className="px-4 py-2 border border-border rounded-lg text-sm text-foreground hover:bg-muted font-medium"
          >
            Vehicle Directory
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between text-blue-500">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Total Fleet Assets
            </span>
            <Truck className="w-5 h-5" />
          </div>
          <div className="text-3xl font-extrabold text-foreground">{metrics?.total_vehicles || 0}</div>
          <div className="text-xs text-muted-foreground">Registered agency vehicles</div>
        </div>

        <div className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between text-emerald-500">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Available For Trip
            </span>
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div className="text-3xl font-extrabold text-foreground">{metrics?.available_count || 0}</div>
          <div className="text-xs text-muted-foreground">Ready for caseworker checkout</div>
        </div>

        <div className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between text-amber-500">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Active Trips (In Use)
            </span>
            <Navigation className="w-5 h-5" />
          </div>
          <div className="text-3xl font-extrabold text-foreground">{metrics?.in_use_count || 0}</div>
          <div className="text-xs text-muted-foreground">Vehicles currently checked out</div>
        </div>

        <div className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between text-rose-500">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              In Maintenance
            </span>
            <Wrench className="w-5 h-5" />
          </div>
          <div className="text-3xl font-extrabold text-foreground">{metrics?.maintenance_count || 0}</div>
          <div className="text-xs text-muted-foreground">Service & repair in progress</div>
        </div>
      </div>

      {/* Fleet Map & Quick Action Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <FleetMap vehicles={vehicles} height="420px" />
        </div>

        <div className="bg-card border border-border rounded-xl p-5 space-y-4 shadow-sm flex flex-col justify-between">
          <div className="space-y-3">
            <h3 className="font-bold text-foreground text-base">Fleet Operations Alerts</h3>

            <div className="p-3 bg-muted/40 border border-border rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span className="text-xs font-medium text-foreground">Insurance Expiring (30d)</span>
              </div>
              <span className="px-2 py-0.5 bg-card border border-border rounded text-xs font-bold">
                {metrics?.insurance_expiring_count || 0}
              </span>
            </div>

            <div className="p-3 bg-muted/40 border border-border rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-amber-500" />
                <span className="text-xs font-medium text-foreground">Maintenance Due</span>
              </div>
              <span className="px-2 py-0.5 bg-card border border-border rounded text-xs font-bold">
                {metrics?.maintenance_due_count || 0}
              </span>
            </div>
          </div>

          <div className="space-y-2 border-t border-border pt-4">
            <button
              onClick={() => navigate('/fleet/vehicles')}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              View Vehicle Directory <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/fleet/maintenance')}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-border text-foreground rounded-lg text-sm font-medium hover:bg-muted transition-colors"
            >
              Maintenance Management
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

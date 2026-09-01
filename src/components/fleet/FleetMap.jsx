import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Truck, Navigation, AlertTriangle, ShieldCheck, MapPin } from 'lucide-react';

// Fix for default Leaflet marker icons in React bundles
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function FleetMap({ vehicles = [], height = '400px' }) {
  // Filter vehicles with valid location coordinates
  const validVehicles = vehicles.filter(
    (item) =>
      item.latest_location &&
      item.latest_location.latitude != null &&
      item.latest_location.longitude != null
  );

  const defaultCenter =
    validVehicles.length > 0
      ? [validVehicles[0].latest_location.latitude, validVehicles[0].latest_location.longitude]
      : [50.4452, -104.6189]; // Regina, SK coordinates default

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm space-y-2">
      <div className="p-3 bg-muted/40 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-primary" />
          <span className="text-xs font-semibold text-foreground">
            Live Fleet & Location Tracking Map
          </span>
        </div>
        <span className="text-[10px] text-muted-foreground font-medium">
          {validVehicles.length} vehicle(s) mapped
        </span>
      </div>

      <div style={{ height, width: '100%' }}>
        <MapContainer center={defaultCenter} zoom={11} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {validVehicles.map(({ vehicle, latest_location, is_location_stale }) => (
            <Marker
              key={vehicle.id}
              position={[latest_location.latitude, latest_location.longitude]}
            >
              <Popup>
                <div className="p-1 space-y-1.5 text-xs">
                  <div className="font-bold text-foreground text-sm">
                    {vehicle.vehicle_internal_id} ({vehicle.make} {vehicle.model})
                  </div>
                  <div className="text-muted-foreground">Plate: {vehicle.licence_plate}</div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary uppercase">
                      {vehicle.status}
                    </span>
                    {is_location_stale && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-600">
                        Stale (&gt; 60m)
                      </span>
                    )}

                  </div>
                  <div className="text-[10px] text-muted-foreground pt-1 border-t border-border">
                    Recorded: {new Date(latest_location.recorded_at).toLocaleTimeString()} ({latest_location.source})
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

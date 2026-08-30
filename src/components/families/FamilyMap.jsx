import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MapPin, Home, Navigation, AlertCircle } from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet marker icons in React bundles
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function FamilyMap({ locations = [], familyName = "" }) {
  const validLocations = locations.filter(
    (loc) => loc.latitude != null && loc.longitude != null && !isNaN(loc.latitude) && !isNaN(loc.longitude)
  );

  const defaultCenter = validLocations.length > 0
    ? [validLocations[0].latitude, validLocations[0].longitude]
    : [50.4452, -104.6189]; // Default to Regina, SK coordinates

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden border-border/80">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <MapPin className="w-4 h-4 text-primary" />
                Family Household & Dwelling Locations
              </CardTitle>
              <CardDescription>
                {validLocations.length} registered address{validLocations.length === 1 ? '' : 'es'} for {familyName || 'this family'}
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-xs">
              Saskatchewan Region
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="h-[360px] w-full relative z-0">
            <MapContainer
              center={defaultCenter}
              zoom={validLocations.length > 0 ? 12 : 10}
              scrollWheelZoom={false}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {validLocations.map((loc, idx) => (
                <Marker key={loc.id || idx} position={[loc.latitude, loc.longitude]}>
                  <Popup>
                    <div className="text-xs space-y-1">
                      <strong className="block text-sm text-primary font-semibold">{loc.name || 'Family Dwelling'}</strong>
                      <p>{loc.address}</p>
                      <p>{loc.city}, {loc.province}</p>
                      {loc.on_reserve && (
                        <span className="inline-block mt-1 px-1.5 py-0.5 bg-amber-100 text-amber-900 rounded font-semibold text-[10px]">
                          On-Reserve
                        </span>
                      )}
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </CardContent>
      </Card>

      {/* Locations List */}
      {validLocations.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {validLocations.map((loc, idx) => (
            <div key={loc.id || idx} className="p-3 bg-muted/40 rounded-lg border border-border/50 text-xs flex items-start justify-between">
              <div className="flex items-start gap-2.5">
                <Home className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <h5 className="font-semibold text-foreground">{loc.name || 'Primary Residence'}</h5>
                  <p className="text-muted-foreground">{loc.address}, {loc.city}</p>
                  <p className="text-[11px] text-muted-foreground font-mono mt-0.5">
                    Lat: {loc.latitude.toFixed(4)}, Long: {loc.longitude.toFixed(4)}
                  </p>
                </div>
              </div>
              <Badge variant="secondary" className="text-[10px]">Active</Badge>
            </div>
          ))}
        </div>
      )}

      {validLocations.length === 0 && (
        <div className="p-4 bg-muted/20 rounded-lg border border-dashed text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-500" />
          No geographical coordinates mapped for this family's addresses yet.
        </div>
      )}
    </div>
  );
}

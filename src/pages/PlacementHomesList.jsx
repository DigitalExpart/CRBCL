import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Home,
  Plus,
  Search,
  Filter,
  MapPin,
  Bed,
  ShieldCheck,
  AlertTriangle,
  Users,
  CheckCircle2,
  Calendar,
  Phone,
  Layers,
  Map as MapIcon,
  List as ListIcon,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { placementHomesApi } from "@/api/placementHomes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { toast } from "react-hot-toast";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet Default Icon issue in React Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const createCustomMarker = (color) => {
  return new L.DivIcon({
    className: "custom-leaflet-marker",
    html: `<div style="background-color: ${color}; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
};

export default function PlacementHomesList() {
  const navigate = useNavigate();
  const [homes, setHomes] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [mapMarkers, setMapMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState("table"); // 'table' | 'map'

  // Filters
  const [search, setSearch] = useState("");
  const [homeType, setHomeType] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [licensingFilter, setLicensingFilter] = useState("all");
  const [availableOnly, setAvailableOnly] = useState(false);

  // New Home Dialog
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    home_type: "LICENSED_FOSTER",
    total_capacity: 2,
    address_line_1: "",
    city: "Regina",
    province: "Saskatchewan",
    postal_code: "",
    community: "",
    latitude: 50.4547,
    longitude: -104.6067,
    phone: "",
    email: "",
    primary_caregiver_name: "",
    intake_criteria_notes: "",
    notes: "",
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = {
        page: 1,
        page_size: 100,
        available_only: availableOnly,
      };
      if (search.trim()) params.search = search.trim();
      if (homeType !== "all") params.home_type = homeType;
      if (statusFilter !== "all") params.status = statusFilter;
      if (licensingFilter !== "all") params.licensing_status = licensingFilter;

      const [homesRes, metricsRes, mapRes] = await Promise.all([
        placementHomesApi.list(params),
        placementHomesApi.getMetrics(),
        placementHomesApi.getMapMarkers(),
      ]);

      setHomes(homesRes.data.items || []);
      setMetrics(metricsRes.data);
      setMapMarkers(mapRes.data || []);
    } catch (err) {
      toast.error("Failed to load placement homes directory.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [search, homeType, statusFilter, licensingFilter, availableOnly]);

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error("Home / Facility name is required.");
      return;
    }
    try {
      setCreateSubmitting(true);
      const res = await placementHomesApi.create(formData);
      toast.success(`Placement Home ${res.data.name} created successfully!`);
      setShowCreateModal(false);
      navigate(`/placement-homes/${res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create placement home.");
      console.error(err);
    } finally {
      setCreateSubmitting(false);
    }
  };

  const getCapacityBadge = (occupied, total) => {
    const available = Math.max(0, total - occupied);
    if (available === 0) {
      return (
        <Badge className="bg-red-500/10 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800">
          Full ({occupied}/{total})
        </Badge>
      );
    }
    if (available === 1) {
      return (
        <Badge className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
          1 Bed Available ({occupied}/{total})
        </Badge>
      );
    }
    return (
      <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
        {available} Beds Available ({occupied}/{total})
      </Badge>
    );
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Home className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Placement Homes & Facilities
            </h1>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Directory of licensed foster homes, kinship residences, therapeutic care, and residential facilities.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
            <Button
              variant={viewMode === "table" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setViewMode("table")}
              className="gap-1.5"
            >
              <ListIcon className="h-4 w-4" />
              Table
            </Button>
            <Button
              variant={viewMode === "map" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setViewMode("map")}
              className="gap-1.5"
            >
              <MapIcon className="h-4 w-4" />
              Map
            </Button>
          </div>
          <Button onClick={() => setShowCreateModal(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white">
            <Plus className="h-4 w-4" />
            Add Placement Home
          </Button>
        </div>
      </div>

      {/* Metrics Dashboard */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="text-xs text-slate-500 font-medium">Total Homes</div>
            <div className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">{metrics.total_homes}</div>
            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 mt-1">
              <CheckCircle2 className="h-3 w-3" /> {metrics.active_homes} Active
            </div>
          </Card>
          <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="text-xs text-slate-500 font-medium">Approved Beds</div>
            <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">{metrics.total_beds}</div>
            <div className="text-[11px] text-slate-500 mt-1">Capacity integrity</div>
          </Card>
          <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="text-xs text-slate-500 font-medium">Occupied Beds</div>
            <div className="text-xl font-bold text-slate-700 dark:text-slate-300 mt-1">{metrics.occupied_beds}</div>
            <div className="text-[11px] text-slate-500 mt-1">
              {metrics.total_beds > 0 ? `${Math.round((metrics.occupied_beds / metrics.total_beds) * 100)}% occupancy` : "0%"}
            </div>
          </Card>
          <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="text-xs text-slate-500 font-medium">Available Beds</div>
            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{metrics.available_beds}</div>
            <div className="text-[11px] text-slate-500 mt-1">Ready for placement</div>
          </Card>
          <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="text-xs text-slate-500 font-medium">Homes At Capacity</div>
            <div className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">{metrics.homes_at_capacity}</div>
            <div className="text-[11px] text-slate-500 mt-1">No vacancies</div>
          </Card>
          <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <div className="text-xs text-slate-500 font-medium">Licence Alerts</div>
            <div className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-1">{metrics.expiring_licenses_90d}</div>
            <div className="text-[11px] text-rose-600 dark:text-rose-400 mt-1">Expiring in 90 days</div>
          </Card>
        </div>
      )}

      {/* Filter Bar */}
      <Card className="p-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <div className="relative md:col-span-2">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by name, code, caregiver, community..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={homeType} onValueChange={setHomeType}>
            <SelectTrigger>
              <SelectValue placeholder="Home Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Home Types</SelectItem>
              <SelectItem value="LICENSED_FOSTER">Licensed Foster Home</SelectItem>
              <SelectItem value="KINSHIP">Kinship / Customary Care</SelectItem>
              <SelectItem value="THERAPEUTIC">Therapeutic Foster Home</SelectItem>
              <SelectItem value="FACILITY">Residential Facility / Group Home</SelectItem>
              <SelectItem value="RELATIVE">Relative Care</SelectItem>
            </SelectContent>
          </Select>
          <Select value={licensingFilter} onValueChange={setLicensingFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Licensing Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Licensing Statuses</SelectItem>
              <SelectItem value="ACTIVE">Active License</SelectItem>
              <SelectItem value="PENDING">Pending Renewal / Inspection</SelectItem>
              <SelectItem value="UNLICENSED">Unlicensed</SelectItem>
              <SelectItem value="SUSPENDED">Suspended</SelectItem>
              <SelectItem value="EXPIRED">Expired</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant={availableOnly ? "default" : "outline"}
            onClick={() => setAvailableOnly(!availableOnly)}
            className="gap-2"
          >
            <Bed className="h-4 w-4" />
            {availableOnly ? "Showing Vacancies Only" : "Filter Vacancies"}
          </Button>
        </div>
      </Card>

      {/* Main Content Area */}
      {viewMode === "map" ? (
        <Card className="p-0 overflow-hidden border-slate-200 dark:border-slate-800">
          <div style={{ height: "600px", width: "100%" }}>
            <MapContainer center={[50.4547, -104.6067]} zoom={7} scrollWheelZoom={true} style={{ height: "100%", width: "100%" }}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mapMarkers.map((m) => {
                const markerColor = m.available_beds > 0 ? "#10b981" : "#ef4444";
                return (
                  <Marker
                    key={m.id}
                    position={[m.latitude, m.longitude]}
                    icon={createCustomMarker(markerColor)}
                  >
                    <Popup>
                      <div className="p-1 space-y-1.5">
                        <div className="font-bold text-sm text-slate-900">{m.name}</div>
                        <div className="text-xs text-slate-500">{m.home_code} • {m.home_type}</div>
                        <div className="text-xs">
                          {m.community ? `${m.community}, ` : ""}{m.city}
                        </div>
                        <div className="pt-1">
                          {getCapacityBadge(m.occupied_beds, m.total_capacity)}
                        </div>
                        <div className="pt-2">
                          <Link
                            to={`/placement-homes/${m.id}`}
                            className="text-xs text-indigo-600 font-semibold flex items-center gap-1 hover:underline"
                          >
                            View Home Profile <ExternalLink className="h-3 w-3" />
                          </Link>
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}
            </MapContainer>
          </div>
        </Card>
      ) : (
        /* Table View */
        <Card className="overflow-hidden border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Home / Facility</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Capacity & Availability</th>
                  <th className="px-4 py-3">Primary Caregiver</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Licensing</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                      Loading placement homes directory...
                    </td>
                  </tr>
                ) : homes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-slate-400">
                      No placement homes match the selected filter criteria.
                    </td>
                  </tr>
                ) : (
                  homes.map((home) => (
                    <tr
                      key={home.id}
                      className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                      onClick={() => navigate(`/placement-homes/${home.id}`)}
                    >
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                        <div className="font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">
                          {home.name}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">{home.home_code}</div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="text-xs font-normal">
                          {home.home_type.replace(/_/g, " ")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        {getCapacityBadge(home.occupied_beds, home.total_capacity)}
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                        {home.primary_caregiver_name || "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                        {home.community ? `${home.community}, ` : ""}{home.city}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          className={
                            home.licensing_status === "ACTIVE"
                              ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                              : home.licensing_status === "PENDING"
                              ? "bg-amber-500/10 text-amber-700 dark:text-amber-400"
                              : "bg-slate-500/10 text-slate-700 dark:text-slate-400"
                          }
                        >
                          {home.licensing_status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/placement-homes/${home.id}`)}
                          className="gap-1 text-slate-600 hover:text-indigo-600"
                        >
                          View <ChevronRight className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* New Placement Home Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Register New Placement Home / Facility</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateSubmit} className="space-y-4 pt-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5 md:col-span-2">
                <Label>Home / Facility Name *</Label>
                <Input
                  required
                  placeholder="e.g. Eagle Feather Customary Care Home"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Home Type *</Label>
                <Select
                  value={formData.home_type}
                  onValueChange={(val) => setFormData({ ...formData, home_type: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LICENSED_FOSTER">Licensed Foster Home</SelectItem>
                    <SelectItem value="KINSHIP">Kinship / Customary Care</SelectItem>
                    <SelectItem value="THERAPEUTIC">Therapeutic Foster Home</SelectItem>
                    <SelectItem value="FACILITY">Residential Facility / Group Home</SelectItem>
                    <SelectItem value="RELATIVE">Relative Care</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Approved Bed Capacity *</Label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  required
                  value={formData.total_capacity}
                  onChange={(e) => setFormData({ ...formData, total_capacity: parseInt(e.target.value) || 1 })}
                />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <Label>Street Address</Label>
                <Input
                  placeholder="e.g. 452 Saulteaux Way"
                  value={formData.address_line_1}
                  onChange={(e) => setFormData({ ...formData, address_line_1: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>City / Town</Label>
                <Input
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>First Nation / Community</Label>
                <Input
                  placeholder="e.g. Muscowpetung First Nation"
                  value={formData.community}
                  onChange={(e) => setFormData({ ...formData, community: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Primary Caregiver Name</Label>
                <Input
                  placeholder="e.g. Eleanor Desjarlais"
                  value={formData.primary_caregiver_name}
                  onChange={(e) => setFormData({ ...formData, primary_caregiver_name: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Phone Number</Label>
                <Input
                  placeholder="e.g. 306-555-8910"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Latitude Coordinates</Label>
                <Input
                  type="number"
                  step="any"
                  value={formData.latitude}
                  onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Longitude Coordinates</Label>
                <Input
                  type="number"
                  step="any"
                  value={formData.longitude}
                  onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <Label>Intake & Placement Acceptance Criteria</Label>
                <Textarea
                  placeholder="e.g. Siblings group preferred, cultural customary connection, age ranges accepted..."
                  value={formData.intake_criteria_notes}
                  onChange={(e) => setFormData({ ...formData, intake_criteria_notes: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter className="pt-4">
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={createSubmitting} className="bg-indigo-600 hover:bg-indigo-700 text-white">
                {createSubmitting ? "Creating..." : "Save Placement Home"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

import React, { useState, useEffect, useCallback } from "react";
import {
  Building2, Truck, Key, Calendar, Package, ClipboardList,
  Plus, AlertTriangle,
  FileText, Shield, RefreshCw, ChevronRight,
  Laptop, MapPin
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatCard from "@/components/shared/StatCard";
import StatusBadge from "@/components/shared/StatusBadge";
import { toast } from "@/components/ui/use-toast";
import { api } from "@/api";

export default function OfficeCoordinator() {
  const [activeTab, setActiveTab] = useState("overview"); // overview | requests | reservations | keys | rooms | supplies | fleet_ref | integrations
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [availabilityMessage, setAvailabilityMessage] = useState(null);

  // Sub-data states
  const [requests, setRequests] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [keyLogs, setKeyLogs] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [supplies, setSupplies] = useState([]);
  const [vehicles, setVehicles] = useState([]);

  // Dialog states
  const [newRequestOpen, setNewRequestOpen] = useState(false);
  const [newReservationOpen, setNewReservationOpen] = useState(false);
  const [newKeyCheckoutOpen, setNewKeyCheckoutOpen] = useState(false);
  const [newRoomOpen, setNewRoomOpen] = useState(false);
  const [newSupplyOpen, setNewSupplyOpen] = useState(false);

  // Form states
  const [reqForm, setReqForm] = useState({ title: "", description: "", category: "GENERAL", priority: "MEDIUM", department: "" });
  const [resForm, setResForm] = useState({ vehicle_id: "", start_time: "", end_time: "", purpose: "", destination: "", passengers_count: 1, notes: "" });
  const [keyForm, setKeyForm] = useState({ vehicle_id: "", key_tag: "", staff_id: "", notes: "" });
  const [roomForm, setRoomForm] = useState({ room_name: "", title: "", start_time: "", end_time: "", attendees_count: 1, notes: "" });
  const [supplyForm, setSupplyForm] = useState({ item_name: "", category: "OFFICE", quantity: 10, unit: "boxes", location: "Main Supply Closet", reorder_threshold: 5, notes: "" });
  const [staffUsers, setStaffUsers] = useState([]);

  // Check workspace availability first
  const checkAvailability = async () => {
    try {
      const res = await api.fetch("/api/v1/dashboards/office_coordinator/availability");
      if (res.ok) {
        const data = await res.json();
        if (!data.is_enabled) {
          setAvailabilityMessage(data.message || "Office Coordinator workspace is temporarily disabled by administrative policy.");
        }
      }
    } catch {
      // Ignore network errors on availability probe
    }
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      await checkAvailability();

      // Load overview
      const ovRes = await api.fetch("/api/v1/operations/overview");
      if (ovRes.ok) {
        const ovData = await ovRes.json();
        setOverview(ovData);
      }

      // Load operational requests
      const reqRes = await api.fetch("/api/v1/operations/requests?limit=50");
      if (reqRes.ok) {
        const reqData = await reqRes.json();
        setRequests(reqData.items || []);
      }

      // Load reservations
      const resRes = await api.fetch("/api/v1/operations/reservations?limit=50");
      if (resRes.ok) {
        const resData = await resRes.json();
        setReservations(resData.items || []);
      }

      // Load keys
      const keyRes = await api.fetch("/api/v1/operations/keys?limit=50");
      if (keyRes.ok) {
        const keyData = await keyRes.json();
        setKeyLogs(keyData.items || []);
      }

      // Load rooms
      const roomRes = await api.fetch("/api/v1/operations/rooms?limit=50");
      if (roomRes.ok) {
        const roomData = await roomRes.json();
        setRooms(roomData.items || []);
      }

      // Load supplies
      const supRes = await api.fetch("/api/v1/operations/supplies?limit=50");
      if (supRes.ok) {
        const supData = await supRes.json();
        setSupplies(supData.items || []);
      }

      // Load canonical vehicles for reservation picker
      try {
        const vRes = await api.fetch("/api/v1/fleet/vehicles?limit=100");
        if (vRes.ok) {
          const vData = await vRes.json();
          setVehicles(vData.items || []);
        }
      } catch {}

      // Load staff list for key assignments
      try {
        const uRes = await api.fetch("/api/v1/users?limit=100");
        if (uRes.ok) {
          const uData = await uRes.json();
          setStaffUsers(uData.items || []);
        }
      } catch {}

    } catch (err) {
      toast({ title: "Error loading operations data", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Request handlers
  const handleCreateRequest = async (e) => {
    e.preventDefault();
    try {
      const res = await api.fetch("/api/v1/operations/requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reqForm),
      });
      if (!res.ok) throw new Error("Failed to submit operational request");
      const created = await res.json();
      setRequests([created, ...requests]);
      setNewRequestOpen(false);
      setReqForm({ title: "", description: "", category: "GENERAL", priority: "MEDIUM", department: "" });
      toast({ title: "Request Logged", description: `Ticket ${created.request_number} created successfully.` });
    } catch (err) {
      toast({ title: "Submission Failed", description: err.message, variant: "destructive" });
    }
  };

  const handleCreateReservation = async (e) => {
    e.preventDefault();
    try {
      const res = await api.fetch("/api/v1/operations/reservations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...resForm,
          start_time: new Date(resForm.start_time).toISOString(),
          end_time: new Date(resForm.end_time).toISOString(),
        }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to reserve vehicle");
      }
      const created = await res.json();
      setReservations([created, ...reservations]);
      setNewReservationOpen(false);
      toast({ title: "Reservation Confirmed", description: "Vehicle reserved with conflict verification." });
    } catch (err) {
      toast({ title: "Reservation Conflict", description: err.message, variant: "destructive" });
    }
  };

  const handleCheckoutKey = async (e) => {
    e.preventDefault();
    try {
      const res = await api.fetch("/api/v1/operations/keys/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(keyForm),
      });
      if (!res.ok) throw new Error("Failed to checkout vehicle key");
      const created = await res.json();
      setKeyLogs([created, ...keyLogs]);
      setNewKeyCheckoutOpen(false);
      toast({ title: "Key Checked Out", description: `Key ${created.key_tag} custody logged.` });
    } catch (err) {
      toast({ title: "Checkout Failed", description: err.message, variant: "destructive" });
    }
  };

  const handleReturnKey = async (keyLogId) => {
    try {
      const res = await api.fetch(`/api/v1/operations/keys/${keyLogId}/return`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "Returned in good order" }),
      });
      if (!res.ok) throw new Error("Failed to return key");
      const updated = await res.json();
      setKeyLogs(keyLogs.map((k) => (k.id === updated.id ? updated : k)));
      toast({ title: "Key Returned", description: "Vehicle key custody restored." });
    } catch (err) {
      toast({ title: "Return Failed", description: err.message, variant: "destructive" });
    }
  };

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    try {
      const res = await api.fetch("/api/v1/operations/rooms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...roomForm,
          start_time: new Date(roomForm.start_time).toISOString(),
          end_time: new Date(roomForm.end_time).toISOString(),
        }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Room booking conflict");
      }
      const created = await res.json();
      setRooms([created, ...rooms]);
      setNewRoomOpen(false);
      toast({ title: "Room Booked", description: `Meeting room scheduled for ${created.title}.` });
    } catch (err) {
      toast({ title: "Booking Conflict", description: err.message, variant: "destructive" });
    }
  };

  const handleCreateSupply = async (e) => {
    e.preventDefault();
    try {
      const res = await api.fetch("/api/v1/operations/supplies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(supplyForm),
      });
      if (!res.ok) throw new Error("Failed to create supply item");
      const created = await res.json();
      setSupplies([created, ...supplies]);
      setNewSupplyOpen(false);
      toast({ title: "Inventory Item Added", description: `${created.item_name} registered in inventory.` });
    } catch (err) {
      toast({ title: "Failed", description: err.message, variant: "destructive" });
    }
  };

  if (loading && !overview) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (availabilityMessage) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-600 mx-auto flex items-center justify-center">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold font-heading">Workspace Currently Unavailable</h2>
        <p className="text-muted-foreground text-sm">{availabilityMessage}</p>
        <p className="text-xs text-muted-foreground">
          Please contact an authorized IT Administrator in the Admin & IT Portal to restore organizational availability.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Office Coordinator Workspace"
        subtitle="Centralized operations, advance fleet reservations, key custody, room booking, and facilities coordination"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={loadData} className="gap-1.5">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
            <Button size="sm" onClick={() => setNewRequestOpen(true)} className="gap-1.5">
              <Plus className="w-4 h-4" />
              New Operational Request
            </Button>
          </div>
        }
      />

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          title="Open Requests"
          value={overview?.open_requests_count ?? "—"}
          icon={ClipboardList}
          color="primary"
          subtitle="Tickets in progress"
        />
        <StatCard
          title="Active Reservations"
          value={overview?.active_reservations_count ?? "—"}
          icon={Calendar}
          color="amber"
          subtitle="Fleet bookings"
        />
        <StatCard
          title="Keys Out"
          value={overview?.keys_checked_out_count ?? "—"}
          icon={Key}
          color="orange"
          subtitle="Staff custody"
        />
        <StatCard
          title="Available Fleet"
          value={overview?.available_vehicles_count ?? "—"}
          icon={Truck}
          color="emerald"
          subtitle="Ready for checkout"
        />
        <StatCard
          title="Low Supplies"
          value={overview?.low_stock_supplies_count ?? "—"}
          icon={Package}
          color="rose"
          subtitle="Below threshold"
        />
        <StatCard
          title="Today's Rooms"
          value={overview?.today_room_bookings_count ?? "—"}
          icon={Building2}
          color="blue"
          subtitle="Scheduled meetings"
        />
      </div>

      {/* Workspace Navigation Tabs */}
      <div className="flex border-b border-border overflow-x-auto gap-2">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === "overview" ? "border-primary text-primary font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <ClipboardList className="w-4 h-4" />
          Today's Operations
        </button>
        <button
          onClick={() => setActiveTab("requests")}
          className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === "requests" ? "border-primary text-primary font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileText className="w-4 h-4" />
          Request Queue ({requests.length})
        </button>
        <button
          onClick={() => setActiveTab("reservations")}
          className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === "reservations" ? "border-primary text-primary font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Calendar className="w-4 h-4" />
          Vehicle Reservations ({reservations.length})
        </button>
        <button
          onClick={() => setActiveTab("keys")}
          className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === "keys" ? "border-primary text-primary font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Key className="w-4 h-4" />
          Key Accountability ({keyLogs.length})
        </button>
        <button
          onClick={() => setActiveTab("rooms")}
          className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === "rooms" ? "border-primary text-primary font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Building2 className="w-4 h-4" />
          Room Bookings ({rooms.length})
        </button>
        <button
          onClick={() => setActiveTab("supplies")}
          className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === "supplies" ? "border-primary text-primary font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Package className="w-4 h-4" />
          Supplies & Inventory ({supplies.length})
        </button>
        <button
          onClick={() => setActiveTab("integrations")}
          className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === "integrations" ? "border-primary text-primary font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Shield className="w-4 h-4" />
          Integrations & GPS Status
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Recent Requests */}
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <ClipboardList className="w-4 h-4 text-primary" />
                  Active Operational Requests
                </h3>
                <Button variant="ghost" size="sm" onClick={() => setActiveTab("requests")} className="text-xs">
                  View All ({requests.length}) <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>

              {requests.length === 0 ? (
                <p className="text-xs text-muted-foreground py-6 text-center">No active operational requests.</p>
              ) : (
                <div className="divide-y divide-border">
                  {requests.slice(0, 5).map((r) => (
                    <div key={r.id} className="py-3 flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-foreground">{r.request_number}</span>
                          <span className="text-xs font-semibold">{r.title}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground capitalize">
                            {r.category.toLowerCase()}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{r.description}</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          Requested by {r.requester_name || "Staff"} • {new Date(r.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <StatusBadge status={r.status} />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Upcoming Reservations */}
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Truck className="w-4 h-4 text-primary" />
                  Upcoming Vehicle Reservations
                </h3>
                <Button size="sm" variant="outline" onClick={() => setNewReservationOpen(true)} className="text-xs gap-1.5">
                  <Plus className="w-3.5 h-3.5" /> Advance Booking
                </Button>
              </div>

              {reservations.length === 0 ? (
                <p className="text-xs text-muted-foreground py-6 text-center">No advance vehicle reservations scheduled.</p>
              ) : (
                <div className="divide-y divide-border">
                  {reservations.slice(0, 4).map((res) => (
                    <div key={res.id} className="py-3 flex items-start justify-between gap-4">
                      <div>
                        <p className="text-xs font-semibold text-foreground">
                          {res.vehicle_name || "Vehicle"} ({res.licence_plate})
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {res.purpose} {res.destination ? `• Destination: ${res.destination}` : ""}
                        </p>
                        <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
                          {new Date(res.start_time).toLocaleString()} → {new Date(res.end_time).toLocaleTimeString()}
                        </p>
                      </div>
                      <StatusBadge status={res.status} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Key Custody & Room Schedule */}
          <div className="space-y-6">
            {/* Keys Currently Out */}
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Key className="w-4 h-4 text-amber-500" />
                  Keys Currently Out
                </h3>
                <Button size="sm" variant="outline" onClick={() => setNewKeyCheckoutOpen(true)} className="text-xs gap-1">
                  <Plus className="w-3.5 h-3.5" /> Checkout Key
                </Button>
              </div>

              {keyLogs.filter((k) => k.status === "CHECKED_OUT").length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">All vehicle keys returned to custody.</p>
              ) : (
                <div className="space-y-2">
                  {keyLogs
                    .filter((k) => k.status === "CHECKED_OUT")
                    .map((k) => (
                      <div key={k.id} className="p-3 rounded-lg border border-border bg-muted/20 flex items-center justify-between">
                        <div>
                          <p className="text-xs font-semibold text-foreground">{k.key_tag}</p>
                          <p className="text-[11px] text-muted-foreground">With: {k.staff_name || "Staff"}</p>
                          <p className="text-[10px] text-muted-foreground font-mono">
                            Out: {new Date(k.checked_out_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </p>
                        </div>
                        <Button size="sm" variant="secondary" onClick={() => handleReturnKey(k.id)} className="h-7 text-xs">
                          Return
                        </Button>
                      </div>
                    ))}
                </div>
              )}
            </div>

            {/* Today's Room Bookings */}
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-primary" />
                  Room Bookings
                </h3>
                <Button size="sm" variant="outline" onClick={() => setNewRoomOpen(true)} className="text-xs gap-1">
                  <Plus className="w-3.5 h-3.5" /> Book Room
                </Button>
              </div>

              {rooms.length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">No meeting rooms scheduled today.</p>
              ) : (
                <div className="space-y-2">
                  {rooms.slice(0, 4).map((r) => (
                    <div key={r.id} className="p-2.5 rounded-lg border border-border text-xs">
                      <p className="font-semibold text-foreground">{r.title}</p>
                      <p className="text-muted-foreground text-[11px]">{r.room_name} • {r.attendees_count} attendees</p>
                      <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
                        {new Date(r.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} -{" "}
                        {new Date(r.end_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: REQUEST QUEUE */}
      {activeTab === "requests" && (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-sm">Centralized Operational Tickets</h3>
            <Button size="sm" onClick={() => setNewRequestOpen(true)} className="gap-1.5">
              <Plus className="w-4 h-4" /> Log Request
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 border-b border-border text-xs font-semibold text-muted-foreground uppercase">
                <tr>
                  <th className="px-4 py-3">Number</th>
                  <th className="px-4 py-3">Title & Summary</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Requester</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {requests.map((r) => (
                  <tr key={r.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3 font-mono font-semibold text-xs">{r.request_number}</td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-foreground">{r.title}</p>
                      <p className="text-xs text-muted-foreground line-clamp-1">{r.description}</p>
                    </td>
                    <td className="px-4 py-3 text-xs capitalize">{r.category.toLowerCase()}</td>
                    <td className="px-4 py-3">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        r.priority === "URGENT" ? "bg-rose-500/20 text-rose-600" :
                        r.priority === "HIGH" ? "bg-amber-500/20 text-amber-600" : "bg-muted text-muted-foreground"
                      }`}>
                        {r.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{r.requester_name || "Staff"}</td>
                    <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                    <td className="px-4 py-3 text-right text-xs text-muted-foreground font-mono">
                      {new Date(r.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: RESERVATIONS */}
      {activeTab === "reservations" && (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-sm">Advance Vehicle Reservations</h3>
            <Button size="sm" onClick={() => setNewReservationOpen(true)} className="gap-1.5">
              <Plus className="w-4 h-4" /> Advance Booking
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 border-b border-border text-xs font-semibold text-muted-foreground uppercase">
                <tr>
                  <th className="px-4 py-3">Vehicle</th>
                  <th className="px-4 py-3">Purpose & Destination</th>
                  <th className="px-4 py-3">Start Window</th>
                  <th className="px-4 py-3">End Window</th>
                  <th className="px-4 py-3">Reserved By</th>
                  <th className="px-4 py-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {reservations.map((res) => (
                  <tr key={res.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3 font-semibold text-xs text-foreground">
                      {res.vehicle_name || "Vehicle"} ({res.licence_plate})
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-xs text-foreground">{res.purpose}</p>
                      {res.destination && <p className="text-[11px] text-muted-foreground">To: {res.destination}</p>}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono">{new Date(res.start_time).toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs font-mono">{new Date(res.end_time).toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{res.reserved_by_name || "Staff"}</td>
                    <td className="px-4 py-3 text-right"><StatusBadge status={res.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: KEYS */}
      {activeTab === "keys" && (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-sm">Key Pickup & Return Custody Log</h3>
            <Button size="sm" onClick={() => setNewKeyCheckoutOpen(true)} className="gap-1.5">
              <Plus className="w-4 h-4" /> Checkout Key
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 border-b border-border text-xs font-semibold text-muted-foreground uppercase">
                <tr>
                  <th className="px-4 py-3">Key Tag</th>
                  <th className="px-4 py-3">Vehicle</th>
                  <th className="px-4 py-3">Staff Recipient</th>
                  <th className="px-4 py-3">Checked Out</th>
                  <th className="px-4 py-3">Returned</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {keyLogs.map((k) => (
                  <tr key={k.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3 font-mono font-bold text-xs">{k.key_tag}</td>
                    <td className="px-4 py-3 text-xs">{k.vehicle_name || "Fleet Vehicle"}</td>
                    <td className="px-4 py-3 text-xs font-medium">{k.staff_name || "Staff Member"}</td>
                    <td className="px-4 py-3 text-xs font-mono">{new Date(k.checked_out_at).toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs font-mono">
                      {k.returned_at ? new Date(k.returned_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={k.status} /></td>
                    <td className="px-4 py-3 text-right">
                      {k.status === "CHECKED_OUT" && (
                        <Button size="sm" variant="secondary" onClick={() => handleReturnKey(k.id)} className="h-7 text-xs">
                          Record Return
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: ROOMS */}
      {activeTab === "rooms" && (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-sm">Boardroom & Facility Space Scheduling</h3>
            <Button size="sm" onClick={() => setNewRoomOpen(true)} className="gap-1.5">
              <Plus className="w-4 h-4" /> Book Room
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 border-b border-border text-xs font-semibold text-muted-foreground uppercase">
                <tr>
                  <th className="px-4 py-3">Meeting / Event Title</th>
                  <th className="px-4 py-3">Room / Space</th>
                  <th className="px-4 py-3">Start Window</th>
                  <th className="px-4 py-3">End Window</th>
                  <th className="px-4 py-3">Attendees</th>
                  <th className="px-4 py-3">Booked By</th>
                  <th className="px-4 py-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rooms.map((rm) => (
                  <tr key={rm.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3 font-medium text-xs text-foreground">{rm.title}</td>
                    <td className="px-4 py-3 text-xs font-semibold">{rm.room_name}</td>
                    <td className="px-4 py-3 text-xs font-mono">{new Date(rm.start_time).toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs font-mono">{new Date(rm.end_time).toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs">{rm.attendees_count}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{rm.booked_by_name || "Staff"}</td>
                    <td className="px-4 py-3 text-right"><StatusBadge status={rm.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 6: SUPPLIES & INVENTORY */}
      {activeTab === "supplies" && (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-sm">Office Supplies & Consumables Inventory</h3>
            <Button size="sm" onClick={() => setNewSupplyOpen(true)} className="gap-1.5">
              <Plus className="w-4 h-4" /> Add Item
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 border-b border-border text-xs font-semibold text-muted-foreground uppercase">
                <tr>
                  <th className="px-4 py-3">Item Name</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Quantity On Hand</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Reorder Threshold</th>
                  <th className="px-4 py-3 text-right">Stock Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {supplies.map((s) => (
                  <tr key={s.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3 font-semibold text-xs text-foreground">{s.item_name}</td>
                    <td className="px-4 py-3 text-xs capitalize">{s.category.toLowerCase()}</td>
                    <td className="px-4 py-3 text-xs font-bold">{s.quantity} {s.unit}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{s.location || "Central Storage"}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{s.reorder_threshold}</td>
                    <td className="px-4 py-3 text-right">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        s.status === "OUT_OF_STOCK" ? "bg-rose-500/20 text-rose-600" :
                        s.status === "LOW_STOCK" ? "bg-amber-500/20 text-amber-600" : "bg-emerald-500/20 text-emerald-600"
                      }`}>
                        {s.status.replace(/_/g, " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 7: INTEGRATIONS & GPS STATUS */}
      {activeTab === "integrations" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Physical Vehicle GPS Status */}
          <div className="bg-card border border-border rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-amber-500" />
              <h3 className="font-semibold text-sm">Physical Vehicle GPS Hardware</h3>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-800 dark:text-amber-300">
              <p className="font-bold">CONFIRMED REQUIREMENT — NOT YET IMPLEMENTED</p>
              <p className="mt-1">
                Physical tracker hardware (e.g. OBD-II or hardwired telematics units) has not yet been procured or installed.
                The software architecture supports future ingestion, but live GPS telematics remain unconfigured.
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              GPS location coordinates and trip history remain protected under separate capability controls (<code>fleet.location.history</code>). Ordinary Fleet access does not grant location breadcrumbs.
            </p>
          </div>

          {/* Microsoft 365 / SharePoint Coexistence */}
          <div className="bg-card border border-border rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Laptop className="w-5 h-5 text-blue-500" />
              <h3 className="font-semibold text-sm">Microsoft 365 & SharePoint Coexistence</h3>
            </div>
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-xs text-blue-800 dark:text-blue-300">
              <p className="font-bold">Enterprise Coexistence Mode</p>
              <p className="mt-1">
                Office Coordination operations coexist alongside existing CRBCL Microsoft SharePoint and Teams channels. Live Microsoft Graph automated document synchronization is planned for future phases.
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              Staff may continue storing formal legal policies and operational archives in approved CRBCL SharePoint document libraries.
            </p>
          </div>
        </div>
      )}

      {/* MODAL: New Operational Request */}
      <Dialog open={newRequestOpen} onOpenChange={setNewRequestOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Log Operational Ticket / Request</DialogTitle>
            <DialogDescription>Submit an operational or facility service request to the coordinator queue.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateRequest} className="space-y-4 py-2">
            <div className="space-y-1">
              <Label className="text-xs">Category</Label>
              <Select value={reqForm.category} onValueChange={(v) => setReqForm({ ...reqForm, category: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="GENERAL">General Operational</SelectItem>
                  <SelectItem value="FACILITIES">Facilities & Maintenance</SelectItem>
                  <SelectItem value="FLEET">Fleet & Vehicle</SelectItem>
                  <SelectItem value="SUPPLIES">Office Supplies</SelectItem>
                  <SelectItem value="IT_SUPPORT">IT / Hardware</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Request Title</Label>
              <Input
                placeholder="Brief summary of what is needed"
                value={reqForm.title}
                onChange={(e) => setReqForm({ ...reqForm, title: e.target.value })}
                required
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Detailed Description</Label>
              <Input
                placeholder="Specific details, location, or urgency notes"
                value={reqForm.description}
                onChange={(e) => setReqForm({ ...reqForm, description: e.target.value })}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Priority</Label>
                <Select value={reqForm.priority} onValueChange={(v) => setReqForm({ ...reqForm, priority: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">Low</SelectItem>
                    <SelectItem value="MEDIUM">Medium</SelectItem>
                    <SelectItem value="HIGH">High</SelectItem>
                    <SelectItem value="URGENT">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Department</Label>
                <Input
                  placeholder="e.g. Operations"
                  value={reqForm.department}
                  onChange={(e) => setReqForm({ ...reqForm, department: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setNewRequestOpen(false)}>Cancel</Button>
              <Button type="submit">Submit Request</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL: New Vehicle Reservation */}
      <Dialog open={newReservationOpen} onOpenChange={setNewReservationOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Advance Vehicle Reservation</DialogTitle>
            <DialogDescription>Reserve a fleet vehicle with automated time conflict validation.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateReservation} className="space-y-4 py-2">
            <div className="space-y-1">
              <Label className="text-xs">Select Fleet Vehicle</Label>
              <Select value={resForm.vehicle_id} onValueChange={(v) => setResForm({ ...resForm, vehicle_id: v })}>
                <SelectTrigger><SelectValue placeholder="Choose vehicle..." /></SelectTrigger>
                <SelectContent>
                  {vehicles.map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.year} {v.make} {v.model} ({v.licence_plate})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Start Time</Label>
                <Input
                  type="datetime-local"
                  value={resForm.start_time}
                  onChange={(e) => setResForm({ ...resForm, start_time: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">End Time</Label>
                <Input
                  type="datetime-local"
                  value={resForm.end_time}
                  onChange={(e) => setResForm({ ...resForm, end_time: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Purpose</Label>
              <Input
                placeholder="Operational purpose (e.g. community visit, outreach)"
                value={resForm.purpose}
                onChange={(e) => setResForm({ ...resForm, purpose: e.target.value })}
                required
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Destination</Label>
              <Input
                placeholder="Destination town or facility site"
                value={resForm.destination}
                onChange={(e) => setResForm({ ...resForm, destination: e.target.value })}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setNewReservationOpen(false)}>Cancel</Button>
              <Button type="submit">Verify & Confirm Reservation</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL: Key Checkout */}
      <Dialog open={newKeyCheckoutOpen} onOpenChange={setNewKeyCheckoutOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Vehicle Key Checkout Custody</DialogTitle>
            <DialogDescription>Assign physical vehicle key custody to an authorized staff recipient.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCheckoutKey} className="space-y-4 py-2">
            <div className="space-y-1">
              <Label className="text-xs">Fleet Vehicle</Label>
              <Select value={keyForm.vehicle_id} onValueChange={(v) => setKeyForm({ ...keyForm, vehicle_id: v })}>
                <SelectTrigger><SelectValue placeholder="Choose vehicle..." /></SelectTrigger>
                <SelectContent>
                  {vehicles.map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.year} {v.make} {v.model} ({v.licence_plate})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Key Tag Identifier</Label>
              <Input
                placeholder="e.g. KEY-V04"
                value={keyForm.key_tag}
                onChange={(e) => setKeyForm({ ...keyForm, key_tag: e.target.value })}
                required
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Staff Recipient</Label>
              <Select value={keyForm.staff_id} onValueChange={(v) => setKeyForm({ ...keyForm, staff_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select staff..." /></SelectTrigger>
                <SelectContent>
                  {staffUsers.map((u) => (
                    <SelectItem key={u.id} value={u.id}>
                      {u.full_name || u.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setNewKeyCheckoutOpen(false)}>Cancel</Button>
              <Button type="submit">Record Key Checkout</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL: Book Room */}
      <Dialog open={newRoomOpen} onOpenChange={setNewRoomOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reserve Meeting Room / Facility Space</DialogTitle>
            <DialogDescription>Schedule a boardroom or meeting space with conflict detection.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateRoom} className="space-y-4 py-2">
            <div className="space-y-1">
              <Label className="text-xs">Room / Resource Name</Label>
              <Input
                placeholder="Enter configured room or facility space name"
                value={roomForm.room_name}
                onChange={(e) => setRoomForm({ ...roomForm, room_name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Meeting Title</Label>
              <Input
                placeholder="Purpose or meeting title"
                value={roomForm.title}
                onChange={(e) => setRoomForm({ ...roomForm, title: e.target.value })}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Start Time</Label>
                <Input
                  type="datetime-local"
                  value={roomForm.start_time}
                  onChange={(e) => setRoomForm({ ...roomForm, start_time: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">End Time</Label>
                <Input
                  type="datetime-local"
                  value={roomForm.end_time}
                  onChange={(e) => setRoomForm({ ...roomForm, end_time: e.target.value })}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setNewRoomOpen(false)}>Cancel</Button>
              <Button type="submit">Confirm Room Booking</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL: New Supply Item */}
      <Dialog open={newSupplyOpen} onOpenChange={setNewSupplyOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Supplies Inventory Item</DialogTitle>
            <DialogDescription>Register an office or facility consumable item for inventory tracking.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSupply} className="space-y-4 py-2">
            <div className="space-y-1">
              <Label className="text-xs">Item Name</Label>
              <Input
                placeholder="e.g. Printer Paper (Letter), Hand Sanitizer"
                value={supplyForm.item_name}
                onChange={(e) => setSupplyForm({ ...supplyForm, item_name: e.target.value })}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Category</Label>
                <Select value={supplyForm.category} onValueChange={(v) => setSupplyForm({ ...supplyForm, category: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="OFFICE">Office</SelectItem>
                    <SelectItem value="CLEANING">Cleaning & Sanitization</SelectItem>
                    <SelectItem value="FIRST_AID">First Aid & Safety</SelectItem>
                    <SelectItem value="EVENT">Event / Community</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Location</Label>
                <Input
                  placeholder="e.g. Main Supply Closet"
                  value={supplyForm.location}
                  onChange={(e) => setSupplyForm({ ...supplyForm, location: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Quantity</Label>
                <Input
                  type="number"
                  min="0"
                  value={supplyForm.quantity}
                  onChange={(e) => setSupplyForm({ ...supplyForm, quantity: parseInt(e.target.value) || 0 })}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Reorder Threshold</Label>
                <Input
                  type="number"
                  min="0"
                  value={supplyForm.reorder_threshold}
                  onChange={(e) => setSupplyForm({ ...supplyForm, reorder_threshold: parseInt(e.target.value) || 0 })}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setNewSupplyOpen(false)}>Cancel</Button>
              <Button type="submit">Register Supply Item</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Plus, Building2, Wrench, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

export default function Facilities() {
  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "",
    facility_type: "OFFICE",
    address: "",
    status: "OPERATIONAL",
    notes: "",
  });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.entities.Facility.list();
      setFacilities(Array.isArray(res) ? res : []);
    } catch (e) {
      console.error("Failed to load facilities", e);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.entities.Facility.create(form);
      setShowForm(false);
      load();
    } catch (err) {
      console.error("Failed to create facility", err);
    }
    setSaving(false);
  };

  const filtered = facilities.filter((f) => {
    const q = search.toLowerCase();
    return !search || f.name?.toLowerCase().includes(q) || f.address?.toLowerCase().includes(q);
  });

  if (loading)
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Facilities & Maintenance"
        subtitle={`${facilities.length} registered buildings & program sites`}
        actions={
          <Button onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4 mr-2" /> Add Facility
          </Button>
        }
      />

      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Input
            placeholder="Search facilities..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
          <Building2 className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Building2} title="No Facilities Registered" description="Add CRBCL offices, program sites, or shelters to manage building maintenance work orders." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((f) => (
            <div key={f.id} className="p-4 border rounded-xl bg-card shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-base">{f.name}</h3>
                <StatusBadge status={f.status} />
              </div>
              <p className="text-xs text-muted-foreground">{f.address}</p>
              <div className="flex items-center justify-between text-xs pt-2 border-t text-muted-foreground">
                <span>Type: {f.facility_type}</span>
                <span className="flex items-center gap-1 text-primary cursor-pointer hover:underline">
                  <Wrench className="w-3.5 h-3.5" /> Work Orders
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Register Building / Facility</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <Label>Facility Name *</Label>
              <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>

            <div>
              <Label>Address *</Label>
              <Input required value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Facility Type</Label>
                <Select value={form.facility_type} onValueChange={(val) => setForm({ ...form, facility_type: val })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="OFFICE">Office</SelectItem>
                    <SelectItem value="PROGRAM_SITE">Program Site</SelectItem>
                    <SelectItem value="SHELTER">Shelter</SelectItem>
                    <SelectItem value="RESIDENCE">Residence</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Status</Label>
                <Select value={form.status} onValueChange={(val) => setForm({ ...form, status: val })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="OPERATIONAL">Operational</SelectItem>
                    <SelectItem value="MAINTENANCE">Maintenance</SelectItem>
                    <SelectItem value="CLOSED">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Create Facility"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

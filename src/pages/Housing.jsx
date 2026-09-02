import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Plus, Home, Shield, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

export default function Housing() {
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    unit_number: "",
    name: "",
    address: "",
    unit_type: "APARTMENT",
    status: "AVAILABLE",
    bedrooms: 1,
    capacity: 2,
    accessibility_features: "",
    notes: "",
  });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.entities.HousingUnit.list();
      setUnits(Array.isArray(res) ? res : []);
    } catch (e) {
      console.error("Failed to load housing units", e);
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
      await api.entities.HousingUnit.create(form);
      setShowForm(false);
      load();
    } catch (err) {
      console.error("Failed to create housing unit", err);
    }
    setSaving(false);
  };

  const filtered = units.filter((u) => {
    const q = search.toLowerCase();
    return !search || u.unit_number?.toLowerCase().includes(q) || u.name?.toLowerCase().includes(q) || u.address?.toLowerCase().includes(q);
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
        title="Housing & Shelter Units"
        subtitle={`${units.length} registered housing units`}
        actions={
          <Button onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4 mr-2" /> Add Housing Unit
          </Button>
        }
      />

      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Input
            placeholder="Search by unit number, name, or address..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
          <Home className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Home} title="No Housing Units" description="Add CRBCL shelter or housing units to track occupancy and maintenance." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((u) => (
            <div key={u.id} className="p-4 border rounded-xl bg-card shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-base">{u.name}</h3>
                  <p className="text-xs text-muted-foreground">Unit #{u.unit_number}</p>
                </div>
                <StatusBadge status={u.status} />
              </div>
              <p className="text-xs text-muted-foreground">{u.address}</p>
              <div className="flex items-center justify-between text-xs pt-2 border-t text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5" /> Capacity: {u.capacity || 1}
                </span>
                <span>Type: {u.unit_type}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Housing Unit</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Unit Number *</Label>
                <Input required value={form.unit_number} onChange={(e) => setForm({ ...form, unit_number: e.target.value })} />
              </div>
              <div>
                <Label>Unit Name *</Label>
                <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
            </div>

            <div>
              <Label>Address *</Label>
              <Input required value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Unit Type</Label>
                <Select value={form.unit_type} onValueChange={(val) => setForm({ ...form, unit_type: val })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="APARTMENT">Apartment</SelectItem>
                    <SelectItem value="HOUSE">House</SelectItem>
                    <SelectItem value="SHELTER_BED">Shelter Bed</SelectItem>
                    <SelectItem value="SUITE">Suite</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Bedrooms</Label>
                <Input type="number" min="1" value={form.bedrooms} onChange={(e) => setForm({ ...form, bedrooms: parseInt(e.target.value) || 1 })} />
              </div>
              <div>
                <Label>Capacity</Label>
                <Input type="number" min="1" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: parseInt(e.target.value) || 1 })} />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Create Unit"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

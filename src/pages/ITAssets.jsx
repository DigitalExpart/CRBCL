import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Plus, Laptop, Shield, Tag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

export default function ITAssets() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    asset_tag: "",
    asset_type: "LAPTOP",
    manufacturer: "",
    model: "",
    serial_number: "",
    status: "AVAILABLE",
    location: "",
  });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.entities.ITAsset.list();
      setAssets(Array.isArray(res) ? res : []);
    } catch (e) {
      console.error("Failed to load IT assets", e);
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
      await api.entities.ITAsset.create(form);
      setShowForm(false);
      load();
    } catch (err) {
      console.error("Failed to create IT asset", err);
    }
    setSaving(false);
  };

  const filtered = assets.filter((a) => {
    const q = search.toLowerCase();
    return !search || a.asset_tag?.toLowerCase().includes(q) || a.model?.toLowerCase().includes(q) || a.serial_number?.toLowerCase().includes(q);
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
        title="IT Asset Management"
        subtitle={`${assets.length} registered hardware assets`}
        actions={
          <Button onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4 mr-2" /> Add IT Asset
          </Button>
        }
      />

      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Input
            placeholder="Search by asset tag, model, or serial..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
          <Laptop className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Laptop} title="No IT Assets" description="Add laptops, tablets, desktops, and equipment to track assignments and warranties." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((a) => (
            <div key={a.id} className="p-4 border rounded-xl bg-card shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-base">{a.manufacturer} {a.model}</h3>
                  <p className="text-xs text-muted-foreground">Tag: {a.asset_tag}</p>
                </div>
                <StatusBadge status={a.status} />
              </div>
              <p className="text-xs text-muted-foreground">S/N: {a.serial_number}</p>
              <div className="flex items-center justify-between text-xs pt-2 border-t text-muted-foreground">
                <span>Type: {a.asset_type}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Register Hardware Asset</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Asset Tag *</Label>
                <Input required value={form.asset_tag} onChange={(e) => setForm({ ...form, asset_tag: e.target.value })} />
              </div>
              <div>
                <Label>Asset Type</Label>
                <Select value={form.asset_type} onValueChange={(val) => setForm({ ...form, asset_type: val })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LAPTOP">Laptop</SelectItem>
                    <SelectItem value="DESKTOP">Desktop</SelectItem>
                    <SelectItem value="TABLET">Tablet</SelectItem>
                    <SelectItem value="MONITOR">Monitor</SelectItem>
                    <SelectItem value="PRINTER">Printer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Manufacturer *</Label>
                <Input required value={form.manufacturer} onChange={(e) => setForm({ ...form, manufacturer: e.target.value })} />
              </div>
              <div>
                <Label>Model *</Label>
                <Input required value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
              </div>
            </div>

            <div>
              <Label>Serial Number *</Label>
              <Input required value={form.serial_number} onChange={(e) => setForm({ ...form, serial_number: e.target.value })} />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Add Asset"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

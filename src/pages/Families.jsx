import React, { useState, useEffect } from "react";
import { base44 } from "@/api/base44Client";
import { Plus, Search, Heart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

export default function Families() {
  const [families, setFamilies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ family_name: "", primary_contact_name: "", primary_contact_phone: "", primary_contact_email: "", address: "", city: "", province: "Saskatchewan", status: "Active", risk_level: "Low", indigenous_identity: "", band_nation: "", total_members: 1, notes: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setFamilies(await base44.entities.Family.list("-created_date", 50));
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    await base44.entities.Family.create(form);
    setSaving(false);
    setShowForm(false);
    load();
  };

  const filtered = families.filter(f => !search || f.family_name?.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <PageHeader title="Families" subtitle={`${families.length} registered families`} actions={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Add Family</Button>} />

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search families…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Heart} title="No families found" action={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Add Family</Button>} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(f => (
            <div key={f.id} className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-medium text-foreground">{f.family_name}</p>
                  <p className="text-xs text-muted-foreground">{f.total_members || 1} member{(f.total_members || 1) > 1 ? "s" : ""} • {f.indigenous_identity || "—"}</p>
                </div>
                <StatusBadge status={f.status} />
              </div>
              <div className="space-y-1 text-xs text-muted-foreground">
                {f.primary_contact_name && <p>👤 {f.primary_contact_name}</p>}
                {f.primary_contact_phone && <p>☎ {f.primary_contact_phone}</p>}
                {f.city && <p>📍 {f.city}, {f.province}</p>}
              </div>
              <div className="mt-3 pt-3 border-t border-border">
                <StatusBadge status={f.risk_level} />
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-heading">New Family</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div><Label>Family Name *</Label><Input value={form.family_name} onChange={e => setForm({...form, family_name: e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Primary Contact</Label><Input value={form.primary_contact_name} onChange={e => setForm({...form, primary_contact_name: e.target.value})} /></div>
              <div><Label>Phone</Label><Input value={form.primary_contact_phone} onChange={e => setForm({...form, primary_contact_phone: e.target.value})} /></div>
            </div>
            <div><Label>Email</Label><Input type="email" value={form.primary_contact_email} onChange={e => setForm({...form, primary_contact_email: e.target.value})} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Status</Label><Select value={form.status} onValueChange={v => setForm({...form, status: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Active", "Inactive", "Under Review", "Closed"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Risk Level</Label><Select value={form.risk_level} onValueChange={v => setForm({...form, risk_level: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Low", "Medium", "High", "Critical"].map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Indigenous Identity</Label><Select value={form.indigenous_identity} onValueChange={v => setForm({...form, indigenous_identity: v})}><SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger><SelectContent>{["First Nations", "Métis", "Inuit", "Non-Indigenous", "Mixed"].map(i => <SelectItem key={i} value={i}>{i}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Members</Label><Input type="number" min={1} value={form.total_members} onChange={e => setForm({...form, total_members: parseInt(e.target.value) || 1})} /></div>
            </div>
            <div><Label>Band / Nation</Label><Input value={form.band_nation} onChange={e => setForm({...form, band_nation: e.target.value})} /></div>
            <div><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.family_name}>{saving ? "Saving…" : "Add Family"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
import React, { useState, useEffect } from "react";
import { base44 } from "@/api/base44Client";
import { Plus, Search, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";
import ImportExport from "@/components/shared/ImportExport";

const CLIENT_EXPORT_FIELDS = ["first_name","last_name","date_of_birth","gender","status","risk_level","phone","email","address","city","province","indigenous_identity","band_nation","notes"];
const CLIENT_LABELS = { first_name:"First Name", last_name:"Last Name", date_of_birth:"Date of Birth", gender:"Gender", status:"Status", risk_level:"Risk Level", phone:"Phone", email:"Email", address:"Address", city:"City", province:"Province", indigenous_identity:"Indigenous Identity", band_nation:"Band/Nation", notes:"Notes" };

const STATUSES = ["Active", "Inactive", "Pending Intake", "Closed", "Referred"];
const GENDERS = ["Male", "Female", "Non-Binary", "Two-Spirit", "Prefer Not to Say"];
const IDENTITIES = ["First Nations", "Métis", "Inuit", "Non-Indigenous", "Prefer Not to Say"];
const RISK_LEVELS = ["Low", "Medium", "High", "Critical"];

export default function Clients() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ first_name: "", last_name: "", status: "Pending Intake", risk_level: "Low", gender: "", indigenous_identity: "", phone: "", email: "", address: "", city: "", province: "Saskatchewan", band_nation: "", notes: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setClients(await base44.entities.Client.list("-created_date", 50));
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    await base44.entities.Client.create(form);
    setSaving(false);
    setShowForm(false);
    setForm({ first_name: "", last_name: "", status: "Pending Intake", risk_level: "Low", gender: "", indigenous_identity: "", phone: "", email: "", address: "", city: "", province: "Saskatchewan", band_nation: "", notes: "" });
    load();
  };

  const filtered = clients.filter(c => {
    const name = `${c.first_name} ${c.last_name}`.toLowerCase();
    return !search || name.includes(search.toLowerCase()) || c.email?.toLowerCase().includes(search.toLowerCase());
  });

  if (loading) {
    return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Clients"
        subtitle={`${clients.length} registered clients`}
        actions={
          <div className="flex items-center gap-2">
            <ImportExport
              data={filtered}
              filename="clients"
              exportFields={CLIENT_EXPORT_FIELDS}
              fieldLabels={CLIENT_LABELS}
              onImport={async (rows) => {
                for (const row of rows) {
                  if (row.first_name && row.last_name) await base44.entities.Client.create({ status: "Pending Intake", risk_level: "Low", province: "Saskatchewan", ...row });
                }
                load();
              }}
            />
            <Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Add Client</Button>
          </div>
        }
      />

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search by name or email…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Users} title="No clients found" description="Add your first client to begin tracking" action={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Add Client</Button>} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(c => (
            <div key={c.id} className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold text-primary">
                    {c.first_name?.[0]}{c.last_name?.[0]}
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{c.first_name} {c.last_name}</p>
                    <p className="text-xs text-muted-foreground">{c.indigenous_identity || "—"} {c.band_nation ? `• ${c.band_nation}` : ""}</p>
                  </div>
                </div>
                <StatusBadge status={c.status} />
              </div>
              <div className="space-y-1.5 text-xs text-muted-foreground">
                {c.email && <p>✉ {c.email}</p>}
                {c.phone && <p>☎ {c.phone}</p>}
                {c.city && <p>📍 {c.city}, {c.province}</p>}
              </div>
              <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
                <StatusBadge status={c.risk_level} />
                {c.date_of_birth && <span className="text-xs text-muted-foreground">DOB: {c.date_of_birth}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-heading">New Client</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label>First Name *</Label><Input value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})} required /></div>
              <div><Label>Last Name *</Label><Input value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} required /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Status</Label><Select value={form.status} onValueChange={v => setForm({...form, status: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{STATUSES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Risk Level</Label><Select value={form.risk_level} onValueChange={v => setForm({...form, risk_level: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{RISK_LEVELS.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Gender</Label><Select value={form.gender} onValueChange={v => setForm({...form, gender: v})}><SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger><SelectContent>{GENDERS.map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Indigenous Identity</Label><Select value={form.indigenous_identity} onValueChange={v => setForm({...form, indigenous_identity: v})}><SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger><SelectContent>{IDENTITIES.map(i => <SelectItem key={i} value={i}>{i}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Phone</Label><Input value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} /></div>
              <div><Label>Email</Label><Input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} /></div>
            </div>
            <div><Label>Band / Nation</Label><Input value={form.band_nation} onChange={e => setForm({...form, band_nation: e.target.value})} /></div>
            <div><Label>Address</Label><Input value={form.address} onChange={e => setForm({...form, address: e.target.value})} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>City</Label><Input value={form.city} onChange={e => setForm({...form, city: e.target.value})} /></div>
              <div><Label>Province</Label><Input value={form.province} onChange={e => setForm({...form, province: e.target.value})} /></div>
            </div>
            <div><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.first_name || !form.last_name}>{saving ? "Saving…" : "Add Client"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
import React, { useState, useEffect } from "react";
import { base44 } from "@/api/base44Client";
import { Plus, Search, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

const TYPES = ["Safety Concern", "Behavioral", "Medical", "Abuse/Neglect", "Property Damage", "Unauthorized Absence", "Other"];

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", incident_type: "Safety Concern", severity: "Medium", description: "", date_occurred: new Date().toISOString().split("T")[0], location: "", reported_by: "", actions_taken: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => { setLoading(true); setIncidents(await base44.entities.Incident.list("-created_date", 50)); setLoading(false); };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    await base44.entities.Incident.create({ ...form, status: "Reported" });
    setSaving(false);
    setShowForm(false);
    load();
  };

  const filtered = incidents.filter(i => !search || i.title?.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <PageHeader title="Incident Reports" subtitle={`${incidents.length} incidents`} actions={<Button onClick={() => setShowForm(true)} className="bg-destructive hover:bg-destructive/90"><Plus className="w-4 h-4 mr-2" /> Report Incident</Button>} />
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search incidents…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={AlertTriangle} title="No incidents reported" />
      ) : (
        <div className="space-y-3">
          {filtered.map(i => (
            <div key={i.id} className="bg-card rounded-xl border border-border p-4 hover:shadow-md transition-shadow">
              <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${i.severity === "Critical" ? "bg-red-100" : i.severity === "High" ? "bg-orange-100" : "bg-amber-100"}`}>
                  <AlertTriangle className={`w-5 h-5 ${i.severity === "Critical" ? "text-red-600" : i.severity === "High" ? "text-orange-600" : "text-amber-600"}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-medium text-foreground">{i.title}</p>
                    <StatusBadge status={i.severity} />
                    <StatusBadge status={i.status} />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{i.incident_type} • {i.date_occurred || "—"} • {i.location || "—"}</p>
                  {i.description && <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{i.description}</p>}
                  {i.reported_by && <p className="text-xs text-muted-foreground mt-1">Reported by: {i.reported_by}</p>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-heading">Report Incident</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div><Label>Title *</Label><Input value={form.title} onChange={e => setForm({...form, title: e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Type</Label><Select value={form.incident_type} onValueChange={v => setForm({...form, incident_type: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Severity</Label><Select value={form.severity} onValueChange={v => setForm({...form, severity: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Low", "Medium", "High", "Critical"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Date</Label><Input type="date" value={form.date_occurred} onChange={e => setForm({...form, date_occurred: e.target.value})} /></div>
              <div><Label>Location</Label><Input value={form.location} onChange={e => setForm({...form, location: e.target.value})} /></div>
            </div>
            <div><Label>Description *</Label><Textarea rows={3} value={form.description} onChange={e => setForm({...form, description: e.target.value})} required /></div>
            <div><Label>Reported By</Label><Input value={form.reported_by} onChange={e => setForm({...form, reported_by: e.target.value})} /></div>
            <div><Label>Actions Taken</Label><Textarea rows={2} value={form.actions_taken} onChange={e => setForm({...form, actions_taken: e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.title || !form.description}>{saving ? "Submitting…" : "Submit Report"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
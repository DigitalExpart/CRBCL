import React, { useState, useEffect } from "react";
import { base44 } from "@/api/base44Client";
import { Plus, Search, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

const TYPES = ["Initial Assessment", "Follow-Up", "Home Visit", "Court Hearing", "Team Meeting", "Family Meeting", "Counselling", "Cultural Activity", "Other"];

export default function Appointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", appointment_type: "Follow-Up", date: "", time: "", duration_minutes: 60, client_name: "", staff_name: "", location: "", status: "Scheduled", notes: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => { setLoading(true); setAppointments(await base44.entities.Appointment.list("-date", 50)); setLoading(false); };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    await base44.entities.Appointment.create(form);
    setSaving(false);
    setShowForm(false);
    load();
  };

  const filtered = appointments.filter(a => !search || a.title?.toLowerCase().includes(search.toLowerCase()) || a.client_name?.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <PageHeader title="Appointments" subtitle={`${appointments.length} appointments`} actions={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> New Appointment</Button>} />
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search appointments…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={Calendar} title="No appointments" action={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Schedule Appointment</Button>} />
      ) : (
        <div className="space-y-3">
          {filtered.map(a => (
            <div key={a.id} className="bg-card rounded-xl border border-border p-4 flex flex-col sm:flex-row sm:items-center gap-4 hover:shadow-md transition-shadow">
              <div className="w-14 h-14 rounded-lg bg-primary/10 flex flex-col items-center justify-center flex-shrink-0">
                <span className="text-xs font-medium text-primary">{a.date ? new Date(a.date + "T00:00:00").toLocaleDateString("en", { month: "short" }) : "—"}</span>
                <span className="text-lg font-bold text-primary">{a.date ? new Date(a.date + "T00:00:00").getDate() : "—"}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground">{a.title}</p>
                <p className="text-xs text-muted-foreground">{a.appointment_type} • {a.time || "TBD"} • {a.duration_minutes}min</p>
                <p className="text-xs text-muted-foreground mt-0.5">{a.client_name || "No client"} • {a.staff_name || "No staff"} {a.location ? `• ${a.location}` : ""}</p>
              </div>
              <StatusBadge status={a.status} />
            </div>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-heading">New Appointment</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div><Label>Title *</Label><Input value={form.title} onChange={e => setForm({...form, title: e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Type</Label><Select value={form.appointment_type} onValueChange={v => setForm({...form, appointment_type: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Status</Label><Select value={form.status} onValueChange={v => setForm({...form, status: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Scheduled", "Completed", "Cancelled", "No Show", "Rescheduled"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div><Label>Date *</Label><Input type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} required /></div>
              <div><Label>Time</Label><Input type="time" value={form.time} onChange={e => setForm({...form, time: e.target.value})} /></div>
              <div><Label>Duration (min)</Label><Input type="number" min={15} value={form.duration_minutes} onChange={e => setForm({...form, duration_minutes: parseInt(e.target.value) || 60})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Client Name</Label><Input value={form.client_name} onChange={e => setForm({...form, client_name: e.target.value})} /></div>
              <div><Label>Staff Name</Label><Input value={form.staff_name} onChange={e => setForm({...form, staff_name: e.target.value})} /></div>
            </div>
            <div><Label>Location</Label><Input value={form.location} onChange={e => setForm({...form, location: e.target.value})} /></div>
            <div><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.title || !form.date}>{saving ? "Saving…" : "Create"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
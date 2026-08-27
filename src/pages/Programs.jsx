import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Plus, Search, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

const CATEGORIES = ["Youth Services", "Family Support", "Cultural Programming", "Mental Health", "Housing", "Education", "Employment", "Community", "Prevention", "Crisis"];

export default function Programs() {
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", category: "Youth Services", status: "Active", description: "", capacity: 0, enrolled_count: 0, location: "", coordinator_name: "", budget: 0, funding_source: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => { setLoading(true); setPrograms(await api.entities.Program.list("-created_date", 50)); setLoading(false); };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    await api.entities.Program.create(form);
    setSaving(false);
    setShowForm(false);
    load();
  };

  const filtered = programs.filter(p => !search || p.name?.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <PageHeader title="Programs" subtitle={`${programs.length} programs`} actions={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> New Program</Button>} />
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search programs…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={BookOpen} title="No programs found" action={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> New Program</Button>} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(p => {
            const utilization = p.capacity > 0 ? Math.round((p.enrolled_count / p.capacity) * 100) : 0;
            return (
              <div key={p.id} className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-medium text-foreground">{p.name}</p>
                    <p className="text-xs text-muted-foreground">{p.category}</p>
                  </div>
                  <StatusBadge status={p.status} />
                </div>
                {p.description && <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{p.description}</p>}
                <div className="mt-3 space-y-2">
                  {p.capacity > 0 && (
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground">Enrollment</span>
                        <span className="font-medium">{p.enrolled_count || 0}/{p.capacity}</span>
                      </div>
                      <Progress value={utilization} className="h-1.5" />
                    </div>
                  )}
                  <div className="flex justify-between text-xs text-muted-foreground pt-2 border-t border-border">
                    <span>{p.coordinator_name || "No coordinator"}</span>
                    {p.budget > 0 && <span>${p.budget.toLocaleString()}</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-heading">New Program</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div><Label>Name *</Label><Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Category</Label><Select value={form.category} onValueChange={v => setForm({...form, category: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Status</Label><Select value={form.status} onValueChange={v => setForm({...form, status: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Active", "Inactive", "Planning", "Completed"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div><Label>Description</Label><Textarea rows={2} value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Capacity</Label><Input type="number" min={0} value={form.capacity} onChange={e => setForm({...form, capacity: parseInt(e.target.value) || 0})} /></div>
              <div><Label>Current Enrollment</Label><Input type="number" min={0} value={form.enrolled_count} onChange={e => setForm({...form, enrolled_count: parseInt(e.target.value) || 0})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Location</Label><Input value={form.location} onChange={e => setForm({...form, location: e.target.value})} /></div>
              <div><Label>Coordinator</Label><Input value={form.coordinator_name} onChange={e => setForm({...form, coordinator_name: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Budget ($)</Label><Input type="number" min={0} value={form.budget} onChange={e => setForm({...form, budget: parseFloat(e.target.value) || 0})} /></div>
              <div><Label>Funding Source</Label><Input value={form.funding_source} onChange={e => setForm({...form, funding_source: e.target.value})} /></div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.name}>{saving ? "Saving…" : "Create Program"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
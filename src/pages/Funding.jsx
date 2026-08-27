import React, { useState, useEffect } from "react";
import { base44 } from "@/api/base44Client";
import { Plus, Search, DollarSign } from "lucide-react";
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
import ImportExport from "@/components/shared/ImportExport";

const GRANT_EXPORT_FIELDS = ["name","funder","grant_type","amount","amount_spent","status","start_date","end_date","reporting_deadline","program_area","description"];
const GRANT_LABELS = { name:"Grant Name", funder:"Funder", grant_type:"Type", amount:"Amount", amount_spent:"Spent", status:"Status", start_date:"Start Date", end_date:"End Date", reporting_deadline:"Report Deadline", program_area:"Program Area", description:"Description" };

export default function Funding() {
  const [grants, setGrants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", funder: "", grant_type: "Federal", amount: 0, status: "Applied", start_date: "", end_date: "", reporting_deadline: "", program_area: "", description: "", contact_name: "", contact_email: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => { setLoading(true); setGrants(await base44.entities.FundingGrant.list("-created_date", 50)); setLoading(false); };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    await base44.entities.FundingGrant.create(form);
    setSaving(false);
    setShowForm(false);
    load();
  };

  const filtered = grants.filter(g => !search || g.name?.toLowerCase().includes(search.toLowerCase()) || g.funder?.toLowerCase().includes(search.toLowerCase()));
  const totalFunding = grants.filter(g => g.status === "Active" || g.status === "Approved").reduce((s, g) => s + (g.amount || 0), 0);
  const totalSpent = grants.reduce((s, g) => s + (g.amount_spent || 0), 0);

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <PageHeader title="Funding & Grants" subtitle={`$${totalFunding.toLocaleString()} active funding • $${totalSpent.toLocaleString()} spent`} actions={
        <div className="flex items-center gap-2">
          <ImportExport data={filtered} filename="grants" exportFields={GRANT_EXPORT_FIELDS} fieldLabels={GRANT_LABELS} onImport={async (rows) => {
            for (const row of rows) {
              if (row.name && row.funder) await base44.entities.FundingGrant.create({ status: "Applied", grant_type: "Federal", ...row, amount: parseFloat(row.amount) || 0 });
            }
            load();
          }} />
          <Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Add Grant</Button>
        </div>
      } />
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search grants…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={DollarSign} title="No grants found" action={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Add Grant</Button>} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map(g => {
            const spent = g.amount_spent || 0;
            const pct = g.amount > 0 ? Math.round((spent / g.amount) * 100) : 0;
            return (
              <div key={g.id} className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-medium text-foreground">{g.name}</p>
                    <p className="text-xs text-muted-foreground">{g.funder} • {g.grant_type}</p>
                  </div>
                  <StatusBadge status={g.status} />
                </div>
                <div className="mt-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Budget Used</span>
                    <span className="font-medium">${spent.toLocaleString()} / ${(g.amount || 0).toLocaleString()}</span>
                  </div>
                  <Progress value={pct} className="h-1.5" />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground mt-3 pt-3 border-t border-border">
                  <span>{g.start_date || "—"} → {g.end_date || "—"}</span>
                  {g.reporting_deadline && <span className="text-amber-600">Report: {g.reporting_deadline}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-heading">New Grant</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div><Label>Grant Name *</Label><Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Funder *</Label><Input value={form.funder} onChange={e => setForm({...form, funder: e.target.value})} required /></div>
              <div><Label>Type</Label><Select value={form.grant_type} onValueChange={v => setForm({...form, grant_type: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Federal", "Provincial", "Municipal", "Foundation", "Corporate", "Other"].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Amount ($) *</Label><Input type="number" min={0} value={form.amount} onChange={e => setForm({...form, amount: parseFloat(e.target.value) || 0})} required /></div>
              <div><Label>Status</Label><Select value={form.status} onValueChange={v => setForm({...form, status: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Active", "Applied", "Approved", "Pending Review", "Completed", "Rejected", "Expired"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div><Label>Start</Label><Input type="date" value={form.start_date} onChange={e => setForm({...form, start_date: e.target.value})} /></div>
              <div><Label>End</Label><Input type="date" value={form.end_date} onChange={e => setForm({...form, end_date: e.target.value})} /></div>
              <div><Label>Report Due</Label><Input type="date" value={form.reporting_deadline} onChange={e => setForm({...form, reporting_deadline: e.target.value})} /></div>
            </div>
            <div><Label>Program Area</Label><Input value={form.program_area} onChange={e => setForm({...form, program_area: e.target.value})} /></div>
            <div><Label>Description</Label><Textarea rows={2} value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.name || !form.funder}>{saving ? "Saving…" : "Add Grant"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
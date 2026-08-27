import React, { useState, useEffect } from "react";
import { base44 } from "@/api/base44Client";
import { Plus, Search, Gift } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";
import ImportExport from "@/components/shared/ImportExport";

const DON_EXPORT_FIELDS = ["donor_name","donor_email","donor_type","amount","donation_type","payment_method","designation","status","notes"];
const DON_LABELS = { donor_name:"Donor Name", donor_email:"Email", donor_type:"Donor Type", amount:"Amount", donation_type:"Donation Type", payment_method:"Payment Method", designation:"Designation", status:"Status", notes:"Notes" };

export default function Donations() {
  const [donations, setDonations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ donor_name: "", donor_email: "", donor_type: "Individual", amount: 0, donation_type: "One-Time", payment_method: "Credit Card", designation: "General Fund", status: "Completed", notes: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => { setLoading(true); setDonations(await base44.entities.Donation.list("-created_date", 50)); setLoading(false); };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    await base44.entities.Donation.create(form);
    setSaving(false);
    setShowForm(false);
    load();
  };

  const filtered = donations.filter(d => !search || d.donor_name?.toLowerCase().includes(search.toLowerCase()));
  const totalDonations = donations.filter(d => d.status === "Completed").reduce((s, d) => s + (d.amount || 0), 0);

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <PageHeader title="Donations" subtitle={`$${totalDonations.toLocaleString()} total received`} actions={
        <div className="flex items-center gap-2">
          <ImportExport data={filtered} filename="donations" exportFields={DON_EXPORT_FIELDS} fieldLabels={DON_LABELS} onImport={async (rows) => {
            for (const row of rows) {
              if (row.donor_name && row.amount) await base44.entities.Donation.create({ status: "Completed", donor_type: "Individual", ...row, amount: parseFloat(row.amount) || 0 });
            }
            load();
          }} />
          <Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Record Donation</Button>
        </div>
      } />
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search donors…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={Gift} title="No donations recorded" action={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Record Donation</Button>} />
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="bg-muted/50 border-b border-border">
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Donor</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Amount</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden sm:table-cell">Type</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden md:table-cell">Designation</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Status</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden lg:table-cell">Date</th>
              </tr></thead>
              <tbody>
                {filtered.map(d => (
                  <tr key={d.id} className="border-b border-border/50 last:border-0 hover:bg-muted/30">
                    <td className="px-4 py-3">
                      <p className="font-medium text-foreground">{d.donor_name}</p>
                      <p className="text-xs text-muted-foreground">{d.donor_type} • {d.payment_method || "—"}</p>
                    </td>
                    <td className="px-4 py-3 font-semibold text-foreground">${(d.amount || 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">{d.donation_type}</td>
                    <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">{d.designation}</td>
                    <td className="px-4 py-3"><StatusBadge status={d.status} /></td>
                    <td className="px-4 py-3 text-muted-foreground hidden lg:table-cell">{new Date(d.created_date).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-heading">Record Donation</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div><Label>Donor Name *</Label><Input value={form.donor_name} onChange={e => setForm({...form, donor_name: e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Email</Label><Input type="email" value={form.donor_email} onChange={e => setForm({...form, donor_email: e.target.value})} /></div>
              <div><Label>Donor Type</Label><Select value={form.donor_type} onValueChange={v => setForm({...form, donor_type: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Individual", "Corporate", "Foundation", "Government", "Anonymous"].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Amount ($) *</Label><Input type="number" min={0} step={0.01} value={form.amount} onChange={e => setForm({...form, amount: parseFloat(e.target.value) || 0})} required /></div>
              <div><Label>Donation Type</Label><Select value={form.donation_type} onValueChange={v => setForm({...form, donation_type: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["One-Time", "Recurring", "Sponsorship", "In-Kind", "Event"].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Payment Method</Label><Select value={form.payment_method} onValueChange={v => setForm({...form, payment_method: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["Credit Card", "Debit Card", "Interac", "EFT", "Cheque", "Cash", "Other"].map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Designation</Label><Select value={form.designation} onValueChange={v => setForm({...form, designation: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{["General Fund", "Youth Programs", "Cultural Programs", "Housing", "Mental Health", "Education", "Emergency Fund", "Other"].map(d => <SelectItem key={d} value={d}>{d}</SelectItem>)}</SelectContent></Select></div>
            </div>
            <div><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.donor_name || !form.amount}>{saving ? "Saving…" : "Record"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
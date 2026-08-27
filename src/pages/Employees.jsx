import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Plus, Search, UserCog } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";
import ImportExport from "@/components/shared/ImportExport";

const EMP_EXPORT_FIELDS = ["first_name","last_name","email","phone","position","department","status","hire_date","supervisor_name","caseload_count"];
const EMP_LABELS = { first_name:"First Name", last_name:"Last Name", email:"Email", phone:"Phone", position:"Position", department:"Department", status:"Status", hire_date:"Hire Date", supervisor_name:"Supervisor", caseload_count:"Caseload" };

const DEPARTMENTS = ["Administration", "Case Management", "Youth Services", "Family Services", "Mental Health", "Cultural Programs", "Housing", "Finance", "HR", "IT", "Community Outreach"];

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", phone: "", position: "", department: "Administration", status: "Active", hire_date: "", supervisor_name: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => { setLoading(true); setEmployees(await api.entities.Employee.list("-created_date", 50)); setLoading(false); };
  useEffect(() => { load(); }, []);

  const handleImport = async (rows) => {
    for (const row of rows) {
      if (row.first_name && row.last_name && row.position) await api.entities.Employee.create({ status: "Active", department: "Administration", ...row });
    }
    load();
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    await api.entities.Employee.create(form);
    setSaving(false);
    setShowForm(false);
    load();
  };

  const filtered = employees.filter(emp => {
    const name = `${emp.first_name} ${emp.last_name}`.toLowerCase();
    return !search || name.includes(search.toLowerCase()) || emp.position?.toLowerCase().includes(search.toLowerCase());
  });

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <PageHeader title="HR & Staff" subtitle={`${employees.length} employees`} actions={
        <div className="flex items-center gap-2">
          <ImportExport data={employees} filename="employees" exportFields={EMP_EXPORT_FIELDS} fieldLabels={EMP_LABELS} onImport={handleImport} />
          <Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Add Employee</Button>
        </div>
      } />
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search employees…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={UserCog} title="No employees found" action={<Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> Add Employee</Button>} />
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="bg-muted/50 border-b border-border">
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Employee</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden md:table-cell">Position</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden sm:table-cell">Department</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Status</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden lg:table-cell">Caseload</th>
              </tr></thead>
              <tbody>
                {filtered.map(emp => (
                  <tr key={emp.id} className="border-b border-border/50 last:border-0 hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary">{emp.first_name?.[0]}{emp.last_name?.[0]}</div>
                        <div>
                          <p className="font-medium text-foreground">{emp.first_name} {emp.last_name}</p>
                          <p className="text-xs text-muted-foreground">{emp.email || "—"}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">{emp.position}</td>
                    <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">{emp.department}</td>
                    <td className="px-4 py-3"><StatusBadge status={emp.status} /></td>
                    <td className="px-4 py-3 text-muted-foreground hidden lg:table-cell">{emp.caseload_count || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-heading">New Employee</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label>First Name *</Label><Input value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})} required /></div>
              <div><Label>Last Name *</Label><Input value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} required /></div>
            </div>
            <div><Label>Position *</Label><Input value={form.position} onChange={e => setForm({...form, position: e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Department</Label><Select value={form.department} onValueChange={v => setForm({...form, department: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{DEPARTMENTS.map(d => <SelectItem key={d} value={d}>{d}</SelectItem>)}</SelectContent></Select></div>
              <div><Label>Hire Date</Label><Input type="date" value={form.hire_date} onChange={e => setForm({...form, hire_date: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Email</Label><Input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} /></div>
              <div><Label>Phone</Label><Input value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} /></div>
            </div>
            <div><Label>Supervisor</Label><Input value={form.supervisor_name} onChange={e => setForm({...form, supervisor_name: e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.first_name || !form.last_name || !form.position}>{saving ? "Saving…" : "Add Employee"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
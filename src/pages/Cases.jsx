import React, { useState, useEffect } from "react";
import { base44 } from "@/api/base44Client";
import { Link } from "react-router-dom";
import { Plus, Search, Filter, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";
import CaseFormDialog from "@/components/cases/CaseFormDialog";
import ImportExport from "@/components/shared/ImportExport";

const CASE_EXPORT_FIELDS = ["case_number","title","case_type","status","priority","risk_level","assigned_worker_name","intake_date","referral_source","description"];
const CASE_LABELS = { case_number:"Case #", title:"Title", case_type:"Type", status:"Status", priority:"Priority", risk_level:"Risk Level", assigned_worker_name:"Assigned Worker", intake_date:"Intake Date", referral_source:"Referral Source", description:"Description" };

export default function Cases() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    const data = await base44.entities.Case.list("-created_date", 50);
    setCases(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (form) => {
    const caseNum = `CRB-${Date.now().toString().slice(-6)}`;
    await base44.entities.Case.create({ ...form, case_number: caseNum, status: "Open" });
    load();
  };

  const filtered = cases.filter(c => {
    const matchSearch = !search || c.title?.toLowerCase().includes(search.toLowerCase()) || c.case_number?.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || c.status === statusFilter;
    return matchSearch && matchStatus;
  });

  if (loading) {
    return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Case Management"
        subtitle={`${cases.length} total cases`}
        actions={
          <div className="flex items-center gap-2">
            <ImportExport
              data={filtered}
              filename="cases"
              exportFields={CASE_EXPORT_FIELDS}
              fieldLabels={CASE_LABELS}
              onImport={async (rows) => {
                for (const row of rows) {
                  if (row.title) await base44.entities.Case.create({ ...row, case_number: row.case_number || `CRB-${Date.now().toString().slice(-6)}`, status: row.status || "Open" });
                }
                load();
              }}
            />
            <Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> New Case</Button>
          </div>
        }
      />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search cases…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-44">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            {["Open", "In Progress", "Under Review", "Pending", "Escalated", "Closed"].map(s => (
              <SelectItem key={s} value={s}>{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Cases Table */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title="No cases found"
          description={search ? "Try a different search term" : "Create your first case to get started"}
          action={!search && <Button onClick={() => setShowForm(true)}><Plus className="w-4 h-4 mr-2" /> New Case</Button>}
        />
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/50 border-b border-border">
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Case #</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Title</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden md:table-cell">Type</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden sm:table-cell">Priority</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden lg:table-cell">Worker</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden lg:table-cell">Intake Date</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(c => (
                  <tr key={c.id} className="border-b border-border/50 last:border-0 hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-xs text-muted-foreground font-mono">{c.case_number || "—"}</td>
                    <td className="px-4 py-3">
                      <Link to={`/cases/${c.id}`} className="font-medium text-foreground hover:text-primary transition-colors">
                        {c.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">{c.case_type}</td>
                    <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                    <td className="px-4 py-3 hidden sm:table-cell"><StatusBadge status={c.priority} /></td>
                    <td className="px-4 py-3 text-muted-foreground hidden lg:table-cell">{c.assigned_worker_name || "—"}</td>
                    <td className="px-4 py-3 text-muted-foreground hidden lg:table-cell">{c.intake_date || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <CaseFormDialog open={showForm} onOpenChange={setShowForm} onSubmit={handleCreate} />
    </div>
  );
}
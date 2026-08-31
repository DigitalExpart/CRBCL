import React, { useState, useEffect } from "react";
import { casesApi } from "@/api/cases";
import { Link } from "react-router-dom";
import { Plus, Search, Filter, FolderOpen, AlertCircle, ArrowUpDown, ChevronLeft, ChevronRight, UserCheck, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";
import CaseFormDialog from "@/components/cases/CaseFormDialog";
import ImportExport from "@/components/shared/ImportExport";

const CASE_EXPORT_FIELDS = [
  "case_number",
  "title",
  "case_type",
  "status",
  "stage",
  "priority",
  "risk_level",
  "assigned_worker_name",
  "intake_date",
  "referral_source",
  "description",
];

const CASE_LABELS = {
  case_number: "Case #",
  title: "Title",
  case_type: "Type",
  status: "Status",
  stage: "Stage",
  priority: "Priority",
  risk_level: "Risk Level",
  assigned_worker_name: "Assigned Worker",
  intake_date: "Intake Date",
  referral_source: "Referral Source",
  description: "Description",
};

export default function Cases() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [showForm, setShowForm] = useState(false);

  const loadCases = async () => {
    setLoading(true);
    try {
      const data = await casesApi.list({ sort: "-created_date", limit: 100 });
      setCases(data || []);
    } catch (e) {
      console.error("Error loading cases:", e);
      setCases([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleCreate = async (form) => {
    try {
      await casesApi.create(form);
      loadCases();
    } catch (err) {
      console.error("Error creating case:", err);
      alert(err.message || "Failed to create case");
    }
  };

  const filtered = cases.filter((c) => {
    const s = search.toLowerCase();
    const matchSearch =
      !search ||
      c.title?.toLowerCase().includes(s) ||
      c.case_number?.toLowerCase().includes(s) ||
      c.assigned_worker_name?.toLowerCase().includes(s);

    const matchStatus = statusFilter === "all" || c.status === statusFilter;
    const matchType = typeFilter === "all" || c.case_type === typeFilter;
    const matchStage = stageFilter === "all" || c.stage === stageFilter;
    const matchPriority = priorityFilter === "all" || c.priority === priorityFilter;

    return matchSearch && matchStatus && matchType && matchStage && matchPriority;
  });

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case "critical":
      case "urgent":
        return "bg-rose-500/15 text-rose-700 dark:text-rose-400 border-rose-500/30";
      case "high":
        return "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30";
      case "medium":
        return "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30";
      default:
        return "bg-slate-500/15 text-slate-700 dark:text-slate-400 border-slate-500/30";
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Case Management"
        subtitle={`${cases.length} total cases recorded`}
        actions={
          <div className="flex items-center gap-2">
            <ImportExport
              data={filtered}
              filename="cases"
              exportFields={CASE_EXPORT_FIELDS}
              fieldLabels={CASE_LABELS}
              onImport={async (rows) => {
                for (const row of rows) {
                  if (row.title) await casesApi.create(row);
                }
                loadCases();
              }}
            />
            <Button onClick={() => setShowForm(true)}>
              <Plus className="w-4 h-4 mr-2" /> New Case File
            </Button>
          </div>
        }
      />

      {/* Filters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="relative lg:col-span-2">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by case #, title, or worker…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger>
            <Filter className="w-4 h-4 mr-2 text-muted-foreground" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="Open">Open</SelectItem>
            <SelectItem value="In Progress">In Progress</SelectItem>
            <SelectItem value="Under Review">Under Review</SelectItem>
            <SelectItem value="Reopened">Reopened</SelectItem>
            <SelectItem value="Closed">Closed</SelectItem>
          </SelectContent>
        </Select>

        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger>
            <SelectValue placeholder="Case Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="PROTECTION">Child Protection</SelectItem>
            <SelectItem value="PREVENTION">Prevention & Wellness</SelectItem>
            <SelectItem value="FAMILY_PRESERVATION">Family Preservation</SelectItem>
            <SelectItem value="POST_MAJORITY_SUPPORT">Post-Majority Support</SelectItem>
            <SelectItem value="FOSTER_CARE">Foster Care</SelectItem>
            <SelectItem value="CUSTOMARY_CARE">Customary Care</SelectItem>
          </SelectContent>
        </Select>

        <Select value={stageFilter} onValueChange={setStageFilter}>
          <SelectTrigger>
            <SelectValue placeholder="Stage" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Stages</SelectItem>
            <SelectItem value="INTAKE">Intake</SelectItem>
            <SelectItem value="INVESTIGATION">Investigation</SelectItem>
            <SelectItem value="ASSESSMENT">Assessment</SelectItem>
            <SelectItem value="CASE_PLANNING">Case Planning</SelectItem>
            <SelectItem value="SERVICE_DELIVERY">Service Delivery</SelectItem>
            <SelectItem value="CLOSED">Closed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Cases Content */}
      {loading ? (
        <div className="flex items-center justify-center h-[40vh]">
          <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title="No cases match criteria"
          description={
            search || statusFilter !== "all" || typeFilter !== "all"
              ? "Try adjusting your search terms or filters"
              : "Open a new case file to initiate case management"
          }
          action={
            !search && (
              <Button onClick={() => setShowForm(true)}>
                <Plus className="w-4 h-4 mr-2" /> New Case File
              </Button>
            )
          }
        />
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-muted/50 text-muted-foreground font-medium text-xs border-b border-border">
                <tr>
                  <th className="py-3.5 px-4">Case #</th>
                  <th className="py-3.5 px-4">Title & Description</th>
                  <th className="py-3.5 px-4">Type / Stage</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Assigned Worker</th>
                  <th className="py-3.5 px-4">Priority / Risk</th>
                  <th className="py-3.5 px-4">Intake Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filtered.map((c) => (
                  <tr
                    key={c.id}
                    className="hover:bg-muted/30 transition-colors group cursor-pointer"
                  >
                    <td className="py-3.5 px-4 font-mono font-medium text-primary">
                      <Link to={`/cases/${c.id}`} className="hover:underline">
                        {c.case_number || "Draft File"}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4">
                      <Link to={`/cases/${c.id}`} className="block">
                        <span className="font-medium text-foreground block hover:text-primary transition-colors">
                          {c.title}
                        </span>
                        {c.description && (
                          <span className="text-xs text-muted-foreground line-clamp-1">
                            {c.description}
                          </span>
                        )}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 space-y-1">
                      <Badge variant="outline" className="text-xs">
                        {c.case_type || "Standard"}
                      </Badge>
                      {c.stage && (
                        <div className="text-[11px] text-muted-foreground font-mono">
                          {c.stage}
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={c.status || "Open"} />
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 text-xs text-foreground">
                        <UserCheck className="w-3.5 h-3.5 text-muted-foreground" />
                        <span>{c.assigned_worker_name || "Unassigned"}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 space-x-1.5">
                      {c.priority && (
                        <Badge
                          variant="outline"
                          className={`text-[11px] ${getPriorityColor(c.priority)}`}
                        >
                          {c.priority}
                        </Badge>
                      )}
                      {c.risk_level && (
                        <Badge
                          variant="outline"
                          className={`text-[11px] ${getPriorityColor(c.risk_level)}`}
                        >
                          {c.risk_level} Risk
                        </Badge>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-muted-foreground">
                      {c.intake_date || (c.created_at ? new Date(c.created_at).toLocaleDateString() : "—")}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link to={`/cases/${c.id}`}>
                        <Button variant="ghost" size="sm" className="h-8 text-xs">
                          Open 360°
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <CaseFormDialog
        open={showForm}
        onOpenChange={setShowForm}
        onSubmit={handleCreate}
      />
    </div>
  );
}
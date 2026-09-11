import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api";
import PageHeader from "@/components/shared/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Users,
  Briefcase,
  Home,
  ShieldAlert,
  Calendar,
  DollarSign,
  HeartHandshake,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  Building2,
  Filter,
  Plus,
  ArrowUpRight,
  TrendingUp,
  Sparkles,
  Info,
  Scale,
} from "lucide-react";
import { DEPARTMENTS } from "@/constants/departments";

export default function CEODashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportingPeriod, setReportingPeriod] = useState(
    new Date().toISOString().slice(0, 7) // e.g. "2026-09"
  );
  const [selectedDeptFilter, setSelectedDeptFilter] = useState("ALL");

  // Modals state
  const [initiativeModalOpen, setInitiativeModalOpen] = useState(false);
  const [boardActionModalOpen, setBoardActionModalOpen] = useState(false);
  const [decisionModalOpen, setDecisionModalOpen] = useState(false);
  const [deptUpdateModalOpen, setDeptUpdateModalOpen] = useState(false);
  const [selectedBoardAction, setSelectedBoardAction] = useState(null);

  // Form states
  const [initForm, setInitForm] = useState({
    title: "",
    description: "",
    department: DEPARTMENTS[0],
    status: "ON_TRACK",
    priority: "HIGH",
    target_date: "",
    progress_percentage: 0,
    latest_update: "",
  });

  const [baForm, setBaForm] = useState({
    originating_department: DEPARTMENTS[0],
    title: "",
    background_summary: "",
    requested_action: "",
    priority: "HIGH",
    required_by_date: "",
  });

  const [decisionForm, setDecisionForm] = useState({
    status: "APPROVED",
    decision: "",
    decision_notes: "",
  });

  const [deptUpdateForm, setDeptUpdateForm] = useState({
    reporting_period: reportingPeriod,
    department: DEPARTMENTS[0],
    headline_summary: "",
    accomplishments_narrative: "",
    risks_issues: "",
    support_decision_requested: "",
    status: "SUBMITTED",
  });

  async function loadDashboard(period = reportingPeriod) {
    setLoading(true);
    setError(null);
    try {
      const res = await api.ceoDashboard.getDashboard({ reporting_period: period });
      setData(res);
    } catch (err) {
      console.error("Failed to load CEO dashboard:", err);
      setError(err.message || "Failed to load executive dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard(reportingPeriod);
  }, [reportingPeriod]);

  // Initiative submission
  async function handleCreateInitiative(e) {
    e.preventDefault();
    try {
      await api.ceoDashboard.createInitiative({
        ...initForm,
        target_date: initForm.target_date || null,
        progress_percentage: parseInt(initForm.progress_percentage, 10) || 0,
      });
      setInitiativeModalOpen(false);
      setInitForm({
        title: "",
        description: "",
        department: DEPARTMENTS[0],
        status: "ON_TRACK",
        priority: "HIGH",
        target_date: "",
        progress_percentage: 0,
        latest_update: "",
      });
      loadDashboard();
    } catch (err) {
      alert("Failed to create initiative: " + err.message);
    }
  }

  // Board action submission
  async function handleCreateBoardAction(e) {
    e.preventDefault();
    try {
      await api.ceoDashboard.createBoardAction({
        ...baForm,
        required_by_date: baForm.required_by_date || null,
      });
      setBoardActionModalOpen(false);
      setBaForm({
        originating_department: DEPARTMENTS[0],
        title: "",
        background_summary: "",
        requested_action: "",
        priority: "HIGH",
        required_by_date: "",
      });
      loadDashboard();
    } catch (err) {
      alert("Failed to submit board action: " + err.message);
    }
  }

  // Board decision recording
  async function handleRecordDecision(e) {
    e.preventDefault();
    if (!selectedBoardAction) return;
    try {
      await api.ceoDashboard.recordBoardDecision(selectedBoardAction.id, decisionForm);
      setDecisionModalOpen(false);
      setSelectedBoardAction(null);
      setDecisionForm({ status: "APPROVED", decision: "", decision_notes: "" });
      loadDashboard();
    } catch (err) {
      alert("Failed to record decision: " + err.message);
    }
  }

  // Department update submission
  async function handleSubmitDeptUpdate(e) {
    e.preventDefault();
    try {
      await api.ceoDashboard.submitDepartmentUpdate({
        ...deptUpdateForm,
        reporting_period: reportingPeriod,
      });
      setDeptUpdateModalOpen(false);
      setDeptUpdateForm({
        reporting_period: reportingPeriod,
        department: DEPARTMENTS[0],
        headline_summary: "",
        accomplishments_narrative: "",
        risks_issues: "",
        support_decision_requested: "",
        status: "SUBMITTED",
      });
      loadDashboard();
    } catch (err) {
      alert("Failed to submit department update: " + err.message);
    }
  }

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="font-medium text-sm">Aggregating live organizational command centre metrics...</p>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="p-6 rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/20 text-red-900 dark:text-red-200">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <h3 className="font-semibold text-lg">Executive Command Centre Access</h3>
          </div>
          <p className="text-sm">{error}</p>
          <div className="mt-4">
            <Button onClick={() => loadDashboard()} variant="outline" size="sm">
              Retry Connection
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const exec = data?.executive_summary || {};
  const deptHealth = data?.department_health || [];
  const workforce = data?.workforce || {};
  const service = data?.service_delivery || {};
  const finance = data?.finance || {};
  const compliance = data?.compliance_risk || {};
  const criticalDates = data?.critical_dates || [];
  const initiatives = data?.active_initiatives || [];
  const boardActions = data?.pending_board_actions || [];
  const deptUpdates = data?.recent_department_updates || [];

  // Filtered lists
  const filteredDeptHealth =
    selectedDeptFilter === "ALL"
      ? deptHealth
      : deptHealth.filter((d) => d.department === selectedDeptFilter);

  const filteredInitiatives =
    selectedDeptFilter === "ALL"
      ? initiatives
      : initiatives.filter((i) => i.department === selectedDeptFilter);

  const filteredBoardActions =
    selectedDeptFilter === "ALL"
      ? boardActions
      : boardActions.filter((b) => b.originating_department === selectedDeptFilter);

  const filteredDeptUpdates =
    selectedDeptFilter === "ALL"
      ? deptUpdates
      : deptUpdates.filter((u) => u.department === selectedDeptFilter);

  function renderMetricValue(metric, unit = "") {
    if (!metric) return "—";
    if (!metric.is_available) {
      return (
        <span
          className="text-xs font-normal text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-800"
          title={metric.reason || "Metric not currently structured"}
        >
          Policy Needed
        </span>
      );
    }
    return (
      <span>
        {metric.value?.toLocaleString() || 0}
        {unit}
      </span>
    );
  }

  function getStatusBadge(status) {
    switch (status) {
      case "ON_TRACK":
      case "APPROVED":
      case "COMPLETED":
        return <Badge className="bg-emerald-600 hover:bg-emerald-700 text-white">{status}</Badge>;
      case "AT_RISK":
      case "DECISION_REQUIRED":
      case "UNDER_REVIEW":
        return <Badge className="bg-amber-600 hover:bg-amber-700 text-white">{status}</Badge>;
      case "DELAYED":
      case "DECLINED":
      case "CRITICAL":
        return <Badge className="bg-rose-600 hover:bg-rose-700 text-white">{status}</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header & Controls */}
      <PageHeader
        title="CEO Executive Command Centre"
        subtitle="Authoritative organization-wide operational command, strategic deliverables, and Board governance"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 bg-card border rounded-md px-3 py-1.5 shadow-sm">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <input
                type="month"
                value={reportingPeriod}
                onChange={(e) => setReportingPeriod(e.target.value)}
                className="bg-transparent text-sm font-medium focus:outline-none"
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeptUpdateModalOpen(true)}
              className="gap-1.5"
            >
              <FileText className="w-4 h-4 text-primary" />
              Submit Dept Update
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setBoardActionModalOpen(true)}
              className="gap-1.5"
            >
              <Scale className="w-4 h-4 text-primary" />
              Request Board Action
            </Button>

            <Button
              size="sm"
              onClick={() => setInitiativeModalOpen(true)}
              className="gap-1.5"
            >
              <Plus className="w-4 h-4" />
              New Initiative
            </Button>
          </div>
        }
      />

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-card p-3 rounded-lg border shadow-sm">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Department Scope:
          </span>
          <select
            value={selectedDeptFilter}
            onChange={(e) => setSelectedDeptFilter(e.target.value)}
            className="text-sm bg-muted/50 border rounded px-2.5 py-1 focus:outline-none"
          >
            <option value="ALL">All Departments (Executive View)</option>
            {DEPARTMENTS.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Live Authoritative
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-500" /> Governance Attention
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-rose-500" /> Exceptions
          </span>
        </div>
      </div>

      {/* Top 10 Executive Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {/* 1. Active Staff */}
        <Card className="shadow-sm">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Total Active Staff</span>
              <Users className="w-3.5 h-3.5 text-primary" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold">{renderMetricValue(exec.total_active_employees)}</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Across configured depts</p>
          </CardContent>
        </Card>

        {/* 2. Active Cases */}
        <Card className="shadow-sm">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Active Cases</span>
              <Briefcase className="w-3.5 h-3.5 text-primary" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold">{renderMetricValue(exec.active_cases)}</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Open & active files</p>
          </CardContent>
        </Card>

        {/* 3. Families Served */}
        <Card className="shadow-sm">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Families Served</span>
              <HeartHandshake className="w-3.5 h-3.5 text-primary" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold">{renderMetricValue(exec.families_served)}</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Distinct client families</p>
          </CardContent>
        </Card>

        {/* 4. Children in Care */}
        <Card className="shadow-sm border-blue-200 dark:border-blue-900/40">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Children in Placement</span>
              <ShieldAlert className="w-3.5 h-3.5 text-blue-600" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold text-blue-700 dark:text-blue-300">
              {renderMetricValue(exec.children_in_care)}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Active placement episodes</p>
          </CardContent>
        </Card>

        {/* 5. Resource Homes */}
        <Card className="shadow-sm">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Active Resource Homes</span>
              <Home className="w-3.5 h-3.5 text-primary" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold">{renderMetricValue(exec.active_resource_homes)}</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Licensed & approved</p>
          </CardContent>
        </Card>

        {/* 6. Bed Capacity & Availability */}
        <Card className="shadow-sm">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Available Beds</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
              {renderMetricValue(exec.resource_available_beds)}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Capacity: {exec.resource_capacity?.value || 0}
            </p>
          </CardContent>
        </Card>

        {/* 7. Active Programs */}
        <Card className="shadow-sm">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Active Programs</span>
              <Building2 className="w-3.5 h-3.5 text-primary" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold">{renderMetricValue(exec.active_programs)}</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Cultural & community</p>
          </CardContent>
        </Card>

        {/* 8. Compliance Exceptions */}
        <Card className="shadow-sm border-rose-200 dark:border-rose-900/40">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Compliance Exceptions</span>
              <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold text-rose-600 dark:text-rose-400">
              {renderMetricValue(exec.major_compliance_exceptions)}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Incidents, audits, expiries</p>
          </CardContent>
        </Card>

        {/* 9. Delayed Initiatives */}
        <Card className="shadow-sm border-amber-200 dark:border-amber-900/40">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Delayed Deliverables</span>
              <Clock className="w-3.5 h-3.5 text-amber-600" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold text-amber-600 dark:text-amber-400">
              {renderMetricValue(exec.delayed_overdue_initiatives)}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Target dates at risk</p>
          </CardContent>
        </Card>

        {/* 10. Board Actions Awaiting */}
        <Card className="shadow-sm border-purple-200 dark:border-purple-900/40">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Board Decisions</span>
              <Scale className="w-3.5 h-3.5 text-purple-600" />
            </CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="text-xl font-bold text-purple-600 dark:text-purple-400">
              {renderMetricValue(exec.board_actions_awaiting_decision)}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Awaiting governance review</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="bg-card border p-1 rounded-lg">
          <TabsTrigger value="overview">Department Health</TabsTrigger>
          <TabsTrigger value="initiatives">Strategic Initiatives ({initiatives.length})</TabsTrigger>
          <TabsTrigger value="board">Board Attention ({boardActions.length})</TabsTrigger>
          <TabsTrigger value="updates">Periodic Updates ({deptUpdates.length})</TabsTrigger>
          <TabsTrigger value="service">Service Delivery</TabsTrigger>
          <TabsTrigger value="workforce">Workforce & HR</TabsTrigger>
          <TabsTrigger value="finance">Finance & Funding</TabsTrigger>
          <TabsTrigger value="compliance">Compliance & Risk ({compliance.total_exceptions || 0})</TabsTrigger>
        </TabsList>

        {/* ── Tab 1: Department Health & Critical Dates ──────────────────────── */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Department Health Cards (2 Cols) */}
            <div className="lg:col-span-2 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-base flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-primary" />
                  Operational Department Health
                </h3>
                <span className="text-xs text-muted-foreground">
                  Dynamically aggregated per configured team
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredDeptHealth.map((dept) => (
                  <Card key={dept.department} className="shadow-sm hover:border-primary/40 transition-colors">
                    <CardHeader className="p-4 pb-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <CardTitle className="text-sm font-semibold">{dept.name}</CardTitle>
                          <CardDescription className="text-xs">{dept.department}</CardDescription>
                        </div>
                        {dept.delayed_initiatives > 0 ? (
                          <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                            {dept.delayed_initiatives} delayed
                          </Badge>
                        ) : dept.has_recent_update ? (
                          <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-300">
                            Updated
                          </Badge>
                        ) : null}
                      </div>
                    </CardHeader>
                    <CardContent className="p-4 pt-1 space-y-2">
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="bg-muted/40 p-2 rounded">
                          <span className="text-muted-foreground block text-[10px]">Active Staff</span>
                          <span className="font-bold text-sm">{dept.active_staff}</span>
                        </div>
                        <div className="bg-muted/40 p-2 rounded">
                          <span className="text-muted-foreground block text-[10px]">
                            {dept.operational_metric_label || "Active Files"}
                          </span>
                          <span className="font-bold text-sm">
                            {dept.operational_metric_value || "—"}
                          </span>
                        </div>
                      </div>

                      {dept.latest_update_headline && (
                        <div className="text-xs bg-primary/5 p-2 rounded border border-primary/10">
                          <span className="font-semibold text-[10px] text-primary block">
                            Latest Update ({dept.latest_update_period}):
                          </span>
                          <p className="line-clamp-2 text-muted-foreground">{dept.latest_update_headline}</p>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t">
                        <span>Initiatives: {dept.active_initiatives}</span>
                        <span>Board Actions: {dept.pending_board_actions}</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Critical Dates Feed (1 Col) */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-base flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-primary" />
                  Critical Executive Dates
                </h3>
                <span className="text-xs text-muted-foreground">Next 30–60 Days</span>
              </div>

              <Card className="shadow-sm">
                <CardContent className="p-4 divide-y">
                  {criticalDates.length === 0 ? (
                    <p className="text-xs text-muted-foreground py-4 text-center">
                      No upcoming critical milestones recorded.
                    </p>
                  ) : (
                    criticalDates.map((item, idx) => (
                      <div key={idx} className="py-2.5 first:pt-0 last:pb-0 space-y-1">
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-xs font-semibold line-clamp-1">{item.title}</span>
                          <Badge
                            variant={
                              item.urgency === "OVERDUE"
                                ? "destructive"
                                : item.urgency === "URGENT"
                                ? "default"
                                : "outline"
                            }
                            className="text-[10px] px-1 py-0 uppercase"
                          >
                            {item.urgency}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                          <span>{item.department || item.category}</span>
                          <span className="font-medium text-foreground">{item.date}</span>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* ── Tab 2: Strategic Initiatives ──────────────────────────────────── */}
        <TabsContent value="initiatives" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-base">Strategic Deliverables & Projects</h3>
              <p className="text-xs text-muted-foreground">
                Canonical status tracking, explicit progress percentages, and audit logs
              </p>
            </div>
            <Button size="sm" onClick={() => setInitiativeModalOpen(true)}>
              <Plus className="w-4 h-4 mr-1.5" />
              Add Initiative
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredInitiatives.map((init) => (
              <Card key={init.id} className="shadow-sm">
                <CardHeader className="p-4 pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <CardTitle className="text-sm font-semibold">{init.title}</CardTitle>
                      <CardDescription className="text-xs">
                        {init.department || "Agency-Wide"} • Owner: {init.responsible_owner_name || "Unassigned"}
                      </CardDescription>
                    </div>
                    {getStatusBadge(init.status)}
                  </div>
                </CardHeader>
                <CardContent className="p-4 pt-2 space-y-3">
                  <p className="text-xs text-muted-foreground line-clamp-2">{init.description}</p>

                  {/* Progress bar */}
                  {init.progress_percentage !== null && init.progress_percentage !== undefined && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-muted-foreground">Progress</span>
                        <span className="font-semibold">{init.progress_percentage}%</span>
                      </div>
                      <Progress value={init.progress_percentage} className="h-1.5" />
                    </div>
                  )}

                  {init.latest_update && (
                    <div className="bg-muted/50 p-2.5 rounded text-xs">
                      <span className="font-semibold text-[10px] text-muted-foreground block uppercase">
                        Latest Progress Note:
                      </span>
                      <p className="text-muted-foreground mt-0.5">{init.latest_update}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-2 border-t">
                    <span>Priority: {init.priority}</span>
                    <span>Target Date: {init.target_date || "Open"}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ── Tab 3: Board Actions & Attention ──────────────────────────────── */}
        <TabsContent value="board" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-base">Requests for Board Action or Involvement</h3>
              <p className="text-xs text-muted-foreground">
                Governance-safe requests, required-by deadlines, and decision tracking
              </p>
            </div>
            <Button size="sm" onClick={() => setBoardActionModalOpen(true)}>
              <Plus className="w-4 h-4 mr-1.5" />
              New Board Action Request
            </Button>
          </div>

          <div className="space-y-3">
            {filteredBoardActions.map((ba) => (
              <Card key={ba.id} className="shadow-sm">
                <CardContent className="p-4 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="font-mono text-xs">
                        {ba.reference_number}
                      </Badge>
                      <h4 className="font-semibold text-sm">{ba.title}</h4>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(ba.status)}
                      {ba.status !== "APPROVED" && ba.status !== "RESOLVED" && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs"
                          onClick={() => {
                            setSelectedBoardAction(ba);
                            setDecisionModalOpen(true);
                          }}
                        >
                          Record Decision
                        </Button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="font-semibold text-muted-foreground block mb-1">
                        Background & Context:
                      </span>
                      <p className="text-muted-foreground">{ba.background_summary}</p>
                    </div>
                    <div className="bg-primary/5 p-3 rounded border border-primary/10">
                      <span className="font-semibold text-primary block mb-1">
                        Requested Action / Decision:
                      </span>
                      <p className="text-foreground">{ba.requested_action}</p>
                    </div>
                  </div>

                  {ba.decision && (
                    <div className="bg-emerald-50 dark:bg-emerald-950/20 p-2.5 rounded border border-emerald-200 text-xs">
                      <span className="font-semibold text-emerald-800 dark:text-emerald-300 block">
                        Board Decision ({ba.decision_date?.slice(0, 10)} by {ba.decided_by_name || "Board"}):
                      </span>
                      <p className="text-emerald-900 dark:text-emerald-200 mt-0.5">{ba.decision}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                    <span>Originating Dept: {ba.originating_department}</span>
                    <span>Required By: {ba.required_by_date || "Next Board Meeting"}</span>
                    <span>Submitted: {ba.submitted_date?.slice(0, 10)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ── Tab 4: Periodic Department Updates ────────────────────────────── */}
        <TabsContent value="updates" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-base">Periodic Department Executive Submissions</h3>
              <p className="text-xs text-muted-foreground">
                Historical executive narrative summaries preserved across reporting periods
              </p>
            </div>
            <Button size="sm" onClick={() => setDeptUpdateModalOpen(true)}>
              <Plus className="w-4 h-4 mr-1.5" />
              Submit Period Update
            </Button>
          </div>

          <div className="space-y-3">
            {filteredDeptUpdates.map((upd) => (
              <Card key={upd.id} className="shadow-sm">
                <CardHeader className="p-4 pb-2 border-b">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">{upd.reporting_period}</Badge>
                        <CardTitle className="text-sm font-semibold">{upd.headline_summary}</CardTitle>
                      </div>
                      <CardDescription className="text-xs mt-1">
                        {upd.department} • Submitted by {upd.submitted_by_name || "Director"}
                      </CardDescription>
                    </div>
                    <Badge variant="outline">{upd.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3 text-xs">
                  {upd.accomplishments_narrative && (
                    <div>
                      <span className="font-semibold text-muted-foreground block mb-0.5">
                        Accomplishments & Delivery:
                      </span>
                      <p className="text-foreground whitespace-pre-line">{upd.accomplishments_narrative}</p>
                    </div>
                  )}

                  {upd.risks_issues && (
                    <div className="bg-amber-50 dark:bg-amber-950/20 p-2.5 rounded border border-amber-200">
                      <span className="font-semibold text-amber-800 dark:text-amber-300 block mb-0.5">
                        Emerging Risks & Bottlenecks:
                      </span>
                      <p className="text-amber-900 dark:text-amber-200">{upd.risks_issues}</p>
                    </div>
                  )}

                  {upd.support_decision_requested && (
                    <div className="bg-primary/5 p-2.5 rounded border border-primary/10">
                      <span className="font-semibold text-primary block mb-0.5">
                        Support or Executive Decision Requested:
                      </span>
                      <p className="text-foreground">{upd.support_decision_requested}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ── Tab 5: Service Delivery ───────────────────────────────────────── */}
        <TabsContent value="service" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-sm font-semibold">Child & Family Protection</CardTitle>
                <CardDescription className="text-xs">Growing Up Well casework</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-2">
                <div className="flex justify-between text-xs py-1 border-b">
                  <span className="text-muted-foreground">Active Protection Cases</span>
                  <span className="font-semibold">{renderMetricValue(service.protection_active_cases)}</span>
                </div>
                <div className="flex justify-between text-xs py-1 border-b">
                  <span className="text-muted-foreground">Children in Out-of-Home Placement</span>
                  <span className="font-semibold">{renderMetricValue(service.children_in_placement)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-sm font-semibold">Post-Majority & Prevention</CardTitle>
                <CardDescription className="text-xs">Young adults & family wellness</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-2">
                <div className="flex justify-between text-xs py-1 border-b">
                  <span className="text-muted-foreground">Post-Majority Young Adults</span>
                  <span className="font-semibold">{renderMetricValue(service.post_majority_clients)}</span>
                </div>
                <div className="flex justify-between text-xs py-1 border-b">
                  <span className="text-muted-foreground">Prevention Families Supported</span>
                  <span className="font-semibold">{renderMetricValue(service.prevention_families_supported)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-sm font-semibold">Resource Unit Capacity</CardTitle>
                <CardDescription className="text-xs">Homes, recruitment & beds</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-2">
                <div className="flex justify-between text-xs py-1 border-b">
                  <span className="text-muted-foreground">Active Resource Homes</span>
                  <span className="font-semibold">{renderMetricValue(service.active_resource_homes)}</span>
                </div>
                <div className="flex justify-between text-xs py-1 border-b">
                  <span className="text-muted-foreground">Available Beds</span>
                  <span className="font-semibold text-emerald-600">{renderMetricValue(service.available_beds)}</span>
                </div>
                <div className="flex justify-between text-xs py-1 border-b">
                  <span className="text-muted-foreground">Recruitment Pipeline</span>
                  <span className="font-semibold">{renderMetricValue(service.resource_recruitment_pipeline)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── Tab 6: Workforce & HR ─────────────────────────────────────────── */}
        <TabsContent value="workforce" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-sm font-semibold">Workforce Indicators</CardTitle>
                <CardDescription className="text-xs">Active personnel and compliance</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-2">
                <div className="flex justify-between text-xs py-1.5 border-b">
                  <span className="text-muted-foreground">Total Active Staff</span>
                  <span className="font-semibold">{renderMetricValue(workforce.total_active_staff)}</span>
                </div>
                <div className="flex justify-between text-xs py-1.5 border-b">
                  <span className="text-muted-foreground">Permanent Staff</span>
                  <span>{renderMetricValue(workforce.permanent_staff)}</span>
                </div>
                <div className="flex justify-between text-xs py-1.5 border-b">
                  <span className="text-muted-foreground">Term Staff</span>
                  <span>{renderMetricValue(workforce.term_staff)}</span>
                </div>
                <div className="flex justify-between text-xs py-1.5 border-b">
                  <span className="text-muted-foreground">Employees on Leave</span>
                  <span className="font-semibold">{renderMetricValue(workforce.employees_on_leave)}</span>
                </div>
                <div className="flex justify-between text-xs py-1.5 border-b">
                  <span className="text-muted-foreground">Recent Hires in Period</span>
                  <span className="font-semibold text-emerald-600">{renderMetricValue(workforce.recent_hires)}</span>
                </div>
                <div className="flex justify-between text-xs py-1.5 border-b">
                  <span className="text-muted-foreground">Recent Resignations</span>
                  <span>{renderMetricValue(workforce.recent_resignations)}</span>
                </div>
                <div className="flex justify-between text-xs py-1.5 border-b">
                  <span className="text-muted-foreground">Total Departures</span>
                  <span className="font-semibold">{renderMetricValue(workforce.total_departures)}</span>
                </div>
                <div className="flex justify-between text-xs py-1.5">
                  <span className="text-muted-foreground">Expiring Certifications</span>
                  <span className="font-semibold text-amber-600">{renderMetricValue(workforce.certification_warnings)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-sm font-semibold">Staffing by Department</CardTitle>
                <CardDescription className="text-xs">Live personnel distribution</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-2 max-h-[350px] overflow-y-auto">
                {Object.entries(workforce.staff_by_department || {}).length === 0 ? (
                  <p className="text-xs text-muted-foreground py-4 text-center">
                    No active employees registered yet.
                  </p>
                ) : (
                  Object.entries(workforce.staff_by_department).map(([dept, count]) => (
                    <div key={dept} className="flex justify-between text-xs py-1 border-b">
                      <span>{dept}</span>
                      <span className="font-semibold">{count}</span>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── Tab 7: Finance & Funding ──────────────────────────────────────── */}
        <TabsContent value="finance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-4 space-y-1">
              <span className="text-xs text-muted-foreground">Total Allocated Funding</span>
              <div className="text-2xl font-bold text-foreground">
                ${parseFloat(finance.total_allocated || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <p className="text-[11px] text-muted-foreground">Fiscal budget allocations</p>
            </Card>

            <Card className="p-4 space-y-1">
              <span className="text-xs text-muted-foreground">Total Expenditures</span>
              <div className="text-2xl font-bold text-primary">
                ${parseFloat(finance.total_spent || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <p className="text-[11px] text-muted-foreground">Disbursed to date</p>
            </Card>

            <Card className="p-4 space-y-1">
              <span className="text-xs text-muted-foreground">Remaining Budget</span>
              <div className="text-2xl font-bold text-emerald-600">
                ${parseFloat(finance.total_remaining || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <p className="text-[11px] text-muted-foreground">Uncommitted capital</p>
            </Card>
          </div>

          <Card>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-sm font-semibold">Spending by Major Program / Budget Line</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-1">
              <div className="space-y-2">
                {(finance.spending_by_program || []).length === 0 ? (
                  <p className="text-xs text-muted-foreground py-4 text-center">
                    No active budget lines configured.
                  </p>
                ) : (
                  finance.spending_by_program.map((bl) => (
                    <div key={bl.code} className="flex items-center justify-between text-xs py-1.5 border-b">
                      <div>
                        <span className="font-semibold">{bl.name}</span>
                        <span className="text-muted-foreground ml-2">({bl.code})</span>
                      </div>
                      <div className="text-right">
                        <span className="font-semibold text-primary">
                          ${parseFloat(bl.spent_amount).toLocaleString()}
                        </span>
                        <span className="text-muted-foreground ml-1">
                          / ${parseFloat(bl.allocated_amount).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Tab 8: Compliance & Risk Exceptions ────────────────────────────── */}
        <TabsContent value="compliance" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-base">Executive Risk & Compliance Register</h3>
              <p className="text-xs text-muted-foreground">
                Critical exceptions requiring CEO oversight and mitigation
              </p>
            </div>
            <Badge variant="outline" className="text-xs">
              {compliance.critical_exceptions || 0} Critical • {compliance.high_exceptions || 0} High
            </Badge>
          </div>

          <div className="space-y-2">
            {(compliance.items || []).length === 0 ? (
              <Card className="p-6 text-center text-xs text-muted-foreground">
                No active critical exceptions or compliance breaches detected.
              </Card>
            ) : (
              compliance.items.map((item, idx) => (
                <Card key={idx} className="p-3 shadow-sm border-l-4 border-l-rose-500">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant="destructive" className="text-[10px] uppercase">
                          {item.severity}
                        </Badge>
                        <span className="text-xs font-semibold">{item.title}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">{item.details}</p>
                    </div>
                    <span className="text-[11px] text-muted-foreground whitespace-nowrap">
                      {item.department || item.category}
                    </span>
                  </div>
                </Card>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* ── MODALS ──────────────────────────────────────────────────────────── */}

      {/* Modal 1: New Initiative */}
      <Dialog open={initiativeModalOpen} onOpenChange={setInitiativeModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Strategic Initiative</DialogTitle>
            <DialogDescription>
              Record an executive deliverable with canonical status tracking.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateInitiative} className="space-y-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">Initiative Title *</label>
              <Input
                required
                value={initForm.title}
                onChange={(e) => setInitForm({ ...initForm, title: e.target.value })}
                placeholder="e.g. C-92 Successor Agreement Negotiation"
              />
            </div>
            <div>
              <label className="font-semibold block mb-1">Operational Department</label>
              <select
                className="w-full border rounded px-2.5 py-1.5 bg-background text-xs"
                value={initForm.department}
                onChange={(e) => setInitForm({ ...initForm, department: e.target.value })}
              >
                {DEPARTMENTS.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="font-semibold block mb-1">Status</label>
                <select
                  className="w-full border rounded px-2.5 py-1.5 bg-background text-xs"
                  value={initForm.status}
                  onChange={(e) => setInitForm({ ...initForm, status: e.target.value })}
                >
                  <option value="ON_TRACK">ON_TRACK</option>
                  <option value="AT_RISK">AT_RISK</option>
                  <option value="DELAYED">DELAYED</option>
                  <option value="ON_HOLD">ON_HOLD</option>
                  <option value="COMPLETED">COMPLETED</option>
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Priority</label>
                <select
                  className="w-full border rounded px-2.5 py-1.5 bg-background text-xs"
                  value={initForm.priority}
                  onChange={(e) => setInitForm({ ...initForm, priority: e.target.value })}
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="font-semibold block mb-1">Target Date</label>
                <Input
                  type="date"
                  value={initForm.target_date}
                  onChange={(e) => setInitForm({ ...initForm, target_date: e.target.value })}
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Progress % (0-100)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={initForm.progress_percentage}
                  onChange={(e) => setInitForm({ ...initForm, progress_percentage: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="font-semibold block mb-1">Description & Scope</label>
              <Textarea
                rows={2}
                value={initForm.description}
                onChange={(e) => setInitForm({ ...initForm, description: e.target.value })}
                placeholder="Background and scope of this strategic objective..."
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setInitiativeModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Initiative</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal 2: New Board Action */}
      <Dialog open={boardActionModalOpen} onOpenChange={setBoardActionModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Request Board Action or Decision</DialogTitle>
            <DialogDescription>
              Governance-level submission for Board attention. Do not include private case narratives.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateBoardAction} className="space-y-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">Request Title *</label>
              <Input
                required
                value={baForm.title}
                onChange={(e) => setBaForm({ ...baForm, title: e.target.value })}
                placeholder="e.g. Approval for Extension Agreement Signing"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="font-semibold block mb-1">Originating Department</label>
                <select
                  className="w-full border rounded px-2.5 py-1.5 bg-background text-xs"
                  value={baForm.originating_department}
                  onChange={(e) => setBaForm({ ...baForm, originating_department: e.target.value })}
                >
                  {DEPARTMENTS.map((dept) => (
                    <option key={dept} value={dept}>
                      {dept}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Required-By Date</label>
                <Input
                  type="date"
                  value={baForm.required_by_date}
                  onChange={(e) => setBaForm({ ...baForm, required_by_date: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="font-semibold block mb-1">Background / Summary *</label>
              <Textarea
                required
                rows={2}
                value={baForm.background_summary}
                onChange={(e) => setBaForm({ ...baForm, background_summary: e.target.value })}
                placeholder="Governance context and rationale..."
              />
            </div>
            <div>
              <label className="font-semibold block mb-1">Requested Decision / Action *</label>
              <Textarea
                required
                rows={2}
                value={baForm.requested_action}
                onChange={(e) => setBaForm({ ...baForm, requested_action: e.target.value })}
                placeholder="Specific motion or approval requested from the Board..."
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setBoardActionModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Submit Request</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal 3: Record Board Decision */}
      <Dialog open={decisionModalOpen} onOpenChange={setDecisionModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Record Board Decision</DialogTitle>
            <DialogDescription>
              Reference: {selectedBoardAction?.reference_number} — {selectedBoardAction?.title}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRecordDecision} className="space-y-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">Board Decision Status</label>
              <select
                className="w-full border rounded px-2.5 py-1.5 bg-background text-xs"
                value={decisionForm.status}
                onChange={(e) => setDecisionForm({ ...decisionForm, status: e.target.value })}
              >
                <option value="APPROVED">APPROVED</option>
                <option value="DECLINED">DECLINED</option>
                <option value="DEFERRED">DEFERRED</option>
                <option value="RESOLVED">RESOLVED</option>
                <option value="WITHDRAWN">WITHDRAWN</option>
              </select>
            </div>
            <div>
              <label className="font-semibold block mb-1">Formal Decision Summary *</label>
              <Textarea
                required
                rows={3}
                value={decisionForm.decision}
                onChange={(e) => setDecisionForm({ ...decisionForm, decision: e.target.value })}
                placeholder="Record the Board's resolution or directives..."
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDecisionModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Decision</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal 4: Submit Department Executive Update */}
      <Dialog open={deptUpdateModalOpen} onOpenChange={setDeptUpdateModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Submit Department Executive Update</DialogTitle>
            <DialogDescription>
              Periodic narrative report for period {reportingPeriod}. Preserved across historical records.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitDeptUpdate} className="space-y-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">Department</label>
              <select
                className="w-full border rounded px-2.5 py-1.5 bg-background text-xs"
                value={deptUpdateForm.department}
                onChange={(e) => setDeptUpdateForm({ ...deptUpdateForm, department: e.target.value })}
              >
                {DEPARTMENTS.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-semibold block mb-1">Executive Headline / Summary *</label>
              <Input
                required
                value={deptUpdateForm.headline_summary}
                onChange={(e) => setDeptUpdateForm({ ...deptUpdateForm, headline_summary: e.target.value })}
                placeholder="e.g. Completed initial customary care caregiver circle"
              />
            </div>
            <div>
              <label className="font-semibold block mb-1">Accomplishments & Delivery</label>
              <Textarea
                rows={3}
                value={deptUpdateForm.accomplishments_narrative}
                onChange={(e) =>
                  setDeptUpdateForm({ ...deptUpdateForm, accomplishments_narrative: e.target.value })
                }
                placeholder="Key accomplishments achieved during this reporting period..."
              />
            </div>
            <div>
              <label className="font-semibold block mb-1">Risks & Bottlenecks</label>
              <Textarea
                rows={2}
                value={deptUpdateForm.risks_issues}
                onChange={(e) => setDeptUpdateForm({ ...deptUpdateForm, risks_issues: e.target.value })}
                placeholder="Emerging challenges requiring executive awareness..."
              />
            </div>
            <div>
              <label className="font-semibold block mb-1">Executive Support / Decision Requested</label>
              <Textarea
                rows={2}
                value={deptUpdateForm.support_decision_requested}
                onChange={(e) =>
                  setDeptUpdateForm({ ...deptUpdateForm, support_decision_requested: e.target.value })
                }
                placeholder="Any action or support needed from the CEO..."
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDeptUpdateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Submit Update</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

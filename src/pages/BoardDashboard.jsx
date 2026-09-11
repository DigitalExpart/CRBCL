import React, { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/api";
import {
  Landmark,
  Shield,
  Clock,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  DollarSign,
  Users,
  Building,
  FileText,
  ChevronRight,
  Filter,
  RefreshCw,
  Eye,
  CheckSquare,
  Lock,
  ArrowUpRight,
  Sparkles,
  HelpCircle,
  History,
  Send,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "@/components/ui/use-toast";

export default function BoardDashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") || "overview";
  const [activeTab, setActiveTab] = useState(initialTab);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Board Data States
  const [summary, setSummary] = useState(null);
  const [actions, setActions] = useState([]);
  const [initiatives, setInitiatives] = useState([]);
  const [departmentUpdates, setDepartmentUpdates] = useState([]);
  const [workforce, setWorkforce] = useState(null);
  const [finance, setFinance] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [risk, setRisk] = useState(null);
  const [criticalDates, setCriticalDates] = useState([]);

  // User capabilities
  const [currentUser, setCurrentUser] = useState(null);
  const [isLeadership, setIsLeadership] = useState(false);

  // Modals & Inspection States
  const [selectedActionHistory, setSelectedActionHistory] = useState(null);
  const [actionToDecide, setActionToDecide] = useState(null);
  const [decisionText, setDecisionText] = useState("");
  const [decisionStatus, setDecisionStatus] = useState("RESOLVED");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);

  // Filter States
  const [actionStatusFilter, setActionStatusFilter] = useState("ALL");
  const [initiativeFilter, setInitiativeFilter] = useState("ALL");
  const [reportingPeriodFilter, setReportingPeriodFilter] = useState("");

  // Sync tab with URL search parameter
  useEffect(() => {
    const tabFromUrl = searchParams.get("tab");
    if (tabFromUrl && tabFromUrl !== activeTab) {
      setActiveTab(tabFromUrl);
    }
  }, [searchParams]);

  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    setSearchParams({ tab: newTab });
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Determine user capabilities
      const user = await api.auth.me().catch(() => null);
      setCurrentUser(user);
      const roles = (Array.isArray(user?.roles) ? user.roles : [user?.role || ""])
        .map((r) => (typeof r === "string" ? r : r?.key || ""))
        .map((r) => String(r).toLowerCase().trim());
      const hasLeadership = roles.includes("ceo") || roles.includes("executive_director");
      setIsLeadership(hasLeadership);

      // Fetch all board-safe endpoints in parallel
      const [
        sumRes,
        actRes,
        initRes,
        updatesRes,
        wfRes,
        finRes,
        perfRes,
        riskRes,
        datesRes,
      ] = await Promise.all([
        api.boardDashboard.getSummary(reportingPeriodFilter || undefined),
        api.boardDashboard.getActions(),
        api.boardDashboard.getInitiatives(),
        api.boardDashboard.getDepartmentUpdates(reportingPeriodFilter || undefined),
        api.boardDashboard.getWorkforce(),
        api.boardDashboard.getFinance(),
        api.boardDashboard.getPerformance(),
        api.boardDashboard.getRiskCompliance(),
        api.boardDashboard.getCriticalDates(),
      ]);

      setSummary(sumRes);
      setActions(actRes || []);
      setInitiatives(initRes || []);
      setDepartmentUpdates(updatesRes || []);
      setWorkforce(wfRes);
      setFinance(finRes);
      setPerformance(perfRes);
      setRisk(riskRes);
      setCriticalDates(datesRes || []);
    } catch (err) {
      console.error("Failed to load Board Dashboard:", err);
      setError(err.message || "Failed to load governance dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [reportingPeriodFilter]);

  // Decision Recording Handler
  const handleRecordDecision = async (e) => {
    e.preventDefault();
    if (!actionToDecide || !decisionText.trim()) return;

    setSubmittingDecision(true);
    try {
      await api.boardDashboard.recordDecision(actionToDecide.id, {
        decision: decisionText.trim(),
        status: decisionStatus,
        resolution_notes: resolutionNotes.trim() || null,
      });

      toast({
        title: "Board Decision Recorded",
        description: `Formal decision saved for ${actionToDecide.reference_number}.`,
      });

      setActionToDecide(null);
      setDecisionText("");
      setResolutionNotes("");
      loadData();
    } catch (err) {
      toast({
        title: "Failed to record decision",
        description: err.message || "An error occurred.",
        variant: "destructive",
      });
    } finally {
      setSubmittingDecision(false);
    }
  };

  // Filtered Actions
  const filteredActions = useMemo(() => {
    if (actionStatusFilter === "ALL") return actions;
    if (actionStatusFilter === "PENDING") {
      return actions.filter((a) =>
        ["SUBMITTED", "UNDER_REVIEW", "DECISION_REQUIRED"].includes(a.status)
      );
    }
    return actions.filter((a) => a.status === actionStatusFilter);
  }, [actions, actionStatusFilter]);

  // Filtered Initiatives
  const filteredInitiatives = useMemo(() => {
    if (initiativeFilter === "ALL") return initiatives;
    return initiatives.filter((i) => i.status === initiativeFilter);
  }, [initiatives, initiativeFilter]);

  const formatCurrency = (amount) => {
    if (amount === undefined || amount === null) return "$0.00";
    return new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD" }).format(amount);
  };

  if (loading && !summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground font-medium">Loading Board Governance Command Centre...</p>
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center space-y-4">
        <div className="p-4 bg-destructive/10 text-destructive rounded-xl inline-block">
          <AlertTriangle className="h-8 w-8 mx-auto" />
        </div>
        <h2 className="text-xl font-bold text-foreground">Access Restricted or Error</h2>
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={loadData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" /> Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl border border-indigo-500/20 text-white shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-indigo-500/20 text-indigo-300 border-indigo-400/30 px-2.5 py-0.5 text-xs font-semibold tracking-wider">
              GOVERNANCE PORTAL • STRICT OVERSIGHT
            </Badge>
            <span className="text-xs text-slate-400">Chief Red Bear Children's Lodge</span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold tracking-tight flex items-center gap-3 text-white">
            <Landmark className="h-7 w-7 text-indigo-400" />
            Board of Governors Command Centre
          </h1>
          <p className="text-sm text-slate-300 max-w-3xl">
            Strategic organizational performance, approved finances, critical compliance milestones, and formal matters requiring Board attention.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={loadData}
            variant="outline"
            size="sm"
            className="bg-white/10 hover:bg-white/20 text-white border-white/20"
          >
            <RefreshCw className={`h-4 w-4 mr-1.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
        </div>
      </div>

      {/* Governance Safety Alert */}
      <div className="flex items-center justify-between gap-3 p-3.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-indigo-400 shrink-0" />
          <span>
            <strong>Governance Information Boundary:</strong> Operational casework details, confidential child identities, and staff personnel records are strictly excluded from this governance portal.
          </span>
        </div>
        <span className="font-semibold text-indigo-400">Strictly Redacted</span>
      </div>

      {/* Tabs Navigation */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
        <TabsList className="bg-card border border-border p-1 w-full sm:w-auto overflow-x-auto flex justify-start">
          <TabsTrigger value="overview" className="gap-2 text-xs sm:text-sm">
            <Landmark className="h-4 w-4" /> Board Overview
          </TabsTrigger>
          <TabsTrigger value="actions" className="gap-2 text-xs sm:text-sm">
            <CheckSquare className="h-4 w-4" /> Actions & Decisions
            {summary?.board_actions_pending > 0 && (
              <Badge variant="destructive" className="ml-1 px-1.5 py-0 text-[10px]">
                {summary.board_actions_pending}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="initiatives" className="gap-2 text-xs sm:text-sm">
            <TrendingUp className="h-4 w-4" /> Strategic Initiatives
          </TabsTrigger>
          <TabsTrigger value="performance" className="gap-2 text-xs sm:text-sm">
            <Users className="h-4 w-4" /> Performance & Risk
          </TabsTrigger>
          <TabsTrigger value="reports" className="gap-2 text-xs sm:text-sm">
            <FileText className="h-4 w-4" /> Department Reports
          </TabsTrigger>
        </TabsList>

        {/* ── TAB 1: BOARD OVERVIEW ──────────────────────────────────── */}
        <TabsContent value="overview" className="space-y-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="border-border shadow-sm">
              <CardContent className="p-4 space-y-1">
                <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold">
                  <span>ACTIVE CARE PLACEMENTS</span>
                  <Users className="h-4 w-4 text-primary" />
                </div>
                <div className="text-2xl font-bold text-foreground">
                  {summary?.active_care_placements?.value ?? 0}
                </div>
                <p className="text-[11px] text-muted-foreground">Distinct children in active care</p>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="p-4 space-y-1">
                <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold">
                  <span>APPROVED BED CAPACITY</span>
                  <Building className="h-4 w-4 text-emerald-500" />
                </div>
                <div className="text-2xl font-bold text-foreground">
                  {summary?.approved_bed_capacity?.value ?? 0}
                </div>
                <p className="text-[11px] text-muted-foreground">Licensed resource home beds</p>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="p-4 space-y-1">
                <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold">
                  <span>APPROVED ANNUAL BUDGET</span>
                  <DollarSign className="h-4 w-4 text-amber-500" />
                </div>
                <div className="text-2xl font-bold text-foreground">
                  {formatCurrency(summary?.approved_budget_total)}
                </div>
                <p className="text-[11px] text-muted-foreground">
                  {formatCurrency(summary?.approved_budget_spent)} spent ({summary?.approved_budget_total ? Math.round((Number(summary.approved_budget_spent) / Number(summary.approved_budget_total)) * 100) : 0}%)
                </p>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="p-4 space-y-1">
                <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold">
                  <span>BOARD ACTIONS PENDING</span>
                  <CheckSquare className="h-4 w-4 text-indigo-500" />
                </div>
                <div className="text-2xl font-bold text-foreground flex items-center gap-2">
                  <span>{summary?.board_actions_pending ?? 0}</span>
                  {summary?.board_actions_pending > 0 && (
                    <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/20 text-[10px]">
                      Action Required
                    </Badge>
                  )}
                </div>
                <p className="text-[11px] text-muted-foreground">
                  {summary?.board_actions_total ?? 0} total governance items
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Strategic Initiatives & Compliance Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2 border-border shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-indigo-400" />
                    Strategic Initiatives Status Overview
                  </CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => handleTabChange("initiatives")}>
                    View All ({summary?.initiatives_total ?? 0}) <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
                <CardDescription className="text-xs">
                  High-level milestones approved for Board of Governors visibility.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-4 gap-2 text-center">
                  <div className="p-3 bg-muted/40 rounded-xl">
                    <span className="text-xs text-muted-foreground">Total Published</span>
                    <p className="text-xl font-bold">{summary?.initiatives_total ?? 0}</p>
                  </div>
                  <div className="p-3 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-xl">
                    <span className="text-xs">On Track</span>
                    <p className="text-xl font-bold">{summary?.initiatives_on_track ?? 0}</p>
                  </div>
                  <div className="p-3 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-xl">
                    <span className="text-xs">At Risk</span>
                    <p className="text-xl font-bold">{summary?.initiatives_at_risk ?? 0}</p>
                  </div>
                  <div className="p-3 bg-rose-500/10 text-rose-600 dark:text-rose-400 rounded-xl">
                    <span className="text-xs">Delayed</span>
                    <p className="text-xl font-bold">{summary?.initiatives_delayed ?? 0}</p>
                  </div>
                </div>

                {initiatives.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-6">
                    No strategic initiatives have been published to the Board yet.
                  </p>
                ) : (
                  <div className="space-y-2.5">
                    {initiatives.slice(0, 3).map((init) => (
                      <div
                        key={init.id}
                        className="p-3 border border-border rounded-xl flex items-center justify-between gap-4 hover:bg-muted/20 transition-colors"
                      >
                        <div className="space-y-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm truncate">{init.title}</span>
                            <Badge variant="outline" className="text-[10px] uppercase">
                              {init.department || "Organization"}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {init.board_summary || "Strategic governance milestone"}
                          </p>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <div className="text-right">
                            <span className="text-xs font-bold">{init.progress_percentage ?? 0}%</span>
                            <Progress value={init.progress_percentage ?? 0} className="w-16 h-1.5 mt-1" />
                          </div>
                          <Badge
                            variant={
                              init.status === "ON_TRACK"
                                ? "outline"
                                : init.status === "AT_RISK"
                                ? "secondary"
                                : "destructive"
                            }
                            className="text-[10px]"
                          >
                            {init.status.replace("_", " ")}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Critical Governance Dates */}
            <Card className="border-border shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-amber-500" />
                  Critical Governance Dates
                </CardTitle>
                <CardDescription className="text-xs">
                  Milestones and statutory reporting deadlines.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {criticalDates.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-8">
                    No upcoming governance deadlines recorded.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {criticalDates.slice(0, 5).map((dateItem) => (
                      <div
                        key={dateItem.id}
                        className="flex items-start justify-between gap-2 pb-2.5 border-b border-border/50 last:border-0 last:pb-0"
                      >
                        <div className="space-y-0.5">
                          <p className="text-xs font-semibold leading-tight">{dateItem.title}</p>
                          <span className="text-[11px] text-muted-foreground">{dateItem.date}</span>
                        </div>
                        <Badge
                          variant={
                            dateItem.urgency === "OVERDUE"
                              ? "destructive"
                              : dateItem.urgency === "URGENT"
                              ? "secondary"
                              : "outline"
                          }
                          className="text-[10px] shrink-0"
                        >
                          {dateItem.urgency}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── TAB 2: ACTIONS & DECISIONS ──────────────────────────────── */}
        <TabsContent value="actions" className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-card p-4 rounded-xl border border-border">
            <div>
              <h2 className="text-base font-semibold">Governance Actions & Board Decisions</h2>
              <p className="text-xs text-muted-foreground">
                Formal matters submitted by executive leadership for Board consideration and resolution.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <select
                value={actionStatusFilter}
                onChange={(e) => setActionStatusFilter(e.target.value)}
                className="bg-background border border-border rounded-lg text-xs px-3 py-1.5 font-medium"
              >
                <option value="ALL">All Statuses ({actions.length})</option>
                <option value="PENDING">Pending Attention</option>
                <option value="DECISION_REQUIRED">Decision Required</option>
                <option value="RESOLVED">Resolved / Decided</option>
                <option value="APPROVED">Approved</option>
                <option value="DECLINED">Declined</option>
              </select>
            </div>
          </div>

          {filteredActions.length === 0 ? (
            <Card className="border-border shadow-sm p-12 text-center space-y-2">
              <CheckSquare className="h-10 w-10 text-muted-foreground mx-auto" />
              <h3 className="font-semibold text-base">No Board Actions Found</h3>
              <p className="text-xs text-muted-foreground">
                There are no governance actions matching the selected filter.
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredActions.map((action) => (
                <Card key={action.id} className="border-border shadow-sm">
                  <CardHeader className="pb-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-primary">
                            {action.reference_number}
                          </span>
                          <Badge variant="outline" className="text-[10px]">
                            {action.originating_department}
                          </Badge>
                          <Badge
                            variant={
                              action.priority === "CRITICAL"
                                ? "destructive"
                                : action.priority === "HIGH"
                                ? "secondary"
                                : "outline"
                            }
                            className="text-[10px]"
                          >
                            {action.priority}
                          </Badge>
                        </div>
                        <CardTitle className="text-base font-bold">{action.title}</CardTitle>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            ["APPROVED", "RESOLVED"].includes(action.status)
                              ? "outline"
                              : ["DECLINED"].includes(action.status)
                              ? "destructive"
                              : "secondary"
                          }
                          className="text-xs font-semibold"
                        >
                          {action.status.replace("_", " ")}
                        </Badge>
                        {action.history && action.history.length > 0 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedActionHistory(action)}
                            className="h-8 text-xs gap-1"
                          >
                            <History className="h-3.5 w-3.5" /> History ({action.history.length})
                          </Button>
                        )}
                        {isLeadership && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setActionToDecide(action);
                              setDecisionText(action.decision || "");
                              setDecisionStatus(action.status === "SUBMITTED" ? "RESOLVED" : action.status);
                            }}
                            className="h-8 text-xs gap-1"
                          >
                            <CheckSquare className="h-3.5 w-3.5" /> Record Decision
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-0">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="p-3 bg-muted/30 rounded-xl space-y-1 border border-border/50">
                        <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider">
                          Background & Governance Context
                        </span>
                        <p className="text-foreground leading-relaxed">{action.background_summary}</p>
                      </div>

                      <div className="p-3 bg-primary/5 rounded-xl space-y-1 border border-primary/20">
                        <span className="font-semibold text-primary uppercase text-[10px] tracking-wider">
                          Requested Board Action
                        </span>
                        <p className="text-foreground leading-relaxed font-medium">{action.requested_action}</p>
                      </div>
                    </div>

                    {action.decision && (
                      <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl space-y-1 text-xs">
                        <div className="flex items-center justify-between font-semibold text-emerald-600 dark:text-emerald-400">
                          <span className="flex items-center gap-1.5">
                            <CheckCircle2 className="h-4 w-4" /> Board Decision & Resolution
                          </span>
                          {action.decision_date && (
                            <span className="text-[11px] font-normal text-muted-foreground">
                              {new Date(action.decision_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        <p className="text-foreground leading-relaxed font-medium">{action.decision}</p>
                        {action.decided_by_name && (
                          <p className="text-[11px] text-muted-foreground">
                            Recorded by: {action.decided_by_name}
                          </p>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ── TAB 3: STRATEGIC INITIATIVES ────────────────────────────── */}
        <TabsContent value="initiatives" className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-card p-4 rounded-xl border border-border">
            <div>
              <h2 className="text-base font-semibold">Strategic Organizational Deliverables</h2>
              <p className="text-xs text-muted-foreground">
                High-level strategic initiatives approved for Board oversight.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <select
                value={initiativeFilter}
                onChange={(e) => setInitiativeFilter(e.target.value)}
                className="bg-background border border-border rounded-lg text-xs px-3 py-1.5 font-medium"
              >
                <option value="ALL">All Statuses ({initiatives.length})</option>
                <option value="ON_TRACK">On Track</option>
                <option value="AT_RISK">At Risk</option>
                <option value="DELAYED">Delayed</option>
                <option value="COMPLETED">Completed</option>
              </select>
            </div>
          </div>

          {filteredInitiatives.length === 0 ? (
            <Card className="border-border shadow-sm p-12 text-center space-y-2">
              <TrendingUp className="h-10 w-10 text-muted-foreground mx-auto" />
              <h3 className="font-semibold text-base">No Initiatives Published</h3>
              <p className="text-xs text-muted-foreground">
                There are no strategic initiatives currently published for Board review under this filter.
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredInitiatives.map((init) => (
                <Card key={init.id} className="border-border shadow-sm flex flex-col justify-between">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <Badge variant="outline" className="text-[10px] uppercase font-semibold">
                          {init.department || "Organization-Wide"}
                        </Badge>
                        <CardTitle className="text-base font-bold leading-snug">{init.title}</CardTitle>
                      </div>
                      <Badge
                        variant={
                          init.status === "ON_TRACK"
                            ? "outline"
                            : init.status === "AT_RISK"
                            ? "secondary"
                            : init.status === "COMPLETED"
                            ? "default"
                            : "destructive"
                        }
                        className="text-[10px] shrink-0"
                      >
                        {init.status.replace("_", " ")}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-xs text-foreground leading-relaxed bg-muted/30 p-3 rounded-xl border border-border/40">
                      {init.board_summary || "Strategic organizational priority."}
                    </p>

                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-muted-foreground">Progress Completion</span>
                        <span>{init.progress_percentage ?? 0}%</span>
                      </div>
                      <Progress value={init.progress_percentage ?? 0} className="h-2" />
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-2 border-t border-border/50">
                      <span>Priority: <strong className="text-foreground">{init.priority}</strong></span>
                      <span>Target: <strong className="text-foreground">{init.target_date || "Open"}</strong></span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ── TAB 4: PERFORMANCE & RISK ──────────────────────────────── */}
        <TabsContent value="performance" className="space-y-6">
          {/* Service Delivery Grid */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              Organizational Service Delivery
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="border-border shadow-sm">
                <CardContent className="p-4 space-y-1">
                  <span className="text-xs text-muted-foreground font-semibold">ACTIVE CASES</span>
                  <div className="text-2xl font-bold">{performance?.active_cases_total?.value ?? 0}</div>
                  <p className="text-[11px] text-muted-foreground">Child protection & prevention files</p>
                </CardContent>
              </Card>

              <Card className="border-border shadow-sm">
                <CardContent className="p-4 space-y-1">
                  <span className="text-xs text-muted-foreground font-semibold">FAMILIES SERVED</span>
                  <div className="text-2xl font-bold">{performance?.families_served?.value ?? 0}</div>
                  <p className="text-[11px] text-muted-foreground">Distinct active client families</p>
                </CardContent>
              </Card>

              <Card className="border-border shadow-sm">
                <CardContent className="p-4 space-y-1">
                  <span className="text-xs text-muted-foreground font-semibold">RESOURCE HOMES</span>
                  <div className="text-2xl font-bold">{performance?.active_resource_homes?.value ?? 0}</div>
                  <p className="text-[11px] text-muted-foreground">
                    {performance?.available_resource_beds?.value ?? 0} available beds
                  </p>
                </CardContent>
              </Card>

              <Card className="border-border shadow-sm">
                <CardContent className="p-4 space-y-1">
                  <span className="text-xs text-muted-foreground font-semibold">CULTURAL PROGRAMS</span>
                  <div className="text-2xl font-bold">{performance?.active_cultural_programs?.value ?? 0}</div>
                  <p className="text-[11px] text-muted-foreground">
                    {performance?.cultural_program_enrollment?.value ?? 0} enrolled participants
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Workforce & Risk Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Workforce Overview */}
            <Card className="border-border shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Users className="h-4 w-4 text-primary" />
                  Aggregate Workforce Distribution
                </CardTitle>
                <CardDescription className="text-xs">
                  Active staff headcount by organizational department.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2.5 bg-muted/40 rounded-xl">
                    <span className="text-[11px] text-muted-foreground">Active Staff</span>
                    <p className="text-lg font-bold">{workforce?.total_active_staff?.value ?? 0}</p>
                  </div>
                  <div className="p-2.5 bg-muted/40 rounded-xl">
                    <span className="text-[11px] text-muted-foreground">On Leave</span>
                    <p className="text-lg font-bold">{workforce?.staff_on_leave?.value ?? 0}</p>
                  </div>
                  <div className="p-2.5 bg-muted/40 rounded-xl">
                    <span className="text-[11px] text-muted-foreground">Recent Hires</span>
                    <p className="text-lg font-bold">{workforce?.recent_hires_in_period?.value ?? 0}</p>
                  </div>
                </div>

                <div className="space-y-2 pt-2">
                  <span className="text-xs font-semibold text-muted-foreground">Department Distribution:</span>
                  <div className="space-y-1.5 max-h-[220px] overflow-y-auto pr-1">
                    {Object.entries(workforce?.staff_by_department || {}).map(([dept, count]) => (
                      <div key={dept} className="flex items-center justify-between text-xs py-1 border-b border-border/40 last:border-0">
                        <span className="truncate max-w-[240px]">{dept}</span>
                        <Badge variant="outline" className="font-mono text-[11px]">
                          {count}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Risk & Compliance Register */}
            <Card className="border-border shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  Organizational Risk & Compliance Exceptions
                </CardTitle>
                <CardDescription className="text-xs">
                  Statutory warnings, license expiries, and delayed deliverables.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2.5 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-xl">
                    <span className="text-[11px]">Delayed Items</span>
                    <p className="text-lg font-bold">{risk?.delayed_initiatives_count ?? 0}</p>
                  </div>
                  <div className="p-2.5 bg-rose-500/10 text-rose-600 dark:text-rose-400 rounded-xl">
                    <span className="text-[11px]">Licenses Due</span>
                    <p className="text-lg font-bold">{risk?.expiring_licenses_30d_count ?? 0}</p>
                  </div>
                  <div className="p-2.5 bg-muted/40 rounded-xl">
                    <span className="text-[11px] text-muted-foreground">Total Incidents</span>
                    <p className="text-lg font-bold">{risk?.serious_incidents_total ?? 0}</p>
                  </div>
                </div>

                <div className="space-y-2 pt-2">
                  <span className="text-xs font-semibold text-muted-foreground">Active Risk Items:</span>
                  {risk?.risk_items && risk.risk_items.length > 0 ? (
                    <div className="space-y-2">
                      {risk.risk_items.map((item, idx) => (
                        <div key={idx} className="p-2.5 bg-muted/20 border border-border rounded-lg text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold truncate">{item.title}</span>
                            <Badge variant="outline" className="text-[10px]">
                              {item.severity}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                            <span>Status: {item.status}</span>
                            <span>Due: {item.due_date || "N/A"}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground text-center py-6">
                      No active compliance risk exceptions flagged.
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── TAB 5: DEPARTMENT REPORTS ──────────────────────────────── */}
        <TabsContent value="reports" className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-card p-4 rounded-xl border border-border">
            <div>
              <h2 className="text-base font-semibold">Department Executive Reports</h2>
              <p className="text-xs text-muted-foreground">
                Periodic departmental narratives, accomplishments, and strategic support requests approved for Board review.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Period:</span>
              <Input
                placeholder="Filter by period (e.g. 2026-04)"
                value={reportingPeriodFilter}
                onChange={(e) => setReportingPeriodFilter(e.target.value)}
                className="w-48 text-xs h-8"
              />
            </div>
          </div>

          {departmentUpdates.length === 0 ? (
            <Card className="border-border shadow-sm p-12 text-center space-y-2">
              <FileText className="h-10 w-10 text-muted-foreground mx-auto" />
              <h3 className="font-semibold text-base">No Department Reports Published</h3>
              <p className="text-xs text-muted-foreground">
                No department updates have been approved and published for Board visibility yet.
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {departmentUpdates.map((dept) => (
                <Card key={dept.id} className="border-border shadow-sm">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-bold">{dept.department}</CardTitle>
                      <Badge variant="outline" className="font-mono text-xs">
                        {dept.reporting_period}
                      </Badge>
                    </div>
                    <CardDescription className="text-xs font-semibold text-foreground">
                      {dept.headline_summary}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    {dept.accomplishments_narrative && (
                      <div className="p-3 bg-muted/20 rounded-xl space-y-1">
                        <span className="font-bold text-[10px] uppercase text-muted-foreground tracking-wider">
                          Key Accomplishments
                        </span>
                        <p className="text-foreground leading-relaxed">{dept.accomplishments_narrative}</p>
                      </div>
                    )}

                    {dept.risks_issues && (
                      <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl space-y-1">
                        <span className="font-bold text-[10px] uppercase text-amber-600 dark:text-amber-400 tracking-wider">
                          Strategic Risks & Challenges
                        </span>
                        <p className="text-foreground leading-relaxed">{dept.risks_issues}</p>
                      </div>
                    )}

                    {dept.support_decision_requested && (
                      <div className="p-3 bg-primary/10 border border-primary/20 rounded-xl space-y-1">
                        <span className="font-bold text-[10px] uppercase text-primary tracking-wider">
                          Support / Board Decision Requested
                        </span>
                        <p className="text-foreground leading-relaxed font-medium">{dept.support_decision_requested}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Decision Recording Modal */}
      <Dialog open={!!actionToDecide} onOpenChange={(open) => !open && setActionToDecide(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Record Formal Board Decision</DialogTitle>
            <DialogDescription>
              {actionToDecide?.reference_number} — {actionToDecide?.title}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleRecordDecision} className="space-y-4 text-xs">
            <div className="space-y-1.5">
              <Label>Resolution Status</Label>
              <select
                value={decisionStatus}
                onChange={(e) => setDecisionStatus(e.target.value)}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs"
              >
                <option value="RESOLVED">Resolved / Noted</option>
                <option value="APPROVED">Approved by Board</option>
                <option value="DECLINED">Declined by Board</option>
                <option value="DEFERRED">Deferred for Further Review</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <Label>Formal Motion / Resolution Text *</Label>
              <Textarea
                required
                rows={4}
                value={decisionText}
                onChange={(e) => setDecisionText(e.target.value)}
                placeholder="Enter formal Board motion, resolution number, and decision outcome..."
              />
            </div>

            <div className="space-y-1.5">
              <Label>Internal Governance Notes (Optional)</Label>
              <Input
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="Optional follow-up notes or action item assignments..."
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setActionToDecide(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submittingDecision || !decisionText.trim()}>
                {submittingDecision ? "Recording..." : "Save Resolution"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Decision Audit History Modal */}
      <Dialog open={!!selectedActionHistory} onOpenChange={(open) => !open && setSelectedActionHistory(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="h-5 w-5 text-primary" />
              Decision Audit Ledger
            </DialogTitle>
            <DialogDescription>
              {selectedActionHistory?.reference_number} — {selectedActionHistory?.title}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1 text-xs">
            {selectedActionHistory?.history && selectedActionHistory.history.length > 0 ? (
              selectedActionHistory.history.map((hist, idx) => (
                <div key={hist.id || idx} className="p-3 bg-muted/30 border border-border rounded-xl space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground">
                      Status changed: {hist.previous_status} → {hist.new_status}
                    </span>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      {new Date(hist.changed_at).toLocaleString()}
                    </span>
                  </div>
                  {hist.decision_notes && (
                    <div className="p-2 bg-background border border-border/50 rounded-lg">
                      <span className="font-semibold text-[10px] uppercase text-muted-foreground">
                        Decision / Motion:
                      </span>
                      <p className="text-foreground">{hist.decision_notes}</p>
                    </div>
                  )}
                  {hist.changed_by_name && (
                    <p className="text-[11px] text-muted-foreground">Actor: {hist.changed_by_name}</p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-center py-6 text-muted-foreground">No historical revisions recorded.</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

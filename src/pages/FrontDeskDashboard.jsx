import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Inbox,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Search,
  RefreshCw,
  PlusCircle,
  FileText,
  User,
  Phone,
  Mail,
  ArrowRight,
  ShieldAlert,
  HelpCircle,
  XCircle,
  Loader2,
  ExternalLink,
  ChevronRight,
  Send,
  Building2,
  CornerUpLeft,
  Copy,
  History,
  Info,
} from "lucide-react";
import { toast } from "@/components/ui/use-toast";
import { DEPARTMENTS } from "@/constants/departments";

const STATUS_TABS = [
  { key: "RECEIVED", label: "New (Received)" },
  { key: "FRONT_DESK_REVIEW", label: "Under Review" },
  { key: "ROUTED", label: "Routed" },
  { key: "RETURNED_TO_FRONT_DESK", label: "Returned" },
  { key: "ACCEPTED", label: "Accepted" },
  { key: "DUPLICATE", label: "Duplicate" },
  { key: "OUT_OF_SCOPE", label: "Out of Scope" },
  { key: "SPAM", label: "Spam / Closed" },
  { key: "ALL", label: "All Records" },
];

export default function FrontDeskDashboard() {
  const [stats, setStats] = useState({
    received_count: 0,
    front_desk_review_count: 0,
    routed_count: 0,
    department_review_count: 0,
    accepted_count: 0,
    returned_count: 0,
    duplicate_count: 0,
    out_of_scope_count: 0,
    closed_count: 0,
    spam_count: 0,
    total_count: 0,
    oldest_unreviewed_hours: null,
    department_counts: {},
  });
  const [submissions, setSubmissions] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("RECEIVED");

  // Modals state
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [routeModalOpen, setRouteModalOpen] = useState(false);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [walkInModalOpen, setWalkInModalOpen] = useState(false);
  const [duplicateModalOpen, setDuplicateModalOpen] = useState(false);
  const [duplicateCandidates, setDuplicateCandidates] = useState([]);
  const [duplicateLoading, setDuplicateLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Routing Form state
  const [destDepartment, setDestDepartment] = useState("");
  const [routeUrgency, setRouteUrgency] = useState("Medium");
  const [routeNotes, setRouteNotes] = useState("");

  // Review status form state
  const [reviewStatus, setReviewStatus] = useState("FRONT_DESK_REVIEW");
  const [reviewNotes, setReviewNotes] = useState("");

  // Manual Walk-in Form state
  const [manualSource, setManualSource] = useState("walk_in");
  const [manualName, setManualName] = useState("");
  const [manualPhone, setManualPhone] = useState("");
  const [manualEmail, setManualEmail] = useState("");
  const [manualRelationship, setManualRelationship] = useState("");
  const [manualInquiryType, setManualInquiryType] = useState("general_inquiry");
  const [manualUrgency, setManualUrgency] = useState("Medium");
  const [manualSummary, setManualSummary] = useState("");
  const [manualDetails, setManualDetails] = useState("");

  const fetchStats = async () => {
    try {
      const res = await api.frontDesk.getStats();
      setStats(res);
    } catch (err) {
      console.warn("Could not fetch front desk stats:", err);
    }
  };

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const res = await api.frontDesk.getSubmissions({
        status: activeTab === "ALL" ? undefined : activeTab,
        query: searchQuery || undefined,
        limit: 50,
      });
      setSubmissions(res.items || []);
      setTotal(res.pagination?.total || 0);
    } catch (err) {
      toast({
        title: "Error Loading Queue",
        description: err.message || "Failed to load submissions.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchSubmissions();
  }, [activeTab]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchSubmissions();
  };

  const handleOpenDetail = async (sub) => {
    try {
      const fullSub = await api.frontDesk.getSubmission(sub.id);
      setSelectedSubmission(fullSub);
      setDetailModalOpen(true);
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to load submission details.",
        variant: "destructive",
      });
    }
  };

  const handleOpenRoute = (sub) => {
    setSelectedSubmission(sub);
    setDestDepartment(sub.destination_department || DEPARTMENTS[0]);
    setRouteUrgency(sub.urgency || "Medium");
    setRouteNotes("");
    setRouteModalOpen(true);
  };

  const handleRouteSubmit = async (e) => {
    e.preventDefault();
    if (!destDepartment) {
      toast({ title: "Validation Error", description: "Select a destination department.", variant: "destructive" });
      return;
    }
    setActionLoading(true);
    try {
      await api.frontDesk.routeSubmission(selectedSubmission.id, {
        destination_department: destDepartment,
        urgency: routeUrgency,
        routing_notes: routeNotes,
      });
      toast({
        title: "Submission Routed",
        description: `Successfully routed ${selectedSubmission.submission_number} to ${destDepartment}.`,
      });
      setRouteModalOpen(false);
      setDetailModalOpen(false);
      fetchStats();
      fetchSubmissions();
    } catch (err) {
      toast({
        title: "Routing Failed",
        description: err.message || "Could not route submission.",
        variant: "destructive",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenReview = (sub) => {
    setSelectedSubmission(sub);
    setReviewStatus("FRONT_DESK_REVIEW");
    setReviewNotes("");
    setReviewModalOpen(true);
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await api.frontDesk.reviewSubmission(selectedSubmission.id, {
        status: reviewStatus,
        notes: reviewNotes,
      });
      toast({
        title: "Status Updated",
        description: `Submission marked as ${reviewStatus.replace(/_/g, " ")}.`,
      });
      setReviewModalOpen(false);
      setDetailModalOpen(false);
      fetchStats();
      fetchSubmissions();
    } catch (err) {
      toast({
        title: "Update Failed",
        description: err.message || "Failed to update review status.",
        variant: "destructive",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckDuplicates = async (sub) => {
    setDuplicateLoading(true);
    setDuplicateCandidates([]);
    setDuplicateModalOpen(true);
    try {
      const candidates = await api.frontDesk.checkDuplicates(sub.id);
      setDuplicateCandidates(candidates || []);
    } catch (err) {
      toast({
        title: "Duplicate Check Failed",
        description: err.message || "Error searching canonical person directory.",
        variant: "destructive",
      });
    } finally {
      setDuplicateLoading(false);
    }
  };

  const handleCreateManual = async (e) => {
    e.preventDefault();
    if (!manualSummary.trim()) {
      toast({ title: "Validation Error", description: "Summary is required.", variant: "destructive" });
      return;
    }
    setActionLoading(true);
    try {
      const created = await api.frontDesk.createManual({
        source: manualSource,
        submitter_name: manualName || undefined,
        submitter_phone: manualPhone || undefined,
        submitter_email: manualEmail || undefined,
        submitter_relationship: manualRelationship || undefined,
        inquiry_type: manualInquiryType,
        urgency: manualUrgency,
        summary: manualSummary,
        details: manualDetails || undefined,
      });
      toast({
        title: "Intake Recorded",
        description: `Created ${created.submission_number} for ${created.submitter_name || "Anonymous"}.`,
      });
      setWalkInModalOpen(false);
      // Reset form
      setManualName("");
      setManualPhone("");
      setManualEmail("");
      setManualRelationship("");
      setManualSummary("");
      setManualDetails("");
      fetchStats();
      fetchSubmissions();
    } catch (err) {
      toast({
        title: "Failed to Record Intake",
        description: err.message || "Could not save manual entry.",
        variant: "destructive",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "RECEIVED":
        return <Badge className="bg-sky-600 text-white hover:bg-sky-700">New / Received</Badge>;
      case "FRONT_DESK_REVIEW":
        return <Badge className="bg-amber-600 text-white hover:bg-amber-700">Front Desk Review</Badge>;
      case "ROUTED":
        return <Badge className="bg-indigo-600 text-white hover:bg-indigo-700">Routed to Dept</Badge>;
      case "DEPARTMENT_REVIEW":
        return <Badge className="bg-purple-600 text-white hover:bg-purple-700">Dept Review</Badge>;
      case "ACCEPTED":
        return <Badge className="bg-emerald-600 text-white hover:bg-emerald-700">Accepted</Badge>;
      case "RETURNED_TO_FRONT_DESK":
        return <Badge className="bg-rose-600 text-white hover:bg-rose-700">Returned</Badge>;
      case "DUPLICATE":
        return <Badge variant="secondary">Duplicate</Badge>;
      case "OUT_OF_SCOPE":
        return <Badge variant="outline">Out of Scope</Badge>;
      case "SPAM":
      case "CLOSED":
        return <Badge variant="outline" className="text-muted-foreground">Closed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getUrgencyBadge = (urgency) => {
    switch (urgency) {
      case "Critical":
        return <Badge variant="destructive" className="animate-pulse">Critical</Badge>;
      case "High":
        return <Badge className="bg-orange-500 text-white">High</Badge>;
      case "Medium":
        return <Badge variant="secondary">Medium</Badge>;
      default:
        return <Badge variant="outline">Low</Badge>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 rounded-xl text-primary">
              <Inbox className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold font-heading text-foreground">
                Front Desk & Public Intake
              </h1>
              <p className="text-sm text-muted-foreground">
                Reception, triage, and departmental routing for community inquiries & web submissions.
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchStats();
              fetchSubmissions();
            }}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => setWalkInModalOpen(true)}
            className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <PlusCircle className="w-4 h-4" />
            Record Walk-in / Call
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="bg-card border rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase">New</span>
            <Inbox className="w-4 h-4 text-sky-500" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{stats.received_count}</div>
          <p className="text-[11px] text-muted-foreground mt-1">Awaiting triage</p>
        </div>

        <div className="bg-card border rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase">Under Review</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{stats.front_desk_review_count}</div>
          <p className="text-[11px] text-muted-foreground mt-1">In active assessment</p>
        </div>

        <div className="bg-card border rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase">Routed</span>
            <ArrowRight className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{stats.routed_count}</div>
          <p className="text-[11px] text-muted-foreground mt-1">In department queues</p>
        </div>

        <div className="bg-card border rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase">Returned</span>
            <CornerUpLeft className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{stats.returned_count}</div>
          <p className="text-[11px] text-muted-foreground mt-1">Needs re-routing</p>
        </div>

        <div className="bg-card border rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase">Accepted</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{stats.accepted_count}</div>
          <p className="text-[11px] text-muted-foreground mt-1">Department ownership</p>
        </div>

        <div className="bg-card border rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase">Oldest Age</span>
            <Clock className="w-4 h-4 text-muted-foreground" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">
            {stats.oldest_unreviewed_hours !== null ? `${stats.oldest_unreviewed_hours}h` : "—"}
          </div>
          <p className="text-[11px] text-muted-foreground mt-1">Unreviewed waiting</p>
        </div>
      </div>

      {/* Destination Department Summary */}
      {stats.department_counts && Object.keys(stats.department_counts).length > 0 && (
        <div className="bg-card border rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Building2 className="w-4 h-4 text-primary" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Department Routing Breakdown
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.department_counts).map(([dept, count]) => (
              <Badge key={dept} variant="outline" className="px-3 py-1 bg-muted/50 text-xs font-medium">
                {dept}: <span className="ml-1 font-bold text-primary">{count}</span>
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Main Queue & Tabs */}
      <div className="bg-card border rounded-xl shadow-sm overflow-hidden">
        {/* Search & Tabs */}
        <div className="p-4 border-b space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 max-w-md w-full">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by submission #, name, phone, email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-9 text-sm"
                />
              </div>
              <Button type="submit" size="sm" variant="secondary">
                Search
              </Button>
            </form>
            <div className="text-xs text-muted-foreground">
              Showing <span className="font-semibold text-foreground">{submissions.length}</span> of{" "}
              <span className="font-semibold text-foreground">{total}</span> records
            </div>
          </div>

          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.key
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-12 text-center text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-primary" />
              <p className="text-sm">Loading intake queue...</p>
            </div>
          ) : submissions.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              <Inbox className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-base font-medium">No submissions found</p>
              <p className="text-xs mt-1">There are no records matching the current tab and filter.</p>
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 text-xs font-semibold text-muted-foreground border-b uppercase">
                <tr>
                  <th className="py-3 px-4">Ref #</th>
                  <th className="py-3 px-4">Source</th>
                  <th className="py-3 px-4">Submitter</th>
                  <th className="py-3 px-4">Summary</th>
                  <th className="py-3 px-4">Urgency</th>
                  <th className="py-3 px-4">Destination</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Received</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {submissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4 font-mono font-semibold text-primary">
                      {sub.submission_number}
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-xs capitalize font-medium text-muted-foreground">
                        {sub.source.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-foreground">
                        {sub.submitter_name || "Anonymous"}
                      </div>
                      {(sub.submitter_phone || sub.submitter_email) && (
                        <div className="text-xs text-muted-foreground">
                          {sub.submitter_phone || sub.submitter_email}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate" title={sub.summary}>
                      {sub.summary}
                    </td>
                    <td className="py-3 px-4">{getUrgencyBadge(sub.urgency)}</td>
                    <td className="py-3 px-4 text-xs font-medium text-muted-foreground">
                      {sub.destination_department || <span className="italic text-muted-foreground/60">Unrouted</span>}
                    </td>
                    <td className="py-3 px-4">{getStatusBadge(sub.status)}</td>
                    <td className="py-3 px-4 text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(sub.received_at).toLocaleDateString()}{" "}
                      {new Date(sub.received_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenDetail(sub)}
                        className="h-8 text-xs"
                      >
                        Inspect
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleOpenRoute(sub)}
                        className="h-8 text-xs"
                      >
                        Route
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* DETAIL MODAL */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {selectedSubmission && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <DialogTitle className="text-xl font-bold font-mono text-primary flex items-center gap-2">
                      {selectedSubmission.submission_number}
                      {getStatusBadge(selectedSubmission.status)}
                      {getUrgencyBadge(selectedSubmission.urgency)}
                    </DialogTitle>
                    <DialogDescription className="text-xs text-muted-foreground mt-1">
                      Received via {selectedSubmission.source.replace(/_/g, " ")} on{" "}
                      {new Date(selectedSubmission.received_at).toLocaleString()}
                    </DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-6 pt-2">
                {/* Submitter Info Card */}
                <div className="bg-muted/40 rounded-xl p-4 border grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="text-muted-foreground font-medium block">Submitter Name:</span>
                    <span className="font-semibold text-foreground text-sm">
                      {selectedSubmission.submitter_name || "Anonymous"}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-medium block">Phone:</span>
                    <span className="text-foreground">{selectedSubmission.submitter_phone || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-medium block">Email:</span>
                    <span className="text-foreground">{selectedSubmission.submitter_email || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-medium block">Relationship:</span>
                    <span className="text-foreground">{selectedSubmission.submitter_relationship || "N/A"}</span>
                  </div>
                </div>

                {/* Summary & Details */}
                <div className="space-y-3">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">
                      Inquiry Summary
                    </h4>
                    <p className="text-sm font-medium text-foreground bg-card border rounded-lg p-3">
                      {selectedSubmission.summary}
                    </p>
                  </div>

                  {selectedSubmission.details && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">
                        Detailed Narrative
                      </h4>
                      <p className="text-xs text-muted-foreground bg-card border rounded-lg p-3 whitespace-pre-wrap">
                        {selectedSubmission.details}
                      </p>
                    </div>
                  )}
                </div>

                {/* Raw Immutable Webhook Payload */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-primary" />
                    Original Google Form Payload (Immutable)
                  </h4>
                  <pre className="text-[11px] font-mono bg-muted/60 p-3 rounded-lg overflow-x-auto max-h-40 border">
                    {JSON.stringify(selectedSubmission.payload_raw || {}, null, 2)}
                  </pre>
                </div>

                {/* Duplicate Check Button */}
                <div className="border rounded-xl p-4 bg-muted/20 flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold">Duplicate Check</h4>
                    <p className="text-xs text-muted-foreground">
                      Search canonical Person / Family records matching submitter before downstream action.
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleCheckDuplicates(selectedSubmission)}
                  >
                    Check Duplicates
                  </Button>
                </div>

                {/* Append-Only Routing History Timeline */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-primary" />
                    Audit & Routing History (Append-Only)
                  </h4>
                  <div className="border rounded-xl p-3 bg-card divide-y text-xs space-y-2">
                    {selectedSubmission.routing_history?.length > 0 ? (
                      selectedSubmission.routing_history.map((hist) => (
                        <div key={hist.id} className="pt-2 first:pt-0">
                          <div className="flex items-center justify-between text-muted-foreground">
                            <span className="font-semibold text-foreground">
                              {hist.previous_status} → {hist.new_status}
                            </span>
                            <span>{new Date(hist.changed_at).toLocaleString()}</span>
                          </div>
                          {hist.new_destination && (
                            <div className="text-[11px] text-primary mt-0.5">
                              Destination: {hist.new_destination}
                            </div>
                          )}
                          {hist.reason_note && (
                            <p className="text-[11px] text-muted-foreground mt-0.5 italic">
                              "{hist.reason_note}"
                            </p>
                          )}
                          <div className="text-[10px] text-muted-foreground/70 mt-0.5">
                            By: {hist.changed_by_name || "System"}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-muted-foreground text-xs italic">No history records logged yet.</p>
                    )}
                  </div>
                </div>

                {/* Downstream Conversion Linkages */}
                {selectedSubmission.conversion_links?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                      <ExternalLink className="w-3.5 h-3.5 text-emerald-600" />
                      Downstream Conversions & Linkages
                    </h4>
                    <div className="border rounded-xl p-3 bg-card divide-y text-xs space-y-2">
                      {selectedSubmission.conversion_links.map((link) => (
                        <div key={link.id} className="pt-2 first:pt-0 flex items-center justify-between">
                          <div>
                            <span className="font-semibold uppercase text-emerald-700">
                              {link.downstream_entity_type}:
                            </span>{" "}
                            <span className="font-mono text-foreground font-bold">
                              {link.downstream_entity_reference || link.downstream_entity_id}
                            </span>
                            {link.notes && <p className="text-[11px] text-muted-foreground mt-0.5">{link.notes}</p>}
                          </div>
                          <div className="text-right text-[10px] text-muted-foreground">
                            Linked by {link.created_by_name || "Staff"} on {new Date(link.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <DialogFooter className="mt-6 flex justify-between gap-2 sm:justify-between">
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenReview(selectedSubmission)}
                  >
                    Triage Status
                  </Button>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    className="bg-primary text-primary-foreground"
                    onClick={() => {
                      setDetailModalOpen(false);
                      handleOpenRoute(selectedSubmission);
                    }}
                  >
                    Route to Department
                  </Button>
                </div>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* ROUTING MODAL */}
      <Dialog open={routeModalOpen} onOpenChange={setRouteModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold flex items-center gap-2">
              <Send className="w-5 h-5 text-primary" />
              Route to Receiving Department
            </DialogTitle>
            <DialogDescription className="text-xs">
              Front Desk assigns destination department. The receiving department determines authoritative downstream action.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleRouteSubmit} className="space-y-4 pt-2">
            <div className="space-y-1.5">
              <Label htmlFor="destinationDept" className="text-xs font-semibold">
                Destination Department *
              </Label>
              <Select value={destDepartment} onValueChange={setDestDepartment}>
                <SelectTrigger id="destinationDept">
                  <SelectValue placeholder="Select receiving department" />
                </SelectTrigger>
                <SelectContent className="max-h-60">
                  {DEPARTMENTS.map((dept) => (
                    <SelectItem key={dept} value={dept}>
                      {dept}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="routeUrgency" className="text-xs font-semibold">
                Priority / Urgency
              </Label>
              <Select value={routeUrgency} onValueChange={setRouteUrgency}>
                <SelectTrigger id="routeUrgency">
                  <SelectValue placeholder="Select urgency" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Low">Low</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="routeNotes" className="text-xs font-semibold">
                Routing Rationale & Triage Notes
              </Label>
              <textarea
                id="routeNotes"
                rows={3}
                value={routeNotes}
                onChange={(e) => setRouteNotes(e.target.value)}
                placeholder="Reason for routing to this department..."
                className="w-full text-xs rounded-md border border-input bg-transparent px-3 py-2 shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setRouteModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={actionLoading}>
                {actionLoading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                Confirm Routing
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* REVIEW / TRIAGE STATUS MODAL */}
      <Dialog open={reviewModalOpen} onOpenChange={setReviewModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold">Update Review Status</DialogTitle>
            <DialogDescription className="text-xs">
              Mark submission under Front Desk review, or resolve non-routable items (Duplicate, Out of Scope, Spam).
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleReviewSubmit} className="space-y-4 pt-2">
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold">Review Status</Label>
              <Select value={reviewStatus} onValueChange={setReviewStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="FRONT_DESK_REVIEW">Under Review (Front Desk)</SelectItem>
                  <SelectItem value="DUPLICATE">Duplicate Record</SelectItem>
                  <SelectItem value="OUT_OF_SCOPE">Out of Scope</SelectItem>
                  <SelectItem value="SPAM">Spam</SelectItem>
                  <SelectItem value="CLOSED">Closed (Administrative)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-semibold">Administrative Notes</Label>
              <textarea
                rows={3}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Reason or disposition note..."
                className="w-full text-xs rounded-md border border-input bg-transparent px-3 py-2 shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setReviewModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={actionLoading}>
                {actionLoading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                Update Status
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* DUPLICATE DETECTION RESULTS MODAL */}
      <Dialog open={duplicateModalOpen} onOpenChange={setDuplicateModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold">Duplicate Search Results</DialogTitle>
            <DialogDescription className="text-xs">
              Matches found in canonical Person / Family directory. No records are auto-merged.
            </DialogDescription>
          </DialogHeader>

          <div className="py-2 space-y-3">
            {duplicateLoading ? (
              <div className="p-8 text-center text-muted-foreground">
                <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-primary" />
                <p className="text-xs">Searching canonical records...</p>
              </div>
            ) : duplicateCandidates.length === 0 ? (
              <div className="p-6 text-center text-muted-foreground border rounded-lg bg-muted/20">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-sm font-semibold text-foreground">No Potential Duplicates Found</p>
                <p className="text-xs mt-1">Submitter name and contact details do not match existing client records.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {duplicateCandidates.map((cand) => (
                  <div key={cand.id} className="p-3 border rounded-lg bg-card text-xs flex justify-between items-center">
                    <div>
                      <div className="font-semibold text-foreground">{cand.name}</div>
                      <div className="text-[11px] text-muted-foreground">{cand.details}</div>
                      <div className="text-[10px] text-amber-600 mt-0.5">
                        Factors: {cand.match_reasons?.join(", ") || "Name similarity"}
                      </div>
                    </div>
                    <Badge variant="outline" className="font-mono text-xs">
                      {Math.round(cand.match_score * 100)}% Match
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button size="sm" onClick={() => setDuplicateModalOpen(false)}>
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* MANUAL INTAKE (WALK-IN / PHONE) MODAL */}
      <Dialog open={walkInModalOpen} onOpenChange={setWalkInModalOpen}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold flex items-center gap-2">
              <PlusCircle className="w-5 h-5 text-primary" />
              Record Public Intake (Walk-In / Phone / Counter)
            </DialogTitle>
            <DialogDescription className="text-xs">
              Log an in-person, phone, or direct counter inquiry for Front Desk triage.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCreateManual} className="space-y-4 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold">Intake Source *</Label>
                <Select value={manualSource} onValueChange={setManualSource}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="walk_in">Walk-in (Counter)</SelectItem>
                    <SelectItem value="phone">Phone Call</SelectItem>
                    <SelectItem value="email">Direct Email</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold">Priority / Urgency</Label>
                <Select value={manualUrgency} onValueChange={setManualUrgency}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select urgency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Low">Low</SelectItem>
                    <SelectItem value="Medium">Medium</SelectItem>
                    <SelectItem value="High">High</SelectItem>
                    <SelectItem value="Critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold">Submitter Name</Label>
                <Input
                  value={manualName}
                  onChange={(e) => setManualName(e.target.value)}
                  placeholder="Full name (or leave empty if anonymous)"
                  className="h-8 text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold">Phone Number</Label>
                <Input
                  value={manualPhone}
                  onChange={(e) => setManualPhone(e.target.value)}
                  placeholder="306-555-0199"
                  className="h-8 text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold">Email Address</Label>
                <Input
                  type="email"
                  value={manualEmail}
                  onChange={(e) => setManualEmail(e.target.value)}
                  placeholder="contact@example.com"
                  className="h-8 text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold">Relationship / Role</Label>
                <Input
                  value={manualRelationship}
                  onChange={(e) => setManualRelationship(e.target.value)}
                  placeholder="e.g. Parent, Neighbour, Self"
                  className="h-8 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-semibold">Summary / Concern *</Label>
              <Input
                required
                value={manualSummary}
                onChange={(e) => setManualSummary(e.target.value)}
                placeholder="Brief summary of inquiry or concern"
                className="h-8 text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-semibold">Detailed Description</Label>
              <textarea
                rows={3}
                value={manualDetails}
                onChange={(e) => setManualDetails(e.target.value)}
                placeholder="Full details provided by submitter..."
                className="w-full text-xs rounded-md border border-input bg-transparent px-3 py-2 shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setWalkInModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={actionLoading}>
                {actionLoading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                Save Intake Submission
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

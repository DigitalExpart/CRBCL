import React, { useState, useEffect } from "react";
import { casesApi } from "@/api/cases";
import { caseNotesApi } from "@/api/caseNotes";
import { assessmentsApi } from "@/api/assessments";
import { assessmentTemplatesApi } from "@/api/assessmentTemplates";
import { useParams, Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft, Edit2, CheckCircle2, AlertTriangle, User, Users, ShieldAlert,
  FileText, Clock, ArrowRightLeft, Link as LinkIcon, Download, Plus, Lock,
  Calendar, MapPin, Phone, Mail, Building, History, Check, X, RotateCcw,
  Sparkles, Stethoscope, AlertCircle, Share2, FolderCheck, ClipboardList, ShieldCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import CaseFormDialog from "@/components/cases/CaseFormDialog";

export default function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") || "snapshot";

  const [caseData, setCaseData] = useState(null);
  const [snapshot, setSnapshot] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [people, setPeople] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [externalWorkers, setExternalWorkers] = useState([]);
  const [sources, setSources] = useState([]);
  const [links, setLinks] = useState([]);
  const [restrictions, setRestrictions] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [statusHistory, setStatusHistory] = useState([]);
  const [notes, setNotes] = useState([]);
  const [noteMetrics, setNoteMetrics] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [availableTemplates, setAvailableTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals & Actions
  const [showEdit, setShowEdit] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [showReopenModal, setShowReopenModal] = useState(false);
  const [showAddPersonModal, setShowAddPersonModal] = useState(false);
  const [showAssignWorkerModal, setShowAssignWorkerModal] = useState(false);
  const [showAddExtWorkerModal, setShowAddExtWorkerModal] = useState(false);
  const [showAddSourceModal, setShowAddSourceModal] = useState(false);
  const [showLinkCaseModal, setShowLinkCaseModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showAddRestrictionModal, setShowAddRestrictionModal] = useState(false);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [showAddendumModal, setShowAddendumModal] = useState(null); // note_id when open
  const [showLaunchAssessmentModal, setShowLaunchAssessmentModal] = useState(false);
  const [launchAssessmentForm, setLaunchAssessmentForm] = useState({
    template_key: "HOME_ASSESSMENT",
    person_id: "",
    title: "",
  });

  // Form states
  const [closeForm, setCloseForm] = useState({ closed_reason: "", closed_date: "" });
  const [reopenForm, setReopenForm] = useState({ reopened_reason: "" });
  const [personForm, setPersonForm] = useState({ person_id: "", role: "subject_child", is_primary: false, notes: "" });
  const [workerForm, setWorkerForm] = useState({ user_id: "", role: "caseworker", notes: "" });
  const [extWorkerForm, setExtWorkerForm] = useState({ name: "", organization: "", role: "", phone: "", email: "" });
  const [sourceForm, setSourceForm] = useState({ category: "COLLATERAL_SOURCE", name: "", relationship_or_role: "", organization: "", phone: "", notes: "" });
  const [linkForm, setLinkForm] = useState({ target_case_id: "", link_type: "related_family", reason: "" });
  const [transferForm, setTransferForm] = useState({ destination_team_id: "", reason: "", submit_immediately: true });
  const [restrictionForm, setRestrictionForm] = useState({ user_id: "", restriction_type: "CONFLICT_OF_INTEREST", reason: "" });
  const [addendumForm, setAddendumForm] = useState({ content: "", reason: "" });
  const [noteForm, setNoteForm] = useState({
    subject: "",
    content: "",
    note_type: "Progress Note",
    contact_type: "FACE_TO_FACE",
    location: "OFFICE",
    duration_minutes: 30,
    is_well_child_checkup: false,
    appointment_status: "ATTENDED",
    status: "COMPLETED",
    notify_team: false,
    is_confidential: false,
  });

  const loadAll = async () => {
    try {
      setLoading(true);
      const [
        caseRes,
        snapRes,
        peopleRes,
        assignRes,
        extWorkersRes,
        sourcesRes,
        linksRes,
        restrRes,
        transfersRes,
        historyRes,
        notesRes,
        metricsRes,
        assessmentsRes,
        templatesRes,
      ] = await Promise.all([
        casesApi.get(id),
        casesApi.getSnapshot(id).catch(() => null),
        casesApi.getPeople(id).catch(() => []),
        casesApi.getAssignments(id).catch(() => []),
        casesApi.getExternalWorkers(id).catch(() => []),
        casesApi.getSources(id).catch(() => []),
        casesApi.getLinks(id).catch(() => []),
        casesApi.getRestrictions(id).catch(() => []),
        casesApi.getTransfers(id).catch(() => []),
        casesApi.getStatusHistory(id).catch(() => []),
        caseNotesApi.listForCase(id, { limit: 100 }).catch(() => ({ items: [] })),
        caseNotesApi.getMetrics(id).catch(() => null),
        assessmentsApi.listByCase(id, { limit: 100 }).catch(() => ({ items: [] })),
        assessmentTemplatesApi.list({ is_active: true }).catch(() => []),
      ]);

      setCaseData(caseRes);
      setSnapshot(snapRes);
      setPeople(peopleRes || []);
      setAssignments(assignRes || []);
      setExternalWorkers(extWorkersRes || []);
      setSources(sourcesRes || []);
      setLinks(linksRes || []);
      setRestrictions(restrRes || []);
      setTransfers(transfersRes || []);
      setStatusHistory(historyRes || []);
      setNotes(notesRes?.items || []);
      setNoteMetrics(metricsRes);
      setAssessments(assessmentsRes?.items || []);
      setAvailableTemplates(templatesRes || []);
    } catch (e) {
      console.error("Error loading case detail:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchAssessment = async () => {
    try {
      const payload = {
        case_id: id,
        template_key: launchAssessmentForm.template_key,
        person_id: launchAssessmentForm.person_id || undefined,
        title: launchAssessmentForm.title.trim() || undefined,
      };
      const created = await assessmentsApi.create(id, payload);
      setShowLaunchAssessmentModal(false);
      navigate(`/assessments/${created.id}`);
    } catch (err) {
      alert(err.message || "Failed to initiate assessment");
    }
  };

  useEffect(() => {
    loadAll();
  }, [id]);

  const handleCloseCase = async () => {
    if (!closeForm.closed_reason.trim()) return alert("Closing rationale is mandatory.");
    await casesApi.close(id, closeForm);
    setShowCloseModal(false);
    loadAll();
  };

  const handleReopenCase = async () => {
    if (!reopenForm.reopened_reason.trim()) return alert("Reopening justification is mandatory.");
    await casesApi.reopen(id, reopenForm);
    setShowReopenModal(false);
    loadAll();
  };

  const handleCreateNote = async () => {
    if (!noteForm.content.trim()) return alert("Note content is required.");
    await caseNotesApi.create(id, noteForm);
    setShowNoteModal(false);
    loadAll();
  };

  const handleLockNote = async (noteId) => {
    if (window.confirm("Are you sure you want to permanently lock this case note? Once locked, edits are prohibited and only addenda may be appended.")) {
      await caseNotesApi.lock(noteId);
      loadAll();
    }
  };

  const handleAddAddendum = async () => {
    if (!addendumForm.content.trim()) return alert("Addendum narrative is required.");
    await caseNotesApi.addAddendum(showAddendumModal, addendumForm);
    setShowAddendumModal(null);
    setAddendumForm({ content: "", reason: "" });
    loadAll();
  };

  const handleCloneNote = async (noteId) => {
    await caseNotesApi.clone(noteId);
    loadAll();
  };

  const handleApproveTransfer = async (transferId) => {
    const notes = prompt("Enter approval review notes (optional):");
    await casesApi.approveTransfer(transferId, { review_notes: notes || "Transfer approved by supervisor." });
    loadAll();
  };

  const handleReturnTransfer = async (transferId) => {
    const notes = prompt("Enter reason for return / clarifications required:");
    if (!notes) return alert("Return notes are required.");
    await casesApi.returnTransfer(transferId, { review_notes: notes });
    loadAll();
  };

  const handleDenyTransfer = async (transferId) => {
    const notes = prompt("Enter denial rationale:");
    if (!notes) return alert("Denial rationale is required.");
    await casesApi.denyTransfer(transferId, { review_notes: notes });
    loadAll();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-heading font-semibold mb-2">Case not found</h2>
        <Link to="/cases" className="text-primary hover:underline">
          ← Back to cases
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Link to="/cases" className="hover:text-primary transition-colors flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" /> Cases
          </Link>
          <span>/</span>
          <span className="text-foreground font-mono font-medium">{caseData.case_number}</span>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs">
            STAGE: {caseData.stage}
          </Badge>
          <StatusBadge status={caseData.status} />
        </div>
      </div>

      {/* Main Header Banner */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold font-heading text-foreground">{caseData.title}</h1>
            <Badge variant="secondary" className="text-xs">
              {caseData.case_type}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground max-w-3xl">
            {caseData.description || "No case description provided."}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {caseData.status === "Closed" ? (
            <Button variant="default" size="sm" onClick={() => setShowReopenModal(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white">
              <RotateCcw className="w-4 h-4 mr-1.5" /> Reopen File
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setShowCloseModal(true)} className="border-rose-500/30 text-rose-600 hover:bg-rose-500/10">
              <Check className="w-4 h-4 mr-1.5" /> Controlled Close
            </Button>
          )}

          <Button variant="outline" size="sm" onClick={() => setShowEdit(true)}>
            <Edit2 className="w-4 h-4 mr-1.5" /> Edit File
          </Button>

          <Button variant="outline" size="sm" onClick={() => setShowAddRestrictionModal(true)} className="text-amber-600 border-amber-500/30 hover:bg-amber-500/10">
            <ShieldAlert className="w-4 h-4 mr-1.5" /> Conflict Restriction
          </Button>
        </div>
      </div>

      {/* 360° Navigation Tabs */}
      <Tabs value={activeTab} onValueChange={(val) => setSearchParams({ tab: val })}>
        <TabsList className="grid grid-cols-3 md:grid-cols-9 h-auto p-1 bg-muted/60">
          <TabsTrigger value="snapshot" className="text-xs py-2">Snapshot</TabsTrigger>
          <TabsTrigger value="people" className="text-xs py-2">People ({people.length})</TabsTrigger>
          <TabsTrigger value="workers" className="text-xs py-2">Workers ({assignments.length})</TabsTrigger>
          <TabsTrigger value="notes" className="text-xs py-2">Clinical Notes ({notes.length})</TabsTrigger>
          <TabsTrigger value="assessments" className="text-xs py-2 font-medium text-emerald-600 dark:text-emerald-400">Assessments ({assessments.length})</TabsTrigger>
          <TabsTrigger value="sources" className="text-xs py-2">Sources ({sources.length})</TabsTrigger>
          <TabsTrigger value="links" className="text-xs py-2">Linked ({links.length})</TabsTrigger>
          <TabsTrigger value="transfers" className="text-xs py-2">Transfers ({transfers.length})</TabsTrigger>
          <TabsTrigger value="history" className="text-xs py-2">Audit & History</TabsTrigger>
        </TabsList>

        {/* ── TAB 1: SNAPSHOT ───────────────────────────── */}
        <TabsContent value="snapshot" className="space-y-6 mt-6">
          {snapshot?.alerts?.length > 0 && (
            <div className="space-y-2">
              {snapshot.alerts.map((alt, i) => (
                <div
                  key={i}
                  className={`p-3.5 rounded-lg border text-sm flex items-center gap-2.5 ${
                    alt.severity === "high"
                      ? "bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-300"
                      : "bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-300"
                  }`}
                >
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{alt.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* KPI Dashboard */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground uppercase">Days Open</span>
                  <Clock className="w-4 h-4 text-primary" />
                </div>
                <div className="text-2xl font-bold mt-1 text-foreground">{snapshot?.days_open ?? 0} days</div>
                <p className="text-[11px] text-muted-foreground mt-0.5">Intake: {snapshot?.intake_date || "—"}</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground uppercase">Assigned Team</span>
                  <Building className="w-4 h-4 text-blue-500" />
                </div>
                <div className="text-lg font-bold mt-1 text-foreground truncate">
                  {caseData.assigned_team?.name || "Prevention Team"}
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">Lead: {caseData.assigned_worker_name || "Unassigned"}</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground uppercase">People Involved</span>
                  <Users className="w-4 h-4 text-emerald-500" />
                </div>
                <div className="text-2xl font-bold mt-1 text-foreground">{snapshot?.total_people_count ?? people.length}</div>
                <p className="text-[11px] text-muted-foreground mt-0.5">Family & Extended Kin</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground uppercase">Next Appointment</span>
                  <Calendar className="w-4 h-4 text-purple-500" />
                </div>
                <div className="text-sm font-semibold mt-1 text-foreground truncate">
                  {snapshot?.next_appointment ? new Date(snapshot.next_appointment).toLocaleDateString() : "None Scheduled"}
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">Last note: {snapshot?.last_note_date ? new Date(snapshot.last_note_date).toLocaleDateString() : "None"}</p>
              </CardContent>
            </Card>
          </div>

          {/* Primary Entities Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Primary Client */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <User className="w-4 h-4 text-primary" /> Primary Subject Client
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-2">
                {snapshot?.primary_client ? (
                  <div>
                    <div className="font-semibold text-foreground text-base">{snapshot.primary_client.full_name}</div>
                    <div className="text-xs text-muted-foreground mt-1">DOB: {snapshot.primary_client.date_of_birth || "—"}</div>
                    <div className="text-xs text-muted-foreground">Gender: {snapshot.primary_client.gender || "—"}</div>
                    <Link to={`/clients/${snapshot.primary_client.id}`} className="text-xs text-primary hover:underline mt-2 inline-block">
                      View Client 360° Profile →
                    </Link>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No primary subject linked directly to this case.</p>
                )}
              </CardContent>
            </Card>

            {/* Family Unit */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Users className="w-4 h-4 text-emerald-500" /> Family File
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-2">
                {snapshot?.family ? (
                  <div>
                    <div className="font-semibold text-foreground text-base">{snapshot.family.family_name}</div>
                    <div className="text-xs text-muted-foreground mt-1">Nation / Community: {snapshot.family.first_nation || "Qu'Appelle Territory"}</div>
                    <Link to={`/families/${snapshot.family.id}`} className="text-xs text-primary hover:underline mt-2 inline-block">
                      View Family Wellness Record →
                    </Link>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No family unit linked.</p>
                )}
              </CardContent>
            </Card>

            {/* Originating Referral */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <FolderCheck className="w-4 h-4 text-purple-500" /> Originating Referral
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-2">
                {snapshot?.origin_referral ? (
                  <div>
                    <div className="font-semibold text-foreground text-base font-mono">{snapshot.origin_referral.referral_number}</div>
                    <div className="text-xs text-muted-foreground mt-1">Received: {snapshot.origin_referral.received_date || "—"} via {snapshot.origin_referral.received_method}</div>
                    <div className="text-xs text-muted-foreground">Priority: {snapshot.origin_referral.priority}</div>
                    <Link to={`/referrals/${snapshot.origin_referral.id}`} className="text-xs text-primary hover:underline mt-2 inline-block">
                      View Source Referral →
                    </Link>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">Direct intake (no linked referral record).</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── TAB 2: PEOPLE ROSTER ───────────────────────── */}
        <TabsContent value="people" className="space-y-4 mt-6">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-foreground">Involved Family & Collateral People</h3>
            <Button size="sm" onClick={() => setShowAddPersonModal(true)}>
              <Plus className="w-4 h-4 mr-1.5" /> Add Person to Case
            </Button>
          </div>

          <div className="bg-card border rounded-xl overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-muted/50 text-muted-foreground text-xs border-b">
                <tr>
                  <th className="py-3 px-4">Name</th>
                  <th className="py-3 px-4">Role in Case</th>
                  <th className="py-3 px-4">Relationship</th>
                  <th className="py-3 px-4">Primary?</th>
                  <th className="py-3 px-4">Start Date</th>
                  <th className="py-3 px-4">Notes</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {people.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-muted-foreground text-xs">
                      No individuals linked to this case roster yet.
                    </td>
                  </tr>
                ) : (
                  people.map((p) => (
                    <tr key={p.id} className="hover:bg-muted/30">
                      <td className="py-3 px-4 font-medium text-foreground">
                        {p.person_first_name} {p.person_last_name}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="capitalize text-xs font-normal">
                          {p.role?.replace(/_/g, " ")}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">{p.relationship_to_subject || "—"}</td>
                      <td className="py-3 px-4">
                        {p.is_primary && (
                          <Badge variant="secondary" className="text-[11px] bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                            Primary Subject
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs text-muted-foreground">{p.start_date || "—"}</td>
                      <td className="py-3 px-4 text-xs text-muted-foreground max-w-xs truncate">{p.notes || "—"}</td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-rose-600 hover:bg-rose-500/10 h-7 px-2"
                          onClick={async () => {
                            if (window.confirm("Remove this person from the case roster?")) {
                              await casesApi.removePerson(id, p.id);
                              loadAll();
                            }
                          }}
                        >
                          Remove
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* ── TAB 3: WORKERS & ASSIGNMENTS ──────────────── */}
        <TabsContent value="workers" className="space-y-6 mt-6">
          {/* Internal Staff */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-semibold text-foreground">Assigned Caseworkers & Investigators</h3>
              <Button size="sm" onClick={() => setShowAssignWorkerModal(true)}>
                <Plus className="w-4 h-4 mr-1.5" /> Assign Worker
              </Button>
            </div>
            <div className="bg-card border rounded-xl overflow-hidden">
              <table className="w-full text-sm text-left">
                <thead className="bg-muted/50 text-muted-foreground text-xs border-b">
                  <tr>
                    <th className="py-3 px-4">Worker Name</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Assigned Date</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {assignments.map((a) => (
                    <tr key={a.id} className="hover:bg-muted/30">
                      <td className="py-3 px-4 font-medium text-foreground">{a.user_name || "Staff Member"}</td>
                      <td className="py-3 px-4 text-xs text-muted-foreground">{a.user_email || "—"}</td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="capitalize text-xs font-normal">
                          {a.role?.replace(/_/g, " ")}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        {a.is_active ? (
                          <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-0 text-[11px]">
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-[11px]">Historical</Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs text-muted-foreground">
                        {a.assigned_at ? new Date(a.assigned_at).toLocaleDateString() : "—"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {a.is_active && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-rose-600 hover:bg-rose-500/10 h-7 px-2"
                            onClick={async () => {
                              if (window.confirm("End worker assignment on this case?")) {
                                await casesApi.unassignWorker(id, a.id);
                                loadAll();
                              }
                            }}
                          >
                            Unassign
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* External Workers */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-semibold text-foreground">External Workers (Band Reps, Legal, Collateral)</h3>
              <Button size="sm" variant="outline" onClick={() => setShowAddExtWorkerModal(true)}>
                <Plus className="w-4 h-4 mr-1.5" /> Add External Worker
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {externalWorkers.length === 0 ? (
                <div className="col-span-3 py-6 text-center text-xs text-muted-foreground border border-dashed rounded-lg">
                  No external workers or First Nation band representatives attached to this file.
                </div>
              ) : (
                externalWorkers.map((ew) => (
                  <Card key={ew.id} className="bg-card">
                    <CardContent className="pt-4 space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold text-foreground text-sm">{ew.name}</div>
                          <div className="text-xs text-muted-foreground">{ew.organization}</div>
                        </div>
                        <Badge variant="secondary" className="text-[10px]">{ew.role}</Badge>
                      </div>
                      <div className="pt-2 text-xs space-y-1 text-muted-foreground border-t">
                        {ew.phone && <div className="flex items-center gap-1.5"><Phone className="w-3 h-3" /> {ew.phone}</div>}
                        {ew.email && <div className="flex items-center gap-1.5"><Mail className="w-3 h-3" /> {ew.email}</div>}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        </TabsContent>

        {/* ── TAB 4: CLINICAL CASE NOTES ────────────────── */}
        <TabsContent value="notes" className="space-y-6 mt-6">
          {/* Note Metrics Banner */}
          {noteMetrics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-muted/40 p-4 rounded-xl border">
              <div>
                <span className="text-xs text-muted-foreground font-medium uppercase">Total Notes</span>
                <div className="text-xl font-bold text-foreground mt-0.5">{noteMetrics.total_notes}</div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground font-medium uppercase">Attended Visits</span>
                <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                  {noteMetrics.attendance?.attended || 0}
                </div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground font-medium uppercase">No Shows / Missed</span>
                <div className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-0.5">
                  {noteMetrics.attendance?.no_show || 0}
                </div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground font-medium uppercase">Top Contact Mode</span>
                <div className="text-sm font-semibold text-foreground mt-1">
                  {Object.keys(noteMetrics.contact_types || {})[0]?.replace(/_/g, " ") || "In Person"}
                </div>
              </div>
            </div>
          )}

          {/* Action Bar */}
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-foreground">Clinical & Family Contact Documentation</h3>
            <div className="flex items-center gap-2">
              <a href={caseNotesApi.exportCsvUrl(id)} download="case_notes.csv">
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-1.5" /> Export CSV
                </Button>
              </a>
              <Button size="sm" onClick={() => setShowNoteModal(true)}>
                <Plus className="w-4 h-4 mr-1.5" /> Record Case Note
              </Button>
            </div>
          </div>

          {/* Notes Stream */}
          <div className="space-y-4">
            {notes.length === 0 ? (
              <div className="text-center py-12 border border-dashed rounded-xl text-muted-foreground text-sm">
                No clinical notes recorded yet. Record your initial contact or progress note.
              </div>
            ) : (
              notes.map((n) => (
                <Card key={n.id} className={n.is_locked ? "border-slate-400/40 bg-slate-50/50 dark:bg-slate-900/20" : ""}>
                  <CardHeader className="pb-3 flex flex-row items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-base font-semibold text-foreground">{n.subject}</CardTitle>
                        <Badge variant="outline" className="text-xs">{n.note_type}</Badge>
                        {n.is_well_child_checkup && (
                          <Badge className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-0 text-xs flex items-center gap-1">
                            <Stethoscope className="w-3 h-3" /> Well-Child Checkup
                          </Badge>
                        )}
                        {n.is_locked ? (
                          <Badge variant="secondary" className="text-xs bg-slate-200 dark:bg-slate-800 flex items-center gap-1">
                            <Lock className="w-3 h-3" /> Immutable / Locked
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-xs">{n.status}</Badge>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center gap-3">
                        <span>By {n.author_name}</span>
                        <span>•</span>
                        <span>{new Date(n.created_at).toLocaleString()}</span>
                        {n.duration_minutes && <span>• {n.duration_minutes} mins</span>}
                        {n.contact_type && <span>• {n.contact_type.replace(/_/g, " ")}</span>}
                        {n.location && <span>• {n.location.replace(/_/g, " ")}</span>}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleCloneNote(n.id)} title="Clone metadata to new note">
                        Clone
                      </Button>
                      {!n.is_locked ? (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs text-amber-600 border-amber-500/30"
                          onClick={() => handleLockNote(n.id)}
                        >
                          <Lock className="w-3 h-3 mr-1" /> Lock Note
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs text-primary"
                          onClick={() => setShowAddendumModal(n.id)}
                        >
                          <Plus className="w-3 h-3 mr-1" /> Add Addendum
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4 text-sm text-foreground">
                    <p className="whitespace-pre-wrap leading-relaxed">{n.content}</p>

                    {/* Addenda Section */}
                    {n.addenda?.length > 0 && (
                      <div className="pt-3 border-t border-border/80 space-y-2.5">
                        <span className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1.5">
                          <History className="w-3.5 h-3.5" /> Legal Addenda ({n.addenda.length})
                        </span>
                        {n.addenda.map((ad) => (
                          <div key={ad.id} className="p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg text-xs space-y-1">
                            <div className="flex justify-between text-muted-foreground text-[11px]">
                              <span>Addendum by {ad.author?.full_name || "Authorized Staff"}</span>
                              <span>{new Date(ad.created_at).toLocaleString()}</span>
                            </div>
                            {ad.reason && <p className="font-medium text-amber-800 dark:text-amber-300">Reason: {ad.reason}</p>}
                            <p className="text-foreground whitespace-pre-wrap">{ad.content}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* ── TAB 5: SOURCES ────────────────────────────── */}
        <TabsContent value="sources" className="space-y-4 mt-6">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-foreground">Collateral & Other Information Sources</h3>
            <Button size="sm" onClick={() => setShowAddSourceModal(true)}>
              <Plus className="w-4 h-4 mr-1.5" /> Add Source
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sources.length === 0 ? (
              <div className="col-span-2 py-8 text-center text-muted-foreground text-xs border border-dashed rounded-lg">
                No collateral or community sources documented for this case.
              </div>
            ) : (
              sources.map((s) => (
                <Card key={s.id}>
                  <CardContent className="pt-4 space-y-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-semibold text-foreground text-sm">{s.name}</div>
                        <div className="text-xs text-muted-foreground">{s.relationship_or_role}</div>
                      </div>
                      <Badge variant="outline" className="text-[10px]">
                        {s.category === "COLLATERAL_SOURCE" ? "Collateral" : "Other"}
                      </Badge>
                    </div>
                    {s.organization && <p className="text-xs text-muted-foreground">Org: {s.organization}</p>}
                    {s.phone && <p className="text-xs text-muted-foreground">Phone: {s.phone}</p>}
                    {s.notes && <p className="text-xs text-foreground bg-muted/30 p-2 rounded">{s.notes}</p>}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* ── TAB 6: LINKED CASES ───────────────────────── */}
        <TabsContent value="links" className="space-y-4 mt-6">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-foreground">Cross-Linked Cases (Siblings & Family Matters)</h3>
            <Button size="sm" onClick={() => setShowLinkCaseModal(true)}>
              <LinkIcon className="w-4 h-4 mr-1.5" /> Link Case
            </Button>
          </div>

          <div className="bg-card border rounded-xl overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-muted/50 text-muted-foreground text-xs border-b">
                <tr>
                  <th className="py-3 px-4">Linked Case #</th>
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-4">Link Relationship</th>
                  <th className="py-3 px-4">Reason</th>
                  <th className="py-3 px-4">Linked Date</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {links.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted-foreground text-xs">
                      No linked sibling or concurrent cases connected.
                    </td>
                  </tr>
                ) : (
                  links.map((l) => {
                    const isSource = l.source_case_id === id;
                    const linkedNum = isSource ? l.target_case_number : l.source_case_number;
                    const linkedTitle = isSource ? l.target_case_title : "Linked Matter";
                    const targetId = isSource ? l.target_case_id : l.source_case_id;

                    return (
                      <tr key={l.id} className="hover:bg-muted/30">
                        <td className="py-3 px-4 font-mono font-medium text-primary">
                          <Link to={`/cases/${targetId}`} className="hover:underline">
                            {linkedNum || "Linked File"}
                          </Link>
                        </td>
                        <td className="py-3 px-4 text-foreground">{linkedTitle}</td>
                        <td className="py-3 px-4">
                          <Badge variant="outline" className="capitalize text-xs">
                            {l.link_type?.replace(/_/g, " ")}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-xs text-muted-foreground">{l.reason || "—"}</td>
                        <td className="py-3 px-4 text-xs text-muted-foreground">
                          {new Date(l.linked_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-rose-600 hover:bg-rose-500/10 h-7 px-2"
                            onClick={async () => {
                              if (window.confirm("Remove link between these cases?")) {
                                await casesApi.removeLink(id, l.id);
                                loadAll();
                              }
                            }}
                          >
                            Unlink
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* ── TAB 7: TRANSFERS ──────────────────────────── */}
        <TabsContent value="transfers" className="space-y-4 mt-6">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-foreground">Team & Program Transfers</h3>
            <Button size="sm" onClick={() => setShowTransferModal(true)}>
              <ArrowRightLeft className="w-4 h-4 mr-1.5" /> Request Transfer
            </Button>
          </div>

          <div className="space-y-3">
            {transfers.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground text-xs border border-dashed rounded-lg">
                No transfer requests on record for this case.
              </div>
            ) : (
              transfers.map((t) => (
                <Card key={t.id} className="p-4">
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground text-sm">
                          {t.source_team_name || "Current Team"} → {t.destination_team_name || "New Team"}
                        </span>
                        <StatusBadge status={t.status} />
                      </div>
                      <p className="text-xs text-muted-foreground">Reason: {t.reason}</p>
                      {t.review_notes && (
                        <p className="text-xs text-amber-700 dark:text-amber-300 font-medium">
                          Supervisor Notes: {t.review_notes}
                        </p>
                      )}
                    </div>

                    {t.status === "PENDING_APPROVAL" && (
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="default" onClick={() => handleApproveTransfer(t.id)} className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs">
                          Approve
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleReturnTransfer(t.id)} className="h-8 text-xs">
                          Return
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleDenyTransfer(t.id)} className="text-rose-600 hover:bg-rose-500/10 h-8 text-xs">
                          Deny
                        </Button>
                      </div>
                    )}
                  </div>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* ── TAB 8: AUDIT & HISTORY ────────────────────── */}
        <TabsContent value="history" className="space-y-4 mt-6">
          <h3 className="text-base font-semibold text-foreground">Case Status Lifecycle Audit Trail</h3>
          <div className="bg-card border rounded-xl overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-muted/50 text-muted-foreground text-xs border-b">
                <tr>
                  <th className="py-3 px-4">Transition</th>
                  <th className="py-3 px-4">Reason / Justification</th>
                  <th className="py-3 px-4">Changed By</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {statusHistory.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-muted-foreground text-xs">
                      No status transitions recorded.
                    </td>
                  </tr>
                ) : (
                  statusHistory.map((h) => (
                    <tr key={h.id} className="hover:bg-muted/30">
                      <td className="py-3 px-4 font-medium text-foreground">
                        {h.previous_status || "Initiated"} → {h.new_status}
                      </td>
                      <td className="py-3 px-4 text-xs text-muted-foreground">{h.reason || "—"}</td>
                      <td className="py-3 px-4 text-xs text-foreground">{h.changer_name || "System"}</td>
                      <td className="py-3 px-4 text-xs text-muted-foreground">
                        {new Date(h.changed_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* ── TAB: ASSESSMENTS ─────────────────────────── */}
        <TabsContent value="assessments" className="space-y-4 mt-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-semibold text-foreground">Clinical & Safety Assessments</h3>
              <p className="text-xs text-muted-foreground">Standardized, versioned questionnaires with deterministic indicator calculation and lifecycle governance.</p>
            </div>
            <Button size="sm" onClick={() => setShowLaunchAssessmentModal(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5">
              <Plus className="w-4 h-4" /> Launch Assessment
            </Button>
          </div>

          <div className="border rounded-lg overflow-hidden bg-card">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 border-b text-muted-foreground uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-4 font-semibold">Assessment #</th>
                  <th className="py-3 px-4 font-semibold">Template & Version</th>
                  <th className="py-3 px-4 font-semibold">Subject Individual</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Determination</th>
                  <th className="py-3 px-4 font-semibold">Indicators</th>
                  <th className="py-3 px-4 font-semibold">Conductor & Date</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {assessments.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-muted-foreground space-y-2">
                      <ClipboardList className="w-8 h-8 text-muted-foreground/50 mx-auto" />
                      <div className="font-medium text-foreground text-sm">No assessments initiated yet.</div>
                      <p className="text-xs">Conduct a Home Assessment, Threat Assessment, or AIEI screening for this family.</p>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowLaunchAssessmentModal(true)}
                        className="mt-2 text-emerald-600 border-emerald-500/30 hover:bg-emerald-500/10"
                      >
                        <Plus className="w-3.5 h-3.5 mr-1" /> Start Assessment
                      </Button>
                    </td>
                  </tr>
                ) : (
                  assessments.map((asm) => {
                    const ind = asm.indicator_summary || {};
                    const isLocked = asm.status === 'LOCKED';
                    const isCompleted = asm.status === 'COMPLETED';

                    return (
                      <tr key={asm.id} className="hover:bg-muted/30">
                        <td className="py-3 px-4 font-mono font-bold text-primary">
                          <Link to={`/assessments/${asm.id}`} className="hover:underline flex items-center gap-1.5">
                            {asm.assessment_number}
                            {isLocked && <Lock className="w-3 h-3 text-rose-500" />}
                          </Link>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-foreground">{asm.template?.name || asm.template_key}</div>
                          <div className="text-[10px] text-muted-foreground">Version {asm.template_version?.version_number || '1'}</div>
                        </td>
                        <td className="py-3 px-4 text-foreground">
                          {asm.person ? `${asm.person.first_name} ${asm.person.last_name}` : 'Family Unit'}
                        </td>
                        <td className="py-3 px-4">
                          <Badge
                            variant="outline"
                            className={
                              isLocked
                                ? 'bg-rose-500/10 text-rose-600 border-rose-500/30 text-[10px]'
                                : isCompleted
                                ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[10px]'
                                : 'bg-amber-500/10 text-amber-600 border-amber-500/30 text-[10px]'
                            }
                          >
                            {asm.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-medium text-foreground">
                            {asm.determination ? asm.determination.replace(/_/g, ' ') : <span className="text-muted-foreground italic">Pending</span>}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {ind.present_danger_count > 0 && (
                              <Badge variant="outline" className="bg-rose-500/10 text-rose-600 border-rose-500/30 text-[10px] py-0">
                                {ind.present_danger_count} Danger
                              </Badge>
                            )}
                            {ind.impending_danger_count > 0 && (
                              <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-500/30 text-[10px] py-0">
                                {ind.impending_danger_count} Impending
                              </Badge>
                            )}
                            {ind.protective_capacities_count > 0 && (
                              <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[10px] py-0">
                                {ind.protective_capacities_count} Strengths
                              </Badge>
                            )}
                            {!ind.present_danger_count && !ind.impending_danger_count && !ind.protective_capacities_count && (
                              <span className="text-[10px] text-muted-foreground">—</span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-xs text-muted-foreground">
                          <div>{asm.conductor?.full_name || asm.conductor?.email || 'Worker'}</div>
                          <div className="text-[10px]">{asm.conducted_at ? new Date(asm.conducted_at).toLocaleDateString() : 'Draft'}</div>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/assessments/${asm.id}`)}
                            className="h-7 text-xs"
                          >
                            Open
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>
      </Tabs>

      {/* ── Modals ────────────────────────────────────────── */}
      {/* Close Case Dialog */}
      <Dialog open={showCloseModal} onOpenChange={setShowCloseModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Controlled Case Closure</DialogTitle>
            <DialogDescription>
              Provide mandatory closure rationale for case {caseData.case_number}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-xs font-medium text-muted-foreground">Closing Rationale *</label>
              <Textarea
                placeholder="Detail goals met, safety plan verification, or transfer completion…"
                value={closeForm.closed_reason}
                onChange={(e) => setCloseForm({ ...closeForm, closed_reason: e.target.value })}
                rows={4}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Closing Date (Optional)</label>
              <Input
                type="date"
                value={closeForm.closed_date}
                onChange={(e) => setCloseForm({ ...closeForm, closed_date: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCloseModal(false)}>Cancel</Button>
            <Button onClick={handleCloseCase} className="bg-rose-600 hover:bg-rose-700 text-white">
              Confirm Closure
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reopen Case Dialog */}
      <Dialog open={showReopenModal} onOpenChange={setShowReopenModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Reopen Closed Case File</DialogTitle>
            <DialogDescription>
              Provide mandatory clinical rationale for reopening {caseData.case_number}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-xs font-medium text-muted-foreground">Reopening Justification *</label>
              <Textarea
                placeholder="Explain new concerns, service resumption, or follow-up requirements…"
                value={reopenForm.reopened_reason}
                onChange={(e) => setReopenForm({ ...reopenForm, reopened_reason: e.target.value })}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReopenModal(false)}>Cancel</Button>
            <Button onClick={handleReopenCase} className="bg-emerald-600 hover:bg-emerald-700 text-white">
              Reopen Case
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Record Note Dialog */}
      <Dialog open={showNoteModal} onOpenChange={setShowNoteModal}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Record Clinical Case Note</DialogTitle>
            <DialogDescription>
              Document family interaction, home visit, or case progress.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Subject / Title</label>
                <Input
                  placeholder="e.g. Home Safety Assessment"
                  value={noteForm.subject}
                  onChange={(e) => setNoteForm({ ...noteForm, subject: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Note Type</label>
                <Select value={noteForm.note_type} onValueChange={(val) => setNoteForm({ ...noteForm, note_type: val })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Progress Note">Progress Note</SelectItem>
                    <SelectItem value="Home Visit">Home Visit</SelectItem>
                    <SelectItem value="Cultural Ceremony">Cultural Ceremony</SelectItem>
                    <SelectItem value="Safety Assessment">Safety Assessment</SelectItem>
                    <SelectItem value="School Contact">School Contact</SelectItem>
                    <SelectItem value="Medical Checkup">Medical Checkup</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Contact Type</label>
                <Select value={noteForm.contact_type} onValueChange={(val) => setNoteForm({ ...noteForm, contact_type: val })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FACE_TO_FACE">Face to Face</SelectItem>
                    <SelectItem value="PHONE">Phone</SelectItem>
                    <SelectItem value="VIRTUAL">Virtual / Video</SelectItem>
                    <SelectItem value="COLLATERAL">Collateral</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Duration (Mins)</label>
                <Input
                  type="number"
                  value={noteForm.duration_minutes}
                  onChange={(e) => setNoteForm({ ...noteForm, duration_minutes: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Status</label>
                <Select value={noteForm.appointment_status} onValueChange={(val) => setNoteForm({ ...noteForm, appointment_status: val })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ATTENDED">Attended</SelectItem>
                    <SelectItem value="NO_SHOW">No Show</SelectItem>
                    <SelectItem value="CANCELLED">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground">Clinical Narrative *</label>
              <Textarea
                placeholder="Narrative summary of discussion, observations, cultural elements, and agreed action items…"
                value={noteForm.content}
                onChange={(e) => setNoteForm({ ...noteForm, content: e.target.value })}
                rows={5}
              />
            </div>

            <div className="flex items-center gap-4 pt-1">
              <label className="flex items-center gap-2 text-xs text-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={noteForm.is_well_child_checkup}
                  onChange={(e) => setNoteForm({ ...noteForm, is_well_child_checkup: e.target.checked })}
                  className="rounded"
                />
                Well-Child Checkup Completed
              </label>
              <label className="flex items-center gap-2 text-xs text-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={noteForm.notify_team}
                  onChange={(e) => setNoteForm({ ...noteForm, notify_team: e.target.checked })}
                  className="rounded"
                />
                Notify Team via Outbox
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNoteModal(false)}>Cancel</Button>
            <Button onClick={handleCreateNote}>Save Case Note</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Addendum Dialog */}
      <Dialog open={!!showAddendumModal} onOpenChange={() => setShowAddendumModal(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Append Legal Addendum</DialogTitle>
            <DialogDescription>
              Locked case notes cannot be mutated. Append an authorized clarification.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs font-medium text-muted-foreground">Reason for Addendum</label>
              <Input
                placeholder="e.g. Timeline correction or collateral clarification"
                value={addendumForm.reason}
                onChange={(e) => setAddendumForm({ ...addendumForm, reason: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Addendum Narrative *</label>
              <Textarea
                placeholder="Additional facts or corrections…"
                value={addendumForm.content}
                onChange={(e) => setAddendumForm({ ...addendumForm, content: e.target.value })}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddendumModal(null)}>Cancel</Button>
            <Button onClick={handleAddAddendum}>Append Addendum</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Launch Assessment Modal */}
      <Dialog open={showLaunchAssessmentModal} onOpenChange={setShowLaunchAssessmentModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 mb-1">
              <ClipboardList className="w-5 h-5" />
              <DialogTitle className="text-lg font-semibold">
                Launch Clinical / Safety Assessment
              </DialogTitle>
            </div>
            <DialogDescription className="text-xs text-muted-foreground">
              Select an approved, versioned assessment template to initiate a structured questionnaire for this case.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Assessment Template <span className="text-rose-500">*</span>
              </label>
              <Select
                value={launchAssessmentForm.template_key}
                onValueChange={(val) => setLaunchAssessmentForm({ ...launchAssessmentForm, template_key: val })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select template..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="HOME_ASSESSMENT">
                    Home Assessment (Residence Safety & Environment)
                  </SelectItem>
                  <SelectItem value="THREAT_ASSESSMENT">
                    Threat Assessment (Present & Impending Danger Screening)
                  </SelectItem>
                  <SelectItem value="AIEI_ASSESSMENT">
                    AIEI Assessment (Prevention, Intervention & Aftercare)
                  </SelectItem>
                  {availableTemplates
                    .filter((t) => !['HOME_ASSESSMENT', 'THREAT_ASSESSMENT', 'AIEI_ASSESSMENT'].includes(t.key))
                    .map((t) => (
                      <SelectItem key={t.key} value={t.key}>
                        {t.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Subject Person (Optional)
              </label>
              <Select
                value={launchAssessmentForm.person_id}
                onValueChange={(val) => setLaunchAssessmentForm({ ...launchAssessmentForm, person_id: val })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Whole Family / Case Unit" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Whole Family / Case Unit</SelectItem>
                  {people.map((p) => (
                    <SelectItem key={p.person_id} value={p.person_id}>
                      {p.first_name} {p.last_name} ({p.role?.replace(/_/g, ' ')})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Assessment Title / Focus (Optional)
              </label>
              <Input
                placeholder="e.g. Initial Living Condition Inspection"
                value={launchAssessmentForm.title}
                onChange={(e) => setLaunchAssessmentForm({ ...launchAssessmentForm, title: e.target.value })}
                className="mt-1 text-sm"
              />
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowLaunchAssessmentModal(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleLaunchAssessment}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium gap-1.5"
            >
              <Plus className="w-4 h-4" /> Start Questionnaire
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Case Dialog */}
      <CaseFormDialog
        open={showEdit}
        onOpenChange={setShowEdit}
        initialData={caseData}
        onSubmit={async (form) => {
          await casesApi.update(id, form);
          setShowEdit(false);
          loadAll();
        }}
      />
    </div>
  );
}
import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Clock,
  CheckCircle2,
  RotateCcw,
  RefreshCw,
  ExternalLink,
  UserCheck,
  XCircle,
  AlertTriangle,
  Eye,
  User,
  Calendar,
  MapPin,
  Phone,
  Heart,
  FileText,
  Copy,
  Check,
  Shield,
  Send,
  Users,
} from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { clientsApi } from "@/api/clients";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/use-toast";

export default function SupervisorApprovalQueue() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();

  // Active tab: 'referrals' | 'clients'
  const initialTab = searchParams.get("tab") === "clients" ? "clients" : "referrals";
  const [activeTab, setActiveTab] = useState(initialTab);

  // Sync tab with URL search parameter
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  // ── REFERRALS QUEUE STATE ───────────────────────────────────────────────────
  const [referralQueue, setReferralQueue] = useState([]);
  const [referralsLoading, setReferralsLoading] = useState(true);
  const [referralsTotal, setReferralsTotal] = useState(0);

  // Referral Action Modal
  const [activeReferral, setActiveReferral] = useState(null);
  const [referralActionType, setReferralActionType] = useState(null); // 'approve' | 'return'
  const [referralNotes, setReferralNotes] = useState("");
  const [referralExecuting, setReferralExecuting] = useState(false);

  // ── CLIENTS QUEUE STATE ─────────────────────────────────────────────────────
  const [clientQueue, setClientQueue] = useState([]);
  const [clientsLoading, setClientsLoading] = useState(true);
  const [clientsTotal, setClientsTotal] = useState(0);

  // Client Decision Modal (Approve, Return, Decline)
  const [activeClient, setActiveClient] = useState(null);
  const [clientDecisionType, setClientDecisionType] = useState(null); // 'approve' | 'return' | 'decline'
  const [clientDecisionReason, setClientDecisionReason] = useState("");
  const [clientExecuting, setClientExecuting] = useState(false);

  // Client Comprehensive Review Modal
  const [reviewClientId, setReviewClientId] = useState(null);
  const [reviewData, setReviewData] = useState(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  // ── DATA FETCHING ───────────────────────────────────────────────────────────
  const fetchReferrals = async () => {
    try {
      setReferralsLoading(true);
      const res = await referralsApi.getApprovalQueue({ page: 1, page_size: 50 });
      setReferralQueue(res.items || []);
      setReferralsTotal(res.total || 0);
    } catch (err) {
      toast({
        title: "Error loading referrals",
        description: err.message || "Failed to load referral approval queue",
        variant: "destructive",
      });
    } finally {
      setReferralsLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      setClientsLoading(true);
      const res = await clientsApi.getPendingApprovals(0, 50);
      setClientQueue(res.items || []);
      setClientsTotal(res.pagination?.total ?? res.total ?? res.items?.length ?? 0);
    } catch (err) {
      toast({
        title: "Error loading client proposals",
        description: err.message || "Failed to load pending client proposals",
        variant: "destructive",
      });
    } finally {
      setClientsLoading(false);
    }
  };

  const refreshAll = () => {
    fetchReferrals();
    fetchClients();
  };

  useEffect(() => {
    fetchReferrals();
    fetchClients();
  }, []);

  // ── REFERRAL ACTIONS ────────────────────────────────────────────────────────
  const handleExecuteReferralAction = async () => {
    if (!activeReferral) return;

    if (referralActionType === "return" && !referralNotes.trim()) {
      toast({ title: "Return comments required", variant: "destructive" });
      return;
    }

    try {
      setReferralExecuting(true);
      if (referralActionType === "approve") {
        await referralsApi.approve(activeReferral.id, {
          supervisor_notes: referralNotes || undefined,
        });
        toast({
          title: "Referral Approved",
          description: `${activeReferral.referral_number} approved and resulting cases generated.`,
        });
      } else {
        await referralsApi.returnToWorker(activeReferral.id, referralNotes.trim());
        toast({
          title: "Referral Returned",
          description: `${activeReferral.referral_number} returned to worker.`,
        });
      }

      setActiveReferral(null);
      setReferralActionType(null);
      setReferralNotes("");
      fetchReferrals();
    } catch (err) {
      toast({ title: "Action Failed", description: err.message, variant: "destructive" });
    } finally {
      setReferralExecuting(false);
    }
  };

  // ── CLIENT ACTIONS ──────────────────────────────────────────────────────────
  const openClientDecision = (client, type) => {
    setActiveClient(client);
    setClientDecisionType(type);
    setClientDecisionReason("");
  };

  const handleExecuteClientDecision = async () => {
    if (!activeClient || !clientDecisionType) return;

    if ((clientDecisionType === "return" || clientDecisionType === "decline") && !clientDecisionReason.trim()) {
      toast({
        title: "Reason Required",
        description: `Please provide a reason when ${clientDecisionType === "return" ? "returning" : "declining"} a proposal.`,
        variant: "destructive",
      });
      return;
    }

    try {
      setClientExecuting(true);
      const clientId = activeClient.client_id || activeClient.id;

      if (clientDecisionType === "approve") {
        await clientsApi.approve(clientId, clientDecisionReason.trim());
        toast({
          title: "Client Approved",
          description: `${activeClient.first_name} ${activeClient.last_name} is now an Active Client.`,
        });
      } else if (clientDecisionType === "return") {
        await clientsApi.returnProposal(clientId, clientDecisionReason.trim());
        toast({
          title: "Proposal Returned",
          description: `Proposal for ${activeClient.first_name} ${activeClient.last_name} returned for revisions. Canonical Person record preserved.`,
        });
      } else if (clientDecisionType === "decline") {
        await clientsApi.declineProposal(clientId, clientDecisionReason.trim());
        toast({
          title: "Proposal Declined",
          description: `Proposal for ${activeClient.first_name} ${activeClient.last_name} declined. Canonical Person record preserved.`,
        });
      }

      setActiveClient(null);
      setClientDecisionType(null);
      setClientDecisionReason("");
      // If review modal was open for this client, close it too
      if (reviewClientId === clientId) {
        setReviewClientId(null);
        setReviewData(null);
      }
      fetchClients();
    } catch (err) {
      toast({
        title: "Action Failed",
        description: err.message || err.detail?.error?.message || "Failed to execute decision",
        variant: "destructive",
      });
    } finally {
      setClientExecuting(false);
    }
  };

  // ── CLIENT REVIEW MODAL ─────────────────────────────────────────────────────
  const openReviewModal = async (clientId) => {
    try {
      setReviewClientId(clientId);
      setReviewLoading(true);
      const data = await clientsApi.getApprovalReview(clientId);
      setReviewData(data);
    } catch (err) {
      toast({
        title: "Failed to load dossier",
        description: err.message || "Could not retrieve client approval dossier",
        variant: "destructive",
      });
      setReviewClientId(null);
    } finally {
      setReviewLoading(false);
    }
  };

  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (tabParam === "clients" || tabParam === "referrals") {
      setActiveTab(tabParam);
    }
    const reviewId = searchParams.get("reviewId");
    if (reviewId) {
      setActiveTab("clients");
      openReviewModal(reviewId);
    }
  }, [searchParams]);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast({ title: "Copied to clipboard", description: text });
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getRiskBadge = (level) => {
    switch (level?.toLowerCase()) {
      case "high":
        return <Badge variant="destructive" className="text-[11px] font-medium">High Risk</Badge>;
      case "medium":
        return <Badge className="bg-amber-500 hover:bg-amber-600 text-white text-[11px] font-medium">Medium Risk</Badge>;
      case "low":
      default:
        return <Badge className="bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-medium">Low Risk</Badge>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-20">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-purple-100 text-purple-800 dark:bg-purple-950/50 dark:text-purple-300">
            <Clock className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-heading text-foreground">
              Supervisor Approval Queue
            </h1>
            <p className="text-xs text-muted-foreground">
              Multi-disciplinary intake screening decisions and pending Client proposal authorizations
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={refreshAll} className="gap-1.5 text-xs">
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Queue</span>
          </Button>
        </div>
      </div>

      {/* Primary Tab Switcher */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <div className="flex items-center justify-between border-b pb-1">
          <TabsList className="bg-muted/60 p-1">
            <TabsTrigger value="referrals" className="text-xs gap-2 font-medium">
              <span>Referral Screenings</span>
              <Badge variant={referralsTotal > 0 ? "secondary" : "outline"} className="text-[10px] px-1.5 py-0 font-mono">
                {referralsTotal}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="clients" className="text-xs gap-2 font-medium">
              <span>Client Proposals</span>
              <Badge variant={clientsTotal > 0 ? "destructive" : "outline"} className="text-[10px] px-1.5 py-0 font-mono">
                {clientsTotal}
              </Badge>
            </TabsTrigger>
          </TabsList>

          <span className="text-xs text-muted-foreground hidden sm:inline">
            Supervisory review authority required for formal status transitions
          </span>
        </div>

        {/* ══════════════════════════════════════════════════════════════════════ */}
        {/* TAB 1: REFERRAL SCREENINGS                                            */}
        {/* ══════════════════════════════════════════════════════════════════════ */}
        <TabsContent value="referrals" className="space-y-4 pt-3">
          <Card className="border shadow-sm overflow-hidden">
            <CardHeader className="bg-muted/20 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold">
                  Pending Referrals Requiring Supervisory Action ({referralsTotal})
                </CardTitle>
                <Badge className="bg-purple-600 text-white text-xs">{referralsTotal} Pending</Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-muted/50 text-muted-foreground border-b font-semibold uppercase">
                    <tr>
                      <th className="px-4 py-3">Referral #</th>
                      <th className="px-4 py-3">Received Date</th>
                      <th className="px-4 py-3">Priority</th>
                      <th className="px-4 py-3">Primary Concern</th>
                      <th className="px-4 py-3">Children</th>
                      <th className="px-4 py-3">Assigned Worker</th>
                      <th className="px-4 py-3 text-right">Supervisory Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {referralsLoading ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                          Loading referral queue...
                        </td>
                      </tr>
                    ) : referralQueue.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                          <CheckCircle2 className="w-10 h-10 mx-auto mb-3 text-emerald-500 opacity-60" />
                          <p className="font-medium text-foreground">Referral Queue Clean</p>
                          <p className="text-xs text-muted-foreground mt-1">There are currently no referrals awaiting supervisor review.</p>
                        </td>
                      </tr>
                    ) : (
                      referralQueue.map((ref) => (
                        <tr key={ref.id} className="hover:bg-muted/20 transition-colors">
                          <td className="px-4 py-3.5 font-bold font-mono text-primary">
                            {ref.referral_number}
                          </td>

                          <td className="px-4 py-3.5 text-muted-foreground whitespace-nowrap">
                            {ref.received_date}
                          </td>

                          <td className="px-4 py-3.5 whitespace-nowrap">
                            <Badge variant={ref.priority === "Crisis" ? "destructive" : "default"} className="text-[10px]">
                              {ref.priority}
                            </Badge>
                          </td>

                          <td className="px-4 py-3.5 max-w-xs truncate font-medium">
                            {ref.primary_concern?.replace(/_/g, " ") || ref.summary || "General Intake"}
                          </td>

                          <td className="px-4 py-3.5 whitespace-nowrap">
                            <Badge variant="outline" className="text-[10px] bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                              {ref.children_count || 0} child(ren)
                            </Badge>
                          </td>

                          <td className="px-4 py-3.5 text-muted-foreground">
                            {ref.assigned_worker_name || "Unassigned"}
                          </td>

                          <td className="px-4 py-3.5 text-right whitespace-nowrap space-x-1.5">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs text-muted-foreground hover:text-foreground"
                              onClick={() => navigate(`/intake/${ref.id}/decision`)}
                            >
                              <span>Review</span>
                              <ExternalLink className="w-3 h-3 ml-1" />
                            </Button>

                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs text-rose-700 border-rose-200 hover:bg-rose-50 dark:text-rose-400 dark:border-rose-900"
                              onClick={() => {
                                setActiveReferral(ref);
                                setReferralActionType("return");
                                setReferralNotes("");
                              }}
                            >
                              <RotateCcw className="w-3 h-3 mr-1" />
                              <span>Return</span>
                            </Button>

                            <Button
                              size="sm"
                              className="h-7 text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                              onClick={() => {
                                setActiveReferral(ref);
                                setReferralActionType("approve");
                                setReferralNotes("");
                              }}
                            >
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              <span>Approve</span>
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ══════════════════════════════════════════════════════════════════════ */}
        {/* TAB 2: CLIENT PROPOSALS                                               */}
        {/* ══════════════════════════════════════════════════════════════════════ */}
        <TabsContent value="clients" className="space-y-4 pt-3">
          <Card className="border shadow-sm overflow-hidden">
            <CardHeader className="bg-muted/20 pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-bold">
                    Pending Client Proposals Awaiting Supervisor Decision ({clientsTotal})
                  </CardTitle>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Search-before-create proposals submitted by caseworkers. Review canonical Person identity and authorize client enrollment.
                  </p>
                </div>
                <Badge className="bg-amber-600 hover:bg-amber-700 text-white text-xs">
                  {clientsTotal} Awaiting Sign-off
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              {clientsLoading ? (
                <div className="py-16 text-center text-muted-foreground">
                  <div className="w-7 h-7 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                  <p className="text-xs">Loading pending client proposals...</p>
                </div>
              ) : clientQueue.length === 0 ? (
                <div className="py-16 text-center text-muted-foreground space-y-2">
                  <CheckCircle2 className="w-12 h-12 mx-auto text-emerald-500 opacity-70" />
                  <p className="font-semibold text-foreground text-sm">No Pending Client Proposals</p>
                  <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                    All submitted client proposals have been reviewed, returned, or approved by supervisors.
                  </p>
                </div>
              ) : (
                <div className="divide-y">
                  {clientQueue.map((item) => (
                    <div
                      key={item.client_id}
                      className="p-4 hover:bg-muted/25 transition-colors flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                    >
                      {/* Left: Photo & Person Identity */}
                      <div className="flex items-start gap-3.5">
                        <Avatar className="h-12 w-12 border shadow-sm shrink-0">
                          <AvatarImage src={item.person_profile_photo_url} alt={item.first_name} />
                          <AvatarFallback className="font-bold text-sm bg-primary/10 text-primary">
                            {item.first_name?.[0]}{item.last_name?.[0]}
                          </AvatarFallback>
                        </Avatar>

                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-bold text-base text-foreground">
                              {item.first_name} {item.last_name}
                            </span>
                            <button
                              onClick={() => copyToClipboard(item.person_id_number, item.client_id)}
                              className="inline-flex items-center gap-1 font-mono text-xs px-2 py-0.5 rounded bg-muted hover:bg-muted/80 text-muted-foreground border transition"
                              title="Copy permanent CRBCL ID"
                            >
                              <span>#{item.person_id_number}</span>
                              {copiedId === item.client_id ? (
                                <Check className="w-3 h-3 text-emerald-600" />
                              ) : (
                                <Copy className="w-3 h-3 text-muted-foreground" />
                              )}
                            </button>
                            {getRiskBadge(item.risk_level)}
                            <Badge variant="outline" className="text-[11px] bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30">
                              PENDING APPROVAL
                            </Badge>
                          </div>

                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                            <span>DOB: <strong className="font-medium text-foreground">{item.date_of_birth || "Unknown"}</strong></span>
                            <span>•</span>
                            <span>Submitted by: <strong className="font-medium text-foreground">{item.submitted_by_name || "Caseworker"}</strong></span>
                            <span>•</span>
                            <span>
                              {item.submitted_at ? new Date(item.submitted_at).toLocaleDateString(undefined, {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              }) : "Recently"}
                            </span>
                          </div>

                          {item.submission_notes && (
                            <p className="text-xs text-muted-foreground/90 italic line-clamp-2 mt-1 bg-muted/30 p-2 rounded border border-muted-foreground/10">
                              "{item.submission_notes}"
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Right: Actions */}
                      <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 text-xs gap-1.5"
                          onClick={() => openReviewModal(item.client_id)}
                        >
                          <Eye className="w-3.5 h-3.5 text-primary" />
                          <span>Review Dossier</span>
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 text-xs text-rose-700 border-rose-200 hover:bg-rose-50 dark:text-rose-400 dark:border-rose-900 gap-1"
                          onClick={() => openClientDecision(item, "return")}
                        >
                          <RotateCcw className="w-3.5 h-3.5 mr-0.5" />
                          <span>Return</span>
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 text-xs text-destructive border-destructive/30 hover:bg-destructive/10 gap-1"
                          onClick={() => openClientDecision(item, "decline")}
                        >
                          <XCircle className="w-3.5 h-3.5 mr-0.5" />
                          <span>Decline</span>
                        </Button>

                        <Button
                          size="sm"
                          className="h-8 text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm gap-1"
                          onClick={() => openClientDecision(item, "approve")}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 mr-0.5" />
                          <span>Approve</span>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* ══════════════════════════════════════════════════════════════════════ */}
      {/* REFERRAL QUICK ACTION DIALOG                                           */}
      {/* ══════════════════════════════════════════════════════════════════════ */}
      <Dialog open={!!activeReferral} onOpenChange={(open) => !open && setActiveReferral(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {referralActionType === "approve" ? "Approve Intake Referral & Open Cases" : "Return Referral to Worker"}
            </DialogTitle>
            <DialogDescription className="text-xs">
              {referralActionType === "approve"
                ? `Confirming will approve referral ${activeReferral?.referral_number} and immediately generate corresponding Child Protection or Prevention cases.`
                : `Specify mandatory revision comments explaining what updates are required for ${activeReferral?.referral_number}.`}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            <Label className="text-xs font-semibold">
              {referralActionType === "approve" ? "Supervisor Notes (Optional)" : "Return Reason / Revision Instructions *"}
            </Label>
            <Textarea
              rows={3}
              placeholder={referralActionType === "approve" ? "Supervisory notes..." : "Enter details on required revisions..."}
              value={referralNotes}
              onChange={(e) => setReferralNotes(e.target.value)}
              required={referralActionType === "return"}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setActiveReferral(null)}>Cancel</Button>
            <Button
              className={referralActionType === "approve" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : "bg-destructive text-destructive-foreground"}
              onClick={handleExecuteReferralAction}
              disabled={referralExecuting}
            >
              {referralActionType === "approve" ? "Execute Approval" : "Return to Worker"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ══════════════════════════════════════════════════════════════════════ */}
      {/* CLIENT DECISION CONFIRMATION DIALOG (Approve, Return, Decline)        */}
      {/* ══════════════════════════════════════════════════════════════════════ */}
      <Dialog open={!!activeClient && !!clientDecisionType} onOpenChange={(open) => !open && setActiveClient(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {clientDecisionType === "approve" && (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <span>Approve Client Proposal</span>
                </>
              )}
              {clientDecisionType === "return" && (
                <>
                  <RotateCcw className="w-5 h-5 text-amber-600" />
                  <span>Return Proposal for Revisions</span>
                </>
              )}
              {clientDecisionType === "decline" && (
                <>
                  <XCircle className="w-5 h-5 text-destructive" />
                  <span>Decline Client Proposal</span>
                </>
              )}
            </DialogTitle>
            <DialogDescription className="text-xs">
              Target Client: <strong>{activeClient?.first_name} {activeClient?.last_name}</strong> (CRBCL ID: #{activeClient?.person_id_number})
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            {clientDecisionType === "approve" && (
              <p className="text-xs text-muted-foreground">
                Authorizing will transition this record to <strong>Active Client</strong> status, granting caseworker operational access to enroll services and case management.
              </p>
            )}

            {(clientDecisionType === "return" || clientDecisionType === "decline") && (
              <div className="p-3 rounded-lg bg-muted/40 border text-xs text-muted-foreground space-y-1">
                <p>
                  <strong>Data Preservation Guarantee:</strong> The canonical Person record and permanent ID #{activeClient?.person_id_number} will remain safely intact.
                </p>
                <p>
                  {clientDecisionType === "return"
                    ? "The caseworker can revise submission notes or attributes and re-submit."
                    : "The client record will be marked DECLINED. A future proposal can re-use this Person."}
                </p>
              </div>
            )}

            <div className="space-y-1.5">
              <Label className="text-xs font-semibold">
                {clientDecisionType === "approve" ? "Supervisory Notes / Directives (Optional)" : "Reason / Specific Instructions *"}
              </Label>
              <Textarea
                rows={3}
                placeholder={
                  clientDecisionType === "approve"
                    ? "Optional directives, service allocation notes..."
                    : "Specify the exact reason or instructions for the caseworker..."
                }
                value={clientDecisionReason}
                onChange={(e) => setClientDecisionReason(e.target.value)}
                required={clientDecisionType !== "approve"}
                autoFocus
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setActiveClient(null)}>Cancel</Button>
            <Button
              className={
                clientDecisionType === "approve"
                  ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                  : clientDecisionType === "return"
                  ? "bg-amber-600 hover:bg-amber-700 text-white"
                  : "bg-destructive text-destructive-foreground"
              }
              onClick={handleExecuteClientDecision}
              disabled={clientExecuting || (clientDecisionType !== "approve" && !clientDecisionReason.trim())}
            >
              {clientExecuting ? (
                <span>Executing...</span>
              ) : clientDecisionType === "approve" ? (
                "Authorize & Approve"
              ) : clientDecisionType === "return" ? (
                "Return to Caseworker"
              ) : (
                "Confirm Decline"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ══════════════════════════════════════════════════════════════════════ */}
      {/* COMPREHENSIVE CLIENT REVIEW DOSSIER MODAL                             */}
      {/* ══════════════════════════════════════════════════════════════════════ */}
      <Dialog open={!!reviewClientId} onOpenChange={(open) => !open && setReviewClientId(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {reviewLoading || !reviewData ? (
            <div className="py-20 text-center text-muted-foreground">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm">Loading comprehensive client review dossier...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Dossier Header */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-muted/30 border">
                <div className="flex items-center gap-4">
                  <Avatar className="h-16 w-16 border-2 shadow-sm">
                    <AvatarImage src={reviewData.client?.person_profile_photo_url} />
                    <AvatarFallback className="text-lg font-bold bg-primary/10 text-primary">
                      {reviewData.person?.first_name?.[0]}{reviewData.person?.last_name?.[0]}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-xl font-bold text-foreground">
                        {reviewData.person?.first_name} {reviewData.person?.middle_name ? `${reviewData.person.middle_name} ` : ""}{reviewData.person?.last_name}
                      </h2>
                      {reviewData.person?.preferred_name && (
                        <span className="text-sm text-muted-foreground">("{reviewData.person.preferred_name}")</span>
                      )}
                      <Badge variant="outline" className="font-mono text-xs bg-muted">
                        ID: #{reviewData.person?.person_id_number}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground mt-1">
                      <span>DOB: <strong>{reviewData.person?.date_of_birth || "Unknown"}</strong></span>
                      <span>•</span>
                      <span>Gender: <strong>{reviewData.person?.gender || "Not specified"}</strong></span>
                      <span>•</span>
                      <span>Nation: <strong>{reviewData.person?.band_nation || "Not recorded"}</strong></span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-start sm:items-end gap-1.5">
                  <Badge className="bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30 text-xs">
                    {reviewData.client?.approval_status || "PENDING_APPROVAL"}
                  </Badge>
                  <span className="text-[11px] text-muted-foreground">
                    Initial Risk: <strong>{reviewData.client?.risk_level || "Low"}</strong>
                  </span>
                </div>
              </div>

              {/* Dossier Tabs */}
              <Tabs defaultValue="overview" className="w-full">
                <TabsList className="grid grid-cols-4 w-full text-xs">
                  <TabsTrigger value="overview" className="text-xs">Identity & Contact</TabsTrigger>
                  <TabsTrigger value="physical" className="text-xs">Physical & Cultural</TabsTrigger>
                  <TabsTrigger value="clinical" className="text-xs">Clinical & Medical</TabsTrigger>
                  <TabsTrigger value="history" className="text-xs">
                    Audit Trail ({reviewData.approval_history?.length || 0})
                  </TabsTrigger>
                </TabsList>

                {/* TAB 1: IDENTITY & CONTACT */}
                <TabsContent value="overview" className="space-y-4 pt-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Legal Identity Card */}
                    <Card className="border">
                      <CardHeader className="p-3.5 bg-muted/20 border-b">
                        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                          <User className="w-3.5 h-3.5 text-primary" />
                          Canonical Human Identity
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-3.5 text-xs space-y-2">
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">Permanent CRBCL ID:</span>
                          <span className="font-mono font-bold">#{reviewData.person?.person_id_number}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">Legal Full Name:</span>
                          <span className="font-medium">{reviewData.person?.first_name} {reviewData.person?.last_name}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">Aliases / Previous:</span>
                          <span>{reviewData.person?.aliases || "None"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">Date of Birth:</span>
                          <span>{reviewData.person?.date_of_birth || "N/A"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">Treaty / Status #:</span>
                          <span>{reviewData.person?.treaty_number || "None"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">SK Health Card (HSN):</span>
                          <span>{reviewData.person?.health_card_number || "None"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Indigenous Identity:</span>
                          <span>{reviewData.person?.indigenous_identity || "Not stated"}</span>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Contact & Residential Card */}
                    <Card className="border">
                      <CardHeader className="p-3.5 bg-muted/20 border-b">
                        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 text-primary" />
                          Contact & Residential Context
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-3.5 text-xs space-y-2">
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">Primary Phone:</span>
                          <span>{reviewData.person?.phone || "None"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">Email:</span>
                          <span>{reviewData.person?.email || "None"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">Street Address:</span>
                          <span>{reviewData.person?.addresses?.[0]?.address_line_1 || reviewData.client?.address || "None"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">City & Province:</span>
                          <span>
                            {(reviewData.person?.addresses?.[0]?.city || reviewData.client?.city || "Regina")},{" "}
                            {(reviewData.person?.addresses?.[0]?.province || reviewData.client?.province || "SK")}
                          </span>
                        </div>
                        <div className="flex justify-between border-b pb-1.5">
                          <span className="text-muted-foreground">On-Reserve:</span>
                          <span>
                            {reviewData.person?.addresses?.[0]?.on_reserve ? (
                              <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-700">Yes</Badge>
                            ) : "No"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Emergency Contact:</span>
                          <span>
                            {reviewData.person?.emergency_contact_name
                              ? `${reviewData.person.emergency_contact_name} (${reviewData.person.emergency_contact_phone || "No phone"})`
                              : "None recorded"}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Proposal Submission Notes */}
                  <Card className="border bg-primary/5 border-primary/20">
                    <CardHeader className="p-3.5 border-b">
                      <CardTitle className="text-xs font-semibold uppercase tracking-wider text-primary flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        Proposal Submission Rationale
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-3.5 text-xs space-y-2">
                      <p className="text-foreground leading-relaxed whitespace-pre-wrap">
                        {reviewData.client?.submission_notes || "No submission rationale notes provided."}
                      </p>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* TAB 2: PHYSICAL & CULTURAL */}
                <TabsContent value="physical" className="space-y-4 pt-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Physical Identifiers */}
                    <Card className="border">
                      <CardHeader className="p-3.5 bg-muted/20 border-b">
                        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          Physical Identification
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-3.5 text-xs space-y-2">
                        <div className="grid grid-cols-2 gap-2 border-b pb-2">
                          <div>
                            <span className="text-muted-foreground block">Eye Colour:</span>
                            <span className="font-medium">{reviewData.person?.physical_description?.eye_colour || "Not stated"}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground block">Hair Colour:</span>
                            <span className="font-medium">{reviewData.person?.physical_description?.hair_colour || "Not stated"}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground block">Height:</span>
                            <span>{reviewData.person?.physical_description?.height_cm ? `${reviewData.person.physical_description.height_cm} cm` : "N/A"}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground block">Weight:</span>
                            <span>{reviewData.person?.physical_description?.weight_kg ? `${reviewData.person.physical_description.weight_kg} kg` : "N/A"}</span>
                          </div>
                        </div>
                        <div className="space-y-1 pt-1">
                          <span className="text-muted-foreground block">Scars / Birthmarks:</span>
                          <span className="text-foreground">
                            {[reviewData.person?.physical_description?.scars, reviewData.person?.physical_description?.birthmarks]
                              .filter(Boolean)
                              .join("; ") || "None recorded"}
                          </span>
                        </div>
                        <div className="space-y-1 pt-1">
                          <span className="text-muted-foreground block">Tattoos / Piercings:</span>
                          <span className="text-foreground">
                            {[reviewData.person?.physical_description?.tattoos, reviewData.person?.physical_description?.piercings]
                              .filter(Boolean)
                              .join("; ") || "None recorded"}
                          </span>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Cultural Profile */}
                    <Card className="border">
                      <CardHeader className="p-3.5 bg-muted/20 border-b">
                        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          Cultural & Community Connections
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-3.5 text-xs space-y-2">
                        <div className="space-y-1 border-b pb-2">
                          <span className="text-muted-foreground block">Cultural / Clan Connections:</span>
                          <span>{reviewData.person?.cultural_profile?.cultural_connections || "Not recorded"}</span>
                        </div>
                        <div className="space-y-1 border-b pb-2">
                          <span className="text-muted-foreground block">Ceremonies & Protocols:</span>
                          <span>{reviewData.person?.cultural_profile?.ceremonies || "Not recorded"}</span>
                        </div>
                        <div className="space-y-1 border-b pb-2">
                          <span className="text-muted-foreground block">Elders Connected:</span>
                          <span>{reviewData.person?.cultural_profile?.elders_connected || "Not recorded"}</span>
                        </div>
                        <div className="space-y-1">
                          <span className="text-muted-foreground block">Dietary & Extracurricular:</span>
                          <span>
                            {[reviewData.person?.cultural_profile?.dietary_preferences, reviewData.person?.cultural_profile?.extracurricular_activities]
                              .filter(Boolean)
                              .join("; ") || "Not recorded"}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* TAB 3: CLINICAL & MEDICAL */}
                <TabsContent value="clinical" className="space-y-4 pt-3">
                  <Card className="border">
                    <CardHeader className="p-3.5 bg-muted/20 border-b">
                      <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                        <Shield className="w-3.5 h-3.5 text-primary" />
                        Clinical & Health Information Privacy Boundary
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 text-xs space-y-3">
                      {reviewData.person?.medical_profile ? (
                        <div className="space-y-3">
                          <div className="p-2.5 rounded bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2">
                            <Shield className="w-4 h-4 text-emerald-600 shrink-0" />
                            <span>Authorized clinical profile view enabled for supervisory staff.</span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                            <div className="border p-2.5 rounded">
                              <span className="font-semibold block mb-1">Medical Conditions:</span>
                              <p className="text-muted-foreground">
                                {reviewData.person.medical_profile.conditions || "None declared at intake."}
                              </p>
                            </div>
                            <div className="border p-2.5 rounded">
                              <span className="font-semibold block mb-1">Known Allergies:</span>
                              <p className="text-muted-foreground">
                                {reviewData.person.medical_profile.allergies || "None declared."}
                              </p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="p-6 text-center text-muted-foreground space-y-2">
                          <Shield className="w-8 h-8 mx-auto text-primary/60" />
                          <p className="font-semibold text-foreground">Health Confidentiality Protected</p>
                          <p className="text-xs max-w-md mx-auto">
                            Detailed medical, clinical, and psychiatric records are maintained separately under statutory privacy boundaries and accessible only by credentialed clinical officers.
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* TAB 4: AUDIT TRAIL */}
                <TabsContent value="history" className="space-y-3 pt-3">
                  <Card className="border">
                    <CardHeader className="p-3.5 bg-muted/20 border-b">
                      <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Append-Only Approval History & Governance Audit Trail
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4">
                      {reviewData.approval_history?.length === 0 ? (
                        <p className="text-xs text-muted-foreground text-center py-6">
                          Initial submission pending. No previous approval actions recorded.
                        </p>
                      ) : (
                        <div className="relative pl-6 border-l space-y-4">
                          {reviewData.approval_history?.map((h) => (
                            <div key={h.id} className="relative">
                              <div className="absolute -left-[31px] top-0.5 w-3.5 h-3.5 rounded-full bg-primary border-2 border-background" />
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="text-[10px] font-semibold">
                                  {h.action}
                                </Badge>
                                <span className="text-xs font-medium text-foreground">
                                  by {h.actor_name || "System"}
                                </span>
                                <span className="text-[11px] text-muted-foreground">
                                  {new Date(h.created_at).toLocaleString()}
                                </span>
                              </div>
                              {h.notes && (
                                <p className="text-xs text-muted-foreground mt-1 bg-muted/30 p-2 rounded border">
                                  "{h.notes}"
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>

              {/* Action Footer in Dossier Modal */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t pt-4">
                <Button variant="outline" size="sm" onClick={() => setReviewClientId(null)}>
                  Close Dossier
                </Button>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-rose-700 border-rose-200 hover:bg-rose-50 dark:text-rose-400 dark:border-rose-900"
                    onClick={() => {
                      const item = {
                        client_id: reviewData.client?.id,
                        first_name: reviewData.person?.first_name,
                        last_name: reviewData.person?.last_name,
                        person_id_number: reviewData.person?.person_id_number,
                      };
                      openClientDecision(item, "return");
                    }}
                  >
                    <RotateCcw className="w-3.5 h-3.5 mr-1" />
                    Return with Instructions
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    className="text-destructive border-destructive/30 hover:bg-destructive/10"
                    onClick={() => {
                      const item = {
                        client_id: reviewData.client?.id,
                        first_name: reviewData.person?.first_name,
                        last_name: reviewData.person?.last_name,
                        person_id_number: reviewData.person?.person_id_number,
                      };
                      openClientDecision(item, "decline");
                    }}
                  >
                    <XCircle className="w-3.5 h-3.5 mr-1" />
                    Decline
                  </Button>

                  <Button
                    size="sm"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                    onClick={() => {
                      const item = {
                        client_id: reviewData.client?.id,
                        first_name: reviewData.person?.first_name,
                        last_name: reviewData.person?.last_name,
                        person_id_number: reviewData.person?.person_id_number,
                      };
                      openClientDecision(item, "approve");
                    }}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                    Authorize & Approve Client
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

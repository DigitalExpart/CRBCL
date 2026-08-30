import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  Inbox, ArrowLeft, Shield, AlertTriangle, CheckCircle, Clock,
  User, Users, Phone, Building, FileText, Lock, Link as LinkIcon,
  ExternalLink, ChevronRight, Edit3, Send, AlertCircle, History, Sparkles
} from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";

const STATUS_BADGES = {
  DRAFT: { label: "Draft", bg: "bg-slate-100 text-slate-800 border-slate-300" },
  RECEIVED: { label: "Received", bg: "bg-blue-100 text-blue-800 border-blue-300" },
  IN_PROGRESS: { label: "In Progress", bg: "bg-amber-100 text-amber-800 border-amber-300" },
  PENDING_SUPERVISOR: { label: "Pending Supervisor Approval", bg: "bg-purple-100 text-purple-800 border-purple-300 font-semibold" },
  APPROVED: { label: "Approved & Routed", bg: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  RETURNED: { label: "Returned for Revision", bg: "bg-rose-100 text-rose-800 border-rose-300" },
  SCREENED_OUT: { label: "Screened Out", bg: "bg-gray-100 text-gray-700 border-gray-300" },
  REFERRED_EXTERNALLY: { label: "Referred Externally", bg: "bg-cyan-100 text-cyan-800 border-cyan-300" },
};

const DISPOSITION_BADGES = {
  PROTECTION: { label: "Child Protection Investigation", bg: "bg-red-100 text-red-800 border-red-300" },
  PREVENTION: { label: "Family Prevention & Wellness", bg: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  POST_MAJORITY: { label: "Post-Majority Support", bg: "bg-indigo-100 text-indigo-800 border-indigo-300" },
  SCREEN_OUT: { label: "Screen Out", bg: "bg-gray-100 text-gray-700 border-gray-300" },
  EXTERNAL_REFERRAL: { label: "External Agency Referral", bg: "bg-blue-100 text-blue-800 border-blue-300" },
};

export default function IntakeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [referral, setReferral] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [linkModalOpen, setLinkModalOpen] = useState(false);
  const [targetReferralId, setTargetReferralId] = useState("");
  const [linkType, setLinkType] = useState("related_incident");
  const [linkReason, setLinkReason] = useState("");

  const fetchReferral = async () => {
    try {
      setLoading(true);
      const data = await referralsApi.get(id);
      setReferral(data);

      // Fetch prior history discovery
      referralsApi.getPriorHistory(id)
        .then(hist => setHistoryData(hist))
        .catch(() => {});
    } catch (err) {
      toast({
        title: "Error loading referral",
        description: err.message || "Failed to load intake record",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReferral();
  }, [id]);

  const handleCreateLink = async () => {
    if (!targetReferralId) {
      toast({ title: "Target Referral ID required", variant: "destructive" });
      return;
    }
    try {
      await referralsApi.createLink(id, {
        target_referral_id: targetReferralId,
        link_type: linkType,
        reason: linkReason || undefined,
      });
      toast({ title: "Referral Linked", description: "Cross-referral relationship registered successfully." });
      setLinkModalOpen(false);
      setTargetReferralId("");
      setLinkReason("");
      fetchReferral();
    } catch (err) {
      toast({ title: "Link Failed", description: err.message, variant: "destructive" });
    }
  };

  if (loading || !referral) {
    return (
      <div className="max-w-6xl mx-auto py-12 text-center text-muted-foreground">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading Intake Referral 360° Record...
      </div>
    );
  }

  const statusBadge = STATUS_BADGES[referral.status] || { label: referral.status, bg: "bg-gray-100" };
  const canEditDecision = ["DRAFT", "IN_PROGRESS", "RETURNED", "PENDING_SUPERVISOR"].includes(referral.status);

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Header Breadcrumb & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/intake")}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold font-mono text-foreground">{referral.referral_number}</h1>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${statusBadge.bg}`}>
                {statusBadge.label}
              </span>
              <Badge className="bg-slate-700 text-white text-xs">{referral.priority} Priority</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Received {referral.received_date} via {referral.received_method} • Community: {referral.community || "Unspecified"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Dialog open={linkModalOpen} onOpenChange={setLinkModalOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                <LinkIcon className="w-3.5 h-3.5" />
                <span>Link Referral</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Link Cross-Referral Record</DialogTitle>
              </DialogHeader>
              <div className="space-y-3 py-2">
                <div className="space-y-1">
                  <Label className="text-xs">Target Referral UUID</Label>
                  <Input
                    placeholder="Enter Referral UUID to link..."
                    value={targetReferralId}
                    onChange={(e) => setTargetReferralId(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Relationship Type</Label>
                  <Select value={linkType} onValueChange={setLinkType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="duplicate_report">Duplicate / Secondary Report</SelectItem>
                      <SelectItem value="related_incident">Related Incident / Concurrent Referral</SelectItem>
                      <SelectItem value="prior_history">Prior Intake History</SelectItem>
                      <SelectItem value="split_family">Cross-Household / Sibling Connection</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Clinical Reason</Label>
                  <Input
                    placeholder="Reason for linking these intakes..."
                    value={linkReason}
                    onChange={(e) => setLinkReason(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setLinkModalOpen(false)}>Cancel</Button>
                <Button onClick={handleCreateLink}>Create Link</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {canEditDecision && (
            <Button
              onClick={() => navigate(`/intake/${referral.id}/decision`)}
              className="bg-primary hover:bg-primary/90 text-primary-foreground gap-1.5 text-xs shadow-sm"
            >
              {referral.status === "PENDING_SUPERVISOR" ? (
                <>
                  <Shield className="w-3.5 h-3.5" />
                  <span>Supervisor Review & Decision</span>
                </>
              ) : (
                <>
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>Dispositions & Submit</span>
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Return Warning Banner if returned */}
      {referral.status === "RETURNED" && referral.decision?.return_reason && (
        <Card className="border-rose-300 bg-rose-50/80">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-rose-900">Returned by Supervisor for Revision</h4>
              <p className="text-xs text-rose-800 mt-1 font-medium">Comments: {referral.decision.return_reason}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 360° Tabbed Detail View */}
      <Tabs defaultValue="overview" className="w-full space-y-4">
        <TabsList className="grid grid-cols-2 sm:grid-cols-5 w-full bg-muted/60 p-1">
          <TabsTrigger value="overview" className="text-xs">Overview & Details</TabsTrigger>
          <TabsTrigger value="people" className="text-xs">Involved People ({referral.people?.length || 0})</TabsTrigger>
          <TabsTrigger value="concerns" className="text-xs">Concerns & Incidents</TabsTrigger>
          <TabsTrigger value="dispositions" className="text-xs">Child Dispositions ({referral.dispositions?.length || 0})</TabsTrigger>
          <TabsTrigger value="history" className="text-xs">Prior History Discovery</TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="md:col-span-2 border shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <FileText className="w-4 h-4 text-primary" />
                  <span>Intake Narrative Summary</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="p-3.5 bg-muted/20 rounded-lg border text-foreground leading-relaxed">
                  {referral.summary || "No summary provided."}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 text-xs">
                  <div>
                    <span className="text-muted-foreground block">Received Channel:</span>
                    <span className="font-semibold capitalize">{referral.received_method}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Risk Level:</span>
                    <span className="font-semibold">{referral.risk_level || "Standard"}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Community:</span>
                    <span className="font-semibold">{referral.community || "Unspecified"}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Confidential Reporter Card */}
            <Card className="border shadow-sm border-amber-200/60 bg-amber-50/10">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold flex items-center justify-between">
                  <div className="flex items-center gap-2 text-amber-900">
                    <Lock className="w-4 h-4 text-amber-600" />
                    <span>Reporter Record</span>
                  </div>
                  <Badge variant="outline" className="text-[10px] bg-amber-100 text-amber-900">
                    Confidential
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5 text-xs">
                {referral.reporter ? (
                  <>
                    <div>
                      <span className="text-muted-foreground block">Reporter Name:</span>
                      <span className="font-semibold">{referral.reporter.reporter_name || "[ANONYMOUS]"}</span>
                    </div>
                    {referral.reporter.organization && (
                      <div>
                        <span className="text-muted-foreground block">Organization:</span>
                        <span>{referral.reporter.organization}</span>
                      </div>
                    )}
                    {referral.reporter.phone && (
                      <div>
                        <span className="text-muted-foreground block">Phone:</span>
                        <span>{referral.reporter.phone}</span>
                      </div>
                    )}
                    {referral.reporter.relationship_to_family && (
                      <div>
                        <span className="text-muted-foreground block">Relationship:</span>
                        <span>{referral.reporter.relationship_to_family}</span>
                      </div>
                    )}
                    <div className="pt-2 border-t flex items-center gap-2">
                      {referral.reporter.is_mandated_reporter && (
                        <Badge variant="secondary" className="text-[10px]">Mandated Reporter</Badge>
                      )}
                      {referral.reporter.is_anonymous && (
                        <Badge variant="outline" className="text-[10px]">Anonymous</Badge>
                      )}
                    </div>
                  </>
                ) : (
                  <p className="text-muted-foreground italic">No reporter recorded.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Links Section */}
          {referral.links && referral.links.length > 0 && (
            <Card className="border shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <LinkIcon className="w-4 h-4 text-primary" />
                  <span>Linked Intakes & Concurrent Incidents</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="divide-y text-xs">
                  {referral.links.map((lk) => (
                    <div key={lk.id} className="py-2.5 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-[11px]">
                          {lk.target_referral_number || lk.target_referral_id}
                        </Badge>
                        <span className="capitalize font-medium text-muted-foreground">({lk.link_type.replace(/_/g, ' ')})</span>
                        {lk.reason && <span className="text-foreground">— {lk.reason}</span>}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-primary"
                        onClick={() => navigate(`/intake/${lk.target_referral_id}`)}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab 2: Involved People */}
        <TabsContent value="people" className="space-y-4">
          <Card className="border shadow-sm">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-muted/50 text-muted-foreground border-b font-medium">
                    <tr>
                      <th className="px-4 py-3">Full Name</th>
                      <th className="px-4 py-3">Role</th>
                      <th className="px-4 py-3">Birth Date / Age</th>
                      <th className="px-4 py-3">Nation / Band</th>
                      <th className="px-4 py-3">Primary Caregiver</th>
                      <th className="px-4 py-3 text-right">Client Record</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {referral.people?.map((rp) => (
                      <tr key={rp.id} className="hover:bg-muted/10">
                        <td className="px-4 py-3 font-semibold text-foreground">
                          {rp.first_name} {rp.last_name}
                        </td>
                        <td className="px-4 py-3 capitalize">
                          <Badge variant={rp.role === "child" ? "default" : "secondary"} className="text-[10px]">
                            {rp.role.replace(/_/g, ' ')}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{rp.date_of_birth || "—"}</td>
                        <td className="px-4 py-3">{rp.band_nation || rp.indigenous_identity || "—"}</td>
                        <td className="px-4 py-3">{rp.is_primary_caregiver ? "Yes" : "No"}</td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-primary"
                            onClick={() => navigate(`/clients/${rp.person_id}`)}
                          >
                            View Client
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Concerns & Incidents */}
        <TabsContent value="concerns" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold">Structured Concerns</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5 text-xs">
                {referral.concerns?.map((c) => (
                  <div key={c.id} className="p-3 border rounded-lg bg-muted/20 flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold capitalize">{c.concern_type.replace(/_/g, ' ')}</span>
                        {c.is_primary && <Badge className="bg-amber-600 text-white text-[10px]">Primary</Badge>}
                      </div>
                      {c.description && <p className="text-muted-foreground mt-1">{c.description}</p>}
                    </div>
                    <Badge variant="outline" className="text-[10px]">{c.severity}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold">Incident Specifics & Danger Flags</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-xs">
                <div className="p-3 bg-muted/20 rounded-lg space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Immediate Danger Present:</span>
                    <span className="font-semibold text-red-600">{referral.immediate_safety_concerns ? "YES" : "No"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Law Enforcement Involved:</span>
                    <span className="font-semibold">{referral.law_enforcement_involved ? "Yes" : "No"}</span>
                  </div>
                  {referral.law_enforcement_file_number && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Police File Number:</span>
                      <span className="font-mono">{referral.law_enforcement_file_number}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 4: Child Dispositions */}
        <TabsContent value="dispositions" className="space-y-4">
          <Card className="border shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-bold">Individual Child Dispositions</CardTitle>
                  <CardDescription className="text-xs">
                    Mandatory child-level screening outcomes according to CRBCL technical architecture
                  </CardDescription>
                </div>
                {canEditDecision && (
                  <Button
                    size="sm"
                    onClick={() => navigate(`/intake/${referral.id}/decision`)}
                    className="h-8 gap-1 text-xs"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Manage Dispositions</span>
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-muted/50 text-muted-foreground border-b font-medium">
                    <tr>
                      <th className="px-4 py-3">Child Name</th>
                      <th className="px-4 py-3">Screening Outcome / Disposition</th>
                      <th className="px-4 py-3">Clinical Rationale</th>
                      <th className="px-4 py-3">Approval State</th>
                      <th className="px-4 py-3 text-right">Resulting Case</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {referral.dispositions?.length > 0 ? (
                      referral.dispositions.map((d) => {
                        const dispBadge = DISPOSITION_BADGES[d.decision] || { label: d.decision, bg: "bg-gray-100" };
                        return (
                          <tr key={d.id} className="hover:bg-muted/10">
                            <td className="px-4 py-3 font-semibold text-foreground">
                              {d.child_first_name} {d.child_last_name}
                            </td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-0.5 rounded-md text-[11px] font-semibold border ${dispBadge.bg}`}>
                                {dispBadge.label}
                              </span>
                            </td>
                            <td className="px-4 py-3 max-w-xs text-muted-foreground">
                              {d.reason || "—"}
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant="outline" className="text-[10px]">{d.approval_state}</Badge>
                            </td>
                            <td className="px-4 py-3 text-right">
                              {d.resulting_case_id ? (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="h-7 text-xs text-primary border-primary/30"
                                  onClick={() => navigate(`/cases/${d.resulting_case_id}`)}
                                >
                                  <span>View Case</span>
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </Button>
                              ) : (
                                <span className="text-muted-foreground text-[11px]">Pending Approval</span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground italic">
                          No dispositions recorded yet. Click "Manage Dispositions" to record child outcomes.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 5: Prior History Discovery */}
        <TabsContent value="history" className="space-y-4">
          <Card className="border shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <History className="w-4 h-4 text-primary" />
                <span>Automated Prior History Cross-Match</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Historical cases and prior intake reports discovered for persons linked to this intake
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-2">Prior Intake Referrals</h4>
                {historyData?.prior_referrals?.length > 0 ? (
                  <div className="divide-y border rounded-lg overflow-hidden text-xs">
                    {historyData.prior_referrals.map((pr) => (
                      <div key={pr.referral_id} className="p-3 flex items-center justify-between hover:bg-muted/20">
                        <div>
                          <span className="font-mono font-bold text-primary">{pr.referral_number}</span>
                          <span className="text-muted-foreground ml-2">({pr.received_date})</span>
                          <span className="block text-foreground mt-0.5 capitalize">Primary Concern: {pr.primary_concern?.replace(/_/g, ' ') || 'General'}</span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs text-primary"
                          onClick={() => navigate(`/intake/${pr.referral_id}`)}
                        >
                          View Referral
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground italic">No prior intake referrals found for these individuals.</p>
                )}
              </div>

              <div className="pt-2">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-2">Prior Case History</h4>
                {historyData?.prior_cases?.length > 0 ? (
                  <div className="divide-y border rounded-lg overflow-hidden text-xs">
                    {historyData.prior_cases.map((pc) => (
                      <div key={pc.case_id} className="p-3 flex items-center justify-between hover:bg-muted/20">
                        <div>
                          <span className="font-mono font-bold text-primary">{pc.case_number}</span>
                          <span className="text-foreground font-medium ml-2">{pc.title}</span>
                          <span className="block text-muted-foreground mt-0.5">{pc.case_type} • Status: {pc.status}</span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs text-primary"
                          onClick={() => navigate(`/cases/${pc.case_id}`)}
                        >
                          View Case
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground italic">No prior open/closed cases found for these individuals.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

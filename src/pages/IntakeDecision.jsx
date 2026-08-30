import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Shield, ArrowLeft, CheckCircle2, AlertTriangle, Send,
  FileText, Users, Clock, RotateCcw, Building, Check, Sparkles
} from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { teamsApi } from "@/api/teams";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";

export default function IntakeDecision() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [referral, setReferral] = useState(null);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Decision State
  const [overallRecommendation, setOverallRecommendation] = useState("");
  const [rationale, setRationale] = useState("");
  const [childDispositions, setChildDispositions] = useState({});

  // Supervisor Action Modals
  const [approveModalOpen, setApproveModalOpen] = useState(false);
  const [supervisorNotes, setSupervisorNotes] = useState("");
  const [returnModalOpen, setReturnModalOpen] = useState(false);
  const [returnReason, setReturnReason] = useState("");

  const fetchReferralAndTeams = async () => {
    try {
      setLoading(true);
      const [refData, teamsData] = await Promise.all([
        referralsApi.get(id),
        teamsApi.list().catch(() => []),
      ]);

      setReferral(refData);
      setTeams(teamsData || []);

      if (refData.decision) {
        setOverallRecommendation(refData.decision.overall_recommendation || "");
        setRationale(refData.decision.rationale || "");
      }

      // Populate existing child dispositions
      const children = refData.people?.filter(p => p.role === "child") || [];
      const dispMap = {};

      children.forEach(c => {
        const existing = refData.dispositions?.find(d => d.person_id === c.person_id);
        dispMap[c.person_id] = {
          decision: existing?.decision || "PROTECTION",
          reason: existing?.reason || "",
          destination_team_id: existing?.destination_team_id || "",
          external_agency_name: existing?.external_agency_name || "",
          external_referral_contact: existing?.external_referral_contact || "",
        };
      });

      setChildDispositions(dispMap);
    } catch (err) {
      toast({
        title: "Error loading intake decision",
        description: err.message || "Failed to load referral",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReferralAndTeams();
  }, [id]);

  const updateChildDisp = (personId, field, val) => {
    setChildDispositions(prev => ({
      ...prev,
      [personId]: {
        ...prev[personId],
        [field]: val,
      }
    }));
  };

  const handleSaveDraft = async () => {
    try {
      setSaving(true);
      const dispositionsPayload = Object.entries(childDispositions).map(([personId, d]) => ({
        person_id: personId,
        decision: d.decision,
        reason: d.reason || "",
        destination_team_id: d.destination_team_id || undefined,
        external_agency_name: d.external_agency_name || undefined,
        external_referral_contact: d.external_referral_contact || undefined,
      }));

      await referralsApi.saveDecision(id, {
        overall_recommendation: overallRecommendation,
        rationale: rationale,
        dispositions: dispositionsPayload,
      });

      toast({ title: "Draft Saved", description: "Decision recommendations and dispositions updated." });
    } catch (err) {
      toast({ title: "Save Failed", description: err.message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitForApproval = async () => {
    if (!overallRecommendation.trim()) {
      toast({ title: "Recommendation required", description: "Please enter an overall recommendation before submitting.", variant: "destructive" });
      return;
    }

    try {
      setSaving(true);
      const dispositionsPayload = Object.entries(childDispositions).map(([personId, d]) => ({
        person_id: personId,
        decision: d.decision,
        reason: d.reason || "",
        destination_team_id: d.destination_team_id || undefined,
        external_agency_name: d.external_agency_name || undefined,
        external_referral_contact: d.external_referral_contact || undefined,
      }));

      await referralsApi.submitForApproval(id, {
        overall_recommendation: overallRecommendation,
        rationale: rationale,
        dispositions: dispositionsPayload,
      });

      toast({
        title: "Submitted for Supervisor Approval",
        description: `Referral ${referral.referral_number} has been placed in the supervisor approval queue.`,
      });

      navigate(`/intake/${id}`);
    } catch (err) {
      toast({ title: "Submission Failed", description: err.message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    try {
      setSaving(true);
      await referralsApi.approve(id, {
        supervisor_notes: supervisorNotes || undefined,
      });

      toast({
        title: "Intake Approved & Routed",
        description: "Child dispositions executed and resulting case records opened successfully.",
      });

      setApproveModalOpen(false);
      navigate(`/intake/${id}`);
    } catch (err) {
      toast({ title: "Approval Failed", description: err.message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleReturn = async () => {
    if (!returnReason.trim()) {
      toast({ title: "Return comments required", variant: "destructive" });
      return;
    }

    try {
      setSaving(true);
      await referralsApi.returnToWorker(id, returnReason.trim());
      toast({
        title: "Referral Returned",
        description: "Intake returned to worker with revision instructions.",
      });
      setReturnModalOpen(false);
      navigate(`/intake/${id}`);
    } catch (err) {
      toast({ title: "Return Failed", description: err.message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  if (loading || !referral) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center text-muted-foreground">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading Decision Workflow...
      </div>
    );
  }

  const children = referral.people?.filter(p => p.role === "child") || [];

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate(`/intake/${id}`)}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold font-heading text-foreground">
                Screening Decision & Child Dispositions
              </h1>
              <Badge variant="outline" className="font-mono">{referral.referral_number}</Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Define individualized dispositions for each child on the referral and submit for supervisor approval.
            </p>
          </div>
        </div>

        {/* Supervisor Action Buttons if pending */}
        {referral.status === "PENDING_SUPERVISOR" && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              className="text-rose-700 border-rose-300 hover:bg-rose-50 text-xs"
              onClick={() => setReturnModalOpen(true)}
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" />
              <span>Return for Revision</span>
            </Button>

            <Button
              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs gap-1.5 shadow-sm"
              onClick={() => setApproveModalOpen(true)}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Approve & Route Cases</span>
            </Button>
          </div>
        )}
      </div>

      {/* Intake Context Recap */}
      <Card className="border shadow-sm bg-muted/20">
        <CardContent className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div>
            <span className="text-muted-foreground block">Primary Concern:</span>
            <span className="font-semibold capitalize">{referral.primary_concern?.replace(/_/g, ' ') || "General"}</span>
          </div>
          <div>
            <span className="text-muted-foreground block">Priority & Risk:</span>
            <span className="font-semibold">{referral.priority} Priority • {referral.risk_level || "Standard"} Risk</span>
          </div>
          <div>
            <span className="text-muted-foreground block">Community:</span>
            <span className="font-semibold">{referral.community || "Unspecified"}</span>
          </div>
        </CardContent>
      </Card>

      {/* Multi-Child Dispositions Matrix */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-foreground flex items-center gap-2">
              <Users className="w-4 h-4 text-primary" />
              <span>Per-Child Disposition Outcomes ({children.length} Children)</span>
            </h2>
            <p className="text-xs text-muted-foreground">
              Under CRBCL Architecture, each child receives an individualized disposition and clinical rationale.
            </p>
          </div>
        </div>

        {children.length === 0 ? (
          <Card className="border p-8 text-center text-muted-foreground italic text-xs">
            No children associated with this referral. Return to intake details and add child participants.
          </Card>
        ) : (
          children.map((child) => {
            const disp = childDispositions[child.person_id] || { decision: "PROTECTION", reason: "" };

            return (
              <Card key={child.person_id} className="border shadow-sm border-l-4 border-l-primary">
                <CardHeader className="pb-3 bg-muted/10">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-sm font-bold text-foreground">
                        {child.first_name} {child.last_name}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Birth Date: {child.date_of_birth || "Unknown"} • Band/Nation: {child.band_nation || "Not Specified"}
                      </CardDescription>
                    </div>
                    <Badge variant="secondary" className="text-xs capitalize">
                      {disp.decision.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label className="text-xs font-semibold">Individual Disposition Outcome *</Label>
                      <Select
                        value={disp.decision}
                        onValueChange={(val) => updateChildDisp(child.person_id, "decision", val)}
                      >
                        <SelectTrigger className="h-9">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="PROTECTION">Child Protection Investigation (Open Protection Case)</SelectItem>
                          <SelectItem value="PREVENTION">Family Prevention & Wellness Services (Open Prevention Case)</SelectItem>
                          <SelectItem value="POST_MAJORITY">Post-Majority Transition Services</SelectItem>
                          <SelectItem value="SCREEN_OUT">Screen Out (No Statutory Welfare Services Required)</SelectItem>
                          <SelectItem value="EXTERNAL_REFERRAL">External Agency / Community Referral</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {["PROTECTION", "PREVENTION", "POST_MAJORITY"].includes(disp.decision) && (
                      <div className="space-y-1.5">
                        <Label className="text-xs font-semibold">Assigned Destination Team</Label>
                        <Select
                          value={disp.destination_team_id || ""}
                          onValueChange={(val) => updateChildDisp(child.person_id, "destination_team_id", val)}
                        >
                          <SelectTrigger className="h-9">
                            <SelectValue placeholder="Select Destination Team..." />
                          </SelectTrigger>
                          <SelectContent>
                            {teams.map(t => (
                              <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {disp.decision === "EXTERNAL_REFERRAL" && (
                      <div className="space-y-1.5">
                        <Label className="text-xs font-semibold">External Agency Name</Label>
                        <Input
                          className="h-9 text-xs"
                          placeholder="e.g. Regina Child and Youth Mental Health"
                          value={disp.external_agency_name || ""}
                          onChange={(e) => updateChildDisp(child.person_id, "external_agency_name", e.target.value)}
                        />
                      </div>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label className="text-xs font-semibold">Clinical Rationale for this Child *</Label>
                    <Textarea
                      rows={2}
                      className="text-xs"
                      placeholder={`Document the specific safety assessment or voluntary wellness rationale for ${child.first_name}...`}
                      value={disp.reason}
                      onChange={(e) => updateChildDisp(child.person_id, "reason", e.target.value)}
                    />
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Overall Intake Recommendation */}
      <Card className="border shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary" />
            <span>Overall Intake Recommendation & Summary Rationale</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold">Recommendation Summary *</Label>
            <Input
              placeholder="e.g. Recommend initiating formal investigation for Child A and voluntary prevention for Child B."
              value={overallRecommendation}
              onChange={(e) => setOverallRecommendation(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs font-semibold">Overall Family Wellness & Safety Rationale</Label>
            <Textarea
              rows={4}
              placeholder="Summarize parental capacity, kinship supports, historical factors, and overall assessment conclusions..."
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Worker Bottom Action Bar */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="outline" onClick={() => navigate(`/intake/${id}`)}>
          Cancel
        </Button>

        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={handleSaveDraft} disabled={saving}>
            Save Decision Draft
          </Button>

          <Button
            onClick={handleSubmitForApproval}
            disabled={saving}
            className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2 min-w-[180px]"
          >
            <Send className="w-4 h-4" />
            <span>Submit to Supervisor</span>
          </Button>
        </div>
      </div>

      {/* Supervisor Approve Modal */}
      <Dialog open={approveModalOpen} onOpenChange={setApproveModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Intake Referral & Route Cases</DialogTitle>
            <DialogDescription className="text-xs">
              Approving will finalize screening outcomes and automatically create corresponding Child Protection or Prevention case records.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <Label className="text-xs">Supervisor Approval Notes (Optional)</Label>
            <Textarea
              rows={3}
              placeholder="Enter any supervisory instructions or concurrence notes..."
              value={supervisorNotes}
              onChange={(e) => setSupervisorNotes(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setApproveModalOpen(false)}>Cancel</Button>
            <Button className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={handleApprove} disabled={saving}>
              Confirm & Execute Approval
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Supervisor Return Modal */}
      <Dialog open={returnModalOpen} onOpenChange={setReturnModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Return Referral for Revision</DialogTitle>
            <DialogDescription className="text-xs">
              Provide mandatory revision comments explaining what additional information or adjustments are needed from the worker.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <Label className="text-xs font-semibold text-rose-800">Return Reason / Required Revisions *</Label>
            <Textarea
              rows={3}
              placeholder="Detail required collateral checks, missing assessments, or necessary updates..."
              value={returnReason}
              onChange={(e) => setReturnReason(e.target.value)}
              required
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReturnModalOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleReturn} disabled={saving}>
              Return to Worker
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

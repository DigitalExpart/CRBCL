import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Shield, Clock, AlertTriangle, CheckCircle2, RotateCcw,
  Users, ChevronRight, Inbox, RefreshCw, ExternalLink
} from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/use-toast";

export default function SupervisorApprovalQueue() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Quick Action Modal
  const [activeReferral, setActiveReferral] = useState(null);
  const [actionType, setActionType] = useState(null); // 'approve' | 'return'
  const [actionNotes, setActionNotes] = useState("");
  const [executing, setExecuting] = useState(false);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const res = await referralsApi.getApprovalQueue({ page: 1, page_size: 50 });
      setQueue(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      toast({
        title: "Error loading queue",
        description: err.message || "Failed to load approval queue",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleExecuteAction = async () => {
    if (!activeReferral) return;

    if (actionType === "return" && !actionNotes.trim()) {
      toast({ title: "Return comments required", variant: "destructive" });
      return;
    }

    try {
      setExecuting(true);
      if (actionType === "approve") {
        await referralsApi.approve(activeReferral.id, {
          supervisor_notes: actionNotes || undefined,
        });
        toast({
          title: "Referral Approved",
          description: `${activeReferral.referral_number} approved and resulting cases generated.`,
        });
      } else {
        await referralsApi.returnToWorker(activeReferral.id, actionNotes.trim());
        toast({
          title: "Referral Returned",
          description: `${activeReferral.referral_number} returned to worker.`,
        });
      }

      setActiveReferral(null);
      setActionType(null);
      setActionNotes("");
      fetchQueue();
    } catch (err) {
      toast({ title: "Action Failed", description: err.message, variant: "destructive" });
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-purple-100 text-purple-800">
            <Clock className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-heading text-foreground">
              Supervisor Approval Queue
            </h1>
            <p className="text-xs text-muted-foreground">
              Review and approve pending multi-child screening decisions, or return to worker with revision instructions
            </p>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={fetchQueue} className="gap-1.5 text-xs">
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Queue Table */}
      <Card className="border shadow-sm overflow-hidden">
        <CardHeader className="bg-muted/20 pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-bold">
              Pending Referrals Requiring Supervisory Action ({total})
            </CardTitle>
            <Badge className="bg-purple-600 text-white text-xs">{total} Pending</Badge>
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
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                      <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                      Loading supervisor queue...
                    </td>
                  </tr>
                ) : queue.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                      <CheckCircle2 className="w-10 h-10 mx-auto mb-3 text-emerald-500 opacity-60" />
                      <p className="font-medium text-foreground">Supervisor Queue Clean</p>
                      <p className="text-xs text-muted-foreground mt-1">There are currently no referrals awaiting supervisor review.</p>
                    </td>
                  </tr>
                ) : (
                  queue.map((ref) => (
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
                        {ref.primary_concern?.replace(/_/g, ' ') || ref.summary || "General Intake"}
                      </td>

                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <Badge variant="outline" className="text-[10px] bg-blue-50 text-blue-700">
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
                          className="h-7 text-xs text-rose-700 border-rose-200 hover:bg-rose-50"
                          onClick={() => { setActiveReferral(ref); setActionType("return"); setActionNotes(""); }}
                        >
                          <RotateCcw className="w-3 h-3 mr-1" />
                          <span>Return</span>
                        </Button>

                        <Button
                          size="sm"
                          className="h-7 text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                          onClick={() => { setActiveReferral(ref); setActionType("approve"); setActionNotes(""); }}
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

      {/* Action Dialog */}
      <Dialog open={!!activeReferral} onOpenChange={(open) => !open && setActiveReferral(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {actionType === "approve" ? "Approve Intake Referral & Open Cases" : "Return Referral to Worker"}
            </DialogTitle>
            <DialogDescription className="text-xs">
              {actionType === "approve"
                ? `Confirming will approve referral ${activeReferral?.referral_number} and immediately generate corresponding Child Protection or Prevention cases.`
                : `Specify mandatory revision comments explaining what updates are required for ${activeReferral?.referral_number}.`}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            <Label className="text-xs font-semibold">
              {actionType === "approve" ? "Supervisor Notes (Optional)" : "Return Reason / Revision Instructions *"}
            </Label>
            <Textarea
              rows={3}
              placeholder={actionType === "approve" ? "Supervisory notes..." : "Enter details on required revisions..."}
              value={actionNotes}
              onChange={(e) => setActionNotes(e.target.value)}
              required={actionType === "return"}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setActiveReferral(null)}>Cancel</Button>
            <Button
              className={actionType === "approve" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : "bg-destructive text-destructive-foreground"}
              onClick={handleExecuteAction}
              disabled={executing}
            >
              {actionType === "approve" ? "Execute Approval" : "Return to Worker"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

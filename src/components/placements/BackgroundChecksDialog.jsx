import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Plus,
  Calendar,
  User,
  CheckCircle2,
  AlertTriangle,
  Clock,
  FileText,
  BadgeCheck,
  XCircle,
  Gavel,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { placementsApi } from '@/api/placements';

export default function BackgroundChecksDialog({ open, onOpenChange, subjectPersonId = null }) {
  const [checks, setChecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [adjudicatingCheck, setAdjudicatingCheck] = useState(null);

  const [createForm, setCreateForm] = useState({
    subject_person_id: subjectPersonId || '',
    subject_name: '',
    subject_relationship: 'Foster Parent Candidate',
    check_type: 'CRIMINAL_RECORD',
    requested_date: new Date().toISOString().split('T')[0],
    screening_agency: 'RCMP / CPIC',
    notes: '',
  });

  const [adjudicateForm, setAdjudicateForm] = useState({
    status: 'CLEARED',
    clearance_number: '',
    completed_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
    adjudication_notes: 'Full clearance granted without conditions.',
    adjudication_conditions: '',
  });

  const loadChecks = async () => {
    try {
      setLoading(true);
      const params = subjectPersonId ? { subject_person_id: subjectPersonId } : {};
      const data = await placementsApi.listBackgroundChecks(params);
      setChecks(data || []);
    } catch (err) {
      console.error('Failed to load background checks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      loadChecks();
    }
  }, [open, subjectPersonId]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...createForm,
        subject_person_id: createForm.subject_person_id || null,
      };
      await placementsApi.createBackgroundCheck(payload);
      setShowCreateModal(false);
      loadChecks();
    } catch (err) {
      console.error('Failed to create background check:', err);
      alert(err.message || 'Failed to submit background check');
    }
  };

  const handleAdjudicate = async (e) => {
    e.preventDefault();
    if (!adjudicatingCheck) return;
    try {
      await placementsApi.adjudicateBackgroundCheck(adjudicatingCheck.id, adjudicateForm);
      setAdjudicatingCheck(null);
      loadChecks();
    } catch (err) {
      console.error('Failed to adjudicate background check:', err);
      alert(err.message || 'Failed to adjudicate background check');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'CLEARED':
        return <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20">Cleared</Badge>;
      case 'PENDING':
        return <Badge className="bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/20">Pending</Badge>;
      case 'IN_PROGRESS':
        return <Badge className="bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20">In Progress</Badge>;
      case 'CONDITIONAL':
        return <Badge className="bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/20">Conditional</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive">Rejected</Badge>;
      case 'EXPIRED':
        return <Badge variant="outline" className="bg-muted text-muted-foreground">Expired</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between pr-6">
              <DialogTitle className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-primary" /> Caregiver Screening & Background Checks
              </DialogTitle>
              <Button size="sm" onClick={() => setShowCreateModal(true)} className="gap-1.5 text-xs">
                <Plus className="w-3.5 h-3.5" /> Request Screening
              </Button>
            </div>
            <DialogDescription>
              Audit CPIC, Child Abuse Registry (CAR), Vulnerable Sector, and Band customary clearances.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 pt-2">
            {loading ? (
              <div className="py-8 text-center text-sm text-muted-foreground">Loading background checks...</div>
            ) : checks.length === 0 ? (
              <div className="py-8 text-center border border-dashed rounded-lg">
                <ShieldCheck className="w-7 h-7 mx-auto text-muted-foreground mb-1.5" />
                <p className="font-medium text-xs text-foreground">No background checks registered</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Screen caregivers, kinship relatives, and transport staff prior to child placement.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {checks.map((chk) => (
                  <div key={chk.id} className="p-4 rounded-lg border bg-card/60 space-y-2.5">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-sm text-foreground">{chk.subject_name}</span>
                          <Badge variant="secondary" className="text-xs">{chk.subject_relationship}</Badge>
                          <Badge variant="outline">{chk.check_type?.replace(/_/g, ' ')}</Badge>
                          {getStatusBadge(chk.status)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          Agency: <span className="text-foreground font-medium">{chk.screening_agency}</span> • Requested: {chk.requested_date}
                        </p>
                      </div>

                      {(chk.status === 'PENDING' || chk.status === 'IN_PROGRESS') && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setAdjudicatingCheck(chk);
                          }}
                          className="gap-1 text-xs"
                        >
                          <Gavel className="w-3.5 h-3.5" /> Adjudicate
                        </Button>
                      )}
                    </div>

                    {chk.clearance_number && (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs bg-muted/30 p-2 rounded">
                        <div>Clearance #: <span className="font-mono font-medium text-foreground">{chk.clearance_number}</span></div>
                        <div>Completed: <span className="font-medium text-foreground">{chk.completed_date}</span></div>
                        <div>Expiry: <span className="font-medium text-foreground">{chk.expiry_date || 'Standard (2 Yrs)'}</span></div>
                      </div>
                    )}

                    {chk.adjudication_notes && (
                      <p className="text-xs text-muted-foreground bg-card p-2 rounded border">
                        <span className="font-semibold text-foreground">Adjudication Notes: </span>
                        {chk.adjudication_notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* --- Create Screening Dialog --- */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Request Background Screening</DialogTitle>
            <DialogDescription>
              Initiate screening with CPIC, Child Abuse Registry, or Band Elders.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold">Subject Full Name *</label>
              <Input
                className="mt-1"
                placeholder="e.g. Robert Vance"
                value={createForm.subject_name}
                onChange={(e) => setCreateForm({ ...createForm, subject_name: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Relationship / Role *</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. Kinship Uncle"
                  value={createForm.subject_relationship}
                  onChange={(e) => setCreateForm({ ...createForm, subject_relationship: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Check Type *</label>
                <Select
                  value={createForm.check_type}
                  onValueChange={(val) => setCreateForm({ ...createForm, check_type: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CRIMINAL_RECORD">CPIC Criminal Record</SelectItem>
                    <SelectItem value="CHILD_ABUSE_REGISTRY">Child Abuse Registry (CAR)</SelectItem>
                    <SelectItem value="VULNERABLE_SECTOR">Vulnerable Sector Check</SelectItem>
                    <SelectItem value="REFERENCE_CHECK">Community Reference Check</SelectItem>
                    <SelectItem value="CUSTOMARY_VETTING">Customary Band Elder Vetting</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold">Screening Agency</label>
              <Input
                className="mt-1"
                value={createForm.screening_agency}
                onChange={(e) => setCreateForm({ ...createForm, screening_agency: e.target.value })}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button type="submit">Submit Request</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- Adjudicate Dialog --- */}
      <Dialog open={!!adjudicatingCheck} onOpenChange={() => setAdjudicatingCheck(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Adjudicate Background Check</DialogTitle>
            <DialogDescription>
              Review screening findings and record clearance status.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAdjudicate} className="space-y-4 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Adjudication Result *</label>
                <Select
                  value={adjudicateForm.status}
                  onValueChange={(val) => setAdjudicateForm({ ...adjudicateForm, status: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CLEARED">Cleared / Approved</SelectItem>
                    <SelectItem value="CONDITIONAL">Conditional Clearance</SelectItem>
                    <SelectItem value="REJECTED">Rejected / Unsuitable</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-semibold">Clearance Number</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. CPIC-90214"
                  value={adjudicateForm.clearance_number}
                  onChange={(e) => setAdjudicateForm({ ...adjudicateForm, clearance_number: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Completed Date</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={adjudicateForm.completed_date}
                  onChange={(e) => setAdjudicateForm({ ...adjudicateForm, completed_date: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Expiry Date</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={adjudicateForm.expiry_date}
                  onChange={(e) => setAdjudicateForm({ ...adjudicateForm, expiry_date: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold">Adjudication Rationale & Notes</label>
              <Textarea
                className="mt-1"
                value={adjudicateForm.adjudication_notes}
                onChange={(e) => setAdjudicateForm({ ...adjudicateForm, adjudication_notes: e.target.value })}
                required
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setAdjudicatingCheck(null)}>
                Cancel
              </Button>
              <Button type="submit">Finalize Adjudication</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}

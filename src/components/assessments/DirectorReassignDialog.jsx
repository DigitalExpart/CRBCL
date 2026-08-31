import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { ArrowRightLeft, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function DirectorReassignDialog({
  open,
  onOpenChange,
  assessment,
  onReassign,
  isLoading,
}) {
  const [targetCaseId, setTargetCaseId] = useState('');
  const [targetFamilyId, setTargetFamilyId] = useState('');
  const [reason, setReason] = useState('');

  const handleConfirm = async () => {
    if (!targetCaseId.trim()) {
      toast.error('Destination Case UUID is required.');
      return;
    }
    if (!reason.trim()) {
      toast.error('Mandatory reassignment reason is required.');
      return;
    }

    try {
      await onReassign({
        target_case_id: targetCaseId.trim(),
        target_family_id: targetFamilyId.trim() || undefined,
        reason: reason.trim(),
      });
      setTargetCaseId('');
      setTargetFamilyId('');
      setReason('');
      onOpenChange(false);
    } catch (err) {
      toast.error(err.message || 'Failed to reassign assessment');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
        <DialogHeader>
          <div className="flex items-center gap-2 text-indigo-400 mb-1">
            <ArrowRightLeft className="w-5 h-5" />
            <DialogTitle className="text-lg font-semibold text-white">
              Director Assessment Reassignment
            </DialogTitle>
          </div>
          <DialogDescription className="text-slate-400 text-sm">
            Reassign this misfiled assessment ({assessment?.assessment_number}) to a different case/family file.
          </DialogDescription>
        </DialogHeader>

        <div className="bg-indigo-950/40 border border-indigo-900/60 rounded-md p-3 flex gap-2 text-xs text-indigo-200/90 my-1">
          <AlertCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            Case conflict-of-interest restrictions will be strictly verified against the target destination. Reassignment creates append-only timeline and audit records.
          </div>
        </div>

        <div className="space-y-3 py-2">
          <div>
            <Label htmlFor="target-case-id" className="text-xs font-medium text-slate-300">
              Destination Case ID (UUID) <span className="text-rose-400">*</span>
            </Label>
            <Input
              id="target-case-id"
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
              value={targetCaseId}
              onChange={(e) => setTargetCaseId(e.target.value)}
              className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 text-sm font-mono mt-1"
            />
          </div>

          <div>
            <Label htmlFor="target-family-id" className="text-xs font-medium text-slate-300">
              Target Family ID (UUID) <span className="text-slate-500">(Optional)</span>
            </Label>
            <Input
              id="target-family-id"
              placeholder="Optional Family record ID"
              value={targetFamilyId}
              onChange={(e) => setTargetFamilyId(e.target.value)}
              className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 text-sm font-mono mt-1"
            />
          </div>

          <div>
            <Label htmlFor="reassign-reason" className="text-xs font-medium text-slate-300">
              Reassignment Reason <span className="text-rose-400">*</span>
            </Label>
            <Textarea
              id="reassign-reason"
              rows={2}
              placeholder="e.g. Assessment mistakenly initiated under sibling intake case file."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 text-sm mt-1"
            />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-slate-700 hover:bg-slate-800 text-slate-300"
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleConfirm}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium gap-1.5"
            disabled={isLoading || !targetCaseId.trim() || !reason.trim()}
          >
            <ArrowRightLeft className="w-4 h-4" />
            {isLoading ? 'Reassigning...' : 'Confirm Reassign'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

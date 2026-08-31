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
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { LockOpen, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

export default function DirectorUnlockDialog({
  open,
  onOpenChange,
  assessment,
  onUnlock,
  isLoading,
}) {
  const [reason, setReason] = useState('');

  const handleConfirm = async () => {
    if (!reason.trim()) {
      toast.error('Mandatory justification reason is required to unlock a finalized assessment.');
      return;
    }
    try {
      await onUnlock(reason.trim());
      setReason('');
      onOpenChange(false);
    } catch (err) {
      toast.error(err.message || 'Failed to unlock assessment');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
        <DialogHeader>
          <div className="flex items-center gap-2 text-amber-400 mb-1">
            <LockOpen className="w-5 h-5" />
            <DialogTitle className="text-lg font-semibold text-white">
              Director Assessment Unlock
            </DialogTitle>
          </div>
          <DialogDescription className="text-slate-400 text-sm">
            Unlocking a finalized assessment will transition it back to{' '}
            <span className="font-semibold text-emerald-400">COMPLETED</span> status so amendments can be made. This action is permanently recorded in the immutable audit log and sacred timeline.
          </DialogDescription>
        </DialogHeader>

        <div className="bg-amber-950/40 border border-amber-900/60 rounded-md p-3 flex gap-2 text-xs text-amber-200/90 my-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong>CRBCL Legal & Governance Policy:</strong> You must provide an explicit, auditable reason (e.g. court order, supervisor discovery, addendum requirement).
          </div>
        </div>

        <div className="space-y-2 py-2">
          <Label htmlFor="unlock-reason" className="text-xs font-medium text-slate-300">
            Mandatory Justification / Unlock Reason <span className="text-rose-400">*</span>
          </Label>
          <Textarea
            id="unlock-reason"
            rows={3}
            placeholder="e.g. Supplemental court request for updated household safety details; approved by Executive Director."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 focus:border-amber-500 text-sm"
          />
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
            className="bg-amber-600 hover:bg-amber-500 text-white font-medium gap-1.5"
            disabled={isLoading || !reason.trim()}
          >
            <LockOpen className="w-4 h-4" />
            {isLoading ? 'Unlocking...' : 'Authorize Unlock'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

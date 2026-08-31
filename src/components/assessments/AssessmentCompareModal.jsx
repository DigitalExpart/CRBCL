import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { GitCompare, CheckCircle2, XCircle, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';

export default function AssessmentCompareModal({
  open,
  onOpenChange,
  comparisonData,
  isLoading,
}) {
  if (!comparisonData && !isLoading) return null;

  const current = comparisonData?.current_assessment;
  const previous = comparisonData?.previous_assessment;
  const deltas = comparisonData?.deltas || [];
  const changedCount = comparisonData?.summary?.questions_changed || 0;
  const unchangedCount = comparisonData?.summary?.questions_unchanged || 0;
  const isDeterminationChanged = comparisonData?.summary?.determination_changed;

  const formatVal = (val) => {
    if (val === null || val === undefined || val === '') return <span className="text-slate-600 italic">Not answered</span>;
    if (typeof val === 'boolean') {
      return val ? (
        <span className="inline-flex items-center gap-1 text-emerald-400 font-medium"><CheckCircle2 className="w-3.5 h-3.5" /> Yes</span>
      ) : (
        <span className="inline-flex items-center gap-1 text-rose-400 font-medium"><XCircle className="w-3.5 h-3.5" /> No</span>
      );
    }
    if (Array.isArray(val)) {
      if (val.length === 0) return <span className="text-slate-600 italic">None selected</span>;
      return <span className="text-slate-200">{val.join(', ')}</span>;
    }
    return <span className="text-slate-200">{String(val)}</span>;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto bg-slate-900 border-slate-800 text-slate-100 p-6">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-cyan-400">
              <GitCompare className="w-5 h-5" />
              <DialogTitle className="text-lg font-semibold text-white">
                Time-Series Assessment Comparison
              </DialogTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-amber-500/10 text-amber-300 border-amber-500/30 text-xs">
                {changedCount} Changed
              </Badge>
              <Badge variant="outline" className="bg-slate-800 text-slate-400 border-slate-700 text-xs">
                {unchangedCount} Unchanged
              </Badge>
            </div>
          </div>
          <DialogDescription className="text-slate-400 text-xs mt-1">
            Comparing historical answers and clinical determinations across sequential assessment dates.
          </DialogDescription>
        </DialogHeader>

        {/* Comparison Header Meta */}
        <div className="grid grid-cols-2 gap-4 bg-slate-950/70 border border-slate-800 rounded-lg p-4 my-3 text-xs">
          <div className="border-r border-slate-800/80 pr-4">
            <div className="text-slate-500 font-medium uppercase tracking-wider mb-1">Baseline Assessment (Earlier)</div>
            <div className="text-slate-200 font-semibold text-sm">{previous?.assessment_number}</div>
            <div className="text-slate-400 mt-0.5">
              {previous?.conducted_at ? format(new Date(previous.conducted_at), 'PPP p') : 'N/A'}
            </div>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-slate-500">Determination:</span>
              <Badge variant="outline" className="text-slate-300 border-slate-700">
                {previous?.determination || 'Pending'}
              </Badge>
            </div>
          </div>

          <div className="pl-2">
            <div className="text-slate-500 font-medium uppercase tracking-wider mb-1">Current Assessment (Later)</div>
            <div className="text-emerald-400 font-semibold text-sm">{current?.assessment_number}</div>
            <div className="text-slate-400 mt-0.5">
              {current?.conducted_at ? format(new Date(current.conducted_at), 'PPP p') : 'N/A'}
            </div>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-slate-500">Determination:</span>
              <Badge
                variant="outline"
                className={
                  isDeterminationChanged
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    : 'text-slate-300 border-slate-700'
                }
              >
                {current?.determination || 'Pending'}
              </Badge>
            </div>
          </div>
        </div>

        {/* Delta Table */}
        <div className="space-y-3 mt-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Question-by-Question Response Comparison
          </div>

          <div className="divide-y divide-slate-800 border border-slate-800 rounded-lg overflow-hidden bg-slate-950/40">
            {deltas.map((d) => (
              <div
                key={d.question_key}
                className={`p-3 text-xs transition-colors ${
                  d.is_changed ? 'bg-amber-500/5 hover:bg-amber-500/10' : 'hover:bg-slate-900/40'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="font-medium text-slate-200 flex items-center gap-2">
                    <span>{d.question_label}</span>
                    <span className="text-[10px] text-slate-500 font-mono">({d.question_key})</span>
                  </div>
                  {d.is_changed ? (
                    <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30 text-[10px] uppercase">
                      Changed
                    </Badge>
                  ) : (
                    <span className="text-[10px] text-slate-600 uppercase font-medium">Unchanged</span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 pl-2">
                  <div className="bg-slate-900/60 p-2 rounded border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 mb-0.5">Previous Value</div>
                    <div className="text-xs">{formatVal(d.previous_value)}</div>
                  </div>

                  <div className={`p-2 rounded border ${d.is_changed ? 'bg-amber-950/20 border-amber-900/40' : 'bg-slate-900/60 border-slate-800/80'}`}>
                    <div className="text-[10px] text-slate-500 mb-0.5">Current Value</div>
                    <div className="text-xs flex items-center gap-2">
                      {d.is_changed && <ArrowRight className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                      {formatVal(d.current_value)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

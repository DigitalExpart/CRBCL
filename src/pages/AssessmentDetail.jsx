import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assessmentsApi } from '@/api/assessments';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  ArrowLeft,
  Save,
  CheckCircle,
  Lock,
  LockOpen,
  Printer,
  GitCompare,
  ArrowRightLeft,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Info,
  Clock,
  Check,
  X,
  FileText,
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import DirectorUnlockDialog from '@/components/assessments/DirectorUnlockDialog';
import DirectorReassignDialog from '@/components/assessments/DirectorReassignDialog';
import AssessmentCompareModal from '@/components/assessments/AssessmentCompareModal';
import AssessmentPrintView from '@/components/assessments/AssessmentPrintView';

export default function AssessmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Dialog states
  const [completeOpen, setCompleteOpen] = useState(false);
  const [lockOpen, setLockOpen] = useState(false);
  const [unlockOpen, setUnlockOpen] = useState(false);
  const [reassignOpen, setReassignOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);
  const [comparisonTargetId, setComparisonTargetId] = useState('');

  // Active section tab
  const [activeSectionId, setActiveSectionId] = useState('');

  // Form State: question_id -> { boolean_value, number_value, text_value, date_value, selected_option_ids }
  const [formAnswers, setFormAnswers] = useState({});
  const [determination, setDetermination] = useState('');
  const [determinationNotes, setDeterminationNotes] = useState('');
  const [summary, setSummary] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  // Fetch assessment data
  const {
    data: assessment,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['assessment', id],
    queryFn: () => assessmentsApi.get(id),
  });

  // Fetch sibling assessments for comparison
  const { data: caseAssessmentsData } = useQuery({
    queryKey: ['case-assessments', assessment?.case_id],
    queryFn: () => assessmentsApi.listByCase(assessment.case_id),
    enabled: !!assessment?.case_id,
  });

  // Fetch comparison data when target chosen
  const { data: comparisonData, isLoading: isComparing } = useQuery({
    queryKey: ['assessment-comparison', id, comparisonTargetId],
    queryFn: () => assessmentsApi.compare(id, comparisonTargetId),
    enabled: !!comparisonTargetId && compareOpen,
  });

  const templateVersion = assessment?.template_version;
  const sections = templateVersion?.sections || [];

  // Map question key to question object & question id to key
  const { keyToQuestionMap, idToQuestionMap } = useMemo(() => {
    const kMap = new Map();
    const idMap = new Map();
    sections.forEach((sec) => {
      (sec.questions || []).forEach((q) => {
        kMap.set(q.key, q);
        idMap.set(q.id, q);
      });
    });
    return { keyToQuestionMap: kMap, idToQuestionMap: idMap };
  }, [sections]);

  // Initialize form state from loaded assessment answers
  useEffect(() => {
    if (assessment) {
      const answersMap = {};
      (assessment.answers || []).forEach((a) => {
        answersMap[a.question_id] = {
          question_id: a.question_id,
          boolean_value: a.boolean_value,
          number_value: a.number_value !== null && a.number_value !== undefined ? a.number_value : '',
          text_value: a.text_value || '',
          date_value: a.date_value || '',
          datetime_value: a.datetime_value || '',
          selected_option_ids: (a.selected_options || []).map((o) => o.option_id),
        };
      });
      setFormAnswers(answersMap);
      setDetermination(assessment.determination || '');
      setDeterminationNotes(assessment.determination_notes || '');
      setSummary(assessment.summary || '');
      setIsDirty(false);

      if (sections.length > 0 && !activeSectionId) {
        setActiveSectionId(sections[0].id);
      }
    }
  }, [assessment, sections]);

  // Mutations
  const saveMutation = useMutation({
    mutationFn: (payload) => assessmentsApi.saveAnswers(id, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['assessment', id], updated);
      setIsDirty(false);
      toast.success('Assessment draft saved successfully.');
    },
    onError: (err) => {
      toast.error(err.message || 'Failed to save answers.');
    },
  });

  const completeMutation = useMutation({
    mutationFn: (payload) => assessmentsApi.complete(id, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['assessment', id], updated);
      setCompleteOpen(false);
      toast.success('Assessment completed successfully.');
    },
    onError: (err) => {
      toast.error(err.message || 'Failed to complete assessment.');
    },
  });

  const lockMutation = useMutation({
    mutationFn: (payload) => assessmentsApi.lock(id, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['assessment', id], updated);
      setLockOpen(false);
      toast.success('Assessment permanently locked.');
    },
    onError: (err) => {
      toast.error(err.message || 'Failed to lock assessment.');
    },
  });

  const unlockMutation = useMutation({
    mutationFn: (reason) => assessmentsApi.unlock(id, { reason }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['assessment', id], updated);
      toast.success('Assessment unlocked for amendments.');
    },
  });

  const reassignMutation = useMutation({
    mutationFn: (payload) => assessmentsApi.reassign(id, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['assessment', id], updated);
      toast.success('Assessment reassigned successfully.');
      navigate(`/cases/${updated.case_id}`);
    },
  });

  // Evaluate Question Visibility Condition
  const isQuestionVisible = (q) => {
    if (!q.visibility_condition) return true;
    const cond = q.visibility_condition;
    const depKey = cond.depends_on_question_key;
    if (!depKey) return true;

    const parentQuestion = keyToQuestionMap.get(depKey);
    if (!parentQuestion) return true;

    const parentAns = formAnswers[parentQuestion.id];
    if (!parentAns) return false;

    const op = cond.operator || 'eq';
    const targetVal = cond.value;

    if (parentQuestion.question_type === 'BOOLEAN') {
      const boolVal = parentAns.boolean_value;
      if (op === 'eq') return boolVal === targetVal;
      if (op === 'neq') return boolVal !== targetVal;
    }

    if (parentQuestion.question_type === 'SINGLE_SELECT' || parentQuestion.question_type === 'MULTI_SELECT') {
      const selectedIds = parentAns.selected_option_ids || [];
      const matchingOpt = parentQuestion.options?.find((opt) => opt.key === targetVal);
      if (!matchingOpt) return false;
      if (op === 'in' || op === 'eq') return selectedIds.includes(matchingOpt.id);
      if (op === 'not_in' || op === 'neq') return !selectedIds.includes(matchingOpt.id);
    }

    return true;
  };

  // Update handlers
  const handleBooleanChange = (qId, val) => {
    setFormAnswers((prev) => ({
      ...prev,
      [qId]: {
        ...(prev[qId] || { question_id: qId }),
        boolean_value: val,
      },
    }));
    setIsDirty(true);
  };

  const handleSingleSelectChange = (qId, optId) => {
    setFormAnswers((prev) => ({
      ...prev,
      [qId]: {
        ...(prev[qId] || { question_id: qId }),
        selected_option_ids: [optId],
      },
    }));
    setIsDirty(true);
  };

  const handleMultiSelectToggle = (qId, optId) => {
    setFormAnswers((prev) => {
      const current = prev[qId]?.selected_option_ids || [];
      const updated = current.includes(optId)
        ? current.filter((x) => x !== optId)
        : [...current, optId];
      return {
        ...prev,
        [qId]: {
          ...(prev[qId] || { question_id: qId }),
          selected_option_ids: updated,
        },
      };
    });
    setIsDirty(true);
  };

  const handleTextChange = (qId, val) => {
    setFormAnswers((prev) => ({
      ...prev,
      [qId]: {
        ...(prev[qId] || { question_id: qId }),
        text_value: val,
      },
    }));
    setIsDirty(true);
  };

  const handleNumberChange = (qId, val) => {
    setFormAnswers((prev) => ({
      ...prev,
      [qId]: {
        ...(prev[qId] || { question_id: qId }),
        number_value: val === '' ? null : Number(val),
      },
    }));
    setIsDirty(true);
  };

  const handleDateChange = (qId, val) => {
    setFormAnswers((prev) => ({
      ...prev,
      [qId]: {
        ...(prev[qId] || { question_id: qId }),
        date_value: val,
      },
    }));
    setIsDirty(true);
  };

  // Save draft
  const handleSaveDraft = () => {
    const payload = {
      answers: Object.values(formAnswers).map((a) => ({
        question_id: a.question_id,
        boolean_value: a.boolean_value ?? null,
        number_value: a.number_value !== '' && a.number_value !== null && a.number_value !== undefined ? Number(a.number_value) : null,
        text_value: a.text_value || null,
        date_value: a.date_value || null,
        datetime_value: a.datetime_value || null,
        selected_option_ids: a.selected_option_ids || [],
      })),
      determination: determination || null,
      determination_notes: determinationNotes || null,
      summary: summary || null,
    };
    saveMutation.mutate(payload);
  };

  // Complete submission
  const handleCompleteSubmit = () => {
    if (!determination.trim()) {
      toast.error('Please select an official clinical determination.');
      return;
    }
    completeMutation.mutate({
      determination: determination.trim(),
      determination_notes: determinationNotes.trim() || undefined,
      summary: summary.trim() || undefined,
    });
  };

  // Lock submission
  const [lockReason, setLockReason] = useState('');
  const handleLockSubmit = () => {
    lockMutation.mutate({ reason: lockReason.trim() || undefined });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">Loading assessment engine data...</p>
        </div>
      </div>
    );
  }

  if (isError || !assessment) {
    return (
      <div className="max-w-xl mx-auto mt-12 p-6 bg-slate-900 border border-rose-900/50 rounded-xl text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto" />
        <h2 className="text-xl font-bold text-white">Assessment Unavailable</h2>
        <p className="text-slate-400 text-sm">
          {error?.message || 'The requested assessment could not be loaded.'}
        </p>
        <Button
          onClick={() => navigate(-1)}
          variant="outline"
          className="border-slate-700 text-slate-300"
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Return to Case File
        </Button>
      </div>
    );
  }

  const isLocked = assessment.status === 'LOCKED';
  const isCompleted = assessment.status === 'COMPLETED';
  const indicatorSummary = assessment.indicator_summary || {};
  const siblingAssessments = (caseAssessmentsData?.items || []).filter((a) => a.id !== assessment.id);

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20">
      {/* Print View Component (Only shown during window.print()) */}
      <AssessmentPrintView assessment={assessment} />

      {/* Screen Interactive Container */}
      <div className="print:hidden space-y-6">
        {/* Navigation & Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(`/cases/${assessment.case_id}`)}
                className="text-slate-400 hover:text-slate-200 hover:bg-slate-800 -ml-2 h-8 px-2"
              >
                <ArrowLeft className="w-4 h-4 mr-1" /> Case #{assessment.case?.case_number || 'File'}
              </Button>
              <span className="text-slate-600">&bull;</span>
              <span className="text-xs font-mono text-emerald-400 font-semibold">
                {assessment.assessment_number}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white tracking-tight">
                {assessment.template?.name}
              </h1>
              <Badge
                variant="outline"
                className={
                  isLocked
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    : isCompleted
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }
              >
                {isLocked ? (
                  <span className="flex items-center gap-1"><Lock className="w-3 h-3" /> LOCKED</span>
                ) : (
                  assessment.status
                )}
              </Badge>
              {isDirty && !isLocked && (
                <span className="text-xs text-amber-400/90 italic animate-pulse">
                  ● Unsaved changes
                </span>
              )}
            </div>

            <p className="text-xs text-slate-400">
              Form Version {templateVersion?.version_number} &bull; Conductor: {assessment.conductor?.full_name || assessment.conductor?.email || 'Assigned Worker'} &bull; Date: {assessment.conducted_at ? format(new Date(assessment.conducted_at), 'PPP') : 'Draft'}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              <Printer className="w-4 h-4 mr-1.5" /> Print / PDF
            </Button>

            {siblingAssessments.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setComparisonTargetId(siblingAssessments[0].id);
                  setCompareOpen(true);
                }}
                className="border-slate-700 text-cyan-400 hover:bg-slate-800"
              >
                <GitCompare className="w-4 h-4 mr-1.5" /> Compare History
              </Button>
            )}

            {!isLocked && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveDraft}
                  disabled={saveMutation.isPending || !isDirty}
                  className="border-slate-700 text-slate-200 hover:bg-slate-800"
                >
                  <Save className="w-4 h-4 mr-1.5" />
                  {saveMutation.isPending ? 'Saving...' : 'Save Draft'}
                </Button>

                <Button
                  size="sm"
                  onClick={() => setCompleteOpen(true)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-sm"
                >
                  <CheckCircle className="w-4 h-4 mr-1.5" /> Complete Assessment
                </Button>
              </>
            )}

            {isCompleted && !isLocked && (
              <Button
                size="sm"
                onClick={() => setLockOpen(true)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                <Lock className="w-4 h-4 mr-1.5 text-rose-400" /> Lock Record
              </Button>
            )}

            {isLocked && (
              <Button
                size="sm"
                onClick={() => setUnlockOpen(true)}
                className="bg-amber-600 hover:bg-amber-500 text-white font-medium"
              >
                <LockOpen className="w-4 h-4 mr-1.5" /> Director Unlock
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setReassignOpen(true)}
              className="text-slate-400 hover:text-indigo-300 hover:bg-indigo-950/40"
              title="Director Reassign Assessment"
            >
              <ArrowRightLeft className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Deterministic Indicator Banner */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Present Danger</span>
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-xl font-bold text-white mt-1">
              {indicatorSummary.present_danger_count || 0}
            </div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Impending Danger</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-xl font-bold text-white mt-1">
              {indicatorSummary.impending_danger_count || 0}
            </div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Protective Capacities</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-xl font-bold text-white mt-1">
              {indicatorSummary.protective_capacities_count || 0}
            </div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Active Concerns</span>
              <Info className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-xl font-bold text-white mt-1">
              {indicatorSummary.active_concerns_count || 0}
            </div>
          </div>
        </div>

        {/* Section Navigation Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800">
          {sections.map((sec, idx) => (
            <button
              key={sec.id}
              onClick={() => setActiveSectionId(sec.id)}
              className={`px-3.5 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex items-center gap-2 ${
                activeSectionId === sec.id
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              <span className="w-5 h-5 rounded-full bg-black/20 flex items-center justify-center text-[10px]">
                {idx + 1}
              </span>
              {sec.title}
            </button>
          ))}
        </div>

        {/* Active Section Question Renderer */}
        {sections
          .filter((sec) => sec.id === activeSectionId)
          .map((sec) => (
            <Card key={sec.id} className="bg-slate-900 border-slate-800">
              <CardHeader className="border-b border-slate-800 pb-4">
                <CardTitle className="text-lg font-semibold text-white">
                  {sec.title}
                </CardTitle>
                {sec.description && (
                  <p className="text-xs text-slate-400 mt-1">{sec.description}</p>
                )}
              </CardHeader>

              <CardContent className="space-y-6 pt-6">
                {(sec.questions || []).map((q, qIdx) => {
                  if (!isQuestionVisible(q)) return null;

                  const ans = formAnswers[q.id] || {};

                  return (
                    <div
                      key={q.id}
                      className="p-4 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-3 transition-all hover:border-slate-700"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <Label className="text-sm font-medium text-slate-200">
                            {q.label}
                            {q.is_required && (
                              <span className="text-rose-400 ml-1 font-bold">*</span>
                            )}
                          </Label>
                          {q.help_text && (
                            <p className="text-xs text-slate-400 mt-0.5">{q.help_text}</p>
                          )}
                        </div>
                        <span className="text-[10px] font-mono text-slate-600 uppercase">
                          {q.question_type}
                        </span>
                      </div>

                      {/* Question Inputs By Type */}
                      {q.question_type === 'BOOLEAN' && (
                        <div className="flex items-center gap-3 pt-1">
                          <button
                            type="button"
                            disabled={isLocked}
                            onClick={() => handleBooleanChange(q.id, true)}
                            className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-semibold border transition-all ${
                              ans.boolean_value === true
                                ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                                : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                            }`}
                          >
                            <Check className="w-3.5 h-3.5" /> Yes
                          </button>
                          <button
                            type="button"
                            disabled={isLocked}
                            onClick={() => handleBooleanChange(q.id, false)}
                            className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-semibold border transition-all ${
                              ans.boolean_value === false
                                ? 'bg-rose-500/20 border-rose-500 text-rose-300'
                                : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                            }`}
                          >
                            <X className="w-3.5 h-3.5" /> No
                          </button>
                        </div>
                      )}

                      {q.question_type === 'SINGLE_SELECT' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                          {(q.options || []).map((opt) => {
                            const isSelected = (ans.selected_option_ids || []).includes(opt.id);
                            return (
                              <div
                                key={opt.id}
                                onClick={() => !isLocked && handleSingleSelectChange(q.id, opt.id)}
                                className={`p-3 rounded-md border text-xs cursor-pointer transition-all ${
                                  isSelected
                                    ? 'bg-emerald-950/40 border-emerald-500/80 text-emerald-200'
                                    : 'bg-slate-900/70 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900'
                                }`}
                              >
                                <div className="font-semibold flex items-center justify-between">
                                  <span>{opt.label}</span>
                                  {isSelected && <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
                                </div>
                                {opt.description && (
                                  <p className="text-[11px] text-slate-400 mt-1">{opt.description}</p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {q.question_type === 'MULTI_SELECT' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                          {(q.options || []).map((opt) => {
                            const isSelected = (ans.selected_option_ids || []).includes(opt.id);
                            return (
                              <div
                                key={opt.id}
                                onClick={() => !isLocked && handleMultiSelectToggle(q.id, opt.id)}
                                className={`p-3 rounded-md border text-xs cursor-pointer transition-all ${
                                  isSelected
                                    ? 'bg-emerald-950/40 border-emerald-500/80 text-emerald-200'
                                    : 'bg-slate-900/70 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900'
                                }`}
                              >
                                <div className="font-semibold flex items-center justify-between">
                                  <span>{opt.label}</span>
                                  <input
                                    type="checkbox"
                                    checked={isSelected}
                                    onChange={() => {}}
                                    className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-0"
                                  />
                                </div>
                                {opt.description && (
                                  <p className="text-[11px] text-slate-400 mt-1">{opt.description}</p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {q.question_type === 'NUMBER' && (
                        <Input
                          type="number"
                          disabled={isLocked}
                          value={ans.number_value ?? ''}
                          onChange={(e) => handleNumberChange(q.id, e.target.value)}
                          placeholder="Enter numeric value..."
                          className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 max-w-xs text-sm"
                        />
                      )}

                      {q.question_type === 'TEXT' && (
                        <Textarea
                          disabled={isLocked}
                          rows={3}
                          value={ans.text_value || ''}
                          onChange={(e) => handleTextChange(q.id, e.target.value)}
                          placeholder="Provide details and clinical notes..."
                          className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 text-sm"
                        />
                      )}

                      {q.question_type === 'DATE' && (
                        <Input
                          type="date"
                          disabled={isLocked}
                          value={ans.date_value || ''}
                          onChange={(e) => handleDateChange(q.id, e.target.value)}
                          className="bg-slate-950 border-slate-800 text-slate-100 max-w-xs text-sm"
                        />
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          ))}

        {/* Clinical Determination & Assessment Summary Card */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="border-b border-slate-800 pb-3">
            <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              Clinical Determination & Final Safety Rationale
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="determination" className="text-xs font-medium text-slate-300">
                  Official Determination Outcome
                </Label>
                <Input
                  id="determination"
                  disabled={isLocked}
                  value={determination}
                  onChange={(e) => {
                    setDetermination(e.target.value);
                    setIsDirty(true);
                  }}
                  placeholder="e.g. CHILD_SAFE_AT_HOME or CONDITIONALLY_SAFE"
                  className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 text-sm mt-1 uppercase"
                />
              </div>

              <div>
                <Label htmlFor="summary" className="text-xs font-medium text-slate-300">
                  Executive Assessment Summary
                </Label>
                <Input
                  id="summary"
                  disabled={isLocked}
                  value={summary}
                  onChange={(e) => {
                    setSummary(e.target.value);
                    setIsDirty(true);
                  }}
                  placeholder="High-level narrative summary..."
                  className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 text-sm mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="determination-notes" className="text-xs font-medium text-slate-300">
                Determination Notes & Statutory Findings
              </Label>
              <Textarea
                id="determination-notes"
                disabled={isLocked}
                rows={3}
                value={determinationNotes}
                onChange={(e) => {
                  setDeterminationNotes(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="Detailed rationale justifying the clinical safety determination..."
                className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-600 text-sm mt-1"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Complete Assessment Dialog */}
      <Dialog open={completeOpen} onOpenChange={setCompleteOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-lg font-semibold text-white">
              Complete Assessment
            </DialogTitle>
            <DialogDescription className="text-slate-400 text-sm">
              Finalize this assessment and set its official determination. All required fields across all sections will be strictly validated.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2 text-xs">
            <div>
              <Label htmlFor="comp-determination" className="text-xs font-medium text-slate-300">
                Official Determination <span className="text-rose-400">*</span>
              </Label>
              <Input
                id="comp-determination"
                value={determination}
                onChange={(e) => setDetermination(e.target.value)}
                placeholder="e.g. CHILD_SAFE_AT_HOME, CONDITIONALLY_SAFE, or UNSAFE"
                className="bg-slate-950 border-slate-800 text-slate-100 uppercase mt-1 text-sm"
              />
            </div>

            <div>
              <Label htmlFor="comp-notes" className="text-xs font-medium text-slate-300">
                Determination Notes & Clinical Rationale
              </Label>
              <Textarea
                id="comp-notes"
                rows={3}
                value={determinationNotes}
                onChange={(e) => setDeterminationNotes(e.target.value)}
                placeholder="Document safety network, living condition remedies, and case decisions..."
                className="bg-slate-950 border-slate-800 text-slate-100 mt-1 text-sm"
              />
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCompleteOpen(false)}
              className="border-slate-700 hover:bg-slate-800 text-slate-300"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleCompleteSubmit}
              disabled={completeMutation.isPending || !determination.trim()}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              {completeMutation.isPending ? 'Validating & Completing...' : 'Confirm & Complete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Lock Dialog */}
      <Dialog open={lockOpen} onOpenChange={setLockOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-lg font-semibold text-white flex items-center gap-2">
              <Lock className="w-5 h-5 text-rose-400" />
              Lock Assessment Record
            </DialogTitle>
            <DialogDescription className="text-slate-400 text-sm">
              Locking prevents any further edits to answers or determinations. Only an authorized Executive Director with explicit permission can unlock it.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 py-2">
            <Label htmlFor="lock-reason" className="text-xs font-medium text-slate-300">
              Lock Reason / Supervisory Sign-Off Notes
            </Label>
            <Textarea
              id="lock-reason"
              rows={2}
              value={lockReason}
              onChange={(e) => setLockReason(e.target.value)}
              placeholder="e.g. Assessment reviewed and finalized following multidisciplinary team review."
              className="bg-slate-950 border-slate-800 text-slate-100 mt-1 text-sm"
            />
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => setLockOpen(false)}
              className="border-slate-700 hover:bg-slate-800 text-slate-300"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleLockSubmit}
              disabled={lockMutation.isPending}
              className="bg-rose-600 hover:bg-rose-500 text-white font-medium"
            >
              {lockMutation.isPending ? 'Locking...' : 'Confirm Lock'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Director Unlock Modal */}
      <DirectorUnlockDialog
        open={unlockOpen}
        onOpenChange={setUnlockOpen}
        assessment={assessment}
        onUnlock={(reason) => unlockMutation.mutateAsync(reason)}
        isLoading={unlockMutation.isPending}
      />

      {/* Director Reassign Modal */}
      <DirectorReassignDialog
        open={reassignOpen}
        onOpenChange={setReassignOpen}
        assessment={assessment}
        onReassign={(payload) => reassignMutation.mutateAsync(payload)}
        isLoading={reassignMutation.isPending}
      />

      {/* Comparison Modal */}
      <AssessmentCompareModal
        open={compareOpen}
        onOpenChange={setCompareOpen}
        comparisonData={comparisonData}
        isLoading={isComparing}
      />
    </div>
  );
}

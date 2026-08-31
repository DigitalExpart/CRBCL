import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Shield,
  FileText,
  ChevronLeft,
  CheckCircle2,
  Lock,
  Unlock,
  Send,
  RotateCcw,
  Check,
  Plus,
  PenTool,
  UploadCloud,
  Printer,
  Copy,
  Clock,
  User,
  Users,
  AlertTriangle,
  Heart,
  Target,
  Hash,
  Sparkles,
} from 'lucide-react';
import { plansApi } from '../api/plans';
import PlanSignatureDialog from '../components/plans/PlanSignatureDialog';
import PhysicalSignatureUploadDialog from '../components/plans/PhysicalSignatureUploadDialog';
import PlanCloneModal from '../components/plans/PlanCloneModal';
import PlanPrintView from '../components/plans/PlanPrintView';

export default function PlanDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [plan, setPlan] = useState(null);
  const [printData, setPrintData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVersionId, setSelectedVersionId] = useState(null);

  // Dialog States
  const [showSignDialog, setShowSignDialog] = useState(false);
  const [showPhysicalSigDialog, setShowPhysicalSigDialog] = useState(false);
  const [showCloneModal, setShowCloneModal] = useState(false);

  // Action prompts / comment state
  const [actionLoading, setActionLoading] = useState(false);

  const loadPlan = async () => {
    try {
      setLoading(true);
      const data = await plansApi.get(id);
      setPlan(data);
      if (data.current_version?.id) {
        setSelectedVersionId(data.current_version.id);
      }
      const printRes = await plansApi.getPrintData(id).catch(() => null);
      setPrintData(printRes);
    } catch (err) {
      setError(err.message || 'Failed to load plan details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadPlan();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="p-12 text-center text-muted-foreground text-sm">
        Loading Family Wellness Plan...
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="p-8 max-w-xl mx-auto text-center space-y-4">
        <div className="p-3 bg-rose-500/10 text-rose-600 rounded-full w-12 h-12 mx-auto flex items-center justify-center">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-foreground">Error Loading Plan</h2>
        <p className="text-xs text-muted-foreground">{error || 'Plan not found.'}</p>
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-xs"
        >
          Go Back
        </button>
      </div>
    );
  }

  // Active version to display
  const versions = plan.versions || [];
  const activeVersion =
    versions.find((v) => v.id === selectedVersionId) || plan.current_version || versions[0];
  const metrics = plan.metrics || {};

  // Lifecycle Action Handlers
  const handleSubmitForReview = async () => {
    const comments = window.prompt('Optional submission comments for clinical supervisor:');
    if (comments === null) return;
    try {
      setActionLoading(true);
      await plansApi.submit(plan.id, { comments });
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to submit plan.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprovePlan = async () => {
    const notes = window.prompt('Supervisor approval endorsement notes:');
    if (notes === null) return;
    try {
      setActionLoading(true);
      await plansApi.approve(plan.id, { supervisor_notes: notes });
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to approve plan.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReturnPlan = async () => {
    const reasons = window.prompt('Mandatory clinical revision notes for caseworker:');
    if (!reasons) return alert('Revision rationale is required to return a plan.');
    try {
      setActionLoading(true);
      await plansApi.returnForRevisions(plan.id, { reasons });
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to return plan.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleFinalizePlan = async () => {
    if (!window.confirm('Finalize and seal this plan version with canonical SHA-256 hash?')) return;
    try {
      setActionLoading(true);
      await plansApi.finalize(plan.id);
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to finalize plan.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleLockPlan = async () => {
    const reason = window.prompt('Locking rationale (e.g. Case closure, Court filing):') || 'Standard locking.';
    try {
      setActionLoading(true);
      await plansApi.lock(plan.id, { reason });
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to lock plan.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUnlockPlan = async () => {
    const justification = window.prompt('Mandatory Director justification for unlocking:');
    if (!justification) return alert('Written justification is required to unlock a plan.');
    try {
      setActionLoading(true);
      await plansApi.unlock(plan.id, { justification });
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to unlock plan.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateNewVersion = async () => {
    if (!window.confirm('Create next version (v' + ((activeVersion?.version_number || 1) + 1) + ') for this plan?')) return;
    try {
      setActionLoading(true);
      await plansApi.createVersion(plan.id);
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to create new version.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompleteGoal = async (goalId) => {
    const notes = window.prompt('Goal completion notes:');
    if (notes === null) return;
    try {
      await plansApi.completeGoal(goalId, { notes });
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to complete goal.');
    }
  };

  const handleCompleteActivity = async (activityId) => {
    const completionNotes = window.prompt('Activity completion notes:');
    if (completionNotes === null) return;
    try {
      await plansApi.completeActivity(activityId, { completion_notes: completionNotes });
      await loadPlan();
    } catch (err) {
      alert(err.message || 'Failed to complete activity.');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200 pb-16">
      {/* Print View Component (rendered only during print) */}
      <PlanPrintView printData={printData} />

      {/* Screen View */}
      <div className="print:hidden space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Link
              to={`/cases/${plan.case_id}?tab=plans`}
              className="hover:text-primary flex items-center gap-1 font-medium"
            >
              <ChevronLeft className="w-4 h-4" /> Back to Case Plans
            </Link>
            <span>/</span>
            <span className="font-mono text-foreground">{plan.plan_number}</span>
          </div>

          {/* Version Selector */}
          {versions.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">View Version:</span>
              <select
                value={selectedVersionId || ''}
                onChange={(e) => setSelectedVersionId(e.target.value)}
                className="px-3 py-1 bg-card border rounded-lg text-xs font-mono font-semibold"
              >
                {versions.map((v) => (
                  <option key={v.id} value={v.id}>
                    Version {v.version_number} ({v.status})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Master Header Card */}
        <div className="p-6 bg-card border border-border rounded-2xl shadow-sm space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div
                className={`p-3 rounded-2xl shrink-0 ${
                  plan.plan_type === 'SAFETY_PLAN'
                    ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                    : 'bg-purple-500/10 text-purple-600 dark:text-purple-400'
                }`}
              >
                {plan.plan_type === 'SAFETY_PLAN' ? (
                  <Shield className="w-7 h-7" />
                ) : (
                  <FileText className="w-7 h-7" />
                )}
              </div>

              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs font-bold text-primary">{plan.plan_number}</span>
                  <span className="text-xs font-mono bg-muted px-2 py-0.5 rounded font-semibold">
                    Version {activeVersion?.version_number || 1}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide ${
                      activeVersion?.status === 'FINALIZED'
                        ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20'
                        : activeVersion?.status === 'LOCKED'
                        ? 'bg-gray-500/10 text-gray-700 dark:text-gray-300 border border-gray-500/20'
                        : activeVersion?.status === 'IN_REVIEW'
                        ? 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20'
                        : 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20'
                    }`}
                  >
                    {activeVersion?.status || plan.status}
                  </span>
                </div>

                <h1 className="text-xl font-bold text-foreground mt-1">{plan.title}</h1>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {plan.plan_type === 'SAFETY_PLAN'
                    ? 'Immediate Crisis Protection Protocol'
                    : 'Comprehensive Family Wellness Plan'}
                </p>
              </div>
            </div>

            {/* Action Buttons Toolbar */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* Draft State Actions */}
              {activeVersion?.status === 'DRAFT' && (
                <>
                  <button
                    onClick={handleSubmitForReview}
                    disabled={actionLoading}
                    className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs shadow-sm flex items-center gap-1.5 transition"
                  >
                    <Send className="w-3.5 h-3.5" /> Submit for Review
                  </button>

                  <button
                    onClick={handleFinalizePlan}
                    disabled={actionLoading}
                    className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-xs shadow-sm flex items-center gap-1.5 transition"
                  >
                    <Check className="w-3.5 h-3.5" /> Finalize Plan
                  </button>
                </>
              )}

              {/* Review State Actions */}
              {activeVersion?.status === 'IN_REVIEW' && (
                <>
                  <button
                    onClick={handleApprovePlan}
                    disabled={actionLoading}
                    className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-xs shadow-sm flex items-center gap-1.5 transition"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Approve & Seal
                  </button>

                  <button
                    onClick={handleReturnPlan}
                    disabled={actionLoading}
                    className="px-3.5 py-1.5 border border-rose-500/30 text-rose-600 hover:bg-rose-500/10 font-semibold rounded-xl text-xs flex items-center gap-1.5 transition"
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Return for Changes
                  </button>
                </>
              )}

              {/* Finalized & Locked Actions */}
              {(activeVersion?.status === 'FINALIZED' || activeVersion?.status === 'LOCKED') && (
                <>
                  <button
                    onClick={() => setShowSignDialog(true)}
                    className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-xs shadow-sm flex items-center gap-1.5 transition"
                  >
                    <PenTool className="w-3.5 h-3.5" /> Sign
                  </button>

                  <button
                    onClick={() => setShowPhysicalSigDialog(true)}
                    className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-xl text-xs shadow-sm flex items-center gap-1.5 transition"
                  >
                    <UploadCloud className="w-3.5 h-3.5" /> Upload Scan
                  </button>

                  {activeVersion?.status === 'FINALIZED' ? (
                    <button
                      onClick={handleLockPlan}
                      className="px-3 py-1.5 border border-gray-500/30 text-gray-700 dark:text-gray-300 hover:bg-muted font-semibold rounded-xl text-xs flex items-center gap-1.5 transition"
                    >
                      <Lock className="w-3.5 h-3.5" /> Lock Plan
                    </button>
                  ) : (
                    <button
                      onClick={handleUnlockPlan}
                      className="px-3 py-1.5 border border-amber-500/30 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10 font-semibold rounded-xl text-xs flex items-center gap-1.5 transition"
                    >
                      <Unlock className="w-3.5 h-3.5" /> Director Unlock
                    </button>
                  )}

                  <button
                    onClick={handleCreateNewVersion}
                    className="px-3 py-1.5 border rounded-xl text-xs font-semibold hover:bg-muted transition flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" /> Next Version
                  </button>
                </>
              )}

              <button
                onClick={() => setShowCloneModal(true)}
                className="p-2 border rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition text-xs flex items-center gap-1"
                title="Clone Plan into New Master Record"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={handlePrint}
                className="p-2 border rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition text-xs flex items-center gap-1"
                title="Print Official Document"
              >
                <Printer className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Cryptographic SHA-256 Hash Display */}
          {activeVersion?.document_hash && (
            <div className="p-3 bg-muted/40 border rounded-xl flex items-center justify-between gap-2 text-xs font-mono">
              <div className="flex items-center gap-2 truncate text-muted-foreground">
                <Hash className="w-4 h-4 text-primary shrink-0" />
                <span className="font-semibold text-foreground">Canonical Document Hash:</span>
                <span className="truncate">{activeVersion.document_hash}</span>
              </div>
              <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 rounded font-semibold text-[10px] uppercase shrink-0">
                Verified Sealed
              </span>
            </div>
          )}

          {/* Meta Details Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-3 border-t border-border/60 text-xs">
            <div>
              <span className="text-muted-foreground">Master Case:</span>
              <div className="font-semibold text-foreground font-mono">
                {plan.case?.case_number || 'N/A'}
              </div>
            </div>
            <div>
              <span className="text-muted-foreground">Primary Client:</span>
              <div className="font-semibold text-foreground">
                {plan.primary_person
                  ? `${plan.primary_person.first_name} ${plan.primary_person.last_name}`
                  : 'N/A'}
              </div>
            </div>
            <div>
              <span className="text-muted-foreground">Formulation Date:</span>
              <div className="font-semibold text-foreground">
                {activeVersion?.meeting_date || 'Not specified'}
              </div>
            </div>
            <div>
              <span className="text-muted-foreground">Meeting Location:</span>
              <div className="font-semibold text-foreground">
                {activeVersion?.meeting_location || 'Not specified'}
              </div>
            </div>
          </div>
        </div>

        {/* Narrative Section */}
        {activeVersion?.narrative && (
          <div className="p-5 bg-card border border-border rounded-2xl shadow-sm space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" /> Clinical Narrative & Context
            </h3>
            <p className="text-xs text-foreground leading-relaxed whitespace-pre-wrap">
              {activeVersion.narrative}
            </p>
          </div>
        )}

        {/* 2-Column Grid: Concerns & Strengths */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Concerns / Harm Statements */}
          <div className="p-5 bg-card border border-border rounded-2xl shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" /> Concerns & Harm Statements (
              {activeVersion?.concerns?.length || 0})
            </h3>

            <div className="space-y-2.5">
              {(activeVersion?.concerns || []).map((c, idx) => (
                <div key={idx} className="p-3 bg-muted/20 border rounded-xl space-y-1 text-xs">
                  <div className="flex justify-between items-center font-semibold">
                    <span className="capitalize">{c.concern_type?.replace(/_/g, ' ')}</span>
                    <span className="text-rose-600 dark:text-rose-400 uppercase font-bold text-[10px]">
                      {c.severity}
                    </span>
                  </div>
                  <p className="text-muted-foreground">{c.statement}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Strengths & Protective Capacities */}
          <div className="p-5 bg-card border border-border rounded-2xl shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Heart className="w-4 h-4 text-rose-500" /> Strengths & Protective Capacities (
              {activeVersion?.strengths?.length || 0})
            </h3>

            <div className="space-y-2.5">
              {(activeVersion?.strengths || []).map((s, idx) => (
                <div key={idx} className="p-3 bg-muted/20 border rounded-xl space-y-1 text-xs">
                  <div className="font-semibold text-emerald-600 dark:text-emerald-400 capitalize">
                    {s.category?.replace(/_/g, ' ')}
                  </div>
                  <p className="text-muted-foreground">{s.statement}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* SMART Goals & Action Steps Matrix */}
        <div className="p-6 bg-card border border-border rounded-2xl shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Target className="w-4 h-4 text-blue-500" /> SMART Goals & Activities Matrix
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Measurable commitments with accountable parties and tracking
              </p>
            </div>

            <div className="text-right">
              <span className="text-xs font-bold text-foreground">
                {metrics.completion_percentage || 0}% Completed
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {(activeVersion?.goals || []).map((g, gIdx) => (
              <div key={g.id || gIdx} className="p-4 bg-muted/20 border rounded-2xl space-y-3">
                {/* Goal Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-primary/10 text-primary font-bold text-xs rounded">
                      Goal #{gIdx + 1}
                    </span>
                    <span className="font-semibold text-xs text-foreground uppercase">{g.category}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                        g.status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
                          : 'bg-amber-500/10 text-amber-700 dark:text-amber-300'
                      }`}
                    >
                      {g.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      Target: {g.target_date || 'Ongoing'}
                    </span>
                    {g.status !== 'COMPLETED' && (
                      <button
                        onClick={() => handleCompleteGoal(g.id)}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold flex items-center gap-1 transition"
                      >
                        <Check className="w-3 h-3" /> Complete Goal
                      </button>
                    )}
                  </div>
                </div>

                <p className="text-xs text-foreground font-medium">{g.goal_text}</p>

                {/* Activities List */}
                {g.activities && g.activities.length > 0 && (
                  <div className="space-y-1.5 pl-3 border-l-2 border-primary/30">
                    <span className="text-[11px] font-semibold text-muted-foreground uppercase">
                      Action Steps & Responsible Parties
                    </span>
                    {g.activities.map((a, aIdx) => (
                      <div
                        key={a.id || aIdx}
                        className="p-2.5 bg-card border rounded-lg flex items-center justify-between gap-2 text-xs"
                      >
                        <div className="space-y-0.5">
                          <div className="font-medium text-foreground">{a.activity_text}</div>
                          <div className="text-[10px] text-muted-foreground">
                            Assigned to: <span className="font-semibold">{a.responsible_name}</span> • Due:{' '}
                            {a.due_date || 'Ongoing'}
                          </div>
                        </div>

                        <div>
                          {a.status === 'COMPLETED' ? (
                            <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 rounded text-[10px] font-semibold flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Done
                            </span>
                          ) : (
                            <button
                              onClick={() => handleCompleteActivity(a.id)}
                              className="px-2 py-0.5 border rounded hover:bg-muted text-[10px] font-semibold transition"
                            >
                              Mark Done
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Signatures & Attestation Log */}
        <div className="p-6 bg-card border border-border rounded-2xl shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" /> Signatures & Attestation Registry (
                {activeVersion?.signatures?.length || 0})
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Tamper-evident legal signatures verified against Version {activeVersion?.version_number || 1} SHA-256 seal
              </p>
            </div>

            {(activeVersion?.status === 'FINALIZED' || activeVersion?.status === 'LOCKED') && (
              <button
                onClick={() => setShowSignDialog(true)}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-xs shadow-sm flex items-center gap-1.5 transition"
              >
                <PenTool className="w-3.5 h-3.5" /> Sign Plan
              </button>
            )}
          </div>

          {(activeVersion?.signatures || []).length === 0 ? (
            <div className="p-8 text-center border border-dashed rounded-xl text-muted-foreground text-xs">
              No signatures collected on Version {activeVersion?.version_number || 1} yet. Finalize the plan to begin
              attestation.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {activeVersion.signatures.map((sig, idx) => (
                <div key={sig.id || idx} className="p-4 bg-muted/20 border rounded-xl space-y-2 text-xs">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-bold text-foreground">{sig.signer_name}</div>
                      <div className="text-[11px] text-muted-foreground">
                        {sig.signer_role} • {sig.signer_type}
                      </div>
                    </div>
                    <div className="text-[10px] text-muted-foreground font-mono">
                      {new Date(sig.signed_at).toLocaleString()}
                    </div>
                  </div>

                  {sig.signature_image_url ? (
                    <div className="p-2 bg-white rounded-lg border flex justify-center">
                      <img src={sig.signature_image_url} alt="Signature" className="h-12 object-contain" />
                    </div>
                  ) : (
                    <div className="p-2 bg-card rounded-lg border italic font-serif text-sm text-foreground">
                      {sig.signature_data || sig.signer_name}
                    </div>
                  )}

                  <p className="text-[11px] text-muted-foreground italic">{sig.attestation_text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <PlanSignatureDialog
        isOpen={showSignDialog}
        onClose={() => setShowSignDialog(false)}
        plan={plan}
        onSigned={() => loadPlan()}
      />

      <PhysicalSignatureUploadDialog
        isOpen={showPhysicalSigDialog}
        onClose={() => setShowPhysicalSigDialog(false)}
        plan={plan}
        onUploaded={() => loadPlan()}
      />

      <PlanCloneModal
        isOpen={showCloneModal}
        onClose={() => setShowCloneModal(false)}
        plan={plan}
        onCloned={(cloned) => navigate(`/plans/${cloned.id}`)}
      />
    </div>
  );
}

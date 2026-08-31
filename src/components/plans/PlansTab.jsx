import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  FileText,
  Plus,
  Copy,
  PenTool,
  Printer,
  ChevronRight,
  CheckCircle2,
  Clock,
  Lock,
  RotateCcw,
  Target,
  Sparkles,
  AlertCircle,
  UploadCloud,
} from 'lucide-react';
import { plansApi } from '../../api/plans';
import PlanCreateModal from './PlanCreateModal';
import PlanCloneModal from './PlanCloneModal';
import PlanSignatureDialog from './PlanSignatureDialog';
import PhysicalSignatureUploadDialog from './PhysicalSignatureUploadDialog';

export default function PlansTab({ caseId, caseData, people = [] }) {
  const navigate = useNavigate();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('ALL'); // 'ALL' | 'SAFETY_PLAN' | 'CASE_PLAN'

  // Modal States
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [cloneTargetPlan, setCloneTargetPlan] = useState(null);
  const [signTargetPlan, setSignTargetPlan] = useState(null);
  const [physicalSigTargetPlan, setPhysicalSigTargetPlan] = useState(null);

  const loadPlans = async () => {
    try {
      setLoading(true);
      const data = await plansApi.listByCase(
        caseId,
        filterType === 'ALL' ? null : filterType
      );
      setPlans(data || []);
    } catch (err) {
      console.error('Error fetching case plans:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      loadPlans();
    }
  }, [caseId, filterType]);

  // Aggregate Metrics
  const safetyCount = plans.filter((p) => p.plan_type === 'SAFETY_PLAN').length;
  const casePlanCount = plans.filter((p) => p.plan_type === 'CASE_PLAN').length;
  const totalGoals = plans.reduce((acc, p) => acc + (p.metrics?.total_goals || 0), 0);
  const completedGoals = plans.reduce((acc, p) => acc + (p.metrics?.completed_goals || 0), 0);
  const avgCompletion = totalGoals > 0 ? Math.round((completedGoals / totalGoals) * 100) : 0;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'DRAFT':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20">
            Draft
          </span>
        );
      case 'IN_REVIEW':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20">
            In Review
          </span>
        );
      case 'FINALIZED':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
            Finalized
          </span>
        );
      case 'LOCKED':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-500/10 text-gray-700 dark:text-gray-300 border border-gray-500/20 flex items-center gap-1">
            <Lock className="w-3 h-3" /> Locked
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-muted text-muted-foreground border">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
            <span>Safety & Family Wellness Plans</span>
            <span className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 text-xs font-mono font-semibold">
              Phase 6
            </span>
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Standardized child protection safety protocols, preservation case plans, and cryptographic e-signatures
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-xs shadow-sm hover:bg-primary/90 transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Create New Plan
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-card border border-border rounded-xl">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase">Safety Plans</span>
            <Shield className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold mt-1 text-foreground">{safetyCount}</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">Crisis & immediate safety</p>
        </div>

        <div className="p-4 bg-card border border-border rounded-xl">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase">Case Plans</span>
            <FileText className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-2xl font-bold mt-1 text-foreground">{casePlanCount}</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">Long-term preservation</p>
        </div>

        <div className="p-4 bg-card border border-border rounded-xl">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase">Goal Completion</span>
            <Target className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold mt-1 text-foreground">{avgCompletion}%</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">{completedGoals} of {totalGoals} goals achieved</p>
        </div>

        <div className="p-4 bg-card border border-border rounded-xl">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase">Total Plans</span>
            <Sparkles className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold mt-1 text-foreground">{plans.length}</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">Active & historical versions</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <button
          onClick={() => setFilterType('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
            filterType === 'ALL'
              ? 'bg-primary text-primary-foreground font-semibold shadow-sm'
              : 'text-muted-foreground hover:bg-muted'
          }`}
        >
          All Plans ({plans.length})
        </button>
        <button
          onClick={() => setFilterType('SAFETY_PLAN')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
            filterType === 'SAFETY_PLAN'
              ? 'bg-rose-500 text-white font-semibold shadow-sm'
              : 'text-muted-foreground hover:bg-muted'
          }`}
        >
          <Shield className="w-3.5 h-3.5" /> Safety Plans ({safetyCount})
        </button>
        <button
          onClick={() => setFilterType('CASE_PLAN')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
            filterType === 'CASE_PLAN'
              ? 'bg-purple-600 text-white font-semibold shadow-sm'
              : 'text-muted-foreground hover:bg-muted'
          }`}
        >
          <FileText className="w-3.5 h-3.5" /> Case Plans ({casePlanCount})
        </button>
      </div>

      {/* Plan Cards List */}
      {loading ? (
        <div className="p-12 text-center text-muted-foreground text-sm">
          Loading Family Wellness Plans...
        </div>
      ) : plans.length === 0 ? (
        <div className="p-12 text-center border-2 border-dashed border-border rounded-2xl bg-card">
          <div className="p-3 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded-full w-12 h-12 mx-auto flex items-center justify-center mb-3">
            <FileText className="w-6 h-6" />
          </div>
          <h4 className="font-semibold text-foreground text-sm">No Plans Authored Yet</h4>
          <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
            Formulate a Safety Plan for immediate risk mitigation or a Case Plan for multi-month family preservation.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-xs shadow-sm hover:bg-primary/90 transition inline-flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Create First Plan
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {plans.map((p) => {
            const metrics = p.metrics || {};
            const pct = metrics.completion_percentage || 0;

            return (
              <div
                key={p.id}
                className="p-5 bg-card border border-border rounded-2xl shadow-sm hover:shadow-md transition space-y-4"
              >
                {/* Header Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2.5 rounded-xl ${
                        p.plan_type === 'SAFETY_PLAN'
                          ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                          : 'bg-purple-500/10 text-purple-600 dark:text-purple-400'
                      }`}
                    >
                      {p.plan_type === 'SAFETY_PLAN' ? (
                        <Shield className="w-5 h-5" />
                      ) : (
                        <FileText className="w-5 h-5" />
                      )}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-primary">{p.plan_number}</span>
                        <span className="text-xs font-mono text-muted-foreground">v{p.current_version_number}</span>
                        {getStatusBadge(p.status)}
                      </div>
                      <h4 className="text-base font-bold text-foreground mt-0.5">{p.title}</h4>
                    </div>
                  </div>

                  {/* Actions Dropdown / Buttons */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCloneTargetPlan(p)}
                      title="Clone into new Plan Blueprint"
                      className="p-2 text-muted-foreground hover:text-foreground border rounded-lg hover:bg-muted transition text-xs flex items-center gap-1"
                    >
                      <Copy className="w-3.5 h-3.5" /> Clone
                    </button>

                    {(p.status === 'FINALIZED' || p.status === 'LOCKED') && (
                      <>
                        <button
                          onClick={async () => {
                            const fullPlan = await plansApi.get(p.id);
                            setSignTargetPlan(fullPlan);
                          }}
                          title="Electronic Attestation"
                          className="p-2 text-emerald-600 hover:text-emerald-700 bg-emerald-500/10 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 transition text-xs flex items-center gap-1 font-semibold"
                        >
                          <PenTool className="w-3.5 h-3.5" /> Sign
                        </button>

                        <button
                          onClick={async () => {
                            const fullPlan = await plansApi.get(p.id);
                            setPhysicalSigTargetPlan(fullPlan);
                          }}
                          title="Upload Scanned Paper Signature"
                          className="p-2 text-purple-600 hover:text-purple-700 bg-purple-500/10 border border-purple-500/20 rounded-lg hover:bg-purple-500/20 transition text-xs flex items-center gap-1"
                        >
                          <UploadCloud className="w-3.5 h-3.5" /> Scan
                        </button>
                      </>
                    )}

                    <button
                      onClick={() => navigate(`/plans/${p.id}`)}
                      className="px-3.5 py-1.5 bg-primary text-primary-foreground font-semibold rounded-lg text-xs hover:bg-primary/90 transition flex items-center gap-1"
                    >
                      <span>Open Plan</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Progress & Metadata Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 border-t border-border/60 text-xs">
                  {/* Goal Progress Bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[11px] text-muted-foreground font-medium">
                      <span>Goal Execution Progress</span>
                      <span className="font-bold text-foreground">{pct}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-muted-foreground">
                      <span>{metrics.completed_goals || 0} completed</span>
                      <span>{metrics.total_goals || 0} total goals</span>
                    </div>
                  </div>

                  {/* Signatures Status */}
                  <div className="space-y-1">
                    <span className="text-muted-foreground text-[11px] font-medium">Attestation Status</span>
                    <div className="flex items-center gap-2 font-semibold text-foreground">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      <span>
                        {p.signatures_count || 0} / {p.signatures_required || 1} Signatures Collected
                      </span>
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      {p.status === 'FINALIZED' || p.status === 'LOCKED' ? 'Document sealed with SHA-256' : 'Awaiting final approval'}
                    </p>
                  </div>

                  {/* Formulation & Dates */}
                  <div className="space-y-1">
                    <span className="text-muted-foreground text-[11px] font-medium">Formulation & Review</span>
                    <div className="flex items-center gap-2 text-foreground font-medium">
                      <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                      <span>Meeting: {p.meeting_date || 'Not specified'}</span>
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      Updated: {new Date(p.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal Dialogs */}
      <PlanCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        caseId={caseId}
        people={people}
        onCreated={() => loadPlans()}
      />

      <PlanCloneModal
        isOpen={!!cloneTargetPlan}
        onClose={() => setCloneTargetPlan(null)}
        plan={cloneTargetPlan}
        onCloned={() => loadPlans()}
      />

      <PlanSignatureDialog
        isOpen={!!signTargetPlan}
        onClose={() => setSignTargetPlan(null)}
        plan={signTargetPlan}
        onSigned={() => loadPlans()}
      />

      <PhysicalSignatureUploadDialog
        isOpen={!!physicalSigTargetPlan}
        onClose={() => setPhysicalSigTargetPlan(null)}
        plan={physicalSigTargetPlan}
        onUploaded={() => loadPlans()}
      />
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import {
  X,
  Plus,
  Trash2,
  Shield,
  FileText,
  Users,
  AlertTriangle,
  Heart,
  Target,
  Calendar,
  MapPin,
  Check,
} from 'lucide-react';
import { plansApi } from '../../api/plans';
import { assessmentsApi } from '../../api/assessments';

export default function PlanCreateModal({ isOpen, onClose, caseId, onCreated, people = [] }) {
  if (!isOpen) return null;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [assessments, setAssessments] = useState([]);

  // Form State
  const [planType, setPlanType] = useState('SAFETY_PLAN');
  const [title, setTitle] = useState('');
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().split('T')[0]);
  const [meetingLocation, setMeetingLocation] = useState('CRBCL Wellness Centre');
  const [narrative, setNarrative] = useState('');
  const [selectedAssessmentIds, setSelectedAssessmentIds] = useState([]);

  // Child collections
  const [participants, setParticipants] = useState([
    {
      name: '',
      role: 'Primary Caregiver',
      relationship: 'Parent / Guardian',
      participant_type: 'FAMILY_MEMBER',
      signature_required: true,
      attendance_status: 'ATTENDED',
    },
  ]);

  const [concerns, setConcerns] = useState([
    {
      concern_type: 'SAFETY_THREAT',
      statement: '',
      severity: 'HIGH',
      sort_order: 1,
    },
  ]);

  const [strengths, setStrengths] = useState([
    {
      category: 'CULTURAL_SPIRITUAL',
      statement: '',
      sort_order: 1,
    },
  ]);

  const [goals, setGoals] = useState([
    {
      goal_text: '',
      category: 'SAFETY',
      target_date: '',
      status: 'NOT_STARTED',
      sort_order: 1,
      activities: [
        {
          activity_text: '',
          responsible_name: 'Caseworker & Family',
          responsible_type: 'JOINT',
          due_date: '',
          status: 'NOT_STARTED',
          sort_order: 1,
        },
      ],
    },
  ]);

  useEffect(() => {
    if (caseId) {
      assessmentsApi
        .listByCase(caseId)
        .then((res) => setAssessments(res?.items || []))
        .catch(() => setAssessments([]));
    }
  }, [caseId]);

  // Handle participant methods
  const addParticipant = () => {
    setParticipants([
      ...participants,
      {
        name: '',
        role: 'Community Support',
        relationship: 'Extended Kin',
        participant_type: 'COMMUNITY_SUPPORT',
        signature_required: true,
        attendance_status: 'ATTENDED',
      },
    ]);
  };

  const removeParticipant = (index) => {
    setParticipants(participants.filter((_, i) => i !== index));
  };

  const updateParticipant = (index, field, value) => {
    const updated = [...participants];
    updated[index][field] = value;
    setParticipants(updated);
  };

  // Handle concerns
  const addConcern = () => {
    setConcerns([
      ...concerns,
      {
        concern_type: 'SAFETY_THREAT',
        statement: '',
        severity: 'HIGH',
        sort_order: concerns.length + 1,
      },
    ]);
  };

  const removeConcern = (index) => {
    setConcerns(concerns.filter((_, i) => i !== index));
  };

  const updateConcern = (index, field, value) => {
    const updated = [...concerns];
    updated[index][field] = value;
    setConcerns(updated);
  };

  // Handle strengths
  const addStrength = () => {
    setStrengths([
      ...strengths,
      {
        category: 'FAMILY_UNITY',
        statement: '',
        sort_order: strengths.length + 1,
      },
    ]);
  };

  const removeStrength = (index) => {
    setStrengths(strengths.filter((_, i) => i !== index));
  };

  const updateStrength = (index, field, value) => {
    const updated = [...strengths];
    updated[index][field] = value;
    setStrengths(updated);
  };

  // Handle goals & activities
  const addGoal = () => {
    setGoals([
      ...goals,
      {
        goal_text: '',
        category: planType === 'SAFETY_PLAN' ? 'SAFETY' : 'WELLNESS',
        target_date: '',
        status: 'NOT_STARTED',
        sort_order: goals.length + 1,
        activities: [
          {
            activity_text: '',
            responsible_name: 'Caseworker & Family',
            responsible_type: 'JOINT',
            due_date: '',
            status: 'NOT_STARTED',
            sort_order: 1,
          },
        ],
      },
    ]);
  };

  const removeGoal = (index) => {
    setGoals(goals.filter((_, i) => i !== index));
  };

  const updateGoal = (index, field, value) => {
    const updated = [...goals];
    updated[index][field] = value;
    setGoals(updated);
  };

  const addActivity = (goalIndex) => {
    const updated = [...goals];
    updated[goalIndex].activities.push({
      activity_text: '',
      responsible_name: 'Caseworker',
      responsible_type: 'WORKER',
      due_date: '',
      status: 'NOT_STARTED',
      sort_order: updated[goalIndex].activities.length + 1,
    });
    setGoals(updated);
  };

  const removeActivity = (goalIndex, actIndex) => {
    const updated = [...goals];
    updated[goalIndex].activities = updated[goalIndex].activities.filter((_, i) => i !== actIndex);
    setGoals(updated);
  };

  const updateActivity = (goalIndex, actIndex, field, value) => {
    const updated = [...goals];
    updated[goalIndex].activities[actIndex][field] = value;
    setGoals(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Please provide a Plan Title.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        case_id: caseId,
        plan_type: planType,
        title: title.trim(),
        meeting_date: meetingDate || null,
        meeting_location: meetingLocation.trim() || null,
        narrative: narrative.trim() || null,
        assessment_ids: selectedAssessmentIds,
        participants: participants
          .filter((p) => p.name.trim())
          .map((p) => ({
            name: p.name.trim(),
            role: p.role,
            relationship: p.relationship,
            participant_type: p.participant_type,
            signature_required: p.signature_required,
            attendance_status: p.attendance_status,
          })),
        concerns: concerns
          .filter((c) => c.statement.trim())
          .map((c, i) => ({
            concern_type: c.concern_type,
            statement: c.statement.trim(),
            severity: c.severity,
            sort_order: i + 1,
          })),
        strengths: strengths
          .filter((s) => s.statement.trim())
          .map((s, i) => ({
            category: s.category,
            statement: s.statement.trim(),
            sort_order: i + 1,
          })),
        goals: goals
          .filter((g) => g.goal_text.trim())
          .map((g, i) => ({
            goal_text: g.goal_text.trim(),
            category: g.category,
            target_date: g.target_date || null,
            status: g.status,
            sort_order: i + 1,
            activities: g.activities
              .filter((a) => a.activity_text.trim())
              .map((a, j) => ({
                activity_text: a.activity_text.trim(),
                responsible_name: a.responsible_name.trim(),
                responsible_type: a.responsible_type,
                due_date: a.due_date || null,
                status: a.status,
                sort_order: j + 1,
              })),
          })),
      };

      const created = await plansApi.create(caseId, payload);
      onCreated(created);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create plan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-6 border-b border-border flex items-center justify-between bg-muted/30">
          <div className="flex items-center gap-3">
            <div
              className={`p-2.5 rounded-xl ${
                planType === 'SAFETY_PLAN'
                  ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                  : 'bg-purple-500/10 text-purple-600 dark:text-purple-400'
              }`}
            >
              {planType === 'SAFETY_PLAN' ? <Shield className="w-6 h-6" /> : <FileText className="w-6 h-6" />}
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">Author Family Wellness Plan</h2>
              <p className="text-xs text-muted-foreground">
                Child Welfare Standardized Planning, Version 1 Draft
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-8">
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-600 dark:text-rose-400 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Section 1: Plan Type & Metadata */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" /> Plan Core Details
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground">Plan Classification *</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setPlanType('SAFETY_PLAN');
                      if (!title) setTitle('Immediate Safety & Protection Protocol');
                    }}
                    className={`p-3 rounded-xl border text-left transition flex flex-col gap-1 ${
                      planType === 'SAFETY_PLAN'
                        ? 'border-rose-500 bg-rose-500/10 text-rose-700 dark:text-rose-300 font-semibold'
                        : 'border-border bg-card text-muted-foreground hover:bg-muted/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold">Safety Plan</span>
                      {planType === 'SAFETY_PLAN' && <Check className="w-3.5 h-3.5" />}
                    </div>
                    <span className="text-[11px] font-normal opacity-80">Crisis mitigation & immediate protection</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setPlanType('CASE_PLAN');
                      if (!title) setTitle('Comprehensive Family Wellness Plan');
                    }}
                    className={`p-3 rounded-xl border text-left transition flex flex-col gap-1 ${
                      planType === 'CASE_PLAN'
                        ? 'border-purple-500 bg-purple-500/10 text-purple-700 dark:text-purple-300 font-semibold'
                        : 'border-border bg-card text-muted-foreground hover:bg-muted/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold">Case Plan</span>
                      {planType === 'CASE_PLAN' && <Check className="w-3.5 h-3.5" />}
                    </div>
                    <span className="text-[11px] font-normal opacity-80">Long-term healing, preservation & goals</span>
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground">Plan Title *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. 90-Day Family Wellness & Safety Protocol"
                  className="w-full px-3 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-muted-foreground" /> Meeting / Formulation Date
                </label>
                <input
                  type="date"
                  value={meetingDate}
                  onChange={(e) => setMeetingDate(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-muted-foreground" /> Meeting Location / Setting
                </label>
                <input
                  type="text"
                  value={meetingLocation}
                  onChange={(e) => setMeetingLocation(e.target.value)}
                  placeholder="e.g. Family Home, CRBCL Lodge, Virtual"
                  className="w-full px-3 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-foreground">Clinical Narrative / Context Overview</label>
              <textarea
                value={narrative}
                onChange={(e) => setNarrative(e.target.value)}
                rows={3}
                placeholder="Document the family context, Elder guidance, consensus decisions, and overarching purpose of this plan..."
                className="w-full px-3 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            {/* Linked Assessments */}
            {assessments.length > 0 && (
              <div className="space-y-2 pt-2">
                <label className="text-xs font-medium text-foreground">Link Completed Clinical Assessments</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-36 overflow-y-auto p-2 bg-muted/20 border rounded-lg">
                  {assessments.map((a) => (
                    <label
                      key={a.id}
                      className="flex items-center gap-2 p-2 bg-card border rounded-md text-xs cursor-pointer hover:bg-muted/50"
                    >
                      <input
                        type="checkbox"
                        checked={selectedAssessmentIds.includes(a.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedAssessmentIds([...selectedAssessmentIds, a.id]);
                          } else {
                            setSelectedAssessmentIds(selectedAssessmentIds.filter((id) => id !== a.id));
                          }
                        }}
                        className="rounded border-input text-primary"
                      />
                      <span className="font-medium truncate">{a.title || a.template_name || 'Assessment'}</span>
                      <span className="text-[10px] text-muted-foreground ml-auto">{a.status}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section 2: Participants */}
          <div className="space-y-4 border-t pt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Users className="w-4 h-4 text-emerald-500" /> Plan Participants & Signers
              </h3>
              <button
                type="button"
                onClick={addParticipant}
                className="text-xs text-primary hover:underline flex items-center gap-1 font-medium"
              >
                <Plus className="w-3.5 h-3.5" /> Add Participant
              </button>
            </div>

            <div className="space-y-3">
              {participants.map((p, idx) => (
                <div key={idx} className="p-3 bg-muted/20 border rounded-xl grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
                  <div className="md:col-span-4">
                    <input
                      type="text"
                      value={p.name}
                      onChange={(e) => updateParticipant(idx, 'name', e.target.value)}
                      placeholder="Participant Full Name *"
                      className="w-full px-2.5 py-1.5 bg-background border rounded text-xs focus:ring-1 focus:ring-primary"
                    />
                  </div>
                  <div className="md:col-span-3">
                    <select
                      value={p.role}
                      onChange={(e) => updateParticipant(idx, 'role', e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-background border rounded text-xs"
                    >
                      <option value="Primary Caregiver">Primary Caregiver</option>
                      <option value="Co-Parent / Partner">Co-Parent / Partner</option>
                      <option value="Youth / Child">Youth / Child</option>
                      <option value="Elder / Knowledge Keeper">Elder / Knowledge Keeper</option>
                      <option value="Extended Kin">Extended Kin</option>
                      <option value="Lead Caseworker">Lead Caseworker</option>
                      <option value="Clinical Therapist">Clinical Therapist</option>
                      <option value="Support Worker">Support Worker</option>
                    </select>
                  </div>
                  <div className="md:col-span-3">
                    <select
                      value={p.participant_type}
                      onChange={(e) => updateParticipant(idx, 'participant_type', e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-background border rounded text-xs"
                    >
                      <option value="FAMILY_MEMBER">Family Member</option>
                      <option value="COMMUNITY_SUPPORT">Community Support</option>
                      <option value="WORKER">Caseworker / Staff</option>
                      <option value="PROVIDER">External Provider</option>
                    </select>
                  </div>
                  <div className="md:col-span-1 flex items-center justify-center">
                    <label className="flex items-center gap-1 text-[11px] text-muted-foreground cursor-pointer" title="Requires Electronic Signature">
                      <input
                        type="checkbox"
                        checked={p.signature_required}
                        onChange={(e) => updateParticipant(idx, 'signature_required', e.target.checked)}
                        className="rounded"
                      />
                      <span>Sign</span>
                    </label>
                  </div>
                  <div className="md:col-span-1 flex justify-end">
                    {participants.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeParticipant(idx)}
                        className="p-1 text-rose-500 hover:bg-rose-500/10 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Concerns / Harm Statements */}
          <div className="space-y-4 border-t pt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" /> Concerns & Harm Statements
              </h3>
              <button
                type="button"
                onClick={addConcern}
                className="text-xs text-primary hover:underline flex items-center gap-1 font-medium"
              >
                <Plus className="w-3.5 h-3.5" /> Add Concern
              </button>
            </div>

            <div className="space-y-3">
              {concerns.map((c, idx) => (
                <div key={idx} className="p-3 bg-muted/20 border rounded-xl space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <select
                        value={c.concern_type}
                        onChange={(e) => updateConcern(idx, 'concern_type', e.target.value)}
                        className="px-2.5 py-1 bg-background border rounded text-xs font-medium"
                      >
                        <option value="SAFETY_THREAT">Safety Threat</option>
                        <option value="RISK_FACTOR">Risk Factor</option>
                        <option value="HARM_STATEMENT">Harm Statement</option>
                        <option value="UNMET_NEED">Unmet Need</option>
                      </select>

                      <select
                        value={c.severity}
                        onChange={(e) => updateConcern(idx, 'severity', e.target.value)}
                        className="px-2.5 py-1 bg-background border rounded text-xs font-semibold text-rose-600 dark:text-rose-400"
                      >
                        <option value="CRITICAL">Critical</option>
                        <option value="HIGH">High</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="LOW">Low</option>
                      </select>
                    </div>

                    {concerns.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeConcern(idx)}
                        className="p-1 text-rose-500 hover:bg-rose-500/10 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <textarea
                    value={c.statement}
                    onChange={(e) => updateConcern(idx, 'statement', e.target.value)}
                    rows={2}
                    placeholder="Specific, behavioral harm statement or danger concern..."
                    className="w-full px-2.5 py-1.5 bg-background border rounded text-xs focus:ring-1 focus:ring-primary"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Strengths & Cultural Protections */}
          <div className="space-y-4 border-t pt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Heart className="w-4 h-4 text-rose-500" /> Strengths & Protective Capacities
              </h3>
              <button
                type="button"
                onClick={addStrength}
                className="text-xs text-primary hover:underline flex items-center gap-1 font-medium"
              >
                <Plus className="w-3.5 h-3.5" /> Add Strength
              </button>
            </div>

            <div className="space-y-3">
              {strengths.map((s, idx) => (
                <div key={idx} className="p-3 bg-muted/20 border rounded-xl space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <select
                      value={s.category}
                      onChange={(e) => updateStrength(idx, 'category', e.target.value)}
                      className="px-2.5 py-1 bg-background border rounded text-xs font-medium text-emerald-600 dark:text-emerald-400"
                    >
                      <option value="CULTURAL_SPIRITUAL">Cultural & Spiritual Grounding</option>
                      <option value="FAMILY_UNITY">Family Unity & Kinship Network</option>
                      <option value="COMMUNITY_SUPPORT">Community Supports & Allies</option>
                      <option value="PARENTING_CAPACITY">Parenting & Protective Capacity</option>
                      <option value="ENVIRONMENTAL_SAFETY">Safe Physical Environment</option>
                    </select>

                    {strengths.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeStrength(idx)}
                        className="p-1 text-rose-500 hover:bg-rose-500/10 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <textarea
                    value={s.statement}
                    onChange={(e) => updateStrength(idx, 'statement', e.target.value)}
                    rows={2}
                    placeholder="Specific family strength, cultural connection, or demonstrated protective capacity..."
                    className="w-full px-2.5 py-1.5 bg-background border rounded text-xs focus:ring-1 focus:ring-primary"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Section 5: Goals & Structured Activities */}
          <div className="space-y-4 border-t pt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Target className="w-4 h-4 text-blue-500" /> Goals & Concrete Activities
              </h3>
              <button
                type="button"
                onClick={addGoal}
                className="text-xs text-primary hover:underline flex items-center gap-1 font-medium"
              >
                <Plus className="w-3.5 h-3.5" /> Add Goal
              </button>
            </div>

            <div className="space-y-6">
              {goals.map((g, gIdx) => (
                <div key={gIdx} className="p-4 bg-muted/20 border rounded-2xl space-y-4">
                  {/* Goal Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-primary/10 text-primary font-bold text-xs rounded">
                        Goal #{gIdx + 1}
                      </span>
                      <select
                        value={g.category}
                        onChange={(e) => updateGoal(gIdx, 'category', e.target.value)}
                        className="px-2.5 py-1 bg-background border rounded text-xs font-semibold"
                      >
                        <option value="SAFETY">Safety</option>
                        <option value="WELLNESS">Family Wellness</option>
                        <option value="CULTURAL">Cultural Connection</option>
                        <option value="PARENTING">Parenting</option>
                        <option value="HEALTH">Health & Well-being</option>
                        <option value="HOUSING">Housing & Environment</option>
                      </select>
                    </div>

                    <div className="flex items-center gap-2">
                      <label className="text-xs text-muted-foreground flex items-center gap-1">
                        <span>Target:</span>
                        <input
                          type="date"
                          value={g.target_date}
                          onChange={(e) => updateGoal(gIdx, 'target_date', e.target.value)}
                          className="px-2 py-0.5 bg-background border rounded text-xs"
                        />
                      </label>

                      {goals.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeGoal(gIdx)}
                          className="p-1 text-rose-500 hover:bg-rose-500/10 rounded"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Goal Text */}
                  <div>
                    <textarea
                      value={g.goal_text}
                      onChange={(e) => updateGoal(gIdx, 'goal_text', e.target.value)}
                      rows={2}
                      placeholder="SMART Goal Description (Specific, Measurable, Achievable, Relevant, Time-bound)..."
                      className="w-full px-3 py-2 bg-background border rounded-lg text-xs focus:ring-1 focus:ring-primary"
                    />
                  </div>

                  {/* Child Activities */}
                  <div className="pl-4 border-l-2 border-primary/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-muted-foreground">Required Activities & Action Steps</span>
                      <button
                        type="button"
                        onClick={() => addActivity(gIdx)}
                        className="text-[11px] text-primary hover:underline flex items-center gap-1 font-medium"
                      >
                        <Plus className="w-3 h-3" /> Add Activity
                      </button>
                    </div>

                    <div className="space-y-2">
                      {g.activities.map((a, aIdx) => (
                        <div key={aIdx} className="p-2.5 bg-card border rounded-lg grid grid-cols-1 md:grid-cols-12 gap-2 items-center">
                          <div className="md:col-span-6">
                            <input
                              type="text"
                              value={a.activity_text}
                              onChange={(e) => updateActivity(gIdx, aIdx, 'activity_text', e.target.value)}
                              placeholder="Action step / commitment..."
                              className="w-full px-2 py-1 bg-background border rounded text-xs"
                            />
                          </div>
                          <div className="md:col-span-3">
                            <input
                              type="text"
                              value={a.responsible_name}
                              onChange={(e) => updateActivity(gIdx, aIdx, 'responsible_name', e.target.value)}
                              placeholder="Responsible person..."
                              className="w-full px-2 py-1 bg-background border rounded text-xs"
                            />
                          </div>
                          <div className="md:col-span-2">
                            <input
                              type="date"
                              value={a.due_date}
                              onChange={(e) => updateActivity(gIdx, aIdx, 'due_date', e.target.value)}
                              className="w-full px-2 py-1 bg-background border rounded text-xs"
                            />
                          </div>
                          <div className="md:col-span-1 flex justify-end">
                            {g.activities.length > 1 && (
                              <button
                                type="button"
                                onClick={() => removeActivity(gIdx, aIdx)}
                                className="p-1 text-rose-500 hover:bg-rose-500/10 rounded"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="pt-6 border-t flex items-center justify-end gap-3 sticky bottom-0 bg-card py-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-xl text-sm font-medium text-muted-foreground hover:bg-muted transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-sm shadow-md hover:bg-primary/90 transition flex items-center gap-2"
            >
              {loading ? (
                <span>Authoring Plan...</span>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>Create Plan Draft</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

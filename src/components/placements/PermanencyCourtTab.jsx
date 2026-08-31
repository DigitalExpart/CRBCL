import React, { useState, useEffect } from 'react';
import {
  Scale,
  Users,
  Compass,
  Plus,
  Calendar,
  Clock,
  MapPin,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Globe,
  Gavel,
  ShieldCheck,
  Edit2,
  Trash2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { placementsApi } from '@/api/placements';

export default function PermanencyCourtTab({ caseId, caseData, people = [] }) {
  const [permanencyPlans, setPermanencyPlans] = useState([]);
  const [visitationPlans, setVisitationPlans] = useState([]);
  const [courtEvents, setCourtEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showPermanencyModal, setShowPermanencyModal] = useState(false);
  const [showVisitationModal, setShowVisitationModal] = useState(false);
  const [showCourtModal, setShowCourtModal] = useState(false);

  // Forms
  const [permForm, setPermForm] = useState({
    child_id: '',
    primary_goal: 'REUNIFICATION',
    concurrent_goal: 'CUSTOMARY_CARE',
    target_date: '',
    custom_adoption_considered: false,
    cultural_belonging_plan: '',
    review_frequency_months: 6,
    notes: '',
  });

  const [visitForm, setVisitForm] = useState({
    child_id: '',
    visiting_party_name: '',
    relationship_to_child: 'Mother',
    frequency: 'WEEKLY',
    duration_minutes: 90,
    location_type: 'FAMILY_WELLNESS_CENTER',
    supervision_level: 'SUPERVISED',
    transportation_provider: 'Agency Transport',
    safety_measures: 'No unauthorized third parties.',
    cultural_elements: 'Traditional storytelling and shared meal.',
    notes: '',
  });

  const [courtForm, setCourtForm] = useState({
    hearing_type: 'PERMANENCY_HEARING',
    court_level: 'PROVINCIAL_COURT',
    docket_number: '',
    scheduled_date: new Date().toISOString().split('T')[0],
    judge_name: '',
    band_representation_present: true,
    court_orders_issued: '',
    next_hearing_date: '',
    legal_status: 'TEMPORARY_ORDER_EXTENDED',
    notes: '',
  });

  const loadAllData = async () => {
    try {
      setLoading(true);
      const [permRes, visitRes, courtRes] = await Promise.all([
        placementsApi.listPermanencyPlans(caseId).catch(() => []),
        placementsApi.listVisitationPlans(caseId).catch(() => []),
        placementsApi.listCourtEvents(caseId).catch(() => []),
      ]);
      setPermanencyPlans(permRes || []);
      setVisitationPlans(visitRes || []);
      setCourtEvents(courtRes || []);
    } catch (err) {
      console.error('Failed to load permanency and court data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      loadAllData();
    }
  }, [caseId]);

  const handleCreatePermanency = async (e) => {
    e.preventDefault();
    try {
      await placementsApi.createPermanencyPlan(caseId, permForm);
      setShowPermanencyModal(false);
      loadAllData();
    } catch (err) {
      console.error('Failed to create permanency plan:', err);
      alert(err.message || 'Failed to create permanency plan');
    }
  };

  const handleCreateVisitation = async (e) => {
    e.preventDefault();
    try {
      await placementsApi.createVisitationPlan(caseId, visitForm);
      setShowVisitationModal(false);
      loadAllData();
    } catch (err) {
      console.error('Failed to create visitation plan:', err);
      alert(err.message || 'Failed to create visitation plan');
    }
  };

  const handleCreateCourt = async (e) => {
    e.preventDefault();
    try {
      await placementsApi.createCourtEvent(caseId, courtForm);
      setShowCourtModal(false);
      loadAllData();
    } catch (err) {
      console.error('Failed to create court event:', err);
      alert(err.message || 'Failed to create court event');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Permanency Plans</p>
              <p className="text-xl font-bold text-foreground">{permanencyPlans.length}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-500/5 border-blue-500/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Active Visitation Plans</p>
              <p className="text-xl font-bold text-blue-600 dark:text-blue-400">{visitationPlans.length}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-purple-500/5 border-purple-500/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Court Hearings & Orders</p>
              <p className="text-xl font-bold text-purple-600 dark:text-purple-400">{courtEvents.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sub Tabs: Permanency Plans, Visitation Plans, Court Proceedings */}
      <Tabs defaultValue="permanency" className="w-full">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <TabsList className="grid grid-cols-3 max-w-md">
            <TabsTrigger value="permanency">Permanency Plans ({permanencyPlans.length})</TabsTrigger>
            <TabsTrigger value="visitation">Family Visitation ({visitationPlans.length})</TabsTrigger>
            <TabsTrigger value="court">Court Events ({courtEvents.length})</TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                if (people.length > 0) setVisitForm({ ...visitForm, child_id: people[0].person_id });
                setShowVisitationModal(true);
              }}
              className="gap-1.5 text-xs"
            >
              <Plus className="w-3.5 h-3.5" /> Plan Family Visit
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowCourtModal(true)}
              className="gap-1.5 text-xs text-purple-600 border-purple-500/30 hover:bg-purple-500/10"
            >
              <Plus className="w-3.5 h-3.5" /> Log Court Event
            </Button>
            <Button
              size="sm"
              onClick={() => {
                if (people.length > 0) setPermForm({ ...permForm, child_id: people[0].person_id });
                setShowPermanencyModal(true);
              }}
              className="gap-1.5 text-xs"
            >
              <Plus className="w-3.5 h-3.5" /> New Permanency Plan
            </Button>
          </div>
        </div>

        {/* --- Permanency Plans Tab --- */}
        <TabsContent value="permanency" className="space-y-4">
          {permanencyPlans.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <Compass className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
              <p className="font-medium text-sm text-foreground">No permanency plans established</p>
              <p className="text-xs text-muted-foreground mt-1">
                Establish concurrent permanency goals honoring Indigenous customary care and family reunification.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {permanencyPlans.map((plan) => (
                <div key={plan.id} className="p-5 rounded-lg border bg-card/60 hover:bg-card transition-all space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-foreground">Primary: {plan.primary_goal}</span>
                      {plan.concurrent_goal && (
                        <Badge variant="outline" className="text-xs bg-muted">
                          Concurrent: {plan.concurrent_goal}
                        </Badge>
                      )}
                      <Badge
                        variant="outline"
                        className={
                          plan.status === 'ACTIVE'
                            ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20'
                            : 'bg-muted'
                        }
                      >
                        {plan.status}
                      </Badge>
                    </div>
                    {plan.target_date && (
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" /> Target Date: {plan.target_date}
                      </span>
                    )}
                  </div>

                  {plan.cultural_belonging_plan && (
                    <div className="text-xs bg-muted/30 p-2.5 rounded border">
                      <span className="font-semibold text-foreground flex items-center gap-1 mb-1">
                        <Globe className="w-3.5 h-3.5 text-primary" /> Cultural Belonging & Identity Strategy:
                      </span>
                      {plan.cultural_belonging_plan}
                    </div>
                  )}

                  {plan.notes && <p className="text-xs text-muted-foreground italic">"{plan.notes}"</p>}
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* --- Family Visitation Tab --- */}
        <TabsContent value="visitation" className="space-y-4">
          {visitationPlans.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <Users className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
              <p className="font-medium text-sm text-foreground">No visitation plans recorded</p>
              <p className="text-xs text-muted-foreground mt-1">
                Design supportive, culturally enriching family visitation schedules.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {visitationPlans.map((v) => (
                <div key={v.id} className="p-4 rounded-lg border bg-card/60 hover:bg-card transition-all space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-foreground">
                        Visits with: {v.visiting_party_name} ({v.relationship_to_child})
                      </span>
                      <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">
                        {v.frequency} • {v.duration_minutes} mins
                      </Badge>
                      <Badge variant="secondary">{v.supervision_level}</Badge>
                    </div>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5" /> {v.location_type?.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs bg-muted/30 p-2.5 rounded-md">
                    {v.cultural_elements && (
                      <div>
                        <span className="font-medium text-foreground block">Cultural / Customary Activities:</span>
                        <span className="text-muted-foreground">{v.cultural_elements}</span>
                      </div>
                    )}
                    {v.safety_measures && (
                      <div>
                        <span className="font-medium text-foreground block">Safety Measures:</span>
                        <span className="text-muted-foreground">{v.safety_measures}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* --- Court Events Tab --- */}
        <TabsContent value="court" className="space-y-4">
          {courtEvents.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <Gavel className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
              <p className="font-medium text-sm text-foreground">No court proceedings logged</p>
              <p className="text-xs text-muted-foreground mt-1">
                Track court hearings, docket numbers, band legal representation, and judicial orders.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {courtEvents.map((c) => (
                <div key={c.id} className="p-4 rounded-lg border bg-card/60 hover:bg-card transition-all space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <Badge className="bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/20 font-medium">
                        {c.hearing_type?.replace(/_/g, ' ')}
                      </Badge>
                      <span className="font-semibold text-xs text-foreground">
                        Docket #{c.docket_number || 'N/A'} • {c.court_level?.replace(/_/g, ' ')}
                      </span>
                      {c.band_representation_present && (
                        <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20 text-xs gap-1 font-medium">
                          <ShieldCheck className="w-3 h-3" /> Band Rep Present
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" /> Date: {c.scheduled_date}
                    </span>
                  </div>

                  {c.judge_name && (
                    <p className="text-xs text-muted-foreground">
                      Presiding Judicial Officer: <span className="font-medium text-foreground">{c.judge_name}</span>
                    </p>
                  )}

                  {c.court_orders_issued && (
                    <div className="text-xs bg-purple-500/5 p-2.5 rounded border border-purple-500/15">
                      <span className="font-semibold text-purple-900 dark:text-purple-200 block mb-1">
                        Court Orders Issued:
                      </span>
                      <span className="text-foreground">{c.court_orders_issued}</span>
                    </div>
                  )}

                  {c.next_hearing_date && (
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-primary" />
                      Next Hearing Scheduled: <span className="font-semibold text-foreground">{c.next_hearing_date}</span>
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* --- Modal: Create Permanency Plan --- */}
      <Dialog open={showPermanencyModal} onOpenChange={setShowPermanencyModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Establish Permanency Plan</DialogTitle>
            <DialogDescription>
              Define concurrent permanency goals, cultural belonging plans, and target milestones.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreatePermanency} className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold">Child *</label>
              <Select
                value={permForm.child_id}
                onValueChange={(val) => setPermForm({ ...permForm, child_id: val })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select child..." />
                </SelectTrigger>
                <SelectContent>
                  {people.map((p) => (
                    <SelectItem key={p.person_id} value={p.person_id}>
                      {p.person?.first_name} {p.person?.last_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Primary Goal *</label>
                <Select
                  value={permForm.primary_goal}
                  onValueChange={(val) => setPermForm({ ...permForm, primary_goal: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="REUNIFICATION">Family Reunification</SelectItem>
                    <SelectItem value="CUSTOMARY_CARE">Band Customary Care</SelectItem>
                    <SelectItem value="CUSTOMARY_ADOPTION">Customary Adoption</SelectItem>
                    <SelectItem value="PERMANENT_GUARDIANSHIP">Permanent Guardianship</SelectItem>
                    <SelectItem value="INDEPENDENT_LIVING">Independent Youth</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-semibold">Concurrent Goal</label>
                <Select
                  value={permForm.concurrent_goal}
                  onValueChange={(val) => setPermForm({ ...permForm, concurrent_goal: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CUSTOMARY_CARE">Band Customary Care</SelectItem>
                    <SelectItem value="CUSTOMARY_ADOPTION">Customary Adoption</SelectItem>
                    <SelectItem value="PERMANENT_GUARDIANSHIP">Permanent Guardianship</SelectItem>
                    <SelectItem value="KINSHIP_LEGAL_CUSTODY">Kinship Legal Custody</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold">Target Completion Date</label>
              <Input
                type="date"
                className="mt-1"
                value={permForm.target_date}
                onChange={(e) => setPermForm({ ...permForm, target_date: e.target.value })}
              />
            </div>

            <div>
              <label className="text-xs font-semibold">Cultural Belonging & Identity Plan</label>
              <Textarea
                className="mt-1"
                placeholder="Plan for maintaining First Nation language, culture, Elder mentorship, and band ceremonies..."
                value={permForm.cultural_belonging_plan}
                onChange={(e) => setPermForm({ ...permForm, cultural_belonging_plan: e.target.value })}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowPermanencyModal(false)}>
                Cancel
              </Button>
              <Button type="submit">Establish Plan</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- Modal: Plan Family Visitation --- */}
      <Dialog open={showVisitationModal} onOpenChange={setShowVisitationModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Family Visitation Plan</DialogTitle>
            <DialogDescription>
              Schedule regular, supportive visitation to maintain family bonds and emotional security.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateVisitation} className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold">Child *</label>
              <Select
                value={visitForm.child_id}
                onValueChange={(val) => setVisitForm({ ...visitForm, child_id: val })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select child..." />
                </SelectTrigger>
                <SelectContent>
                  {people.map((p) => (
                    <SelectItem key={p.person_id} value={p.person_id}>
                      {p.person?.first_name} {p.person?.last_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Visiting Party Name *</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. John Doe"
                  value={visitForm.visiting_party_name}
                  onChange={(e) => setVisitForm({ ...visitForm, visiting_party_name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Relationship</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. Father, Grandmother"
                  value={visitForm.relationship_to_child}
                  onChange={(e) => setVisitForm({ ...visitForm, relationship_to_child: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-xs font-semibold">Frequency</label>
                <Select
                  value={visitForm.frequency}
                  onValueChange={(val) => setVisitForm({ ...visitForm, frequency: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="WEEKLY">Weekly</SelectItem>
                    <SelectItem value="BI_WEEKLY">Bi-Weekly</SelectItem>
                    <SelectItem value="MONTHLY">Monthly</SelectItem>
                    <SelectItem value="TWICE_WEEKLY">Twice Weekly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-semibold">Duration (Mins)</label>
                <Input
                  type="number"
                  className="mt-1"
                  value={visitForm.duration_minutes}
                  onChange={(e) => setVisitForm({ ...visitForm, duration_minutes: parseInt(e.target.value) })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Supervision</label>
                <Select
                  value={visitForm.supervision_level}
                  onValueChange={(val) => setVisitForm({ ...visitForm, supervision_level: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SUPERVISED">Supervised</SelectItem>
                    <SelectItem value="MONITORED">Monitored</SelectItem>
                    <SelectItem value="UNSUPERVISED">Unsupervised</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold">Cultural & Community Activities</label>
              <Input
                className="mt-1"
                placeholder="e.g. Traditional lunch, beading, smudge with Elder"
                value={visitForm.cultural_elements}
                onChange={(e) => setVisitForm({ ...visitForm, cultural_elements: e.target.value })}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowVisitationModal(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Visitation Plan</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- Modal: Log Court Event --- */}
      <Dialog open={showCourtModal} onOpenChange={setShowCourtModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Log Court Hearing / Event</DialogTitle>
            <DialogDescription>
              Record court outcomes, judicial orders, docket details, and band legal representation.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateCourt} className="space-y-4 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Hearing Type *</label>
                <Select
                  value={courtForm.hearing_type}
                  onValueChange={(val) => setCourtForm({ ...courtForm, hearing_type: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PERMANENCY_HEARING">Permanency Hearing</SelectItem>
                    <SelectItem value="TEMPORARY_CUSTODY_REVIEW">Temporary Custody Review</SelectItem>
                    <SelectItem value="INITIAL_HEARING">Initial Custody Hearing</SelectItem>
                    <SelectItem value="CUSTOMARY_CARE_CONFIRMATION">Customary Care Hearing</SelectItem>
                    <SelectItem value="DISCHARGE_HEARING">Discharge Hearing</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-semibold">Court Date *</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={courtForm.scheduled_date}
                  onChange={(e) => setCourtForm({ ...courtForm, scheduled_date: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Court Docket #</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. CR-2026-0894"
                  value={courtForm.docket_number}
                  onChange={(e) => setCourtForm({ ...courtForm, docket_number: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Judge / Officer Name</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. Judge Morrison"
                  value={courtForm.judge_name}
                  onChange={(e) => setCourtForm({ ...courtForm, judge_name: e.target.value })}
                />
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg border">
              <input
                type="checkbox"
                id="band_rep"
                className="rounded border-gray-300 text-primary focus:ring-primary"
                checked={courtForm.band_representation_present}
                onChange={(e) => setCourtForm({ ...courtForm, band_representation_present: e.target.checked })}
              />
              <label htmlFor="band_rep" className="text-xs font-medium cursor-pointer">
                First Nation Band Representative or Legal Counsel present at hearing
              </label>
            </div>

            <div>
              <label className="text-xs font-semibold">Court Orders Issued</label>
              <Textarea
                className="mt-1"
                placeholder="Specific judicial rulings, custody terms, supervision conditions..."
                value={courtForm.court_orders_issued}
                onChange={(e) => setCourtForm({ ...courtForm, court_orders_issued: e.target.value })}
              />
            </div>

            <div>
              <label className="text-xs font-semibold">Next Hearing Date</label>
              <Input
                type="date"
                className="mt-1"
                value={courtForm.next_hearing_date}
                onChange={(e) => setCourtForm({ ...courtForm, next_hearing_date: e.target.value })}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowCourtModal(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Court Event</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

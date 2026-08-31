import React, { useState, useEffect } from 'react';
import {
  Home,
  AlertCircle,
  Plus,
  Calendar,
  User,
  Building,
  CheckCircle2,
  AlertTriangle,
  Clock,
  DollarSign,
  Globe,
  ArrowRight,
  LogOut,
  Shield,
  ShieldAlert,
  Edit2,
  FileText,
  BadgeCheck,
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
import { placementHomesApi } from '@/api/placementHomes';
import { Link } from 'react-router-dom';

export default function PlacementsTab({ caseId, caseData, people = [] }) {
  const [placements, setPlacements] = useState([]);
  const [inHomePlacements, setInHomePlacements] = useState([]);
  const [removals, setRemovals] = useState([]);
  const [discharges, setDischarges] = useState([]);
  const [availableHomes, setAvailableHomes] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showPlacementModal, setShowPlacementModal] = useState(false);
  const [showInHomeModal, setShowInHomeModal] = useState(false);
  const [showRemovalModal, setShowRemovalModal] = useState(false);
  const [showRespiteModal, setShowRespiteModal] = useState(false);
  const [showDischargeModal, setShowDischargeModal] = useState(false);
  const [selectedPlacementForRespite, setSelectedPlacementForRespite] = useState(null);
  const [selectedPlacementForDischarge, setSelectedPlacementForDischarge] = useState(null);

  // Forms
  const [placementForm, setPlacementForm] = useState({
    child_id: '',
    removal_episode_id: '',
    placement_home_id: '',
    placement_type: 'KINSHIP',
    provider_name: '',
    provider_contact: '',
    provider_address: '',
    start_date: new Date().toISOString().split('T')[0],
    primary_caregiver_name: '',
    per_diem_rate: '',
    cultural_plan_in_place: true,
    placement_notes: '',
  });


  const [inHomeForm, setInHomeForm] = useState({
    child_id: '',
    caregiver_name: '',
    caregiver_relationship: 'Mother',
    caregiver_phone: '',
    address: '',
    safety_plan_id: '',
    supervision_level: 'INTENSIVE',
    start_date: new Date().toISOString().split('T')[0],
    notes: '',
  });

  const [removalForm, setRemovalForm] = useState({
    child_id: '',
    removal_date: new Date().toISOString().split('T')[0],
    removal_type: 'TEMPORARY_CUSTODY',
    authority_type: 'COURT_ORDER',
    reason_for_removal: '',
    notified_first_nation: true,
    police_assisted: false,
    child_belongings_inventory: '',
  });

  const [respiteForm, setRespiteForm] = useState({
    respite_provider_name: '',
    respite_caregiver_name: '',
    respite_contact: '',
    start_date: '',
    end_date: '',
    reason_for_respite: 'Scheduled caregiver wellness respite.',
  });

  const [dischargeForm, setDischargeForm] = useState({
    placement_episode_id: '',
    discharge_date: new Date().toISOString().split('T')[0],
    discharge_reason: 'REUNIFICATION',
    destination_type: 'PARENT_HOME',
    destination_caregiver_name: '',
    notes: '',
  });

  const loadAllPlacements = async () => {
    try {
      setLoading(true);
      const [placementsRes, inHomeRes, removalsRes, dischargesRes, homesRes] = await Promise.all([
        placementsApi.listPlacements(caseId).catch(() => []),
        placementsApi.listInHomePlacements(caseId).catch(() => []),
        placementsApi.listRemovals(caseId).catch(() => []),
        placementsApi.listDischarges(caseId).catch(() => []),
        placementHomesApi.list({ page_size: 100 }).catch(() => ({ data: { items: [] } })),
      ]);
      setPlacements(placementsRes || []);
      setInHomePlacements(inHomeRes || []);
      setRemovals(removalsRes || []);
      setDischarges(dischargesRes || []);
      setAvailableHomes(homesRes?.data?.items || []);
    } catch (err) {
      console.error('Failed to load placement data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      loadAllPlacements();
    }
  }, [caseId]);

  // Handlers
  const handleCreatePlacement = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...placementForm,
        placement_home_id: placementForm.placement_home_id || null,
        removal_episode_id: placementForm.removal_episode_id || null,
        per_diem_rate: placementForm.per_diem_rate ? parseFloat(placementForm.per_diem_rate) : null,
      };
      await placementsApi.createPlacement(caseId, payload);
      setShowPlacementModal(false);
      loadAllPlacements();
    } catch (err) {
      console.error('Failed to create placement:', err);
      alert(err.response?.data?.detail || err.message || 'Failed to create placement');
    }
  };


  const handleCreateInHome = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...inHomeForm,
        safety_plan_id: inHomeForm.safety_plan_id || null,
      };
      await placementsApi.createInHomePlacement(caseId, payload);
      setShowInHomeModal(false);
      loadAllPlacements();
    } catch (err) {
      console.error('Failed to create in-home placement:', err);
      alert(err.message || 'Failed to create in-home placement');
    }
  };

  const handleCreateRemoval = async (e) => {
    e.preventDefault();
    try {
      await placementsApi.createRemoval(caseId, removalForm);
      setShowRemovalModal(false);
      loadAllPlacements();
    } catch (err) {
      console.error('Failed to create removal episode:', err);
      alert(err.message || 'Failed to create removal episode');
    }
  };

  const handleCreateRespite = async (e) => {
    e.preventDefault();
    if (!selectedPlacementForRespite) return;
    try {
      await placementsApi.createRespite(selectedPlacementForRespite.id, respiteForm);
      setShowRespiteModal(false);
      loadAllPlacements();
    } catch (err) {
      console.error('Failed to create respite episode:', err);
      alert(err.message || 'Failed to create respite episode');
    }
  };

  const handleCreateDischarge = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...dischargeForm,
        placement_episode_id: selectedPlacementForDischarge ? selectedPlacementForDischarge.id : dischargeForm.placement_episode_id,
      };
      await placementsApi.createDischarge(caseId, payload);
      setShowDischargeModal(false);
      loadAllPlacements();
    } catch (err) {
      console.error('Failed to discharge placement:', err);
      alert(err.message || 'Failed to discharge placement');
    }
  };

  const activePrimaryPlacements = placements.filter((p) => p.status === 'ACTIVE');
  const activeInHome = inHomePlacements.filter((p) => p.status === 'ACTIVE');

  return (
    <div className="space-y-6">
      {/* Top Banner Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Home className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Active Placements</p>
              <p className="text-xl font-bold text-foreground">{activePrimaryPlacements.length}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-emerald-500/5 border-emerald-500/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">In-Home Placements</p>
              <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{activeInHome.length}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-amber-500/5 border-amber-500/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Removal Episodes</p>
              <p className="text-xl font-bold text-amber-600 dark:text-amber-400">{removals.length}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-500/5 border-blue-500/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <LogOut className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Discharged / Reunified</p>
              <p className="text-xl font-bold text-blue-600 dark:text-blue-400">{discharges.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-card rounded-lg border">
        <div>
          <h3 className="text-sm font-semibold">Placement & Removal Chain Actions</h3>
          <p className="text-xs text-muted-foreground">Manage the child's living arrangement, legal custody, respite, and reunification.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (people.length > 0) setInHomeForm({ ...inHomeForm, child_id: people[0].person_id });
              setShowInHomeModal(true);
            }}
            className="gap-1.5"
          >
            <Shield className="w-4 h-4 text-emerald-600" /> Log In-Home Placement
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (people.length > 0) setRemovalForm({ ...removalForm, child_id: people[0].person_id });
              setShowRemovalModal(true);
            }}
            className="gap-1.5 text-amber-600 border-amber-500/30 hover:bg-amber-500/10"
          >
            <ShieldAlert className="w-4 h-4" /> Record Removal
          </Button>
          <Button
            size="sm"
            onClick={() => {
              if (people.length > 0) setPlacementForm({ ...placementForm, child_id: people[0].person_id });
              setShowPlacementModal(true);
            }}
            className="gap-1.5"
          >
            <Plus className="w-4 h-4" /> Create Placement Episode
          </Button>
        </div>
      </div>

      {/* Sub Tabs: Out-of-Home Placements, In-Home Placements, Removals, Discharges */}
      <Tabs defaultValue="out_of_home" className="w-full">
        <TabsList className="grid grid-cols-4 max-w-2xl">
          <TabsTrigger value="out_of_home">Out-of-Home Placements ({placements.length})</TabsTrigger>
          <TabsTrigger value="in_home">In-Home ({inHomePlacements.length})</TabsTrigger>
          <TabsTrigger value="removals">Removals ({removals.length})</TabsTrigger>
          <TabsTrigger value="discharges">Discharges ({discharges.length})</TabsTrigger>
        </TabsList>

        {/* --- Out-of-Home Placements Content --- */}
        <TabsContent value="out_of_home" className="space-y-4 pt-2">
          {placements.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <Home className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
              <p className="font-medium text-sm text-foreground">No placement episodes recorded</p>
              <p className="text-xs text-muted-foreground mt-1">
                Record kinship care, foster care, or customary care placement episodes.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {placements.map((p) => (
                <div
                  key={p.id}
                  className="p-5 rounded-lg border bg-card/60 hover:bg-card hover:shadow-sm transition-all space-y-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-base text-foreground">{p.provider_name}</span>
                        <Badge
                          variant="outline"
                          className={
                            p.status === 'ACTIVE'
                              ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20'
                              : 'bg-muted text-muted-foreground'
                          }
                        >
                          {p.status}
                        </Badge>
                        <Badge variant="secondary">{p.placement_type}</Badge>
                        {p.cultural_plan_in_place && (
                          <Badge className="bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20 gap-1 font-medium">
                            <Globe className="w-3 h-3" /> Cultural Plan Active
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Primary Caregiver: <span className="font-medium text-foreground">{p.primary_caregiver_name || 'Not specified'}</span>
                        {p.provider_contact && <span> • Contact: {p.provider_contact}</span>}
                        {p.placement_home_id && (
                          <span className="ml-2">
                            • <Link to={`/placement-homes/${p.placement_home_id}`} className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline">
                              Registered Home Profile →
                            </Link>
                          </span>
                        )}
                      </p>
                    </div>


                    {p.status === 'ACTIVE' && (
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedPlacementForRespite(p);
                            setShowRespiteModal(true);
                          }}
                          className="gap-1 text-xs"
                        >
                          <Clock className="w-3.5 h-3.5" /> Schedule Respite
                        </Button>
                        <Button
                          size="sm"
                          variant="default"
                          onClick={() => {
                            setSelectedPlacementForDischarge(p);
                            setDischargeForm({ ...dischargeForm, placement_episode_id: p.id });
                            setShowDischargeModal(true);
                          }}
                          className="gap-1 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                        >
                          <LogOut className="w-3.5 h-3.5" /> Discharge / Reunified
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Dates & Per Diem */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-muted/30 p-3 rounded-md">
                    <div>
                      <span className="text-muted-foreground block">Start Date:</span>
                      <span className="font-semibold text-foreground">{p.start_date}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block">End Date:</span>
                      <span className="font-semibold text-foreground">{p.end_date || 'Active / Present'}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block">Per Diem Rate:</span>
                      <span className="font-semibold text-foreground">
                        {p.per_diem_rate ? `$${parseFloat(p.per_diem_rate).toFixed(2)}/day` : 'Standard Customary'}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block">Removal Link:</span>
                      <span className="font-semibold text-foreground">
                        {p.removal_episode_id ? 'Linked to Removal' : 'Voluntary / Agreement'}
                      </span>
                    </div>
                  </div>

                  {p.placement_notes && (
                    <p className="text-xs text-muted-foreground italic bg-card p-2 rounded border">
                      "{p.placement_notes}"
                    </p>
                  )}

                  {/* Respite History if any */}
                  {p.respite_episodes && p.respite_episodes.length > 0 && (
                    <div className="border-t pt-3 mt-3">
                      <p className="text-xs font-semibold text-foreground flex items-center gap-1 mb-2">
                        <Clock className="w-3.5 h-3.5 text-blue-500" /> Respite Care Episodes ({p.respite_episodes.length})
                      </p>
                      <div className="space-y-1.5">
                        {p.respite_episodes.map((r) => (
                          <div key={r.id} className="text-xs flex items-center justify-between bg-blue-500/5 p-2 rounded border border-blue-500/10">
                            <div>
                              <span className="font-medium text-foreground">{r.respite_provider_name}</span>
                              <span className="text-muted-foreground"> ({r.start_date} to {r.end_date})</span>
                            </div>
                            <Badge variant="outline" className="text-[10px] bg-blue-500/10 text-blue-700 dark:text-blue-300">
                              {r.status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* --- In-Home Placements Content --- */}
        <TabsContent value="in_home" className="space-y-4 pt-2">
          {inHomePlacements.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <Shield className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
              <p className="font-medium text-sm text-foreground">No in-home placements recorded</p>
              <p className="text-xs text-muted-foreground mt-1">
                Record safety placements where the child remains in the home under intensive supervision.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {inHomePlacements.map((ih) => (
                <div key={ih.id} className="p-4 rounded-lg border bg-card/60 hover:bg-card transition-all space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-foreground">{ih.caregiver_name}</span>
                      <Badge variant="secondary">{ih.caregiver_relationship}</Badge>
                      <Badge
                        variant="outline"
                        className={ih.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' : 'bg-muted'}
                      >
                        {ih.status}
                      </Badge>
                    </div>
                    <Badge variant="outline" className="bg-primary/5 text-primary text-xs">
                      Supervision: {ih.supervision_level}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs text-muted-foreground">
                    <div>Start Date: <span className="text-foreground font-medium">{ih.start_date}</span></div>
                    {ih.caregiver_phone && <div>Contact: <span className="text-foreground font-medium">{ih.caregiver_phone}</span></div>}
                    {ih.address && <div>Address: <span className="text-foreground font-medium">{ih.address}</span></div>}
                  </div>
                  {ih.notes && <p className="text-xs text-muted-foreground">{ih.notes}</p>}
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* --- Removals Content --- */}
        <TabsContent value="removals" className="space-y-4 pt-2">
          {removals.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <ShieldAlert className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
              <p className="font-medium text-sm text-foreground">No removal episodes recorded</p>
              <p className="text-xs text-muted-foreground mt-1">
                Removals are recorded when child protection custody is initiated under court order or warrant.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {removals.map((r) => (
                <div key={r.id} className="p-4 rounded-lg border bg-card/60 hover:bg-card transition-all space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="destructive" className="font-medium">{r.removal_type}</Badge>
                      <Badge variant="outline">{r.authority_type}</Badge>
                      <span className="text-xs text-muted-foreground">Date: {r.removal_date}</span>
                    </div>
                    {r.notified_first_nation && (
                      <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20 text-xs">
                        First Nation Notified
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-foreground font-medium">{r.reason_for_removal}</p>
                  {r.child_belongings_inventory && (
                    <div className="text-xs bg-muted/30 p-2 rounded text-muted-foreground">
                      <span className="font-semibold text-foreground">Belongings Inventory: </span>
                      {r.child_belongings_inventory}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* --- Discharges Content --- */}
        <TabsContent value="discharges" className="space-y-4 pt-2">
          {discharges.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <LogOut className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
              <p className="font-medium text-sm text-foreground">No discharge records yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Discharges record successful reunifications, customary adoptions, or youth transitions.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {discharges.map((d) => (
                <div key={d.id} className="p-4 rounded-lg border bg-card/60 hover:bg-card transition-all space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20">
                        {d.discharge_reason}
                      </Badge>
                      <Badge variant="outline">{d.destination_type}</Badge>
                      <span className="text-xs text-muted-foreground">Discharge Date: {d.discharge_date}</span>
                    </div>
                    {d.destination_caregiver_name && (
                      <span className="text-xs font-medium text-foreground">
                        Reunified With: {d.destination_caregiver_name}
                      </span>
                    )}
                  </div>
                  {d.notes && <p className="text-xs text-muted-foreground">{d.notes}</p>}
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* --- Modal: Create Placement Episode --- */}
      <Dialog open={showPlacementModal} onOpenChange={setShowPlacementModal}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Create Placement Episode</DialogTitle>
            <DialogDescription>
              Assign the child to an active kinship, foster, or customary care placement.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreatePlacement} className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold">Registered Placement Home / Facility (Optional)</label>
              <Select
                value={placementForm.placement_home_id || "none"}
                onValueChange={(val) => {
                  if (val === "none") {
                    setPlacementForm({ ...placementForm, placement_home_id: "" });
                  } else {
                    const selected = availableHomes.find((h) => h.id === val);
                    if (selected) {
                      setPlacementForm({
                        ...placementForm,
                        placement_home_id: selected.id,
                        provider_name: selected.name,
                        provider_address: `${selected.address_line_1 || ""} ${selected.city || ""}`.trim(),
                        primary_caregiver_name: selected.primary_caregiver_name || placementForm.primary_caregiver_name,
                        provider_contact: selected.phone || selected.email || placementForm.provider_contact,
                      });
                    }
                  }
                }}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Choose approved home or manual..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">-- Manual Provider Entry --</SelectItem>
                  {availableHomes.map((h) => (
                    <SelectItem key={h.id} value={h.id}>
                      {h.name} ({h.available_beds} beds available • {h.home_type})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Child *</label>
                <Select
                  value={placementForm.child_id}
                  onValueChange={(val) => setPlacementForm({ ...placementForm, child_id: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Select child..." />
                  </SelectTrigger>
                  <SelectContent>
                    {people.map((p) => (
                      <SelectItem key={p.person_id} value={p.person_id}>
                        {p.person?.first_name} {p.person?.last_name} ({p.role})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs font-semibold">Placement Type *</label>
                <Select
                  value={placementForm.placement_type}
                  onValueChange={(val) => setPlacementForm({ ...placementForm, placement_type: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="KINSHIP">Kinship Care (Family)</SelectItem>
                    <SelectItem value="CUSTOMARY_CARE">Customary Care (Band Home)</SelectItem>
                    <SelectItem value="FOSTER_HOME">Foster Home</SelectItem>
                    <SelectItem value="GROUP_CARE">Group / Residential Care</SelectItem>
                    <SelectItem value="SPECIALIZED_MEDICAL">Specialized Medical</SelectItem>
                    <SelectItem value="INDEPENDENT_LIVING">Independent Living</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Provider / Home Name *</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. Auntie Mary Kinship Home"
                  value={placementForm.provider_name}
                  onChange={(e) => setPlacementForm({ ...placementForm, provider_name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Primary Caregiver Name</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. Mary Pelly"
                  value={placementForm.primary_caregiver_name}
                  onChange={(e) => setPlacementForm({ ...placementForm, primary_caregiver_name: e.target.value })}
                />
              </div>
            </div>


            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-xs font-semibold">Start Date *</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={placementForm.start_date}
                  onChange={(e) => setPlacementForm({ ...placementForm, start_date: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Per Diem Rate ($/day)</label>
                <Input
                  type="number"
                  step="0.01"
                  className="mt-1"
                  placeholder="45.50"
                  value={placementForm.per_diem_rate}
                  onChange={(e) => setPlacementForm({ ...placementForm, per_diem_rate: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Removal Link</label>
                <Select
                  value={placementForm.removal_episode_id || "none"}
                  onValueChange={(val) => setPlacementForm({ ...placementForm, removal_episode_id: val === "none" ? "" : val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Link removal..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None (Direct Agreement)</SelectItem>
                    {removals.map((r) => (
                      <SelectItem key={r.id} value={r.id}>
                        Removal on {r.removal_date} ({r.removal_type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg border">
              <input
                type="checkbox"
                id="cult_plan"
                className="rounded border-gray-300 text-primary focus:ring-primary"
                checked={placementForm.cultural_plan_in_place}
                onChange={(e) => setPlacementForm({ ...placementForm, cultural_plan_in_place: e.target.checked })}
              />
              <label htmlFor="cult_plan" className="text-xs font-medium cursor-pointer">
                Customary Cultural Plan in place (Elder contact, traditional diet, Band connection)
              </label>
            </div>

            <div>
              <label className="text-xs font-semibold">Placement Notes</label>
              <Textarea
                className="mt-1"
                placeholder="Specific care arrangements, transportation, schooling notes..."
                value={placementForm.placement_notes}
                onChange={(e) => setPlacementForm({ ...placementForm, placement_notes: e.target.value })}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowPlacementModal(false)}>
                Cancel
              </Button>
              <Button type="submit">Create Placement Episode</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- Modal: Record In-Home Placement --- */}
      <Dialog open={showInHomeModal} onOpenChange={setShowInHomeModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Log In-Home Placement</DialogTitle>
            <DialogDescription>
              Record an intensive in-home safety placement where child remains with family.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateInHome} className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold">Child *</label>
              <Select
                value={inHomeForm.child_id}
                onValueChange={(val) => setInHomeForm({ ...inHomeForm, child_id: val })}
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
                <label className="text-xs font-semibold">Caregiver Name *</label>
                <Input
                  className="mt-1"
                  value={inHomeForm.caregiver_name}
                  onChange={(e) => setInHomeForm({ ...inHomeForm, caregiver_name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Relationship</label>
                <Input
                  className="mt-1"
                  value={inHomeForm.caregiver_relationship}
                  onChange={(e) => setInHomeForm({ ...inHomeForm, caregiver_relationship: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Supervision Level</label>
                <Select
                  value={inHomeForm.supervision_level}
                  onValueChange={(val) => setInHomeForm({ ...inHomeForm, supervision_level: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DAILY">Daily Check-in</SelectItem>
                    <SelectItem value="INTENSIVE">Intensive (3x/week)</SelectItem>
                    <SelectItem value="MODERATE">Moderate (Weekly)</SelectItem>
                    <SelectItem value="STANDARD">Standard (Bi-weekly)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-semibold">Start Date *</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={inHomeForm.start_date}
                  onChange={(e) => setInHomeForm({ ...inHomeForm, start_date: e.target.value })}
                  required
                />
              </div>
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowInHomeModal(false)}>
                Cancel
              </Button>
              <Button type="submit">Save In-Home Placement</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- Modal: Record Removal Episode --- */}
      <Dialog open={showRemovalModal} onOpenChange={setShowRemovalModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Record Removal Episode</DialogTitle>
            <DialogDescription>
              Document legal authority, removal date, and physical custody transition.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateRemoval} className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold">Child *</label>
              <Select
                value={removalForm.child_id}
                onValueChange={(val) => setRemovalForm({ ...removalForm, child_id: val })}
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
                <label className="text-xs font-semibold">Removal Type *</label>
                <Select
                  value={removalForm.removal_type}
                  onValueChange={(val) => setRemovalForm({ ...removalForm, removal_type: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="TEMPORARY_CUSTODY">Temporary Custody</SelectItem>
                    <SelectItem value="APPREHENSION">Emergency Apprehension</SelectItem>
                    <SelectItem value="VOLUNTARY_SURRENDER">Voluntary Agreement</SelectItem>
                    <SelectItem value="COURT_TRANSFER">Court Order Transfer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-semibold">Authority Type *</label>
                <Select
                  value={removalForm.authority_type}
                  onValueChange={(val) => setRemovalForm({ ...removalForm, authority_type: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="COURT_ORDER">Court Order</SelectItem>
                    <SelectItem value="EMERGENCY_WARRANT">Emergency Warrant</SelectItem>
                    <SelectItem value="VOLUNTARY_AGREEMENT">Customary Agreement</SelectItem>
                    <SelectItem value="EXIGENT_CIRCUMSTANCES">Exigent Circumstances</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold">Reason for Removal *</label>
              <Textarea
                className="mt-1"
                placeholder="Describe the immediate safety threat or court grounds..."
                value={removalForm.reason_for_removal}
                onChange={(e) => setRemovalForm({ ...removalForm, reason_for_removal: e.target.value })}
                required
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowRemovalModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="destructive">Save Removal Record</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- Modal: Schedule Respite --- */}
      <Dialog open={showRespiteModal} onOpenChange={setShowRespiteModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Schedule Respite Care</DialogTitle>
            <DialogDescription>
              Provide temporary relief for the primary caregiver while preserving placement continuity.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateRespite} className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold">Respite Provider / Home Name *</label>
              <Input
                className="mt-1"
                placeholder="e.g. Yorkton Approved Respite Home"
                value={respiteForm.respite_provider_name}
                onChange={(e) => setRespiteForm({ ...respiteForm, respite_provider_name: e.target.value })}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Start Date *</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={respiteForm.start_date}
                  onChange={(e) => setRespiteForm({ ...respiteForm, start_date: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold">End Date *</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={respiteForm.end_date}
                  onChange={(e) => setRespiteForm({ ...respiteForm, end_date: e.target.value })}
                  required
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold">Reason for Respite</label>
              <Input
                className="mt-1"
                value={respiteForm.reason_for_respite}
                onChange={(e) => setRespiteForm({ ...respiteForm, reason_for_respite: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowRespiteModal(false)}>
                Cancel
              </Button>
              <Button type="submit">Schedule Respite</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- Modal: Discharge Placement --- */}
      <Dialog open={showDischargeModal} onOpenChange={setShowDischargeModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Discharge Placement</DialogTitle>
            <DialogDescription>
              Complete placement episode upon successful family reunification, customary adoption, or youth independence.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateDischarge} className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold">Discharge Reason *</label>
              <Select
                value={dischargeForm.discharge_reason}
                onValueChange={(val) => setDischargeForm({ ...dischargeForm, discharge_reason: val })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="REUNIFICATION">Full Family Reunification</SelectItem>
                  <SelectItem value="CUSTOMARY_ADOPTION">Customary Adoption</SelectItem>
                  <SelectItem value="PERMANENT_GUARDIANSHIP">Permanent Customary Guardianship</SelectItem>
                  <SelectItem value="AGED_OUT">Aged Out / Independent Youth</SelectItem>
                  <SelectItem value="AGENCY_TRANSFER">Transferred to Band Agency</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Discharge Date *</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={dischargeForm.discharge_date}
                  onChange={(e) => setDischargeForm({ ...dischargeForm, discharge_date: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Reunified Caregiver</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. Biological Parents"
                  value={dischargeForm.destination_caregiver_name}
                  onChange={(e) => setDischargeForm({ ...dischargeForm, destination_caregiver_name: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold">Discharge & Aftercare Notes</label>
              <Textarea
                className="mt-1"
                placeholder="Post-reunification support, community wellness check-in schedule..."
                value={dischargeForm.notes}
                onChange={(e) => setDischargeForm({ ...dischargeForm, notes: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowDischargeModal(false)}>
                Cancel
              </Button>
              <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white">
                Finalize Discharge
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

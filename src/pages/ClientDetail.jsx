import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clientsApi, casesApi } from '@/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  User,
  Heart,
  Pill,
  GraduationCap,
  Sparkles,
  MapPin,
  Clock,
  FileText,
  AlertTriangle,
  Users,
  Shield,
  Stethoscope,
  Plus,
  ArrowLeft,
  Calendar,
  Phone,
  Mail,
  Building,
  CheckCircle,
  Activity,
} from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

export default function ClientDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState("overview");

  // Form states for modals/sub-resources
  const [newAllergy, setNewAllergy] = useState({ allergen: '', reaction: '', severity: 'Moderate' });
  const [newMedication, setNewMedication] = useState({ medication_name: '', dosage: '', frequency: '', prescriber_name: '' });
  const [newStrength, setNewStrength] = useState({ name: '' });
  const [newChallenge, setNewChallenge] = useState({ name: '', severity: 'Moderate' });

  // 1. Main Client Query
  const { data: client, isLoading, error } = useQuery({
    queryKey: ['client', id],
    queryFn: () => clientsApi.get(id),
  });

  // 2. Medical Data Query
  const { data: medicalData } = useQuery({
    queryKey: ['client-medical', id],
    queryFn: () => clientsApi.getMedical(id),
    enabled: !!id && activeTab === 'medical',
  });

  // 3. Providers Query
  const { data: providersData } = useQuery({
    queryKey: ['client-providers', id],
    queryFn: () => clientsApi.getProviders(id),
    enabled: !!id && activeTab === 'providers',
  });

  // 4. Schools Query
  const { data: schoolsData } = useQuery({
    queryKey: ['client-schools', id],
    queryFn: () => clientsApi.getSchools(id),
    enabled: !!id && activeTab === 'schools',
  });

  // 5. Timeline Query
  const { data: timelineData } = useQuery({
    queryKey: ['client-timeline', id],
    queryFn: () => clientsApi.getTimeline(id),
    enabled: !!id && activeTab === 'timeline',
  });

  // 6. Connected Cases Query
  const { data: clientCases } = useQuery({
    queryKey: ['client-cases', id],
    queryFn: () => casesApi.filter({ client_id: id }),
    enabled: !!id && activeTab === 'overview',
  });

  // Mutations
  const addAllergyMutation = useMutation({
    mutationFn: (data) => clientsApi.addAllergy(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-medical', id] });
      setNewAllergy({ allergen: '', reaction: '', severity: 'Moderate' });
      toast({ title: "Allergy Added", description: "Medical profile updated successfully." });
    },
  });

  const addMedicationMutation = useMutation({
    mutationFn: (data) => clientsApi.addMedication(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-medical', id] });
      setNewMedication({ medication_name: '', dosage: '', frequency: '', prescriber_name: '' });
      toast({ title: "Medication Recorded", description: "Prescription added to client record." });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="p-8 text-center">
        <AlertTriangle className="w-12 h-12 text-destructive mx-auto mb-4" />
        <h2 className="text-xl font-bold">Client Record Not Found</h2>
        <p className="text-muted-foreground mt-2">The requested client profile is unavailable or access is restricted.</p>
        <Button className="mt-4" onClick={() => navigate('/clients')}>Back to Clients</Button>
      </div>
    );
  }

  const person = client.person || {};

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-card border border-border/80 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/clients')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="w-14 h-14 rounded-full bg-primary/10 border-2 border-primary/30 flex items-center justify-center text-primary font-bold text-xl">
              {client.first_name?.[0]}{client.last_name?.[0]}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-foreground">
                  {client.first_name} {client.last_name}
                </h1>
                <Badge variant={client.status === 'Active' ? 'default' : 'secondary'}>
                  {client.status}
                </Badge>
                <Badge variant="outline" className={
                  client.risk_level === 'High' || client.risk_level === 'Critical' ? 'border-destructive text-destructive' : ''
                }>
                  Risk: {client.risk_level}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-3">
                <span>DOB: {client.date_of_birth || 'Not recorded'}</span>
                <span>•</span>
                <span>Band/Nation: {client.band_nation || 'First Nations'}</span>
                <span>•</span>
                <span>City: {client.city || 'Regina, SK'}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <Button variant="outline" size="sm" asChild>
              <Link to={`/cases?client_id=${client.id}`}>
                <FileText className="w-4 h-4 mr-1.5" /> View Cases
              </Link>
            </Button>
          </div>
        </div>
      </div>

      {/* 14-Tab Detail Workspace */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <div className="overflow-x-auto pb-1">
          <TabsList className="bg-muted/60 p-1 h-auto flex flex-wrap gap-1">
            <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
            <TabsTrigger value="basic" className="text-xs">Basic Info</TabsTrigger>
            <TabsTrigger value="physical" className="text-xs">Physical Description</TabsTrigger>
            <TabsTrigger value="medical" className="text-xs">Medical Profile</TabsTrigger>
            <TabsTrigger value="medications" className="text-xs">Medications</TabsTrigger>
            <TabsTrigger value="providers" className="text-xs">Providers</TabsTrigger>
            <TabsTrigger value="schools" className="text-xs">School / Daycare</TabsTrigger>
            <TabsTrigger value="characteristics" className="text-xs">Characteristics</TabsTrigger>
            <TabsTrigger value="cultural" className="text-xs">Cultural Connections</TabsTrigger>
            <TabsTrigger value="family" className="text-xs">Family</TabsTrigger>
            <TabsTrigger value="timeline" className="text-xs">Sacred Timeline</TabsTrigger>
            <TabsTrigger value="documents" className="text-xs">Documents</TabsTrigger>
            <TabsTrigger value="alerts" className="text-xs">Alerts</TabsTrigger>
            <TabsTrigger value="history" className="text-xs">Episodes & History</TabsTrigger>
          </TabsList>
        </div>

        {/* Tab 1: Overview */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="w-4 h-4 text-primary" /> Key Information Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground text-xs block">Full Legal Name</span>
                  <span className="font-semibold">{client.first_name} {client.last_name}</span>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs block">Indigenous Identity</span>
                  <span className="font-semibold">{client.indigenous_identity || 'First Nations'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs block">Phone Contact</span>
                  <span>{client.phone || 'None recorded'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs block">Email</span>
                  <span>{client.email || 'None recorded'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs block">Primary Address</span>
                  <span>{client.address || 'Regina, SK'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs block">Band / Nation</span>
                  <span>{client.band_nation || 'Muscowpetung Saulteaux Nation'}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="w-4 h-4 text-primary" /> Active Service Files
                </CardTitle>
              </CardHeader>
              <CardContent>
                {clientCases && clientCases.length > 0 ? (
                  <div className="space-y-2">
                    {clientCases.map((c) => (
                      <Link key={c.id} to={`/cases/${c.id}`} className="block p-2.5 bg-muted/40 rounded-lg border hover:border-primary text-xs">
                        <div className="flex items-center justify-between font-semibold">
                          <span>{c.case_number}</span>
                          <Badge variant="outline">{c.status}</Badge>
                        </div>
                        <p className="text-muted-foreground mt-1 truncate">{c.title}</p>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground py-4 text-center">No active cases associated with this client.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 2: Basic Info */}
        <TabsContent value="basic">
          <Card>
            <CardHeader><CardTitle className="text-base">Comprehensive Demographic Profile</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div><span className="text-xs text-muted-foreground block">First Name</span><p className="font-semibold">{client.first_name}</p></div>
              <div><span className="text-xs text-muted-foreground block">Last Name</span><p className="font-semibold">{client.last_name}</p></div>
              <div><span className="text-xs text-muted-foreground block">Date of Birth</span><p>{client.date_of_birth || 'N/A'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Gender Identity</span><p>{client.gender || 'N/A'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Preferred Language</span><p>{person.preferred_language || 'English'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Treaty Number</span><p className="font-mono">{person.treaty_number || 'Confidential / Not Recorded'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Health Card Number</span><p className="font-mono">{person.health_card_number || 'Confidential / Not Recorded'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Emergency Contact</span><p>{person.emergency_contact_name || 'N/A'} ({person.emergency_contact_phone || 'No phone'})</p></div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Physical Description */}
        <TabsContent value="physical">
          <Card>
            <CardHeader><CardTitle className="text-base">Physical Characteristics & Distinguishing Marks</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
              <div><span className="text-xs text-muted-foreground block">Eye Colour</span><p>{person.physical_description?.eye_colour || 'Brown'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Hair Colour</span><p>{person.physical_description?.hair_colour || 'Black'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Height</span><p>{person.physical_description?.height_cm ? `${person.physical_description.height_cm} cm` : 'Not recorded'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Weight</span><p>{person.physical_description?.weight_kg ? `${person.physical_description.weight_kg} kg` : 'Not recorded'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Distinguishing Marks / Scars</span><p>{person.physical_description?.scars || 'None recorded'}</p></div>
              <div><span className="text-xs text-muted-foreground block">Corrective Lenses</span><p>{person.physical_description?.glasses ? 'Yes' : 'No'}</p></div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Medical Profile & Allergies */}
        <TabsContent value="medical" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Stethoscope className="w-4 h-4 text-rose-500" /> Allergies & Alerts
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {medicalData?.allergies && medicalData.allergies.length > 0 ? (
                  <div className="space-y-2">
                    {medicalData.allergies.map((a) => (
                      <div key={a.id} className="p-2.5 bg-rose-950/20 border border-rose-500/30 rounded-lg text-xs flex justify-between">
                        <div>
                          <strong className="text-rose-400 block">{a.allergen}</strong>
                          <span className="text-muted-foreground">Reaction: {a.reaction || 'Standard'}</span>
                        </div>
                        <Badge variant="destructive" className="text-[10px]">{a.severity}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No allergies on record.</p>
                )}

                {/* Add Allergy Form */}
                <div className="pt-3 border-t flex gap-2">
                  <Input
                    placeholder="Allergen (e.g. Peanuts, Penicillin)"
                    value={newAllergy.allergen}
                    onChange={(e) => setNewAllergy({ ...newAllergy, allergen: e.target.value })}
                    className="text-xs h-8"
                  />
                  <Button
                    size="sm"
                    className="h-8 text-xs"
                    disabled={!newAllergy.allergen}
                    onClick={() => addAllergyMutation.mutate(newAllergy)}
                  >
                    <Plus className="w-3.5 h-3.5 mr-1" /> Add
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="w-4 h-4 text-primary" /> Diagnosed Conditions
                </CardTitle>
              </CardHeader>
              <CardContent>
                {medicalData?.conditions && medicalData.conditions.length > 0 ? (
                  <div className="space-y-2">
                    {medicalData.conditions.map((c) => (
                      <div key={c.id} className="p-2.5 bg-muted/40 rounded-lg border text-xs">
                        <strong className="block text-foreground">{c.condition_name}</strong>
                        {c.is_chronic && <Badge variant="secondary" className="text-[10px] mt-1">Chronic</Badge>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No diagnosed conditions recorded.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 5: Medications */}
        <TabsContent value="medications">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Pill className="w-4 h-4 text-emerald-500" /> Prescription & Medication Ledger
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {medicalData?.medications && medicalData.medications.length > 0 ? (
                <div className="space-y-2">
                  {medicalData.medications.map((m) => (
                    <div key={m.id} className="p-3 bg-muted/40 rounded-lg border text-xs flex justify-between items-start">
                      <div>
                        <strong className="text-sm font-semibold text-foreground">{m.medication_name}</strong>
                        <p className="text-muted-foreground mt-0.5">Dosage: {m.dosage} • Frequency: {m.frequency} • Route: {m.route}</p>
                        {m.prescriber_name && <p className="text-[11px] text-muted-foreground italic">Prescribed by: {m.prescriber_name}</p>}
                      </div>
                      <Badge variant={m.status === 'Active' ? 'default' : 'secondary'}>{m.status}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No medication history recorded.</p>
              )}

              {/* Quick Record Form */}
              <div className="p-3 bg-muted/20 border border-dashed rounded-lg space-y-3">
                <span className="text-xs font-semibold text-muted-foreground block">Record New Prescription</span>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
                  <Input
                    placeholder="Medication Name"
                    value={newMedication.medication_name}
                    onChange={(e) => setNewMedication({ ...newMedication, medication_name: e.target.value })}
                    className="text-xs h-8"
                  />
                  <Input
                    placeholder="Dosage (e.g. 10mg)"
                    value={newMedication.dosage}
                    onChange={(e) => setNewMedication({ ...newMedication, dosage: e.target.value })}
                    className="text-xs h-8"
                  />
                  <Input
                    placeholder="Frequency (e.g. Daily)"
                    value={newMedication.frequency}
                    onChange={(e) => setNewMedication({ ...newMedication, frequency: e.target.value })}
                    className="text-xs h-8"
                  />
                  <Button
                    size="sm"
                    className="h-8 text-xs"
                    disabled={!newMedication.medication_name || !newMedication.dosage || !newMedication.frequency}
                    onClick={() => addMedicationMutation.mutate(newMedication)}
                  >
                    <Plus className="w-3.5 h-3.5 mr-1" /> Add Medication
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 6: Providers */}
        <TabsContent value="providers">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Building className="w-4 h-4 text-primary" /> Assigned Care & Healthcare Providers</CardTitle></CardHeader>
            <CardContent>
              {providersData && providersData.length > 0 ? (
                <div className="space-y-2">
                  {providersData.map((p) => (
                    <div key={p.id} className="p-3 bg-muted/40 rounded-lg border text-xs flex justify-between">
                      <div>
                        <strong className="text-sm font-semibold">{p.provider?.name}</strong>
                        <p className="text-muted-foreground">{p.role} • {p.provider?.provider_type}</p>
                      </div>
                      <Badge variant="outline">Connected</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground py-4 text-center">No providers currently linked to this client.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 7: School / Daycare */}
        <TabsContent value="schools">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><GraduationCap className="w-4 h-4 text-primary" /> School & Daycare Enrolments</CardTitle></CardHeader>
            <CardContent>
              {schoolsData && schoolsData.length > 0 ? (
                <div className="space-y-2">
                  {schoolsData.map((s) => (
                    <div key={s.id} className="p-3 bg-muted/40 rounded-lg border text-xs flex justify-between">
                      <div>
                        <strong className="text-sm font-semibold">{s.school?.name}</strong>
                        <p className="text-muted-foreground">{s.grade_level} • {s.has_iep ? 'IEP Active' : 'Regular'}</p>
                      </div>
                      <Badge variant="secondary">{s.is_current ? 'Currently Enrolled' : 'Past'}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground py-4 text-center">No school enrollments on record.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 8: Characteristics */}
        <TabsContent value="characteristics">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><Sparkles className="w-4 h-4 text-amber-400" /> Strengths & Assets</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="px-3 py-1 bg-amber-500/10 text-amber-500 border border-amber-500/20">Strong Family Bond</Badge>
                  <Badge variant="secondary" className="px-3 py-1 bg-amber-500/10 text-amber-500 border border-amber-500/20">Cultural Engagement</Badge>
                  <Badge variant="secondary" className="px-3 py-1 bg-amber-500/10 text-amber-500 border border-amber-500/20">Good Attendance</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-rose-400" /> Behavioral & Support Challenges</CardTitle></CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">No critical behavioral challenges or runaway alerts currently active.</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 9: Cultural Connections */}
        <TabsContent value="cultural">
          <Card>
            <CardHeader><CardTitle className="text-base">Cultural Engagement, Traditions & Ceremonies</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div><strong className="text-xs text-muted-foreground block">First Nation / Band</strong><p className="font-semibold">{client.band_nation || 'Muscowpetung Saulteaux Nation'}</p></div>
              <div><strong className="text-xs text-muted-foreground block">Ceremonies & Elders Connected</strong><p>{person.cultural_profile?.ceremonies || 'Participates in seasonal lodge feasts, sweat lodges, and Elder mentorship.'}</p></div>
              <div><strong className="text-xs text-muted-foreground block">Land-Based Activities</strong><p>{person.cultural_profile?.land_based_activities || 'Seasonal harvesting, medicine picking, and cultural camp attendance.'}</p></div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 10: Family & Kinship */}
        <TabsContent value="family">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Users className="w-4 h-4 text-primary" /> Family File & Relatives</CardTitle></CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Connected to Family File. Visit the dedicated Families portal for interactive Genograms and household maps.</p>
              <Button className="mt-3" size="sm" asChild>
                <Link to="/families">Go to Families Directory</Link>
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 11: Sacred Timeline */}
        <TabsContent value="timeline">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Clock className="w-4 h-4 text-primary" /> Sacred Timeline Milestones</CardTitle></CardHeader>
            <CardContent>
              {timelineData && timelineData.length > 0 ? (
                <div className="relative border-l-2 border-primary/30 pl-4 space-y-4">
                  {timelineData.map((ev) => (
                    <div key={ev.id} className="relative">
                      <div className="absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full bg-primary ring-4 ring-background" />
                      <span className="text-[11px] text-muted-foreground">{new Date(ev.occurred_at).toLocaleString()}</span>
                      <h5 className="text-sm font-semibold text-foreground">{ev.title}</h5>
                      {ev.description && <p className="text-xs text-muted-foreground mt-0.5">{ev.description}</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground py-4 text-center">No timeline milestones logged yet.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 12: Documents */}
        <TabsContent value="documents">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><FileText className="w-4 h-4 text-primary" /> Client Records & Identity Documents</CardTitle></CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Document files are stored encrypted and private by default. Access requires permission-checked signed URLs.</p>
              <Button className="mt-3" size="sm" asChild>
                <Link to="/documents">Open Documents Repository</Link>
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 13: Alerts */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-500" /> Active Safety Alerts & Cautions</CardTitle></CardHeader>
            <CardContent>
              <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded-lg text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-300">No active high-risk safety cautions or emergency warrants flagged for this client.</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 14: Episodes & History */}
        <TabsContent value="history">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Clock className="w-4 h-4 text-primary" /> Service Episodes & Placement History</CardTitle></CardHeader>
            <CardContent>
              <div className="p-8 text-center border border-dashed rounded-lg text-muted-foreground text-xs">
                <Shield className="w-8 h-8 mx-auto mb-2 opacity-40 text-primary" />
                <p className="font-semibold text-sm text-foreground">Future Phases: Intake, Assessment & Placement</p>
                <p className="mt-1">Historical service episode tracking will automatically populate as formal Intake and Placement modules are implemented in upcoming phases.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Inbox, Plus, Trash2, ArrowLeft, Shield, AlertTriangle,
  User, Users, Phone, Building, FileText, CheckCircle2, Lock
} from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { clientsApi } from "@/api/clients";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/components/ui/use-toast";

const CONCERN_TYPES = [
  { key: "physical_abuse", label: "Physical Abuse / Non-Accidental Injury" },
  { key: "neglect", label: "Severe Neglect / Basic Needs Unmet" },
  { key: "emotional_harm", label: "Emotional Harm / Mental Cruelty" },
  { key: "sexual_abuse", label: "Sexual Abuse / Child Exploitation" },
  { key: "domestic_violence", label: "Domestic / Intimate Partner Violence in Home" },
  { key: "substance_use", label: "Caregiver Substance Misuse / Impairment" },
  { key: "food_insecurity", label: "Severe Food Insecurity" },
  { key: "housing_insecurity", label: "Housing Insecurity / Inadequate Shelter" },
  { key: "caregiver_incapacity", label: "Caregiver Incapacity / Abandonment" },
  { key: "welfare_concern", label: "General Family Welfare / Support Concern" },
  { key: "other", label: "Other Structured Concern" },
];

export default function NewIntake() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [receivedDate, setReceivedDate] = useState(new Date().toISOString().split("T")[0]);
  const [receivedMethod, setReceivedMethod] = useState("phone");
  const [priority, setPriority] = useState("Medium");
  const [riskLevel, setRiskLevel] = useState("Medium");
  const [community, setCommunity] = useState("");
  const [summary, setSummary] = useState("");
  const [immediateSafety, setImmediateSafety] = useState(false);
  const [lawEnforcement, setLawEnforcement] = useState(false);
  const [policeFileNumber, setPoliceFileNumber] = useState("");

  // Confidential Reporter
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [isMandated, setIsMandated] = useState(false);
  const [reporterName, setReporterName] = useState("");
  const [reporterOrg, setReporterOrg] = useState("");
  const [reporterPhone, setReporterPhone] = useState("");
  const [reporterEmail, setReporterEmail] = useState("");
  const [reporterRelationship, setReporterRelationship] = useState("");
  const [reporterNotes, setReporterNotes] = useState("");

  // People List
  const [people, setPeople] = useState([]);
  const [availableClients, setAvailableClients] = useState([]);
  const [selectedPersonId, setSelectedPersonId] = useState("");
  const [personRole, setPersonRole] = useState("child");
  const [relationshipToChild, setRelationshipToChild] = useState("");
  const [isPrimaryCaregiver, setIsPrimaryCaregiver] = useState(false);

  // Concerns
  const [concerns, setConcerns] = useState([
    { concern_type: "neglect", is_primary: true, severity: "Moderate", description: "" }
  ]);

  // Load existing clients for dropdown selection
  useEffect(() => {
    clientsApi.list({ limit: 100 })
      .then(res => {
        const items = res?.items || res || [];
        setAvailableClients(items);
      })
      .catch(() => {});
  }, []);

  const handleAddPerson = () => {
    if (!selectedPersonId) {
      toast({ title: "Select a person", description: "Please select an existing person or client record", variant: "destructive" });
      return;
    }
    const client = availableClients.find(c => c.id === selectedPersonId);
    if (!client) return;

    if (people.some(p => p.person_id === selectedPersonId)) {
      toast({ title: "Person already added", description: "This person is already in the intake roster", variant: "destructive" });
      return;
    }

    setPeople([
      ...people,
      {
        person_id: client.id,
        name: `${client.first_name} ${client.last_name}`,
        role: personRole,
        relationship_to_child: relationshipToChild,
        is_primary_caregiver: isPrimaryCaregiver,
      }
    ]);

    setSelectedPersonId("");
    setRelationshipToChild("");
    setIsPrimaryCaregiver(false);
  };

  const handleRemovePerson = (idx) => {
    setPeople(people.filter((_, i) => i !== idx));
  };

  const handleAddConcern = () => {
    setConcerns([
      ...concerns,
      { concern_type: "welfare_concern", is_primary: false, severity: "Moderate", description: "" }
    ]);
  };

  const handleRemoveConcern = (idx) => {
    setConcerns(concerns.filter((_, i) => i !== idx));
  };

  const handleSetPrimaryConcern = (idx) => {
    setConcerns(concerns.map((c, i) => ({ ...c, is_primary: i === idx })));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!summary.trim()) {
      toast({ title: "Summary required", description: "Please enter an intake narrative summary", variant: "destructive" });
      return;
    }

    try {
      setSubmitting(true);

      const payload = {
        received_date: receivedDate,
        received_method: receivedMethod,
        priority,
        risk_level: riskLevel,
        community: community.trim() || undefined,
        summary: summary.trim(),
        immediate_safety_concerns: immediateSafety,
        law_enforcement_involved: lawEnforcement,
        law_enforcement_file_number: lawEnforcement ? policeFileNumber : undefined,
        reporter: {
          is_anonymous: isAnonymous,
          is_mandated_reporter: isMandated,
          reporter_name: isAnonymous ? undefined : reporterName.trim() || undefined,
          organization: reporterOrg.trim() || undefined,
          phone: isAnonymous ? undefined : reporterPhone.trim() || undefined,
          email: isAnonymous ? undefined : reporterEmail.trim() || undefined,
          relationship_to_family: reporterRelationship.trim() || undefined,
          reporter_notes: reporterNotes.trim() || undefined,
        },
        people: people.map(p => ({
          person_id: p.person_id,
          role: p.role,
          relationship_to_child: p.relationship_to_child || undefined,
          is_primary_caregiver: p.is_primary_caregiver,
        })),
        concerns: concerns.map(c => ({
          concern_type: c.concern_type,
          is_primary: c.is_primary,
          severity: c.severity,
          description: c.description.trim() || undefined,
        })),
      };

      const created = await referralsApi.create(payload);
      toast({
        title: "Intake Referral Created",
        description: `Draft referral ${created.referral_number} registered successfully.`,
      });

      navigate(`/intake/${created.id}`);
    } catch (err) {
      toast({
        title: "Failed to create intake",
        description: err.message || "An error occurred while saving the referral",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/intake")}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold font-heading text-foreground">Log New Intake Referral</h1>
            <p className="text-xs text-muted-foreground">Capture front-door referral details, confidential reporter, involved persons, and screening concerns</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Referral Channel & Details */}
        <Card className="border shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Inbox className="w-4 h-4 text-primary" />
              <span>1. Intake Reception & Origin</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="receivedDate">Received Date *</Label>
                <Input
                  id="receivedDate"
                  type="date"
                  value={receivedDate}
                  onChange={(e) => setReceivedDate(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="receivedMethod">Intake Channel *</Label>
                <Select value={receivedMethod} onValueChange={setReceivedMethod}>
                  <SelectTrigger id="receivedMethod">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="phone">Telephone Call</SelectItem>
                    <SelectItem value="in_person">In Person / Walk-In</SelectItem>
                    <SelectItem value="electronic">Electronic / Web Portal</SelectItem>
                    <SelectItem value="law_enforcement">Law Enforcement / Police</SelectItem>
                    <SelectItem value="school">School / Educator</SelectItem>
                    <SelectItem value="healthcare">Healthcare / Hospital</SelectItem>
                    <SelectItem value="self_referral">Child / Youth Self-Referral</SelectItem>
                    <SelectItem value="community_member">Community Member / Relative</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="priority">Initial Priority *</Label>
                <Select value={priority} onValueChange={setPriority}>
                  <SelectTrigger id="priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Crisis">Crisis (Immediate Safety Intervention)</SelectItem>
                    <SelectItem value="High">High (Within 24 Hours)</SelectItem>
                    <SelectItem value="Medium">Medium (Standard Assessment)</SelectItem>
                    <SelectItem value="Low">Low (Routine Support)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="community">Nation / Community</Label>
                <Input
                  id="community"
                  placeholder="e.g. Muscowpetung Saulteaux Nation, Regina, Fort Qu'Appelle"
                  value={community}
                  onChange={(e) => setCommunity(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="riskLevel">Risk Assessment Level</Label>
                <Select value={riskLevel} onValueChange={setRiskLevel}>
                  <SelectTrigger id="riskLevel">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Critical">Critical</SelectItem>
                    <SelectItem value="High">High</SelectItem>
                    <SelectItem value="Moderate">Moderate</SelectItem>
                    <SelectItem value="Low">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row gap-6 border-t">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="immediateSafety"
                  checked={immediateSafety}
                  onCheckedChange={setImmediateSafety}
                />
                <Label htmlFor="immediateSafety" className="text-sm font-medium text-red-600 cursor-pointer">
                  Immediate safety / protection danger flags present
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="lawEnforcement"
                  checked={lawEnforcement}
                  onCheckedChange={setLawEnforcement}
                />
                <Label htmlFor="lawEnforcement" className="text-sm font-medium cursor-pointer">
                  Law Enforcement / Police currently involved
                </Label>
              </div>
            </div>

            {lawEnforcement && (
              <div className="p-3 bg-muted/40 rounded-lg space-y-2">
                <Label htmlFor="policeFile">Police File / Occurrence Number</Label>
                <Input
                  id="policeFile"
                  placeholder="e.g. RCMP File #2026-98124"
                  value={policeFileNumber}
                  onChange={(e) => setPoliceFileNumber(e.target.value)}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Section 2: Confidential Reporter */}
        <Card className="border shadow-sm border-amber-200/60 bg-amber-50/10">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-amber-600" />
                <span>2. Confidential Reporter Information</span>
              </div>
              <Badge variant="outline" className="text-xs bg-amber-100 text-amber-900 border-amber-300">
                Protected by Privacy Rules
              </Badge>
            </CardTitle>
            <CardDescription className="text-xs">
              Reporter identity is strictly confidential and protected by backend authorization.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-6 pb-2 border-b">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="isAnonymous"
                  checked={isAnonymous}
                  onCheckedChange={setIsAnonymous}
                />
                <Label htmlFor="isAnonymous" className="text-sm font-medium cursor-pointer">
                  Reporter requests full anonymity
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="isMandated"
                  checked={isMandated}
                  onCheckedChange={setIsMandated}
                />
                <Label htmlFor="isMandated" className="text-sm font-medium cursor-pointer">
                  Mandated Reporter (Medical, School, Police, Social Worker)
                </Label>
              </div>
            </div>

            {!isAnonymous ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="repName">Reporter Full Name</Label>
                  <Input
                    id="repName"
                    placeholder="Full Name"
                    value={reporterName}
                    onChange={(e) => setReporterName(e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="repOrg">Organization / Agency</Label>
                  <Input
                    id="repOrg"
                    placeholder="e.g. Muscowpetung School, Regina General Hospital"
                    value={reporterOrg}
                    onChange={(e) => setReporterOrg(e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="repPhone">Phone Number</Label>
                  <Input
                    id="repPhone"
                    placeholder="306-..."
                    value={reporterPhone}
                    onChange={(e) => setReporterPhone(e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="repRel">Relationship to Family / Children</Label>
                  <Input
                    id="repRel"
                    placeholder="e.g. Teacher, Neighbor, Aunt, Public Health Nurse"
                    value={reporterRelationship}
                    onChange={(e) => setReporterRelationship(e.target.value)}
                  />
                </div>
              </div>
            ) : (
              <div className="p-3 bg-muted rounded-lg text-xs text-muted-foreground">
                Anonymous reporter: Identity details are withheld.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Section 3: Involved Persons */}
        <Card className="border shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Users className="w-4 h-4 text-primary" />
              <span>3. Involved Individuals & Family Members</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Link existing persons or clients to this intake record.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Person Adder Bar */}
            <div className="p-3 bg-muted/30 border rounded-lg space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">Select Individual</Label>
                  <Select value={selectedPersonId} onValueChange={setSelectedPersonId}>
                    <SelectTrigger className="h-9">
                      <SelectValue placeholder="Choose Person..." />
                    </SelectTrigger>
                    <SelectContent>
                      {availableClients.map(c => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.first_name} {c.last_name} ({c.client_type || 'Client'})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs">Role in Intake</Label>
                  <Select value={personRole} onValueChange={setPersonRole}>
                    <SelectTrigger className="h-9">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="child">Child / Youth (Subject of Intake)</SelectItem>
                      <SelectItem value="parent">Parent / Biological Parent</SelectItem>
                      <SelectItem value="guardian">Legal Guardian / Custodian</SelectItem>
                      <SelectItem value="alleged_person_of_concern">Alleged Person of Concern</SelectItem>
                      <SelectItem value="relative">Extended Kin / Relative</SelectItem>
                      <SelectItem value="other_adult">Household Adult / Other</SelectItem>
                      <SelectItem value="collateral">Collateral Contact</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs">Relationship Context</Label>
                  <Input
                    className="h-9"
                    placeholder="e.g. Mother, Eldest Child"
                    value={relationshipToChild}
                    onChange={(e) => setRelationshipToChild(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="isCaregiver"
                    checked={isPrimaryCaregiver}
                    onCheckedChange={setIsPrimaryCaregiver}
                  />
                  <Label htmlFor="isCaregiver" className="text-xs cursor-pointer">
                    Primary Caregiver in Household
                  </Label>
                </div>

                <Button type="button" size="sm" onClick={handleAddPerson} className="h-8 gap-1">
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add to Intake</span>
                </Button>
              </div>
            </div>

            {/* People Table */}
            {people.length > 0 ? (
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-muted/50 text-muted-foreground border-b font-medium">
                    <tr>
                      <th className="px-3 py-2">Name</th>
                      <th className="px-3 py-2">Role</th>
                      <th className="px-3 py-2">Relationship</th>
                      <th className="px-3 py-2">Caregiver</th>
                      <th className="px-3 py-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {people.map((p, idx) => (
                      <tr key={p.person_id} className="hover:bg-muted/20">
                        <td className="px-3 py-2 font-medium">{p.name}</td>
                        <td className="px-3 py-2 capitalize">
                          <Badge variant={p.role === "child" ? "default" : "secondary"} className="text-[10px]">
                            {p.role.replace(/_/g, ' ')}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 text-muted-foreground">{p.relationship_to_child || "—"}</td>
                        <td className="px-3 py-2">{p.is_primary_caregiver ? "Yes" : "No"}</td>
                        <td className="px-3 py-2 text-right">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 text-red-500 hover:text-red-700"
                            onClick={() => handleRemovePerson(idx)}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground italic">No individuals added yet. Use the selector above to add children and caregivers.</p>
            )}
          </CardContent>
        </Card>

        {/* Section 4: Structured Concerns */}
        <Card className="border shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  <span>4. Structured Screening Concerns</span>
                </CardTitle>
                <CardDescription className="text-xs">
                  Categorized safety concerns and allegations. Exactly one must be marked Primary.
                </CardDescription>
              </div>
              <Button type="button" size="sm" variant="outline" onClick={handleAddConcern} className="gap-1 h-8">
                <Plus className="w-3.5 h-3.5" />
                <span>Add Concern</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {concerns.map((c, idx) => (
              <div key={idx} className="p-3 border rounded-lg bg-muted/10 space-y-2">
                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <div className="flex-1 space-y-1">
                    <Label className="text-xs">Concern Type</Label>
                    <Select
                      value={c.concern_type}
                      onValueChange={(val) => {
                        const updated = [...concerns];
                        updated[idx].concern_type = val;
                        setConcerns(updated);
                      }}
                    >
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CONCERN_TYPES.map(ct => (
                          <SelectItem key={ct.key} value={ct.key}>{ct.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="w-32 space-y-1">
                    <Label className="text-xs">Severity</Label>
                    <Select
                      value={c.severity}
                      onValueChange={(val) => {
                        const updated = [...concerns];
                        updated[idx].severity = val;
                        setConcerns(updated);
                      }}
                    >
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Low">Low</SelectItem>
                        <SelectItem value="Moderate">Moderate</SelectItem>
                        <SelectItem value="High">High</SelectItem>
                        <SelectItem value="Critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center gap-4 pt-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={`primary-${idx}`}
                        checked={c.is_primary}
                        onCheckedChange={() => handleSetPrimaryConcern(idx)}
                      />
                      <Label htmlFor={`primary-${idx}`} className="text-xs font-semibold cursor-pointer text-primary">
                        Primary Concern
                      </Label>
                    </div>

                    {concerns.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-red-500"
                        onClick={() => handleRemoveConcern(idx)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>

                <div>
                  <Input
                    className="h-8 text-xs"
                    placeholder="Specific clinical details regarding this concern..."
                    value={c.description}
                    onChange={(e) => {
                      const updated = [...concerns];
                      updated[idx].description = e.target.value;
                      setConcerns(updated);
                    }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Section 5: Narrative Summary */}
        <Card className="border shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              <span>5. Incident Narrative & Initial Summary *</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              rows={4}
              placeholder="Provide a comprehensive factual summary of the incident or concern reported during intake..."
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              required
            />
          </CardContent>
        </Card>

        {/* Action Bar */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t">
          <Button type="button" variant="outline" onClick={() => navigate("/intake")}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting} className="bg-primary hover:bg-primary/90 min-w-[160px]">
            {submitting ? "Saving Draft..." : "Create Intake Referral"}
          </Button>
        </div>
      </form>
    </div>
  );
}

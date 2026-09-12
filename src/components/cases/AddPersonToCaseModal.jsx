import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useToast } from "@/components/ui/use-toast";
import { personsApi, casesApi } from "@/api";
import {
  Search,
  UserPlus,
  AlertTriangle,
  Check,
  ArrowLeft,
  Loader2,
  ShieldAlert,
  UserCheck,
} from "lucide-react";

export default function AddPersonToCaseModal({ isOpen, onClose, caseId, onSuccess }) {
  const { toast } = useToast();

  // Mode: "search" | "existing_role" | "create_new" | "duplicate_warning"
  const [mode, setMode] = useState("search");

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  // Selected existing person
  const [selectedPerson, setSelectedPerson] = useState(null);

  // Case link fields
  const [caseRoleForm, setCaseRoleForm] = useState({
    role: "subject_child",
    relationship_to_subject: "",
    is_primary: false,
    start_date: new Date().toISOString().split("T")[0],
    notes: "",
  });

  // Comprehensive new person form
  const [newPersonForm, setNewPersonForm] = useState({
    first_name: "",
    middle_name: "",
    last_name: "",
    preferred_name: "",
    aliases: "",
    date_of_birth: "",
    gender: "",
    place_of_birth: "",
    preferred_language: "English",
    languages_spoken: "",
    treaty_number: "",
    band_nation: "",
    indigenous_identity: "",
    health_card_number: "",
    phone: "",
    email: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    source_of_income: "",
    employment_status: "",
    employer: "",
    employment_details: "",
    notes: "",
    // Nested sub-profiles
    physical: {
      eye_colour: "",
      hair_colour: "",
      height_cm: "",
      weight_kg: "",
      birthmarks: "",
      scars: "",
      tattoos: "",
      piercings: "",
      distinguishing_marks: "",
      glasses: false,
      contact_lenses: false,
      notes: "",
    },
    address: {
      address_line_1: "",
      address_line_2: "",
      city: "Regina",
      province: "Saskatchewan",
      postal_code: "",
      on_reserve: false,
      is_primary: true,
    },
    cultural: {
      cultural_connections: "",
      ceremonies: "",
      elders_connected: "",
      land_based_activities: "",
      dietary_preferences: "",
      extracurricular_activities: "",
    },
  });

  // Duplicate warning state
  const [duplicateCandidates, setDuplicateCandidates] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);

  // Reset modal state
  const resetState = () => {
    setMode("search");
    setSearchQuery("");
    setSearchResults([]);
    setHasSearched(false);
    setSelectedPerson(null);
    setDuplicateCandidates([]);
    setIsSubmitting(false);
    setPhotoFile(null);
    setPhotoPreview(null);
    setCaseRoleForm({
      role: "subject_child",
      relationship_to_subject: "",
      is_primary: false,
      start_date: new Date().toISOString().split("T")[0],
      notes: "",
    });
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  // ── Step A: Search Existing People ──────────────────────────────
  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setIsSearching(true);
      setHasSearched(true);
      const res = await personsApi.list({ query: searchQuery.trim(), limit: 15 });
      const items = res?.items || [];
      setSearchResults(items);
    } catch (err) {
      toast({
        title: "Search failed",
        description: err.message || "Failed to search individuals",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectExisting = (person) => {
    setSelectedPerson(person);
    setMode("existing_role");
  };

  // ── Step B: Link Existing Person to Case ─────────────────────────
  const handleLinkExistingPerson = async () => {
    if (!selectedPerson) return;
    try {
      setIsSubmitting(true);
      await casesApi.addPerson(caseId, {
        person_id: selectedPerson.id,
        role: caseRoleForm.role,
        relationship_to_subject: caseRoleForm.relationship_to_subject || undefined,
        is_primary: caseRoleForm.is_primary,
        start_date: caseRoleForm.start_date || undefined,
        notes: caseRoleForm.notes || undefined,
      });

      toast({
        title: "Person linked to case",
        description: `${selectedPerson.first_name} ${selectedPerson.last_name} (ID: ${selectedPerson.person_id_number}) linked successfully.`,
      });

      handleClose();
      if (onSuccess) onSuccess();
    } catch (err) {
      toast({
        title: "Failed to link person",
        description: err.message || "Could not link person to case",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Step C: Create New Person with Duplicate Checking ───────────
  const handlePreCreateCheck = async (e) => {
    e.preventDefault();
    if (!newPersonForm.first_name.trim() || !newPersonForm.last_name.trim()) {
      toast({
        title: "Name required",
        description: "First name and last name are required.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSubmitting(true);
      // Run duplicate check first
      const dupRes = await personsApi.checkDuplicates({
        first_name: newPersonForm.first_name.trim(),
        last_name: newPersonForm.last_name.trim(),
        date_of_birth: newPersonForm.date_of_birth || undefined,
        treaty_number: newPersonForm.treaty_number || undefined,
        health_card_number: newPersonForm.health_card_number || undefined,
        phone: newPersonForm.phone || undefined,
        email: newPersonForm.email || undefined,
      });

      if (dupRes?.has_potential_duplicates && dupRes?.candidates?.length > 0) {
        setDuplicateCandidates(dupRes.candidates);
        setMode("duplicate_warning");
        setIsSubmitting(false);
        return;
      }

      // No duplicates -> proceed to creation
      await executeCreateAndLink();
    } catch (err) {
      toast({
        title: "Validation error",
        description: err.message || "Failed to validate person record",
        variant: "destructive",
      });
      setIsSubmitting(false);
    }
  };

  const executeCreateAndLink = async () => {
    try {
      setIsSubmitting(true);

      // 1. Prepare Person payload
      const personPayload = {
        first_name: newPersonForm.first_name.trim(),
        middle_name: newPersonForm.middle_name.trim() || undefined,
        last_name: newPersonForm.last_name.trim(),
        preferred_name: newPersonForm.preferred_name.trim() || undefined,
        aliases: newPersonForm.aliases.trim() || undefined,
        date_of_birth: newPersonForm.date_of_birth || undefined,
        gender: newPersonForm.gender || undefined,
        place_of_birth: newPersonForm.place_of_birth || undefined,
        preferred_language: newPersonForm.preferred_language || "English",
        languages_spoken: newPersonForm.languages_spoken || undefined,
        treaty_number: newPersonForm.treaty_number || undefined,
        band_nation: newPersonForm.band_nation || undefined,
        indigenous_identity: newPersonForm.indigenous_identity || undefined,
        health_card_number: newPersonForm.health_card_number || undefined,
        phone: newPersonForm.phone || undefined,
        email: newPersonForm.email || undefined,
        emergency_contact_name: newPersonForm.emergency_contact_name || undefined,
        emergency_contact_phone: newPersonForm.emergency_contact_phone || undefined,
        source_of_income: newPersonForm.source_of_income || undefined,
        employment_status: newPersonForm.employment_status || undefined,
        employer: newPersonForm.employer || undefined,
        employment_details: newPersonForm.employment_details || undefined,
        notes: newPersonForm.notes || undefined,
      };

      // Sub-profiles if provided
      if (
        newPersonForm.physical.eye_colour ||
        newPersonForm.physical.hair_colour ||
        newPersonForm.physical.height_cm ||
        newPersonForm.physical.weight_kg ||
        newPersonForm.physical.tattoos ||
        newPersonForm.physical.scars ||
        newPersonForm.physical.birthmarks ||
        newPersonForm.physical.distinguishing_marks
      ) {
        personPayload.physical_description = {
          eye_colour: newPersonForm.physical.eye_colour || undefined,
          hair_colour: newPersonForm.physical.hair_colour || undefined,
          height_cm: newPersonForm.physical.height_cm ? parseFloat(newPersonForm.physical.height_cm) : undefined,
          weight_kg: newPersonForm.physical.weight_kg ? parseFloat(newPersonForm.physical.weight_kg) : undefined,
          tattoos: newPersonForm.physical.tattoos || undefined,
          piercings: newPersonForm.physical.piercings || undefined,
          birthmarks: newPersonForm.physical.birthmarks || undefined,
          scars: newPersonForm.physical.scars || undefined,
          distinguishing_marks: newPersonForm.physical.distinguishing_marks || undefined,
          glasses: newPersonForm.physical.glasses,
          contact_lenses: newPersonForm.physical.contact_lenses,
        };
      }

      if (newPersonForm.address.address_line_1.trim()) {
        personPayload.address = {
          address_line_1: newPersonForm.address.address_line_1.trim(),
          address_line_2: newPersonForm.address.address_line_2.trim() || undefined,
          city: newPersonForm.address.city.trim() || "Regina",
          province: newPersonForm.address.province.trim() || "Saskatchewan",
          postal_code: newPersonForm.address.postal_code.trim() || undefined,
          on_reserve: newPersonForm.address.on_reserve,
          is_primary: true,
        };
      }

      if (
        newPersonForm.cultural.cultural_connections ||
        newPersonForm.cultural.ceremonies ||
        newPersonForm.cultural.elders_connected ||
        newPersonForm.cultural.dietary_preferences
      ) {
        personPayload.cultural_profile = {
          cultural_connections: newPersonForm.cultural.cultural_connections || undefined,
          ceremonies: newPersonForm.cultural.ceremonies || undefined,
          elders_connected: newPersonForm.cultural.elders_connected || undefined,
          land_based_activities: newPersonForm.cultural.land_based_activities || undefined,
          dietary_preferences: newPersonForm.cultural.dietary_preferences || undefined,
          extracurricular_activities: newPersonForm.cultural.extracurricular_activities || undefined,
        };
      }

      // 2. Create canonical Person record
      const createdPerson = await personsApi.create(personPayload);

      // 2b. Upload photo if selected
      if (photoFile) {
        try {
          await personsApi.uploadPhoto(createdPerson.id, photoFile);
        } catch (photoErr) {
          console.warn("Photo upload warning:", photoErr);
        }
      }

      // 3. Link newly created Person to the Case
      await casesApi.addPerson(caseId, {
        person_id: createdPerson.id,
        role: caseRoleForm.role,
        relationship_to_subject: caseRoleForm.relationship_to_subject || undefined,
        is_primary: caseRoleForm.is_primary,
        start_date: caseRoleForm.start_date || undefined,
        notes: caseRoleForm.notes || undefined,
      });

      toast({
        title: "Person created & linked",
        description: `${createdPerson.first_name} ${createdPerson.last_name} assigned CRBCL ID ${createdPerson.person_id_number} and linked to case.`,
      });

      handleClose();
      if (onSuccess) onSuccess();
    } catch (err) {
      toast({
        title: "Creation failed",
        description: err.message || "Failed to create and link person",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl font-bold flex items-center gap-2">
              {mode === "search" && "Add Person to Case — Search First"}
              {mode === "existing_role" && `Link ${selectedPerson?.first_name} ${selectedPerson?.last_name} to Case`}
              {mode === "create_new" && "Create Comprehensive Person Profile"}
              {mode === "duplicate_warning" && "Potential Duplicate Match Warning"}
            </DialogTitle>
          </div>
        </DialogHeader>

        {/* ── MODE 1: SEARCH FIRST ────────────────────────────────────────── */}
        {mode === "search" && (
          <div className="space-y-5 py-2">
            <p className="text-xs text-muted-foreground">
              Always search before creating a new record. You can search by numeric CRBCL Person ID,
              legal name, chosen name, or date of birth.
            </p>

            <form onSubmit={handleSearch} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Enter Person ID (e.g. 1123840557) or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                  autoFocus
                />
              </div>
              <Button type="submit" disabled={isSearching || !searchQuery.trim()}>
                {isSearching ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : <Search className="w-4 h-4 mr-1.5" />}
                Search
              </Button>
            </form>

            {/* Results Display */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {hasSearched ? `Search Matches (${searchResults.length})` : "Start a search or create a new profile"}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setMode("create_new")}
                  className="text-primary hover:text-primary font-medium"
                >
                  <UserPlus className="w-3.5 h-3.5 mr-1.5" />
                  Create New Person Instead
                </Button>
              </div>

              {hasSearched && searchResults.length === 0 && (
                <div className="border border-dashed rounded-xl p-8 text-center space-y-3">
                  <p className="text-sm text-muted-foreground">
                    No matching persons found in the canonical database for "{searchQuery}".
                  </p>
                  <Button onClick={() => setMode("create_new")} size="sm">
                    <UserPlus className="w-4 h-4 mr-1.5" /> Create New Person Record
                  </Button>
                </div>
              )}

              {searchResults.length > 0 && (
                <div className="border rounded-xl divide-y max-h-72 overflow-y-auto">
                  {searchResults.map((p) => (
                    <div
                      key={p.id}
                      className="p-3 hover:bg-muted/40 transition flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10 border">
                          <AvatarFallback className="text-xs font-semibold">
                            {p.first_name?.[0]}{p.last_name?.[0]}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm text-foreground">
                              {p.first_name} {p.middle_name ? `${p.middle_name} ` : ""}{p.last_name}
                            </span>
                            <Badge variant="secondary" className="font-mono text-xs font-normal">
                              ID: {p.person_id_number}
                            </Badge>
                            {p.preferred_name && (
                              <span className="text-xs text-muted-foreground">("{p.preferred_name}")</span>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground flex gap-3 mt-0.5">
                            <span>DOB: {p.date_of_birth || "Unknown"}</span>
                            {p.phone && <span>Phone: {p.phone}</span>}
                            {p.band_nation && <span>Nation: {p.band_nation}</span>}
                          </div>
                        </div>
                      </div>

                      <Button size="sm" onClick={() => handleSelectExisting(p)}>
                        <Check className="w-3.5 h-3.5 mr-1" /> Select Person
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── MODE 2: SPECIFY CASE-SPECIFIC ROLE (EXISTING PERSON) ────────── */}
        {mode === "existing_role" && selectedPerson && (
          <div className="space-y-4 py-2">
            <div className="flex items-center justify-between p-3 bg-muted/40 border rounded-xl">
              <div className="flex items-center gap-3">
                <Avatar className="h-10 w-10 border">
                  <AvatarFallback>{selectedPerson.first_name?.[0]}{selectedPerson.last_name?.[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <div className="font-semibold text-sm">
                    {selectedPerson.first_name} {selectedPerson.last_name}
                  </div>
                  <div className="text-xs text-muted-foreground flex gap-2">
                    <span className="font-mono">CRBCL Person ID: {selectedPerson.person_id_number}</span>
                    <span>•</span>
                    <span>DOB: {selectedPerson.date_of_birth || "N/A"}</span>
                  </div>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setMode("search")}>
                <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Change Person
              </Button>
            </div>

            <div className="border rounded-xl p-4 space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Case Participation Details
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-xs font-medium">Role in this Case *</Label>
                  <select
                    className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                    value={caseRoleForm.role}
                    onChange={(e) => setCaseRoleForm({ ...caseRoleForm, role: e.target.value })}
                  >
                    <option value="subject_child">Subject Child</option>
                    <option value="sibling">Sibling</option>
                    <option value="parent">Parent</option>
                    <option value="guardian">Legal Guardian</option>
                    <option value="caregiver">Kinship / Customary Caregiver</option>
                    <option value="person_of_concern">Person of Concern</option>
                    <option value="collateral">Collateral / Contact</option>
                    <option value="other">Other Relative / Participant</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs font-medium">Relationship to Subject Child</Label>
                  <Input
                    placeholder="e.g. Biological Mother, Maternal Aunt, Brother"
                    value={caseRoleForm.relationship_to_subject}
                    onChange={(e) => setCaseRoleForm({ ...caseRoleForm, relationship_to_subject: e.target.value })}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs font-medium">Participation Start Date</Label>
                  <Input
                    type="date"
                    value={caseRoleForm.start_date}
                    onChange={(e) => setCaseRoleForm({ ...caseRoleForm, start_date: e.target.value })}
                  />
                </div>

                <div className="flex items-center gap-2 pt-6">
                  <Checkbox
                    id="is_primary"
                    checked={caseRoleForm.is_primary}
                    onCheckedChange={(checked) => setCaseRoleForm({ ...caseRoleForm, is_primary: !!checked })}
                  />
                  <Label htmlFor="is_primary" className="text-xs font-medium cursor-pointer">
                    Primary subject / focus person on this case
                  </Label>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Case-Specific Notes (Optional)</Label>
                <Textarea
                  placeholder="Contextual notes regarding their role or involvement in this case..."
                  rows={2}
                  value={caseRoleForm.notes}
                  onChange={(e) => setCaseRoleForm({ ...caseRoleForm, notes: e.target.value })}
                />
              </div>
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button variant="outline" onClick={() => setMode("search")}>Back to Search</Button>
              <Button onClick={handleLinkExistingPerson} disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : <UserCheck className="w-4 h-4 mr-1.5" />}
                Link Person to Case
              </Button>
            </DialogFooter>
          </div>
        )}

        {/* ── MODE 3: CREATE NEW COMPREHENSIVE PERSON ─────────────────────── */}
        {mode === "create_new" && (
          <form onSubmit={handlePreCreateCheck} className="space-y-5 py-2">
            <div className="flex justify-between items-center">
              <p className="text-xs text-muted-foreground">
                Capture the canonical identity record. A permanent 10-digit CRBCL Person ID will be
                automatically generated upon saving.
              </p>
              <Button variant="ghost" size="sm" onClick={() => setMode("search")}>
                <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Search
              </Button>
            </div>

            <Tabs defaultValue="identity" className="w-full">
              <TabsList className="grid grid-cols-4 w-full">
                <TabsTrigger value="identity" className="text-xs">1. Identity</TabsTrigger>
                <TabsTrigger value="physical" className="text-xs">2. Physical ID</TabsTrigger>
                <TabsTrigger value="contact" className="text-xs">3. Contact & Address</TabsTrigger>
                <TabsTrigger value="cultural" className="text-xs">4. Cultural</TabsTrigger>
              </TabsList>

              {/* TAB 1: IDENTITY */}
              <TabsContent value="identity" className="space-y-4 pt-3">
                {/* Profile Photo Selector */}
                <div className="flex items-center gap-4 p-3 border rounded-lg bg-muted/20">
                  <Avatar className="h-14 w-14 border shadow-sm">
                    <AvatarImage src={photoPreview} />
                    <AvatarFallback className="text-sm font-semibold bg-primary/10 text-primary">
                      {newPersonForm.first_name?.[0] || ""}{newPersonForm.last_name?.[0] || "?"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="space-y-1 flex-1">
                    <Label className="text-xs font-medium">Profile Photo (Optional)</Label>
                    <Input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="text-xs h-8 cursor-pointer"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          if (!file.type.startsWith("image/")) {
                            toast({ title: "Invalid file", description: "Only image files (JPEG, PNG, WebP) are allowed", variant: "destructive" });
                            return;
                          }
                          setPhotoFile(file);
                          setPhotoPreview(URL.createObjectURL(file));
                        }
                      }}
                    />
                    <p className="text-[11px] text-muted-foreground">Supported formats: JPEG, PNG, WebP</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Legal First Name *</Label>
                    <Input
                      required
                      value={newPersonForm.first_name}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, first_name: e.target.value })}
                      placeholder="First name"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Middle Name(s)</Label>
                    <Input
                      value={newPersonForm.middle_name}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, middle_name: e.target.value })}
                      placeholder="Middle name"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Legal Last Name *</Label>
                    <Input
                      required
                      value={newPersonForm.last_name}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, last_name: e.target.value })}
                      placeholder="Last name"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Preferred / Chosen Name</Label>
                    <Input
                      value={newPersonForm.preferred_name}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, preferred_name: e.target.value })}
                      placeholder="Preferred name"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Aliases / Previous Names</Label>
                    <Input
                      value={newPersonForm.aliases}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, aliases: e.target.value })}
                      placeholder="Comma-separated"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Date of Birth</Label>
                    <Input
                      type="date"
                      value={newPersonForm.date_of_birth}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, date_of_birth: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Gender</Label>
                    <select
                      className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                      value={newPersonForm.gender}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, gender: e.target.value })}
                    >
                      <option value="">-- Select Gender --</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Non-Binary">Non-Binary</option>
                      <option value="Two-Spirit">Two-Spirit</option>
                      <option value="Prefer Not to Disclose">Prefer Not to Disclose</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Place of Birth</Label>
                    <Input
                      value={newPersonForm.place_of_birth}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, place_of_birth: e.target.value })}
                      placeholder="e.g. Regina, SK"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Preferred Language</Label>
                    <Input
                      value={newPersonForm.preferred_language}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, preferred_language: e.target.value })}
                      placeholder="e.g. English, Cree, Saulteaux"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Treaty / Status Card #</Label>
                    <Input
                      value={newPersonForm.treaty_number}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, treaty_number: e.target.value })}
                      placeholder="10-digit registration #"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Band / First Nation</Label>
                    <Input
                      value={newPersonForm.band_nation}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, band_nation: e.target.value })}
                      placeholder="e.g. Zagime Anishinabek"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Saskatchewan Health Card (HSN)</Label>
                    <Input
                      value={newPersonForm.health_card_number}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, health_card_number: e.target.value })}
                      placeholder="9-digit HSN"
                    />
                  </div>
                </div>
              </TabsContent>

              {/* TAB 2: PHYSICAL IDENTIFICATION */}
              <TabsContent value="physical" className="space-y-4 pt-3">
                <p className="text-xs text-muted-foreground">
                  CRBCL requires detailed physical identifying markers for safeguarding and identification.
                  Leave unknown fields blank.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Eye Colour</Label>
                    <Input
                      value={newPersonForm.physical.eye_colour}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, eye_colour: e.target.value },
                        })
                      }
                      placeholder="e.g. Brown, Hazel"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Hair Colour</Label>
                    <Input
                      value={newPersonForm.physical.hair_colour}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, hair_colour: e.target.value },
                        })
                      }
                      placeholder="e.g. Black, Dark Brown"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Height (cm)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={newPersonForm.physical.height_cm}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, height_cm: e.target.value },
                        })
                      }
                      placeholder="e.g. 145"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Weight (kg)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={newPersonForm.physical.weight_kg}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, weight_kg: e.target.value },
                        })
                      }
                      placeholder="e.g. 42"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Birthmarks & Locations</Label>
                    <Textarea
                      rows={2}
                      value={newPersonForm.physical.birthmarks}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, birthmarks: e.target.value },
                        })
                      }
                      placeholder="e.g. Small oval birthmark on right upper arm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Scars & Surgical Marks</Label>
                    <Textarea
                      rows={2}
                      value={newPersonForm.physical.scars}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, scars: e.target.value },
                        })
                      }
                      placeholder="e.g. 2cm scar above left eyebrow"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Tattoos & Body Art</Label>
                    <Textarea
                      rows={2}
                      value={newPersonForm.physical.tattoos}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, tattoos: e.target.value },
                        })
                      }
                      placeholder="Locations and descriptions of tattoos"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Piercings</Label>
                    <Textarea
                      rows={2}
                      value={newPersonForm.physical.piercings}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, piercings: e.target.value },
                        })
                      }
                      placeholder="e.g. Left earlobe, right nostril"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-medium">Distinguishing Marks & Observable Features</Label>
                  <Textarea
                    rows={2}
                    value={newPersonForm.physical.distinguishing_marks}
                    onChange={(e) =>
                      setNewPersonForm({
                        ...newPersonForm,
                        physical: { ...newPersonForm.physical, distinguishing_marks: e.target.value },
                      })
                    }
                    placeholder="e.g. Dental braces, noticeable limp, unique freckle patterns"
                  />
                </div>

                <div className="flex gap-6 pt-2">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="glasses"
                      checked={newPersonForm.physical.glasses}
                      onCheckedChange={(c) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, glasses: !!c },
                        })
                      }
                    />
                    <Label htmlFor="glasses" className="text-xs cursor-pointer">Wears Prescription Glasses</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="lenses"
                      checked={newPersonForm.physical.contact_lenses}
                      onCheckedChange={(c) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          physical: { ...newPersonForm.physical, contact_lenses: !!c },
                        })
                      }
                    />
                    <Label htmlFor="lenses" className="text-xs cursor-pointer">Wears Contact Lenses</Label>
                  </div>
                </div>
              </TabsContent>

              {/* TAB 3: CONTACT & ADDRESS */}
              <TabsContent value="contact" className="space-y-4 pt-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Primary Phone</Label>
                    <Input
                      value={newPersonForm.phone}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, phone: e.target.value })}
                      placeholder="e.g. (306) 555-0199"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Email Address</Label>
                    <Input
                      type="email"
                      value={newPersonForm.email}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, email: e.target.value })}
                      placeholder="name@example.ca"
                    />
                  </div>
                </div>

                <div className="border rounded-lg p-3 space-y-3 bg-muted/20">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">Current Residential Address</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="space-y-1 sm:col-span-2">
                      <Label className="text-xs font-medium">Street Address</Label>
                      <Input
                        value={newPersonForm.address.address_line_1}
                        onChange={(e) =>
                          setNewPersonForm({
                            ...newPersonForm,
                            address: { ...newPersonForm.address, address_line_1: e.target.value },
                          })
                        }
                        placeholder="e.g. 1245 Saskatchewan Drive"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs font-medium">City</Label>
                      <Input
                        value={newPersonForm.address.city}
                        onChange={(e) =>
                          setNewPersonForm({
                            ...newPersonForm,
                            address: { ...newPersonForm.address, city: e.target.value },
                          })
                        }
                        placeholder="Regina"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs font-medium">Postal Code</Label>
                      <Input
                        value={newPersonForm.address.postal_code}
                        onChange={(e) =>
                          setNewPersonForm({
                            ...newPersonForm,
                            address: { ...newPersonForm.address, postal_code: e.target.value },
                          })
                        }
                        placeholder="S4P 3Y2"
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <Checkbox
                      id="on_reserve"
                      checked={newPersonForm.address.on_reserve}
                      onCheckedChange={(c) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          address: { ...newPersonForm.address, on_reserve: !!c },
                        })
                      }
                    />
                    <Label htmlFor="on_reserve" className="text-xs cursor-pointer">
                      Located On-Reserve / Treaty Land
                    </Label>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Emergency Contact Name</Label>
                    <Input
                      value={newPersonForm.emergency_contact_name}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, emergency_contact_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Emergency Contact Phone</Label>
                    <Input
                      value={newPersonForm.emergency_contact_phone}
                      onChange={(e) => setNewPersonForm({ ...newPersonForm, emergency_contact_phone: e.target.value })}
                    />
                  </div>
                </div>
              </TabsContent>

              {/* TAB 4: CULTURAL & PREFERENCES */}
              <TabsContent value="cultural" className="space-y-4 pt-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Cultural & Clan Connections</Label>
                    <Textarea
                      rows={2}
                      value={newPersonForm.cultural.cultural_connections}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          cultural: { ...newPersonForm.cultural, cultural_connections: e.target.value },
                        })
                      }
                      placeholder="Clan, territory, or customary traditions"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Ceremonies & Protocols</Label>
                    <Textarea
                      rows={2}
                      value={newPersonForm.cultural.ceremonies}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          cultural: { ...newPersonForm.cultural, ceremonies: e.target.value },
                        })
                      }
                      placeholder="Smudging, feast participation, naming ceremonies"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Dietary Needs & Preferences</Label>
                    <Input
                      value={newPersonForm.cultural.dietary_preferences}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          cultural: { ...newPersonForm.cultural, dietary_preferences: e.target.value },
                        })
                      }
                      placeholder="Traditional foods, allergies, cultural preferences"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Extracurricular Activities & Interests</Label>
                    <Input
                      value={newPersonForm.cultural.extracurricular_activities}
                      onChange={(e) =>
                        setNewPersonForm({
                          ...newPersonForm,
                          cultural: { ...newPersonForm.cultural, extracurricular_activities: e.target.value },
                        })
                      }
                      placeholder="Sports, arts, music, powwow dancing"
                    />
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            {/* Case Link Section (Required on this workflow) */}
            <div className="border rounded-xl p-3.5 bg-muted/30 space-y-3">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Case Association For This Person
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs font-medium">Role in this Case *</Label>
                  <select
                    className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                    value={caseRoleForm.role}
                    onChange={(e) => setCaseRoleForm({ ...caseRoleForm, role: e.target.value })}
                  >
                    <option value="subject_child">Subject Child</option>
                    <option value="sibling">Sibling</option>
                    <option value="parent">Parent</option>
                    <option value="guardian">Legal Guardian</option>
                    <option value="caregiver">Kinship / Customary Caregiver</option>
                    <option value="person_of_concern">Person of Concern</option>
                    <option value="collateral">Collateral / Contact</option>
                    <option value="other">Other Relative / Participant</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs font-medium">Relationship to Subject</Label>
                  <Input
                    placeholder="e.g. Mother, Uncle, Self"
                    value={caseRoleForm.relationship_to_subject}
                    onChange={(e) => setCaseRoleForm({ ...caseRoleForm, relationship_to_subject: e.target.value })}
                  />
                </div>
                <div className="flex items-center gap-2 pt-6">
                  <Checkbox
                    id="new_is_primary"
                    checked={caseRoleForm.is_primary}
                    onCheckedChange={(c) => setCaseRoleForm({ ...caseRoleForm, is_primary: !!c })}
                  />
                  <Label htmlFor="new_is_primary" className="text-xs font-medium cursor-pointer">
                    Primary focus child / person
                  </Label>
                </div>
              </div>
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button type="button" variant="outline" onClick={() => setMode("search")}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                    Validating & Creating...
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4 mr-1.5" />
                    Create & Link to Case
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        )}

        {/* ── MODE 4: DUPLICATE WARNING MODAL ─────────────────────────────── */}
        {mode === "duplicate_warning" && (
          <div className="space-y-4 py-2">
            <Alert variant="destructive" className="border-amber-500/50 bg-amber-500/10 text-amber-950 dark:text-amber-200">
              <ShieldAlert className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              <AlertTitle className="font-bold text-sm">Potential Duplicate Person Detected</AlertTitle>
              <AlertDescription className="text-xs">
                One or more existing individuals strongly match the information entered.
                To maintain canonical identity integrity, review matches below before deciding to proceed.
              </AlertDescription>
            </Alert>

            <div className="border rounded-xl divide-y max-h-64 overflow-y-auto">
              {duplicateCandidates.map((c) => (
                <div key={c.person_id} className="p-3.5 flex items-center justify-between gap-3 hover:bg-muted/30">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{c.first_name} {c.last_name}</span>
                      <Badge variant="secondary" className="font-mono text-xs">ID: {c.person_id_number}</Badge>
                      <Badge variant="outline" className="text-xs bg-amber-500/10 text-amber-700 dark:text-amber-300">
                        {Math.round(c.similarity_score * 100)}% Match
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      <span>DOB: {c.date_of_birth || "Unknown"}</span>
                      {c.phone && <span className="ml-3">Phone: {c.phone}</span>}
                      {c.matching_factors?.length > 0 && (
                        <div className="text-amber-700 dark:text-amber-400 mt-0.5">
                          Factors: {c.matching_factors.join(", ")}
                        </div>
                      )}
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="default"
                    onClick={() => {
                      setSelectedPerson({
                        id: c.person_id,
                        first_name: c.first_name,
                        last_name: c.last_name,
                        person_id_number: c.person_id_number,
                        date_of_birth: c.date_of_birth,
                      });
                      setMode("existing_role");
                    }}
                  >
                    <Check className="w-3.5 h-3.5 mr-1" /> Use Existing Person
                  </Button>
                </div>
              ))}
            </div>

            <DialogFooter className="gap-2 sm:gap-0 justify-between items-center w-full">
              <Button variant="outline" onClick={() => setMode("create_new")}>
                <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Edit Form
              </Button>
              <Button
                variant="destructive"
                onClick={executeCreateAndLink}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 mr-1.5" />
                )}
                Confirm Duplicate Override & Create New Record
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

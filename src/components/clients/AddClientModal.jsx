import React, { useState, useEffect } from "react";
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
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/components/ui/use-toast";
import { clientsApi, personsApi, teamsApi } from "@/api";
import ComprehensivePersonForm from "@/components/person/ComprehensivePersonForm";
import {
  Search,
  UserPlus,
  AlertTriangle,
  ArrowLeft,
  Loader2,
  UserCheck,
  CheckCircle2,
  Clock,
  Ban,
  ShieldCheck,
} from "lucide-react";

export default function AddClientModal({ isOpen, onClose, onSuccess }) {
  const { toast } = useToast();

  // Modes: "search" | "submit_existing" | "create_new" | "duplicate_warning"
  const [mode, setMode] = useState("search");

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  // Teams list for assignment
  const [teams, setTeams] = useState([]);

  // Selected existing person for proposal
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [existingProposalForm, setExistingProposalForm] = useState({
    risk_level: "Low",
    assigned_team_id: "",
    submission_notes: "",
  });

  // Comprehensive Person form state for creating new person
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
    treaty_number: "",
    band_nation: "",
    health_card_number: "",
    phone: "",
    email: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    emergency_contact_relationship: "",
    employment_status: "",
    employer: "",
    source_of_income: "",
    physical_description: {
      eye_colour: "",
      hair_colour: "",
      height_cm: null,
      weight_kg: null,
      tattoos: "",
      piercings: "",
      scars: "",
      birthmarks: "",
      distinguishing_marks: "",
      glasses: false,
      contact_lenses: false,
      notes: "",
    },
    primary_address: {
      address_line_1: "",
      address_line_2: "",
      city: "Regina",
      province: "Saskatchewan",
      postal_code: "",
      on_reserve: false,
    },
    cultural_profile: {
      cultural_connections: "",
      ceremonies: "",
      elders_connected: "",
      land_based_activities: "",
    },
  });

  const [newClientProposalMeta, setNewClientProposalMeta] = useState({
    risk_level: "Low",
    assigned_team_id: "",
    submission_notes: "",
  });

  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);

  // Duplicate candidates warning
  const [duplicateCandidates, setDuplicateCandidates] = useState([]);
  const [isCheckingDuplicates, setIsCheckingDuplicates] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadTeams();
    }
  }, [isOpen]);

  const loadTeams = async () => {
    try {
      if (teamsApi?.list) {
        const res = await teamsApi.list();
        setTeams(Array.isArray(res) ? res : res.items || []);
      }
    } catch {
      setTeams([]);
    }
  };

  const handleClose = () => {
    setMode("search");
    setSearchQuery("");
    setSearchResults([]);
    setHasSearched(false);
    setSelectedPerson(null);
    setPhotoFile(null);
    setPhotoPreview(null);
    setDuplicateCandidates([]);
    setExistingProposalForm({
      risk_level: "Low",
      assigned_team_id: "",
      submission_notes: "",
    });
    setNewClientProposalMeta({
      risk_level: "Low",
      assigned_team_id: "",
      submission_notes: "",
    });
    onClose();
  };

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    try {
      const res = await clientsApi.searchPersons({ query: searchQuery.trim(), limit: 20 });
      setSearchResults(res.items || []);
    } catch (err) {
      console.error("Search failed:", err);
      toast({
        title: "Search error",
        description: err?.message || "Failed to search existing persons",
        variant: "destructive",
      });
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectExistingPerson = (person) => {
    setSelectedPerson(person);
    setMode("submit_existing");
  };

  const handleSubmitExistingProposal = async () => {
    if (!selectedPerson) return;
    setIsSubmitting(true);
    try {
      const payload = {
        person_id: selectedPerson.id,
        risk_level: existingProposalForm.risk_level || "Low",
        assigned_team_id: existingProposalForm.assigned_team_id || undefined,
        submission_notes: existingProposalForm.submission_notes?.trim() || undefined,
      };

      const result = await clientsApi.submitExisting(payload);
      toast({
        title: "Client Proposal Submitted",
        description: `${selectedPerson.first_name} ${selectedPerson.last_name} (ID: ${selectedPerson.person_id_number || "Assigned"}) submitted for Supervisor/Director approval.`,
      });

      if (onSuccess) onSuccess(result);
      handleClose();
    } catch (err) {
      const errMsg = err?.error?.message || err?.message || "Failed to submit client proposal";
      toast({
        title: "Proposal Failed",
        description: errMsg,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePreCreateCheck = async (e) => {
    e.preventDefault();
    if (!newPersonForm.first_name?.trim() || !newPersonForm.last_name?.trim()) {
      toast({
        title: "Required Fields Missing",
        description: "Legal First Name and Legal Last Name are required.",
        variant: "destructive",
      });
      return;
    }

    setIsCheckingDuplicates(true);
    try {
      const dupRes = await clientsApi.checkDuplicates({
        first_name: newPersonForm.first_name.trim(),
        last_name: newPersonForm.last_name.trim(),
        date_of_birth: newPersonForm.date_of_birth || undefined,
        treaty_number: newPersonForm.treaty_number || undefined,
        health_card_number: newPersonForm.health_card_number || undefined,
        phone: newPersonForm.phone || undefined,
        email: newPersonForm.email || undefined,
      });

      if (dupRes?.has_potential_duplicates && dupRes.candidates?.length > 0) {
        setDuplicateCandidates(dupRes.candidates);
        setMode("duplicate_warning");
      } else {
        await executeCreateNewClientProposal();
      }
    } catch (err) {
      console.warn("Duplicate check warning:", err);
      await executeCreateNewClientProposal();
    } finally {
      setIsCheckingDuplicates(false);
    }
  };

  const executeCreateNewClientProposal = async () => {
    setIsSubmitting(true);
    try {
      const personData = {
        first_name: newPersonForm.first_name.trim(),
        middle_name: newPersonForm.middle_name?.trim() || undefined,
        last_name: newPersonForm.last_name.trim(),
        preferred_name: newPersonForm.preferred_name?.trim() || undefined,
        aliases: newPersonForm.aliases?.trim() || undefined,
        date_of_birth: newPersonForm.date_of_birth || undefined,
        gender: newPersonForm.gender || undefined,
        place_of_birth: newPersonForm.place_of_birth?.trim() || undefined,
        preferred_language: newPersonForm.preferred_language?.trim() || "English",
        treaty_number: newPersonForm.treaty_number?.trim() || undefined,
        band_nation: newPersonForm.band_nation?.trim() || undefined,
        health_card_number: newPersonForm.health_card_number?.trim() || undefined,
        phone: newPersonForm.phone?.trim() || undefined,
        email: newPersonForm.email?.trim() || undefined,
        emergency_contact_name: newPersonForm.emergency_contact_name?.trim() || undefined,
        emergency_contact_phone: newPersonForm.emergency_contact_phone?.trim() || undefined,
        emergency_contact_relationship: newPersonForm.emergency_contact_relationship?.trim() || undefined,
        employment_status: newPersonForm.employment_status || undefined,
        employer: newPersonForm.employer?.trim() || undefined,
        source_of_income: newPersonForm.source_of_income?.trim() || undefined,
      };

      if (
        newPersonForm.physical_description?.eye_colour ||
        newPersonForm.physical_description?.hair_colour ||
        newPersonForm.physical_description?.height_cm ||
        newPersonForm.physical_description?.weight_kg ||
        newPersonForm.physical_description?.tattoos ||
        newPersonForm.physical_description?.scars ||
        newPersonForm.physical_description?.birthmarks ||
        newPersonForm.physical_description?.distinguishing_marks
      ) {
        personData.physical_description = {
          ...newPersonForm.physical_description,
          height_cm: newPersonForm.physical_description.height_cm ? parseFloat(newPersonForm.physical_description.height_cm) : undefined,
          weight_kg: newPersonForm.physical_description.weight_kg ? parseFloat(newPersonForm.physical_description.weight_kg) : undefined,
        };
      }

      if (newPersonForm.primary_address?.address_line_1?.trim()) {
        personData.primary_address = {
          ...newPersonForm.primary_address,
          address_line_1: newPersonForm.primary_address.address_line_1.trim(),
        };
      }

      if (
        newPersonForm.cultural_profile?.cultural_connections ||
        newPersonForm.cultural_profile?.ceremonies ||
        newPersonForm.cultural_profile?.elders_connected ||
        newPersonForm.cultural_profile?.land_based_activities
      ) {
        personData.cultural_profile = { ...newPersonForm.cultural_profile };
      }

      const payload = {
        person: personData,
        risk_level: newClientProposalMeta.risk_level || "Low",
        assigned_team_id: newClientProposalMeta.assigned_team_id || undefined,
        submission_notes: newClientProposalMeta.submission_notes?.trim() || undefined,
      };

      const result = await clientsApi.submitNew(payload);

      // Upload photo if selected
      if (photoFile && result.person_id) {
        try {
          await personsApi.uploadPhoto(result.person_id, photoFile);
        } catch (photoErr) {
          console.warn("Photo upload warning:", photoErr);
        }
      }

      toast({
        title: "Canonical Person Created & Client Proposed",
        description: `${result.first_name} ${result.last_name} assigned permanent CRBCL ID ${result.person_id_number || ""}. Awaiting supervisor review.`,
      });

      if (onSuccess) onSuccess(result);
      handleClose();
    } catch (err) {
      console.error("Creation failed:", err);
      const msg = err?.error?.message || err?.message || "Failed to create client proposal";
      toast({
        title: "Submission Error",
        description: msg,
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
          <DialogTitle className="flex items-center gap-2 text-lg">
            <UserPlus className="w-5 h-5 text-primary" />
            {mode === "search" && "Add Client — Search Existing Identity"}
            {mode === "submit_existing" && "Propose Existing Person as Client"}
            {mode === "create_new" && "New Client — Canonical Identity Intake"}
            {mode === "duplicate_warning" && "Potential Identity Match Warning"}
          </DialogTitle>
        </DialogHeader>

        {/* ── MODE 1: SEARCH-BEFORE-CREATE ───────────────────────────────── */}
        {mode === "search" && (
          <div className="space-y-4 py-2">
            <div className="bg-primary/5 border border-primary/20 rounded-xl p-3.5 text-xs space-y-1.5">
              <div className="flex items-center gap-1.5 font-semibold text-primary">
                <ShieldCheck className="w-4 h-4" />
                CRBCL Canonical Human Identity Standard
              </div>
              <p className="text-muted-foreground">
                Before proposing a new client, verify whether their canonical Person record already exists.
                Search by full name, aliases, or 10-digit CRBCL Person ID. Photographs are not displayed during search for client privacy.
              </p>
            </div>

            <form onSubmit={handleSearch} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by legal name, preferred name, alias, or 10-digit ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 text-sm"
                  autoFocus
                />
              </div>
              <Button type="submit" disabled={isSearching || !searchQuery.trim()}>
                {isSearching ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
                Search
              </Button>
            </form>

            {/* Results Table */}
            {hasSearched && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Found {searchResults.length} matching {searchResults.length === 1 ? "record" : "records"}</span>
                  <Button
                    variant="link"
                    size="sm"
                    className="p-0 h-auto text-xs"
                    onClick={() => {
                      setNewPersonForm((prev) => ({
                        ...prev,
                        first_name: searchQuery.split(" ")[0] || "",
                        last_name: searchQuery.split(" ").slice(1).join(" ") || "",
                      }));
                      setMode("create_new");
                    }}
                  >
                    Person not found? Create new record &rarr;
                  </Button>
                </div>

                {searchResults.length === 0 ? (
                  <div className="text-center py-8 border border-dashed rounded-xl space-y-3 bg-muted/20">
                    <p className="text-sm font-medium">No matching individuals found</p>
                    <p className="text-xs text-muted-foreground max-w-md mx-auto">
                      No canonical Person matches &quot;{searchQuery}&quot;. You can proceed to create a comprehensive canonical record.
                    </p>
                    <Button
                      size="sm"
                      onClick={() => {
                        setNewPersonForm((prev) => ({
                          ...prev,
                          first_name: searchQuery.split(" ")[0] || "",
                          last_name: searchQuery.split(" ").slice(1).join(" ") || "",
                        }));
                        setMode("create_new");
                      }}
                    >
                      <UserPlus className="w-3.5 h-3.5 mr-1.5" />
                      Create Canonical Person &amp; Propose Client
                    </Button>
                  </div>
                ) : (
                  <div className="divide-y border rounded-xl overflow-hidden bg-card">
                    {searchResults.map((p) => {
                      const isApprovedClient = p.client_approval_status === "APPROVED";
                      const isPendingProposal = p.client_approval_status === "PENDING_APPROVAL";

                      return (
                        <div
                          key={p.id}
                          className="p-3.5 flex items-center justify-between gap-4 hover:bg-muted/40 transition-colors"
                        >
                          <div className="space-y-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-semibold text-sm">
                                {p.first_name} {p.middle_name ? `${p.middle_name} ` : ""}{p.last_name}
                              </span>
                              {p.preferred_name && (
                                <span className="text-xs text-muted-foreground">({p.preferred_name})</span>
                              )}
                              <Badge variant="outline" className="font-mono text-[11px] bg-muted/50">
                                #{p.person_id_number || "NO-ID"}
                              </Badge>

                              {isApprovedClient && (
                                <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 text-[11px] border-emerald-300">
                                  <CheckCircle2 className="w-3 h-3 mr-1" /> Already Approved Client
                                </Badge>
                              )}
                              {isPendingProposal && (
                                <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 text-[11px] border-amber-300">
                                  <Clock className="w-3 h-3 mr-1" /> Proposal Awaiting Approval
                                </Badge>
                              )}
                            </div>

                            <div className="text-xs text-muted-foreground flex gap-3 flex-wrap">
                              {p.date_of_birth && <span>DOB: {p.date_of_birth}</span>}
                              {p.gender && <span>Gender: {p.gender}</span>}
                              {p.band_nation && <span>Nation: {p.band_nation}</span>}
                              {p.city && <span>Location: {p.city}, {p.province || "SK"}</span>}
                            </div>
                          </div>

                          <div>
                            {isApprovedClient ? (
                              <Button size="sm" variant="outline" disabled className="opacity-60 text-xs">
                                <Ban className="w-3.5 h-3.5 mr-1" /> Active Client
                              </Button>
                            ) : isPendingProposal ? (
                              <Button size="sm" variant="outline" disabled className="opacity-60 text-xs">
                                <Clock className="w-3.5 h-3.5 mr-1" /> In Review
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                onClick={() => handleSelectExistingPerson(p)}
                              >
                                <UserCheck className="w-3.5 h-3.5 mr-1.5" />
                                Propose as Client
                              </Button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            <DialogFooter className="border-t pt-3">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              {!hasSearched && (
                <Button
                  variant="secondary"
                  onClick={() => setMode("create_new")}
                >
                  <UserPlus className="w-4 h-4 mr-1.5" />
                  Skip Search &amp; Create New
                </Button>
              )}
            </DialogFooter>
          </div>
        )}

        {/* ── MODE 2: SUBMIT EXISTING PERSON AS CLIENT ───────────────────── */}
        {mode === "submit_existing" && selectedPerson && (
          <div className="space-y-4 py-2">
            <div className="flex items-center justify-between p-3.5 border rounded-xl bg-muted/20">
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Selected Canonical Person</span>
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-sm">
                    {selectedPerson.first_name} {selectedPerson.last_name}
                  </h4>
                  <Badge variant="outline" className="font-mono text-xs">
                    #{selectedPerson.person_id_number || "NO-ID"}
                  </Badge>
                  {selectedPerson.date_of_birth && (
                    <span className="text-xs text-muted-foreground">
                      (DOB: {selectedPerson.date_of_birth})
                    </span>
                  )}
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setMode("search")}>
                <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Change Person
              </Button>
            </div>

            <div className="border rounded-xl p-4 space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Client Intake Proposal Details
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-xs font-medium">Initial Risk Level *</Label>
                  <select
                    className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                    value={existingProposalForm.risk_level}
                    onChange={(e) =>
                      setExistingProposalForm({ ...existingProposalForm, risk_level: e.target.value })
                    }
                  >
                    <option value="Low">Low Risk</option>
                    <option value="Medium">Medium Risk</option>
                    <option value="High">High Risk</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs font-medium">Assigned Team (Optional)</Label>
                  <select
                    className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                    value={existingProposalForm.assigned_team_id}
                    onChange={(e) =>
                      setExistingProposalForm({ ...existingProposalForm, assigned_team_id: e.target.value })
                    }
                  >
                    <option value="">-- General / Unassigned --</option>
                    {teams.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Submission Rationale &amp; Context Notes</Label>
                <Textarea
                  placeholder="Explain why client status is requested, service context, or stabilization needs for supervisor review..."
                  rows={3}
                  value={existingProposalForm.submission_notes}
                  onChange={(e) =>
                    setExistingProposalForm({ ...existingProposalForm, submission_notes: e.target.value })
                  }
                />
              </div>
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button variant="outline" onClick={() => setMode("search")}>
                Back to Search
              </Button>
              <Button onClick={handleSubmitExistingProposal} disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : <UserCheck className="w-4 h-4 mr-1.5" />}
                Submit Client Proposal
              </Button>
            </DialogFooter>
          </div>
        )}

        {/* ── MODE 3: CREATE NEW CANONICAL PERSON & PROPOSE CLIENT ────────── */}
        {mode === "create_new" && (
          <form onSubmit={handlePreCreateCheck} className="space-y-4 py-2">
            <div className="flex justify-between items-center">
              <p className="text-xs text-muted-foreground">
                Capture the canonical identity record. A permanent 10-digit CRBCL Person ID will be
                automatically generated upon saving, and the client context submitted for supervisor review.
              </p>
              <Button variant="ghost" size="sm" onClick={() => setMode("search")}>
                <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Search
              </Button>
            </div>

            <ComprehensivePersonForm
              formData={newPersonForm}
              setFormData={setNewPersonForm}
              photoFile={photoFile}
              setPhotoFile={setPhotoFile}
              photoPreview={photoPreview}
              setPhotoPreview={setPhotoPreview}
              showClientFields={true}
              clientFields={newClientProposalMeta}
              setClientFields={setNewClientProposalMeta}
              teams={teams}
            />

            <DialogFooter className="border-t pt-3 gap-2 sm:gap-0">
              <Button type="button" variant="outline" onClick={() => setMode("search")}>
                Cancel
              </Button>
              <Button type="submit" disabled={isCheckingDuplicates || isSubmitting}>
                {isCheckingDuplicates || isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                ) : (
                  <UserPlus className="w-4 h-4 mr-1.5" />
                )}
                Save Person &amp; Submit Client Proposal
              </Button>
            </DialogFooter>
          </form>
        )}

        {/* ── MODE 4: DUPLICATE WARNING MODAL ────────────────────────────── */}
        {mode === "duplicate_warning" && (
          <div className="space-y-4 py-2">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Potential Duplicate Identity Found</AlertTitle>
              <AlertDescription className="text-xs">
                One or more existing individuals match this name, DOB, or identifying information.
                Creating redundant Person records violates CRBCL canonical identity policies.
              </AlertDescription>
            </Alert>

            <div className="divide-y border rounded-xl overflow-hidden bg-card">
              {duplicateCandidates.map((cand) => (
                <div key={cand.id} className="p-3.5 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">
                        {cand.first_name} {cand.last_name}
                      </span>
                      <Badge variant="outline" className="font-mono text-xs">
                        #{cand.person_id_number || "NO-ID"}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground flex gap-3">
                      {cand.date_of_birth && <span>DOB: {cand.date_of_birth}</span>}
                      {cand.phone && <span>Phone: {cand.phone}</span>}
                      {cand.band_nation && <span>Nation: {cand.band_nation}</span>}
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSelectedPerson(cand);
                      setMode("submit_existing");
                    }}
                  >
                    <UserCheck className="w-3.5 h-3.5 mr-1" />
                    Use This Person Instead
                  </Button>
                </div>
              ))}
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button variant="outline" onClick={() => setMode("create_new")}>
                Back to Editing
              </Button>
              <Button
                variant="destructive"
                onClick={executeCreateNewClientProposal}
                disabled={isSubmitting}
              >
                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
                Confirm Non-Duplicate &amp; Save
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

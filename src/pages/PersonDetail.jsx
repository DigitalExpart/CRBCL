import React, { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { personsApi } from "@/api/persons";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/components/ui/use-toast";
import {
  User,
  ArrowLeft,
  Camera,
  Folder,
  Home,
  Users,
  HeartPulse,
  GraduationCap,
  Sparkles,
  FileText,
  Clock,
  ShieldAlert,
  Edit2,
  Calendar,
  Phone,
  Mail,
  MapPin,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Loader2,
  Download,
} from "lucide-react";

export default function PersonDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState("overview");
  const [showEditModal, setShowEditModal] = useState(false);
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);

  // 1. Fetch Comprehensive Profile
  const {
    data: profileData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["person-profile", id],
    queryFn: () => personsApi.getProfile(id),
    enabled: !!id,
  });

  const person = profileData?.person;

  // Edit form state
  const [editForm, setEditForm] = useState(null);

  const openEditDialog = () => {
    if (!person) return;
    setEditForm({
      first_name: person.first_name || "",
      middle_name: person.middle_name || "",
      last_name: person.last_name || "",
      preferred_name: person.preferred_name || "",
      aliases: person.aliases || "",
      date_of_birth: person.date_of_birth || "",
      gender: person.gender || "",
      place_of_birth: person.place_of_birth || "",
      preferred_language: person.preferred_language || "English",
      languages_spoken: person.languages_spoken || "",
      treaty_number: person.treaty_number || "",
      band_nation: person.band_nation || "",
      indigenous_identity: person.indigenous_identity || "",
      health_card_number: person.health_card_number || "",
      phone: person.phone || "",
      email: person.email || "",
      emergency_contact_name: person.emergency_contact_name || "",
      emergency_contact_phone: person.emergency_contact_phone || "",
      notes: person.notes || "",
      physical_description: {
        eye_colour: person.physical_description?.eye_colour || "",
        hair_colour: person.physical_description?.hair_colour || "",
        height_cm: person.physical_description?.height_cm || "",
        weight_kg: person.physical_description?.weight_kg || "",
        birthmarks: person.physical_description?.birthmarks || "",
        scars: person.physical_description?.scars || "",
        tattoos: person.physical_description?.tattoos || "",
        piercings: person.physical_description?.piercings || "",
        distinguishing_marks: person.physical_description?.distinguishing_marks || "",
        glasses: person.physical_description?.glasses || false,
        contact_lenses: person.physical_description?.contact_lenses || false,
      },
    });
    setShowEditModal(true);
  };

  const updateMutation = useMutation({
    mutationFn: (data) => personsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["person-profile", id] });
      setShowEditModal(false);
      toast({ title: "Profile updated", description: "Person identity details saved successfully." });
    },
    onError: (err) => {
      toast({ title: "Update failed", description: err.message, variant: "destructive" });
    },
  });

  const handleSaveEdit = (e) => {
    e.preventDefault();
    if (!editForm) return;
    const payload = {
      ...editForm,
      physical_description: {
        ...editForm.physical_description,
        height_cm: editForm.physical_description.height_cm
          ? parseFloat(editForm.physical_description.height_cm)
          : undefined,
        weight_kg: editForm.physical_description.weight_kg
          ? parseFloat(editForm.physical_description.weight_kg)
          : undefined,
      },
    };
    updateMutation.mutate(payload);
  };

  // Photo upload handler
  const handlePhotoFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast({ title: "Invalid file", description: "Please choose an image file (JPG, PNG, WebP).", variant: "destructive" });
      return;
    }

    try {
      setIsUploadingPhoto(true);
      await personsApi.uploadPhoto(id, file);
      queryClient.invalidateQueries({ queryKey: ["person-profile", id] });
      toast({ title: "Photo updated", description: "Profile photo saved successfully." });
    } catch (err) {
      toast({ title: "Upload failed", description: err.message || "Could not upload photo", variant: "destructive" });
    } finally {
      setIsUploadingPhoto(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-28 space-y-4">
        <Loader2 className="w-9 h-9 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Loading Canonical Person Record...</p>
      </div>
    );
  }

  if (error || !person) {
    return (
      <div className="p-8 max-w-xl mx-auto text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-destructive mx-auto" />
        <h2 className="text-xl font-bold">Person Profile Unavailable</h2>
        <p className="text-sm text-muted-foreground">
          {error?.message || "The requested person record does not exist or you lack authorization to view this file."}
        </p>
        <Button onClick={() => navigate(-1)} variant="outline">
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Return to Previous Screen
        </Button>
      </div>
    );
  }

  // Calculate age if DOB known
  const calculateAge = (dobString) => {
    if (!dobString) return null;
    const dob = new Date(dobString);
    const diff = Date.now() - dob.getTime();
    const ageDate = new Date(diff);
    return Math.abs(ageDate.getUTCFullYear() - 1970);
  };

  const age = calculateAge(person.date_of_birth);

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto px-4 sm:px-6">
      {/* ── Top Navigation Bar ────────────────────────────────────────── */}
      <div className="flex items-center justify-between pt-2">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="gap-1.5 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-4 h-4" /> Back
        </Button>
        <div className="flex items-center gap-2">
          {profileData?.client_id && (
            <Link to={`/clients/${profileData.client_id}`}>
              <Button variant="outline" size="sm" className="text-xs gap-1.5">
                <ExternalLink className="w-3.5 h-3.5" /> View Client Services File
              </Button>
            </Link>
          )}
          <Button size="sm" onClick={openEditDialog} className="text-xs gap-1.5">
            <Edit2 className="w-3.5 h-3.5" /> Edit Person Details
          </Button>
        </div>
      </div>

      {/* ── Hero Profile Header ───────────────────────────────────────── */}
      <Card className="border shadow-sm overflow-hidden bg-card">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
              {/* Avatar with upload trigger */}
              <div className="relative group">
                <Avatar className="h-24 w-24 border-2 border-primary/20 shadow-sm">
                  <AvatarImage src={person.photo_url} alt={person.first_name} />
                  <AvatarFallback className="text-2xl font-bold bg-muted text-muted-foreground">
                    {person.first_name?.[0]}{person.last_name?.[0]}
                  </AvatarFallback>
                </Avatar>
                <label className="absolute inset-0 flex items-center justify-center bg-black/40 text-white opacity-0 group-hover:opacity-100 rounded-full cursor-pointer transition-opacity">
                  <Camera className="w-5 h-5" />
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handlePhotoFileChange}
                    disabled={isUploadingPhoto}
                  />
                </label>
                {isUploadingPhoto && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-white rounded-full">
                    <Loader2 className="w-5 h-5 animate-spin" />
                  </div>
                )}
              </div>

              {/* Identity Title & Prominent Person ID */}
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h1 className="text-2xl font-bold font-heading text-foreground">
                    {person.first_name} {person.middle_name ? `${person.middle_name} ` : ""}{person.last_name}
                  </h1>
                  {person.preferred_name && (
                    <span className="text-sm font-medium text-muted-foreground">
                      (Known as "{person.preferred_name}")
                    </span>
                  )}
                </div>

                {/* PROMINENT NUMERIC CRBCL PERSON ID */}
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    CRBCL Person ID:
                  </span>
                  <Badge className="font-mono text-sm px-2.5 py-0.5 bg-primary/10 text-primary border-primary/20 font-bold tracking-wider">
                    {person.person_id_number}
                  </Badge>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground pt-1">
                  {person.date_of_birth ? (
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-primary/70" />
                      DOB: {person.date_of_birth} {age !== null ? `(${age} yrs)` : ""}
                    </span>
                  ) : (
                    <span>DOB: Unknown</span>
                  )}
                  {person.gender && <span>• Gender: {person.gender}</span>}
                  {person.band_nation && (
                    <Badge variant="outline" className="text-xs font-normal">
                      {person.band_nation}
                    </Badge>
                  )}
                  {person.treaty_number && (
                    <span className="font-mono">Treaty: {person.treaty_number}</span>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Contact summary */}
            <div className="flex flex-col sm:items-end gap-1.5 text-xs text-muted-foreground border-t sm:border-t-0 pt-3 sm:pt-0 w-full sm:w-auto">
              {person.phone && (
                <div className="flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5 text-primary/70" />
                  <span>{person.phone}</span>
                </div>
              )}
              {person.email && (
                <div className="flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-primary/70" />
                  <span>{person.email}</span>
                </div>
              )}
              {person.addresses?.[0] && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-primary/70" />
                  <span>{person.addresses[0].city}, {person.addresses[0].province}</span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Main Tabbed Content ────────────────────────────────────────── */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 w-full h-auto p-1 bg-muted/60">
          <TabsTrigger value="overview" className="text-xs py-2">Overview</TabsTrigger>
          <TabsTrigger value="identity_physical" className="text-xs py-2">Identity & Physical</TabsTrigger>
          <TabsTrigger value="contact_address" className="text-xs py-2">Contact & Address</TabsTrigger>
          <TabsTrigger value="family" className="text-xs py-2">
            Family & Kin ({profileData.relationships?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="cases_referrals" className="text-xs py-2">
            Cases & Intakes ({profileData.cases?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="placements" className="text-xs py-2">
            Placements ({profileData.placements?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="medical" className="text-xs py-2">Medical & Health</TabsTrigger>
          <TabsTrigger value="documents_timeline" className="text-xs py-2">Docs & Timeline</TabsTrigger>
        </TabsList>

        {/* ── TAB 1: OVERVIEW ──────────────────────────────────────────── */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Physical Snapshot Card */}
            <Card className="border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <User className="w-4 h-4 text-primary" /> Physical Identifier Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-muted-foreground">Eye Colour:</span>{" "}
                    <span className="font-medium text-foreground">{person.physical_description?.eye_colour || "Not Recorded"}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Hair Colour:</span>{" "}
                    <span className="font-medium text-foreground">{person.physical_description?.hair_colour || "Not Recorded"}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Height:</span>{" "}
                    <span className="font-medium text-foreground">
                      {person.physical_description?.height_cm ? `${person.physical_description.height_cm} cm` : "Not Recorded"}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Weight:</span>{" "}
                    <span className="font-medium text-foreground">
                      {person.physical_description?.weight_kg ? `${person.physical_description.weight_kg} kg` : "Not Recorded"}
                    </span>
                  </div>
                </div>
                {person.physical_description?.distinguishing_marks && (
                  <div className="pt-1.5 border-t">
                    <span className="text-muted-foreground">Distinguishing Marks:</span>
                    <p className="text-foreground mt-0.5">{person.physical_description.distinguishing_marks}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Active Cases & Involvements */}
            <Card className="border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Folder className="w-4 h-4 text-primary" /> Active Case Involvements
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs space-y-2">
                {profileData.cases.length === 0 ? (
                  <p className="text-muted-foreground">No active cases associated with this person.</p>
                ) : (
                  profileData.cases.slice(0, 3).map((c) => (
                    <div key={c.case_id} className="p-2 rounded bg-muted/40 flex justify-between items-center">
                      <div>
                        <Link to={`/cases/${c.case_id}`} className="font-medium hover:underline text-primary">
                          {c.case_number}
                        </Link>
                        <div className="text-[11px] text-muted-foreground capitalize">Role: {c.role_in_case?.replace(/_/g, " ")}</div>
                      </div>
                      <Badge variant="outline" className="text-[10px]">{c.stage}</Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Kinship & Living Arrangements */}
            <Card className="border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Home className="w-4 h-4 text-primary" /> Households & Kin
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs space-y-2">
                <div>
                  <span className="text-muted-foreground">Known Relatives / Contacts:</span>{" "}
                  <span className="font-semibold text-foreground">{profileData.relationships.length}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Residential Households:</span>{" "}
                  <span className="font-semibold text-foreground">{profileData.households.length}</span>
                </div>
                {profileData.households[0] && (
                  <div className="p-2 rounded bg-muted/40 mt-2">
                    <span className="font-medium text-foreground">{profileData.households[0].household_name}</span>
                    <p className="text-[11px] text-muted-foreground">{profileData.households[0].address}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Notes & Context */}
          {person.notes && (
            <Card className="border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold">General Biographical Notes</CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-foreground whitespace-pre-wrap">
                {person.notes}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ── TAB 2: IDENTITY & PHYSICAL DESCRIPTION ───────────────────── */}
        <TabsContent value="identity_physical" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Legal Identity Details */}
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Authoritative Legal Identity</CardTitle>
                <CardDescription className="text-xs">Civil registration and governance identifiers</CardDescription>
              </CardHeader>
              <CardContent className="text-xs space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-muted-foreground">Legal First Name</span>
                    <p className="font-medium text-foreground">{person.first_name}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Legal Middle Name</span>
                    <p className="font-medium text-foreground">{person.middle_name || "—"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Legal Last Name</span>
                    <p className="font-medium text-foreground">{person.last_name}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Preferred / Chosen Name</span>
                    <p className="font-medium text-foreground">{person.preferred_name || "—"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Aliases / Previous Names</span>
                    <p className="font-medium text-foreground">{person.aliases || "—"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Date of Birth</span>
                    <p className="font-medium text-foreground">{person.date_of_birth || "Unknown"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Place of Birth</span>
                    <p className="font-medium text-foreground">{person.place_of_birth || "—"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Preferred Language</span>
                    <p className="font-medium text-foreground">{person.preferred_language}</p>
                  </div>
                </div>

                <div className="border-t pt-3 space-y-2">
                  <span className="font-semibold text-muted-foreground uppercase text-[11px]">Indigenous & Civil Registrations</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-muted-foreground">Treaty / Status Card #</span>
                      <p className="font-mono text-foreground">{person.treaty_number || "—"}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Band / First Nation</span>
                      <p className="text-foreground">{person.band_nation || "—"}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Indigenous Identity</span>
                      <p className="text-foreground">{person.indigenous_identity || "—"}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">SK Health Card (HSN)</span>
                      <p className="font-mono text-foreground">{person.health_card_number || "—"}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Physical Characteristics */}
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Physical Identification & Distinguishing Features</CardTitle>
                <CardDescription className="text-xs">Safeguarding and physiological characteristics</CardDescription>
              </CardHeader>
              <CardContent className="text-xs space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-muted-foreground">Eye Colour</span>
                    <p className="font-medium text-foreground">{person.physical_description?.eye_colour || "Not Specified"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Hair Colour</span>
                    <p className="font-medium text-foreground">{person.physical_description?.hair_colour || "Not Specified"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Height</span>
                    <p className="font-medium text-foreground">
                      {person.physical_description?.height_cm ? `${person.physical_description.height_cm} cm` : "Not Specified"}
                    </p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Weight</span>
                    <p className="font-medium text-foreground">
                      {person.physical_description?.weight_kg ? `${person.physical_description.weight_kg} kg` : "Not Specified"}
                    </p>
                  </div>
                </div>

                <div className="border-t pt-3 space-y-2">
                  <div>
                    <span className="text-muted-foreground font-medium">Birthmarks & Locations:</span>
                    <p className="text-foreground mt-0.5">{person.physical_description?.birthmarks || "None recorded"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-medium">Scars & Surgical Marks:</span>
                    <p className="text-foreground mt-0.5">{person.physical_description?.scars || "None recorded"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-medium">Tattoos & Locations:</span>
                    <p className="text-foreground mt-0.5">{person.physical_description?.tattoos || "None recorded"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-medium">Piercings & Other Distinguishing Marks:</span>
                    <p className="text-foreground mt-0.5">{person.physical_description?.piercings || person.physical_description?.distinguishing_marks || "None recorded"}</p>
                  </div>
                  <div className="flex gap-4 pt-1 text-muted-foreground">
                    <span>Glasses: {person.physical_description?.glasses ? "Yes" : "No"}</span>
                    <span>Contact Lenses: {person.physical_description?.contact_lenses ? "Yes" : "No"}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── TAB 3: CONTACT & ADDRESS ─────────────────────────────────── */}
        <TabsContent value="contact_address" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Contact Information */}
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Primary & Emergency Contact</CardTitle>
              </CardHeader>
              <CardContent className="text-xs space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-muted-foreground">Primary Phone</span>
                    <p className="font-medium text-foreground">{person.phone || "None provided"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Email Address</span>
                    <p className="font-medium text-foreground">{person.email || "None provided"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Emergency Contact Name</span>
                    <p className="font-medium text-foreground">{person.emergency_contact_name || "None provided"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Emergency Contact Phone</span>
                    <p className="font-medium text-foreground">{person.emergency_contact_phone || "None provided"}</p>
                  </div>
                </div>

                {person.contacts?.length > 0 && (
                  <div className="border-t pt-3 space-y-2">
                    <span className="font-semibold text-muted-foreground uppercase text-[11px]">Alternate Contact Channels</span>
                    <div className="space-y-1.5">
                      {person.contacts.map((c) => (
                        <div key={c.id} className="flex justify-between items-center p-2 rounded bg-muted/30">
                          <span>{c.contact_type}: {c.value}</span>
                          <Badge variant="outline" className="text-[10px]">{c.label}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Address Ledger */}
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Residential & Historical Addresses</CardTitle>
              </CardHeader>
              <CardContent className="text-xs space-y-3">
                {person.addresses?.length === 0 ? (
                  <p className="text-muted-foreground">No physical addresses on record.</p>
                ) : (
                  person.addresses.map((addr) => (
                    <div key={addr.id} className="p-3 border rounded-lg space-y-1 bg-muted/20">
                      <div className="flex justify-between items-start">
                        <span className="font-medium text-foreground">{addr.address_line_1}</span>
                        {addr.is_primary && (
                          <Badge variant="secondary" className="text-[10px] bg-primary/10 text-primary">Primary</Badge>
                        )}
                      </div>
                      {addr.address_line_2 && <p className="text-muted-foreground">{addr.address_line_2}</p>}
                      <p className="text-muted-foreground">
                        {addr.city}, {addr.province} {addr.postal_code || ""}
                      </p>
                      {addr.on_reserve && (
                        <Badge variant="outline" className="text-[10px] mt-1 border-amber-600/30 text-amber-700 dark:text-amber-300">
                          On-Reserve
                        </Badge>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── TAB 4: FAMILY & KINSHIP ──────────────────────────────────── */}
        <TabsContent value="family" className="space-y-4">
          <Card className="border">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Interpersonal & Family Relationships</CardTitle>
              <CardDescription className="text-xs">Directional kinship ties connecting canonical Person records</CardDescription>
            </CardHeader>
            <CardContent>
              {profileData.relationships.length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">
                  No family relationships recorded for this person yet.
                </p>
              ) : (
                <div className="divide-y border rounded-xl overflow-hidden text-xs">
                  {profileData.relationships.map((rel) => (
                    <div key={rel.relationship_id} className="p-3 flex items-center justify-between hover:bg-muted/30">
                      <div>
                        <Link
                          to={`/people/${rel.target_person_id}`}
                          className="font-semibold text-foreground hover:text-primary hover:underline"
                        >
                          {rel.target_person_name}
                        </Link>
                        <span className="font-mono text-muted-foreground ml-2">ID: {rel.target_person_id_number || "—"}</span>
                        <div className="text-muted-foreground capitalize mt-0.5">
                          Type: {rel.relationship_type.replace(/_/g, " ")}
                        </div>
                      </div>
                      <Badge variant="outline" className="text-[10px]">
                        {rel.is_active ? "Active Link" : "Historical"}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── TAB 5: CASES & REFERRALS ─────────────────────────────────── */}
        <TabsContent value="cases_referrals" className="space-y-4">
          <div className="space-y-4">
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Case Involvements Roster</CardTitle>
              </CardHeader>
              <CardContent>
                {profileData.cases.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-4 text-center">
                    No active or closed cases recorded for this person.
                  </p>
                ) : (
                  <div className="divide-y border rounded-xl overflow-hidden text-xs">
                    {profileData.cases.map((c) => (
                      <div key={c.case_id} className="p-3 flex items-center justify-between hover:bg-muted/30">
                        <div>
                          <div className="flex items-center gap-2">
                            <Link to={`/cases/${c.case_id}`} className="font-semibold text-primary hover:underline">
                              {c.case_number}
                            </Link>
                            <span className="font-medium text-foreground">— {c.title}</span>
                          </div>
                          <div className="text-muted-foreground flex gap-3 mt-0.5">
                            <span className="capitalize">Role: {c.role_in_case?.replace(/_/g, " ")}</span>
                            {c.relationship_to_subject && <span>Relationship: {c.relationship_to_subject}</span>}
                            {c.start_date && <span>Start: {c.start_date}</span>}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {c.is_primary && (
                            <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                              Primary
                            </Badge>
                          )}
                          <Badge variant="outline">{c.stage}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Intake & Referral History</CardTitle>
              </CardHeader>
              <CardContent>
                {profileData.referrals.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-4 text-center">
                    No intake referrals associated with this person.
                  </p>
                ) : (
                  <div className="divide-y border rounded-xl overflow-hidden text-xs">
                    {profileData.referrals.map((r) => (
                      <div key={r.referral_id} className="p-3 flex items-center justify-between hover:bg-muted/30">
                        <div>
                          <Link to={`/intake/${r.referral_id}`} className="font-semibold text-primary hover:underline">
                            {r.referral_number}
                          </Link>
                          <div className="text-muted-foreground flex gap-3 mt-0.5">
                            <span className="capitalize">Role: {r.role}</span>
                            {r.received_date && <span>Received: {r.received_date}</span>}
                          </div>
                        </div>
                        <Badge variant="outline">{r.status}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── TAB 6: PLACEMENTS & EPISODES ─────────────────────────────── */}
        <TabsContent value="placements" className="space-y-4">
          <Card className="border">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Placement Episodes & Customary Care</CardTitle>
            </CardHeader>
            <CardContent>
              {profileData.placements.length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">
                  No out-of-home or in-home placements recorded for this individual.
                </p>
              ) : (
                <div className="divide-y border rounded-xl overflow-hidden text-xs">
                  {profileData.placements.map((p) => (
                    <div key={p.episode_id} className="p-3 flex items-center justify-between hover:bg-muted/30">
                      <div>
                        <div className="font-semibold text-foreground">{p.placement_type}</div>
                        <div className="text-muted-foreground">Provider: {p.provider_name}</div>
                        <div className="text-muted-foreground mt-0.5">
                          Dates: {p.start_date} to {p.end_date || "Present"}
                        </div>
                      </div>
                      <Badge variant="outline">{p.status}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── TAB 7: MEDICAL & HEALTH ──────────────────────────────────── */}
        <TabsContent value="medical" className="space-y-4">
          {profileData.medical ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Clinical Notes & General */}
              <Card className="border">
                <CardHeader>
                  <CardTitle className="text-sm font-semibold">Medical & Clinical Overview</CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <div>
                    <span className="text-muted-foreground">Primary Physician:</span>{" "}
                    <span className="font-medium text-foreground">
                      {profileData.medical.primary_physician_name || "None listed"}
                    </span>
                  </div>
                  {profileData.medical.primary_physician_phone && (
                    <div>
                      <span className="text-muted-foreground">Physician Phone:</span>{" "}
                      <span>{profileData.medical.primary_physician_phone}</span>
                    </div>
                  )}
                  {profileData.medical.dental_notes && (
                    <div className="border-t pt-2">
                      <span className="font-medium text-muted-foreground">Dental Notes:</span>
                      <p className="text-foreground mt-0.5">{profileData.medical.dental_notes}</p>
                    </div>
                  )}
                  {profileData.medical.mental_health_notes && (
                    <div className="border-t pt-2">
                      <span className="font-medium text-muted-foreground">Mental Health Notes:</span>
                      <p className="text-foreground mt-0.5">{profileData.medical.mental_health_notes}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Allergies & Medications */}
              <Card className="border">
                <CardHeader>
                  <CardTitle className="text-sm font-semibold">Allergies & Prescriptions</CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-3">
                  <div>
                    <span className="font-medium text-muted-foreground uppercase text-[11px]">Allergies</span>
                    {profileData.medical.allergies?.length === 0 ? (
                      <p className="text-muted-foreground mt-1">No allergies recorded.</p>
                    ) : (
                      <div className="space-y-1 mt-1">
                        {profileData.medical.allergies.map((a) => (
                          <div key={a.id} className="p-2 rounded bg-rose-500/10 flex justify-between items-center text-rose-950 dark:text-rose-200">
                            <span>{a.allergen}</span>
                            <Badge variant="outline" className="text-[10px]">{a.severity}</Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="border-t pt-2">
                    <span className="font-medium text-muted-foreground uppercase text-[11px]">Medications</span>
                    {profileData.medical.medications?.length === 0 ? (
                      <p className="text-muted-foreground mt-1">No active medications.</p>
                    ) : (
                      <div className="space-y-1 mt-1">
                        {profileData.medical.medications.map((m) => (
                          <div key={m.id} className="p-2 rounded bg-muted/40 flex justify-between items-center">
                            <span>{m.medication_name} ({m.dosage}, {m.frequency})</span>
                            <Badge variant="outline" className="text-[10px]">{m.status}</Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Alert className="border bg-muted/30">
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
              <AlertTitle className="text-sm font-medium">Medical Information Not Linked or Restricted</AlertTitle>
              <AlertDescription className="text-xs text-muted-foreground">
                Clinical medical profiles are attached when an individual receives service client care
                and require clinical medical reading authorization.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* ── TAB 8: DOCUMENTS & TIMELINE ──────────────────────────────── */}
        <TabsContent value="documents_timeline" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Permanent Documents */}
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Identity Documents</CardTitle>
                <CardDescription className="text-xs">Permanent files that remain with this person across all cases</CardDescription>
              </CardHeader>
              <CardContent className="text-xs">
                {profileData.documents.length === 0 ? (
                  <p className="text-muted-foreground py-4 text-center">No documents uploaded for this person.</p>
                ) : (
                  <div className="divide-y border rounded-xl overflow-hidden">
                    {profileData.documents.map((d) => (
                      <div key={d.id} className="p-3 flex items-center justify-between hover:bg-muted/30">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-primary" />
                          <div>
                            <p className="font-medium text-foreground">{d.filename}</p>
                            <span className="text-[11px] text-muted-foreground">{Math.round(d.size_bytes / 1024)} KB</span>
                          </div>
                        </div>
                        <a href={d.download_url} target="_blank" rel="noopener noreferrer">
                          <Button variant="ghost" size="sm" className="h-7 px-2">
                            <Download className="w-3.5 h-3.5" />
                          </Button>
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Sacred Timeline Events */}
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Sacred Timeline Events</CardTitle>
                <CardDescription className="text-xs">Milestones and recorded occurrences</CardDescription>
              </CardHeader>
              <CardContent className="text-xs">
                {profileData.timeline.length === 0 ? (
                  <p className="text-muted-foreground py-4 text-center">No timeline events recorded.</p>
                ) : (
                  <div className="space-y-3">
                    {profileData.timeline.map((t) => (
                      <div key={t.id} className="border-l-2 border-primary/40 pl-3 py-1 space-y-0.5">
                        <span className="font-semibold text-foreground">{t.title}</span>
                        <p className="text-muted-foreground">{t.description}</p>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(t.occurred_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* ── Edit Person Dialog ─────────────────────────────────────────── */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Person Details</DialogTitle>
          </DialogHeader>
          {editForm && (
            <form onSubmit={handleSaveEdit} className="space-y-4 py-2">
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">First Name *</Label>
                  <Input
                    required
                    value={editForm.first_name}
                    onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Middle Name</Label>
                  <Input
                    value={editForm.middle_name}
                    onChange={(e) => setEditForm({ ...editForm, middle_name: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Last Name *</Label>
                  <Input
                    required
                    value={editForm.last_name}
                    onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">Preferred Name</Label>
                  <Input
                    value={editForm.preferred_name}
                    onChange={(e) => setEditForm({ ...editForm, preferred_name: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Date of Birth</Label>
                  <Input
                    type="date"
                    value={editForm.date_of_birth}
                    onChange={(e) => setEditForm({ ...editForm, date_of_birth: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">Treaty Number</Label>
                  <Input
                    value={editForm.treaty_number}
                    onChange={(e) => setEditForm({ ...editForm, treaty_number: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Health Card (HSN)</Label>
                  <Input
                    value={editForm.health_card_number}
                    onChange={(e) => setEditForm({ ...editForm, health_card_number: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">Phone</Label>
                  <Input
                    value={editForm.phone}
                    onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Email</Label>
                  <Input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  />
                </div>
              </div>

              <div className="border-t pt-3">
                <h4 className="text-xs font-semibold mb-2">Physical Description</h4>
                <div className="grid grid-cols-4 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs">Eye Colour</Label>
                    <Input
                      value={editForm.physical_description.eye_colour}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, eye_colour: e.target.value },
                        })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Hair Colour</Label>
                    <Input
                      value={editForm.physical_description.hair_colour}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, hair_colour: e.target.value },
                        })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Height (cm)</Label>
                    <Input
                      type="number"
                      value={editForm.physical_description.height_cm}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, height_cm: e.target.value },
                        })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Weight (kg)</Label>
                    <Input
                      type="number"
                      value={editForm.physical_description.weight_kg}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, weight_kg: e.target.value },
                        })
                      }
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 mt-2">
                  <div className="space-y-1">
                    <Label className="text-xs">Tattoos & Body Art</Label>
                    <Textarea
                      rows={2}
                      value={editForm.physical_description.tattoos}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, tattoos: e.target.value },
                        })
                      }
                      placeholder="Descriptions and locations"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Scars</Label>
                    <Textarea
                      rows={2}
                      value={editForm.physical_description.scars}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, scars: e.target.value },
                        })
                      }
                      placeholder="Surgical or accidental scars"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 mt-2">
                  <div className="space-y-1">
                    <Label className="text-xs">Birthmarks</Label>
                    <Textarea
                      rows={2}
                      value={editForm.physical_description.birthmarks}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, birthmarks: e.target.value },
                        })
                      }
                      placeholder="Birthmarks and locations"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Piercings</Label>
                    <Textarea
                      rows={2}
                      value={editForm.physical_description.piercings}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, piercings: e.target.value },
                        })
                      }
                      placeholder="Pierced ears, nose, etc."
                    />
                  </div>
                </div>

                <div className="space-y-1 mt-2">
                  <Label className="text-xs">Distinguishing Marks / Observable Features</Label>
                  <Textarea
                    rows={2}
                    value={editForm.physical_description.distinguishing_marks}
                    onChange={(e) =>
                      setEditForm({
                        ...editForm,
                        physical_description: { ...editForm.physical_description, distinguishing_marks: e.target.value },
                      })
                    }
                    placeholder="Dental braces, distinctive gait, unique features"
                  />
                </div>

                <div className="flex gap-6 mt-3">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="edit-glasses"
                      checked={editForm.physical_description.glasses}
                      onCheckedChange={(c) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, glasses: !!c },
                        })
                      }
                    />
                    <Label htmlFor="edit-glasses" className="text-xs cursor-pointer">Wears Glasses</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="edit-contacts"
                      checked={editForm.physical_description.contact_lenses}
                      onCheckedChange={(c) =>
                        setEditForm({
                          ...editForm,
                          physical_description: { ...editForm.physical_description, contact_lenses: !!c },
                        })
                      }
                    />
                    <Label htmlFor="edit-contacts" className="text-xs cursor-pointer">Wears Contact Lenses</Label>
                  </div>
                </div>
              </div>

              <DialogFooter className="gap-2 sm:gap-0">
                <Button type="button" variant="outline" onClick={() => setShowEditModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
                  Save Changes
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

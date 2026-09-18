import React from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function ComprehensivePersonForm({
  formData,
  setFormData,
  photoFile,
  setPhotoFile,
  photoPreview,
  setPhotoPreview,
  showClientFields = false,
  clientFields = {},
  setClientFields = () => {},
  teams = [],
}) {
  const updateForm = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const updateNestedForm = (parent, field, value) => {
    setFormData((prev) => {
      const next = {
        ...prev,
        [parent]: {
          ...(prev[parent] || {}),
          [field]: value,
        },
      };
      if (parent === "physical_description" || parent === "physical") {
        next.physical_description = { ...(prev.physical_description || {}), [field]: value };
        next.physical = { ...(prev.physical || {}), [field]: value };
      }
      if (parent === "primary_address" || parent === "address") {
        next.primary_address = { ...(prev.primary_address || {}), [field]: value };
        next.address = { ...(prev.address || {}), [field]: value };
      }
      if (parent === "cultural_profile" || parent === "cultural") {
        next.cultural_profile = { ...(prev.cultural_profile || {}), [field]: value };
        next.cultural = { ...(prev.cultural || {}), [field]: value };
      }
      return next;
    });
  };

  const updateClientField = (field, value) => {
    setClientFields((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-4">
      {showClientFields && (
        <div className="p-4 rounded-xl border bg-primary/5 border-primary/20 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-primary">
              Client Proposal Context
            </h4>
            <span className="text-[11px] bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 px-2 py-0.5 rounded-full font-medium">
              Awaiting Supervisor Review Upon Submit
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Initial Risk Level *</Label>
              <select
                className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                value={clientFields.risk_level || "Low"}
                onChange={(e) => updateClientField("risk_level", e.target.value)}
              >
                <option value="Low">Low Risk</option>
                <option value="Medium">Medium Risk</option>
                <option value="High">High Risk</option>
              </select>
            </div>

            <div className="space-y-1">
              <Label className="text-xs font-medium">Assigned Team (Optional)</Label>
              <select
                className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                value={clientFields.assigned_team_id || ""}
                onChange={(e) => updateClientField("assigned_team_id", e.target.value || null)}
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

          <div className="space-y-1">
            <Label className="text-xs font-medium">Submission Rationale / Intake Notes</Label>
            <Textarea
              placeholder="Provide background, immediate safety or stabilization needs, or rationale for proposing this client..."
              rows={2}
              value={clientFields.submission_notes || ""}
              onChange={(e) => updateClientField("submission_notes", e.target.value)}
            />
          </div>
        </div>
      )}

      <Tabs defaultValue="identity" className="w-full">
        <TabsList className="grid grid-cols-4 w-full">
          <TabsTrigger value="identity" className="text-xs">1. Identity</TabsTrigger>
          <TabsTrigger value="physical" className="text-xs">2. Physical ID</TabsTrigger>
          <TabsTrigger value="contact" className="text-xs">3. Contact & Address</TabsTrigger>
          <TabsTrigger value="cultural" className="text-xs">4. Cultural</TabsTrigger>
        </TabsList>

        {/* ── TAB 1: IDENTITY ─────────────────────────────────── */}
        <TabsContent value="identity" className="space-y-4 pt-3">
          <div className="flex items-center gap-4 p-3 border rounded-lg bg-muted/20">
            <Avatar className="h-14 w-14 border shadow-sm">
              <AvatarImage src={photoPreview} />
              <AvatarFallback className="text-sm font-semibold bg-primary/10 text-primary">
                {formData.first_name?.[0] || ""}{formData.last_name?.[0] || "?"}
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
                      alert("Only image files (JPEG, PNG, WebP) are allowed");
                      return;
                    }
                    if (setPhotoFile) setPhotoFile(file);
                    if (setPhotoPreview) setPhotoPreview(URL.createObjectURL(file));
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
                value={formData.first_name || ""}
                onChange={(e) => updateForm("first_name", e.target.value)}
                placeholder="First name"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Middle Name(s)</Label>
              <Input
                value={formData.middle_name || ""}
                onChange={(e) => updateForm("middle_name", e.target.value)}
                placeholder="Middle name"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Legal Last Name *</Label>
              <Input
                required
                value={formData.last_name || ""}
                onChange={(e) => updateForm("last_name", e.target.value)}
                placeholder="Last name"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Preferred / Chosen Name</Label>
              <Input
                value={formData.preferred_name || ""}
                onChange={(e) => updateForm("preferred_name", e.target.value)}
                placeholder="Preferred name"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Aliases / Previous Names</Label>
              <Input
                value={formData.aliases || ""}
                onChange={(e) => updateForm("aliases", e.target.value)}
                placeholder="Comma-separated"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Date of Birth</Label>
              <Input
                type="date"
                value={formData.date_of_birth || ""}
                onChange={(e) => updateForm("date_of_birth", e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Gender</Label>
              <select
                className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                value={formData.gender || ""}
                onChange={(e) => updateForm("gender", e.target.value)}
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
                value={formData.place_of_birth || ""}
                onChange={(e) => updateForm("place_of_birth", e.target.value)}
                placeholder="e.g. Regina, SK"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Preferred Language</Label>
              <Input
                value={formData.preferred_language || ""}
                onChange={(e) => updateForm("preferred_language", e.target.value)}
                placeholder="e.g. English, Cree, Saulteaux"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Treaty / Status Card #</Label>
              <Input
                value={formData.treaty_number || ""}
                onChange={(e) => updateForm("treaty_number", e.target.value)}
                placeholder="10-digit registration #"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Band / First Nation</Label>
              <Input
                value={formData.band_nation || ""}
                onChange={(e) => updateForm("band_nation", e.target.value)}
                placeholder="e.g. Zagime Anishinabek"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">SK Health Card (HSN)</Label>
              <Input
                value={formData.health_card_number || ""}
                onChange={(e) => updateForm("health_card_number", e.target.value)}
                placeholder="9-digit HSN"
              />
            </div>
          </div>
        </TabsContent>

        {/* ── TAB 2: PHYSICAL IDENTIFICATION ──────────────────── */}
        <TabsContent value="physical" className="space-y-4 pt-3">
          <p className="text-xs text-muted-foreground">
            Observable physical identifiers to assist staff in rapid and accurate client identification.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Eye Colour</Label>
              <Input
                value={formData.physical_description?.eye_colour ?? formData.physical?.eye_colour ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "eye_colour", e.target.value)}
                placeholder="e.g. Brown"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Hair Colour</Label>
              <Input
                value={formData.physical_description?.hair_colour ?? formData.physical?.hair_colour ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "hair_colour", e.target.value)}
                placeholder="e.g. Black"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Height (cm)</Label>
              <Input
                type="number"
                step="0.1"
                value={formData.physical_description?.height_cm ?? formData.physical?.height_cm ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "height_cm", e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="e.g. 165"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Weight (kg)</Label>
              <Input
                type="number"
                step="0.1"
                value={formData.physical_description?.weight_kg ?? formData.physical?.weight_kg ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "weight_kg", e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="e.g. 60"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Tattoos & Body Art</Label>
              <Input
                value={formData.physical_description?.tattoos ?? formData.physical?.tattoos ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "tattoos", e.target.value)}
                placeholder="Describe locations & designs"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Piercings</Label>
              <Input
                value={formData.physical_description?.piercings ?? formData.physical?.piercings ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "piercings", e.target.value)}
                placeholder="Describe locations"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Birthmarks</Label>
              <Input
                value={formData.physical_description?.birthmarks ?? formData.physical?.birthmarks ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "birthmarks", e.target.value)}
                placeholder="Locations and descriptions of birthmarks"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Scars & Surgical Marks</Label>
              <Input
                value={formData.physical_description?.scars ?? formData.physical?.scars ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "scars", e.target.value)}
                placeholder="Locations and descriptions of visible marks"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Other Distinguishing Marks</Label>
              <Input
                value={formData.physical_description?.distinguishing_marks ?? formData.physical?.distinguishing_marks ?? ""}
                onChange={(e) => updateNestedForm("physical_description", "distinguishing_marks", e.target.value)}
                placeholder="Notable features or assistive devices"
              />
            </div>
          </div>

          <div className="flex gap-6 pt-1">
            <div className="flex items-center gap-2">
              <Checkbox
                id="glasses"
                checked={!!(formData.physical_description?.glasses ?? formData.physical?.glasses)}
                onCheckedChange={(checked) => updateNestedForm("physical_description", "glasses", !!checked)}
              />
              <Label htmlFor="glasses" className="text-xs font-medium cursor-pointer">Wears Glasses</Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="contact_lenses"
                checked={!!(formData.physical_description?.contact_lenses ?? formData.physical?.contact_lenses)}
                onCheckedChange={(checked) => updateNestedForm("physical_description", "contact_lenses", !!checked)}
              />
              <Label htmlFor="contact_lenses" className="text-xs font-medium cursor-pointer">Wears Contacts</Label>
            </div>
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-medium">Physical Identifying Notes</Label>
            <Textarea
              rows={2}
              value={formData.physical_description?.notes ?? formData.physical?.notes ?? ""}
              onChange={(e) => updateNestedForm("physical_description", "notes", e.target.value)}
              placeholder="Additional appearance details or physical identifying notes..."
            />
          </div>
        </TabsContent>


        {/* ── TAB 3: CONTACT & ADDRESS ────────────────────────── */}
        <TabsContent value="contact" className="space-y-4 pt-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Primary Phone</Label>
              <Input
                type="tel"
                value={formData.phone || ""}
                onChange={(e) => updateForm("phone", e.target.value)}
                placeholder="306-555-0100"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Email Address</Label>
              <Input
                type="email"
                value={formData.email || ""}
                onChange={(e) => updateForm("email", e.target.value)}
                placeholder="client@example.ca"
              />
            </div>
          </div>

          <div className="border rounded-lg p-3 space-y-3 bg-muted/10">
            <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Emergency Contact
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs font-medium">Name</Label>
                <Input
                  value={formData.emergency_contact_name || ""}
                  onChange={(e) => updateForm("emergency_contact_name", e.target.value)}
                  placeholder="Full name"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-medium">Phone</Label>
                <Input
                  type="tel"
                  value={formData.emergency_contact_phone || ""}
                  onChange={(e) => updateForm("emergency_contact_phone", e.target.value)}
                  placeholder="Phone number"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-medium">Relationship</Label>
                <Input
                  value={formData.emergency_contact_relationship || ""}
                  onChange={(e) => updateForm("emergency_contact_relationship", e.target.value)}
                  placeholder="e.g. Grandmother, Aunt"
                />
              </div>
            </div>
          </div>

          <div className="border rounded-lg p-3 space-y-3 bg-muted/10">
            <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Primary Residential Address
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1 sm:col-span-2">
                <Label className="text-xs font-medium">Street Address</Label>
                <Input
                  value={formData.primary_address?.address_line_1 ?? formData.address?.address_line_1 ?? ""}
                  onChange={(e) => updateNestedForm("primary_address", "address_line_1", e.target.value)}
                  placeholder="123 5th Ave"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-medium">City</Label>
                <Input
                  value={formData.primary_address?.city ?? formData.address?.city ?? "Regina"}
                  onChange={(e) => updateNestedForm("primary_address", "city", e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-medium">Province</Label>
                <Input
                  value={formData.primary_address?.province ?? formData.address?.province ?? "Saskatchewan"}
                  onChange={(e) => updateNestedForm("primary_address", "province", e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-medium">Postal Code</Label>
                <Input
                  value={formData.primary_address?.postal_code ?? formData.address?.postal_code ?? ""}
                  onChange={(e) => updateNestedForm("primary_address", "postal_code", e.target.value)}
                  placeholder="S4P 3Y2"
                />
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  id="on_reserve"
                  checked={!!(formData.primary_address?.on_reserve ?? formData.address?.on_reserve)}
                  onCheckedChange={(checked) => updateNestedForm("primary_address", "on_reserve", !!checked)}
                />
                <Label htmlFor="on_reserve" className="text-xs font-medium cursor-pointer">
                  Located On-Reserve
                </Label>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ── TAB 4: CULTURAL & BACKGROUND ────────────────────── */}
        <TabsContent value="cultural" className="space-y-4 pt-3">
          <p className="text-xs text-muted-foreground">
            Cultural identity, customary connections, and socioeconomic context honoring Indigenous family heritage.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Cultural & Community Connections</Label>
              <Textarea
                rows={2}
                value={formData.cultural_profile?.cultural_connections ?? formData.cultural?.cultural_connections ?? ""}
                onChange={(e) => updateNestedForm("cultural_profile", "cultural_connections", e.target.value)}
                placeholder="Band affiliations, clan, or urban Indigenous community ties..."
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Ceremonies & Customary Practices</Label>
              <Textarea
                rows={2}
                value={formData.cultural_profile?.ceremonies ?? formData.cultural?.ceremonies ?? ""}
                onChange={(e) => updateNestedForm("cultural_profile", "ceremonies", e.target.value)}
                placeholder="Round dances, sweats, smudging, seasonal gatherings..."
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Elders / Knowledge Keepers Connected With</Label>
              <Input
                value={formData.cultural_profile?.elders_connected ?? formData.cultural?.elders_connected ?? ""}
                onChange={(e) => updateNestedForm("cultural_profile", "elders_connected", e.target.value)}
                placeholder="Names or communities of connected Elders"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Land-Based Activities</Label>
              <Input
                value={formData.cultural_profile?.land_based_activities ?? formData.cultural?.land_based_activities ?? ""}
                onChange={(e) => updateNestedForm("cultural_profile", "land_based_activities", e.target.value)}
                placeholder="Hunting, fishing, medicine picking, trapping"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-medium">Dietary Needs & Preferences</Label>
              <Input
                value={formData.cultural_profile?.dietary_preferences ?? formData.cultural?.dietary_preferences ?? ""}
                onChange={(e) => updateNestedForm("cultural_profile", "dietary_preferences", e.target.value)}
                placeholder="Traditional foods, allergies, cultural preferences"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-medium">Extracurricular Activities & Interests</Label>
              <Input
                value={formData.cultural_profile?.extracurricular_activities ?? formData.cultural?.extracurricular_activities ?? ""}
                onChange={(e) => updateNestedForm("cultural_profile", "extracurricular_activities", e.target.value)}
                placeholder="Sports, arts, music, powwow dancing"
              />
            </div>
          </div>

          <div className="border-t pt-3 space-y-3">
            <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Socioeconomic Background
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs font-medium">Employment Status</Label>
                <select
                  className="w-full h-9 px-3 rounded-md border text-sm bg-background"
                  value={formData.employment_status || ""}
                  onChange={(e) => updateForm("employment_status", e.target.value)}
                >
                  <option value="">-- Select Status --</option>
                  <option value="Employed Full-Time">Employed Full-Time</option>
                  <option value="Employed Part-Time">Employed Part-Time</option>
                  <option value="Self-Employed">Self-Employed</option>
                  <option value="Unemployed / Seeking">Unemployed / Seeking</option>
                  <option value="Student">Student</option>
                  <option value="Retired">Retired</option>
                  <option value="Unable to Work">Unable to Work</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-medium">Employer / School</Label>
                <Input
                  value={formData.employer || ""}
                  onChange={(e) => updateForm("employer", e.target.value)}
                  placeholder="Organization name"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-medium">Source of Income</Label>
                <Input
                  value={formData.source_of_income || ""}
                  onChange={(e) => updateForm("source_of_income", e.target.value)}
                  placeholder="e.g. Employment, SIS, SAID, EI"
                />
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

import React, { useState, useEffect, useRef } from "react";
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useToast } from "@/components/ui/use-toast";
import { clientsApi, teamsApi, personsApi } from "@/api";
import { Loader2, Save, User, MapPin, ShieldAlert, Phone, Camera, Upload, X } from "lucide-react";

export default function EditClientModal({ isOpen, onClose, client, onSuccess }) {
  const { toast } = useToast();

  const [loading, setLoading] = useState(false);
  const [teams, setTeams] = useState([]);
  const fileInputRef = useRef(null);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "",
    gender: "",
    status: "Active",
    risk_level: "Low",
    assigned_team_id: "",
    phone: "",
    email: "",
    address: "",
    city: "Regina",
    province: "Saskatchewan",
    indigenous_identity: "First Nations",
    band_nation: "",
    notes: "",
  });

  useEffect(() => {
    if (client) {
      setFormData({
        first_name: client.first_name || "",
        last_name: client.last_name || "",
        date_of_birth: client.date_of_birth ? String(client.date_of_birth).substring(0, 10) : "",
        gender: client.gender || "",
        status: client.status || "Active",
        risk_level: client.risk_level || "Low",
        assigned_team_id: client.assigned_team_id || "",
        phone: client.phone || "",
        email: client.email || "",
        address: client.address || "",
        city: client.city || "Regina",
        province: client.province || "Saskatchewan",
        indigenous_identity: client.indigenous_identity || "First Nations",
        band_nation: client.band_nation || "",
        notes: client.notes || "",
      });
      setPhotoPreview(client.photo_url || client.person?.photo_url || null);
      setPhotoFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }, [client]);

  useEffect(() => {
    if (isOpen) {
      teamsApi.list?.().then((res) => {
        setTeams(Array.isArray(res) ? res : res?.items || []);
      }).catch(() => setTeams([]));
    }
  }, [isOpen]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast({
        title: "Invalid file type",
        description: "Please select an image file (JPEG, PNG, WebP).",
        variant: "destructive",
      });
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Image size must be under 10MB.",
        variant: "destructive",
      });
      return;
    }

    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  };

  const handleRemovePhoto = () => {
    setPhotoFile(null);
    setPhotoPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!client?.id) return;

    if (!formData.first_name.trim() || !formData.last_name.trim()) {
      toast({
        title: "Validation Error",
        description: "First name and last name are required.",
        variant: "destructive",
      });
      return;
    }

    try {
      setLoading(true);
      const payload = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        date_of_birth: formData.date_of_birth || null,
        gender: formData.gender || null,
        status: formData.status || "Active",
        risk_level: formData.risk_level || "Low",
        assigned_team_id: formData.assigned_team_id || null,
        phone: formData.phone.trim() || null,
        email: formData.email.trim() || null,
        address: formData.address.trim() || null,
        city: formData.city.trim() || "Regina",
        province: formData.province.trim() || "Saskatchewan",
        indigenous_identity: formData.indigenous_identity || null,
        band_nation: formData.band_nation.trim() || null,
        notes: formData.notes.trim() || null,
      };

      const updated = await clientsApi.update(client.id, payload);

      if (photoFile) {
        try {
          await clientsApi.uploadPhoto(client.id, photoFile);
        } catch (photoErr) {
          console.warn("Client photo upload fallback to person:", photoErr);
          if (client.person_id) {
            await personsApi.uploadPhoto(client.person_id, photoFile);
          } else {
            throw photoErr;
          }
        }
      }

      toast({
        title: "Client Profile Updated",
        description: photoFile
          ? `Successfully saved changes and new photo for ${formData.first_name} ${formData.last_name}.`
          : `Successfully saved changes for ${formData.first_name} ${formData.last_name}.`,
      });

      if (onSuccess) {
        onSuccess(updated);
      }
      onClose();
    } catch (err) {
      console.error("Failed to update client:", err);
      toast({
        title: "Update Failed",
        description: err?.message || err?.detail?.error?.message || "Failed to save client changes.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !client) return null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg font-bold flex items-center gap-2">
            <User className="w-5 h-5 text-primary" />
            Edit Client Profile: {client.first_name} {client.last_name}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 pt-2">
          {/* Profile Photo Section */}
          <div className="flex flex-col sm:flex-row items-center gap-4 p-3.5 bg-muted/30 border border-border/80 rounded-xl">
            <div className="relative group shrink-0">
              <Avatar className="h-18 w-18 sm:h-20 sm:w-20 rounded-2xl border-2 border-primary/20 shadow-xs overflow-hidden">
                <AvatarImage src={photoPreview} alt={`${formData.first_name} ${formData.last_name}`} className="object-cover" />
                <AvatarFallback className="rounded-2xl text-lg font-bold bg-gradient-to-br from-primary/20 via-primary/10 to-primary/5 text-primary">
                  {formData.first_name?.[0] || ""}{formData.last_name?.[0] || ""}
                </AvatarFallback>
              </Avatar>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="absolute -bottom-1 -right-1 p-1.5 rounded-full bg-primary text-primary-foreground shadow hover:bg-primary/90 transition-transform active:scale-95"
                title="Change Photo"
              >
                <Camera className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex-1 space-y-1.5 text-center sm:text-left">
              <div className="flex items-center justify-center sm:justify-start gap-2">
                <Label className="text-xs font-semibold text-foreground">Client Profile Photo</Label>
                {photoFile && (
                  <Badge variant="outline" className="text-[10px] text-emerald-600 dark:text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                    New photo selected
                  </Badge>
                )}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Upload a clear portrait photo (JPEG, PNG, or WebP). Displayed on client profile cards, directories, and service files.
              </p>
              <div className="flex items-center justify-center sm:justify-start gap-2 pt-0.5">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handlePhotoChange}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="h-8 px-2.5 text-xs gap-1.5"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>{photoPreview ? "Change Photo" : "Upload Photo"}</span>
                </Button>

                {photoPreview && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleRemovePhoto}
                    className="h-8 px-2 text-xs text-muted-foreground hover:text-destructive gap-1"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Remove</span>
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Identity & Demographics */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5 border-b border-border/60 pb-1">
              <User className="w-3.5 h-3.5" /> Identity &amp; Demographics
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <Label htmlFor="first_name" className="text-xs font-semibold">
                  First Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) => handleChange("first_name", e.target.value)}
                  className="mt-1 h-9 text-xs"
                  required
                />
              </div>

              <div>
                <Label htmlFor="last_name" className="text-xs font-semibold">
                  Last Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => handleChange("last_name", e.target.value)}
                  className="mt-1 h-9 text-xs"
                  required
                />
              </div>

              <div>
                <Label htmlFor="date_of_birth" className="text-xs font-semibold">
                  Date of Birth
                </Label>
                <Input
                  id="date_of_birth"
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => handleChange("date_of_birth", e.target.value)}
                  className="mt-1 h-9 text-xs"
                />
              </div>

              <div>
                <Label htmlFor="gender" className="text-xs font-semibold">
                  Gender Identity
                </Label>
                <select
                  id="gender"
                  value={formData.gender}
                  onChange={(e) => handleChange("gender", e.target.value)}
                  className="mt-1 w-full h-9 rounded-md border border-input bg-background px-3 text-xs focus:ring-1 focus:ring-primary"
                >
                  <option value="">Select Gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Two-Spirit">Two-Spirit</option>
                  <option value="Non-Binary">Non-Binary</option>
                  <option value="Other">Other</option>
                  <option value="Undisclosed">Undisclosed</option>
                </select>
              </div>

              <div>
                <Label htmlFor="indigenous_identity" className="text-xs font-semibold">
                  Indigenous Identity
                </Label>
                <select
                  id="indigenous_identity"
                  value={formData.indigenous_identity}
                  onChange={(e) => handleChange("indigenous_identity", e.target.value)}
                  className="mt-1 w-full h-9 rounded-md border border-input bg-background px-3 text-xs focus:ring-1 focus:ring-primary"
                >
                  <option value="First Nations">First Nations</option>
                  <option value="Métis">Métis</option>
                  <option value="Inuit">Inuit</option>
                  <option value="Non-Indigenous">Non-Indigenous</option>
                  <option value="Other">Other</option>
                  <option value="Prefer not to say">Prefer not to say</option>
                </select>
              </div>

              <div>
                <Label htmlFor="band_nation" className="text-xs font-semibold">
                  Band / Nation
                </Label>
                <Input
                  id="band_nation"
                  value={formData.band_nation}
                  onChange={(e) => handleChange("band_nation", e.target.value)}
                  placeholder="e.g., Muscowpetung Saulteaux Nation"
                  className="mt-1 h-9 text-xs"
                />
              </div>
            </div>
          </div>

          {/* Operational Status & Risk */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5 border-b border-border/60 pb-1">
              <ShieldAlert className="w-3.5 h-3.5" /> Operational Status &amp; Assignment
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <Label htmlFor="status" className="text-xs font-semibold">
                  Client Status
                </Label>
                <select
                  id="status"
                  value={formData.status}
                  onChange={(e) => handleChange("status", e.target.value)}
                  className="mt-1 w-full h-9 rounded-md border border-input bg-background px-3 text-xs focus:ring-1 focus:ring-primary"
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                  <option value="Pending Intake">Pending Intake</option>
                  <option value="Closed">Closed</option>
                  <option value="Transferred">Transferred</option>
                </select>
              </div>

              <div>
                <Label htmlFor="risk_level" className="text-xs font-semibold">
                  Risk Level
                </Label>
                <select
                  id="risk_level"
                  value={formData.risk_level}
                  onChange={(e) => handleChange("risk_level", e.target.value)}
                  className="mt-1 w-full h-9 rounded-md border border-input bg-background px-3 text-xs focus:ring-1 focus:ring-primary"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>

              <div>
                <Label htmlFor="assigned_team_id" className="text-xs font-semibold">
                  Assigned Team / Unit
                </Label>
                <select
                  id="assigned_team_id"
                  value={formData.assigned_team_id}
                  onChange={(e) => handleChange("assigned_team_id", e.target.value)}
                  className="mt-1 w-full h-9 rounded-md border border-input bg-background px-3 text-xs focus:ring-1 focus:ring-primary"
                >
                  <option value="">No Team Assigned</option>
                  {teams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Contact & Location */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5 border-b border-border/60 pb-1">
              <Phone className="w-3.5 h-3.5" /> Contact &amp; Location
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <Label htmlFor="phone" className="text-xs font-semibold">
                  Phone Number
                </Label>
                <Input
                  id="phone"
                  value={formData.phone}
                  onChange={(e) => handleChange("phone", e.target.value)}
                  placeholder="e.g., 306-555-0199"
                  className="mt-1 h-9 text-xs"
                />
              </div>

              <div>
                <Label htmlFor="email" className="text-xs font-semibold">
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange("email", e.target.value)}
                  placeholder="e.g., client@example.com"
                  className="mt-1 h-9 text-xs"
                />
              </div>

              <div className="sm:col-span-2">
                <Label htmlFor="address" className="text-xs font-semibold">
                  Primary Street Address
                </Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => handleChange("address", e.target.value)}
                  placeholder="e.g., 1234 Dewdney Ave"
                  className="mt-1 h-9 text-xs"
                />
              </div>

              <div>
                <Label htmlFor="city" className="text-xs font-semibold">
                  City
                </Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => handleChange("city", e.target.value)}
                  className="mt-1 h-9 text-xs"
                />
              </div>

              <div>
                <Label htmlFor="province" className="text-xs font-semibold">
                  Province
                </Label>
                <Input
                  id="province"
                  value={formData.province}
                  onChange={(e) => handleChange("province", e.target.value)}
                  className="mt-1 h-9 text-xs"
                />
              </div>
            </div>
          </div>

          {/* Clinical & Service Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes" className="text-xs font-semibold">
              Case Context &amp; Clinical Notes
            </Label>
            <Textarea
              id="notes"
              value={formData.notes}
              onChange={(e) => handleChange("notes", e.target.value)}
              rows={3}
              placeholder="Record any general caseworker notes, service goals, or intake observations..."
              className="text-xs resize-none"
            />
          </div>

          <DialogFooter className="pt-2 border-t border-border/60 gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={loading} className="gap-1.5 shadow-sm">
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Saving Changes...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" /> Save Profile Changes
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

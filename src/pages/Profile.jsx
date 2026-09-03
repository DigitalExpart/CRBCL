import React, { useState, useEffect, useRef } from "react";
import { api } from "@/api";
import PageHeader from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "@/components/ui/use-toast";
import {
  User,
  Lock,
  Camera,
  Shield,
  Phone,
  Mail,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Loader2,
  Users,
  Calendar,
  Sparkles,
  Trash2,
} from "lucide-react";

export default function Profile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Profile fields state
  const [fullName, setFullName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  // Password fields state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState("");

  const fileInputRef = useRef(null);

  const loadUserData = async () => {
    try {
      setLoading(true);
      const data = await api.auth.me();
      if (data) {
        setUser(data);
        setFullName(data.full_name || "");
        setDisplayName(data.display_name || "");
        setPhone(data.phone || "");
        setAvatarUrl(data.avatar_url || "");
      }
    } catch (err) {
      console.warn("Failed to load user profile:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUserData();
  }, []);

  const getInitials = (name, email) => {
    if (name && name.trim()) {
      const parts = name.trim().split(/\s+/);
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      }
      return parts[0].substring(0, 2).toUpperCase();
    }
    if (email && email.includes("@")) {
      return email.substring(0, 2).toUpperCase();
    }
    return "CB";
  };

  // Handle saving profile changes
  const handleSaveProfile = async (e) => {
    e?.preventDefault();
    if (!fullName.trim()) {
      toast({
        title: "Name required",
        description: "Please enter your full name.",
        variant: "destructive",
      });
      return;
    }

    setSavingProfile(true);
    try {
      const updated = await api.auth.updateProfile({
        full_name: fullName.trim(),
        display_name: displayName.trim() || null,
        phone: phone.trim() || null,
        avatar_url: avatarUrl || null,
      });

      setUser(updated);
      // Dispatch custom event to notify UserNav and other components immediately
      window.dispatchEvent(new Event("crbcl_profile_updated"));

      toast({
        title: "Profile Updated",
        description: "Your profile information has been saved successfully.",
      });
    } catch (err) {
      toast({
        title: "Update Failed",
        description: err.message || "Failed to update profile.",
        variant: "destructive",
      });
    } finally {
      setSavingProfile(false);
    }
  };

  // Handle avatar photo selection and conversion
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast({
        title: "Invalid file type",
        description: "Please select an image file (PNG, JPG, WebP).",
        variant: "destructive",
      });
      return;
    }

    if (file.size > 4 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please upload an image smaller than 4MB.",
        variant: "destructive",
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64Data = event.target?.result;
      if (base64Data && typeof base64Data === "string") {
        setAvatarUrl(base64Data);
      }
    };
    reader.readAsDataURL(file);
  };

  // Handle removing profile photo
  const handleRemovePhoto = () => {
    setAvatarUrl("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Handle password change
  const handleChangePassword = async (e) => {
    e?.preventDefault();
    setPasswordError("");

    if (!currentPassword) {
      setPasswordError("Please enter your current password.");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirm password do not match.");
      return;
    }

    setSavingPassword(true);
    try {
      await api.auth.changePassword({
        currentPassword,
        newPassword,
      });

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      toast({
        title: "Password Changed",
        description: "Your password has been updated. Please remember your new password.",
      });
    } catch (err) {
      setPasswordError(err.message || "Failed to change password. Please verify current password.");
      toast({
        title: "Password Change Failed",
        description: err.message || "Current password incorrect.",
        variant: "destructive",
      });
    } finally {
      setSavingPassword(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
        <p className="text-sm text-muted-foreground">Loading your profile...</p>
      </div>
    );
  }

  const initials = getInitials(fullName || user?.full_name, user?.email);
  const roles = Array.isArray(user?.roles) ? user.roles : (user?.role ? [user.role] : []);
  const teamAccess = Array.isArray(user?.team_access) ? user.team_access : [];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <PageHeader
        title="My Profile & Settings"
        subtitle="Manage your personal details, secure login credentials, and account permissions"
      />

      {/* Hero Profile Overview Card */}
      <Card className="border shadow-sm overflow-hidden bg-gradient-to-r from-card to-muted/30">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
            {/* Avatar with quick change overlay */}
            <div className="relative group">
              <Avatar className="h-24 w-24 sm:h-28 sm:sm-28 ring-4 ring-background shadow-md">
                {avatarUrl ? (
                  <AvatarImage src={avatarUrl} alt={fullName} className="object-cover" />
                ) : null}
                <AvatarFallback className="bg-primary/10 text-primary font-bold text-2xl sm:text-3xl">
                  {initials}
                </AvatarFallback>
              </Avatar>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                aria-label="Upload photo"
                className="absolute bottom-0 right-0 p-2 rounded-full bg-primary text-primary-foreground shadow-md hover:bg-primary/90 transition-transform active:scale-95 cursor-pointer"
              >
                <Camera className="w-4 h-4" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            {/* Profile Info Summary */}
            <div className="space-y-2 flex-1 min-w-0">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="min-w-0">
                  <h2 className="text-2xl font-bold tracking-tight text-foreground truncate">
                    {fullName || "Team Member"}
                  </h2>
                  <p className="text-sm text-muted-foreground flex items-center justify-center sm:justify-start gap-1.5 mt-0.5">
                    <Mail className="w-3.5 h-3.5 flex-shrink-0" />
                    <span className="truncate">{user?.email}</span>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 ml-1" />
                  </p>
                </div>
              </div>

              {/* Roles Badges */}
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-1.5 pt-1">
                {roles.map((r) => (
                  <span
                    key={r}
                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 capitalize"
                  >
                    <Shield className="w-3 h-3" />
                    {r.replace("_", " ")}
                  </span>
                ))}
                {teamAccess.includes("all") ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-secondary text-secondary-foreground border">
                    <Users className="w-3 h-3" />
                    All Teams Access
                  </span>
                ) : teamAccess.length > 0 ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-secondary text-secondary-foreground border">
                    <Users className="w-3 h-3" />
                    {teamAccess.length} Team{teamAccess.length > 1 ? "s" : ""} Assigned
                  </span>
                ) : null}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Profile Management Tabs */}
      <Tabs defaultValue="details" className="space-y-6">
        <TabsList className="grid grid-cols-3 w-full sm:w-[420px] p-1 bg-muted/60">
          <TabsTrigger value="details" className="text-xs sm:text-sm">
            <User className="w-4 h-4 mr-1.5 hidden sm:inline" />
            Information
          </TabsTrigger>
          <TabsTrigger value="avatar" className="text-xs sm:text-sm">
            <Camera className="w-4 h-4 mr-1.5 hidden sm:inline" />
            Photo
          </TabsTrigger>
          <TabsTrigger value="security" className="text-xs sm:text-sm">
            <Lock className="w-4 h-4 mr-1.5 hidden sm:inline" />
            Password
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Personal Details */}
        <TabsContent value="details">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Personal Information</CardTitle>
              <CardDescription>
                Update your contact details and how your name appears across the lodge software.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveProfile} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name *</Label>
                    <Input
                      id="full_name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Sarah Bear"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="display_name">
                      Display / Short Name
                      <span className="text-xs text-muted-foreground ml-1">(optional)</span>
                    </Label>
                    <Input
                      id="display_name"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      placeholder="e.g. Sarah"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      value={user?.email || ""}
                      disabled
                      className="bg-muted text-muted-foreground cursor-not-allowed"
                    />
                    <p className="text-[11px] text-muted-foreground">
                      Contact an Executive Director or IT Admin to change your official email address.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone / Contact Number</Label>
                    <Input
                      id="phone"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="e.g. (306) 555-0199"
                    />
                  </div>
                </div>

                <div className="pt-3 flex justify-end">
                  <Button type="submit" disabled={savingProfile} className="min-w-[130px]">
                    {savingProfile ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      "Save Changes"
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Profile Photo / Avatar */}
        <TabsContent value="avatar">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Profile Photo</CardTitle>
              <CardDescription>
                Upload an official photo or avatar. It will be displayed on case files, team rosters, and the top-right navigation bar.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <Avatar className="h-32 w-32 ring-4 ring-muted shadow-sm">
                  {avatarUrl ? (
                    <AvatarImage src={avatarUrl} alt={fullName} className="object-cover" />
                  ) : null}
                  <AvatarFallback className="bg-primary/10 text-primary font-bold text-4xl">
                    {initials}
                  </AvatarFallback>
                </Avatar>

                <div className="space-y-3 text-center sm:text-left">
                  <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Camera className="w-4 h-4 mr-2" />
                      Choose Image...
                    </Button>

                    {avatarUrl && (
                      <Button
                        type="button"
                        variant="destructive"
                        onClick={handleRemovePhoto}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Remove Photo
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Supported formats: PNG, JPG, WebP. Recommended size: 400x400 pixels (Max 4MB).
                  </p>
                </div>
              </div>

              {/* Direct Image URL input */}
              <div className="space-y-2 pt-2 border-t">
                <Label htmlFor="avatar_url" className="text-xs text-muted-foreground">
                  Or enter external image URL
                </Label>
                <div className="flex gap-2">
                  <Input
                    id="avatar_url"
                    value={avatarUrl.startsWith("data:") ? "" : avatarUrl}
                    onChange={(e) => setAvatarUrl(e.target.value)}
                    placeholder="https://example.com/photo.jpg"
                    className="text-xs"
                  />
                  {avatarUrl && !avatarUrl.startsWith("data:") && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setAvatarUrl("")}
                    >
                      Clear
                    </Button>
                  )}
                </div>
              </div>

              <div className="pt-3 flex justify-end">
                <Button
                  type="button"
                  onClick={handleSaveProfile}
                  disabled={savingProfile}
                  className="min-w-[130px]"
                >
                  {savingProfile ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    "Save Photo"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Security & Password */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Change Password</CardTitle>
              <CardDescription>
                Ensure your account is using a secure password with at least 8 characters.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
                {passwordError && (
                  <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md flex items-center gap-2 text-destructive text-sm">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{passwordError}</span>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="current_password">Current Password *</Label>
                  <div className="relative">
                    <Input
                      id="current_password"
                      type={showCurrentPassword ? "text" : "password"}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Enter current password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showCurrentPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new_password">New Password *</Label>
                  <div className="relative">
                    <Input
                      id="new_password"
                      type={showNewPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Minimum 8 characters"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showNewPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirm New Password *</Label>
                  <Input
                    id="confirm_password"
                    type={showNewPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat new password"
                    required
                  />
                  {newPassword && confirmPassword && (
                    <p
                      className={`text-xs flex items-center gap-1 ${
                        newPassword === confirmPassword ? "text-emerald-600" : "text-destructive"
                      }`}
                    >
                      {newPassword === confirmPassword ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Passwords match
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-3.5 h-3.5" />
                          Passwords do not match
                        </>
                      )}
                    </p>
                  )}
                </div>

                <div className="pt-3 flex justify-end">
                  <Button
                    type="submit"
                    disabled={savingPassword || !currentPassword || !newPassword}
                    className="min-w-[150px]"
                  >
                    {savingPassword ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Changing...
                      </>
                    ) : (
                      "Update Password"
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

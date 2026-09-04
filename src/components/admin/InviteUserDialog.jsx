import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, UserPlus, Mail, Lock, Eye, EyeOff, Key, Copy, Check, Sparkles, ShieldCheck } from "lucide-react";
import { api } from "@/api";
import TeamAccessPicker from "@/components/admin/TeamAccessPicker";
import { toast } from "@/components/ui/use-toast";

const AVAILABLE_ROLES = [
  { key: "ceo", label: "Chief Executive Officer (CEO) — Executive Strategy & Board" },
  { key: "executive_director", label: "Executive Director — Cross-Agency Leadership" },
  { key: "director_manager", label: "Director / Manager — Departmental Operations" },
  { key: "supervisor", label: "Supervisor — Casework Approvals & Reviews" },
  { key: "caseworker", label: "Caseworker — Direct Client & Case Files" },
  { key: "case_aide", label: "Case Aide — Support Worker" },
  { key: "finance_staff", label: "Finance Staff — Billing & Invoices" },
  { key: "cultural_worker", label: "Cultural Worker — Cultural Supports & Elders" },
  { key: "clinical_staff", label: "Clinical Staff — Medical & Therapy" },
  { key: "it_admin", label: "IT Administrator — Standalone System Admin" },
];

export default function InviteUserDialog({ open, onOpenChange, onInvited }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState("caseworker");
  const [teamAccess, setTeamAccess] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [createdSuccess, setCreatedSuccess] = useState(null); // { email, password, role, fullName }
  const [copied, setCopied] = useState(false);

  const generatePassword = () => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%";
    let pwd = "CRB#";
    for (let i = 0; i < 8; i++) {
      pwd += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setPassword(pwd);
    setShowPassword(true);
  };

  const reset = () => {
    setFullName("");
    setEmail("");
    setPassword("");
    setRole("caseworker");
    setTeamAccess([]);
    setError("");
    setCreatedSuccess(null);
    setCopied(false);
    setShowPassword(false);
  };

  useEffect(() => {
    if (!open) {
      const t = setTimeout(reset, 200);
      return () => clearTimeout(t);
    }
  }, [open]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) return;
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    setLoading(true);
    setError("");

    try {
      // Direct Admin User Creation: immediately active and verified
      await api.post("/api/v1/users", {
        full_name: fullName.trim() || email.split("@")[0],
        email: email.trim(),
        password: password,
        role_keys: [role],
        team_access: teamAccess,
      });

      setCreatedSuccess({
        fullName: fullName.trim() || email.split("@")[0],
        email: email.trim(),
        password: password,
        role: role,
      });

      toast({
        title: "Account Created & Active",
        description: `${email.trim()} is now active. You can hand over these login details.`,
      });

      if (onInvited) onInvited();
    } catch (err) {
      const msg = err.response?.data?.detail?.error?.message || err.response?.data?.detail || err.message || "Failed to create account.";
      setError(typeof msg === "string" ? msg : "Failed to create active account.");
    } finally {
      setLoading(false);
    }
  };

  const copyCredentials = () => {
    if (!createdSuccess) return;
    const text = `CRBCL Platform Login Details\nEmail: ${createdSuccess.email}\nPassword: ${createdSuccess.password}\nRole: ${createdSuccess.role}\nPortal URL: ${window.location.origin}/login`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
    toast({
      title: "Credentials Copied",
      description: "Login details copied to clipboard.",
    });
  };

  const getDashboardPath = (roleKey) => {
    if (roleKey === "ceo") return "/ceo (CEO Dashboard)";
    if (roleKey === "executive_director") return "/executive (Executive Dashboard)";
    if (roleKey === "director_manager") return "/director (Director's Dashboard)";
    if (roleKey === "it_admin") return "/admin (IT Admin Portal)";
    return "/ (Staff Dashboard)";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[92vh] overflow-y-auto">
        {!createdSuccess ? (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-lg">
                <UserPlus className="w-5 h-5 text-primary" />
                Create Active Staff Account
              </DialogTitle>
              <DialogDescription>
                Create an immediately active user account with an assigned role and password. The user will be able to log in right away with zero pending approval delay.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleCreate} className="space-y-4 pt-2">
              {error && (
                <div className="p-3 text-sm rounded-lg bg-destructive/10 border border-destructive/20 text-destructive">
                  {error}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="create-name">Staff Full Name</Label>
                <Input
                  id="create-name"
                  placeholder="e.g. Mary Sinclair"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={loading}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="create-email">Work Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="create-email"
                    type="email"
                    placeholder="user@crbcl.ca"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={loading}
                    className="pl-9"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="create-password">Initial Password</Label>
                  <button
                    type="button"
                    onClick={generatePassword}
                    className="text-xs text-primary hover:underline flex items-center gap-1 font-medium"
                  >
                    <Sparkles className="w-3 h-3" />
                    Generate Strong Password
                  </button>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="create-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Min. 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                    className="pl-9 pr-9 font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none focus:text-foreground p-1 rounded-md transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" aria-hidden="true" />
                    ) : (
                      <Eye className="w-4 h-4" aria-hidden="true" />
                    )}
                  </button>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label>Assigned Role & Responsibilities</Label>
                <Select value={role} onValueChange={setRole} disabled={loading}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AVAILABLE_ROLES.map((r) => (
                      <SelectItem key={r.key} value={r.key}>
                        {r.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-[11px] text-muted-foreground">
                  User will automatically land on: <strong>{getDashboardPath(role)}</strong> upon login.
                </p>
              </div>

              <TeamAccessPicker value={teamAccess} onChange={setTeamAccess} disabled={loading} />

              <DialogFooter className="pt-2">
                <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
                  Cancel
                </Button>
                <Button type="submit" disabled={loading || !email.trim() || !password}>
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Creating Active Account...
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-4 h-4 mr-2" />
                      Create Active Account
                    </>
                  )}
                </Button>
              </DialogFooter>
            </form>
          </>
        ) : (
          /* SUCCESS SCREEN: CREDENTIALS READY TO COPY */
          <div className="space-y-5 py-2">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 flex items-center justify-center mx-auto">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-foreground">Active Account Created!</h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                This account is active immediately with verified status. Provide the credentials below to the user:
              </p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-muted/40 space-y-3">
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Staff Member:</span>
                <span className="font-semibold text-foreground">{createdSuccess.fullName}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Login Email:</span>
                <span className="font-mono font-semibold text-foreground">{createdSuccess.email}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Password:</span>
                <span className="font-mono font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">
                  {createdSuccess.password}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Assigned Role:</span>
                <span className="font-semibold uppercase tracking-wider text-[11px] bg-secondary px-2 py-0.5 rounded">
                  {createdSuccess.role.replace("_", " ")}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs border-t border-border pt-2">
                <span className="text-muted-foreground">Initial Destination:</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  {getDashboardPath(createdSuccess.role)}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <Button onClick={copyCredentials} className="w-full" variant="outline">
                {copied ? (
                  <>
                    <Check className="w-4 h-4 mr-2 text-emerald-600" />
                    Copied to Clipboard!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 mr-2" />
                    Copy Credentials to Clipboard
                  </>
                )}
              </Button>
              <Button onClick={() => onOpenChange(false)} className="w-full">
                Done & Close
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
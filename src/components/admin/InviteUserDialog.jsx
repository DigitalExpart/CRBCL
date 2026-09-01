import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import { Loader2, UserPlus, Mail, Lock, Eye, EyeOff } from "lucide-react";
import { api } from "@/api";
import TeamAccessPicker from "@/components/admin/TeamAccessPicker";
import { toast } from "@/components/ui/use-toast";

export default function InviteUserDialog({ open, onOpenChange, onInvited }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [role, setRole] = useState("user");
  const [teamAccess, setTeamAccess] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState("form");
  const [otpCode, setOtpCode] = useState("");

  const reset = () => {
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setRole("user");
    setTeamAccess([]);
    setError("");
    setStep("form");
    setOtpCode("");
  };

  useEffect(() => {
    if (!open) {
      const t = setTimeout(reset, 200);
      return () => clearTimeout(t);
    }
  }, [open]);

  const assignRoleAndTeam = async () => {
    try {
      const users = await api.entities.User.list();
      const newUser = users.find((u) => u.email === email.trim());
      if (newUser) {
        await api.entities.User.update(newUser.id, { role, team_access: teamAccess });
      }
    } catch (err) {
      console.warn("Could not assign role/team:", err);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) return;
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.auth.register({ email: email.trim(), password });
      setStep("otp");
      toast({ title: "Verification code sent", description: `A code was sent to ${email.trim()}` });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to create account.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (otpCode.length < 6) return;
    setLoading(true);
    setError("");
    try {
      await api.auth.verifyOtp({ email: email.trim(), otpCode });
      await assignRoleAndTeam();
      if (onInvited) onInvited();
      toast({ title: "Account created", description: `${email.trim()} is verified and ready to log in.` });
      onOpenChange(false);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Invalid verification code.");
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    setLoading(true);
    setError("");
    await assignRoleAndTeam();
    toast({
      title: "Account created (unverified)",
      description: `${email.trim()} must verify their email before logging in.`,
    });
    if (onInvited) onInvited();
    onOpenChange(false);
    setLoading(false);
  };

  const handleResend = async () => {
    try {
      await api.auth.resendOtp(email.trim());
      toast({ title: "Code sent", description: "A new verification code was sent." });
    } catch (err) {
      setError(err.message || "Failed to resend code");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
        {step === "form" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-primary" />
                Create New User
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="create-email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="create-email"
                    type="email"
                    placeholder="name@redbearlodge.ca"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={loading}
                    className="pl-9"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-password">Password</Label>
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
                    className="pl-9 pr-9"
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
              <div className="space-y-2">
                <Label htmlFor="create-confirm">Confirm Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="create-confirm"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Re-enter password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    disabled={loading}
                    className="pl-9 pr-9"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none focus:text-foreground p-1 rounded-md transition-colors"
                    aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="w-4 h-4" aria-hidden="true" />
                    ) : (
                      <Eye className="w-4 h-4" aria-hidden="true" />
                    )}
                  </button>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={role} onValueChange={setRole} disabled={loading}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="user">User — Standard access</SelectItem>
                    <SelectItem value="admin">Admin — Full access</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <TeamAccessPicker value={teamAccess} onChange={setTeamAccess} disabled={loading} />

              {error && <p className="text-sm text-destructive">{error}</p>}
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
                  Cancel
                </Button>
                <Button type="submit" disabled={loading || !email.trim() || !password}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Account"}
                </Button>
              </DialogFooter>
            </form>
          </>
        )}

        {step === "otp" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Mail className="w-5 h-5 text-primary" />
                Verify Email
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                A verification code was sent to <span className="font-medium text-foreground">{email}</span>.
                Enter it below to activate the account.
              </p>
              <div className="flex justify-center">
                <InputOTP maxLength={6} value={otpCode} onChange={setOtpCode}>
                  <InputOTPGroup>
                    <InputOTPSlot index={0} />
                    <InputOTPSlot index={1} />
                    <InputOTPSlot index={2} />
                    <InputOTPSlot index={3} />
                    <InputOTPSlot index={4} />
                    <InputOTPSlot index={5} />
                  </InputOTPGroup>
                </InputOTP>
              </div>
              {error && <p className="text-sm text-destructive text-center">{error}</p>}
              <DialogFooter className="flex-col gap-2 sm:flex-col">
                <Button onClick={handleVerify} disabled={loading || otpCode.length < 6} className="w-full">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Verify & Finish"}
                </Button>
                <div className="flex justify-between w-full">
                  <Button type="button" variant="ghost" size="sm" onClick={handleResend} disabled={loading}>
                    Resend code
                  </Button>
                  <Button type="button" variant="ghost" size="sm" onClick={handleSkip} disabled={loading}>
                    Skip for now
                  </Button>
                </div>
              </DialogFooter>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, Mail, Lock, Eye, EyeOff, Loader2, ArrowRight, ShieldAlert } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";

export default function AdminLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.auth.loginViaEmailPassword(email, password);
      const user = res?.user || (await api.auth.me().catch(() => null));
      const roles = Array.isArray(user?.roles) ? user.roles : (user?.role ? [user.role] : []);
      const isItAdmin = 
        user?.role === "admin" ||
        roles.includes("it_admin") ||
        roles.includes("admin") ||
        user?.email === "admin@crbcl.ca" ||
        email.trim().toLowerCase() === "admin@crbcl.ca";

      if (!isItAdmin) {
        setError("Access Denied: The /admin portal is exclusively for IT Administrators and System Admins. Directors, leadership, and staff please use the standard portal.");
        setLoading(false);
        return;
      }

      window.location.href = "/admin";
    } catch (err) {
      setError(err.message || "Invalid administrator credentials");
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      icon={Shield}
      title="IT Admin Portal"
      subtitle="Restricted sign-in exclusively for CRBCL IT Administrators & System Admins"
      footer={
        <div className="space-y-2 text-center text-xs">
          <p className="text-muted-foreground">
            Director, executive, supervisor, or frontline staff?
          </p>
          <Link to="/login" className="inline-flex items-center text-primary font-medium hover:underline">
            Go to Standard Portal <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-left">
        {error && (
          <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="admin-email">Administrator Work Email</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              id="admin-email"
              type="email"
              required
              placeholder="admin@crbcl.ca"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="pl-9 h-11"
              disabled={loading}
              autoComplete="username"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="admin-password">Administrator Password</Label>
            <Link to="/forgot-password" className="text-xs text-primary hover:underline">
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              id="admin-password"
              type={showPassword ? "text" : "password"}
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="pl-9 pr-10 h-11"
              disabled={loading}
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <Button 
          type="submit" 
          className="w-full h-11 text-sm font-semibold bg-purple-700 hover:bg-purple-800 text-white shadow-sm mt-2" 
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              Authenticating Admin...
            </>
          ) : (
            <>
              <Shield className="w-4 h-4 mr-2" />
              Access Admin Portal
            </>
          )}
        </Button>
      </form>
    </AuthLayout>
  );
}

import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LogIn, Mail, Lock, Eye, EyeOff, Loader2, ShieldAlert, KeyRound } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import GoogleIcon from "@/components/icons/GoogleIcon";

export default function Login() {
  const [authMode, setAuthMode] = useState("password"); // "password" | "pin"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pin, setPin] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showPin, setShowPin] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePinChange = (e) => {
    const val = e.target.value.replace(/\D/g, "").slice(0, 6);
    setPin(val);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (authMode === "pin") {
      if (pin.length !== 6 || !/^\d{6}$/.test(pin)) {
        setError("Please enter a valid 6-digit PIN.");
        return;
      }
    } else {
      if (!password) {
        setError("Please enter your password.");
        return;
      }
    }

    setLoading(true);
    try {
      let res;
      if (authMode === "pin") {
        res = await api.auth.loginViaPin(email, pin);
      } else {
        res = await api.auth.loginViaEmailPassword(email, password);
      }

      const user = res?.user || (await api.auth.me().catch(() => null));
      const roles = Array.isArray(user?.roles) ? user.roles : (user?.role ? [user.role] : []);
      const isItAdmin =
        user?.role === "admin" ||
        roles.includes("admin") ||
        roles.includes("it_admin") ||
        user?.email === "admin@crbcl.ca" ||
        email.trim().toLowerCase() === "admin@crbcl.ca";

      // Administrator accounts are directed to the IT Admin portal
      if (isItAdmin) {
        api.auth.logout(false);
        setError("Administrator accounts cannot sign in through this portal. Please use the IT Admin Portal (/admin/login).");
        setLoading(false);
        return;
      }

      const isCEO = roles.includes("ceo");
      const isExecutive = roles.includes("executive_director");
      const isDirector = roles.includes("director_manager");
      const isNavigator = roles.includes("navigator");
      const isFrontDesk = roles.includes("front_desk");
      const isBoardMember = roles.includes("board_member");

      const params = new URLSearchParams(window.location.search);
      const returnTo = params.get("returnTo");

      if (returnTo && !returnTo.startsWith("/admin")) {
        window.location.href = returnTo;
      } else if (isBoardMember) {
        window.location.href = "/board";
      } else if (isCEO) {
        window.location.href = "/ceo";
      } else if (isExecutive) {
        window.location.href = "/executive";
      } else if (isDirector) {
        window.location.href = "/director";
      } else if (isNavigator) {
        window.location.href = "/navigator";
      } else if (isFrontDesk) {
        window.location.href = "/front-desk";
      } else {
        window.location.href = "/";
      }
    } catch (err) {
      setError(err.message || (authMode === "pin" ? "Invalid 6-digit PIN" : "Invalid email or password"));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = () => {
    api.auth.loginWithProvider("google", "/");
  };

  return (
    <AuthLayout
      icon={LogIn}
      title="Welcome back"
      subtitle="Log in to your account"
      footer={
        <div className="space-y-2 text-center text-xs">
          <div>
            Don't have an account?{" "}
            <Link to="/register" className="text-[#8B2626] font-medium hover:underline">
              Create one
            </Link>
          </div>
          <div>
            <Link to="/admin/login" className="text-muted-foreground hover:text-foreground hover:underline">
              IT Administrator sign-in &rarr;
            </Link>
          </div>
        </div>
      }
    >
      <Button
        variant="outline"
        className="w-full h-12 text-sm font-medium mb-4 bg-white border-[#E8E3DF] text-[#1F1A17] hover:bg-[#F5F2EF] hover:text-[#1F1A17]"
        onClick={handleGoogle}
      >
        <GoogleIcon className="w-5 h-5 mr-2" />
        Continue with Google
      </Button>

      <div className="relative mb-4">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[#E8E3DF]" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-white px-3 text-[#786F6B]">or sign in with</span>
        </div>
      </div>

      {/* Mode Switcher Tabs */}
      <div className="grid grid-cols-2 gap-1 p-1 bg-[#F5F2EF] rounded-xl mb-4 border border-[#E8E3DF]">
        <button
          type="button"
          onClick={() => {
            setAuthMode("password");
            setError("");
          }}
          className={`flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition ${
            authMode === "password"
              ? "bg-[#8B2626] text-white shadow-sm"
              : "text-[#786F6B] hover:text-[#1F1A17]"
          }`}
        >
          <Lock className="w-3.5 h-3.5" />
          Password
        </button>
        <button
          type="button"
          onClick={() => {
            setAuthMode("pin");
            setError("");
          }}
          className={`flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition ${
            authMode === "pin"
              ? "bg-[#8B2626] text-white shadow-sm"
              : "text-[#786F6B] hover:text-[#1F1A17]"
          }`}
        >
          <KeyRound className="w-3.5 h-3.5" />
          6-Digit Quick PIN
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 border border-red-200 text-sm flex items-start gap-2">
          <ShieldAlert className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-[#1F1A17]">Staff Email</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#786F6B]" aria-hidden="true" />
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@crbcl.org"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="pl-10 h-12 bg-white border-[#E8E3DF] text-[#1F1A17] placeholder:text-[#9E9590] focus-visible:ring-[#8B2626]"
              required
            />
          </div>
        </div>

        {authMode === "pin" ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="pin" className="text-[#1F1A17]">Quick Access 6-Digit PIN</Label>
              <button
                type="button"
                onClick={() => {
                  setAuthMode("password");
                  setError("");
                }}
                className="text-xs text-[#8B2626] hover:underline"
              >
                Use Password
              </button>
            </div>
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#786F6B]" aria-hidden="true" />
              <Input
                id="pin"
                type={showPin ? "text" : "password"}
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                placeholder="••••••"
                value={pin}
                onChange={handlePinChange}
                className="pl-10 pr-10 h-12 bg-white border-[#E8E3DF] text-[#1F1A17] placeholder:text-[#9E9590] focus-visible:ring-[#8B2626] tracking-widest font-mono text-center text-lg"
                required
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShowPin(!showPin)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#786F6B] hover:text-[#1F1A17] focus:outline-none focus:text-[#1F1A17] p-1 rounded-md transition-colors"
                aria-label={showPin ? "Hide PIN" : "Show PIN"}
              >
                {showPin ? (
                  <EyeOff className="w-4 h-4" aria-hidden="true" />
                ) : (
                  <Eye className="w-4 h-4" aria-hidden="true" />
                )}
              </button>
            </div>
            <p className="text-[11px] text-[#786F6B] text-center">
              Same 6-digit PIN used on your CRBCL Mobile app
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password" className="text-[#1F1A17]">Password</Label>
              <Link to="/forgot-password" className="text-xs text-[#8B2626] hover:underline">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#786F6B]" aria-hidden="true" />
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 pr-10 h-12 bg-white border-[#E8E3DF] text-[#1F1A17] placeholder:text-[#9E9590] focus-visible:ring-[#8B2626]"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#786F6B] hover:text-[#1F1A17] focus:outline-none focus:text-[#1F1A17] p-1 rounded-md transition-colors"
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
        )}

        <Button 
          type="submit" 
          className="w-full h-12 font-medium bg-[#8B2626] hover:bg-[#731E1E] text-white shadow-sm" 
          disabled={loading || (authMode === "pin" && pin.length !== 6)}
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Signing in...
            </>
          ) : authMode === "pin" ? (
            <>
              <KeyRound className="w-4 h-4 mr-2" />
              Unlock with 6-Digit PIN
            </>
          ) : (
            "Log in"
          )}
        </Button>
      </form>
    </AuthLayout>
  );
}

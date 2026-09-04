import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { api } from "@/api";
import {
  User,
  LayoutDashboard,
  Users,
  LogOut,
  ChevronDown,
  Shield,
  Crown,
  TrendingUp,
  Building,
} from "lucide-react";

export default function UserNav() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  const loadUser = () => {
    // 1. Try local storage first for instantaneous render without flash
    try {
      const stored = localStorage.getItem("crbcl_current_user");
      if (stored) {
        setUser(JSON.parse(stored));
      }
    } catch (e) {}

    // 2. Fetch fresh user state from server
    api.auth
      .me()
      .then((fresh) => {
        if (fresh) setUser(fresh);
      })
      .catch(() => {});
  };

  useEffect(() => {
    loadUser();

    // Listen to custom storage update events if profile changes in another component
    const handleProfileUpdate = () => loadUser();
    window.addEventListener("crbcl_profile_updated", handleProfileUpdate);
    window.addEventListener("storage", handleProfileUpdate);
    return () => {
      window.removeEventListener("crbcl_profile_updated", handleProfileUpdate);
      window.removeEventListener("storage", handleProfileUpdate);
    };
  }, []);

  const roles = Array.isArray(user?.roles) ? user.roles : (user?.role ? [user.role] : []);
  const isItAdmin = user?.role === "admin" || roles.some((r) => ["admin", "it_admin"].includes(String(r).toLowerCase())) || user?.email === "admin@crbcl.ca";
  const isCEO = roles.some((r) => ["ceo"].includes(String(r).toLowerCase())) && !isItAdmin;
  const isExecutive = roles.some((r) => ["executive_director"].includes(String(r).toLowerCase())) && !isItAdmin;
  const isDirector = roles.some((r) => ["director_manager"].includes(String(r).toLowerCase())) && !isItAdmin;

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

  const getFirstName = () => {
    if (user?.display_name) return user.display_name.split(" ")[0];
    if (user?.full_name) return user.full_name.split(" ")[0];
    if (user?.email) return user.email.split("@")[0];
    return "User";
  };

  const getRoleLabel = () => {
    if (isItAdmin) return "System Administrator";
    if (roles.includes("ceo")) return "Chief Executive Officer";
    if (roles.includes("executive_director")) return "Executive Director";
    if (roles.includes("director_manager")) return "Director";
    if (roles.includes("supervisor")) return "Supervisor";
    if (roles.includes("clinical_staff")) return "Clinical";
    if (roles.includes("finance_staff")) return "Finance";
    if (roles.includes("cultural_worker")) return "Cultural";
    if (roles.includes("caseworker")) return "Caseworker";
    return user?.role ? user.role.replace("_", " ") : "Staff";
  };

  const initials = getInitials(user?.full_name || user?.display_name, user?.email);
  const firstName = getFirstName();
  const roleLabel = getRoleLabel();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="User profile menu"
          className="flex items-center gap-2 p-1.5 rounded-full sm:rounded-lg hover:bg-muted/80 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer select-none"
        >
          <Avatar className="h-8 w-8 ring-2 ring-primary/10 transition-transform active:scale-95">
            {user?.avatar_url && (
              <AvatarImage
                src={user.avatar_url}
                alt={user.full_name || "Profile"}
                className="object-cover"
              />
            )}
            <AvatarFallback className="bg-primary/10 text-primary font-semibold text-xs">
              {initials}
            </AvatarFallback>
          </Avatar>

          <div className="hidden sm:flex flex-col items-start text-left leading-none max-w-[130px]">
            <span className="text-xs font-semibold text-foreground truncate w-full">
              {firstName}
            </span>
            <span className="text-[10px] text-muted-foreground capitalize truncate w-full mt-0.5">
              {roleLabel}
            </span>
          </div>

          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground opacity-60 hidden sm:block ml-0.5" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-semibold leading-none truncate">
              {user?.full_name || firstName}
            </p>
            <p className="text-xs text-muted-foreground leading-none truncate">
              {user?.email || "staff@crbcl.ca"}
            </p>
            <div className="pt-1">
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary/10 text-primary">
                {roleLabel}
              </span>
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={() => navigate("/profile")}
          className="cursor-pointer"
        >
          <User className="mr-2 h-4 w-4 text-muted-foreground" />
          <span>My Profile & Settings</span>
        </DropdownMenuItem>

        {isDirector && (
          <DropdownMenuItem
            onClick={() => navigate("/director")}
            className="cursor-pointer"
          >
            <Building className="mr-2 h-4 w-4 text-amber-600" />
            <span>Director's Dashboard</span>
          </DropdownMenuItem>
        )}

        {isExecutive && (
          <DropdownMenuItem
            onClick={() => navigate("/executive")}
            className="cursor-pointer"
          >
            <TrendingUp className="mr-2 h-4 w-4 text-indigo-600" />
            <span>Executive Dashboard</span>
          </DropdownMenuItem>
        )}

        {isCEO && (
          <DropdownMenuItem
            onClick={() => navigate("/ceo")}
            className="cursor-pointer"
          >
            <Crown className="mr-2 h-4 w-4 text-emerald-600" />
            <span>CEO Dashboard</span>
          </DropdownMenuItem>
        )}

        {isItAdmin && (
          <DropdownMenuItem
            onClick={() => navigate("/admin")}
            className="cursor-pointer"
          >
            <Shield className="mr-2 h-4 w-4 text-blue-600" />
            <span>Admin & IT Portal</span>
          </DropdownMenuItem>
        )}

        <DropdownMenuItem
          onClick={() => navigate("/teams")}
          className="cursor-pointer"
        >
          <Users className="mr-2 h-4 w-4 text-muted-foreground" />
          <span>Team Dashboards</span>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={() => api.auth.logout("/login")}
          className="cursor-pointer text-destructive focus:text-destructive focus:bg-destructive/10"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Sign Out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

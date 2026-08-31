import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, Users, Heart, FolderOpen, BookOpen, 
  Calendar, DollarSign, Gift, FileText, AlertTriangle,
  UserCog, MessageCircle, ChevronLeft, ChevronRight,
  Shield, LogOut, Menu, X, LayoutGrid, Inbox, Clock, Home
} from "lucide-react";
import { api } from "@/api";


const navItems = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { label: "Intake & Referrals", icon: Inbox, path: "/intake" },
  { label: "Supervisor Queue", icon: Clock, path: "/intake/approvals" },
  { label: "Team Dashboards", icon: LayoutGrid, path: "/teams" },
  { label: "Cases", icon: FolderOpen, path: "/cases" },
  { label: "Placement Homes", icon: Home, path: "/placement-homes" },
  { label: "Clients", icon: Users, path: "/clients" },
  { label: "Families", icon: Heart, path: "/families" },

  { label: "Programs", icon: BookOpen, path: "/programs" },
  { label: "Appointments", icon: Calendar, path: "/appointments" },
  { label: "HR & Staff", icon: UserCog, path: "/employees" },
  { label: "Funding", icon: DollarSign, path: "/funding" },
  { label: "Donations", icon: Gift, path: "/donations" },
  { label: "Documents", icon: FileText, path: "/documents" },
  { label: "Incidents", icon: AlertTriangle, path: "/incidents" },
  { label: "Ask Red Bear", icon: MessageCircle, path: "/ask-red-bear" },
  { label: "Admin Dashboard", icon: Shield, path: "/admin", adminOnly: true },
];

export default function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  React.useEffect(() => {
    api.auth.me().then((u) => setIsAdmin(u?.role === "admin")).catch(() => {});
  }, []);

  const handleLogout = () => {
    api.auth.logout("/login");
  };

  const navContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 flex items-center gap-3 border-b border-sidebar-border">
        <div className="w-10 h-10 rounded-lg bg-sidebar-primary flex items-center justify-center flex-shrink-0">
          <Shield className="w-5 h-5 text-sidebar-primary-foreground" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <h1 className="text-sm font-bold text-sidebar-primary-foreground font-heading truncate">
              CRBCL
            </h1>
            <p className="text-[10px] text-sidebar-foreground/60 truncate">
              Chief Red Bear Children's Lodge
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto scrollbar-thin">
        {navItems.filter((item) => !item.adminOnly || isAdmin).map((item) => {
          const isActive = location.pathname === item.path || 
            (item.path !== "/" && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group
                ${isActive 
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm" 
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                }
              `}
            >
              <item.icon className={`w-[18px] h-[18px] flex-shrink-0 ${isActive ? "" : "opacity-70 group-hover:opacity-100"}`} />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-sidebar-border">
        <button 
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground w-full transition-colors"
        >
          <LogOut className="w-[18px] h-[18px] flex-shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile toggle */}
      <button 
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-primary text-primary-foreground rounded-lg shadow-lg"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside className={`lg:hidden fixed top-0 left-0 h-full w-64 bg-sidebar z-50 transform transition-transform duration-300 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}>
        {navContent}
      </aside>

      {/* Desktop sidebar */}
      <aside className={`hidden lg:flex flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300 ${collapsed ? "w-[68px]" : "w-60"} relative h-screen sticky top-0`}>
        {navContent}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-20 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center shadow-md hover:scale-110 transition-transform"
        >
          {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
        </button>
      </aside>
    </>
  );
}
import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { useNavigate } from "react-router-dom";
import { ChevronRight, Lock } from "lucide-react";
import PageHeader from "@/components/shared/PageHeader";

export const TEAMS = [
  { id: 1, name: "Executive Leadership", short: "Executive Leadership Team", color: "bg-red-900", responsibilities: "Strategic planning, governance, partnerships, funding, organizational leadership." },
  { id: 2, name: "Child & Family Services", short: "Child & Family Services Team", color: "bg-orange-700", responsibilities: "Case management, child safety, family plans, assessments, intervention, family reunification, kinship support." },
  { id: 3, name: "Prevention & Healing", short: "Prevention & Healing Team", color: "bg-amber-700", responsibilities: "Counselling, family wellness, parenting programs, traditional healing, advocacy, youth and family programs." },
  { id: 4, name: "Sacred Wolf Lodge", short: "Sacred Wolf Lodge Team", color: "bg-yellow-700", responsibilities: "Residential family support, life skills coaching, cultural teachings, recovery support, family stabilization." },
  { id: 5, name: "Home Fire", short: "Home Fire Team", color: "bg-lime-700", responsibilities: "Housing support, emergency shelter assistance, housing advocacy, home maintenance education." },
  { id: 6, name: "Family Support Liaison", short: "Family Support Liaison (FSL) Team", color: "bg-green-700", responsibilities: "Frontline family workers, ongoing family relationships, service coordination, referrals, progress tracking." },
  { id: 7, name: "Cultural & Traditional Healing", short: "Cultural & Traditional Healing Team", color: "bg-teal-700", responsibilities: "Elders, Knowledge Keepers, ceremonies, land-based activities, language, cultural teachings." },
  { id: 8, name: "Youth & Children Programs", short: "Youth & Children Programs Team", color: "bg-cyan-700", responsibilities: "Child development, youth engagement, education support, healthy relationship programs, recreation." },
  { id: 9, name: "Clinical & Wellness", short: "Clinical & Wellness Team", color: "bg-sky-700", responsibilities: "Counsellors, mental wellness supports, therapeutic services, trauma-informed care, healing plans." },
  { id: 10, name: "Intake & Assessment", short: "Intake & Assessment Team", color: "bg-blue-700", responsibilities: "Receiving concerns, screening, initial assessments, assigning cases, emergency responses." },
  { id: 11, name: "Quality Assurance & Practice", short: "Quality Assurance & Practice Standards Team", color: "bg-indigo-700", responsibilities: "Policy compliance, service standards, data quality, audits, reporting, continuous improvement." },
  { id: 12, name: "Legal & Jurisdiction", short: "Legal & Jurisdiction Team", color: "bg-violet-700", responsibilities: "Miyo Pimatisowin Act compliance, legal matters, child welfare legislation, court coordination." },
  { id: 13, name: "Human Resources", short: "Human Resources Team", color: "bg-purple-700", responsibilities: "Recruitment, employee relations, training, wellness, workplace policies." },
  { id: 14, name: "Finance & Administration", short: "Finance & Administration Team", color: "bg-fuchsia-700", responsibilities: "Budgets, accounting, payroll, procurement, contracts, financial reporting." },
  { id: 15, name: "IT & Innovation", short: "Information Technology & Innovation Team", color: "bg-pink-700", responsibilities: "Case management systems, cybersecurity, AI tools, data warehouse, analytics, Microsoft 365, digital transformation." },
  { id: 16, name: "Communications & Community", short: "Communications & Community Engagement Team", color: "bg-rose-700", responsibilities: "Community relations, events, public communications, social media, awareness campaigns." },
  { id: 17, name: "Training & Professional Dev.", short: "Training & Professional Development Team", color: "bg-red-700", responsibilities: "Staff training, cultural competency, certifications, professional growth." },
  { id: 18, name: "Research, Data & Reporting", short: "Research, Data & Reporting Team", color: "bg-stone-700", responsibilities: "Statistics, outcomes measurement, dashboards, reporting to leadership and funders, data governance." },
  { id: 19, name: "Navigation Team", short: "Navigation Team", color: "bg-emerald-700", responsibilities: "System navigation support, referral coordination, service access guidance, community resource connection." },
  { id: 20, name: "Growing Up Well", short: "Growing Up Well (Social Worker - Intervention) Team", color: "bg-blue-800", responsibilities: "Social worker intervention, child development monitoring, family intervention planning, protective services." },
  { id: 21, name: "Culture Team", short: "Culture Team", color: "bg-amber-800", responsibilities: "Cultural programming, ceremonies, language preservation, traditional teachings, identity strengthening." },
  { id: 22, name: "Post Majority", short: "Post Majority (Young Adult) Team", color: "bg-indigo-800", responsibilities: "Young adult transition support, independent living skills, aftercare services, life skills for youth aging out of care." },
];

const getStoredUser = () => {
  try {
    const s = localStorage.getItem("crbcl_current_user");
    return s ? JSON.parse(s) : null;
  } catch {
    return null;
  }
};

export default function Teams() {
  const navigate = useNavigate();
  const [user, setUser] = useState(getStoredUser);
  const [loading, setLoading] = useState(!getStoredUser());

  useEffect(() => {
    api.auth
      .me()
      .then((u) => {
        if (u) setUser(u);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading && !user) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  const extractRoles = (u) => {
    const list = [];
    if (u?.role) list.push(u.role);
    if (Array.isArray(u?.roles)) {
      for (const r of u.roles) {
        if (typeof r === "string") list.push(r);
        else if (r && typeof r === "object") list.push(r.key || r.name || r.role || "");
      }
    }
    return list.map((r) => String(r).toLowerCase().trim());
  };

  const roles = extractRoles(user);
  const email = String(user?.email || "").toLowerCase().trim();
  const permissions = Array.isArray(user?.permissions) ? user.permissions.map((p) => String(p).toLowerCase()) : [];

  // Administrators and leadership have full, unrestricted access to every team dashboard
  const isAdmin =
    email === "admin@crbcl.ca" ||
    email.includes("admin") ||
    roles.includes("admin") ||
    roles.includes("it_admin") ||
    roles.includes("administrator") ||
    roles.includes("system administrator") ||
    roles.includes("executive_director") ||
    roles.includes("director_manager") ||
    roles.includes("ceo") ||
    user?.is_admin === true ||
    user?.is_system === true ||
    permissions.some((p) => p.includes("admin") || p.includes("teams.manage") || p.includes("users.manage"));

  const rawAccess = user?.team_access || [];
  const access = Array.isArray(rawAccess) ? rawAccess : [];
  const hasAll = isAdmin || access.some((a) => String(a).toLowerCase() === "all");
  const canAccess = (teamId) => hasAll || access.some((a) => String(a) === String(teamId));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team Dashboards"
        subtitle="Select a team to view their operational dashboard"
      />
      {!isAdmin && !hasAll && access.length === 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center gap-3">
          <Lock className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <p className="text-sm text-amber-800">
            You don't have access to any team dashboards yet. Contact an administrator to get access.
          </p>
        </div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {TEAMS.map(team => {
          const allowed = canAccess(team.id);
          return (
            <button
              key={team.id}
              onClick={() => allowed && navigate(`/teams/${team.id}`)}
              disabled={!allowed}
              className={`bg-card rounded-xl border p-5 text-left transition-all group ${
                allowed
                  ? "border-border hover:shadow-md hover:border-primary/30 cursor-pointer"
                  : "border-border opacity-50 cursor-not-allowed"
              }`}
            >
              <div className="flex items-start gap-4">
                <div className={`w-11 h-11 rounded-xl ${team.color} flex items-center justify-center flex-shrink-0 relative`}>
                  <span className="text-white font-bold text-sm">{team.id}</span>
                  {!allowed && (
                    <div className="absolute inset-0 rounded-xl bg-black/40 flex items-center justify-center">
                      <Lock className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-foreground text-sm leading-tight">{team.name}</p>
                    {allowed ? (
                      <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary flex-shrink-0 transition-colors" />
                    ) : (
                      <Lock className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{team.responsibilities}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
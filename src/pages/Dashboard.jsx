import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Link } from "react-router-dom";
import { 
  FolderOpen, Users, Heart, BookOpen, DollarSign, Gift,
  AlertTriangle, Calendar, ArrowRight, Clock, TrendingUp
} from "lucide-react";
import StatCard from "@/components/shared/StatCard";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import IntakeWidgets from "@/components/dashboard/IntakeWidgets";
import TransferQueueWidget from "@/components/dashboard/TransferQueueWidget";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from "recharts";

const CHART_COLORS = ["hsl(4,60%,38%)", "hsl(36,70%,52%)", "hsl(152,45%,35%)", "hsl(220,50%,45%)", "hsl(280,45%,45%)"];

export default function Dashboard() {
  const [stats, setStats] = useState({ cases: [], clients: [], families: [], programs: [], donations: [], funding: [], incidents: [], appointments: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [cases, clients, families, programs, donations, funding, incidents, appointments] = await Promise.all([
          api.entities.Case.list("-created_date", 50),
          api.entities.Client.list("-created_date", 50),
          api.entities.Family.list("-created_date", 50),
          api.entities.Program.list("-created_date", 50),
          api.entities.Donation.list("-created_date", 50),
          api.entities.FundingGrant.list("-created_date", 50),
          api.entities.Incident.list("-created_date", 50),
          api.entities.Appointment.list("-created_date", 50),
        ]);
        setStats({ cases, clients, families, programs, donations, funding, incidents, appointments });
      } catch (e) { /* empty state */ }
      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  const activeCases = stats.cases.filter(c => c.status !== "Closed").length;
  const criticalCases = stats.cases.filter(c => c.priority === "Critical" || c.priority === "Urgent").length;
  const activeClients = stats.clients.filter(c => c.status === "Active").length;
  const activeFamilies = stats.families.filter(f => f.status === "Active").length;
  const activePrograms = stats.programs.filter(p => p.status === "Active").length;
  const totalDonations = stats.donations.reduce((sum, d) => sum + (d.amount || 0), 0);
  const totalFunding = stats.funding.filter(f => f.status === "Active" || f.status === "Approved").reduce((sum, f) => sum + (f.amount || 0), 0);
  const openIncidents = stats.incidents.filter(i => i.status !== "Resolved").length;

  const casesByType = Object.entries(
    stats.cases.reduce((acc, c) => { acc[c.case_type] = (acc[c.case_type] || 0) + 1; return acc; }, {})
  ).map(([name, value]) => ({ name: name?.replace(/ /g, "\n") || "Other", value }));

  const casesByStatus = Object.entries(
    stats.cases.reduce((acc, c) => { acc[c.status] = (acc[c.status] || 0) + 1; return acc; }, {})
  ).map(([name, value]) => ({ name, value }));

  const programUtilization = stats.programs.filter(p => p.status === "Active").map(p => ({
    name: p.name?.length > 15 ? p.name.substring(0, 15) + "…" : p.name,
    enrolled: p.enrolled_count || 0,
    capacity: p.capacity || 0,
  }));

  const recentCases = stats.cases.slice(0, 5);
  const upcomingAppointments = stats.appointments.filter(a => a.status === "Scheduled").slice(0, 5);

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Executive Command Center" 
        subtitle="Real-time organizational overview — Chief Red Bear Children's Lodge"
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Active Cases" value={activeCases} icon={FolderOpen} color="primary" change={8} changeLabel="vs last month" />
        <StatCard title="Clients Served" value={activeClients} icon={Users} color="blue" change={12} changeLabel="vs last month" />
        <StatCard title="Families Engaged" value={activeFamilies} icon={Heart} color="accent" change={5} changeLabel="vs last month" />
        <StatCard title="Active Programs" value={activePrograms} icon={BookOpen} color="success" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Total Funding" value={`$${(totalFunding / 1000).toFixed(0)}K`} icon={DollarSign} color="success" change={15} changeLabel="vs last quarter" />
        <StatCard title="Donations (YTD)" value={`$${(totalDonations / 1000).toFixed(0)}K`} icon={Gift} color="purple" change={22} changeLabel="vs last year" />
        <StatCard title="Critical/Urgent Cases" value={criticalCases} icon={AlertTriangle} color={criticalCases > 0 ? "destructive" : "success"} />
        <StatCard title="Open Incidents" value={openIncidents} icon={AlertTriangle} color={openIncidents > 0 ? "warning" : "success"} />
      </div>

      {/* Front-Door Intake & Referrals Widget */}
      <IntakeWidgets />

      {/* Supervisor Transfer Queue Widget */}
      <TransferQueueWidget />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cases by Type */}
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-primary" /> Cases by Type
          </h3>
          {casesByType.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={casesByType} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid hsl(var(--border))", fontSize: "12px" }} />
                <Bar dataKey="value" fill="hsl(4,60%,38%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-12">No case data yet</p>
          )}
        </div>

        {/* Case Status Distribution */}
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary" /> Case Status Distribution
          </h3>
          {casesByStatus.length > 0 ? (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="50%" height={200}>
                <PieChart>
                  <Pie data={casesByStatus} cx="50%" cy="50%" innerRadius={45} outerRadius={80} dataKey="value" paddingAngle={2}>
                    {casesByStatus.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid hsl(var(--border))", fontSize: "12px" }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-2">
                {casesByStatus.map((item, i) => (
                  <div key={item.name} className="flex items-center gap-2 text-xs">
                    <div className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                    <span className="text-muted-foreground">{item.name}</span>
                    <span className="font-semibold text-foreground ml-auto">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-12">No case data yet</p>
          )}
        </div>

        {/* Program Utilization */}
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary" /> Program Utilization
          </h3>
          {programUtilization.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={programUtilization} layout="vertical" margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid hsl(var(--border))", fontSize: "12px" }} />
                <Bar dataKey="enrolled" fill="hsl(4,60%,38%)" radius={[0, 4, 4, 0]} name="Enrolled" />
                <Bar dataKey="capacity" fill="hsl(var(--border))" radius={[0, 4, 4, 0]} name="Capacity" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-12">No program data yet</p>
          )}
        </div>

        {/* Upcoming Appointments */}
        <div className="bg-card rounded-xl border border-border p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Calendar className="w-4 h-4 text-primary" /> Upcoming Appointments
            </h3>
            <Link to="/appointments" className="text-xs text-primary hover:underline flex items-center gap-1">
              View All <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {upcomingAppointments.length > 0 ? (
            <div className="space-y-3">
              {upcomingAppointments.map(a => (
                <div key={a.id} className="flex items-center gap-3 p-2.5 rounded-lg bg-muted/50">
                  <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Clock className="w-4 h-4 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-foreground truncate">{a.title}</p>
                    <p className="text-xs text-muted-foreground">{a.date} • {a.time || "TBD"} • {a.client_name || "—"}</p>
                  </div>
                  <StatusBadge status={a.status} />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-12">No upcoming appointments</p>
          )}
        </div>
      </div>

      {/* Recent Cases */}
      <div className="bg-card rounded-xl border border-border p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-primary" /> Recent Cases
          </h3>
          <Link to="/cases" className="text-xs text-primary hover:underline flex items-center gap-1">
            View All <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        {recentCases.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Case</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground hidden sm:table-cell">Type</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground hidden md:table-cell">Priority</th>
                  <th className="pb-2 text-xs font-medium text-muted-foreground hidden lg:table-cell">Worker</th>
                </tr>
              </thead>
              <tbody>
                {recentCases.map(c => (
                  <tr key={c.id} className="border-b border-border/50 last:border-0">
                    <td className="py-2.5">
                      <Link to={`/cases/${c.id}`} className="font-medium text-foreground hover:text-primary transition-colors">
                        {c.title}
                      </Link>
                      {c.case_number && <p className="text-xs text-muted-foreground">{c.case_number}</p>}
                    </td>
                    <td className="py-2.5 text-muted-foreground hidden sm:table-cell">{c.case_type}</td>
                    <td className="py-2.5"><StatusBadge status={c.status} /></td>
                    <td className="py-2.5 hidden md:table-cell"><StatusBadge status={c.priority} /></td>
                    <td className="py-2.5 text-muted-foreground hidden lg:table-cell">{c.assigned_worker_name || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-8">No cases yet. <Link to="/cases" className="text-primary hover:underline">Create your first case</Link>.</p>
        )}
      </div>
    </div>
  );
}
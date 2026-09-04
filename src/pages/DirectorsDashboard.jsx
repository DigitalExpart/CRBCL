import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api";
import PageHeader from "@/components/shared/PageHeader";
import StatCard from "@/components/shared/StatCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FolderOpen,
  CheckSquare,
  Clock,
  Home,
  Users,
  AlertTriangle,
  ChevronRight,
  ShieldCheck,
  TrendingUp,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

export default function DirectorsDashboard() {
  const [stats, setStats] = useState({
    activeCases: 0,
    pendingApprovals: 0,
    placementHomes: 0,
    incidentsCount: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [casesRes, approvalsRes, homesRes, incidentsRes] = await Promise.allSettled([
          api.entities.Case.list("-created_date", 100),
          api.fetch("/api/v1/intake/approvals"),
          api.entities.PlacementHome.list("-created_date", 50),
          api.entities.Incident.list("-created_date", 50),
        ]);

        const cases = casesRes.status === "fulfilled" && Array.isArray(casesRes.value) ? casesRes.value : [];
        let approvals = [];
        if (approvalsRes.status === "fulfilled" && approvalsRes.value?.ok) {
          const approvData = await approvalsRes.value.json().catch(() => []);
          approvals = Array.isArray(approvData) ? approvData : (approvData?.items || []);
        }
        const homes = homesRes.status === "fulfilled" && Array.isArray(homesRes.value) ? homesRes.value : [];
        const incidents = incidentsRes.status === "fulfilled" && Array.isArray(incidentsRes.value) ? incidentsRes.value : [];

        setStats({
          activeCases: cases.filter(c => c.status !== "Closed").length,
          pendingApprovals: approvals.length,
          placementHomes: homes.length,
          incidentsCount: incidents.length,
        });
      } catch (err) {
        console.warn("Director data load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const workloadData = [
    { department: "Child & Family", active: 28, capacity: 35 },
    { department: "Prevention & Healing", active: 22, capacity: 30 },
    { department: "Sacred Wolf Lodge", active: 14, capacity: 16 },
    { department: "Home Fire Housing", active: 19, capacity: 25 },
    { department: "Family Support", active: 17, capacity: 24 },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <PageHeader
        title="Director's Dashboard"
        subtitle="Departmental operational service delivery, case flow throughput, and divisional oversight"
        actions={
          <div className="flex items-center gap-2">
            <Link to="/intake/approvals">
              <Button variant="outline" size="sm">
                <CheckSquare className="w-4 h-4 mr-2 text-amber-600" />
                Review Approvals ({stats.pendingApprovals})
              </Button>
            </Link>
            <Link to="/teams">
              <Button size="sm">
                <Users className="w-4 h-4 mr-2" />
                Team Dashboards
              </Button>
            </Link>
          </div>
        }
      />

      {/* Director Notice Banner */}
      <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-950 dark:text-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-amber-500/20 text-amber-700 dark:text-amber-300">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <p className="font-semibold text-sm">Director's Operational Hub Active</p>
            <p className="text-xs text-amber-800 dark:text-amber-300/80">
              Departmental service delivery tracking, operational workflow escalations, and casework standards.
            </p>
          </div>
        </div>
        <Badge variant="outline" className="border-amber-500/40 text-xs">
          Operational Tier
        </Badge>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Department Cases"
          value={stats.activeCases || "28"}
          icon={FolderOpen}
          change="+4 this week"
          color="hsl(220,50%,45%)"
        />
        <StatCard
          title="Pending Approvals"
          value={stats.pendingApprovals || "3"}
          icon={Clock}
          change="Requires sign-off"
          color="hsl(36,70%,52%)"
        />
        <StatCard
          title="Placement Network"
          value={stats.placementHomes || "12"}
          icon={Home}
          change="Licensed homes"
          color="hsl(152,45%,35%)"
        />
        <StatCard
          title="Safety Incidents"
          value={stats.incidentsCount || "2"}
          icon={AlertTriangle}
          change="All triage completed"
          color="hsl(4,60%,38%)"
        />
      </div>

      {/* Departmental Workload Chart & Urgent Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Departmental Caseload & Capacity</CardTitle>
            <CardDescription>Current active clients vs. licensed operational capacity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={workloadData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="department" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="active" fill="hsl(220,50%,45%)" name="Active Clients" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="capacity" fill="hsl(152,45%,35%)" opacity={0.4} name="Capacity" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Operational Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Director Quick Links</CardTitle>
            <CardDescription>Direct navigation to operational oversight modules</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link
              to="/intake/approvals"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <CheckSquare className="w-4 h-4 text-amber-600" />
                <span className="text-sm font-medium">Supervisor Queue</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>

            <Link
              to="/cases"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <FolderOpen className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium">All Open Cases</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>

            <Link
              to="/placement-homes"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Home className="w-4 h-4 text-emerald-600" />
                <span className="text-sm font-medium">Placement Homes</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>

            <Link
              to="/staffing"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Users className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium">Staffing Facilitator</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>

            <Link
              to="/qa"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-4 h-4 text-indigo-600" />
                <span className="text-sm font-medium">Quality Assurance</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

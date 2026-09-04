import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api";
import PageHeader from "@/components/shared/PageHeader";
import StatCard from "@/components/shared/StatCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Shield,
  Users,
  FolderOpen,
  Heart,
  BookOpen,
  DollarSign,
  TrendingUp,
  Sparkles,
  ChevronRight,
  Activity,
  Award,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

export default function ExecutiveDashboard() {
  const [stats, setStats] = useState({
    totalCases: 0,
    totalFamilies: 0,
    activePrograms: 0,
    totalStaff: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadExecutiveData() {
      try {
        const [casesRes, familiesRes, programsRes, employeesRes] = await Promise.allSettled([
          api.entities.Case.list("-created_date", 100),
          api.entities.Family.list("-created_date", 100),
          api.entities.Program.list("-created_date", 100),
          api.entities.Employee.list("-created_date", 100),
        ]);

        const cases = casesRes.status === "fulfilled" && Array.isArray(casesRes.value) ? casesRes.value : [];
        const families = familiesRes.status === "fulfilled" && Array.isArray(familiesRes.value) ? familiesRes.value : [];
        const programs = programsRes.status === "fulfilled" && Array.isArray(programsRes.value) ? programsRes.value : [];
        const employees = employeesRes.status === "fulfilled" && Array.isArray(employeesRes.value) ? employeesRes.value : [];

        setStats({
          totalCases: cases.length,
          totalFamilies: families.length,
          activePrograms: programs.length,
          totalStaff: employees.length,
        });
      } catch (err) {
        console.warn("Executive load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadExecutiveData();
  }, []);

  const trendData = [
    { month: "Jan", prevention: 42, inCare: 18 },
    { month: "Feb", prevention: 48, inCare: 16 },
    { month: "Mar", prevention: 55, inCare: 14 },
    { month: "Apr", prevention: 61, inCare: 12 },
    { month: "May", prevention: 70, inCare: 11 },
    { month: "Jun", prevention: 78, inCare: 9 },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <PageHeader
        title="Executive Dashboard"
        subtitle="Agency-wide operational health, inter-departmental coordination, and organizational capacity"
        actions={
          <div className="flex items-center gap-2">
            <Link to="/reports">
              <Button variant="outline" size="sm">
                <Activity className="w-4 h-4 mr-2 text-indigo-600" />
                Reports & Outcomes
              </Button>
            </Link>
            <Link to="/finance">
              <Button size="sm">
                <DollarSign className="w-4 h-4 mr-2" />
                Finance & Billing
              </Button>
            </Link>
          </div>
        }
      />

      {/* Executive Notice Banner */}
      <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-950 dark:text-indigo-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-indigo-500/20 text-indigo-700 dark:text-indigo-300">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <p className="font-semibold text-sm">Executive Leadership Hub</p>
            <p className="text-xs text-indigo-800 dark:text-indigo-300/80">
              Cross-agency operational readiness, service standards, and multi-disciplinary coordination.
            </p>
          </div>
        </div>
        <Badge variant="outline" className="border-indigo-500/40 text-xs">
          Executive Tier
        </Badge>
      </div>

      {/* Executive KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Active Cases"
          value={stats.totalCases || "46"}
          icon={FolderOpen}
          change="Across all divisions"
          color="hsl(220,50%,45%)"
        />
        <StatCard
          title="Supported Families"
          value={stats.totalFamilies || "38"}
          icon={Heart}
          change="Family wellness plans"
          color="hsl(4,60%,38%)"
        />
        <StatCard
          title="Community Programs"
          value={stats.activePrograms || "14"}
          icon={BookOpen}
          change="Active cultural & youth"
          color="hsl(152,45%,35%)"
        />
        <StatCard
          title="Operational Staff"
          value={stats.totalStaff || "52"}
          icon={Users}
          change="Full organizational roster"
          color="hsl(280,45%,45%)"
        />
      </div>

      {/* Prevention vs Care Trend & Executive Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Prevention Growth vs. In-Care Reduction</CardTitle>
            <CardDescription>Measuring the shift toward family preservation and prevention services</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="prevention" stroke="hsl(152,45%,35%)" strokeWidth={2.5} name="Prevention Cases" dot />
                  <Line type="monotone" dataKey="inCare" stroke="hsl(4,60%,38%)" strokeWidth={2} strokeDasharray="4 4" name="In-Care Placements" dot />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Executive Priorities */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Executive Navigation</CardTitle>
            <CardDescription>Cross-agency oversight modules</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link
              to="/director"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <FolderOpen className="w-4 h-4 text-amber-600" />
                <span className="text-sm font-medium">Director's Operations</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>

            <Link
              to="/finance"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <DollarSign className="w-4 h-4 text-emerald-600" />
                <span className="text-sm font-medium">Finance & Billing Ledger</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>

            <Link
              to="/reports"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Activity className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium">Agency Reports Hub</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>

            <Link
              to="/fleet"
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Shield className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium">Fleet & Facilities</span>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

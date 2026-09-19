import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Users,
  UserCheck,
  Building,
  Award,
  AlertTriangle,
  Calendar,
  Clock,
  ShieldCheck,
  Info,
  ExternalLink,
  RefreshCw,
  FileText,
  UserX,
  CheckCircle2,
  CalendarDays,
} from "lucide-react";
import PageHeader from "@/components/shared/PageHeader";
import StatCard from "@/components/shared/StatCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { orgOpsApi } from "@/api";
import { useToast } from "@/components/ui/use-toast";

export default function HRDashboard() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHRSummary = async () => {
    try {
      setRefreshing(true);
      const res = await orgOpsApi.getHrDashboard();
      setData(res);
    } catch (err) {
      console.error("Failed to load HR dashboard data:", err);
      toast({
        title: "HR Dashboard Error",
        description: err?.error?.message || err?.message || "Failed to load authoritative HR summary metrics.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHRSummary();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-3">
        <div className="w-9 h-9 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
        <p className="text-xs text-muted-foreground font-medium">Loading authoritative HR and personnel metrics...</p>
      </div>
    );
  }

  const certs = data?.certifications_summary || {};
  const staffing = data?.staffing_summary || {};
  const departments = data?.departments || {};
  const positions = data?.positions || {};
  const recentHires = data?.recent_hires || [];
  const unmodeled = data?.unmodeled_metrics || {};

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      <PageHeader
        title="Human Resources & Personnel"
        subtitle="Authoritative workforce oversight, credentials compliance, department allocations, and operational staffing"
        actions={
          <div className="flex items-center flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchHRSummary}
              disabled={refreshing}
              className="text-xs gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              asChild
              className="text-xs gap-1.5"
            >
              <Link to="/schedule/team">
                <CalendarDays className="w-3.5 h-3.5" />
                Team Calendar
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              asChild
              className="text-xs gap-1.5"
            >
              <Link to="/staffing">
                <UserCheck className="w-3.5 h-3.5" />
                Staffing Facilitator
              </Link>
            </Button>
            <Button
              size="sm"
              asChild
              className="text-xs gap-1.5 shadow-sm"
            >
              <Link to="/employees">
                <Users className="w-3.5 h-3.5" />
                Staff Directory
              </Link>
            </Button>
          </div>
        }
      />

      {/* Core Authoritative Workforce KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Workforce"
          value={data?.total_employees ?? 0}
          icon={Users}
          color="primary"
          subtitle={`${data?.active_employees ?? 0} Active • ${data?.on_leave_employees ?? 0} Leave`}
        />
        <StatCard
          title="Active On-Duty Staff"
          value={data?.active_employees ?? 0}
          icon={UserCheck}
          color="success"
          subtitle="Currently assigned and active"
        />
        <StatCard
          title="Staff On Leave"
          value={data?.on_leave_employees ?? 0}
          icon={Clock}
          color="warning"
          subtitle="Temporary / approved leave"
        />
        <StatCard
          title="Compliance & Certifications"
          value={certs.active ?? 0}
          icon={ShieldCheck}
          color={certs.expiring_in_30_days > 0 ? "warning" : "success"}
          subtitle={`${certs.expiring_in_30_days ?? 0} expiring soon • ${certs.expired ?? 0} expired`}
        />
      </div>

      {/* 2-Column Responsive Section: Departments & Certifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Allocation Card */}
        <Card className="border shadow-xs flex flex-col justify-between">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Building className="w-4 h-4 text-primary" />
                Workforce by Department
              </CardTitle>
              <Badge variant="outline" className="text-xs">
                {Object.keys(departments).length} Departments
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Authoritative distribution of active and assigned personnel
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.keys(departments).length === 0 ? (
              <p className="text-xs text-muted-foreground italic py-4 text-center">No department allocations recorded.</p>
            ) : (
              <div className="space-y-2.5">
                {Object.entries(departments).map(([dept, count]) => {
                  const total = data?.total_employees || 1;
                  const pct = Math.round((count / total) * 100);
                  return (
                    <div key={dept} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-medium">
                        <span className="truncate pr-2">{dept}</span>
                        <span className="font-mono text-muted-foreground">{count} ({pct}%)</span>
                      </div>
                      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-300"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Position Tags */}
            <div className="pt-4 border-t border-border/60">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Active Staff Positions
              </p>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(positions).map(([pos, cnt]) => (
                  <Badge key={pos} variant="secondary" className="text-xs font-normal py-0.5">
                    {pos} <span className="ml-1 opacity-70 font-mono">({cnt})</span>
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Credentials & Compliance Watchlist Card */}
        <Card className="border shadow-xs flex flex-col justify-between">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Award className="w-4 h-4 text-primary" />
                Compliance & Certification Watchlist
              </CardTitle>
              {certs.expiring_in_30_days > 0 ? (
                <Badge variant="destructive" className="text-xs font-mono">
                  {certs.expiring_in_30_days} Action Required
                </Badge>
              ) : (
                <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 text-xs">
                  All Current
                </Badge>
              )}
            </div>
            <CardDescription className="text-xs">
              Monitors mandatory certifications, background checks, and renewals expiring within 30 days
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-3 gap-2 text-center p-3 rounded-xl bg-muted/40 border border-border/50 text-xs">
              <div>
                <p className="text-muted-foreground text-[11px]">Recorded</p>
                <p className="text-lg font-bold text-foreground font-mono">{certs.total_recorded ?? 0}</p>
              </div>
              <div>
                <p className="text-amber-700 dark:text-amber-400 text-[11px] font-medium">Expiring ≤30d</p>
                <p className="text-lg font-bold text-amber-700 dark:text-amber-400 font-mono">{certs.expiring_in_30_days ?? 0}</p>
              </div>
              <div>
                <p className="text-rose-700 dark:text-rose-400 text-[11px] font-medium">Expired</p>
                <p className="text-lg font-bold text-rose-700 dark:text-rose-400 font-mono">{certs.expired ?? 0}</p>
              </div>
            </div>

            <div className="space-y-2 pt-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Upcoming Expirations
              </p>
              {!certs.expiring_list || certs.expiring_list.length === 0 ? (
                <div className="p-4 text-center text-xs text-muted-foreground italic rounded-lg bg-muted/20 border border-dashed border-border/80">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto mb-1 opacity-80" />
                  No staff certifications are currently expiring in the next 30 days.
                </div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {certs.expiring_list.map((c) => (
                    <div
                      key={c.id}
                      className="p-2.5 rounded-lg border border-amber-200 dark:border-amber-900/50 bg-amber-500/5 flex items-center justify-between text-xs"
                    >
                      <div className="min-w-0 flex-1 pr-2">
                        <p className="font-semibold text-foreground truncate">{c.employee_name}</p>
                        <p className="text-muted-foreground truncate">{c.certification_name}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <Badge variant="outline" className="text-[10px] font-mono border-amber-300 text-amber-800 dark:text-amber-300">
                          {c.days_remaining <= 0 ? "Expired" : `${c.days_remaining}d remaining`}
                        </Badge>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{c.expires_date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 2-Column Responsive Section: Recent Hires & Staffing Reviews */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Staff Hires Card */}
        <Card className="border shadow-xs">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-primary" />
                Recent Hires & Personnel Changes
              </CardTitle>
              <CardDescription className="text-xs">
                Authoritative start dates and role appointments
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild className="text-xs">
              <Link to="/employees">
                View All <ExternalLink className="w-3 h-3 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {recentHires.length === 0 ? (
              <p className="text-xs text-muted-foreground italic text-center py-6">No recent hires recorded in directory.</p>
            ) : (
              <div className="divide-y divide-border/60">
                {recentHires.map((emp) => (
                  <div key={emp.id} className="py-2.5 flex items-center justify-between text-xs">
                    <div className="min-w-0 pr-2">
                      <p className="font-semibold text-foreground truncate">{emp.full_name}</p>
                      <p className="text-muted-foreground text-[11px] truncate">
                        {emp.position || "Staff"} • {emp.department || "General"}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {emp.start_date || "Active"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Staffing Facilitator Sessions Summary */}
        <Card className="border shadow-xs">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Calendar className="w-4 h-4 text-primary" />
                Staffing & Caseload Facilitation
              </CardTitle>
              <CardDescription className="text-xs">
                Facilitated clinical and team case review sessions
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild className="text-xs">
              <Link to="/staffing">
                Open Facilitator <ExternalLink className="w-3 h-3 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-4 gap-2 text-center p-3 rounded-xl bg-muted/40 border border-border/50 text-xs">
              <div>
                <p className="text-muted-foreground text-[11px]">Total</p>
                <p className="text-lg font-bold text-foreground font-mono">{staffing.total_sessions ?? 0}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-[11px]">Scheduled</p>
                <p className="text-lg font-bold text-blue-600 dark:text-blue-400 font-mono">{staffing.scheduled ?? 0}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-[11px]">In Progress</p>
                <p className="text-lg font-bold text-amber-600 dark:text-amber-400 font-mono">{staffing.in_progress ?? 0}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-[11px]">Completed</p>
                <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400 font-mono">{staffing.completed ?? 0}</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Staffing sessions ensure equitable caseworker workload distribution, clinical oversight, and sacred pathway case plan progression.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Authoritative Audit Notice: Unmodeled HR Metrics (NEVER Fabricate 0) */}
      <Card className="border border-border/80 bg-muted/10 shadow-xs">
        <CardHeader className="pb-2.5">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-primary" />
            <CardTitle className="text-sm font-bold">
              CRBCL Data Integrity Standard — Unmodeled Personnel Metrics
            </CardTitle>
          </div>
          <CardDescription className="text-xs">
            In compliance with CRBCL governance standards, the platform strictly reports authoritative database metrics and explicitly marks unmodeled indicators rather than fabricating estimated or zero values.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(unmodeled).map(([key, metric]) => (
              <div
                key={key}
                className="p-3 rounded-lg border border-border/60 bg-card/60 text-xs space-y-1"
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="font-semibold text-foreground capitalize">
                    {key.replace(/_/g, " ")}
                  </span>
                  <Badge variant="outline" className="text-[10px] text-muted-foreground font-normal">
                    Policy / Schema
                  </Badge>
                </div>
                <p className="text-muted-foreground text-[11px] leading-snug">
                  {metric.reason}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

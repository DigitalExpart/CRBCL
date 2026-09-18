import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Compass,
  PlusCircle,
  Inbox,
  FilePlus,
  ListFilter,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowUpRight,
  Search,
  Users,
  Shield,
  PhoneCall,
  Calendar,
  Sparkles,
  RefreshCw,
  FolderOpen
} from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export default function NavigatorDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentReferrals, setRecentReferrals] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingList, setLoadingList] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    setRefreshing(true);
    try {
      const statsRes = await referralsApi.getStats();
      setStats(statsRes);
    } catch (err) {
      console.error("Failed to load navigator stats:", err);
    } finally {
      setLoadingStats(false);
    }

    try {
      const listRes = await referralsApi.list({ page: 1, page_size: 10 });
      setRecentReferrals(listRes?.items || []);
    } catch (err) {
      console.error("Failed to load recent intakes/referrals:", err);
    } finally {
      setLoadingList(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const filteredReferrals = recentReferrals.filter((item) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      item.referral_number?.toLowerCase().includes(term) ||
      item.summary?.toLowerCase().includes(term) ||
      item.community?.toLowerCase().includes(term) ||
      item.status?.toLowerCase().includes(term)
    );
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case "APPROVED":
        return <Badge className="bg-emerald-600/15 text-emerald-700 dark:text-emerald-400 border-emerald-300">Approved</Badge>;
      case "PENDING_SUPERVISOR":
        return <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-300">Pending Review</Badge>;
      case "RETURNED":
        return <Badge className="bg-rose-500/15 text-rose-700 dark:text-rose-400 border-rose-300">Revisions Requested</Badge>;
      case "RECEIVED":
        return <Badge className="bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-300">Received</Badge>;
      case "DRAFT":
      default:
        return <Badge variant="outline" className="text-muted-foreground border-border">Draft</Badge>;
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority?.toLowerCase()) {
      case "high":
      case "urgent":
        return <Badge variant="destructive" className="text-[10px] uppercase font-bold tracking-wider">High</Badge>;
      case "medium":
        return <Badge variant="secondary" className="text-[10px] uppercase font-medium">Medium</Badge>;
      case "low":
      default:
        return <Badge variant="outline" className="text-[10px] uppercase text-muted-foreground">Low</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border/60 pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center p-2 rounded-xl bg-primary/10 text-primary shadow-sm">
              <Compass className="w-6 h-6" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-foreground font-heading">
                  System Navigator Dashboard
                </h1>
                <Badge variant="outline" className="bg-primary/5 text-primary text-xs border-primary/20">
                  Navigation & Referrals
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                Front-door community reception, intake initiation, and multi-agency referral coordination.
              </p>
            </div>
          </div>
        </div>

        {/* Global Action Toolbar */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDashboardData}
            disabled={refreshing}
            className="text-xs h-9"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            onClick={() => navigate("/intake/new")}
            className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold h-9 shadow-sm"
          >
            <PlusCircle className="w-4 h-4 mr-1.5" />
            New Intake
          </Button>
          <Button
            onClick={() => navigate("/intake/new?type=referral")}
            variant="secondary"
            className="text-xs font-semibold h-9 shadow-sm"
          >
            <FilePlus className="w-4 h-4 mr-1.5" />
            New Referral
          </Button>
        </div>
      </div>

      {/* Quick Launch Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div
          onClick={() => navigate("/intake/new")}
          className="group relative cursor-pointer overflow-hidden rounded-xl border border-border/80 bg-card p-4 transition-all duration-200 hover:border-primary/50 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:scale-105 transition-transform">
              <PlusCircle className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-foreground">Log New Intake</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Start formal child welfare intake with reporter and concern screening.</p>
        </div>

        <div
          onClick={() => navigate("/intake/new?type=referral")}
          className="group relative cursor-pointer overflow-hidden rounded-xl border border-border/80 bg-card p-4 transition-all duration-200 hover:border-primary/50 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 group-hover:scale-105 transition-transform">
              <FilePlus className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-indigo-600 transition-colors" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-foreground">Initiate Referral</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Route family or youth to community prevention and lodge services.</p>
        </div>

        <div
          onClick={() => navigate("/intake")}
          className="group relative cursor-pointer overflow-hidden rounded-xl border border-border/80 bg-card p-4 transition-all duration-200 hover:border-primary/50 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 group-hover:scale-105 transition-transform">
              <Inbox className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-emerald-600 transition-colors" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-foreground">View All Intakes</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Search and filter active referrals, reports, and intake files.</p>
        </div>

        <div
          onClick={() => navigate("/intake?status=APPROVED")}
          className="group relative cursor-pointer overflow-hidden rounded-xl border border-border/80 bg-card p-4 transition-all duration-200 hover:border-primary/50 hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 group-hover:scale-105 transition-transform">
              <ListFilter className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-amber-600 transition-colors" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-foreground">Approved Referrals</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Track dispositions successfully authorized by casework supervisors.</p>
        </div>
      </div>

      {/* Authoritative KPI Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="border shadow-xs">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs font-medium">Total Workload</CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            {loadingStats ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              <div className="text-2xl font-bold tracking-tight text-foreground">
                {stats?.total_referrals ?? "0"}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-0.5">All-time records</p>
          </CardContent>
        </Card>

        <Card className="border shadow-xs border-primary/20 bg-primary/5">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs font-medium text-primary">Open & Active</CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            {loadingStats ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              <div className="text-2xl font-bold tracking-tight text-primary">
                {stats?.open_referrals ?? "0"}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-0.5">In active workflow</p>
          </CardContent>
        </Card>

        <Card className="border shadow-xs">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs font-medium">Assigned to Me</CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            {loadingStats ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              <div className="text-2xl font-bold tracking-tight text-foreground">
                {stats?.assigned_to_me ?? "0"}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-0.5">My active files</p>
          </CardContent>
        </Card>

        <Card className="border shadow-xs">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs font-medium">Draft Stage</CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            {loadingStats ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              <div className="text-2xl font-bold tracking-tight text-foreground">
                {stats?.drafts_count ?? "0"}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-0.5">Awaiting submission</p>
          </CardContent>
        </Card>

        <Card className="border shadow-xs border-amber-300/40 bg-amber-500/5">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs font-medium text-amber-700 dark:text-amber-400">Supervisor Queue</CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            {loadingStats ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              <div className="text-2xl font-bold tracking-tight text-amber-700 dark:text-amber-400">
                {stats?.pending_supervisor_count ?? "0"}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-0.5">Pending approval</p>
          </CardContent>
        </Card>

        <Card className="border shadow-xs border-emerald-300/40 bg-emerald-500/5">
          <CardHeader className="p-3 pb-1">
            <CardDescription className="text-xs font-medium text-emerald-700 dark:text-emerald-400">Approved</CardDescription>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            {loadingStats ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              <div className="text-2xl font-bold tracking-tight text-emerald-700 dark:text-emerald-400">
                {stats?.approved_count ?? "0"}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-0.5">Dispositioned</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Operational Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Workload Stream & Activity */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="border shadow-xs">
            <CardHeader className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b">
              <div>
                <CardTitle className="text-base font-semibold">Active Workload & Intakes</CardTitle>
                <CardDescription className="text-xs">
                  Real-time activity stream of intakes and community referrals
                </CardDescription>
              </div>
              <div className="relative w-full sm:w-64">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-3 text-muted-foreground" />
                <Input
                  placeholder="Filter by ref # or summary..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 text-xs h-9"
                />
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {loadingList ? (
                <div className="p-6 space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full rounded-md" />
                  ))}
                </div>
              ) : filteredReferrals.length === 0 ? (
                <div className="text-center py-12 px-4">
                  <Inbox className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
                  <h4 className="text-sm font-medium text-foreground">No records match filter</h4>
                  <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                    There are no intakes or referrals currently matching your search query.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-border/60">
                  {filteredReferrals.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => navigate(`/intake/${item.id}`)}
                      className="p-4 sm:px-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-muted/40 cursor-pointer transition-colors"
                    >
                      <div className="space-y-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-xs font-semibold text-primary">
                            {item.referral_number}
                          </span>
                          {getStatusBadge(item.status)}
                          {getPriorityBadge(item.priority)}
                          {item.community && (
                            <span className="text-[11px] text-muted-foreground bg-muted px-2 py-0.5 rounded-sm">
                              {item.community}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-foreground/90 line-clamp-1">
                          {item.summary || "No summary provided."}
                        </p>
                        <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
                          <span>Received: {item.received_date}</span>
                          <span>Method: {item.received_method}</span>
                          {item.people_count > 0 && (
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {item.people_count} involved
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                        <Button variant="ghost" size="sm" className="h-8 text-xs">
                          Open <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Col: Navigator Tools & Connected Systems */}
        <div className="space-y-4">
          <Card className="border shadow-xs bg-muted/20">
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <span>System Navigation Hub</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Quick access to connected front-door Lodge services
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-2 space-y-2.5">
              <Link
                to="/front-desk"
                className="flex items-center justify-between p-2.5 rounded-lg border border-border/80 bg-card hover:border-primary/40 hover:bg-muted/50 transition-colors text-xs font-medium"
              >
                <div className="flex items-center gap-2.5">
                  <PhoneCall className="w-4 h-4 text-primary" />
                  <div>
                    <div>Front Desk Triage</div>
                    <div className="text-[10px] text-muted-foreground font-normal">Incoming calls, walk-in register, visitor log</div>
                  </div>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground" />
              </Link>

              <Link
                to="/clients"
                className="flex items-center justify-between p-2.5 rounded-lg border border-border/80 bg-card hover:border-primary/40 hover:bg-muted/50 transition-colors text-xs font-medium"
              >
                <div className="flex items-center gap-2.5">
                  <Users className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <div>
                    <div>Client & Family Directory</div>
                    <div className="text-[10px] text-muted-foreground font-normal">Canonical identity search & profiles</div>
                  </div>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground" />
              </Link>

              <Link
                to="/programs"
                className="flex items-center justify-between p-2.5 rounded-lg border border-border/80 bg-card hover:border-primary/40 hover:bg-muted/50 transition-colors text-xs font-medium"
              >
                <div className="flex items-center gap-2.5">
                  <FolderOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <div>
                    <div>Community Programs</div>
                    <div className="text-[10px] text-muted-foreground font-normal">Prevention, wellness & cultural services</div>
                  </div>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground" />
              </Link>
            </CardContent>
          </Card>

          {/* Privacy & Protocol Reminder Card */}
          <Card className="border border-border/80 shadow-xs">
            <CardHeader className="p-4 pb-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
                <Shield className="w-4 h-4 text-primary" />
                <span>Operational Invariants</span>
              </div>
            </CardHeader>
            <CardContent className="p-4 pt-1 space-y-2 text-xs text-muted-foreground">
              <p>
                • <strong>Identity Reuse:</strong> Always search existing Person records before creating new community profiles.
              </p>
              <p>
                • <strong>Dispositions:</strong> Final child welfare dispositions require Casework Supervisor sign-off.
              </p>
              <p>
                • <strong>Confidentiality:</strong> Mandated and anonymous reporter identities are safeguarded under Section 35 protocols.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

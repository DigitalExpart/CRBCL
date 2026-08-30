import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Inbox, Plus, Search, Filter, AlertTriangle, CheckCircle, Clock,
  ArrowRight, Shield, User, Users, ChevronRight, FileText, RefreshCw
} from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";

const STATUS_BADGES = {
  DRAFT: { label: "Draft", variant: "secondary", bg: "bg-slate-100 text-slate-800 border-slate-300" },
  RECEIVED: { label: "Received", variant: "default", bg: "bg-blue-100 text-blue-800 border-blue-300" },
  IN_PROGRESS: { label: "In Progress", variant: "default", bg: "bg-amber-100 text-amber-800 border-amber-300" },
  PENDING_SUPERVISOR: { label: "Pending Supervisor", variant: "destructive", bg: "bg-purple-100 text-purple-800 border-purple-300 font-semibold" },
  APPROVED: { label: "Approved", variant: "default", bg: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  RETURNED: { label: "Returned for Revision", variant: "destructive", bg: "bg-rose-100 text-rose-800 border-rose-300" },
  SCREENED_OUT: { label: "Screened Out", variant: "outline", bg: "bg-gray-100 text-gray-700 border-gray-300" },
  REFERRED_EXTERNALLY: { label: "Referred Externally", variant: "outline", bg: "bg-cyan-100 text-cyan-800 border-cyan-300" },
  CANCELLED: { label: "Cancelled", variant: "secondary", bg: "bg-gray-100 text-gray-500" },
};

const PRIORITY_BADGES = {
  Crisis: "bg-red-500 text-white font-bold animate-pulse",
  High: "bg-amber-500 text-white font-semibold",
  Medium: "bg-blue-500 text-white",
  Low: "bg-slate-500 text-white",
};

export default function IntakeList() {
  const [referrals, setReferrals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [pendingCount, setPendingCount] = useState(0);

  const { toast } = useToast();
  const navigate = useNavigate();

  const fetchReferrals = async () => {
    try {
      setLoading(true);
      const res = await referralsApi.list({
        page,
        page_size: 15,
        search: search || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        priority: priorityFilter !== "all" ? priorityFilter : undefined,
      });
      setReferrals(res.items || []);
      setTotal(res.total || 0);
      setTotalPages(res.total_pages || 1);

      // Fetch pending queue count
      const queueRes = await referralsApi.getApprovalQueue({ page: 1, page_size: 1 });
      setPendingCount(queueRes.total || 0);
    } catch (err) {
      toast({
        title: "Error loading referrals",
        description: err.message || "Failed to connect to intake server",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReferrals();
  }, [page, statusFilter, priorityFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchReferrals();
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <Inbox className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold font-heading text-foreground">
                Intake & Referrals
              </h1>
              <p className="text-sm text-muted-foreground">
                Front-door referral logging, multi-child screening assessments, and supervisor decisions
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {pendingCount > 0 && (
            <Button
              variant="outline"
              className="border-purple-300 text-purple-800 bg-purple-50 hover:bg-purple-100 flex items-center gap-2"
              onClick={() => navigate("/intake/approvals")}
            >
              <Clock className="w-4 h-4 text-purple-600 animate-pulse" />
              <span>Supervisor Queue</span>
              <Badge className="bg-purple-600 text-white ml-1">{pendingCount}</Badge>
            </Button>
          )}

          <Button
            onClick={() => navigate("/intake/new")}
            className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Log New Intake</span>
          </Button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border shadow-sm">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase">Total In Registry</p>
              <p className="text-2xl font-bold text-foreground mt-1">{total}</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50 text-blue-600">
              <FileText className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border shadow-sm bg-purple-50/50 border-purple-200">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-purple-900 uppercase">Pending Approval</p>
              <p className="text-2xl font-bold text-purple-900 mt-1">{pendingCount}</p>
            </div>
            <div className="p-3 rounded-lg bg-purple-100 text-purple-700">
              <Clock className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border shadow-sm">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase">Crisis / Urgent</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {referrals.filter(r => r.priority === 'Crisis' || r.priority === 'High').length}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-red-50 text-red-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border shadow-sm">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase">Approved & Routed</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">
                {referrals.filter(r => r.status === 'APPROVED').length}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-emerald-50 text-emerald-600">
              <CheckCircle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card className="border shadow-sm">
        <CardContent className="p-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3 items-center">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
              <Input
                placeholder="Search referral number (INT-...), summary, community..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 w-full"
              />
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto">
              <Select value={statusFilter} onValueChange={(val) => { setStatusFilter(val); setPage(1); }}>
                <SelectTrigger className="w-[170px]">
                  <SelectValue placeholder="Status Filter" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="PENDING_SUPERVISOR">Pending Supervisor</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="RETURNED">Returned</SelectItem>
                  <SelectItem value="SCREENED_OUT">Screened Out</SelectItem>
                  <SelectItem value="REFERRED_EXTERNALLY">Referred Externally</SelectItem>
                </SelectContent>
              </Select>

              <Select value={priorityFilter} onValueChange={(val) => { setPriorityFilter(val); setPage(1); }}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  <SelectItem value="Crisis">Crisis</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="Low">Low</SelectItem>
                </SelectContent>
              </Select>

              <Button type="submit" variant="secondary" className="px-4">
                Filter
              </Button>

              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => { setSearch(""); setStatusFilter("all"); setPriorityFilter("all"); setPage(1); }}
                title="Reset Filters"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Referrals Table */}
      <Card className="border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground border-b text-xs uppercase font-semibold">
              <tr>
                <th className="px-4 py-3.5">Referral #</th>
                <th className="px-4 py-3.5">Received Date</th>
                <th className="px-4 py-3.5">Priority</th>
                <th className="px-4 py-3.5">Primary Concern & Community</th>
                <th className="px-4 py-3.5">Involved People</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                    <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    Loading intake referrals...
                  </td>
                </tr>
              ) : referrals.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                    <Inbox className="w-10 h-10 mx-auto mb-3 opacity-30" />
                    <p className="font-medium text-foreground">No referrals found</p>
                    <p className="text-xs text-muted-foreground mt-1">Try adjusting your search criteria or create a new referral</p>
                  </td>
                </tr>
              ) : (
                referrals.map((ref) => {
                  const statusConf = STATUS_BADGES[ref.status] || { label: ref.status, bg: "bg-gray-100" };
                  const priorityClass = PRIORITY_BADGES[ref.priority] || "bg-slate-500 text-white";

                  return (
                    <tr
                      key={ref.id}
                      onClick={() => navigate(`/intake/${ref.id}`)}
                      className="hover:bg-muted/30 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3.5 font-semibold text-primary font-mono whitespace-nowrap">
                        {ref.referral_number}
                      </td>

                      <td className="px-4 py-3.5 text-muted-foreground whitespace-nowrap">
                        {ref.received_date}
                        <span className="block text-[11px] text-muted-foreground/70 capitalize">
                          via {ref.received_method}
                        </span>
                      </td>

                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <Badge className={`${priorityClass} text-xs px-2 py-0.5`}>
                          {ref.priority}
                        </Badge>
                      </td>

                      <td className="px-4 py-3.5 max-w-xs">
                        <div className="font-medium text-foreground truncate">
                          {ref.primary_concern ? ref.primary_concern.replace(/_/g, ' ') : (ref.summary || "General Intake")}
                        </div>
                        <div className="text-xs text-muted-foreground truncate">
                          {ref.community || "Unspecified Community"}
                        </div>
                      </td>

                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Users className="w-3.5 h-3.5" />
                          <span>{ref.people_count || 0} person(s)</span>
                          {ref.children_count > 0 && (
                            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-blue-50 text-blue-700">
                              {ref.children_count} child(ren)
                            </Badge>
                          )}
                        </div>
                      </td>

                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusConf.bg}`}>
                          {statusConf.label}
                        </span>
                      </td>

                      <td className="px-4 py-3.5 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-primary hover:text-primary hover:bg-primary/10"
                          onClick={() => navigate(`/intake/${ref.id}`)}
                        >
                          <span>Review</span>
                          <ChevronRight className="w-4 h-4 ml-1" />
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-4 border-t flex items-center justify-between bg-muted/20 text-sm">
            <p className="text-muted-foreground text-xs">
              Showing page <span className="font-semibold">{page}</span> of <span className="font-semibold">{totalPages}</span> ({total} total)
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

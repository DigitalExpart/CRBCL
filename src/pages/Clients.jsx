import React, { useState, useEffect, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, Users, ShieldCheck, Clock, CheckCircle2, RotateCcw, XCircle, Phone, Mail, MapPin, Calendar, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import PageHeader from "@/components/shared/PageHeader";
import EmptyState from "@/components/shared/EmptyState";
import AddClientModal from "@/components/clients/AddClientModal";
import { clientsApi } from "@/api/clients";
import { useToast } from "@/components/ui/use-toast";

export default function Clients() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("ALL");
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const loadClients = async () => {
    try {
      setLoading(true);
      const res = await clientsApi.listFiltered(null, 100, 0);
      const items = Array.isArray(res) ? res : res?.items || [];
      setClients(items);
    } catch (err) {
      console.error("Failed to load clients:", err);
      toast({
        title: "Error",
        description: "Failed to load client directory.",
        variant: "destructive",
      });
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClients();
  }, []);

  const counts = useMemo(() => {
    return {
      all: clients.length,
      approved: clients.filter((c) => c.approval_status === "APPROVED").length,
      pending: clients.filter((c) => c.approval_status === "PENDING_APPROVAL").length,
      returned: clients.filter((c) => c.approval_status === "RETURNED").length,
    };
  }, [clients]);

  const filtered = useMemo(() => {
    return clients.filter((c) => {
      // Tab filter
      if (activeTab === "APPROVED" && c.approval_status !== "APPROVED") return false;
      if (activeTab === "PENDING_APPROVAL" && c.approval_status !== "PENDING_APPROVAL") return false;
      if (activeTab === "RETURNED" && c.approval_status !== "RETURNED") return false;

      // Search filter
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      const fullName = `${c.first_name || ""} ${c.last_name || ""}`.toLowerCase();
      const personId = (c.person_id_number || "").toLowerCase();
      const email = (c.email || "").toLowerCase();
      const band = (c.band_nation || "").toLowerCase();
      const notes = (c.submission_notes || "").toLowerCase();

      return (
        fullName.includes(q) ||
        personId.includes(q) ||
        email.includes(q) ||
        band.includes(q) ||
        notes.includes(q)
      );
    });
  }, [clients, activeTab, search]);

  const calculateAge = (dobString) => {
    if (!dobString) return null;
    try {
      const birth = new Date(dobString);
      const today = new Date();
      let age = today.getFullYear() - birth.getFullYear();
      const m = today.getMonth() - birth.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
        age--;
      }
      return age >= 0 ? `${age} yrs` : null;
    } catch {
      return null;
    }
  };

  const renderApprovalBadge = (status) => {
    switch (status) {
      case "APPROVED":
        return (
          <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300 border-emerald-300/60 font-medium text-[11px] gap-1 shadow-xs">
            <CheckCircle2 className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
            Approved
          </Badge>
        );
      case "PENDING_APPROVAL":
        return (
          <Badge className="bg-amber-100 text-amber-900 dark:bg-amber-950/70 dark:text-amber-300 border-amber-300/60 font-medium text-[11px] gap-1 shadow-xs animate-pulse">
            <Clock className="w-3 h-3 text-amber-600 dark:text-amber-400" />
            Pending Review
          </Badge>
        );
      case "RETURNED":
        return (
          <Badge className="bg-orange-100 text-orange-900 dark:bg-orange-950/70 dark:text-orange-300 border-orange-300/60 font-medium text-[11px] gap-1 shadow-xs">
            <RotateCcw className="w-3 h-3 text-orange-600 dark:text-orange-400" />
            Returned to Worker
          </Badge>
        );
      case "DECLINED":
        return (
          <Badge className="bg-rose-100 text-rose-900 dark:bg-rose-950/70 dark:text-rose-300 border-rose-300/60 font-medium text-[11px] gap-1 shadow-xs">
            <XCircle className="w-3 h-3 text-rose-600 dark:text-rose-400" />
            Declined
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-[11px]">
            {status || "Pending"}
          </Badge>
        );
    }
  };

  const renderRiskBadge = (risk) => {
    const r = (risk || "Low").toLowerCase();
    if (r === "high" || r === "critical") {
      return (
        <Badge variant="destructive" className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5">
          {risk} Risk
        </Badge>
      );
    }
    if (r === "medium") {
      return (
        <Badge className="bg-amber-500/15 text-amber-800 dark:text-amber-300 border-amber-500/30 text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5">
          Medium Risk
        </Badge>
      );
    }
    return (
      <Badge variant="secondary" className="text-[10px] font-medium tracking-wider uppercase px-2 py-0.5 text-muted-foreground">
        Low Risk
      </Badge>
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      <PageHeader
        title="Clients Directory"
        subtitle="Canonical human identity records and service delivery context for CRBCL children, youth, and families"
        actions={
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setIsAddModalOpen(true)}
              className="shadow-sm font-medium"
            >
              <Plus className="w-4 h-4 mr-2" /> Add Client
            </Button>
          </div>
        }
      />

      {/* Control Bar: Search & Status Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search clients by name, #11-digit ID, nation, or email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-10 shadow-2xs"
          />
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
          <TabsList className="grid grid-cols-4 h-10 bg-muted/60 p-1">
            <TabsTrigger value="ALL" className="text-xs px-3">
              All ({counts.all})
            </TabsTrigger>
            <TabsTrigger value="APPROVED" className="text-xs px-3">
              Approved ({counts.approved})
            </TabsTrigger>
            <TabsTrigger value="PENDING_APPROVAL" className="text-xs px-3">
              Pending ({counts.pending})
            </TabsTrigger>
            <TabsTrigger value="RETURNED" className="text-xs px-3">
              Returned ({counts.returned})
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-[50vh] space-y-3">
          <div className="w-9 h-9 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-xs text-muted-foreground font-medium">Loading canonical client records...</p>
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Users}
          title={search ? "No matching clients found" : "No clients in this view"}
          description={
            search
              ? `No records match "${search}". Try adjusting your filters or search keywords.`
              : "Propose a new client to initiate the supervisor approval intake workflow."
          }
          action={
            <Button onClick={() => setIsAddModalOpen(true)}>
              <Plus className="w-4 h-4 mr-2" /> Add Client
            </Button>
          }
        />
      ) : (
        /* Photo-Forward Client Card Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filtered.map((c) => {
            const ageText = calculateAge(c.date_of_birth);
            const initials = `${c.first_name?.[0] || ""}${c.last_name?.[0] || "?"}`;

            return (
              <Link
                key={c.id}
                to={`/clients/${c.id}`}
                className="group relative bg-card hover:bg-muted/15 border border-border/80 hover:border-primary/50 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all duration-200 flex flex-col justify-between focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 no-underline text-inherit block"
              >
                <div>
                  {/* Top Row: Photo, Name, Person ID, Approval Badge */}
                  <div className="flex items-start gap-4">
                    {/* Photo-Forward Portrait */}
                    <Avatar className="h-16 w-16 rounded-2xl border-2 border-background shadow-xs shrink-0 ring-1 ring-border group-hover:scale-102 transition-transform duration-200">
                      <AvatarImage
                        src={c.photo_url}
                        alt={`${c.first_name} ${c.last_name}`}
                        className="object-cover"
                      />
                      <AvatarFallback className="rounded-2xl text-base font-bold bg-gradient-to-br from-primary/20 via-primary/10 to-primary/5 text-primary">
                        {initials}
                      </AvatarFallback>
                    </Avatar>

                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0">
                          <h3 className="font-bold text-base text-foreground leading-snug truncate group-hover:text-primary transition-colors">
                            {c.first_name} {c.last_name}
                          </h3>
                        </div>
                        {renderApprovalBadge(c.approval_status)}
                      </div>

                      {/* Canonical 10-digit ID */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge
                          variant="outline"
                          className="font-mono text-[11px] font-semibold bg-muted/40 border-muted-foreground/20 text-foreground/90 tracking-tight"
                        >
                          #{c.person_id_number || "PENDING-ID"}
                        </Badge>
                        {renderRiskBadge(c.risk_level)}
                      </div>

                      <p className="text-xs text-muted-foreground truncate pt-0.5">
                        {c.indigenous_identity || "Indigenous"}
                        {c.band_nation ? ` • ${c.band_nation}` : ""}
                      </p>
                    </div>
                  </div>

                  {/* Demographic & Contact Metadata */}
                  <div className="mt-4 pt-3.5 border-t border-border/60 grid grid-cols-2 gap-y-2 gap-x-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5 truncate">
                      <Calendar className="w-3.5 h-3.5 shrink-0 text-muted-foreground/70" />
                      <span className="truncate">
                        {c.date_of_birth ? `${c.date_of_birth} ${ageText ? `(${ageText})` : ""}` : "DOB Unknown"}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 truncate">
                      <MapPin className="w-3.5 h-3.5 shrink-0 text-muted-foreground/70" />
                      <span className="truncate">{c.city || "Regina"}, {c.province || "SK"}</span>
                    </div>

                    {c.phone && (
                      <div className="flex items-center gap-1.5 truncate">
                        <Phone className="w-3.5 h-3.5 shrink-0 text-muted-foreground/70" />
                        <span className="truncate">{c.phone}</span>
                      </div>
                    )}

                    {c.email && (
                      <div className="flex items-center gap-1.5 truncate">
                        <Mail className="w-3.5 h-3.5 shrink-0 text-muted-foreground/70" />
                        <span className="truncate">{c.email}</span>
                      </div>
                    )}
                  </div>

                  {/* Context / Submission Notes */}
                  {c.submission_notes && (
                    <div className="mt-3 p-2 rounded-lg bg-muted/30 text-[11px] text-muted-foreground line-clamp-2 italic border border-border/40">
                      &quot;{c.submission_notes}&quot;
                    </div>
                  )}
                </div>

                {/* Card Footer: Submitter / Approval Audit & Arrow Action */}
                <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-[11px] text-muted-foreground">
                  <div className="truncate">
                    {c.approval_status === "PENDING_APPROVAL" && c.submitted_by_name ? (
                      <span>Submitted by {c.submitted_by_name}</span>
                    ) : c.approval_status === "APPROVED" && c.decided_by_name ? (
                      <span>Approved by {c.decided_by_name}</span>
                    ) : (
                      <span>Status: {c.status || "Active"}</span>
                    )}
                  </div>

                  <div className="flex items-center text-primary font-medium group-hover:translate-x-1 transition-transform">
                    <span>View Profile</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {/* Unified Add Client Modal */}
      <AddClientModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => {
          loadClients();
        }}
      />
    </div>
  );
}
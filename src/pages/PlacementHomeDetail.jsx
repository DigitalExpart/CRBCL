import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  Home,
  ArrowLeft,
  Users,
  Award,
  ShieldCheck,
  ClipboardList,
  Eye,
  PhoneCall,
  Bed,
  FileText,
  Clock,
  Plus,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  MapPin,
  Mail,
  Phone,
  Edit,
  Archive,
  RefreshCw,
  Trash2,
  Lock,
  FileCheck,
} from "lucide-react";
import { placementHomesApi } from "@/api/placementHomes";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { toast } from "react-hot-toast";

export default function PlacementHomeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [home, setHome] = useState(null);
  const [backgroundChecks, setBackgroundChecks] = useState([]);
  const [placementHistory, setPlacementHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Modals state
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [memberForm, setMemberForm] = useState({
    person_id: "",
    role: "PRIMARY_CAREGIVER",
    start_date: new Date().toISOString().split("T")[0],
    notes: "",
  });

  const [showRenewModal, setShowRenewModal] = useState(false);
  const [renewForm, setRenewForm] = useState({
    new_license_number: "",
    license_type: "STANDARD_FOSTER",
    effective_date: new Date().toISOString().split("T")[0],
    expiry_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
    issuing_authority: "Ministry of Social Services / First Nation Authority",
    max_capacity: 2,
    conditions: "",
    notes: "",
  });

  const [showVisitModal, setShowVisitModal] = useState(false);
  const [visitForm, setVisitForm] = useState({
    visit_date: new Date().toISOString().split("T")[0],
    visit_type: "ROUTINE_INSPECTION",
    purpose: "",
    summary: "",
    observations: "",
    follow_up_required: false,
    follow_up_due_date: "",
    status: "COMPLETED",
  });

  const [showContactModal, setShowContactModal] = useState(false);
  const [contactForm, setContactForm] = useState({
    contact_type: "PHONE",
    contact_date: new Date().toISOString(),
    duration_minutes: 15,
    subject: "",
    notes: "",
    follow_up_action: "",
  });

  const [submitting, setSubmitting] = useState(false);

  const fetchHomeData = async () => {
    try {
      setLoading(true);
      const [homeRes, bgRes, historyRes] = await Promise.all([
        placementHomesApi.get(id),
        placementHomesApi.getBackgroundChecks(id),
        placementHomesApi.getPlacementHistory(id),
      ]);
      setHome(homeRes.data);
      setBackgroundChecks(bgRes.data || []);
      setPlacementHistory(historyRes.data || []);
      if (homeRes.data.total_capacity) {
        setRenewForm((prev) => ({ ...prev, max_capacity: homeRes.data.total_capacity }));
      }
    } catch (err) {
      toast.error("Failed to load placement home details.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHomeData();
  }, [id]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!memberForm.person_id) {
      toast.error("Person ID is required.");
      return;
    }
    try {
      setSubmitting(true);
      await placementHomesApi.addMember(id, memberForm);
      toast.success("Household member added successfully.");
      setShowMemberModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add member.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRenewLicense = async (e) => {
    e.preventDefault();
    if (!renewForm.new_license_number.trim()) {
      toast.error("License number is required.");
      return;
    }
    try {
      setSubmitting(true);
      await placementHomesApi.renewLicense(id, renewForm);
      toast.success("Licence renewed successfully.");
      setShowRenewModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to renew licence.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateVisit = async (e) => {
    e.preventDefault();
    if (!visitForm.purpose.trim() || !visitForm.summary.trim()) {
      toast.error("Purpose and Summary are required.");
      return;
    }
    try {
      setSubmitting(true);
      await placementHomesApi.createVisit(id, visitForm);
      toast.success("Inspection / Visit logged successfully.");
      setShowVisitModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to log visit.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateContact = async (e) => {
    e.preventDefault();
    if (!contactForm.subject.trim() || !contactForm.notes.trim()) {
      toast.error("Subject and Notes are required.");
      return;
    }
    try {
      setSubmitting(true);
      await placementHomesApi.createContactLog(id, contactForm);
      toast.success("Caregiver contact log recorded.");
      setShowContactModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to log contact.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleArchive = async () => {
    if (!window.confirm("Are you sure you want to archive / close this placement home?")) return;
    try {
      await placementHomesApi.archive(id);
      toast.success("Placement home archived.");
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to archive home.");
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400">
        Loading placement home profile...
      </div>
    );
  }

  if (!home) {
    return (
      <div className="p-8 text-center text-slate-400">
        Placement home not found.
      </div>
    );
  }

  const occupancyPercent = home.total_capacity > 0 ? Math.min(100, Math.round((home.occupied_beds / home.total_capacity) * 100)) : 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Back button & Header */}
      <div className="flex flex-col gap-4">
        <Link to="/placement-homes" className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 transition-colors w-fit">
          <ArrowLeft className="h-4 w-4" /> Back to Placement Homes Directory
        </Link>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{home.name}</h1>
                <Badge variant="outline" className="text-xs font-mono">{home.home_code}</Badge>
                <Badge
                  className={
                    home.status === "ACTIVE"
                      ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                      : "bg-slate-500/10 text-slate-700 dark:text-slate-400"
                  }
                >
                  {home.status}
                </Badge>
                <Badge
                  className={
                    home.licensing_status === "ACTIVE"
                      ? "bg-indigo-500/10 text-indigo-700 dark:text-indigo-400"
                      : "bg-amber-500/10 text-amber-700 dark:text-amber-400"
                  }
                >
                  Licence: {home.licensing_status}
                </Badge>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 flex-wrap">
                {home.community && <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {home.community} ({home.city})</span>}
                {home.primary_caregiver_name && <span className="flex items-center gap-1"><Users className="h-3.5 w-3.5" /> Primary: {home.primary_caregiver_name}</span>}
                {home.phone && <span className="flex items-center gap-1"><Phone className="h-3.5 w-3.5" /> {home.phone}</span>}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2 flex-wrap">
              <Button size="sm" variant="outline" onClick={() => setShowRenewModal(true)} className="gap-1.5">
                <RefreshCw className="h-4 w-4" /> Renew Licence
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowVisitModal(true)} className="gap-1.5">
                <Eye className="h-4 w-4" /> Log Visit
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowContactModal(true)} className="gap-1.5">
                <PhoneCall className="h-4 w-4" /> Log Contact
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowMemberModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Add Member
              </Button>
            </div>
          </div>

          {/* Capacity Progress Bar */}
          <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
            <div className="md:col-span-3 space-y-2">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-slate-600 dark:text-slate-400">Live Bed Capacity Allocation</span>
                <span className="text-slate-900 dark:text-slate-100 font-bold">
                  {home.occupied_beds} Occupied / {home.total_capacity} Approved ({occupancyPercent}%)
                </span>
              </div>
              <Progress value={occupancyPercent} className="h-2.5" />
            </div>
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg border border-slate-200 dark:border-slate-700 text-center">
              <div className="text-xs text-slate-500 font-medium">Available Beds</div>
              <div className={`text-xl font-extrabold mt-0.5 ${home.available_beds > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                {home.available_beds}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-1 flex-wrap h-auto">
          <TabsTrigger value="overview" className="gap-1.5"><Home className="h-4 w-4" /> Overview</TabsTrigger>
          <TabsTrigger value="members" className="gap-1.5"><Users className="h-4 w-4" /> Members ({home.members?.length || 0})</TabsTrigger>
          <TabsTrigger value="licensing" className="gap-1.5"><Award className="h-4 w-4" /> Licensing ({home.licenses?.length || 0})</TabsTrigger>
          <TabsTrigger value="background" className="gap-1.5"><ShieldCheck className="h-4 w-4" /> Background Checks ({backgroundChecks.length})</TabsTrigger>
          <TabsTrigger value="visits" className="gap-1.5"><Eye className="h-4 w-4" /> Visits & Inspections ({home.visits?.length || 0})</TabsTrigger>
          <TabsTrigger value="contacts" className="gap-1.5"><PhoneCall className="h-4 w-4" /> Contact Logs ({home.contact_logs?.length || 0})</TabsTrigger>
          <TabsTrigger value="placements" className="gap-1.5"><Bed className="h-4 w-4" /> Placements ({placementHistory.length})</TabsTrigger>
        </TabsList>

        {/* 1. OVERVIEW TAB */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-indigo-600" /> Physical Location & Coordinates
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5 text-sm">
                <div>
                  <div className="text-xs text-slate-500">Street Address</div>
                  <div className="font-medium text-slate-800 dark:text-slate-200">{home.address_line_1 || "—"} {home.address_line_2}</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-xs text-slate-500">City / Town</div>
                    <div className="font-medium text-slate-800 dark:text-slate-200">{home.city}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500">Province & Postal</div>
                    <div className="font-medium text-slate-800 dark:text-slate-200">{home.province} {home.postal_code}</div>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">First Nation / Community</div>
                  <div className="font-medium text-slate-800 dark:text-slate-200">{home.community || "—"}</div>
                </div>
                {home.latitude && home.longitude && (
                  <div className="pt-2 text-xs text-slate-500">
                    GPS: {home.latitude.toFixed(4)}, {home.longitude.toFixed(4)}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <ClipboardList className="h-4 w-4 text-indigo-600" /> Intake & Criteria Notes
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <div className="text-xs text-slate-500">Placement Acceptance Criteria</div>
                  <p className="mt-1 text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                    {home.intake_criteria_notes || "No custom criteria restrictions noted. Accepts general placements according to licensing specifications."}
                  </p>
                </div>
                <div>
                  <div className="text-xs text-slate-500">General Notes</div>
                  <p className="mt-1 text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                    {home.notes || "No general operational notes."}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 2. MEMBERS TAB */}
        <TabsContent value="members" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Household Members & Caregivers</CardTitle>
                <CardDescription>All adult caregivers, youth residents, and authorized household members.</CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowMemberModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Add Member
              </Button>
            </CardHeader>
            <CardContent>
              {home.members?.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No household members recorded yet.</div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {home.members.map((m) => (
                    <div key={m.id} className="py-3 flex items-center justify-between">
                      <div className="space-y-0.5">
                        <div className="font-semibold text-slate-900 dark:text-slate-100">{m.person_name || "Person #" + m.person_id}</div>
                        <div className="text-xs text-slate-500">
                          Role: <Badge variant="outline" className="text-[11px] font-normal">{m.role.replace(/_/g, " ")}</Badge> • Active since {m.start_date}
                        </div>
                        {m.notes && <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">{m.notes}</div>}
                      </div>
                      <Badge className={m.is_active ? "bg-emerald-500/10 text-emerald-700" : "bg-slate-500/10 text-slate-700"}>
                        {m.is_active ? "Active Member" : "Former"}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 3. LICENSING TAB */}
        <TabsContent value="licensing" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Licensing & Regulatory History</CardTitle>
                <CardDescription>Full immutable audit of issued and historical licences without destructive overwriting.</CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowRenewModal(true)} className="gap-1.5">
                <RefreshCw className="h-4 w-4" /> Renew / Issue New Licence
              </Button>
            </CardHeader>
            <CardContent>
              {home.licenses?.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No licence records recorded yet.</div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {home.licenses.map((lic) => (
                    <div key={lic.id} className="py-4 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 dark:text-slate-100">{lic.license_number}</span>
                          <Badge variant="outline">{lic.license_type}</Badge>
                          <Badge className={lic.status === "ACTIVE" ? "bg-emerald-500/10 text-emerald-700" : "bg-slate-500/10 text-slate-700"}>
                            {lic.status}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-500 font-mono">
                          Effective: {lic.effective_date} → Expiry: {lic.expiry_date}
                        </div>
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400">
                        Authority: {lic.issuing_authority} {lic.max_capacity && `• Max Capacity: ${lic.max_capacity}`}
                      </div>
                      {lic.conditions && (
                        <div className="text-xs bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 p-2 rounded border border-amber-200 dark:border-amber-900 mt-1">
                          <strong>Conditions:</strong> {lic.conditions}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 4. BACKGROUND SCREENINGS TAB */}
        <TabsContent value="background" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader>
              <CardTitle className="text-base">Household Background Screening Summary</CardTitle>
              <CardDescription>Criminal record checks, child protection checks, and clearances for all home members.</CardDescription>
            </CardHeader>
            <CardContent>
              {backgroundChecks.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No background checks linked to members.</div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {backgroundChecks.map((chk) => (
                    <div key={chk.member_id} className="py-3 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-slate-900 dark:text-slate-100">{chk.member_name}</div>
                        <div className="text-xs text-slate-500">Role: {chk.role} • Clearance #: {chk.clearance_number || "Pending"}</div>
                        {chk.expiry_date && (
                          <div className={`text-xs mt-1 ${chk.is_expired ? 'text-red-600 font-bold' : 'text-slate-500'}`}>
                            Expiry: {chk.expiry_date} {chk.is_expired ? "(EXPIRED)" : ""}
                          </div>
                        )}
                      </div>
                      <Badge className={chk.is_eligible ? "bg-emerald-500/10 text-emerald-700" : "bg-red-500/10 text-red-700"}>
                        {chk.is_eligible ? "Eligible for Placement" : "Screening Incomplete / Expired"}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 5. VISITS & INSPECTIONS TAB */}
        <TabsContent value="visits" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Inspections & Support Visits</CardTitle>
                <CardDescription>Routine physical inspections, unannounced safety checks, and annual reviews.</CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowVisitModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Log Visit
              </Button>
            </CardHeader>
            <CardContent>
              {home.visits?.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No inspection or visit records yet.</div>
              ) : (
                <div className="space-y-4">
                  {home.visits.map((v) => (
                    <div key={v.id} className="p-3.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                          <span>{v.purpose}</span>
                          <Badge variant="outline">{v.visit_type}</Badge>
                        </div>
                        <div className="text-xs text-slate-500 font-mono">Date: {v.visit_date}</div>
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400">Logged by: {v.worker_name || "Caseworker"}</div>
                      <p className="text-xs text-slate-800 dark:text-slate-200 mt-1 whitespace-pre-wrap">{v.summary}</p>
                      {v.follow_up_required && (
                        <div className="text-xs bg-amber-500/10 text-amber-700 dark:text-amber-400 p-2 rounded mt-2 border border-amber-200 dark:border-amber-800 flex items-center gap-1.5">
                          <AlertTriangle className="h-3.5 w-3.5" /> Follow-up Required by: {v.follow_up_due_date || "TBD"}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 6. CONTACT LOGS TAB */}
        <TabsContent value="contacts" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Caregiver Communication Logs</CardTitle>
                <CardDescription>Direct calls, text messages, in-person check-ins, and coordination notes.</CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowContactModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Log Contact
              </Button>
            </CardHeader>
            <CardContent>
              {home.contact_logs?.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No contact logs recorded yet.</div>
              ) : (
                <div className="space-y-3">
                  {home.contact_logs.map((c) => (
                    <div key={c.id} className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 space-y-1">
                      <div className="flex items-center justify-between">
                        <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                          <Phone className="h-3.5 w-3.5 text-indigo-600" />
                          <span>{c.subject}</span>
                          <Badge variant="outline">{c.contact_type}</Badge>
                        </div>
                        <div className="text-xs text-slate-500 font-mono">
                          {new Date(c.contact_date).toLocaleString()} {c.duration_minutes && `(${c.duration_minutes}m)`}
                        </div>
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400">Recorded by: {c.worker_name}</div>
                      <p className="text-xs text-slate-800 dark:text-slate-200 mt-1 whitespace-pre-wrap">{c.notes}</p>
                      {c.follow_up_action && (
                        <div className="text-xs text-indigo-600 dark:text-indigo-400 font-medium mt-1">
                          Action: {c.follow_up_action}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 7. PLACEMENTS HISTORY TAB */}
        <TabsContent value="placements" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader>
              <CardTitle className="text-base">Resident Placement History</CardTitle>
              <CardDescription>Current and historical children placed into this home. Sensitive child identities are automatically redacted if restricted.</CardDescription>
            </CardHeader>
            <CardContent>
              {placementHistory.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No placement episodes recorded for this home.</div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {placementHistory.map((p) => (
                    <div key={p.placement_id} className="py-3 flex items-center justify-between">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          {p.is_redacted ? (
                            <span className="font-mono text-xs text-slate-500 flex items-center gap-1">
                              <Lock className="h-3.5 w-3.5 text-amber-600" /> {p.child_name}
                            </span>
                          ) : (
                            <span className="font-semibold text-slate-900 dark:text-slate-100">{p.child_name}</span>
                          )}
                          <Badge variant="outline">{p.placement_type}</Badge>
                          <Badge className={p.status === "ACTIVE" ? "bg-emerald-500/10 text-emerald-700" : "bg-slate-500/10 text-slate-700"}>
                            {p.status}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-500">
                          Case: {p.case_number} • Start: {p.start_date} {p.end_date ? `→ End: ${p.end_date}` : "→ Active"} ({p.duration_days} days)
                        </div>
                        {p.discharge_reason && (
                          <div className="text-xs text-slate-600 dark:text-slate-400">
                            Discharge Reason: {p.discharge_reason}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Member Modal */}
      <Dialog open={showMemberModal} onOpenChange={setShowMemberModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Household Member / Caregiver</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddMember} className="space-y-3 pt-2">
            <div className="space-y-1">
              <Label>Person UUID *</Label>
              <Input
                required
                placeholder="Enter client / caregiver person UUID"
                value={memberForm.person_id}
                onChange={(e) => setMemberForm({ ...memberForm, person_id: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Role</Label>
              <Select value={memberForm.role} onValueChange={(v) => setMemberForm({ ...memberForm, role: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="PRIMARY_CAREGIVER">Primary Caregiver</SelectItem>
                  <SelectItem value="SECONDARY_CAREGIVER">Secondary Caregiver</SelectItem>
                  <SelectItem value="ADULT_HOUSEHOLD_MEMBER">Adult Household Member</SelectItem>
                  <SelectItem value="YOUTH_HOUSEHOLD_MEMBER">Youth Household Member</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Start Date</Label>
              <Input
                type="date"
                value={memberForm.start_date}
                onChange={(e) => setMemberForm({ ...memberForm, start_date: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <Textarea
                value={memberForm.notes}
                onChange={(e) => setMemberForm({ ...memberForm, notes: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowMemberModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Save Member</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Licence Renewal Modal */}
      <Dialog open={showRenewModal} onOpenChange={setShowRenewModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Renew Placement Home Licence</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleRenewLicense} className="space-y-3 pt-2">
            <div className="space-y-1">
              <Label>New License Number *</Label>
              <Input
                required
                placeholder="e.g. LIC-2026-009"
                value={renewForm.new_license_number}
                onChange={(e) => setRenewForm({ ...renewForm, new_license_number: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Effective Date</Label>
                <Input
                  type="date"
                  value={renewForm.effective_date}
                  onChange={(e) => setRenewForm({ ...renewForm, effective_date: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Expiry Date</Label>
                <Input
                  type="date"
                  value={renewForm.expiry_date}
                  onChange={(e) => setRenewForm({ ...renewForm, expiry_date: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Approved Max Bed Capacity</Label>
              <Input
                type="number"
                min="1"
                value={renewForm.max_capacity}
                onChange={(e) => setRenewForm({ ...renewForm, max_capacity: parseInt(e.target.value) || 1 })}
              />
            </div>
            <div className="space-y-1">
              <Label>Licence Conditions</Label>
              <Textarea
                placeholder="Conditions of approval or special terms..."
                value={renewForm.conditions}
                onChange={(e) => setRenewForm({ ...renewForm, conditions: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowRenewModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Renew Licence</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Visit Modal */}
      <Dialog open={showVisitModal} onOpenChange={setShowVisitModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Log Inspection or Support Visit</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateVisit} className="space-y-3 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Visit Date</Label>
                <Input
                  type="date"
                  value={visitForm.visit_date}
                  onChange={(e) => setVisitForm({ ...visitForm, visit_date: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Visit Type</Label>
                <Select value={visitForm.visit_type} onValueChange={(v) => setVisitForm({ ...visitForm, visit_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ROUTINE_INSPECTION">Routine Inspection</SelectItem>
                    <SelectItem value="UNANNOUNCED_VISIT">Unannounced Visit</SelectItem>
                    <SelectItem value="ANNUAL_REVIEW">Annual Review</SelectItem>
                    <SelectItem value="SUPPORT_CHECKIN">Support Check-in</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1">
              <Label>Purpose *</Label>
              <Input
                required
                placeholder="e.g. Quarterly health & fire safety inspection"
                value={visitForm.purpose}
                onChange={(e) => setVisitForm({ ...visitForm, purpose: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Inspection Summary *</Label>
              <Textarea
                required
                placeholder="Overview of physical dwelling and caregiver interview..."
                value={visitForm.summary}
                onChange={(e) => setVisitForm({ ...visitForm, summary: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Follow-up Required?</Label>
              <Select
                value={visitForm.follow_up_required ? "yes" : "no"}
                onValueChange={(v) => setVisitForm({ ...visitForm, follow_up_required: v === "yes" })}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="no">No</SelectItem>
                  <SelectItem value="yes">Yes</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {visitForm.follow_up_required && (
              <div className="space-y-1">
                <Label>Follow-up Due Date</Label>
                <Input
                  type="date"
                  value={visitForm.follow_up_due_date}
                  onChange={(e) => setVisitForm({ ...visitForm, follow_up_due_date: e.target.value })}
                />
              </div>
            )}
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowVisitModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Log Visit</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Contact Log Modal */}
      <Dialog open={showContactModal} onOpenChange={setShowContactModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Log Caregiver Communication</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateContact} className="space-y-3 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Contact Type</Label>
                <Select value={contactForm.contact_type} onValueChange={(v) => setContactForm({ ...contactForm, contact_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PHONE">Phone Call</SelectItem>
                    <SelectItem value="IN_PERSON">In Person</SelectItem>
                    <SelectItem value="VIDEO">Video Call</SelectItem>
                    <SelectItem value="EMAIL">Email</SelectItem>
                    <SelectItem value="SMS">SMS / Text</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Duration (Minutes)</Label>
                <Input
                  type="number"
                  value={contactForm.duration_minutes}
                  onChange={(e) => setContactForm({ ...contactForm, duration_minutes: parseInt(e.target.value) || 15 })}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Subject *</Label>
              <Input
                required
                placeholder="e.g. Caregiver support and school transportation"
                value={contactForm.subject}
                onChange={(e) => setContactForm({ ...contactForm, subject: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Discussion Notes *</Label>
              <Textarea
                required
                placeholder="Summary of conversation and updates..."
                value={contactForm.notes}
                onChange={(e) => setContactForm({ ...contactForm, notes: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Follow-up Action</Label>
              <Input
                placeholder="e.g. Forward request to supervisor"
                value={contactForm.follow_up_action}
                onChange={(e) => setContactForm({ ...contactForm, follow_up_action: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowContactModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Save Contact Log</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

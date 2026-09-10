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
  Plus,
  AlertTriangle,
  MapPin,
  Phone,
  RefreshCw,
  Lock,
  ShieldAlert,
  GraduationCap,
  Wrench,
  CheckCircle,
  XCircle,
  FileText,
  Calendar,
  FileWarning,
  HeartHandshake,
  DollarSign,
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
  const [assessments, setAssessments] = useState([]);
  const [clearances, setClearances] = useState([]);
  const [trainings, setTrainings] = useState([]);
  const [complianceSummary, setComplianceSummary] = useState(null);
  const [monitorings, setMonitorings] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [supports, setSupports] = useState([]);
  const [financeSummary, setFinanceSummary] = useState(null);
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
    placement_restrictions: "",
    min_age: "",
    max_age: "",
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
    findings: "",
    deficiencies: "",
    corrective_actions: "",
    corrective_action_due_date: "",
    corrective_action_status: "NONE",
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

  // Sprint 2 Modals State
  const [showAssessModal, setShowAssessModal] = useState(false);
  const [assessForm, setAssessForm] = useState({
    title: "Caregiver & Home Study Assessment",
    assessment_type: "HOME_STUDY",
    primary_person_id: "",
    notes: "",
  });

  const [showClearanceModal, setShowClearanceModal] = useState(false);
  const [clearanceForm, setClearanceForm] = useState({
    subject_id: "",
    subject_name: "",
    check_type: "CRIMINAL_RECORD_CHECK",
    request_date: new Date().toISOString().split("T")[0],
    conducted_by_agency: "RCMP / Regina Police Service",
    clearance_reference_number: "",
    risk_assessment_notes: "",
  });

  const [showTrainingModal, setShowTrainingModal] = useState(false);
  const [trainingForm, setTrainingForm] = useState({
    person_id: "",
    training_type: "PRE_SERVICE_PRIDE",
    course_name: "PRIDE Pre-Service Program",
    provider_name: "Saskatchewan Foster Families Association",
    completion_date: new Date().toISOString().split("T")[0],
    expiry_date: "",
    notes: "",
  });

  const [showCorrectiveModal, setShowCorrectiveModal] = useState(false);
  const [selectedVisit, setSelectedVisit] = useState(null);
  const [correctiveForm, setCorrectiveForm] = useState({
    corrective_action_status: "COMPLETED",
    findings: "",
    deficiencies: "",
    corrective_actions: "",
    corrective_action_due_date: "",
    completed_date: new Date().toISOString().split("T")[0],
  });

  // Sprint 3: Modals State
  const [showMonitoringModal, setShowMonitoringModal] = useState(false);
  const [monitoringForm, setMonitoringForm] = useState({
    visit_date: new Date().toISOString().split("T")[0],
    visit_type: "HOME_VISIT",
    contact_method: "IN_PERSON",
    duration_minutes: 45,
    safe_sleep_verified: true,
    caregiver_wellbeing_notes: "",
    follow_up_required: false,
    follow_up_notes: "",
    observations: "",
  });

  const [showComplaintModal, setShowComplaintModal] = useState(false);
  const [complaintForm, setComplaintForm] = useState({
    allegation_type: "CARE_QUALITY",
    allegation_summary: "",
    incident_date: new Date().toISOString().split("T")[0],
    complainant_type: "CASEWORKER",
    complainant_name: "",
    is_sensitive: false,
  });

  const [showSupportModal, setShowSupportModal] = useState(false);
  const [supportForm, setSupportForm] = useState({
    support_type: "RESPITE",
    description: "",
    requested_amount: "",
    service_request_id: "",
  });

  const [submitting, setSubmitting] = useState(false);

  const fetchHomeData = async () => {
    try {
      setLoading(true);
      const [
        homeRes,
        bgRes,
        historyRes,
        assessRes,
        clearancesRes,
        trainingRes,
        compRes,
        monitoringRes,
        complaintRes,
        supportRes,
        financeRes,
      ] = await Promise.all([
        placementHomesApi.get(id),
        placementHomesApi.getBackgroundChecks(id),
        placementHomesApi.getPlacementHistory(id),
        placementHomesApi.getAssessments(id).catch(() => ({ data: [] })),
        placementHomesApi.getClearances(id).catch(() => ({ data: [] })),
        placementHomesApi.getTrainings(id).catch(() => ({ data: [] })),
        placementHomesApi.getTrainingCompliance(id).catch(() => ({ data: null })),
        placementHomesApi.getMonitoring({ home_id: id }).catch(() => ({ data: [] })),
        placementHomesApi.getComplaints({ home_id: id }).catch(() => ({ data: [] })),
        placementHomesApi.getSupports({ home_id: id }).catch(() => ({ data: [] })),
        placementHomesApi.getFinanceSummary(id).catch(() => ({ data: null })),
      ]);
      setHome(homeRes.data);
      setBackgroundChecks(bgRes.data || []);
      setPlacementHistory(historyRes.data || []);
      setAssessments(assessRes.data || []);
      setClearances(clearancesRes.data || []);
      setTrainings(trainingRes.data || []);
      setComplianceSummary(compRes.data || null);
      setMonitorings(monitoringRes.data || []);
      setComplaints(complaintRes.data || []);
      setSupports(supportRes.data || []);
      setFinanceSummary(financeRes?.data || null);

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

  const handleCreateAssessment = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await placementHomesApi.createAssessment(id, {
        title: assessForm.title,
        assessment_type: assessForm.assessment_type,
        placement_home_id: id,
        primary_person_id: assessForm.primary_person_id || undefined,
        notes: assessForm.notes || undefined,
      });
      toast.success("Caregiver assessment initiated.");
      setShowAssessModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to initiate assessment.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateClearance = async (e) => {
    e.preventDefault();
    if (!clearanceForm.subject_id) {
      toast.error("Caregiver Person ID is required for clearance.");
      return;
    }
    try {
      setSubmitting(true);
      await placementHomesApi.createClearance(id, {
        subject_type: "PERSON",
        subject_id: clearanceForm.subject_id,
        subject_name: clearanceForm.subject_name || "Caregiver Subject",
        check_type: clearanceForm.check_type,
        placement_home_id: id,
        request_date: clearanceForm.request_date,
        conducted_by_agency: clearanceForm.conducted_by_agency,
        clearance_reference_number: clearanceForm.clearance_reference_number,
        risk_assessment_notes: clearanceForm.risk_assessment_notes,
      });
      toast.success("Clearance check requested.");
      setShowClearanceModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to record clearance.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateTraining = async (e) => {
    e.preventDefault();
    if (!trainingForm.person_id) {
      toast.error("Caregiver Person ID is required.");
      return;
    }
    try {
      setSubmitting(true);
      await placementHomesApi.createTraining(id, {
        person_id: trainingForm.person_id,
        placement_home_id: id,
        training_type: trainingForm.training_type,
        course_name: trainingForm.course_name,
        provider_name: trainingForm.provider_name,
        completion_date: trainingForm.completion_date,
        expiry_date: trainingForm.expiry_date || undefined,
        notes: trainingForm.notes || undefined,
      });
      toast.success("Caregiver training completion recorded.");
      setShowTrainingModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to record training.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenCorrectiveModal = (visit) => {
    setSelectedVisit(visit);
    setCorrectiveForm({
      corrective_action_status: visit.corrective_action_status || "COMPLETED",
      findings: visit.findings || "",
      deficiencies: visit.deficiencies || "",
      corrective_actions: visit.corrective_actions || "",
      corrective_action_due_date: visit.corrective_action_due_date || "",
      completed_date: visit.completed_date || new Date().toISOString().split("T")[0],
    });
    setShowCorrectiveModal(true);
  };

  const handleUpdateCorrectiveAction = async (e) => {
    e.preventDefault();
    if (!selectedVisit) return;
    try {
      setSubmitting(true);
      await placementHomesApi.updateCorrectiveAction(id, selectedVisit.id, correctiveForm);
      toast.success("Inspection corrective action updated.");
      setShowCorrectiveModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update corrective action.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateMonitoring = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await placementHomesApi.createMonitoring({
        placement_home_id: id,
        ...monitoringForm,
      });
      toast.success("Monitoring visit recorded.");
      setShowMonitoringModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to record monitoring visit.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateComplaint = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await placementHomesApi.createComplaint({
        placement_home_id: id,
        ...complaintForm,
      });
      toast.success("Complaint registered.");
      setShowComplaintModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to register complaint.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateSupport = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await placementHomesApi.createSupport({
        placement_home_id: id,
        support_type: supportForm.support_type,
        description: supportForm.description,
        requested_amount: supportForm.requested_amount ? parseFloat(supportForm.requested_amount) : undefined,
        service_request_id: supportForm.service_request_id || undefined,
      });
      toast.success("Caregiver support requested.");
      setShowSupportModal(false);
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create support request.");
    } finally {
      setSubmitting(false);
    }
  };

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

  const handleEndMembership = async (memberId) => {
    try {
      await placementHomesApi.updateMember(id, memberId, {
        is_active: false,
        end_date: new Date().toISOString().split("T")[0],
      });
      toast.success("Household membership ended and preserved in historical records.");
      fetchHomeData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to end membership.");
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
              <Button size="sm" variant="outline" onClick={() => setShowMonitoringModal(true)} className="gap-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200">
                <Calendar className="h-4 w-4" /> Log Monitoring
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowVisitModal(true)} className="gap-1.5">
                <Eye className="h-4 w-4" /> Log Inspection
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowComplaintModal(true)} className="gap-1.5 bg-rose-50 text-rose-700 hover:bg-rose-100 border-rose-200">
                <FileWarning className="h-4 w-4" /> Register Complaint
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowSupportModal(true)} className="gap-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border-indigo-200">
                <HeartHandshake className="h-4 w-4" /> Request Support
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowAssessModal(true)} className="gap-1.5">
                <ClipboardList className="h-4 w-4" /> New Assessment
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowClearanceModal(true)} className="gap-1.5">
                <ShieldCheck className="h-4 w-4" /> Record Clearance
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowTrainingModal(true)} className="gap-1.5">
                <GraduationCap className="h-4 w-4" /> Record Training
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
          <TabsTrigger value="members" className="gap-1.5"><Users className="h-4 w-4" /> Caregivers & Household ({home.members?.length || 0})</TabsTrigger>
          <TabsTrigger value="monitoring" className="gap-1.5"><Calendar className="h-4 w-4" /> Monitoring ({monitorings.length})</TabsTrigger>
          <TabsTrigger value="complaints" className="gap-1.5"><FileWarning className="h-4 w-4" /> Complaints ({complaints.length})</TabsTrigger>
          <TabsTrigger value="supports" className="gap-1.5"><HeartHandshake className="h-4 w-4" /> Supports ({supports.length})</TabsTrigger>
          <TabsTrigger value="assessments" className="gap-1.5"><ClipboardList className="h-4 w-4" /> Assessments ({assessments.length})</TabsTrigger>
          <TabsTrigger value="clearances" className="gap-1.5"><ShieldCheck className="h-4 w-4" /> Clearances ({clearances.length || backgroundChecks.length})</TabsTrigger>
          <TabsTrigger value="training" className="gap-1.5"><GraduationCap className="h-4 w-4" /> Training ({trainings.length})</TabsTrigger>
          <TabsTrigger value="licensing" className="gap-1.5"><Award className="h-4 w-4" /> Licensing ({home.licenses?.length || 0})</TabsTrigger>
          <TabsTrigger value="visits" className="gap-1.5"><Eye className="h-4 w-4" /> Inspections ({home.visits?.length || 0})</TabsTrigger>
          <TabsTrigger value="compliance" className="gap-1.5"><ShieldAlert className="h-4 w-4" /> Compliance</TabsTrigger>
          <TabsTrigger value="contacts" className="gap-1.5"><PhoneCall className="h-4 w-4" /> Contact Logs ({home.contact_logs?.length || 0})</TabsTrigger>
          <TabsTrigger value="placements" className="gap-1.5"><Bed className="h-4 w-4" /> Placements ({placementHistory.length})</TabsTrigger>
          <TabsTrigger value="finance" className="gap-1.5"><DollarSign className="h-4 w-4" /> Finance</TabsTrigger>
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
                          Role: <Badge variant="outline" className="text-[11px] font-normal">{m.role.replace(/_/g, " ")}</Badge> • Active: {m.start_date}{m.end_date ? ` to ${m.end_date}` : ""}
                        </div>
                        {m.notes && <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">{m.notes}</div>}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={m.is_active ? "bg-emerald-500/10 text-emerald-700" : "bg-slate-500/10 text-slate-700"}>
                          {m.is_active ? "Active Member" : "Former"}
                        </Badge>
                        {m.is_active && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-xs text-rose-600 hover:bg-rose-50 h-7"
                            onClick={() => handleEndMembership(m.id)}
                          >
                            End Membership
                          </Button>
                        )}
                      </div>
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

        {/* 3. ASSESSMENTS TAB */}
        <TabsContent value="assessments" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Caregiver & Home Study Assessments</CardTitle>
                <CardDescription>
                  Comprehensive parenting capacity, home environment, cultural safety, strengths, and recommendations.
                </CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowAssessModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> New Assessment
              </Button>
            </CardHeader>
            <CardContent>
              {assessments.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No caregiver assessments recorded yet.</div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {assessments.map((a) => (
                    <div key={a.id} className="py-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900 dark:text-slate-100">{a.title}</span>
                          <Badge variant="outline">{a.assessment_type}</Badge>
                          <Badge
                            className={
                              a.status === "APPROVED" || a.status === "COMPLETED"
                                ? "bg-emerald-500/10 text-emerald-700"
                                : a.status === "IN_PROGRESS"
                                ? "bg-blue-500/10 text-blue-700"
                                : "bg-amber-500/10 text-amber-700"
                            }
                          >
                            {a.status}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-500 font-mono">
                          {a.completed_date ? `Completed: ${a.completed_date}` : `Created: ${new Date(a.created_at).toLocaleDateString()}`}
                        </div>
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-4">
                        <span>Assessor: {a.assessor_name || "Resource Worker"}</span>
                        {a.sections_count && <span>Sections: {a.sections_count}</span>}
                        {a.summary && <span className="italic truncate max-w-md">{a.summary}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 4. CLEARANCES TAB */}
        <TabsContent value="clearances" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Caregiver Screenings & Clearances</CardTitle>
                <CardDescription>
                  Criminal record checks, vulnerable sector checks, CARC, driver abstracts, and reference checks.
                </CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowClearanceModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Record Clearance
              </Button>
            </CardHeader>
            <CardContent>
              {clearances.length === 0 && backgroundChecks.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No clearance records logged for this home.</div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {(clearances.length > 0 ? clearances : backgroundChecks).map((c) => (
                    <div key={c.id || c.member_id} className="py-3 flex items-center justify-between">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900 dark:text-slate-100">{c.person_name || c.member_name}</span>
                          <Badge variant="outline">{c.check_type || "SCREENING"}</Badge>
                          <Badge
                            className={
                              c.status === "PASSED" || c.status === "CLEARED" || c.status === "COMPLETED" || c.is_eligible
                                ? "bg-emerald-500/10 text-emerald-700"
                                : c.status === "PENDING"
                                ? "bg-blue-500/10 text-blue-700"
                                : "bg-rose-500/10 text-rose-700"
                            }
                          >
                            {c.status || (c.is_eligible ? "CLEARED" : "PENDING")}
                          </Badge>
                          {c.renewal_status === "EXPIRED" && (
                            <Badge className="bg-rose-600 text-white">EXPIRED</Badge>
                          )}
                        </div>
                        <div className="text-xs text-slate-500">
                          Ref: {c.clearance_reference_number || c.clearance_number || "—"} • Agency: {c.conducted_by_agency || "Police Service"} • Req: {c.request_date || "—"} {c.expiry_date ? `• Expiry: ${c.expiry_date}` : ""}
                        </div>
                        {c.risk_assessment_notes && (
                          <div className="text-xs text-slate-600 dark:text-slate-400 italic">
                            Notes: {c.risk_assessment_notes}
                          </div>
                        )}
                      </div>
                      <Badge className={c.is_eligible_for_placement || c.is_eligible ? "bg-emerald-500/10 text-emerald-700" : "bg-red-500/10 text-red-700"}>
                        {c.is_eligible_for_placement || c.is_eligible ? "Eligible" : "Not Cleared / Pending"}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 5. TRAINING TAB */}
        <TabsContent value="training" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Caregiver Training Compliance</CardTitle>
                <CardDescription>
                  Tracking mandatory pre-service (PRIDE), CPR/First Aid, Trauma-Informed Care, and Cultural Safety certifications.
                </CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowTrainingModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Record Training
              </Button>
            </CardHeader>
            <CardContent>
              {trainings.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No training completions recorded yet.</div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {trainings.map((t) => (
                    <div key={t.id} className="py-3 flex items-center justify-between">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900 dark:text-slate-100">{t.person_name || "Caregiver"}</span>
                          <Badge variant="outline">{t.training_type}</Badge>
                          <Badge
                            className={
                              t.status === "COMPLETED"
                                ? "bg-emerald-500/10 text-emerald-700"
                                : t.status === "EXPIRED"
                                ? "bg-rose-500/10 text-rose-700"
                                : "bg-amber-500/10 text-amber-700"
                            }
                          >
                            {t.status}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-500">
                          {t.course_name && <span>{t.course_name} • </span>}
                          Provider: {t.provider_name || "SFFA"} • Completed: {t.completion_date} {t.expiry_date ? `• Expiry: ${t.expiry_date}` : ""}
                        </div>
                        {t.verified_at && (
                          <div className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-medium">
                            <CheckCircle className="h-3 w-3" /> Verified by Supervisor {t.verified_by_name || ""} on {new Date(t.verified_at).toLocaleDateString()}
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

        {/* 6. VISITS & INSPECTIONS TAB */}
        <TabsContent value="visits" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Physical Inspections & Monitoring Visits</CardTitle>
                <CardDescription>Routine physical inspections, safety checks, deficiencies, and corrective action plans.</CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowVisitModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Log Inspection
              </Button>
            </CardHeader>
            <CardContent>
              {home.visits?.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No inspection or visit records yet.</div>
              ) : (
                <div className="space-y-4">
                  {home.visits.map((v) => (
                    <div key={v.id} className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                          <span>{v.purpose}</span>
                          <Badge variant="outline">{v.visit_type}</Badge>
                          {v.corrective_action_status && v.corrective_action_status !== "NONE" && (
                            <Badge
                              className={
                                v.corrective_action_status === "COMPLETED"
                                  ? "bg-emerald-500/10 text-emerald-700"
                                  : v.corrective_action_status === "OVERDUE"
                                  ? "bg-rose-500/10 text-rose-700"
                                  : "bg-amber-500/10 text-amber-700"
                              }
                            >
                              Action: {v.corrective_action_status}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500 font-mono">Date: {v.visit_date}</span>
                          <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => handleOpenCorrectiveModal(v)}>
                            <Wrench className="h-3.5 w-3.5 mr-1" /> Corrective Action
                          </Button>
                        </div>
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400">Inspector: {v.worker_name || "Caseworker"}</div>
                      <p className="text-xs text-slate-800 dark:text-slate-200 whitespace-pre-wrap">{v.summary}</p>
                      {v.deficiencies && (
                        <div className="text-xs bg-rose-50 dark:bg-rose-950/30 text-rose-800 dark:text-rose-300 p-2.5 rounded border border-rose-200 dark:border-rose-900 space-y-1">
                          <div className="font-bold flex items-center gap-1.5"><AlertTriangle className="h-3.5 w-3.5 text-rose-600" /> Deficiencies Identified:</div>
                          <div>{v.deficiencies}</div>
                          {v.corrective_actions && (
                            <div className="mt-1 pt-1 border-t border-rose-200 dark:border-rose-800">
                              <span className="font-semibold">Required Corrective Action:</span> {v.corrective_actions}
                              {v.corrective_action_due_date && ` (Due: ${v.corrective_action_due_date})`}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 7. COMPLIANCE TAB */}
        <TabsContent value="compliance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Overall Status */}
            <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Overall Home Compliance</div>
              <div className="mt-2 flex items-center gap-2">
                {complianceSummary?.overall_status === "COMPLIANT" ? (
                  <>
                    <CheckCircle className="h-6 w-6 text-emerald-600" />
                    <span className="text-xl font-bold text-emerald-600">COMPLIANT</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-6 w-6 text-amber-600" />
                    <span className="text-xl font-bold text-amber-600">
                      {complianceSummary?.overall_status || "PENDING REVIEW"}
                    </span>
                  </>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-2">Active license, clear background screenings, and mandatory training compliance.</p>
            </Card>

            {/* Training Compliance */}
            <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Caregiver Training Status</div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {complianceSummary?.compliant_caregivers || 0} / {complianceSummary?.total_caregivers || home.members?.length || 0}
                </span>
                <span className="text-xs text-slate-500">caregivers certified</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">PRIDE, CPR/First Aid, Trauma-Informed, Cultural Safety.</p>
            </Card>

            {/* Clearances Status */}
            <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Screenings</div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {clearances.filter((c) => c.is_eligible_for_placement).length || backgroundChecks.filter((c) => c.is_eligible).length}
                </span>
                <span className="text-xs text-slate-500">eligible clearances</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">Annual police record and vulnerable sector verification.</p>
            </Card>
          </div>

          {/* Member Training Breakdown */}
          {complianceSummary?.member_summaries && complianceSummary.member_summaries.length > 0 && (
            <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
              <CardHeader>
                <CardTitle className="text-base">Caregiver Training Matrix</CardTitle>
                <CardDescription>Mandatory module status per household member.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {complianceSummary.member_summaries.map((m) => (
                    <div key={m.person_id} className="py-3 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-slate-900 dark:text-slate-100">{m.person_name}</div>
                        <div className="text-xs text-slate-500">Role: {m.role}</div>
                        {m.mandatory_missing?.length > 0 && (
                          <div className="text-xs text-rose-600 font-medium mt-1">
                            Missing: {m.mandatory_missing.join(", ")}
                          </div>
                        )}
                      </div>
                      <Badge className={m.is_compliant ? "bg-emerald-500/10 text-emerald-700" : "bg-amber-500/10 text-amber-700"}>
                        {m.is_compliant ? "Fully Trained" : "Requirements Incomplete"}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
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

        {/* 11. MONITORING TAB (Sprint 3) */}
        <TabsContent value="monitoring" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-600" /> Periodic Resource Home Monitoring
                </CardTitle>
                <CardDescription>
                  Ongoing monthly contact and home observations distinct from annual licensing reviews.
                </CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowMonitoringModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Log Monitoring Visit
              </Button>
            </CardHeader>
            <CardContent>
              {monitorings.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  No periodic monitoring records logged for this home yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {monitorings.map((m) => (
                    <div
                      key={m.id}
                      className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 space-y-2"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                            {m.visit_date}
                          </span>
                          <Badge variant="outline" className="bg-blue-50 text-blue-700 dark:bg-blue-900/30">
                            {m.visit_type}
                          </Badge>
                          <Badge variant="outline" className="bg-slate-100 text-slate-700 dark:bg-slate-800">
                            {m.contact_method}
                          </Badge>
                          {m.safe_sleep_verified && (
                            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30">
                              Safe Sleep Verified
                            </Badge>
                          )}
                          {m.follow_up_required && (
                            <Badge variant="outline" className="bg-rose-50 text-rose-700 dark:bg-rose-900/30">
                              Follow-Up Required
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-slate-500">
                          {m.duration_minutes ? `${m.duration_minutes} min` : ""}
                        </span>
                      </div>
                      {m.observations && (
                        <p className="text-xs text-slate-600 dark:text-slate-300">
                          <span className="font-semibold">Observations:</span> {m.observations}
                        </p>
                      )}
                      {m.caregiver_wellbeing_notes && (
                        <p className="text-xs text-slate-600 dark:text-slate-300">
                          <span className="font-semibold">Caregiver Well-being:</span> {m.caregiver_wellbeing_notes}
                        </p>
                      )}
                      {m.follow_up_required && m.follow_up_notes && (
                        <p className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                          Follow-up Action: {m.follow_up_notes} (Due: {m.follow_up_due_date || "Not set"})
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 12. COMPLAINTS TAB (Sprint 3) */}
        <TabsContent value="complaints" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileWarning className="h-4 w-4 text-rose-600" /> Resource Complaints & Inquiries
                </CardTitle>
                <CardDescription>
                  Confidential tracking of complaints, investigation status, findings, and formal dispositions.
                </CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowComplaintModal(true)} className="gap-1.5 bg-rose-600 hover:bg-rose-700 text-white">
                <Plus className="h-4 w-4" /> Register Complaint
              </Button>
            </CardHeader>
            <CardContent>
              {complaints.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  No complaints or investigations registered for this resource home.
                </div>
              ) : (
                <div className="space-y-3">
                  {complaints.map((c) => (
                    <div
                      key={c.id}
                      className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 space-y-2"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                            {c.complaint_number}
                          </span>
                          <Badge variant="outline" className="bg-rose-50 text-rose-700 dark:bg-rose-900/30">
                            {c.allegation_type}
                          </Badge>
                          <Badge variant="outline" className="bg-slate-100 text-slate-700">
                            Status: {c.status}
                          </Badge>
                          <Badge variant="outline" className="bg-amber-50 text-amber-800">
                            Investigation: {c.investigation_status}
                          </Badge>
                          {c.disposition && (
                            <Badge variant="outline" className="bg-indigo-50 text-indigo-700">
                              Disposition: {c.disposition}
                            </Badge>
                          )}
                          {c.is_sensitive && (
                            <Badge variant="outline" className="bg-purple-50 text-purple-700">
                              Confidential / Sensitive
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-slate-500">
                          Incident: {c.incident_date || c.created_at?.split("T")[0]}
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 dark:text-slate-300">
                        <span className="font-semibold">Allegation:</span> {c.allegation_summary}
                      </p>
                      {c.findings && (
                        <div className="text-xs text-slate-600 dark:text-slate-400 bg-white dark:bg-slate-800 p-2.5 rounded border border-slate-200 dark:border-slate-700">
                          <div className="font-semibold text-slate-700 dark:text-slate-200">
                            Investigation Findings {c.findings_finalized ? "(Finalized)" : "(In Progress)"}:
                          </div>
                          <div>{c.findings}</div>
                        </div>
                      )}
                      {c.disposition_notes && (
                        <p className="text-xs text-slate-500">
                          <span className="font-semibold">Disposition Rationale:</span> {c.disposition_notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 13. SUPPORTS TAB (Sprint 3) */}
        <TabsContent value="supports" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <HeartHandshake className="h-4 w-4 text-indigo-600" /> Caregiver Supports & Stabilization
                </CardTitle>
                <CardDescription>
                  Respite care, clinical consultations, peer support, and financial assistance allocations.
                </CardDescription>
              </div>
              <Button size="sm" onClick={() => setShowSupportModal(true)} className="gap-1.5">
                <Plus className="h-4 w-4" /> Request Caregiver Support
              </Button>
            </CardHeader>
            <CardContent>
              {supports.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  No caregiver supports requested or recorded for this home.
                </div>
              ) : (
                <div className="space-y-3">
                  {supports.map((s) => (
                    <div
                      key={s.id}
                      className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 space-y-2"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="bg-indigo-50 text-indigo-700 font-semibold">
                            {s.support_type}
                          </Badge>
                          <Badge variant="outline" className={s.status === "APPROVED" || s.status === "ACTIVE" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700"}>
                            {s.status}
                          </Badge>
                          {s.service_request_id && (
                            <Badge variant="outline" className="bg-blue-50 text-blue-700">
                              Service Request Linked
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm font-bold text-slate-900 dark:text-slate-100">
                          {s.approved_amount ? `$${Number(s.approved_amount).toLocaleString()}` : s.requested_amount ? `Requested: $${Number(s.requested_amount).toLocaleString()}` : ""}
                        </div>
                      </div>
                      {s.description && (
                        <p className="text-xs text-slate-700 dark:text-slate-300">
                          {s.description}
                        </p>
                      )}
                      {s.notes && (
                        <p className="text-xs text-slate-500">
                          Notes: {s.notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 14. FINANCE TAB (Sprint 3) */}
        <TabsContent value="finance" className="space-y-4">
          <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-emerald-600" /> Resource Financial Integration
              </CardTitle>
              <CardDescription>
                Maintenance rate schedules, generated foster invoices, and authorized service requests.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {financeSummary ? (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
                      <div className="text-xs text-slate-500">Active Rate Schedules</div>
                      <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                        {financeSummary.active_rates_count}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">Placement home maintenance per diem</div>
                    </div>
                    <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
                      <div className="text-xs text-slate-500">Resource Home Invoices</div>
                      <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                        ${Number(financeSummary.total_invoiced_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-[11px] text-amber-600 mt-1">
                        {financeSummary.unpaid_invoices_count} unpaid / pending payment
                      </div>
                    </div>
                    <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
                      <div className="text-xs text-slate-500">Support Service Requests</div>
                      <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                        ${Number(financeSummary.total_service_requests_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        {financeSummary.active_service_requests_count} active service requests
                      </div>
                    </div>
                  </div>

                  {/* Rates Detail */}
                  {financeSummary.rates && financeSummary.rates.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        Rate Schedules
                      </h4>
                      <div className="space-y-2">
                        {financeSummary.rates.map((r, i) => (
                          <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 text-sm">
                            <div>
                              <span className="font-semibold text-slate-900 dark:text-slate-100">{r.rate_type}</span>
                              <span className="text-xs text-slate-500 ml-2">Effective: {r.effective_date} {r.end_date ? `to ${r.end_date}` : "(Ongoing)"}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-emerald-600">${r.daily_rate}/day</span>
                              <Badge variant="outline" className={r.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}>
                                {r.is_active ? "Active" : "Archived"}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Invoices Detail */}
                  {financeSummary.invoices && financeSummary.invoices.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        Recent Invoices
                      </h4>
                      <div className="space-y-2">
                        {financeSummary.invoices.map((inv, i) => (
                          <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 text-sm">
                            <div>
                              <span className="font-semibold text-slate-900 dark:text-slate-100">{inv.invoice_number || `INV-${i+1}`}</span>
                              <span className="text-xs text-slate-500 ml-2">Due: {inv.due_date || "N/A"}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-900 dark:text-white">${Number(inv.amount || 0).toLocaleString()}</span>
                              <Badge variant="outline" className={inv.status === "PAID" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}>
                                {inv.status}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-10 space-y-3">
                  <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-full w-fit mx-auto text-slate-500">
                    <Lock className="h-6 w-6" />
                  </div>
                  <div className="font-medium text-slate-800 dark:text-slate-200 text-sm">
                    Restricted Financial Information
                  </div>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Placement home financial ledgers, per diem schedules, and invoice histories are protected by RBAC policy. Only users with authorized Finance permissions may inspect ledger amounts.
                  </p>
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
                  <SelectItem value="SPOUSE_PARTNER">Spouse / Partner</SelectItem>
                  <SelectItem value="CHILD">Child</SelectItem>
                  <SelectItem value="OTHER_ADULT">Other Adult</SelectItem>
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

      {/* Sprint 2: New Assessment Modal */}
      <Dialog open={showAssessModal} onOpenChange={setShowAssessModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Initiate Caregiver Assessment</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateAssessment} className="space-y-3 pt-2">
            <div className="space-y-1">
              <Label>Assessment Title *</Label>
              <Input
                required
                value={assessForm.title}
                onChange={(e) => setAssessForm({ ...assessForm, title: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Assessment Type</Label>
              <Select value={assessForm.assessment_type} onValueChange={(v) => setAssessForm({ ...assessForm, assessment_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="HOME_STUDY">Home Study Assessment</SelectItem>
                  <SelectItem value="CAREGIVER_INTERVIEW">Caregiver Interview</SelectItem>
                  <SelectItem value="CULTURAL_ASSESSMENT">Cultural Safety Assessment</SelectItem>
                  <SelectItem value="PARENTING_CAPACITY">Parenting Capacity</SelectItem>
                  <SelectItem value="SUPPORT_NETWORK">Support Network Assessment</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Subject Caregiver</Label>
              <Select
                value={assessForm.primary_person_id}
                onValueChange={(v) => setAssessForm({ ...assessForm, primary_person_id: v })}
              >
                <SelectTrigger><SelectValue placeholder="Select household member" /></SelectTrigger>
                <SelectContent>
                  {home.members?.map((m) => (
                    <SelectItem key={m.person_id} value={m.person_id}>
                      {m.person_name || m.person_id} ({m.role})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Notes & Scope</Label>
              <Textarea
                placeholder="Initial assessment goals, background context, or recommendations..."
                value={assessForm.notes}
                onChange={(e) => setAssessForm({ ...assessForm, notes: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowAssessModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Start Assessment</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Sprint 2: Record Screening / Clearance Modal */}
      <Dialog open={showClearanceModal} onOpenChange={setShowClearanceModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Screening & Clearance Check</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateClearance} className="space-y-3 pt-2">
            <div className="space-y-1">
              <Label>Subject Caregiver *</Label>
              <Select
                value={clearanceForm.subject_id}
                onValueChange={(v) => {
                  const m = home.members?.find((x) => x.person_id === v);
                  setClearanceForm({
                    ...clearanceForm,
                    subject_id: v,
                    subject_name: m ? m.person_name : clearanceForm.subject_name,
                  });
                }}
              >
                <SelectTrigger><SelectValue placeholder="Select household member" /></SelectTrigger>
                <SelectContent>
                  {home.members?.map((m) => (
                    <SelectItem key={m.person_id} value={m.person_id}>
                      {m.person_name || m.person_id} ({m.role})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Clearance Type *</Label>
              <Select value={clearanceForm.check_type} onValueChange={(v) => setClearanceForm({ ...clearanceForm, check_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="CRIMINAL_RECORD_CHECK">Criminal Record Check</SelectItem>
                  <SelectItem value="VULNERABLE_SECTOR">Vulnerable Sector Check</SelectItem>
                  <SelectItem value="CHILD_ABUSE_REGISTRY">Child Abuse Registry Check</SelectItem>
                  <SelectItem value="DRIVER_ABSTRACT">Driver Abstract</SelectItem>
                  <SelectItem value="REFERENCE_CHECK">Reference Check</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Request Date</Label>
                <Input
                  type="date"
                  value={clearanceForm.request_date}
                  onChange={(e) => setClearanceForm({ ...clearanceForm, request_date: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Reference Number</Label>
                <Input
                  placeholder="e.g. CRC-2026-8812"
                  value={clearanceForm.clearance_reference_number}
                  onChange={(e) => setClearanceForm({ ...clearanceForm, clearance_reference_number: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Conducted By Agency</Label>
              <Input
                placeholder="e.g. Regina Police Service / RCMP"
                value={clearanceForm.conducted_by_agency}
                onChange={(e) => setClearanceForm({ ...clearanceForm, conducted_by_agency: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <Textarea
                placeholder="Confidential verification or tracking notes..."
                value={clearanceForm.risk_assessment_notes}
                onChange={(e) => setClearanceForm({ ...clearanceForm, risk_assessment_notes: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowClearanceModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Save Clearance</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Sprint 2: Record Training Modal */}
      <Dialog open={showTrainingModal} onOpenChange={setShowTrainingModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Caregiver Training</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTraining} className="space-y-3 pt-2">
            <div className="space-y-1">
              <Label>Caregiver Person *</Label>
              <Select
                value={trainingForm.person_id}
                onValueChange={(v) => setTrainingForm({ ...trainingForm, person_id: v })}
              >
                <SelectTrigger><SelectValue placeholder="Select caregiver" /></SelectTrigger>
                <SelectContent>
                  {home.members?.map((m) => (
                    <SelectItem key={m.person_id} value={m.person_id}>
                      {m.person_name || m.person_id} ({m.role})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Training Module *</Label>
              <Select
                value={trainingForm.training_type}
                onValueChange={(v) => {
                  let defaultCourse = "PRIDE Pre-Service Program";
                  if (v === "CPR_FIRST_AID") defaultCourse = "Standard First Aid & CPR-C";
                  if (v === "TRAUMA_INFORMED_CARE") defaultCourse = "Trauma-Informed Care for Foster Families";
                  if (v === "CULTURAL_SAFETY") defaultCourse = "Indigenous Cultural Safety & Reconciliation";
                  setTrainingForm({ ...trainingForm, training_type: v, course_name: defaultCourse });
                }}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="PRE_SERVICE_PRIDE">Pre-Service / PRIDE</SelectItem>
                  <SelectItem value="CPR_FIRST_AID">CPR & First Aid</SelectItem>
                  <SelectItem value="TRAUMA_INFORMED_CARE">Trauma-Informed Care</SelectItem>
                  <SelectItem value="CULTURAL_SAFETY">Cultural Safety</SelectItem>
                  <SelectItem value="SUICIDE_PREVENTION">Suicide Prevention (ASIST / safeTALK)</SelectItem>
                  <SelectItem value="MEDICATION_ADMINISTRATION">Medication Administration</SelectItem>
                  <SelectItem value="OTHER">Other Configurable Training</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Completion Date *</Label>
                <Input
                  type="date"
                  required
                  value={trainingForm.completion_date}
                  onChange={(e) => setTrainingForm({ ...trainingForm, completion_date: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Expiry Date (if applicable)</Label>
                <Input
                  type="date"
                  value={trainingForm.expiry_date}
                  onChange={(e) => setTrainingForm({ ...trainingForm, expiry_date: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Provider</Label>
              <Input
                placeholder="e.g. Saskatchewan Foster Families Association"
                value={trainingForm.provider_name}
                onChange={(e) => setTrainingForm({ ...trainingForm, provider_name: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <Textarea
                placeholder="Certificate number or verification notes..."
                value={trainingForm.notes}
                onChange={(e) => setTrainingForm({ ...trainingForm, notes: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowTrainingModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Record Training</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Sprint 2: Corrective Action Modal */}
      <Dialog open={showCorrectiveModal} onOpenChange={setShowCorrectiveModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Inspection Findings & Corrective Action</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateCorrectiveAction} className="space-y-3 pt-2">
            <div className="space-y-1">
              <Label>Resolution Status *</Label>
              <Select
                value={correctiveForm.corrective_action_status}
                onValueChange={(v) => setCorrectiveForm({ ...correctiveForm, corrective_action_status: v })}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="REQUIRED">Required (New Deficiencies)</SelectItem>
                  <SelectItem value="PENDING">Pending Action Plan</SelectItem>
                  <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                  <SelectItem value="COMPLETED">Completed / Remediated</SelectItem>
                  <SelectItem value="OVERDUE">Overdue</SelectItem>
                  <SelectItem value="NONE">None Required</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Deficiencies Identified</Label>
              <Textarea
                placeholder="List physical or compliance deficiencies..."
                value={correctiveForm.deficiencies}
                onChange={(e) => setCorrectiveForm({ ...correctiveForm, deficiencies: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Corrective Action Required</Label>
              <Textarea
                placeholder="Action required from caregiver/home..."
                value={correctiveForm.corrective_actions}
                onChange={(e) => setCorrectiveForm({ ...correctiveForm, corrective_actions: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Due Date</Label>
                <Input
                  type="date"
                  value={correctiveForm.corrective_action_due_date}
                  onChange={(e) => setCorrectiveForm({ ...correctiveForm, corrective_action_due_date: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Completed Date</Label>
                <Input
                  type="date"
                  value={correctiveForm.completed_date}
                  onChange={(e) => setCorrectiveForm({ ...correctiveForm, completed_date: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowCorrectiveModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Update Corrective Action</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Sprint 3: Periodic Monitoring Modal */}
      <Dialog open={showMonitoringModal} onOpenChange={setShowMonitoringModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Log Periodic Monitoring Visit</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateMonitoring} className="space-y-3 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Visit Date *</Label>
                <Input
                  type="date"
                  required
                  value={monitoringForm.visit_date}
                  onChange={(e) => setMonitoringForm({ ...monitoringForm, visit_date: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Duration (Minutes)</Label>
                <Input
                  type="number"
                  value={monitoringForm.duration_minutes}
                  onChange={(e) => setMonitoringForm({ ...monitoringForm, duration_minutes: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Visit Type *</Label>
                <Select
                  value={monitoringForm.visit_type}
                  onValueChange={(v) => setMonitoringForm({ ...monitoringForm, visit_type: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="HOME_VISIT">Home Visit</SelectItem>
                    <SelectItem value="VIRTUAL_CHECK_IN">Virtual Check-In</SelectItem>
                    <SelectItem value="COLLATERAL_CONTACT">Collateral Contact</SelectItem>
                    <SelectItem value="UNANNOUNCED_VISIT">Unannounced Visit</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Contact Method *</Label>
                <Select
                  value={monitoringForm.contact_method}
                  onValueChange={(v) => setMonitoringForm({ ...monitoringForm, contact_method: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="IN_PERSON">In Person</SelectItem>
                    <SelectItem value="PHONE">Phone Call</SelectItem>
                    <SelectItem value="VIDEO">Video Conference</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1">
              <Label>Safe Sleep / Living Conditions Verified</Label>
              <Select
                value={monitoringForm.safe_sleep_verified ? "true" : "false"}
                onValueChange={(v) => setMonitoringForm({ ...monitoringForm, safe_sleep_verified: v === "true" })}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Yes - Safe Sleep & Conditions Verified</SelectItem>
                  <SelectItem value="false">No / Deficiencies Observed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Caregiver Well-being & Observations</Label>
              <Textarea
                placeholder="Caregiver coping, dynamics, supports needed..."
                value={monitoringForm.caregiver_wellbeing_notes}
                onChange={(e) => setMonitoringForm({ ...monitoringForm, caregiver_wellbeing_notes: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>General Observations</Label>
              <Textarea
                placeholder="Home environment, child interactions..."
                value={monitoringForm.observations}
                onChange={(e) => setMonitoringForm({ ...monitoringForm, observations: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Follow-Up Action Required?</Label>
              <Select
                value={monitoringForm.follow_up_required ? "true" : "false"}
                onValueChange={(v) => setMonitoringForm({ ...monitoringForm, follow_up_required: v === "true" })}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">No Follow-up Required</SelectItem>
                  <SelectItem value="true">Yes - Follow-up Action Required</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {monitoringForm.follow_up_required && (
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div className="space-y-1">
                  <Label>Follow-Up Notes</Label>
                  <Input
                    placeholder="Specific items to follow up on..."
                    value={monitoringForm.follow_up_notes}
                    onChange={(e) => setMonitoringForm({ ...monitoringForm, follow_up_notes: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label>Follow-Up Due Date</Label>
                  <Input
                    type="date"
                    value={monitoringForm.follow_up_due_date || ""}
                    onChange={(e) => setMonitoringForm({ ...monitoringForm, follow_up_due_date: e.target.value })}
                  />
                </div>
              </div>
            )}
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowMonitoringModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Record Visit</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Sprint 3: Register Complaint Modal */}
      <Dialog open={showComplaintModal} onOpenChange={setShowComplaintModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Register Resource Home Complaint</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateComplaint} className="space-y-3 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Allegation Category *</Label>
                <Select
                  value={complaintForm.allegation_type}
                  onValueChange={(v) => setComplaintForm({ ...complaintForm, allegation_type: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CARE_QUALITY">Care Quality</SelectItem>
                    <SelectItem value="SAFETY_CONCERN">Safety Concern</SelectItem>
                    <SelectItem value="POLICY_BREACH">Policy Breach</SelectItem>
                    <SelectItem value="ABUSE_NEGLECT">Abuse / Neglect Allegation</SelectItem>
                    <SelectItem value="COMMUNICATION_ISSUE">Communication Issue</SelectItem>
                    <SelectItem value="OTHER">Other Inquiry</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Incident Date</Label>
                <Input
                  type="date"
                  value={complaintForm.incident_date}
                  onChange={(e) => setComplaintForm({ ...complaintForm, incident_date: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Complainant Source *</Label>
                <Select
                  value={complaintForm.complainant_type}
                  onValueChange={(v) => setComplaintForm({ ...complaintForm, complainant_type: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CASEWORKER">Caseworker</SelectItem>
                    <SelectItem value="FOSTER_CHILD">Foster Child / Youth</SelectItem>
                    <SelectItem value="BIOLOGICAL_PARENT">Biological Parent / Family</SelectItem>
                    <SelectItem value="COMMUNITY_MEMBER">Community Member / Neighbour</SelectItem>
                    <SelectItem value="ANONYMOUS">Anonymous</SelectItem>
                    <SelectItem value="OTHER">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Complainant Name (Confidential)</Label>
                <Input
                  placeholder="Optional complainant name..."
                  value={complaintForm.complainant_name}
                  onChange={(e) => setComplaintForm({ ...complaintForm, complainant_name: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Allegation Summary *</Label>
              <Textarea
                required
                placeholder="Factual summary of concern or incident reported..."
                value={complaintForm.allegation_summary}
                onChange={(e) => setComplaintForm({ ...complaintForm, allegation_summary: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Confidential / Sensitive Tier</Label>
              <Select
                value={complaintForm.is_sensitive ? "true" : "false"}
                onValueChange={(v) => setComplaintForm({ ...complaintForm, is_sensitive: v === "true" })}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">Standard Complaint</SelectItem>
                  <SelectItem value="true">High Sensitivity / Protected Investigation</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-[11px] text-slate-500">
                Sensitive records are restricted to investigator and supervisor roles.
              </p>
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowComplaintModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting} className="bg-rose-600 hover:bg-rose-700 text-white">
                Register Complaint
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Sprint 3: Request Caregiver Support Modal */}
      <Dialog open={showSupportModal} onOpenChange={setShowSupportModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Request Caregiver Support / Stabilization</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateSupport} className="space-y-3 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Support Type *</Label>
                <Select
                  value={supportForm.support_type}
                  onValueChange={(v) => setSupportForm({ ...supportForm, support_type: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="RESPITE">Respite Care</SelectItem>
                    <SelectItem value="CLINICAL_CONSULTATION">Clinical Consultation</SelectItem>
                    <SelectItem value="PEER_SUPPORT">Peer Support / Mentorship</SelectItem>
                    <SelectItem value="CULTURAL_MENTORSHIP">Cultural Mentorship</SelectItem>
                    <SelectItem value="EQUIPMENT_SPECIAL_NEED">Equipment / Special Need</SelectItem>
                    <SelectItem value="TRAINING_ENHANCED">Enhanced Training</SelectItem>
                    <SelectItem value="EMERGENCY_ASSISTANCE">Emergency Stabilization</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Requested Allocation ($)</Label>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="e.g. 500.00"
                  value={supportForm.requested_amount}
                  onChange={(e) => setSupportForm({ ...supportForm, requested_amount: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Description / Need Justification</Label>
              <Textarea
                placeholder="Details of caregiver support requested and child needs..."
                value={supportForm.description}
                onChange={(e) => setSupportForm({ ...supportForm, description: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Linked Service Request UUID (Optional)</Label>
              <Input
                placeholder="Connect to existing Finance ServiceRequest..."
                value={supportForm.service_request_id}
                onChange={(e) => setSupportForm({ ...supportForm, service_request_id: e.target.value })}
              />
            </div>
            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setShowSupportModal(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>Submit Support Request</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

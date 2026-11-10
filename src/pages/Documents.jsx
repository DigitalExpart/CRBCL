import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { 
  Search, FileText, Upload, Plus, Shield, Lock, Unlock, 
  Clock, CheckCircle, XCircle, AlertCircle, Eye, Edit3, Send
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import PageHeader from "@/components/shared/PageHeader";
import EmptyState from "@/components/shared/EmptyState";

const CATEGORIES = ["Case File", "Policy", "Report", "Form", "Legal", "Financial", "HR", "Training", "General"];
const ACCESS_MODES = [
  { value: "INHERIT", label: "Inherit Standard Role/Team Permissions", desc: "Follows normal role and team permissions" },
  { value: "RESTRICTED", label: "Restricted to Authorized Roles Only", desc: "Only designated roles and supervisors can access" },
  { value: "ALLOW_SELECTED", label: "Allow Selected Lower-Level Roles/Users", desc: "Grants specific roles or staff members within team scope" },
  { value: "REQUIRES_APPROVAL", label: "Requires Formal Supervisor Approval", desc: "Staff must submit a request and await supervisor sign-off" },
];

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [currentUser, setCurrentUser] = useState(null);

  // Form State (Upload or Type)
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [entryMode, setEntryMode] = useState("type"); // "type" | "upload"
  const [form, setForm] = useState({ 
    title: "", 
    category: "General", 
    description: "", 
    document_content: "", 
    is_confidential: false,
    access_mode: "INHERIT"
  });
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);

  // Supervisor Access Control Modal
  const [selectedDocForAccess, setSelectedDocForAccess] = useState(null);
  const [accessControlForm, setAccessControlForm] = useState({
    access_mode: "INHERIT",
    allowed_roles: "",
    restricted_roles: ""
  });
  const [updatingAccess, setUpdatingAccess] = useState(false);

  // Request Access Modal
  const [requestDocTarget, setRequestDocTarget] = useState(null);
  const [requestReason, setRequestReason] = useState("");
  const [submittingRequest, setSubmittingRequest] = useState(false);

  // Pending Approvals Queue (for supervisors)
  const [pendingRequests, setPendingRequests] = useState([]);
  const [activeTab, setActiveTab] = useState("documents"); // "documents" | "approvals"

  const loadData = async () => {
    setLoading(true);
    try {
      const user = await api.auth.me().catch(() => null);
      setCurrentUser(user);

      const docList = await api.fetch("/api/v1/documents").catch(() => []);
      setDocs(Array.isArray(docList) ? docList : []);

      // Check if user is supervisor/leadership to load pending requests
      const roles = Array.isArray(user?.roles) 
        ? user.roles.map(r => typeof r === "string" ? r : (r?.key || ""))
        : (user?.role ? [user.role] : []);
      const isSupervisor = roles.some(r => ["supervisor", "director_manager", "resource_supervisor", "resource_director", "ceo", "executive_director", "admin", "it_admin"].includes(r.toLowerCase()));
      
      if (isSupervisor) {
        const reqs = await api.fetch("/api/v1/documents/access-requests/pending").catch(() => []);
        setPendingRequests(Array.isArray(reqs) ? reqs : []);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateDocument = async (e) => {
    e.preventDefault();
    if (!form.title) return;
    if (entryMode === "upload" && !file) return;
    if (entryMode === "type" && !form.document_content) return;

    setSaving(true);
    try {
      let payload = {
        title: form.title.strip ? form.title.strip() : form.title,
        category: form.category,
        description: form.description,
        is_confidential: form.is_confidential,
        access_mode: form.access_mode,
      };

      if (entryMode === "type") {
        payload.document_content = form.document_content;
      } else if (file) {
        // Upload file via storage endpoint
        const uploadResult = await api.integrations.Core.UploadFile({ file }).catch(() => null);
        payload.file_url = uploadResult?.file_url || URL.createObjectURL(file);
        payload.filename = file.name;
        payload.original_filename = file.name;
        payload.content_type = file.type || "application/octet-stream";
      }

      await api.fetch("/api/v1/documents", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setShowCreateModal(false);
      setForm({ title: "", category: "General", description: "", document_content: "", is_confidential: false, access_mode: "INHERIT" });
      setFile(null);
      await loadData();
    } catch (err) {
      alert("Error saving document: " + (err.message || "Failed"));
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateAccessControl = async (e) => {
    e.preventDefault();
    if (!selectedDocForAccess) return;

    setUpdatingAccess(true);
    try {
      const allowedRolesList = accessControlForm.allowed_roles
        ? accessControlForm.allowed_roles.split(",").map(r => r.trim().toLowerCase()).filter(Boolean)
        : [];
      const restrictedRolesList = accessControlForm.restricted_roles
        ? accessControlForm.restricted_roles.split(",").map(r => r.trim().toLowerCase()).filter(Boolean)
        : [];

      await api.fetch(`/api/v1/documents/${selectedDocForAccess.id}/access-control`, {
        method: "PATCH",
        body: JSON.stringify({
          access_mode: accessControlForm.access_mode,
          allowed_roles: allowedRolesList.length ? allowedRolesList : null,
          restricted_roles: restrictedRolesList.length ? restrictedRolesList : null,
        }),
      });

      setSelectedDocForAccess(null);
      await loadData();
    } catch (err) {
      alert("Error updating access control: " + (err.message || "Unauthorized"));
    } finally {
      setUpdatingAccess(false);
    }
  };

  const handleSubmitAccessRequest = async (e) => {
    e.preventDefault();
    if (!requestDocTarget || !requestReason) return;

    setSubmittingRequest(true);
    try {
      await api.fetch(`/api/v1/documents/${requestDocTarget.id}/request-access`, {
        method: "POST",
        body: JSON.stringify({ reason: requestReason }),
      });
      alert("Access request submitted to supervisor queue.");
      setRequestDocTarget(null);
      setRequestReason("");
      await loadData();
    } catch (err) {
      alert("Error requesting access: " + (err.message || "Conflict"));
    } finally {
      setSubmittingRequest(false);
    }
  };

  const handleApproveRequest = async (reqId) => {
    try {
      await api.fetch(`/api/v1/documents/access-requests/${reqId}/approve`, {
        method: "POST",
        body: JSON.stringify({ review_notes: "Approved by supervisor" }),
      });
      await loadData();
    } catch (err) {
      alert("Error approving request: " + err.message);
    }
  };

  const handleDenyRequest = async (reqId) => {
    try {
      await api.fetch(`/api/v1/documents/access-requests/${reqId}/deny`, {
        method: "POST",
        body: JSON.stringify({ review_notes: "Denied" }),
      });
      await loadData();
    } catch (err) {
      alert("Error denying request: " + err.message);
    }
  };

  const userRoles = Array.isArray(currentUser?.roles) 
    ? currentUser.roles.map(r => typeof r === "string" ? r : (r?.key || ""))
    : (currentUser?.role ? [currentUser.role] : []);
  const isSupervisorOrAbove = userRoles.some(r => 
    ["supervisor", "director_manager", "resource_supervisor", "resource_director", "ceo", "executive_director", "admin", "it_admin"].includes(r.toLowerCase())
  );

  const filtered = docs.filter(d => {
    const matchesSearch = !search || 
      d.title?.toLowerCase().includes(search.toLowerCase()) ||
      d.description?.toLowerCase().includes(search.toLowerCase()) ||
      d.document_content?.toLowerCase().includes(search.toLowerCase());
    const matchesCat = categoryFilter === "all" || d.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Document & Information Repository" 
        subtitle="Staff document entry, secure uploads, and supervisor-controlled access" 
        actions={
          <div className="flex gap-2">
            {isSupervisorOrAbove && (
              <Button 
                variant={activeTab === "approvals" ? "default" : "outline"}
                onClick={() => setActiveTab(activeTab === "approvals" ? "documents" : "approvals")}
                className="relative"
              >
                <Shield className="w-4 h-4 mr-2" />
                Approvals Queue
                {pendingRequests.length > 0 && (
                  <span className="ml-2 bg-destructive text-white rounded-full text-xs px-2 py-0.5 font-bold">
                    {pendingRequests.length}
                  </span>
                )}
              </Button>
            )}
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" /> New Document
            </Button>
          </div>
        } 
      />

      {/* Tabs */}
      {activeTab === "approvals" && isSupervisorOrAbove ? (
        <div className="bg-card rounded-xl border border-border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg text-foreground flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-500" />
              Pending Item-Level Access Requests ({pendingRequests.length})
            </h3>
            <Button variant="ghost" size="sm" onClick={() => setActiveTab("documents")}>
              Back to Documents
            </Button>
          </div>
          {pendingRequests.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">No pending access requests at this time.</p>
          ) : (
            <div className="divide-y divide-border">
              {pendingRequests.map(req => (
                <div key={req.id} className="py-4 flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-foreground">Document Access Request</p>
                    <p className="text-xs text-muted-foreground mt-0.5"><strong>Reason:</strong> {req.reason}</p>
                    <p className="text-xs text-muted-foreground">Requested: {new Date(req.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleApproveRequest(req.id)} className="bg-emerald-600 hover:bg-emerald-700">
                      <CheckCircle className="w-4 h-4 mr-1" /> Approve
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => handleDenyRequest(req.id)}>
                      <XCircle className="w-4 h-4 mr-1" /> Deny
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="relative flex-1 max-w-md w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input 
                placeholder="Search documents and typed content…" 
                value={search} 
                onChange={e => setSearch(e.target.value)} 
                className="pl-9" 
              />
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Label className="text-xs text-muted-foreground whitespace-nowrap">Category:</Label>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Document Cards */}
          {filtered.length === 0 ? (
            <EmptyState 
              icon={FileText} 
              title="No documents found" 
              action={<Button onClick={() => setShowCreateModal(true)}><Plus className="w-4 h-4 mr-2" /> Create First Document</Button>} 
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filtered.map(d => (
                <div key={d.id} className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <FileText className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <Badge variant="outline" className="text-xs">
                            {d.category}
                          </Badge>
                          {d.document_content && (
                            <Badge variant="secondary" className="ml-1 text-[10px]">
                              Typed Text
                            </Badge>
                          )}
                        </div>
                      </div>
                      
                      {/* Access Mode Badge */}
                      {d.access_mode === "RESTRICTED" && (
                        <Badge variant="destructive" className="text-[10px] flex items-center gap-1">
                          <Lock className="w-3 h-3" /> Restricted
                        </Badge>
                      )}
                      {d.access_mode === "REQUIRES_APPROVAL" && (
                        <Badge className="bg-amber-600 text-white text-[10px] flex items-center gap-1">
                          <Shield className="w-3 h-3" /> Approval Required
                        </Badge>
                      )}
                      {d.access_mode === "ALLOW_SELECTED" && (
                        <Badge className="bg-blue-600 text-white text-[10px] flex items-center gap-1">
                          <Unlock className="w-3 h-3" /> Selected Roles
                        </Badge>
                      )}
                    </div>

                    <div>
                      <h4 className="font-semibold text-foreground text-base leading-snug">{d.title}</h4>
                      {d.description && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{d.description}</p>
                      )}
                    </div>

                    {d.document_content && (
                      <div className="bg-muted/50 rounded-lg p-3 text-xs text-foreground font-mono max-h-24 overflow-y-auto whitespace-pre-wrap border border-border/50">
                        {d.document_content}
                      </div>
                    )}
                  </div>

                  <div className="pt-4 border-t border-border/50 mt-4 flex items-center justify-between text-xs text-muted-foreground">
                    <span>{new Date(d.created_at).toLocaleDateString()}</span>
                    
                    <div className="flex items-center gap-2">
                      {isSupervisorOrAbove && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-8 px-2 text-xs"
                          onClick={() => {
                            setSelectedDocForAccess(d);
                            setAccessControlForm({
                              access_mode: d.access_mode || "INHERIT",
                              allowed_roles: (d.allowed_roles || []).join(", "),
                              restricted_roles: (d.restricted_roles || []).join(", ")
                            });
                          }}
                        >
                          <Shield className="w-3.5 h-3.5 mr-1" /> Access Control
                        </Button>
                      )}

                      {d.file_url && (
                        <a 
                          href={d.file_url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-primary hover:underline font-medium inline-flex items-center"
                        >
                          <Eye className="w-3.5 h-3.5 mr-1" /> View
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Create / Type Document Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading">Staff Document & Information Entry</DialogTitle>
            <DialogDescription>
              Type notes and reports directly into the platform or attach an authorized document.
            </DialogDescription>
          </DialogHeader>

          <div className="flex border-b border-border mb-4">
            <button
              type="button"
              onClick={() => setEntryMode("type")}
              className={`pb-2 px-4 text-sm font-medium border-b-2 flex items-center gap-1.5 ${
                entryMode === "type" ? "border-primary text-primary" : "border-transparent text-muted-foreground"
              }`}
            >
              <Edit3 className="w-4 h-4" /> Type Information
            </button>
            <button
              type="button"
              onClick={() => setEntryMode("upload")}
              className={`pb-2 px-4 text-sm font-medium border-b-2 flex items-center gap-1.5 ${
                entryMode === "upload" ? "border-primary text-primary" : "border-transparent text-muted-foreground"
              }`}
            >
              <Upload className="w-4 h-4" /> Upload Document
            </button>
          </div>

          <form onSubmit={handleCreateDocument} className="space-y-4">
            <div>
              <Label>Document Title *</Label>
              <Input 
                value={form.title} 
                onChange={e => setForm({...form, title: e.target.value})} 
                placeholder="e.g. Independent Living Transition Review"
                required 
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Category</Label>
                <Select value={form.category} onValueChange={v => setForm({...form, category: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
                </Select>
              </div>

              <div>
                <Label>Access Level</Label>
                <Select value={form.access_mode} onValueChange={v => setForm({...form, access_mode: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="INHERIT">Standard (Team/Role)</SelectItem>
                    <SelectItem value="RESTRICTED">Restricted (Supervisors Only)</SelectItem>
                    <SelectItem value="REQUIRES_APPROVAL">Require Access Approval</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {entryMode === "type" ? (
              <div>
                <Label>Document Content *</Label>
                <Textarea 
                  rows={6} 
                  value={form.document_content} 
                  onChange={e => setForm({...form, document_content: e.target.value})} 
                  placeholder="Type official records, summaries, assessments, or transition notes directly here…"
                  required 
                />
              </div>
            ) : (
              <div>
                <Label>Select Authorized File *</Label>
                <Input type="file" onChange={e => setFile(e.target.files?.[0] || null)} required />
              </div>
            )}

            <div>
              <Label>Description / Summary</Label>
              <Textarea 
                rows={2} 
                value={form.description} 
                onChange={e => setForm({...form, description: e.target.value})} 
                placeholder="Brief administrative context..."
              />
            </div>

            <div className="flex items-center gap-2">
              <Switch checked={form.is_confidential} onCheckedChange={v => setForm({...form, is_confidential: v})} />
              <Label className="text-sm">Mark as Protected / Confidential</Label>
            </div>

            <div className="flex justify-end gap-2 pt-3">
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.title}>
                {saving ? "Saving…" : (entryMode === "type" ? "Save Information" : "Upload Document")}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Supervisor Item-Level Access Control Modal */}
      <Dialog open={!!selectedDocForAccess} onOpenChange={() => setSelectedDocForAccess(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Supervisor Item-Level Access Control
            </DialogTitle>
            <DialogDescription>
              Configure access restrictions specifically for: <strong>{selectedDocForAccess?.title}</strong>
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleUpdateAccessControl} className="space-y-4">
            <div>
              <Label>Access Mode</Label>
              <Select 
                value={accessControlForm.access_mode} 
                onValueChange={v => setAccessControlForm({...accessControlForm, access_mode: v})}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {ACCESS_MODES.map(m => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                {ACCESS_MODES.find(m => m.value === accessControlForm.access_mode)?.desc}
              </p>
            </div>

            {accessControlForm.access_mode === "ALLOW_SELECTED" && (
              <div>
                <Label>Allowed Role Keys (comma separated)</Label>
                <Input 
                  value={accessControlForm.allowed_roles} 
                  onChange={e => setAccessControlForm({...accessControlForm, allowed_roles: e.target.value})} 
                  placeholder="e.g. caseworker, case_aide"
                />
              </div>
            )}

            {accessControlForm.access_mode === "RESTRICTED" && (
              <div>
                <Label>Explicitly Restricted Roles (comma separated)</Label>
                <Input 
                  value={accessControlForm.restricted_roles} 
                  onChange={e => setAccessControlForm({...accessControlForm, restricted_roles: e.target.value})} 
                  placeholder="e.g. external_worker, case_aide"
                />
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setSelectedDocForAccess(null)}>Cancel</Button>
              <Button type="submit" disabled={updatingAccess}>
                {updatingAccess ? "Saving Changes…" : "Apply Access Policy"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

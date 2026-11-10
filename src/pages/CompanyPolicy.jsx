import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { 
  BookOpen, Search, Plus, Edit3, History, Shield, 
  CheckCircle, Clock, ChevronRight, FileText, ArrowLeft, AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import PageHeader from "@/components/shared/PageHeader";
import EmptyState from "@/components/shared/EmptyState";

const POLICY_CATEGORIES = [
  "Governance & Ethics",
  "Child Welfare Practice & Family Safety",
  "Privacy & Data Governance",
  "Human Resources & Workplace Standards",
  "Finance & Procurement",
  "Cultural Protocol & Ceremonial Practices",
  "General Operations",
];

export default function CompanyPolicy() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);

  // Edit / Create Dialog State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isEditingExisting, setIsEditingExisting] = useState(false);
  const [form, setForm] = useState({
    title: "",
    category: "Governance & Ethics",
    content: "",
    department: "Policy and Data",
    status: "published",
    change_summary: "",
  });
  const [saving, setSaving] = useState(false);

  // Version History Modal State
  const [historyModalPolicy, setHistoryModalPolicy] = useState(null);
  const [versions, setVersions] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(false);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const user = await api.auth.me().catch(() => null);
      setCurrentUser(user);

      const data = await api.fetch("/api/v1/policies").catch(() => []);
      setPolicies(Array.isArray(data) ? data : []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  // Determine if current user is authorized to edit policy content
  // Designated policy staff: Angela Yellow Bird, Thomas Favel, or user with policy.write / executive leadership
  const userEmail = (currentUser?.email || "").toLowerCase().trim();
  const userPermissions = Array.isArray(currentUser?.permissions) 
    ? currentUser.permissions.map(p => String(p).toLowerCase()) 
    : [];
  const userRoles = Array.isArray(currentUser?.roles)
    ? currentUser.roles.map(r => typeof r === "string" ? r.toLowerCase() : (r?.key || "").toLowerCase())
    : (currentUser?.role ? [currentUser.role.toLowerCase()] : []);

  const isDesignatedPolicyStaff = 
    userEmail === "angela.yellowbird@redbearlodge.ca" ||
    userEmail === "thomas.favel@redbearlodge.ca" ||
    userPermissions.includes("policy.write") ||
    userRoles.includes("ceo") ||
    userRoles.includes("executive_director") ||
    currentUser?.is_system === true;

  const handleOpenCreate = () => {
    setIsEditingExisting(false);
    setForm({
      title: "",
      category: "Governance & Ethics",
      content: "",
      department: "Policy and Data",
      status: "published",
      change_summary: "Initial publication",
    });
    setIsEditModalOpen(true);
  };

  const handleOpenEdit = (policy) => {
    setIsEditingExisting(true);
    setForm({
      title: policy.title,
      category: policy.category,
      content: policy.content,
      department: policy.department || "Policy and Data",
      status: policy.status || "published",
      change_summary: "",
    });
    setIsEditModalOpen(true);
  };

  const handleSavePolicy = async (e) => {
    e.preventDefault();
    if (!form.title || !form.content) return;
    if (isEditingExisting && !form.change_summary.trim()) {
      alert("A change summary is required for audit history.");
      return;
    }

    setSaving(true);
    try {
      if (isEditingExisting && selectedPolicy) {
        await api.fetch(`/api/v1/policies/${selectedPolicy.id}`, {
          method: "PUT",
          body: JSON.stringify(form),
        });
      } else {
        await api.fetch("/api/v1/policies", {
          method: "POST",
          body: JSON.stringify(form),
        });
      }

      setIsEditModalOpen(false);
      await loadPolicies();

      // Refresh selected policy view if active
      if (selectedPolicy) {
        const refreshed = await api.fetch(`/api/v1/policies/${selectedPolicy.id}`).catch(() => null);
        if (refreshed) setSelectedPolicy(refreshed);
      }
    } catch (err) {
      alert("Error saving policy: " + (err.message || "Unauthorized"));
    } finally {
      setSaving(false);
    }
  };

  const handleOpenHistory = async (policy) => {
    setHistoryModalPolicy(policy);
    setLoadingVersions(true);
    try {
      const vData = await api.fetch(`/api/v1/policies/${policy.id}/versions`).catch(() => []);
      setVersions(Array.isArray(vData) ? vData : []);
    } finally {
      setLoadingVersions(false);
    }
  };

  const filtered = policies.filter(p => {
    const matchesSearch = !search || 
      p.title?.toLowerCase().includes(search.toLowerCase()) ||
      p.content?.toLowerCase().includes(search.toLowerCase()) ||
      p.category?.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === "all" || p.category === selectedCategory;
    return matchesSearch && matchesCategory;
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
        title="Company Policy Manual" 
        subtitle="Official agency standards, practice guidelines, and governance directives" 
        actions={
          isDesignatedPolicyStaff && (
            <Button onClick={handleOpenCreate}>
              <Plus className="w-4 h-4 mr-2" /> New Policy
            </Button>
          )
        } 
      />

      {/* Selected Policy Detail View */}
      {selectedPolicy ? (
        <div className="space-y-4">
          <Button variant="ghost" size="sm" onClick={() => setSelectedPolicy(null)} className="mb-2">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Policy List
          </Button>

          <div className="bg-card rounded-xl border border-border p-6 space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline">{selectedPolicy.category}</Badge>
                  <Badge className="bg-emerald-600 text-white">Version {selectedPolicy.version}.0</Badge>
                  <span className="text-xs text-muted-foreground">
                    Effective: {new Date(selectedPolicy.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <h2 className="text-2xl font-bold font-heading text-foreground">{selectedPolicy.title}</h2>
              </div>

              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => handleOpenHistory(selectedPolicy)}>
                  <History className="w-4 h-4 mr-1" /> Version History
                </Button>
                {isDesignatedPolicyStaff && (
                  <Button size="sm" onClick={() => handleOpenEdit(selectedPolicy)}>
                    <Edit3 className="w-4 h-4 mr-1" /> Edit Policy
                  </Button>
                )}
              </div>
            </div>

            <div className="prose prose-slate dark:prose-invert max-w-none text-foreground whitespace-pre-wrap leading-relaxed">
              {selectedPolicy.content}
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Search & Category Filter */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="relative flex-1 max-w-md w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input 
                placeholder="Search policy titles and text…" 
                value={search} 
                onChange={e => setSearch(e.target.value)} 
                className="pl-9" 
              />
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Label className="text-xs text-muted-foreground whitespace-nowrap">Category:</Label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {POLICY_CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Policy Cards Grid */}
          {filtered.length === 0 ? (
            <EmptyState 
              icon={BookOpen} 
              title="No company policies found" 
              action={isDesignatedPolicyStaff && (
                <Button onClick={handleOpenCreate}>
                  <Plus className="w-4 h-4 mr-2" /> Add Initial Policy
                </Button>
              )} 
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filtered.map(p => (
                <div 
                  key={p.id} 
                  className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow flex flex-col justify-between group"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <Badge variant="outline" className="text-xs">
                        {p.category}
                      </Badge>
                      <Badge variant="secondary" className="text-[10px]">
                        v{p.version}.0
                      </Badge>
                    </div>

                    <div>
                      <h4 className="font-semibold text-foreground text-base group-hover:text-primary transition-colors">
                        {p.title}
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-3">
                        {p.content}
                      </p>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-border/50 mt-4 flex items-center justify-between text-xs text-muted-foreground">
                    <span>Updated: {new Date(p.updated_at).toLocaleDateString()}</span>
                    
                    <div className="flex items-center gap-1">
                      {isDesignatedPolicyStaff && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-8 px-2 text-xs" 
                          onClick={(e) => { e.stopPropagation(); handleOpenEdit(p); }}
                        >
                          <Edit3 className="w-3.5 h-3.5 mr-1" /> Edit
                        </Button>
                      )}
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-8 px-2 text-xs text-primary"
                        onClick={() => setSelectedPolicy(p)}
                      >
                        Read <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Edit / Create Policy Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary" />
              {isEditingExisting ? "Edit Company Policy" : "Draft New Company Policy"}
            </DialogTitle>
            <DialogDescription>
              {isEditingExisting 
                ? "Edits increment the version and record an auditable change history." 
                : "Author and publish a new agency policy document."}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSavePolicy} className="space-y-4">
            <div>
              <Label>Policy Title *</Label>
              <Input 
                value={form.title} 
                onChange={e => setForm({...form, title: e.target.value})} 
                placeholder="e.g. Traditional Medicine & Ceremonial Leave Policy"
                required 
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Policy Category</Label>
                <Select value={form.category} onValueChange={v => setForm({...form, category: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {POLICY_CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Responsible Department</Label>
                <Input 
                  value={form.department} 
                  onChange={e => setForm({...form, department: e.target.value})} 
                  placeholder="Policy and Data"
                />
              </div>
            </div>

            <div>
              <Label>Policy Content *</Label>
              <Textarea 
                rows={10} 
                value={form.content} 
                onChange={e => setForm({...form, content: e.target.value})} 
                placeholder="Enter formal company policy statements, procedures, obligations, and references..."
                required 
              />
            </div>

            <div>
              <Label>Auditable Change Summary *</Label>
              <Input 
                value={form.change_summary} 
                onChange={e => setForm({...form, change_summary: e.target.value})} 
                placeholder={isEditingExisting ? "Describe the exact change and reason (e.g. updated per annual AGM review)" : "Initial policy publication"}
                required 
              />
            </div>

            <div className="flex justify-end gap-2 pt-3">
              <Button type="button" variant="outline" onClick={() => setIsEditModalOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.title || !form.content}>
                {saving ? "Saving…" : (isEditingExisting ? "Publish New Version" : "Publish Policy")}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Version History Modal */}
      <Dialog open={!!historyModalPolicy} onOpenChange={() => setHistoryModalPolicy(null)}>
        <DialogContent className="max-w-xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2">
              <History className="w-5 h-5 text-primary" />
              Version History — {historyModalPolicy?.title}
            </DialogTitle>
            <DialogDescription>
              Chronological log of revisions, authors, and change summaries.
            </DialogDescription>
          </DialogHeader>

          {loadingVersions ? (
            <div className="flex justify-center p-8">
              <div className="w-6 h-6 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
            </div>
          ) : versions.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">No revision history found.</p>
          ) : (
            <div className="space-y-4">
              {versions.map(v => (
                <div key={v.id} className="border border-border rounded-lg p-4 bg-muted/30 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-foreground">Version {v.version_number}.0</span>
                    <span className="text-xs text-muted-foreground">{new Date(v.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-foreground"><strong>Change Summary:</strong> {v.change_summary || "—"}</p>
                  <p className="text-xs text-muted-foreground"><strong>Author:</strong> {v.author_name || "Policy Staff"}</p>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}


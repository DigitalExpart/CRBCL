import React, { useState, useEffect } from "react";
import {
  Shield, Check, Search, Lock, Unlock, AlertTriangle,
  Settings, CheckCircle2, XCircle, ExternalLink, Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { toast } from "@/components/ui/use-toast";
import { ROLES } from "@/constants/roles";

const CATEGORIES = [
  "All",
  "Intake & Reception",
  "Intake & Referrals",
  "Case & Client",
  "Resource & Placements",
  "Executive Leadership",
  "Board of Governors",
  "Operations & Facilities",
  "Finance & Administration",
  "Human Resources",
  "Administration & IT",
  "General Operations",
];

export default function DashboardControlCentre() {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [editingWorkspace, setEditingWorkspace] = useState(null);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [savingRoles, setSavingRoles] = useState(false);
  const [confirmProtectedGrant, setConfirmProtectedGrant] = useState(false);
  const [togglingKey, setTogglingKey] = useState(null);

  const fetchWorkspaces = async () => {
    try {
      const res = await fetch("/api/v1/admin/dashboards", {
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to load dashboard registry");
      const data = await res.json();
      setWorkspaces(data);
    } catch (err) {
      toast({
        title: "Error loading registry",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const handleToggleStatus = async (workspace) => {
    setTogglingKey(workspace.key);
    const newStatus = !workspace.is_enabled;
    try {
      const res = await fetch(`/api/v1/admin/dashboards/${workspace.key}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ is_enabled: newStatus }),
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.error?.message || "Failed to update workspace status");
      }
      const updated = await res.json();
      setWorkspaces((prev) => prev.map((w) => (w.key === updated.key ? updated : w)));
      toast({
        title: `Workspace ${newStatus ? "Enabled" : "Disabled"}`,
        description: `${workspace.name} is now ${newStatus ? "active and available" : "temporarily disabled"} across the platform.`,
      });
    } catch (err) {
      toast({
        title: "Status Update Failed",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setTogglingKey(null);
    }
  };

  const handleOpenRoleModal = (workspace) => {
    setEditingWorkspace(workspace);
    setSelectedRoles([...workspace.authorized_roles]);
    setConfirmProtectedGrant(false);
  };

  const handleToggleRole = (roleKey) => {
    setSelectedRoles((prev) =>
      prev.includes(roleKey) ? prev.filter((r) => r !== roleKey) : [...prev, roleKey]
    );
  };

  const handleSaveRoles = async () => {
    if (!editingWorkspace) return;
    setSavingRoles(true);
    try {
      const res = await fetch(`/api/v1/admin/dashboards/${editingWorkspace.key}/roles`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ role_keys: selectedRoles }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail?.error?.message || "Failed to update role access");
      }
      const updated = await res.json();
      setWorkspaces((prev) => prev.map((w) => (w.key === updated.key ? updated : w)));
      toast({
        title: "Role Access Saved",
        description: `Authoritative permissions for ${editingWorkspace.name} have been updated.`,
      });
      setEditingWorkspace(null);
    } catch (err) {
      toast({
        title: "Access Update Failed",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setSavingRoles(false);
    }
  };

  const filteredWorkspaces = workspaces.filter((w) => {
    const matchesSearch =
      w.name.toLowerCase().includes(search.toLowerCase()) ||
      w.route.toLowerCase().includes(search.toLowerCase()) ||
      w.key.toLowerCase().includes(search.toLowerCase()) ||
      w.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory =
      categoryFilter === "All" || w.category.toLowerCase() === categoryFilter.toLowerCase();
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      {/* Administrative Unified Access Banner */}
      <div className="bg-primary/10 border border-primary/20 rounded-xl p-4 flex items-start gap-3">
        <Shield className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
        <div className="text-xs text-foreground space-y-1">
          <p className="font-semibold text-sm text-primary">
            Unified Administrator Access & Platform Governance
          </p>
          <p className="text-muted-foreground">
            The Dashboard Control Centre manages organizational availability and authoritative role assignments.
            System Administrators hold full access to oversee, launch, and support all staff dashboards—including Front Desk,
            Office Coordinator, Navigator, Intake, HR, Case Management, and team workspaces across the platform.
          </p>
        </div>
      </div>

      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
          <Input
            placeholder="Search dashboards or routes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-card"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-1">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
                categoryFilter === cat
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Registry Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/40 border-b border-border text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">Workspace / Route</th>
                <th className="px-4 py-3.5">Category</th>
                <th className="px-4 py-3.5">Classification</th>
                <th className="px-4 py-3.5">Availability</th>
                <th className="px-4 py-3.5">Authorized Roles</th>
                <th className="px-4 py-3.5 text-right">Access Controls</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-muted-foreground">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-primary" />
                    Loading workspace registry...
                  </td>
                </tr>
              ) : filteredWorkspaces.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-muted-foreground">
                    No matching dashboards found.
                  </td>
                </tr>
              ) : (
                filteredWorkspaces.map((ws) => (
                  <tr key={ws.key} className="hover:bg-muted/20 transition-colors">
                    <td className="px-5 py-4">
                      <div className="font-semibold text-foreground flex items-center gap-2">
                        {ws.name}
                        {ws.has_protected_data && (
                          <span title="Contains Confidential Child Welfare or Medical Data" className="text-amber-500">
                            <Lock className="w-3.5 h-3.5" />
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="text-xs bg-muted px-1.5 py-0.5 rounded text-muted-foreground font-mono">
                          {ws.route}
                        </code>
                        <span className="text-[10px] text-muted-foreground capitalize">
                          • {ws.workspace_type}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{ws.description}</p>
                    </td>

                    <td className="px-4 py-4 text-xs text-muted-foreground whitespace-nowrap">
                      {ws.category}
                    </td>

                    <td className="px-4 py-4 whitespace-nowrap">
                      {ws.has_protected_data ? (
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                          <Lock className="w-3 h-3" />
                          {ws.security_classification.replace(/_/g, " ")}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-muted text-muted-foreground">
                          <Unlock className="w-3 h-3" />
                          {ws.security_classification.replace(/_/g, " ")}
                        </span>
                      )}
                    </td>

                    <td className="px-4 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleToggleStatus(ws)}
                        disabled={togglingKey === ws.key}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold transition-all ${
                          ws.is_enabled
                            ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/25"
                            : "bg-muted text-muted-foreground hover:bg-muted/80 opacity-70"
                        }`}
                      >
                        {togglingKey === ws.key ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : ws.is_enabled ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-muted-foreground" />
                        )}
                        {ws.is_enabled ? "Active" : "Disabled"}
                      </button>
                    </td>

                    <td className="px-4 py-4">
                      {ws.primary_permission_key === null ? (
                        <span className="text-xs text-muted-foreground italic">Universal Staff Access</span>
                      ) : (
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {ws.authorized_roles.slice(0, 3).map((r) => (
                            <span
                              key={r}
                              className="px-1.5 py-0.5 bg-muted rounded text-[10px] font-mono text-muted-foreground"
                            >
                              {r}
                            </span>
                          ))}
                          {ws.authorized_roles.length > 3 && (
                            <span className="px-1.5 py-0.5 bg-muted rounded text-[10px] font-mono text-muted-foreground">
                              +{ws.authorized_roles.length - 3} more
                            </span>
                          )}
                        </div>
                      )}
                    </td>

                    <td className="px-4 py-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        {ws.primary_permission_key !== null && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleOpenRoleModal(ws)}
                            className="h-8 gap-1.5 text-xs"
                          >
                            <Settings className="w-3.5 h-3.5" />
                            Manage Roles
                          </Button>
                        )}
                        <a
                          href={ws.route}
                          target="_blank"
                          rel="noreferrer"
                          title="Open workspace route"
                          className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Role Access Management Modal */}
      {editingWorkspace && (
        <Dialog open={!!editingWorkspace} onOpenChange={() => setEditingWorkspace(null)}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-primary" />
                Manage Role Access: {editingWorkspace.name}
              </DialogTitle>
              <DialogDescription>
                Select which staff roles possess the authoritative permission key:{" "}
                <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-foreground font-semibold">
                  {editingWorkspace.primary_permission_key}
                </code>
              </DialogDescription>
            </DialogHeader>

            {editingWorkspace.has_protected_data && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 flex-shrink-0 mt-0.5" />
                <div>
                  <strong>Protected Data Warning:</strong> This workspace accesses restricted child welfare, clinical, or confidential community data.
                  Only grant access to roles with statutory, clinical, or operational necessity.
                </div>
              </div>
            )}

            <div className="py-2 max-h-72 overflow-y-auto space-y-2 pr-1">
              {ROLES.map((r) => {
                const isSelected = selectedRoles.includes(r.key);
                return (
                  <label
                    key={r.key}
                    onClick={() => handleToggleRole(r.key)}
                    className={`flex items-center justify-between p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? "bg-primary/5 border-primary/40 text-foreground font-medium"
                        : "bg-card border-border text-muted-foreground hover:border-border/80"
                    }`}
                  >
                    <div>
                      <p className="font-semibold text-foreground">{r.label}</p>
                      <p className="text-[10px] text-muted-foreground font-mono mt-0.5">key: {r.key}</p>
                    </div>
                    <div
                      className={`w-5 h-5 rounded flex items-center justify-center border transition-all ${
                        isSelected
                          ? "bg-primary border-primary text-primary-foreground"
                          : "border-muted-foreground/30 bg-background"
                      }`}
                    >
                      {isSelected && <Check className="w-3.5 h-3.5" />}
                    </div>
                  </label>
                );
              })}
            </div>

            {editingWorkspace.has_protected_data && (
              <div className="pt-2 border-t border-border flex items-start gap-2">
                <input
                  type="checkbox"
                  id="confirm-protected"
                  checked={confirmProtectedGrant}
                  onChange={(e) => setConfirmProtectedGrant(e.target.checked)}
                  className="mt-0.5 rounded border-muted-foreground/40 text-primary focus:ring-primary h-4 w-4"
                />
                <label htmlFor="confirm-protected" className="text-xs text-foreground cursor-pointer">
                  <strong>Explicit Authorization Confirmation:</strong> I confirm that selected roles require access to confidential community, child welfare, clinical, or governance records.
                </label>
              </div>
            )}

            <DialogFooter className="flex items-center justify-between sm:justify-between w-full">
              <div className="text-xs text-muted-foreground">
                {selectedRoles.length} role{selectedRoles.length !== 1 ? "s" : ""} selected
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" onClick={() => setEditingWorkspace(null)} disabled={savingRoles}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveRoles}
                  disabled={savingRoles || (editingWorkspace.has_protected_data && !confirmProtectedGrant)}
                  className="gap-2"
                >
                  {savingRoles && <Loader2 className="w-4 h-4 animate-spin" />}
                  Save Role Permissions
                </Button>
              </div>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { api } from "@/api";
import TeamAccessPicker from "@/components/admin/TeamAccessPicker";

import { toast } from "@/components/ui/use-toast";

const ROLES = [
  { key: "ceo", label: "Chief Executive Officer (CEO) — Strategic Leadership & Governance" },
  { key: "executive_director", label: "Executive Director — Cross-Agency Leadership" },
  { key: "director_manager", label: "Director / Manager — Departmental Operations" },
  { key: "supervisor", label: "Supervisor — Casework Approvals & Reviews" },
  { key: "caseworker", label: "Caseworker — Direct Client & Case Management" },
  { key: "case_aide", label: "Case Aide — Support Worker" },
  { key: "finance_staff", label: "Finance Staff — Billing & Invoices" },
  { key: "cultural_worker", label: "Cultural Worker — Cultural Supports & Elders" },
  { key: "clinical_staff", label: "Clinical Staff — Medical & Therapy" },
  { key: "it_admin", label: "IT Administrator — Standalone System Admin" },
];

export default function EditUserDialog({ user, open, onOpenChange, onSaved }) {
  const [role, setRole] = useState("caseworker");
  const [teamAccess, setTeamAccess] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) {
      const userRole = (user.roles && user.roles[0]) || user.role || "caseworker";
      setRole(userRole);
      setTeamAccess(user.team_access || []);
      setError("");
    }
  }, [user]);

  const handleSave = async () => {
    setLoading(true);
    setError("");
    try {
      await api.patch(`/api/v1/users/${user.id}`, {
        role,
        role_keys: [role],
        team_access: teamAccess,
      });
      try {
        const stored = localStorage.getItem("crbcl_current_user");
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed && (parsed.id === user.id || parsed.email === user.email)) {
            parsed.role = role;
            parsed.roles = [role];
            parsed.team_access = teamAccess;
            localStorage.setItem("crbcl_current_user", JSON.stringify(parsed));
          }
        }
      } catch (e) {}

      toast({
        title: "Role & Teams Updated",
        description: `User role and team access have been successfully updated.`,
      });
      if (onSaved) onSaved();
      onOpenChange(false);
    } catch (err) {
      const detailMsg = err.response?.data?.detail?.error?.message || err.response?.data?.detail || err.message;
      if (err.response?.status === 401 || (typeof detailMsg === "string" && detailMsg.toLowerCase().includes("token"))) {
        setError("Your session has expired. Please refresh the page or sign in again to save role changes.");
      } else {
        setError(typeof detailMsg === "string" ? detailMsg : "Failed to update user role.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit User Roles & Access</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label className="text-muted-foreground">User</Label>
            <p className="text-sm font-medium">{user?.full_name || user?.email}</p>
            <p className="text-xs text-muted-foreground font-mono">{user?.email}</p>
          </div>
          <div className="space-y-2">
            <Label>Assigned Role</Label>
            <Select value={role} onValueChange={setRole} disabled={loading}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {ROLES.map((r) => (
                  <SelectItem key={r.key} value={r.key}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <TeamAccessPicker value={teamAccess} onChange={setTeamAccess} disabled={loading} />
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
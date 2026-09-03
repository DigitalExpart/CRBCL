import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { api } from "@/api";
import TeamAccessPicker from "@/components/admin/TeamAccessPicker";

const ROLES = [
  { key: "caseworker", label: "Caseworker — Standard Case Files" },
  { key: "supervisor", label: "Supervisor — Approval & Reviews" },
  { key: "director_manager", label: "Director / Manager — Operational Oversight" },
  { key: "executive_director", label: "Executive Director — Full Administrator" },
  { key: "case_aide", label: "Case Aide — Support Worker" },
  { key: "finance_staff", label: "Finance Staff — Billing & Invoices" },
  { key: "cultural_worker", label: "Cultural Worker — Programs & Elders" },
  { key: "clinical_staff", label: "Clinical Staff — Medical & Therapy" },
  { key: "it_admin", label: "IT Administrator — Security & Config" },
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
      await api.patch(`/users/${user.id}`, {
        role,
        role_keys: [role],
        team_access: teamAccess,
      });
      if (onSaved) onSaved();
      onOpenChange(false);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to update user.");
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
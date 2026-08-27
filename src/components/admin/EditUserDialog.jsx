import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { api } from "@/api";
import TeamAccessPicker from "@/components/admin/TeamAccessPicker";

export default function EditUserDialog({ user, open, onOpenChange, onSaved }) {
  const [role, setRole] = useState("user");
  const [teamAccess, setTeamAccess] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) {
      setRole(user.role || "user");
      setTeamAccess(user.team_access || []);
      setError("");
    }
  }, [user]);

  const handleSave = async () => {
    setLoading(true);
    setError("");
    try {
      await api.entities.User.update(user.id, { role, team_access: teamAccess });
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
          <DialogTitle>Edit User</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label className="text-muted-foreground">User</Label>
            <p className="text-sm font-medium">{user?.full_name || user?.email}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
          <div className="space-y-2">
            <Label>Role</Label>
            <Select value={role} onValueChange={setRole} disabled={loading}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="user">User — Standard access</SelectItem>
                <SelectItem value="admin">Admin — Full access</SelectItem>
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
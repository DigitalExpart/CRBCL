import React, { useState, useEffect, useCallback } from "react";
import { base44 } from "@/api/base44Client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, UserPlus, Search, Shield, Users as UsersIcon, Pencil, Ban } from "lucide-react";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";
import InviteUserDialog from "@/components/admin/InviteUserDialog";
import EditUserDialog from "@/components/admin/EditUserDialog";

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [inviteOpen, setInviteOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [error, setError] = useState("");

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const list = await base44.entities.User.list();
      setUsers(list);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const filtered = users.filter((u) => {
    const q = search.toLowerCase();
    return (
      (u.email || "").toLowerCase().includes(q) ||
      (u.full_name || "").toLowerCase().includes(q) ||
      JSON.stringify(u.team_access || []).toLowerCase().includes(q)
    );
  });

  const adminCount = users.filter((u) => u.role === "admin").length;
  const assignedCount = users.filter((u) => {
    const ta = u.team_access;
    return Array.isArray(ta) && ta.length > 0;
  }).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin Dashboard"
        subtitle="Manage user access, roles, and team assignments"
        actions={
          <Button onClick={() => setInviteOpen(true)}>
            <UserPlus className="w-4 h-4" />
            Create User
          </Button>
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <UsersIcon className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-2xl font-bold">{users.length}</p>
            <p className="text-xs text-muted-foreground">Total Users</p>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
            <Shield className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <p className="text-2xl font-bold">{adminCount}</p>
            <p className="text-xs text-muted-foreground">Admins</p>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
            <UserPlus className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <p className="text-2xl font-bold">{assignedCount}</p>
            <p className="text-xs text-muted-foreground">Has Team Access</p>
          </div>
        </div>
      </div>

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by name, email, or team..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : error ? (
          <div className="py-16">
            <EmptyState icon={Ban} title="Error loading users" description={error} />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState
              icon={UsersIcon}
              title={search ? "No users found" : "No users yet"}
              description={search ? "Try a different search term." : "Invite your first team member to get started."}
              action={!search && <Button onClick={() => setInviteOpen(true)}><UserPlus className="w-4 h-4" />Invite User</Button>}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-muted-foreground">
                <tr>
                  <th className="text-left font-medium px-4 py-3">Name</th>
                  <th className="text-left font-medium px-4 py-3">Email</th>
                  <th className="text-left font-medium px-4 py-3">Role</th>
                  <th className="text-left font-medium px-4 py-3">Team Access</th>
                  <th className="text-right font-medium px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((u) => (
                  <tr key={u.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-medium">
                      {u.full_name || <span className="text-muted-foreground italic">Not set</span>}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={u.role === "admin" ? "Active" : "Pending"} />
                      <span className="ml-2 text-xs text-muted-foreground capitalize">{u.role}</span>
                    </td>
                    <td className="px-4 py-3">
                      {(() => {
                        const ta = u.team_access || [];
                        if (ta.includes("all")) {
                          return <StatusBadge status="Active" />;
                        }
                        if (ta.length === 0) {
                          return <span className="text-xs text-muted-foreground">No access</span>;
                        }
                        return <span className="text-xs text-muted-foreground">{ta.length} team{ta.length !== 1 ? "s" : ""}</span>;
                      })()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="ghost" size="sm" onClick={() => setEditUser(u)}>
                        <Pencil className="w-4 h-4" />
                        Edit
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <InviteUserDialog open={inviteOpen} onOpenChange={setInviteOpen} onInvited={loadUsers} />
      <EditUserDialog user={editUser} open={!!editUser} onOpenChange={(v) => !v && setEditUser(null)} onSaved={loadUsers} />
    </div>
  );
}
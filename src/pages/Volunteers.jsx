import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Plus, UserCheck, Clock, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

export default function Volunteers() {
  const [volunteers, setVolunteers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    status: "APPLIED",
    availability: "",
    skills: "",
    interests: "",
  });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.entities.Volunteer.list();
      setVolunteers(Array.isArray(res) ? res : []);
    } catch (e) {
      console.error("Failed to load volunteers", e);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.entities.Volunteer.create(form);
      setShowForm(false);
      load();
    } catch (err) {
      console.error("Failed to create volunteer", err);
    }
    setSaving(false);
  };

  const filtered = volunteers.filter((v) => {
    const q = search.toLowerCase();
    const name = `${v.first_name} ${v.last_name}`.toLowerCase();
    return !search || name.includes(q) || v.email?.toLowerCase().includes(q);
  });

  if (loading)
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Volunteer Coordination"
        subtitle={`${volunteers.length} registered volunteers`}
        actions={
          <Button onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4 mr-2" /> Add Volunteer
          </Button>
        }
      />

      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Input
            placeholder="Search volunteers by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
          <UserCheck className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={UserCheck} title="No Volunteers Registered" description="Add volunteers, track screening applications, and log service hours." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((v) => (
            <div key={v.id} className="p-4 border rounded-xl bg-card shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-base">{v.first_name} {v.last_name}</h3>
                <StatusBadge status={v.status} />
              </div>
              <p className="text-xs text-muted-foreground">{v.email}</p>
              <div className="flex items-center justify-between text-xs pt-2 border-t text-muted-foreground">
                <span className="flex items-center gap-1 text-primary cursor-pointer hover:underline">
                  <Clock className="w-3.5 h-3.5" /> Log Hours
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Register Volunteer</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>First Name *</Label>
                <Input required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
              </div>
              <div>
                <Label>Last Name *</Label>
                <Input required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
              </div>
            </div>

            <div>
              <Label>Email *</Label>
              <Input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Add Volunteer"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const CASE_TYPES = ["Child Protection", "Family Support", "Youth Services", "Mental Health", "Housing", "Cultural", "Crisis Intervention", "Prevention", "Other"];
const PRIORITIES = ["Low", "Medium", "High", "Urgent", "Critical"];
const RISK_LEVELS = ["Low", "Medium", "High", "Critical"];
const REFERRAL_SOURCES = ["Self-Referral", "Family", "School", "Healthcare", "Law Enforcement", "Government Agency", "Community", "Other"];

export default function CaseFormDialog({ open, onOpenChange, onSubmit, initialData }) {
  const isEdit = !!initialData;
  const [form, setForm] = useState(initialData || {
    title: "", case_type: "Family Support", priority: "Medium", risk_level: "Low",
    referral_source: "", assigned_worker_name: "", description: "", intake_date: new Date().toISOString().split("T")[0],
  });
  const [saving, setSaving] = useState(false);

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    await onSubmit(form);
    setSaving(false);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-heading">{isEdit ? "Edit Case" : "New Case"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Title *</Label>
            <Input value={form.title} onChange={e => update("title", e.target.value)} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Case Type</Label>
              <Select value={form.case_type} onValueChange={v => update("case_type", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{CASE_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label>Priority</Label>
              <Select value={form.priority} onValueChange={v => update("priority", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{PRIORITIES.map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Risk Level</Label>
              <Select value={form.risk_level} onValueChange={v => update("risk_level", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{RISK_LEVELS.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label>Referral Source</Label>
              <Select value={form.referral_source} onValueChange={v => update("referral_source", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{REFERRAL_SOURCES.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Intake Date</Label>
              <Input type="date" value={form.intake_date} onChange={e => update("intake_date", e.target.value)} />
            </div>
            <div>
              <Label>Assigned Worker</Label>
              <Input value={form.assigned_worker_name || ""} onChange={e => update("assigned_worker_name", e.target.value)} placeholder="Worker name" />
            </div>
          </div>
          <div>
            <Label>Description</Label>
            <Textarea rows={3} value={form.description || ""} onChange={e => update("description", e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving || !form.title}>
              {saving ? "Saving…" : isEdit ? "Update Case" : "Create Case"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
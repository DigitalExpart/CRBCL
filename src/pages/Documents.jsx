import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { Plus, Search, FileText, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";

const CATEGORIES = ["Case File", "Policy", "Report", "Form", "Legal", "Financial", "HR", "Training", "General"];

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", category: "General", description: "", is_confidential: false });
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = async () => { setLoading(true); setDocs(await api.entities.Document.list("-created_date", 50)); setLoading(false); };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!file) return;
    setSaving(true);
    const { file_url } = await api.integrations.Core.UploadFile({ file });
    await api.entities.Document.create({ ...form, file_url, file_type: file.name.split(".").pop(), file_size: `${(file.size / 1024).toFixed(1)} KB` });
    setSaving(false);
    setShowForm(false);
    setFile(null);
    load();
  };

  const filtered = docs.filter(d => !search || d.title?.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <PageHeader title="Documents" subtitle={`${docs.length} documents`} actions={<Button onClick={() => setShowForm(true)}><Upload className="w-4 h-4 mr-2" /> Upload</Button>} />
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search documents…" value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
      </div>
      {filtered.length === 0 ? (
        <EmptyState icon={FileText} title="No documents" action={<Button onClick={() => setShowForm(true)}><Upload className="w-4 h-4 mr-2" /> Upload Document</Button>} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(d => (
            <a key={d.id} href={d.file_url} target="_blank" rel="noopener noreferrer" className="bg-card rounded-xl border border-border p-4 hover:shadow-md transition-shadow block">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-foreground truncate">{d.title}</p>
                  <p className="text-xs text-muted-foreground">{d.category} • {d.file_type?.toUpperCase() || "—"} • {d.file_size || "—"}</p>
                  {d.is_confidential && <span className="text-xs text-destructive font-medium">🔒 Confidential</span>}
                  {d.description && <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{d.description}</p>}
                </div>
              </div>
            </a>
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle className="font-heading">Upload Document</DialogTitle></DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div><Label>Title *</Label><Input value={form.title} onChange={e => setForm({...form, title: e.target.value})} required /></div>
            <div><Label>Category</Label><Select value={form.category} onValueChange={v => setForm({...form, category: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent></Select></div>
            <div>
              <Label>File *</Label>
              <Input type="file" onChange={e => setFile(e.target.files?.[0] || null)} required />
            </div>
            <div><Label>Description</Label><Textarea rows={2} value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
            <div className="flex items-center gap-2">
              <Switch checked={form.is_confidential} onCheckedChange={v => setForm({...form, is_confidential: v})} />
              <Label>Confidential</Label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={saving || !form.title || !file}>{saving ? "Uploading…" : "Upload"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
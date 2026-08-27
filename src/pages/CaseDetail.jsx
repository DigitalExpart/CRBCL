import React, { useState, useEffect } from "react";
import { api } from "@/api";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Edit2, Trash2, Plus, FileText, Clock, AlertTriangle, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PageHeader from "@/components/shared/PageHeader";
import StatusBadge from "@/components/shared/StatusBadge";
import CaseFormDialog from "@/components/cases/CaseFormDialog";

export default function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEdit, setShowEdit] = useState(false);
  const [newNote, setNewNote] = useState("");
  const [noteType, setNoteType] = useState("Progress Note");
  const [addingNote, setAddingNote] = useState(false);

  useEffect(() => {
    async function load() {
      const [caseItem, caseNotes] = await Promise.all([
        api.entities.Case.filter({ id }),
        api.entities.CaseNote.filter({ case_id: id }, "-created_date", 50),
      ]);
      setCaseData(caseItem[0] || null);
      setNotes(caseNotes);
      setLoading(false);
    }
    load();
  }, [id]);

  const handleUpdate = async (form) => {
    await api.entities.Case.update(id, form);
    setCaseData({ ...caseData, ...form });
  };

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this case?")) {
      await api.entities.Case.delete(id);
      navigate("/cases");
    }
  };

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    setAddingNote(true);
    const note = await api.entities.CaseNote.create({
      case_id: id,
      content: newNote,
      note_type: noteType,
      subject: noteType,
    });
    setNotes([note, ...notes]);
    setNewNote("");
    setAddingNote(false);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" /></div>;
  }

  if (!caseData) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-heading font-semibold mb-2">Case not found</h2>
        <Link to="/cases" className="text-primary hover:underline">← Back to cases</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link to="/cases" className="hover:text-primary transition-colors flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Cases
        </Link>
        <span>/</span>
        <span className="text-foreground">{caseData.title}</span>
      </div>

      <PageHeader
        title={caseData.title}
        subtitle={`${caseData.case_number || "No case number"} • ${caseData.case_type}`}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowEdit(true)}>
              <Edit2 className="w-4 h-4 mr-1" /> Edit
            </Button>
            <Button variant="outline" size="sm" className="text-destructive" onClick={handleDelete}>
              <Trash2 className="w-4 h-4 mr-1" /> Delete
            </Button>
          </div>
        }
      />

      {/* Case Info Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Details Card */}
          <div className="bg-card rounded-xl border border-border p-5 space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Case Details</h3>
            {caseData.description && (
              <p className="text-sm text-muted-foreground leading-relaxed">{caseData.description}</p>
            )}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <InfoItem label="Status" value={<StatusBadge status={caseData.status} />} />
              <InfoItem label="Priority" value={<StatusBadge status={caseData.priority} />} />
              <InfoItem label="Risk Level" value={<StatusBadge status={caseData.risk_level} />} />
              <InfoItem label="Referral Source" value={caseData.referral_source || "—"} />
              <InfoItem label="Intake Date" value={caseData.intake_date || "—"} />
              <InfoItem label="Target Resolution" value={caseData.target_resolution_date || "—"} />
            </div>
          </div>

          {/* Service Plan */}
          {caseData.service_plan && (
            <div className="bg-card rounded-xl border border-border p-5">
              <h3 className="text-sm font-semibold text-foreground mb-2">Service Plan</h3>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">{caseData.service_plan}</p>
            </div>
          )}

          {/* Case Notes */}
          <div className="bg-card rounded-xl border border-border p-5 space-y-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" /> Case Notes ({notes.length})
            </h3>
            <div className="space-y-3">
              <div className="flex gap-2">
                <Select value={noteType} onValueChange={setNoteType}>
                  <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {["Progress Note", "Contact Note", "Assessment", "Incident Report", "Meeting Summary", "General"].map(t => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Textarea
                rows={3}
                placeholder="Add a case note…"
                value={newNote}
                onChange={e => setNewNote(e.target.value)}
              />
              <Button size="sm" onClick={handleAddNote} disabled={addingNote || !newNote.trim()}>
                <Plus className="w-4 h-4 mr-1" /> {addingNote ? "Adding…" : "Add Note"}
              </Button>
            </div>
            <div className="space-y-3 mt-4">
              {notes.map(note => (
                <div key={note.id} className="border border-border rounded-lg p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={note.note_type} />
                      {note.is_confidential && <span className="text-xs text-destructive font-medium">CONFIDENTIAL</span>}
                    </div>
                    <span className="text-xs text-muted-foreground">{new Date(note.created_date).toLocaleDateString()}</span>
                  </div>
                  <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{note.content}</p>
                </div>
              ))}
              {notes.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">No notes yet</p>}
            </div>
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-4">
          <div className="bg-card rounded-xl border border-border p-5 space-y-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <User className="w-4 h-4 text-primary" /> Assigned Worker
            </h3>
            <p className="text-sm">{caseData.assigned_worker_name || "Unassigned"}</p>
          </div>

          <div className="bg-card rounded-xl border border-border p-5 space-y-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Clock className="w-4 h-4 text-primary" /> Timeline
            </h3>
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex justify-between"><span>Created</span><span>{new Date(caseData.created_date).toLocaleDateString()}</span></div>
              <div className="flex justify-between"><span>Last Updated</span><span>{new Date(caseData.updated_date).toLocaleDateString()}</span></div>
              {caseData.closed_date && <div className="flex justify-between"><span>Closed</span><span>{caseData.closed_date}</span></div>}
            </div>
          </div>

          {caseData.notes && (
            <div className="bg-card rounded-xl border border-border p-5 space-y-2">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-accent" /> Internal Notes
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{caseData.notes}</p>
            </div>
          )}
        </div>
      </div>

      <CaseFormDialog open={showEdit} onOpenChange={setShowEdit} onSubmit={handleUpdate} initialData={caseData} />
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-0.5">{label}</p>
      <div className="text-sm font-medium text-foreground">{value}</div>
    </div>
  );
}
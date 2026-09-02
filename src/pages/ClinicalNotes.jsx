import React, { useState, useEffect } from 'react';
import { Stethoscope, Lock, Plus, FileText, ShieldAlert, Download, MessageSquarePlus } from 'lucide-react';
import { api } from '../api/client';
import { TalkToTextControl } from '../components/shared/TalkToTextControl';

export default function ClinicalNotes() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState('');
  
  // New Note Modal
  const [showModal, setShowModal] = useState(false);
  const [subject, setSubject] = useState('');
  const [narrative, setNarrative] = useState('');
  const [noteType, setNoteType] = useState('LPN_OBSERVATION');

  // Addendum Modal
  const [showAddendumModal, setShowAddendumModal] = useState(false);
  const [activeNoteId, setActiveNoteId] = useState(null);
  const [addendumNarrative, setAddendumNarrative] = useState('');

  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const clientRes = await api.get('/clients');
        const clientList = Array.isArray(clientRes) ? clientRes : (clientRes.items || []);
        setClients(clientList);
        if (clientList.length > 0) {
          setSelectedClientId(clientList[0].id);
          await loadNotes(clientList[0].id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.error("Clinical Notes load error:", err);
        setError("Clinical / LPN access restricted. Specialized capability permissions required.");
        setLoading(false);
      }
    }
    init();
  }, []);

  async function loadNotes(cId) {
    try {
      setLoading(true);
      const res = await api.get(`/clinical-notes/client/${cId}`);
      setNotes(Array.isArray(res) ? res : []);
      setError(null);
    } catch (err) {
      setNotes([]);
      setError("Permission Denied: You do not have 'clinical.note.read' authorization.");
    } finally {
      setLoading(false);
    }
  }

  const handleClientChange = (e) => {
    const val = e.target.value;
    setSelectedClientId(val);
    loadNotes(val);
  };

  const handleCreateNote = async (e) => {
    e.preventDefault();
    try {
      await api.post('/clinical-notes', {
        client_id: selectedClientId,
        note_type: noteType,
        subject,
        narrative,
        confidentiality: 'CONFIDENTIAL',
      });
      setShowModal(false);
      setSubject('');
      setNarrative('');
      await loadNotes(selectedClientId);
    } catch (err) {
      alert("Failed to create clinical note: " + (err.message || 'Permission denied'));
    }
  };

  const handleLockNote = async (noteId) => {
    if (!confirm("Are you sure you want to LOCK this clinical note? Locked notes become immutable legal health records.")) return;
    try {
      await api.post(`/clinical-notes/${noteId}/lock`);
      await loadNotes(selectedClientId);
    } catch (err) {
      alert("Failed to lock clinical note: " + (err.message || 'Permission denied'));
    }
  };

  const handleAddAddendum = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/clinical-notes/${activeNoteId}/addenda`, { narrative: addendumNarrative });
      setShowAddendumModal(false);
      setAddendumNarrative('');
      setActiveNoteId(null);
      await loadNotes(selectedClientId);
    } catch (err) {
      alert("Failed to add addendum: " + (err.message || 'Permission denied'));
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <Stethoscope className="h-6 w-6 text-indigo-600" />
            <h1 className="text-2xl font-bold text-slate-900">Clinical & LPN Health Notes</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Dedicated health records domain. Access strictly gated to authorized LPN & Medical Staff.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {clients.length > 0 && (
            <select
              value={selectedClientId}
              onChange={handleClientChange}
              className="rounded-lg border-slate-300 shadow-sm text-sm border p-2 focus:ring-indigo-500"
            >
              {clients.map(c => (
                <option key={c.id} value={c.id}>
                  Client: {c.first_name} {c.last_name} ({c.id.substring(0, 6)})
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Clinical Note
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 border border-red-200 flex items-start space-x-3">
          <ShieldAlert className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-red-800">Domain Access Restricted</h3>
            <p className="text-xs text-red-700 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-slate-500 text-sm">Loading clinical health notes...</div>
      ) : notes.length === 0 ? (
        <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
          <FileText className="h-10 w-10 text-slate-400 mx-auto mb-2" />
          <p className="text-sm font-medium text-slate-700">No Clinical Health Notes Recorded</p>
          <p className="text-xs text-slate-500 mt-1">Select a client or click 'New Clinical Note' to record LPN observations.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {notes.map(n => (
            <div key={n.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-3">
              <div className="flex items-center justify-between border-b pb-3">
                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                    {n.note_type}
                  </span>
                  <h3 className="text-base font-bold text-slate-900">{n.subject}</h3>
                </div>

                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 text-xs font-medium rounded ${n.status === 'LOCKED' ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
                    {n.status}
                  </span>

                  {n.status !== 'LOCKED' ? (
                    <button
                      onClick={() => handleLockNote(n.id)}
                      className="inline-flex items-center px-2.5 py-1 text-xs border border-amber-300 text-amber-800 bg-amber-50 rounded hover:bg-amber-100"
                    >
                      <Lock className="h-3.5 w-3.5 mr-1" />
                      Lock Record
                    </button>
                  ) : (
                    <button
                      onClick={() => { setActiveNoteId(n.id); setShowAddendumModal(true); }}
                      className="inline-flex items-center px-2.5 py-1 text-xs border border-indigo-300 text-indigo-800 bg-indigo-50 rounded hover:bg-indigo-100"
                    >
                      <MessageSquarePlus className="h-3.5 w-3.5 mr-1" />
                      Add Addendum
                    </button>
                  )}
                </div>
              </div>

              <p className="text-sm text-slate-800 whitespace-pre-wrap">{n.narrative}</p>

              {n.addenda && n.addenda.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Note Addenda</h4>
                  {n.addenda.map(a => (
                    <div key={a.id} className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs text-slate-700 space-y-1">
                      <div className="flex justify-between text-slate-500 text-[10px]">
                        <span>Addendum Author: {a.author_id.substring(0, 8)}</span>
                        <span>{new Date(a.created_at).toLocaleString()}</span>
                      </div>
                      <p>{a.narrative}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* New Note Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateNote} className="bg-white rounded-xl shadow-2xl max-w-xl w-full p-6 space-y-4">
            <h2 className="text-lg font-bold text-slate-900 border-b pb-3">New LPN Clinical Note</h2>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700">Note Category</label>
                <select
                  value={noteType}
                  onChange={(e) => setNoteType(e.target.value)}
                  className="w-full mt-1 rounded-md border-slate-300 shadow-sm text-sm border p-2"
                >
                  <option value="LPN_OBSERVATION">LPN Daily Observation</option>
                  <option value="VITAL_SIGNS">Vital Signs & Assessment</option>
                  <option value="MEDICATION_LOG">Medication Administration</option>
                  <option value="CLINICAL_ASSESSMENT">Clinical Health Summary</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700">Subject / Heading</label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Routine Wellness Check & Vitals"
                  className="w-full mt-1 rounded-md border-slate-300 shadow-sm text-sm border p-2"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-700">Clinical Narrative</label>
                  <TalkToTextControl
                    buttonText="Dictate Note"
                    onTranscriptReady={(text) => setNarrative(prev => prev ? `${prev}\n${text}` : text)}
                  />
                </div>
                <textarea
                  required
                  rows={6}
                  value={narrative}
                  onChange={(e) => setNarrative(e.target.value)}
                  placeholder="Record clinical health narrative..."
                  className="w-full rounded-md border-slate-300 shadow-sm text-sm border p-3 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-xs font-medium text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
              >
                Save Draft Note
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Addendum Modal */}
      {showAddendumModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleAddAddendum} className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 space-y-4">
            <h2 className="text-lg font-bold text-slate-900 border-b pb-3">Add Clinical Addendum</h2>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700">Addendum Narrative</label>
                <TalkToTextControl
                  buttonText="Dictate Addendum"
                  onTranscriptReady={(text) => setAddendumNarrative(prev => prev ? `${prev}\n${text}` : text)}
                />
              </div>
              <textarea
                required
                rows={4}
                value={addendumNarrative}
                onChange={(e) => setAddendumNarrative(e.target.value)}
                placeholder="Enter addendum text to attach to locked record..."
                className="w-full rounded-md border-slate-300 shadow-sm text-sm border p-3"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t">
              <button
                type="button"
                onClick={() => setShowAddendumModal(false)}
                className="px-4 py-2 text-xs font-medium text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
              >
                Submit Addendum
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

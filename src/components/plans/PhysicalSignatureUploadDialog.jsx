import React, { useState } from 'react';
import { X, UploadCloud, FileText, Check, AlertTriangle } from 'lucide-react';
import { plansApi } from '../../api/plans';

export default function PhysicalSignatureUploadDialog({ isOpen, onClose, plan, onUploaded }) {
  if (!isOpen || !plan) return null;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [signerName, setSignerName] = useState('');
  const [signerRole, setSignerRole] = useState('Primary Caregiver');
  const [signerType, setSignerType] = useState('PARENT');
  const [documentUrl, setDocumentUrl] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!signerName.trim()) {
      setError('Please provide the Signer Full Name.');
      return;
    }
    if (!documentUrl.trim()) {
      setError('Please provide a valid document storage URL or reference.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        signer_type: signerType,
        signer_name: signerName.trim(),
        signer_role: signerRole,
        document_url: documentUrl.trim(),
        notes: notes.trim() || undefined,
      };

      const result = await plansApi.addPhysicalSignature(plan.id, payload);
      onUploaded(result);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to attach physical signature document.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-border flex items-center justify-between bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">Attach Scanned Physical Signature</h2>
              <p className="text-xs text-muted-foreground">
                Upload paper document record for {plan.plan_number}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Signer Full Name *</label>
              <input
                type="text"
                value={signerName}
                onChange={(e) => setSignerName(e.target.value)}
                placeholder="e.g. Thomas Brass"
                className="w-full px-3 py-2 bg-background border rounded-lg text-xs"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Signer Role</label>
              <input
                type="text"
                value={signerRole}
                onChange={(e) => setSignerRole(e.target.value)}
                placeholder="e.g. Elder / Grandfather"
                className="w-full px-3 py-2 bg-background border rounded-lg text-xs"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Scanned Document URL / S3 Key *</label>
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
              <input
                type="url"
                value={documentUrl}
                onChange={(e) => setDocumentUrl(e.target.value)}
                placeholder="https://storage.crbcl.ca/documents/signatures/scan_001.pdf"
                className="w-full px-3 py-2 bg-background border rounded-lg text-xs font-mono"
                required
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Verification Notes / Archive Box</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Physical file located in Archive Binder A-4, signed during home visit on..."
              className="w-full px-3 py-2 bg-background border rounded-lg text-xs"
            />
          </div>

          <div className="pt-3 border-t flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-xl text-sm font-medium text-muted-foreground hover:bg-muted transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-sm shadow-md hover:bg-primary/90 transition flex items-center gap-2"
            >
              {loading ? <span>Uploading...</span> : (
                <>
                  <Check className="w-4 h-4" />
                  <span>Attach Scan Record</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

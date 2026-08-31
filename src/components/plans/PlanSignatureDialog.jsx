import React, { useState, useRef, useEffect } from 'react';
import { X, ShieldCheck, PenTool, Type, Eraser, Check, AlertTriangle, Hash } from 'lucide-react';
import { plansApi } from '../../api/plans';

export default function PlanSignatureDialog({ isOpen, onClose, plan, onSigned }) {
  if (!isOpen || !plan) return null;

  const currentVersion = plan.current_version;
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [sigMethod, setSigMethod] = useState('DRAW'); // 'DRAW' | 'TYPE'
  const [signerName, setSignerName] = useState('');
  const [signerRole, setSignerRole] = useState('Primary Caregiver');
  const [signerType, setSignerType] = useState('PARENT');
  const [typedSignature, setTypedSignature] = useState('');
  const [attestationText, setAttestationText] = useState(
    'I agree with this Family Wellness Plan and my commitments within it.'
  );
  const [hasDrawn, setHasDrawn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize canvas
  useEffect(() => {
    if (sigMethod === 'DRAW' && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 2.5;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    }
  }, [sigMethod, isOpen]);

  // Drawing event handlers
  const startDrawing = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    ctx.beginPath();
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
    setIsDrawing(true);
    setHasDrawn(true);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawn(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!signerName.trim()) {
      setError('Please provide the Signer Full Name.');
      return;
    }

    let sigData = null;
    let sigImg = null;

    if (sigMethod === 'DRAW') {
      if (!hasDrawn) {
        setError('Please draw your signature on the pad.');
        return;
      }
      const canvas = canvasRef.current;
      sigImg = canvas.toDataURL('image/png');
    } else {
      if (!typedSignature.trim()) {
        setError('Please type your legal signature.');
        return;
      }
      sigData = typedSignature.trim();
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        signer_type: signerType,
        signer_name: signerName.trim(),
        signer_role: signerRole,
        signature_data: sigData,
        signature_image_url: sigImg,
        method: sigMethod === 'DRAW' ? 'CANVAS_DRAW' : 'TYPED_ATTESTATION',
        attestation_text: attestationText.trim(),
      };

      const result = await plansApi.addSignature(plan.id, payload);
      onSigned(result);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to record signature.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-6 border-b border-border flex items-center justify-between bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">Electronic Signature & Attestation</h2>
              <p className="text-xs text-muted-foreground">
                Cryptographically bound to Version {currentVersion?.version_number || 1}
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

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Document Verification Box */}
          <div className="p-3.5 bg-muted/30 border border-border rounded-xl space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-foreground">{plan.title}</span>
              <span className="font-mono text-muted-foreground">{plan.plan_number}</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground font-mono truncate">
              <Hash className="w-3.5 h-3.5 text-primary shrink-0" />
              <span className="truncate">Document SHA-256: {currentVersion?.document_hash || 'PENDING'}</span>
            </div>
          </div>

          {/* Signer Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Signer Full Name *</label>
              <input
                type="text"
                value={signerName}
                onChange={(e) => setSignerName(e.target.value)}
                placeholder="e.g. Eleanor Brass"
                className="w-full px-3 py-2 bg-background border rounded-lg text-xs focus:ring-2 focus:ring-primary"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Signer Role</label>
              <select
                value={signerRole}
                onChange={(e) => setSignerRole(e.target.value)}
                className="w-full px-3 py-2 bg-background border rounded-lg text-xs"
              >
                <option value="Primary Caregiver">Primary Caregiver</option>
                <option value="Co-Parent / Guardian">Co-Parent / Guardian</option>
                <option value="Youth / Child">Youth / Child</option>
                <option value="Elder / Knowledge Keeper">Elder / Knowledge Keeper</option>
                <option value="Extended Kin">Extended Kin</option>
                <option value="Caseworker">Caseworker</option>
                <option value="Supervisor">Supervisor</option>
                <option value="Service Provider">Service Provider</option>
              </select>
            </div>
          </div>

          {/* Signer Classification */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Signer Classification</label>
            <div className="grid grid-cols-4 gap-2">
              {[
                { id: 'PARENT', label: 'Parent' },
                { id: 'YOUTH', label: 'Youth' },
                { id: 'WORKER', label: 'Worker' },
                { id: 'COLLATERAL', label: 'Collateral' },
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setSignerType(t.id)}
                  className={`py-1.5 px-2 rounded-lg border text-xs font-medium transition ${
                    signerType === t.id
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border bg-card text-muted-foreground hover:bg-muted'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Method Selector: Draw vs Type */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-foreground">Signature Capture Method</label>
              <div className="flex rounded-lg border border-border overflow-hidden">
                <button
                  type="button"
                  onClick={() => setSigMethod('DRAW')}
                  className={`px-3 py-1 text-xs font-medium flex items-center gap-1.5 transition ${
                    sigMethod === 'DRAW' ? 'bg-primary text-primary-foreground' : 'bg-card text-muted-foreground'
                  }`}
                >
                  <PenTool className="w-3 h-3" /> Draw
                </button>
                <button
                  type="button"
                  onClick={() => setSigMethod('TYPE')}
                  className={`px-3 py-1 text-xs font-medium flex items-center gap-1.5 transition ${
                    sigMethod === 'TYPE' ? 'bg-primary text-primary-foreground' : 'bg-card text-muted-foreground'
                  }`}
                >
                  <Type className="w-3 h-3" /> Type
                </button>
              </div>
            </div>

            {sigMethod === 'DRAW' ? (
              <div className="space-y-2">
                <div className="relative border-2 border-dashed border-border rounded-xl bg-white overflow-hidden">
                  <canvas
                    ref={canvasRef}
                    width={480}
                    height={160}
                    onMouseDown={startDrawing}
                    onMouseMove={draw}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                    className="w-full h-40 cursor-crosshair touch-none"
                  />
                  <button
                    type="button"
                    onClick={clearCanvas}
                    className="absolute top-2 right-2 p-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs flex items-center gap-1 shadow-sm transition"
                  >
                    <Eraser className="w-3.5 h-3.5" /> Clear
                  </button>
                </div>
                <p className="text-[11px] text-muted-foreground text-center">
                  Use your mouse, trackpad, or finger/stylus to sign above
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <input
                  type="text"
                  value={typedSignature}
                  onChange={(e) => setTypedSignature(e.target.value)}
                  placeholder="Type your full legal name as signature..."
                  className="w-full px-4 py-3 bg-background border rounded-xl text-lg font-serif italic text-foreground focus:ring-2 focus:ring-primary"
                />
                <p className="text-[11px] text-muted-foreground">
                  Typing your name constitutes a legally binding electronic signature under applicable legislation.
                </p>
              </div>
            )}
          </div>

          {/* Attestation Text */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Attestation Statement</label>
            <textarea
              value={attestationText}
              onChange={(e) => setAttestationText(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 bg-background border rounded-lg text-xs text-muted-foreground focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Submit Controls */}
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
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-sm shadow-md transition flex items-center gap-2"
            >
              {loading ? <span>Recording...</span> : (
                <>
                  <Check className="w-4 h-4" />
                  <span>Seal Signature</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

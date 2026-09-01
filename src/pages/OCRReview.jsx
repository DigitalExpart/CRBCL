import React, { useState } from 'react';
import { 
  FileCheck, 
  FileText, 
  Check, 
  X, 
  Edit3, 
  AlertCircle, 
  ShieldCheck,
  Sparkles,
  ArrowRight
} from 'lucide-react';

export default function OCRReview() {
  const [documentName] = useState('Intake_Referral_Form_Scan_2026.pdf');
  const [jobStatus, setJobStatus] = useState('REVIEW_REQUIRED');
  const [extractedText] = useState(
    "CHIEF RED BEAR CHILDREN'S LODGE INTAKE REFERRAL FORM\n" +
    "Client Name: Jordan Bear\n" +
    "Date of Birth: 2014-05-12\n" +
    "Healthcare Number: 9948201948\n" +
    "Allegation: Educational neglect noted by school counselor."
  );

  const [candidates, setCandidates] = useState([
    { field_name: 'first_name', value: 'Jordan', confidence: 0.95, target_domain: 'client.identifiers', status: 'PENDING' },
    { field_name: 'last_name', value: 'Bear', confidence: 0.94, target_domain: 'client.identifiers', status: 'PENDING' },
    { field_name: 'date_of_birth', value: '2014-05-12', confidence: 0.89, target_domain: 'client.identifiers', status: 'PENDING' },
    { field_name: 'health_card_number', value: '9948201948', confidence: 0.92, target_domain: 'client.identifiers', status: 'PENDING' },
  ]);

  const [confirmedSuccess, setConfirmedSuccess] = useState(false);

  const handleFieldAction = (index, action) => {
    setCandidates(prev => prev.map((item, idx) => {
      if (idx === index) {
        return { ...item, status: action };
      }
      return item;
    }));
  };

  const handleFieldValueChange = (index, val) => {
    setCandidates(prev => prev.map((item, idx) => {
      if (idx === index) {
        return { ...item, value: val };
      }
      return item;
    }));
  };

  const handleConfirmAll = () => {
    setJobStatus('CONFIRMED');
    setConfirmedSuccess(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8">
      <div className="max-w-6xl mx-auto mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-600 shadow-lg shadow-emerald-900/30">
            <FileCheck className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              OCR Document Review & Verification
            </h1>
            <p className="text-sm text-slate-400">
              Human-in-the-Loop review of extracted document draft fields.
            </p>
          </div>
        </div>
      </div>

      {confirmedSuccess ? (
        <div className="max-w-6xl mx-auto p-8 rounded-2xl bg-emerald-950/60 border border-emerald-700 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-emerald-900/80 border border-emerald-500 text-emerald-300 flex items-center justify-center mx-auto">
            <ShieldCheck className="w-10 h-10" />
          </div>
          <h2 className="text-2xl font-bold text-emerald-200">OCR Fields Verified & Committed</h2>
          <p className="text-sm text-emerald-300 max-w-md mx-auto">
            The human-confirmed fields have been securely committed to the authoritative Client Record.
          </p>
          <button 
            onClick={() => setConfirmedSuccess(false) || setJobStatus('REVIEW_REQUIRED')}
            className="px-5 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-600 text-white font-semibold text-sm transition"
          >
            Review Another Document
          </button>
        </div>
      ) : (
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Document Preview */}
          <div className="lg:col-span-5 rounded-2xl bg-slate-900/90 border border-slate-800 p-6 flex flex-col justify-between shadow-xl">
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 mb-3 uppercase tracking-wider">
                <FileText className="w-4 h-4" /> Original Document Source
              </div>
              <h3 className="font-semibold text-slate-200 mb-4 text-base">{documentName}</h3>
              
              <div className="rounded-xl bg-slate-950 p-4 border border-slate-850 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto">
                {extractedText}
              </div>
            </div>

            <div className="mt-6 p-3 rounded-xl bg-amber-950/40 border border-amber-900/50 text-amber-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong>ADR-035 Compliance:</strong> OCR output is purely assistive. Confirmation requires target field write authorization (<code className="font-mono">client.identifiers.write</code>).
              </div>
            </div>
          </div>

          {/* Extracted Candidates & Review Controls */}
          <div className="lg:col-span-7 rounded-2xl bg-slate-900/90 border border-slate-800 p-6 flex flex-col justify-between shadow-xl">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                  <Sparkles className="w-4 h-4" /> Extracted Field Candidates
                </div>
                <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-950 text-amber-300 border border-amber-800">
                  {jobStatus}
                </span>
              </div>

              <div className="space-y-4">
                {candidates.map((item, idx) => (
                  <div key={idx} className="rounded-xl bg-slate-950 p-4 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
                        {item.field_name}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                        item.confidence >= 0.9 ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-amber-950 text-amber-300 border border-amber-800'
                      }`}>
                        {(item.confidence * 100).toFixed(0)}% Confidence
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <input 
                        type="text"
                        value={item.value}
                        onChange={(e) => handleFieldValueChange(idx, e.target.value)}
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-100 font-medium focus:outline-none focus:border-indigo-500"
                      />

                      <div className="flex items-center gap-1">
                        <button 
                          onClick={() => handleFieldAction(idx, 'ACCEPTED')}
                          className={`p-1.5 rounded-lg border transition ${
                            item.status === 'ACCEPTED' ? 'bg-emerald-600 border-emerald-500 text-white' : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                          }`}
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleFieldAction(idx, 'REJECTED')}
                          className={`p-1.5 rounded-lg border transition ${
                            item.status === 'REJECTED' ? 'bg-red-600 border-red-500 text-white' : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                          }`}
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-6 border-t border-slate-800 flex items-center justify-end gap-3 mt-6">
              <button 
                onClick={handleConfirmAll}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm transition shadow-lg shadow-emerald-900/30 flex items-center gap-2"
              >
                <ShieldCheck className="w-4 h-4" /> Confirm & Commit Fields <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

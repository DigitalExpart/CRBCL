import React from 'react';
import { format } from 'date-fns';
import { Shield, FileText, CheckCircle, Hash } from 'lucide-react';

export default function PlanPrintView({ printData }) {
  if (!printData) return null;

  return (
    <div className="hidden print:block print:w-full print:p-8 bg-white text-black font-sans leading-relaxed">
      {/* Official Header */}
      <div className="border-b-2 border-black pb-4 mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold uppercase tracking-wide">
            Cote First Nation • CRBCL Child & Family Wellness Services
          </h1>
          <p className="text-sm font-medium text-gray-700">
            Family Wellness & Safety Planning Engine • Treaty 4 Territory
          </p>
        </div>
        <div className="text-right">
          <div className="text-lg font-mono font-bold">{printData.plan_number}</div>
          <div className="text-xs text-gray-600">Version {printData.version_number} • {printData.status}</div>
        </div>
      </div>

      {/* Document Title & Metadata Box */}
      <div className="bg-gray-50 border border-gray-300 rounded p-4 mb-6">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-xl font-bold text-gray-900">{printData.title}</h2>
          <span className="px-2.5 py-1 text-xs font-bold uppercase border border-black rounded">
            {printData.plan_type === 'SAFETY_PLAN' ? 'Immediate Safety Plan' : 'Family Wellness Case Plan'}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs mt-3 pt-3 border-t border-gray-200">
          <div>
            <span className="font-semibold text-gray-600">Case Number:</span>
            <div className="font-mono font-bold text-gray-900">{printData.case_number}</div>
          </div>
          <div>
            <span className="font-semibold text-gray-600">Primary Client:</span>
            <div className="font-bold text-gray-900">{printData.client_name || 'N/A'}</div>
          </div>
          <div>
            <span className="font-semibold text-gray-600">Family File:</span>
            <div className="font-bold text-gray-900">{printData.family_name || 'N/A'}</div>
          </div>
          <div>
            <span className="font-semibold text-gray-600">Formulation Date:</span>
            <div className="font-bold text-gray-900">{printData.meeting_date || 'N/A'}</div>
          </div>
        </div>
      </div>

      {/* Narrative Context */}
      {printData.narrative && (
        <div className="mb-6">
          <h3 className="text-sm font-bold uppercase border-b border-gray-300 pb-1 mb-2 text-gray-900">
            1. Clinical Context & Family Narrative
          </h3>
          <p className="text-xs text-gray-800 whitespace-pre-wrap">{printData.narrative}</p>
        </div>
      )}

      {/* Participants */}
      <div className="mb-6">
        <h3 className="text-sm font-bold uppercase border-b border-gray-300 pb-1 mb-2 text-gray-900">
          2. Plan Participants & Circle Members
        </h3>
        <table className="w-full text-xs text-left border border-gray-300 mb-2">
          <thead className="bg-gray-100 border-b border-gray-300">
            <tr>
              <th className="p-2">Name</th>
              <th className="p-2">Role</th>
              <th className="p-2">Relationship</th>
              <th className="p-2">Type</th>
              <th className="p-2 text-center">Signer?</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {(printData.participants || []).map((p, idx) => (
              <tr key={idx}>
                <td className="p-2 font-medium">{p.name}</td>
                <td className="p-2">{p.role || '—'}</td>
                <td className="p-2">{p.relationship || '—'}</td>
                <td className="p-2">{p.participant_type?.replace(/_/g, ' ')}</td>
                <td className="p-2 text-center">{p.signature_required ? '[X]' : '[ ]'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Harm Statements & Danger Concerns */}
      {(printData.concerns || []).length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-bold uppercase border-b border-gray-300 pb-1 mb-2 text-gray-900">
            3. Concerns, Harm Statements & Safety Threats
          </h3>
          <div className="space-y-2">
            {printData.concerns.map((c, idx) => (
              <div key={idx} className="p-2 border border-gray-300 rounded bg-gray-50 text-xs">
                <div className="flex justify-between font-semibold mb-1">
                  <span>Concern #{idx + 1}: {c.concern_type?.replace(/_/g, ' ')}</span>
                  <span className="text-red-700 uppercase font-bold">Severity: {c.severity}</span>
                </div>
                <p className="text-gray-800">{c.statement}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strengths & Protective Capacities */}
      {(printData.strengths || []).length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-bold uppercase border-b border-gray-300 pb-1 mb-2 text-gray-900">
            4. Strengths & Protective Capacities
          </h3>
          <div className="space-y-2">
            {printData.strengths.map((s, idx) => (
              <div key={idx} className="p-2 border border-gray-300 rounded bg-gray-50 text-xs">
                <div className="font-semibold mb-1 text-emerald-800">
                  Strength #{idx + 1} • {s.category?.replace(/_/g, ' ')}
                </div>
                <p className="text-gray-800">{s.statement}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Goals & Activities Matrix */}
      <div className="mb-6">
        <h3 className="text-sm font-bold uppercase border-b border-gray-300 pb-1 mb-2 text-gray-900">
          5. Goals, Activities & Action Commitments
        </h3>
        <div className="space-y-4">
          {(printData.goals || []).map((g, idx) => (
            <div key={idx} className="border border-gray-300 rounded p-3 bg-white">
              <div className="flex justify-between items-center text-xs font-bold mb-2 pb-1 border-b border-gray-200">
                <span>Goal #{idx + 1}: {g.goal_text}</span>
                <span className="text-gray-600">Target Date: {g.target_date || 'Ongoing'} • Status: {g.status}</span>
              </div>

              {g.activities && g.activities.length > 0 && (
                <table className="w-full text-xs text-left mt-2">
                  <thead>
                    <tr className="border-b text-gray-600">
                      <th className="py-1">Action Step / Activity</th>
                      <th className="py-1">Responsible Person</th>
                      <th className="py-1">Due Date</th>
                      <th className="py-1 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {g.activities.map((a, aIdx) => (
                      <tr key={aIdx}>
                        <td className="py-1 font-medium">{a.activity_text}</td>
                        <td className="py-1">{a.responsible_name}</td>
                        <td className="py-1">{a.due_date || '—'}</td>
                        <td className="py-1 text-right font-semibold">{a.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Signatures & Attestations */}
      <div className="mb-6 page-break-inside-avoid">
        <h3 className="text-sm font-bold uppercase border-b border-gray-300 pb-1 mb-3 text-gray-900">
          6. Legal Signatures & Attestation Seals
        </h3>

        <div className="grid grid-cols-2 gap-4">
          {(printData.signatures || []).map((sig, idx) => (
            <div key={idx} className="border border-gray-300 rounded p-3 bg-gray-50 text-xs">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="font-bold text-gray-900">{sig.signer_name}</div>
                  <div className="text-gray-600">{sig.signer_role} ({sig.signer_type})</div>
                </div>
                <div className="text-right text-[10px] text-gray-500 font-mono">
                  {sig.signed_at ? format(new Date(sig.signed_at), 'yyyy-MM-dd HH:mm') : '—'}
                </div>
              </div>

              {sig.signature_image_url ? (
                <div className="my-2 p-1 bg-white border border-gray-200 rounded flex justify-center">
                  <img src={sig.signature_image_url} alt="Signature" className="h-12 object-contain" />
                </div>
              ) : (
                <div className="my-2 p-2 bg-white border border-gray-200 rounded italic font-serif text-sm">
                  {sig.signature_data || sig.signer_name}
                </div>
              )}

              <p className="text-[10px] text-gray-600 italic mt-1">{sig.attestation_text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Cryptographic Verification Box */}
      <div className="mt-8 pt-4 border-t-2 border-black text-[10px] text-gray-600 flex justify-between items-end">
        <div>
          <div className="font-bold uppercase tracking-wider text-gray-800">
            Document Security & Integrity Seal
          </div>
          <div className="font-mono text-gray-700 mt-0.5">
            SHA-256: {printData.document_hash || 'UNSEALED_DRAFT'}
          </div>
          <div className="mt-0.5">
            Printed by {printData.printed_by_name} on {format(new Date(printData.printed_at), 'yyyy-MM-dd HH:mm:ss')} UTC
          </div>
        </div>
        <div className="text-right font-bold text-gray-800">
          CRBCL Case Management Engine • Page 1
        </div>
      </div>
    </div>
  );
}

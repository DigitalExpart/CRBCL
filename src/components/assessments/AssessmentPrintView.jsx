import React from 'react';
import { format } from 'date-fns';
import { CheckCircle, XCircle } from 'lucide-react';

export default function AssessmentPrintView({ assessment }) {
  if (!assessment) return null;

  const version = assessment.template_version;
  const sections = version?.sections || [];

  // Group answers by question_id
  const answerMap = new Map();
  (assessment.answers || []).forEach((a) => {
    answerMap.set(a.question_id, a);
  });

  const renderPrintAnswer = (q) => {
    const ans = answerMap.get(q.id);
    if (!ans) return <span className="text-gray-400 italic">Not recorded</span>;

    if (q.question_type === 'BOOLEAN') {
      return ans.boolean_value ? (
        <span className="font-semibold text-black flex items-center gap-1">
          [X] YES &nbsp; [ ] NO
        </span>
      ) : (
        <span className="font-semibold text-black flex items-center gap-1">
          [ ] YES &nbsp; [X] NO
        </span>
      );
    }

    if (q.question_type === 'SINGLE_SELECT') {
      const selected = ans.selected_options?.[0]?.option;
      return <span className="font-medium text-black">{selected?.label || ans.text_value || 'None'}</span>;
    }

    if (q.question_type === 'MULTI_SELECT') {
      const opts = (ans.selected_options || []).map((o) => o.option?.label).filter(Boolean);
      return <span className="font-medium text-black">{opts.length ? opts.join(', ') : 'None'}</span>;
    }

    if (q.question_type === 'NUMBER') {
      return <span className="font-medium text-black">{ans.number_value !== null ? ans.number_value : 'N/A'}</span>;
    }

    if (q.question_type === 'DATE') {
      return <span className="font-medium text-black">{ans.date_value || 'N/A'}</span>;
    }

    return <span className="font-medium text-black whitespace-pre-wrap">{ans.text_value || 'N/A'}</span>;
  };

  return (
    <div className="hidden print:block print:w-full print:p-8 bg-white text-black font-sans leading-relaxed">
      {/* Header */}
      <div className="border-b-2 border-black pb-4 mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold uppercase tracking-wide">
            CRBCL Child & Family Wellness Platform
          </h1>
          <h2 className="text-lg font-semibold text-gray-800 mt-1">
            {assessment.template?.name || 'Assessment Report'}
          </h2>
          <p className="text-xs text-gray-600">
            Form Version: {version?.version_number} &bull; Template Key: {assessment.template?.key}
          </p>
        </div>
        <div className="text-right text-xs space-y-1">
          <div className="font-mono font-bold text-sm">{assessment.assessment_number}</div>
          <div>Status: <span className="font-semibold uppercase">{assessment.status}</span></div>
          <div>Date: {assessment.conducted_at ? format(new Date(assessment.conducted_at), 'PPP') : 'N/A'}</div>
        </div>
      </div>

      {/* Case and Person Metadata Box */}
      <div className="border border-gray-400 p-4 rounded mb-6 text-xs grid grid-cols-2 gap-4 bg-gray-50">
        <div>
          <p><span className="font-semibold text-gray-700">Case Number:</span> {assessment.case?.case_number || 'N/A'}</p>
          <p><span className="font-semibold text-gray-700">Case Title:</span> {assessment.case?.title || 'N/A'}</p>
          <p><span className="font-semibold text-gray-700">Subject Individual:</span> {assessment.person ? `${assessment.person.first_name} ${assessment.person.last_name}` : 'N/A'}</p>
        </div>
        <div>
          <p><span className="font-semibold text-gray-700">Assessor / Conductor:</span> {assessment.conductor?.full_name || assessment.conductor?.email || 'N/A'}</p>
          <p><span className="font-semibold text-gray-700">Completed By:</span> {assessment.completer?.full_name || 'N/A'}</p>
          <p><span className="font-semibold text-gray-700">Lock Finalized:</span> {assessment.locked_at ? format(new Date(assessment.locked_at), 'PPP p') : 'No'}</p>
        </div>
      </div>

      {/* Structured Sections */}
      <div className="space-y-6">
        {sections.map((sec, secIdx) => (
          <div key={sec.id} className="border-b border-gray-300 pb-4">
            <h3 className="text-sm font-bold uppercase tracking-wider bg-gray-200 px-3 py-1.5 rounded-sm mb-3">
              Section {secIdx + 1}: {sec.title}
            </h3>
            {sec.description && (
              <p className="text-xs text-gray-600 italic px-2 mb-2">{sec.description}</p>
            )}

            <div className="space-y-3 px-2">
              {(sec.questions || []).map((q, qIdx) => (
                <div key={q.id} className="text-xs">
                  <div className="font-medium text-gray-900 mb-1">
                    {qIdx + 1}. {q.label}
                  </div>
                  <div className="pl-4 py-1 bg-gray-50 border-l-2 border-gray-300">
                    {renderPrintAnswer(q)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Official Determination Block */}
      <div className="mt-8 border-2 border-black p-4 rounded bg-gray-50 text-xs">
        <h3 className="text-sm font-bold uppercase tracking-wider mb-2 border-b border-gray-300 pb-1">
          Clinical Determination & Legal Findings
        </h3>
        <p className="mb-2">
          <span className="font-bold">Official Determination Outcome:</span>{' '}
          <span className="font-semibold text-black uppercase">{assessment.determination || 'Pending Determination'}</span>
        </p>
        {assessment.determination_notes && (
          <p className="mb-3">
            <span className="font-bold">Determination Rationale / Safety Findings:</span>
            <br />
            <span className="text-gray-800 whitespace-pre-wrap">{assessment.determination_notes}</span>
          </p>
        )}
        {assessment.summary && (
          <p className="mb-4">
            <span className="font-bold">Assessment Summary:</span>
            <br />
            <span className="text-gray-800 whitespace-pre-wrap">{assessment.summary}</span>
          </p>
        )}

        {/* Signatures */}
        <div className="grid grid-cols-2 gap-8 pt-8 border-t border-gray-300 mt-6">
          <div>
            <div className="border-b border-black mb-1 h-8"></div>
            <p className="font-semibold text-gray-800">Caseworker / Assessor Signature & Date</p>
          </div>
          <div>
            <div className="border-b border-black mb-1 h-8"></div>
            <p className="font-semibold text-gray-800">Supervisor / Director Review Signature & Date</p>
          </div>
        </div>
      </div>
    </div>
  );
}

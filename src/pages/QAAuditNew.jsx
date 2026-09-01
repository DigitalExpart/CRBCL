import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { reportingApi } from '../api/reporting';
import api from '../api/client';
import {
  ClipboardCheck,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  MinusCircle,
  Save,
  AlertCircle,
} from 'lucide-react';

export default function QAAuditNew() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [cases, setCases] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [reviewNotes, setReviewNotes] = useState('');
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tRes, cRes] = await Promise.all([
        reportingApi.getQATemplates(),
        api.get('/cases?limit=100'),
      ]);
      setTemplates(tRes.data || []);
      const cList = cRes.data.items || cRes.data || [];
      setCases(cList);

      if (tRes.data && tRes.data.length > 0) {
        selectTemplate(tRes.data[0]);
      }
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  const selectTemplate = (tpl) => {
    setSelectedTemplate(tpl);
    const initialAns = {};
    const currentVersion = tpl.versions?.[0] || tpl;
    if (currentVersion.items) {
      currentVersion.items.forEach((item) => {
        initialAns[item.id] = {
          item_id: item.id,
          compliance: 'YES',
          notes: '',
          finding_severity: 'MEDIUM',
        };
      });
    }
    setAnswers(initialAns);
  };

  const setAnswerCompliance = (itemId, val) => {
    setAnswers({
      ...answers,
      [itemId]: { ...answers[itemId], compliance: val },
    });
  };

  const setAnswerNotes = (itemId, notes) => {
    setAnswers({
      ...answers,
      [itemId]: { ...answers[itemId], notes },
    });
  };

  const handleSubmit = async (statusVal) => {
    if (!selectedCaseId) {
      alert('Please select a Case to audit.');
      return;
    }

    setSubmitting(true);
    try {
      const currentVer = selectedTemplate.versions?.[0] || selectedTemplate;
      const payload = {
        case_id: selectedCaseId,
        template_version_id: currentVer.id,
        review_date: new Date().toISOString().slice(0, 10),
        status: statusVal,
        notes: reviewNotes,
        results: Object.values(answers),
      };
      await reportingApi.createQAAudit(payload);
      navigate('/qa');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit QA audit.');
    } finally {
      setSubmitting(false);
    }
  };

  // Calculate overall score preview
  const applicableAns = Object.values(answers).filter((a) => a.compliance !== 'NA');
  const yesCount = applicableAns.filter((a) => a.compliance === 'YES').length;
  const scorePreview = applicableAns.length > 0 ? ((yesCount / applicableAns.length) * 100).toFixed(1) : '100.0';

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading QA checklist wizard...</div>;
  }

  const currentVer = selectedTemplate?.versions?.[0] || selectedTemplate;
  const itemsList = currentVer?.items || [];

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/qa')}
            className="p-2 border border-border rounded-lg text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Conduct Case QA Audit</h1>
            <p className="text-sm text-muted-foreground">
              Review case compliance against standardized quality assurance checklist.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Score Preview</div>
            <div className="text-lg font-extrabold text-primary">{scorePreview}%</div>
          </div>
          <button
            onClick={() => handleSubmit('DRAFT')}
            disabled={submitting}
            className="px-4 py-2 border border-border text-foreground rounded-lg text-sm font-medium hover:bg-muted"
          >
            Save Draft
          </button>
          <button
            onClick={() => handleSubmit('COMPLETED')}
            disabled={submitting}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
          >
            Complete Audit
          </button>
        </div>
      </div>

      {/* Target Case & Template Selection */}
      <div className="p-5 bg-card border border-border rounded-xl grid grid-cols-1 md:grid-cols-2 gap-4 shadow-sm">
        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1">
            Target Case *
          </label>
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
          >
            <option value="">-- Select Case to Audit --</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.case_number} — {c.title} ({c.case_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1">
            Audit Checklist Template
          </label>
          <select
            value={selectedTemplate?.id || ''}
            onChange={(e) => {
              const t = templates.find((tpl) => tpl.id === e.target.value);
              if (t) selectTemplate(t);
            }}
            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
          >
            {templates.map((tpl) => (
              <option key={tpl.id} value={tpl.id}>
                {tpl.title} ({tpl.cadence})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Checklist Items */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-foreground">Compliance Checklist Items</h2>

        {itemsList.map((item, idx) => {
          const currentAns = answers[item.id] || { compliance: 'YES', notes: '' };
          return (
            <div key={item.id} className="p-5 bg-card border border-border rounded-xl space-y-3 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-primary">
                    Section: {item.section}
                  </div>
                  <h3 className="font-semibold text-foreground text-sm mt-0.5">{item.item_text}</h3>
                </div>

                {/* YES / NO / NA Compliance Buttons */}
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setAnswerCompliance(item.id, 'YES')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors ${
                      currentAns.compliance === 'YES'
                        ? 'bg-emerald-500 text-white'
                        : 'bg-muted text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> YES
                  </button>
                  <button
                    type="button"
                    onClick={() => setAnswerCompliance(item.id, 'NO')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors ${
                      currentAns.compliance === 'NO'
                        ? 'bg-rose-500 text-white'
                        : 'bg-muted text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <XCircle className="w-3.5 h-3.5" /> NO
                  </button>
                  <button
                    type="button"
                    onClick={() => setAnswerCompliance(item.id, 'NA')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors ${
                      currentAns.compliance === 'NA'
                        ? 'bg-zinc-600 text-white'
                        : 'bg-muted text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <MinusCircle className="w-3.5 h-3.5" /> N/A
                  </button>
                </div>
              </div>

              {/* Item Notes */}
              <input
                type="text"
                placeholder="Checklist finding notes or corrective actions..."
                value={currentAns.notes || ''}
                onChange={(e) => setAnswerNotes(item.id, e.target.value)}
                className="w-full px-3 py-1.5 bg-background border border-border rounded-lg text-xs text-foreground focus:outline-none focus:border-primary"
              />
            </div>
          );
        })}
      </div>

      {/* Overall Review Notes */}
      <div className="p-5 bg-card border border-border rounded-xl space-y-2 shadow-sm">
        <label className="text-xs font-semibold text-muted-foreground block">
          Overall Supervisor Audit Summary & Findings
        </label>
        <textarea
          rows={3}
          value={reviewNotes}
          onChange={(e) => setReviewNotes(e.target.value)}
          placeholder="Enter overall case review observations, supervisor recommendations, or required follow-up dates..."
          className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary"
        />
      </div>
    </div>
  );
}

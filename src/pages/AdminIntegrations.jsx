import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  RefreshCw, 
  Server, 
  Cpu, 
  FileText, 
  Navigation, 
  Share2, 
  CheckCircle2, 
  XCircle,
  AlertTriangle,
  Lock
} from 'lucide-react';

export default function AdminIntegrations() {
  const [integrations, setIntegrations] = useState([
    {
      provider_key: 'M365',
      display_name: 'Microsoft 365 / Graph (Outlook & Teams)',
      category: 'M365',
      status: 'DISABLED',
      is_enabled: false,
      is_approved: false,
      last_health_check_at: '2026-09-01T20:00:00Z',
      last_sync_at: '2026-09-01T22:15:00Z',
      last_error: null,
      config_summary: { tenant_type: 'SINGLE_TENANT', scopes: ['Calendars.ReadWrite'] }
    },
    {
      provider_key: 'AI_RED_BEAR',
      display_name: 'Ask Red Bear Assistive AI (Anthropic)',
      category: 'AI',
      status: 'PILOT',
      is_enabled: true,
      is_approved: true,
      last_health_check_at: '2026-09-01T23:10:00Z',
      last_sync_at: null,
      last_error: null,
      config_summary: { model: 'claude-3-5-sonnet', max_tokens: 1024, zero_retention: true }
    },
    {
      provider_key: 'OCR_TESSERACT',
      display_name: 'Document OCR Engine',
      category: 'OCR',
      status: 'CONFIGURED',
      is_enabled: true,
      is_approved: true,
      last_health_check_at: '2026-09-01T22:00:00Z',
      last_sync_at: null,
      last_error: null,
      config_summary: { engine: 'Tesseract OCR', human_review_required: true }
    },
    {
      provider_key: 'TELEMATICS_SAMSARA',
      display_name: 'Fleet GPS & Telematics Provider',
      category: 'TELEMATICS',
      status: 'PILOT',
      is_enabled: true,
      is_approved: true,
      last_health_check_at: '2026-09-01T23:20:00Z',
      last_sync_at: '2026-09-01T23:25:00Z',
      last_error: null,
      config_summary: { update_frequency_seconds: 60 }
    },
    {
      provider_key: 'SOCIAL_META',
      display_name: 'Public Communications (Meta / X)',
      category: 'SOCIAL',
      status: 'DISABLED',
      is_enabled: false,
      is_approved: false,
      last_health_check_at: null,
      last_sync_at: null,
      last_error: null,
      config_summary: { approval_required: true }
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const categoryIcons = {
    M365: <Server className="w-5 h-5 text-blue-400" />,
    AI: <Cpu className="w-5 h-5 text-purple-400" />,
    OCR: <FileText className="w-5 h-5 text-emerald-400" />,
    TELEMATICS: <Navigation className="w-5 h-5 text-amber-400" />,
    SOCIAL: <Share2 className="w-5 h-5 text-pink-400" />
  };

  const statusBadge = (status, is_enabled) => {
    if (!is_enabled || status === 'DISABLED') {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5"><XCircle className="w-3.5 h-3.5" /> Disabled</span>;
    }
    if (status === 'APPROVED') {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5" /> Approved</span>;
    }
    if (status === 'PILOT') {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> Pilot Mode</span>;
    }
    if (status === 'CONFIGURED') {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-950 text-blue-300 border border-blue-800 flex items-center gap-1.5"><Server className="w-3.5 h-3.5" /> Configured</span>;
    }
    return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-red-950 text-red-300 border border-red-800 flex items-center gap-1.5"><ShieldAlert className="w-3.5 h-3.5" /> Error</span>;
  };

  const handleToggle = (provider_key) => {
    setIntegrations(prev => prev.map(item => {
      if (item.provider_key === provider_key) {
        const nextEnabled = !item.is_enabled;
        const nextStatus = nextEnabled ? (item.is_approved ? 'APPROVED' : 'PILOT') : 'DISABLED';
        return { ...item, is_enabled: nextEnabled, status: nextStatus };
      }
      return item;
    }));
    setToastMessage(`Integration state updated for ${provider_key}`);
    setTimeout(() => setToastMessage(''), 3000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 shadow-lg shadow-indigo-900/30">
                <ShieldCheck className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  Enterprise Integration Governance
                </h1>
                <p className="text-sm text-slate-400 mt-1">
                  Controlled external processor gateway, feature flags, health metrics & security status.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => setLoading(true) || setTimeout(() => setLoading(false), 800)}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 transition flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh Status
            </button>
          </div>
        </div>

        {toastMessage && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-950/80 border border-emerald-700 text-emerald-200 text-sm flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            {toastMessage}
          </div>
        )}
      </div>

      {/* Security Banner */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="p-4 rounded-xl bg-slate-900/70 border border-indigo-900/50 backdrop-blur-md flex items-start gap-3">
          <Lock className="w-5 h-5 text-indigo-400 mt-0.5 shrink-0" />
          <div className="text-xs md:text-sm text-slate-300">
            <strong className="text-indigo-300">Zero Secret Leakage Guarantee:</strong> All provider credentials, OAuth client secrets, and API keys are strictly stored in server-side environment vaults. Sensitive CRBCL child welfare records pass through FastAPI data-minimization filters prior to external dispatch.
          </div>
        </div>
      </div>

      {/* Integrations Grid */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.map((item) => (
          <div 
            key={item.provider_key}
            className="rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition duration-200 p-6 flex flex-col justify-between shadow-xl shadow-black/20"
          >
            <div>
              <div className="flex items-start justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-slate-800 border border-slate-700">
                    {categoryIcons[item.category] || <Server className="w-5 h-5 text-slate-400" />}
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-100 text-sm leading-tight">{item.display_name}</h3>
                    <span className="text-xs text-slate-400 font-mono mt-0.5 block">{item.provider_key}</span>
                  </div>
                </div>
                {statusBadge(item.status, item.is_enabled)}
              </div>

              {/* Config Metadata */}
              <div className="rounded-xl bg-slate-950/80 p-3 border border-slate-850 mb-4 text-xs font-mono text-slate-400 space-y-1">
                {Object.entries(item.config_summary || {}).map(([key, val]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-slate-500">{key}:</span>
                    <span className="text-slate-300 font-semibold">{String(val)}</span>
                  </div>
                ))}
              </div>

              {/* Timestamps */}
              <div className="space-y-1 text-xs text-slate-400 border-t border-slate-800 pt-3 mb-4">
                <div className="flex justify-between">
                  <span>Last Health Check:</span>
                  <span className="text-slate-300">{item.last_health_check_at ? new Date(item.last_health_check_at).toLocaleTimeString() : 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last Successful Sync:</span>
                  <span className="text-slate-300">{item.last_sync_at ? new Date(item.last_sync_at).toLocaleTimeString() : 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Toggle Control */}
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
              <span className="text-xs font-medium text-slate-300">Integration Gateway State</span>
              <button
                onClick={() => handleToggle(item.provider_key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                  item.is_enabled 
                    ? 'bg-red-950/60 hover:bg-red-900/80 text-red-300 border-red-800' 
                    : 'bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border-emerald-800'
                }`}
              >
                {item.is_enabled ? 'Disable Provider' : 'Enable Integration'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { notificationsApi } from '../api/notifications';
import { Bell, Mail, MessageSquare, Shield, Check, X, Lock } from 'lucide-react';

export default function NotificationPreferencesModal({ isOpen, onClose }) {
  const [preferences, setPreferences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadPreferences();
    }
  }, [isOpen]);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await notificationsApi.getPreferences();
      setPreferences(data);
    } catch (err) {
      console.error('Failed to load notification preferences:', err);
      setError('Unable to load notification preferences.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (pref, channel) => {
    if (pref.is_mandatory && (channel === 'in_app' || channel === 'email')) {
      return; // Locked for mandatory compliance
    }

    const key = `${pref.event_type}_${channel}`;
    setSavingKey(key);

    const updated = {
      event_type: pref.event_type,
      in_app_enabled: channel === 'in_app' ? !pref.in_app_enabled : pref.in_app_enabled,
      email_enabled: channel === 'email' ? !pref.email_enabled : pref.email_enabled,
      sms_enabled: channel === 'sms' ? !pref.sms_enabled : pref.sms_enabled,
    };

    try {
      const res = await notificationsApi.updatePreference(updated);
      setPreferences(prev => prev.map(p => p.event_type === res.event_type ? res : p));
    } catch (err) {
      console.error('Failed to update preference:', err);
      setError('Failed to update preference settings.');
    } finally {
      setSavingKey(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Notification Preferences</h3>
              <p className="text-xs text-slate-400">Configure your personal and compliance alert delivery channels</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 max-h-[70vh] overflow-y-auto space-y-4">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
              {error}
            </div>
          )}

          <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 flex items-start gap-3">
            <Shield className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300 space-y-1">
              <p className="font-medium text-white">Saskatchewan Child Welfare Compliance Notice</p>
              <p className="text-slate-400 leading-relaxed">
                Mandatory alerts (Court Hearings, Removal Orders, Placement Licensing) cannot be disabled on in-app and email channels to ensure statutory legal compliance under the Act.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="py-12 text-center text-slate-400 text-sm">Loading notification channels...</div>
          ) : (
            <div className="divide-y divide-slate-800 border border-slate-800 rounded-xl overflow-hidden bg-slate-900/40">
              {preferences.map((pref) => {
                const title = pref.event_type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
                return (
                  <div key={pref.id || pref.event_type} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-800/20 transition-colors">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white">{title}</span>
                        {pref.is_mandatory && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <Lock className="w-2.5 h-2.5" /> Mandatory
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {pref.is_mandatory ? 'Required regulatory and compliance alert' : 'Operational notifications and reminders'}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* In-App */}
                      <button
                        type="button"
                        disabled={pref.is_mandatory}
                        onClick={() => handleToggle(pref, 'in_app')}
                        title={pref.is_mandatory ? "Required in-app" : "Toggle In-App"}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all border ${
                          pref.in_app_enabled
                            ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                            : 'bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-600'
                        } ${pref.is_mandatory ? 'opacity-80 cursor-not-allowed' : ''}`}
                      >
                        <Bell className="w-3.5 h-3.5" />
                        In-App
                        {pref.in_app_enabled && <Check className="w-3 h-3 ml-0.5" />}
                      </button>

                      {/* Email */}
                      <button
                        type="button"
                        disabled={pref.is_mandatory}
                        onClick={() => handleToggle(pref, 'email')}
                        title={pref.is_mandatory ? "Required email" : "Toggle Email"}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all border ${
                          pref.email_enabled
                            ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                            : 'bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-600'
                        } ${pref.is_mandatory ? 'opacity-80 cursor-not-allowed' : ''}`}
                      >
                        <Mail className="w-3.5 h-3.5" />
                        Email
                        {pref.email_enabled && <Check className="w-3 h-3 ml-0.5" />}
                      </button>

                      {/* SMS */}
                      <button
                        type="button"
                        onClick={() => handleToggle(pref, 'sms')}
                        title="Toggle SMS"
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all border ${
                          pref.sms_enabled
                            ? 'bg-sky-500/15 text-sky-300 border-sky-500/30'
                            : 'bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-600'
                        }`}
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        SMS
                        {pref.sms_enabled && <Check className="w-3 h-3 ml-0.5" />}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/90 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

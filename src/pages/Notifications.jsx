import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationsApi } from '../api/notifications';
import {
  Bell,
  Check,
  CheckCheck,
  Clock,
  Shield,
  ShieldAlert,
  Settings,
  Filter,
  RefreshCw,
  Mail,
  MessageSquare,
  RotateCw,
  AlertCircle,
  ExternalLink,
  Search,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import NotificationPreferencesModal from '../components/NotificationPreferencesModal';

export default function Notifications() {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'unread', 'high_priority', 'deliveries'
  const [deliveries, setDeliveries] = useState([]);
  const [deliveriesLoading, setDeliveriesLoading] = useState(false);
  const [isPreferencesOpen, setIsPreferencesOpen] = useState(false);
  const [retryingId, setRetryingId] = useState(null);

  useEffect(() => {
    if (activeTab === 'deliveries') {
      loadDeliveries();
    } else {
      loadNotifications();
    }
  }, [activeTab]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const params = { page: 1, page_size: 50 };
      if (activeTab === 'unread') params.is_read = false;

      const data = await notificationsApi.listNotifications(params);
      let items = data.items || [];
      if (activeTab === 'high_priority') {
        items = items.filter(n => n.priority === 'HIGH' || n.priority === 'URGENT');
      }
      setNotifications(items);
      setTotal(data.total || items.length);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDeliveries = async () => {
    try {
      setDeliveriesLoading(true);
      const data = await notificationsApi.listDeliveries({ page: 1, page_size: 50 });
      setDeliveries(data.items || []);
    } catch (err) {
      console.error('Failed to load deliveries:', err);
    } finally {
      setDeliveriesLoading(false);
    }
  };

  const handleMarkAsRead = async (id, e) => {
    e?.stopPropagation();
    try {
      await notificationsApi.markAsRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error('Failed to mark notification read:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  const handleRetryDelivery = async (delivId) => {
    try {
      setRetryingId(delivId);
      const res = await notificationsApi.retryDelivery(delivId);
      setDeliveries(prev => prev.map(d => d.id === res.id ? res : d));
    } catch (err) {
      console.error('Failed to retry delivery:', err);
      alert('Failed to retry delivery.');
    } finally {
      setRetryingId(null);
    }
  };

  const handleNavigateRelated = (notif) => {
    if (!notif.is_read) {
      handleMarkAsRead(notif.id);
    }
    if (notif.related_entity_type === 'case' && notif.related_entity_id) {
      navigate(`/cases/${notif.related_entity_id}`);
    } else if (notif.related_entity_type === 'staffing_session' && notif.related_entity_id) {
      navigate(`/staffing/${notif.related_entity_id}`);
    } else if (notif.related_entity_type === 'court_event' || notif.related_entity_type === 'calendar_event') {
      navigate('/schedule');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-slate-900/60 p-6 rounded-3xl border border-slate-800 backdrop-blur-xl shadow-xl">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-white tracking-tight">Notification Center</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
              <Bell className="w-3 h-3" /> Multi-Channel Alerts
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            In-app notices, court reminders, case assignments, and compliance dispatch audits
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleMarkAllAsRead}
            className="px-3.5 py-2 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors flex items-center gap-1.5"
          >
            <CheckCheck className="w-4 h-4 text-emerald-400" />
            <span>Mark All as Read</span>
          </button>

          <button
            type="button"
            onClick={() => setIsPreferencesOpen(true)}
            className="px-4 py-2.5 rounded-2xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-amber-500/20 flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            <span>Delivery Preferences</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'all'
              ? 'bg-slate-800 text-amber-400 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          All Notifications
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('unread')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'unread'
              ? 'bg-slate-800 text-amber-400 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Unread Only
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('high_priority')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'high_priority'
              ? 'bg-slate-800 text-rose-400 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          High Priority &amp; Compliance
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('deliveries')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'deliveries'
              ? 'bg-slate-800 text-indigo-400 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Delivery Audit Logs
        </button>
      </div>

      {/* Main Container */}
      {activeTab === 'deliveries' ? (
        /* Deliveries Audit Table */
        <div className="bg-slate-900/60 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-800/20">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Mail className="w-4 h-4 text-indigo-400" />
              <span>Multi-Channel Outbox Deliveries ({deliveries.length})</span>
            </h3>
            <button
              type="button"
              onClick={loadDeliveries}
              className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {deliveriesLoading ? (
            <div className="py-20 text-center text-slate-500 text-xs flex flex-col items-center gap-2">
              <RefreshCw className="w-6 h-6 animate-spin text-indigo-500" />
              <span>Loading delivery logs...</span>
            </div>
          ) : deliveries.length === 0 ? (
            <div className="py-16 text-center text-slate-500 text-xs">
              No delivery records found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/40 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Channel</th>
                    <th className="py-3 px-4 font-semibold">Recipient</th>
                    <th className="py-3 px-4 font-semibold">Status</th>
                    <th className="py-3 px-4 font-semibold">Attempts</th>
                    <th className="py-3 px-4 font-semibold">Sent / Timestamp</th>
                    <th className="py-3 px-4 font-semibold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {deliveries.map((deliv) => (
                    <tr key={deliv.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-bold flex items-center gap-1.5">
                        {deliv.channel === 'EMAIL' ? <Mail className="w-3.5 h-3.5 text-emerald-400" /> :
                         deliv.channel === 'SMS' ? <MessageSquare className="w-3.5 h-3.5 text-sky-400" /> :
                         <Bell className="w-3.5 h-3.5 text-amber-400" />}
                        <span>{deliv.channel}</span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-300">
                        {deliv.recipient_address}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          deliv.status === 'SENT' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' :
                          deliv.status === 'FAILED' ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30' :
                          'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                        }`}>
                          {deliv.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {deliv.attempt_count} / {deliv.max_attempts}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {new Date(deliv.created_at).toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {deliv.status === 'FAILED' && (
                          <button
                            type="button"
                            disabled={retryingId === deliv.id}
                            onClick={() => handleRetryDelivery(deliv.id)}
                            className="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 text-[11px] font-semibold flex items-center gap-1 ml-auto"
                          >
                            <RotateCw className={`w-3 h-3 ${retryingId === deliv.id ? 'animate-spin' : ''}`} />
                            <span>Retry</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        /* Notifications List */
        <div className="bg-slate-900/60 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="py-24 text-center text-slate-500 text-sm flex flex-col items-center gap-3">
              <RefreshCw className="w-8 h-8 animate-spin text-amber-500/80" />
              <span>Loading notifications...</span>
            </div>
          ) : notifications.length === 0 ? (
            <div className="py-20 text-center p-8 flex flex-col items-center gap-3">
              <Bell className="w-12 h-12 text-slate-700" />
              <h3 className="text-base font-semibold text-slate-300">No notifications in this view</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                You're all caught up with your case updates, reminders, and team activity.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/60">
              {notifications.map((notif) => {
                const isUrgent = notif.priority === 'URGENT' || notif.priority === 'HIGH';
                return (
                  <div
                    key={notif.id}
                    onClick={() => handleNavigateRelated(notif)}
                    className={`p-5 flex flex-col sm:flex-row sm:items-start justify-between gap-4 cursor-pointer hover:bg-slate-800/30 transition-colors ${
                      !notif.is_read ? 'bg-amber-500/5' : ''
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`p-2.5 rounded-2xl shrink-0 border ${
                        isUrgent
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      }`}>
                        <ShieldAlert className="w-5 h-5" />
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-sm font-bold ${!notif.is_read ? 'text-white' : 'text-slate-300'}`}>
                            {notif.title}
                          </span>
                          {!notif.is_read && (
                            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                          )}
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                            isUrgent
                              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                              : 'bg-slate-800 text-slate-400'
                          }`}>
                            {notif.priority}
                          </span>
                        </div>

                        <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
                          {notif.message}
                        </p>

                        <div className="text-[11px] text-slate-500 pt-1">
                          {new Date(notif.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {!notif.is_read && (
                        <button
                          type="button"
                          onClick={(e) => handleMarkAsRead(notif.id, e)}
                          title="Mark as read"
                          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Mark Read</span>
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleNavigateRelated(notif);
                        }}
                        className="px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-xs font-semibold transition-colors flex items-center gap-1"
                      >
                        <span>Open</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Notification Preferences Modal */}
      <NotificationPreferencesModal
        isOpen={isPreferencesOpen}
        onClose={() => setIsPreferencesOpen(false)}
      />
    </div>
  );
}

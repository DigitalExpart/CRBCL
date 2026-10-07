import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationsApi } from '../api/notifications';
import {
  Bell,
  Check,
  CheckCheck,
  ShieldAlert,
  Settings,
  RefreshCw,
  Mail,
  MessageSquare,
  RotateCw,
  ExternalLink
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
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-card p-6 rounded-2xl border border-border shadow-sm">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Notification Center</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center gap-1">
              <Bell className="w-3 h-3" /> Multi-Channel Alerts
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            In-app notices, court reminders, case assignments, and compliance dispatch audits
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleMarkAllAsRead}
            className="px-3.5 py-2 rounded-xl bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs font-semibold transition-colors flex items-center gap-1.5"
          >
            <CheckCheck className="w-4 h-4 text-emerald-500" />
            <span>Mark All as Read</span>
          </button>

          <button
            type="button"
            onClick={() => setIsPreferencesOpen(true)}
            className="px-4 py-2 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-bold transition-all shadow-sm flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            <span>Delivery Preferences</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'all'
              ? 'bg-secondary text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          All Notifications
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('unread')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'unread'
              ? 'bg-secondary text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Unread Only
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('high_priority')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'high_priority'
              ? 'bg-secondary text-rose-500 shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          High Priority &amp; Compliance
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('deliveries')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'deliveries'
              ? 'bg-secondary text-indigo-500 shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Delivery Audit Logs
        </button>
      </div>

      {/* Main Container */}
      {activeTab === 'deliveries' ? (
        /* Deliveries Audit Table */
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
              <Mail className="w-4 h-4 text-indigo-500" />
              <span>Multi-Channel Outbox Deliveries ({deliveries.length})</span>
            </h3>
            <button
              type="button"
              onClick={loadDeliveries}
              className="p-1.5 rounded-lg bg-secondary text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {deliveriesLoading ? (
            <div className="py-20 text-center text-muted-foreground text-xs flex flex-col items-center gap-2">
              <RefreshCw className="w-6 h-6 animate-spin text-primary" />
              <span>Loading delivery logs...</span>
            </div>
          ) : deliveries.length === 0 ? (
            <div className="py-16 text-center text-muted-foreground text-xs">
              No delivery records found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/40 text-muted-foreground border-b border-border">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Channel</th>
                    <th className="py-3 px-4 font-semibold">Recipient</th>
                    <th className="py-3 px-4 font-semibold">Status</th>
                    <th className="py-3 px-4 font-semibold">Attempts</th>
                    <th className="py-3 px-4 font-semibold">Sent / Timestamp</th>
                    <th className="py-3 px-4 font-semibold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-foreground">
                  {deliveries.map((deliv) => (
                    <tr key={deliv.id} className="hover:bg-muted/50 transition-colors">
                      <td className="py-3.5 px-4 font-bold flex items-center gap-1.5">
                        {deliv.channel === 'EMAIL' ? <Mail className="w-3.5 h-3.5 text-emerald-500" /> :
                         deliv.channel === 'SMS' ? <MessageSquare className="w-3.5 h-3.5 text-sky-500" /> :
                         <Bell className="w-3.5 h-3.5 text-amber-500" />}
                        <span>{deliv.channel}</span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-muted-foreground">
                        {deliv.recipient_address}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          deliv.status === 'SENT' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' :
                          deliv.status === 'FAILED' ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30' :
                          'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30'
                        }`}>
                          {deliv.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-muted-foreground">
                        {deliv.attempt_count} / {deliv.max_attempts}
                      </td>
                      <td className="py-3.5 px-4 text-muted-foreground">
                        {new Date(deliv.created_at).toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {deliv.status === 'FAILED' && (
                          <button
                            type="button"
                            disabled={retryingId === deliv.id}
                            onClick={() => handleRetryDelivery(deliv.id)}
                            className="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 text-[11px] font-semibold flex items-center gap-1 ml-auto"
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
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          {loading ? (
            <div className="py-24 text-center text-muted-foreground text-sm flex flex-col items-center gap-3">
              <RefreshCw className="w-8 h-8 animate-spin text-primary" />
              <span>Loading notifications...</span>
            </div>
          ) : notifications.length === 0 ? (
            <div className="py-20 text-center p-8 flex flex-col items-center gap-3">
              <Bell className="w-12 h-12 text-muted-foreground/40" />
              <h3 className="text-base font-semibold text-foreground">No notifications in this view</h3>
              <p className="text-xs text-muted-foreground max-w-sm">
                You're all caught up with your case updates, reminders, and team activity.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {notifications.map((notif) => {
                const isUrgent = notif.priority === 'URGENT' || notif.priority === 'HIGH';
                return (
                  <div
                    key={notif.id}
                    onClick={() => handleNavigateRelated(notif)}
                    className={`p-5 flex flex-col sm:flex-row sm:items-start justify-between gap-4 cursor-pointer hover:bg-muted/50 transition-colors ${
                      !notif.is_read ? 'bg-primary/5' : ''
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`p-2.5 rounded-2xl shrink-0 border ${
                        isUrgent
                          ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                      }`}>
                        <ShieldAlert className="w-5 h-5" />
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-sm font-bold ${!notif.is_read ? 'text-foreground' : 'text-muted-foreground'}`}>
                            {notif.title}
                          </span>
                          {!notif.is_read && (
                            <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
                          )}
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                            isUrgent
                              ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30'
                              : 'bg-secondary text-secondary-foreground'
                          }`}>
                            {notif.priority}
                          </span>
                        </div>

                        <p className="text-xs text-muted-foreground leading-relaxed max-w-2xl">
                          {notif.message}
                        </p>

                        <div className="text-[11px] text-muted-foreground pt-1">
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
                          className="px-3 py-1.5 rounded-xl bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs font-medium transition-colors flex items-center gap-1"
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
                        className="px-3 py-1.5 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary text-xs font-semibold transition-colors flex items-center gap-1"
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

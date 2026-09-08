import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { notificationsApi } from "@/api/notifications";
import { Bell, Check, CheckCheck, ShieldAlert, Sparkles, ExternalLink, Settings } from "lucide-react";
import NotificationPreferencesModal from "@/components/NotificationPreferencesModal";

export default function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [recentNotifications, setRecentNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [preferencesOpen, setPreferencesOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const data = await notificationsApi.getUnreadCount();
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      // silently ignore
    }
  };

  const handleOpenDropdown = async () => {
    if (!isOpen) {
      setIsOpen(true);
      setLoading(true);
      try {
        const data = await notificationsApi.listNotifications({ page: 1, page_size: 5 });
        setRecentNotifications(data.items || []);
      } catch (err) {
        console.error("Failed to load recent notifications:", err);
      } finally {
        setLoading(false);
      }
    } else {
      setIsOpen(false);
    }
  };

  const handleMarkAsRead = async (id, e) => {
    e.stopPropagation();
    try {
      await notificationsApi.markAsRead(id);
      setRecentNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to mark read:", err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setRecentNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all as read:", err);
    }
  };

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      notificationsApi.markAsRead(notification.id).catch(() => {});
      setUnreadCount(prev => Math.max(0, prev - 1));
    }
    setIsOpen(false);

    if (notification.related_entity_type === "case" && notification.related_entity_id) {
      navigate(`/cases/${notification.related_entity_id}`);
    } else if (notification.related_entity_type === "court_event") {
      navigate("/schedule");
    } else if (notification.related_entity_type === "staffing_session" && notification.related_entity_id) {
      navigate(`/staffing/${notification.related_entity_id}`);
    } else if (notification.related_entity_type === "calendar_event") {
      navigate("/schedule");
    } else {
      navigate("/notifications");
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={handleOpenDropdown}
        aria-label="Notifications"
        className="relative p-2 rounded-xl bg-card hover:bg-muted/80 text-foreground border border-border transition-all focus:outline-none focus:ring-2 focus:ring-amber-500/40"
      >
        <Bell className="w-5 h-5 text-muted-foreground hover:text-foreground" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-destructive px-1.5 text-[10px] font-bold text-white shadow-lg ring-2 ring-background animate-pulse">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 sm:w-96 rounded-2xl bg-card border border-border shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between bg-muted/20">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-foreground text-xs">Notifications</h4>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                  {unreadCount} new
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={handleMarkAllAsRead}
                  title="Mark all as read"
                  className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  <CheckCheck className="w-4 h-4" />
                </button>
              )}
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  setPreferencesOpen(true);
                }}
                title="Notification preferences"
                className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="max-h-[360px] overflow-y-auto divide-y divide-border/60">
            {loading ? (
              <div className="py-8 text-center text-muted-foreground text-xs">Loading alerts...</div>
            ) : recentNotifications.length === 0 ? (
              <div className="py-10 text-center text-muted-foreground text-xs flex flex-col items-center gap-2">
                <Sparkles className="w-6 h-6 text-muted-foreground/60" />
                <span>All caught up! No notifications.</span>
              </div>
            ) : (
              recentNotifications.map((notif) => (
                <div
                  key={notif.id}
                  onClick={() => handleNotificationClick(notif)}
                  className={`p-3.5 flex items-start gap-3 cursor-pointer hover:bg-muted/40 transition-colors ${
                    !notif.is_read ? "bg-amber-500/5" : ""
                  }`}
                >
                  <div className="p-1.5 rounded-lg shrink-0 border border-border bg-card text-amber-500">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline justify-between gap-1">
                      <p className={`text-xs truncate ${!notif.is_read ? "font-bold text-foreground" : "font-medium text-muted-foreground"}`}>
                        {notif.title}
                      </p>
                      <span className="text-[10px] text-muted-foreground shrink-0">
                        {new Date(notif.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <p className="text-[11px] text-muted-foreground line-clamp-2 mt-0.5 leading-relaxed">
                      {notif.message}
                    </p>
                  </div>
                  {!notif.is_read && (
                    <button
                      type="button"
                      onClick={(e) => handleMarkAsRead(notif.id, e)}
                      title="Mark as read"
                      className="p-1 rounded-md text-muted-foreground hover:text-amber-500 hover:bg-muted"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="p-2 border-t border-border bg-card text-center">
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                navigate("/notifications");
              }}
              className="w-full py-1.5 rounded-lg text-xs font-semibold text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 transition-colors flex items-center justify-center gap-1"
            >
              <span>View all notifications</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}

      <NotificationPreferencesModal
        isOpen={preferencesOpen}
        onClose={() => setPreferencesOpen(false)}
      />
    </div>
  );
}

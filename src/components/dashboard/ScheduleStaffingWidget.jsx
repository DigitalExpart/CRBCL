import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { calendarApi } from '@/api/calendar';
import { staffingApi } from '@/api/staffing';
import {
  Calendar,
  Clock,
  Users,
  ChevronRight,
  ShieldAlert,
  ArrowRight,
  AlertCircle,
  FileText
} from 'lucide-react';

export default function ScheduleStaffingWidget() {
  const navigate = useNavigate();
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [staffingBuckets, setStaffingBuckets] = useState({ not_staffed_90_days: [], high_risk: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const todayStart = new Date();
        todayStart.setHours(0, 0, 0, 0);
        const inThreeDays = new Date();
        inThreeDays.setDate(inThreeDays.getDate() + 3);
        inThreeDays.setHours(23, 59, 59, 999);

        const [sched, buckets] = await Promise.all([
          calendarApi.getPersonalSchedule(todayStart, inThreeDays, []).catch(() => []),
          staffingApi.getCaseBuckets().catch(() => ({ not_staffed_90_days: [], high_risk: [] })),
        ]);

        setUpcomingEvents((sched || []).slice(0, 4));
        setStaffingBuckets(buckets || {});
      } catch (err) {
        // silent fallback
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const notStaffedCount = staffingBuckets.not_staffed_90_days?.length || 0;
  const highRiskCount = staffingBuckets.high_risk?.length || 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Upcoming Schedule */}
      <div className="bg-card rounded-xl border border-border p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Calendar className="w-4 h-4 text-amber-500" />
              <span>Upcoming Appointments &amp; Hearings</span>
            </h3>
            <Link
              to="/schedule"
              className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
            >
              <span>My Schedule</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <p className="text-xs text-muted-foreground text-center py-6">Loading schedule...</p>
          ) : upcomingEvents.length === 0 ? (
            <div className="p-6 text-center text-xs text-muted-foreground bg-muted/20 rounded-xl">
              No appointments or court hearings in the next 3 days.
            </div>
          ) : (
            <div className="space-y-2.5">
              {upcomingEvents.map((evt) => {
                const timeStr = new Date(evt.start_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const dateStr = new Date(evt.start_at).toLocaleDateString([], { month: 'short', day: 'numeric' });
                return (
                  <div
                    key={evt.id}
                    onClick={() => navigate('/schedule')}
                    className="p-2.5 rounded-lg border border-border bg-card hover:bg-muted/40 transition-colors flex items-center justify-between gap-3 cursor-pointer text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="px-2 py-1 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-mono font-bold text-[11px] shrink-0 text-center">
                        <div>{dateStr}</div>
                        <div className="text-[9px] font-normal">{timeStr}</div>
                      </div>
                      <div className="truncate">
                        <p className="font-semibold text-foreground truncate">{evt.title}</p>
                        <p className="text-[11px] text-muted-foreground truncate">
                          {evt.event_type} {evt.location ? `• ${evt.location}` : ''}
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground shrink-0">
                      {evt.status}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Staffing Facilitator Triage Quick View */}
      <div className="bg-card rounded-xl border border-border p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-500" />
              <span>Multi-Disciplinary Staffing Alerts</span>
            </h3>
            <Link
              to="/staffing"
              className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
            >
              <span>Staffing Hub</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-2">
            <Link
              to="/staffing"
              className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/5 hover:bg-amber-500/10 transition-colors block"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-amber-700 dark:text-amber-300">Not Staffed 90+ Days</span>
                <Clock className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-bold font-mono text-foreground">{notStaffedCount}</div>
              <p className="text-[10px] text-muted-foreground mt-1">Cases needing statutory review</p>
            </Link>

            <Link
              to="/staffing"
              className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-500/5 hover:bg-rose-500/10 transition-colors block"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-rose-700 dark:text-rose-300">High Risk Active</span>
                <ShieldAlert className="w-4 h-4 text-rose-500" />
              </div>
              <div className="text-2xl font-bold font-mono text-rose-600 dark:text-rose-400">{highRiskCount}</div>
              <p className="text-[10px] text-muted-foreground mt-1">Immediate safety concerns</p>
            </Link>
          </div>
        </div>

        <div className="pt-3 border-t border-border mt-3 text-right">
          <Link
            to="/staffing"
            className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            <span>Launch Staffing Facilitator Console</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>
    </div>
  );
}

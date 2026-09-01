import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { calendarApi } from '../api/calendar';
import { usersApi } from '../api/users';
import { teamsApi } from '../api/teams';
import {
  Users,
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  ChevronLeft,
  ChevronRight,
  Shield,
  FolderLock,
  Filter,
  User,
  RefreshCw,
  FileText,
  Activity,
  Layers
} from 'lucide-react';

const EVENT_TYPE_COLORS = {
  APPOINTMENT: { bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30', label: 'Appointment' },
  COURT: { bg: 'bg-rose-500/15', text: 'text-rose-300', border: 'border-rose-500/30', label: 'Court Hearing' },
  STAFFING: { bg: 'bg-indigo-500/15', text: 'text-indigo-300', border: 'border-indigo-500/30', label: 'Staffing Session' },
  VISITATION: { bg: 'bg-purple-500/15', text: 'text-purple-300', border: 'border-purple-500/30', label: 'Kinship Visitation' },
  CASE_NOTE_FOLLOWUP: { bg: 'bg-amber-500/15', text: 'text-amber-300', border: 'border-amber-500/30', label: 'Follow-Up' },
  HOME_VISIT: { bg: 'bg-sky-500/15', text: 'text-sky-300', border: 'border-sky-500/30', label: 'Home Visit' },
  OTHER: { bg: 'bg-slate-500/15', text: 'text-slate-300', border: 'border-slate-500/30', label: 'Other' },
};

export default function TeamSchedule() {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [teams, setTeams] = useState([]);
  const [selectedTeamId, setSelectedTeamId] = useState('');
  const [workers, setWorkers] = useState([]);
  const [selectedWorkerIds, setSelectedWorkerIds] = useState([]);

  // Calculate Monday to Sunday current week range
  const { weekStart, weekEnd, weekDays } = useMemo(() => {
    const start = new Date(currentDate);
    const day = start.getDay();
    const diff = start.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is sunday
    start.setDate(diff);
    start.setHours(0, 0, 0, 0);

    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    end.setHours(23, 59, 59, 999);

    const days = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      days.push(d);
    }

    return { weekStart: start, weekEnd: end, weekDays: days };
  }, [currentDate]);

  useEffect(() => {
    loadTeamsAndWorkers();
  }, []);

  useEffect(() => {
    loadTeamSchedule();
  }, [weekStart, weekEnd, selectedTeamId, selectedWorkerIds]);

  const loadTeamsAndWorkers = async () => {
    try {
      const [teamsRes, usersRes] = await Promise.all([
        teamsApi.listTeams().catch(() => ({ items: [] })),
        usersApi.listUsers({ is_active: true, page_size: 100 }).catch(() => ({ items: [] })),
      ]);
      setTeams(teamsRes.items || teamsRes || []);
      setWorkers(usersRes.items || usersRes || []);
    } catch (err) {
      console.error('Failed to load teams/workers:', err);
    }
  };

  const loadTeamSchedule = async () => {
    try {
      setLoading(true);
      const data = await calendarApi.getTeamSchedule(
        weekStart,
        weekEnd,
        selectedTeamId || null,
        selectedWorkerIds,
        []
      );
      setEvents(data || []);
    } catch (err) {
      console.error('Failed to load team schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrevWeek = () => {
    const next = new Date(currentDate);
    next.setDate(next.getDate() - 7);
    setCurrentDate(next);
  };

  const handleNextWeek = () => {
    const next = new Date(currentDate);
    next.setDate(next.getDate() + 7);
    setCurrentDate(next);
  };

  const handleThisWeek = () => {
    setCurrentDate(new Date());
  };

  // Group events by day
  const eventsByDay = useMemo(() => {
    const map = {};
    weekDays.forEach(d => {
      map[d.toDateString()] = [];
    });
    events.forEach(evt => {
      const d = new Date(evt.start_at).toDateString();
      if (map[d]) map[d].push(evt);
    });
    return map;
  }, [events, weekDays]);

  // Worker workload event summary
  const workerWorkload = useMemo(() => {
    const counts = {};
    events.forEach(e => {
      const name = e.assigned_user_name || 'Unassigned / Team';
      counts[name] = (counts[name] || 0) + 1;
    });
    return counts;
  }, [events]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-slate-900/60 p-6 rounded-3xl border border-slate-800 backdrop-blur-xl shadow-xl">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-white tracking-tight">Team Calendar & Workload</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center gap-1">
              <Users className="w-3 h-3" /> Multi-Worker Overview
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Supervisor visibility into casework assignments, hearing schedules, and team commitments
          </p>
        </div>

        {/* Team & Worker Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedTeamId}
            onChange={(e) => setSelectedTeamId(e.target.value)}
            className="px-3.5 py-2 rounded-2xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          >
            <option value="">All Teams & Units</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Week Navigator & Workload Strip */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Date Controls */}
        <div className="lg:col-span-3 bg-slate-900/40 p-4 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleThisWeek}
              className="px-3 py-1.5 rounded-xl bg-slate-800 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            >
              Current Week
            </button>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handlePrevWeek}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={handleNextWeek}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <span className="text-sm font-semibold text-white">
              {weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              {' — '}
              {weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          </div>

          <div className="text-xs text-slate-400 font-medium">
            Total Events: <span className="text-amber-400 font-bold">{events.length}</span>
          </div>
        </div>

        {/* Workload Pill summary */}
        <div className="bg-slate-900/40 p-4 rounded-2xl border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-semibold text-white">Active Staff</span>
          </div>
          <span className="text-xs font-bold text-slate-300 bg-slate-800 px-2.5 py-1 rounded-lg">
            {Object.keys(workerWorkload).length} Workers Scheduled
          </span>
        </div>
      </div>

      {/* 7-Day Week Grid */}
      {loading ? (
        <div className="py-24 text-center text-slate-500 text-sm flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500/80" />
          <span>Synchronizing team schedules...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-3">
          {weekDays.map((day) => {
            const dayKey = day.toDateString();
            const dayEvents = eventsByDay[dayKey] || [];
            const isToday = new Date().toDateString() === dayKey;

            return (
              <div
                key={dayKey}
                className={`rounded-2xl border flex flex-col min-h-[420px] overflow-hidden ${
                  isToday
                    ? 'bg-slate-900/90 border-amber-500/40 ring-1 ring-amber-500/20'
                    : 'bg-slate-900/40 border-slate-800/80'
                }`}
              >
                {/* Day Header */}
                <div className={`p-3 text-center border-b ${
                  isToday ? 'bg-amber-500/10 border-amber-500/20' : 'bg-slate-800/30 border-slate-800'
                }`}>
                  <span className={`text-[11px] font-bold block uppercase tracking-wider ${
                    isToday ? 'text-amber-400' : 'text-slate-400'
                  }`}>
                    {day.toLocaleDateString('en-US', { weekday: 'short' })}
                  </span>
                  <span className={`text-base font-bold ${
                    isToday ? 'text-white' : 'text-slate-200'
                  }`}>
                    {day.getDate()}
                  </span>
                </div>

                {/* Day Event List */}
                <div className="p-2 space-y-2 flex-1 overflow-y-auto max-h-[500px]">
                  {dayEvents.length === 0 ? (
                    <div className="py-8 text-center text-[11px] text-slate-600">
                      No events
                    </div>
                  ) : (
                    dayEvents.map((evt) => {
                      const style = EVENT_TYPE_COLORS[evt.event_type] || EVENT_TYPE_COLORS.OTHER;
                      const timeStr = new Date(evt.start_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

                      return (
                        <div
                          key={evt.id}
                          onClick={() => {
                            if (!evt.is_redacted && evt.case_id) {
                              navigate(`/cases/${evt.case_id}`);
                            }
                          }}
                          className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all hover:scale-[1.02] ${
                            style.bg
                          } ${style.border} ${evt.is_redacted ? 'opacity-70 bg-slate-950/60' : ''}`}
                        >
                          <div className="flex items-center justify-between gap-1 mb-1">
                            <span className="text-[10px] font-bold font-mono text-slate-400">
                              {timeStr}
                            </span>
                            <span className={`text-[9px] font-bold uppercase px-1.5 py-0.2 rounded ${style.text}`}>
                              {evt.event_type}
                            </span>
                          </div>

                          <p className="font-semibold text-white line-clamp-2 leading-tight">
                            {evt.title}
                          </p>

                          {evt.is_redacted ? (
                            <div className="mt-1 flex items-center gap-1 text-[10px] text-amber-400">
                              <FolderLock className="w-3 h-3" />
                              <span>Restricted</span>
                            </div>
                          ) : (
                            <div className="mt-1.5 pt-1 border-t border-slate-700/40 text-[10px] text-slate-300 space-y-0.5">
                              {evt.assigned_user_name && (
                                <div className="flex items-center gap-1 truncate">
                                  <User className="w-3 h-3 text-slate-400 shrink-0" />
                                  <span className="truncate">{evt.assigned_user_name}</span>
                                </div>
                              )}
                              {evt.case_number && (
                                <div className="flex items-center gap-1 font-mono text-amber-300/80">
                                  <FileText className="w-3 h-3 text-slate-400 shrink-0" />
                                  <span>{evt.case_number}</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

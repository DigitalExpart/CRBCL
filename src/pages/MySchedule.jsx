import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { calendarApi } from '../api/calendar';
import { casesApi } from '../api/cases';
import {
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  Plus,
  Filter,
  ChevronLeft,
  ChevronRight,
  Shield,
  User,
  FolderLock,
  Sparkles,
  RefreshCw,
  X,
  AlertCircle,
  FileText,
  Gavel,
  Users,
  Home,
  CheckCircle2
} from 'lucide-react';

const EVENT_TYPE_COLORS = {
  APPOINTMENT: { bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30', label: 'Appointment' },
  COURT: { bg: 'bg-rose-500/15', text: 'text-rose-300', border: 'border-rose-500/30', label: 'Court Hearing' },
  STAFFING: { bg: 'bg-indigo-500/15', text: 'text-indigo-300', border: 'border-indigo-500/30', label: 'Staffing Session' },
  VISITATION: { bg: 'bg-purple-500/15', text: 'text-purple-300', border: 'border-purple-500/30', label: 'Kinship Visitation' },
  CASE_NOTE_FOLLOWUP: { bg: 'bg-amber-500/15', text: 'text-amber-300', border: 'border-amber-500/30', label: 'Case Follow-Up' },
  HOME_VISIT: { bg: 'bg-sky-500/15', text: 'text-sky-300', border: 'border-sky-500/30', label: 'Home Visit' },
  ASSESSMENT: { bg: 'bg-cyan-500/15', text: 'text-cyan-300', border: 'border-cyan-500/30', label: 'Assessment' },
  PLAN_MEETING: { bg: 'bg-teal-500/15', text: 'text-teal-300', border: 'border-teal-500/30', label: 'Plan Meeting' },
  OTHER: { bg: 'bg-slate-500/15', text: 'text-slate-300', border: 'border-slate-500/30', label: 'General Event' },
};

export default function MySchedule() {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState('week'); // 'day', 'week', 'month', 'agenda'
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState(Object.keys(EVENT_TYPE_COLORS));
  const [casesList, setCasesList] = useState([]);

  // Date Range Calculation based on viewMode
  const { rangeStart, rangeEnd } = useMemo(() => {
    const start = new Date(currentDate);
    const end = new Date(currentDate);

    if (viewMode === 'day') {
      start.setHours(0, 0, 0, 0);
      end.setHours(23, 59, 59, 999);
    } else if (viewMode === 'week') {
      const day = start.getDay();
      start.setDate(start.getDate() - day);
      start.setHours(0, 0, 0, 0);
      end.setDate(start.getDate() + 6);
      end.setHours(23, 59, 59, 999);
    } else if (viewMode === 'month') {
      start.setDate(1);
      start.setHours(0, 0, 0, 0);
      end.setMonth(end.getMonth() + 1);
      end.setDate(0);
      end.setHours(23, 59, 59, 999);
    } else {
      // Agenda (30 days from start of week)
      start.setHours(0, 0, 0, 0);
      end.setDate(start.getDate() + 30);
      end.setHours(23, 59, 59, 999);
    }
    return { rangeStart: start, rangeEnd: end };
  }, [currentDate, viewMode]);

  useEffect(() => {
    loadSchedule();
  }, [rangeStart, rangeEnd, selectedTypes]);

  useEffect(() => {
    loadCases();
  }, []);

  const loadSchedule = async () => {
    try {
      setLoading(true);
      const data = await calendarApi.getPersonalSchedule(rangeStart, rangeEnd, selectedTypes);
      setEvents(data || []);
    } catch (err) {
      console.error('Failed to load schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCases = async () => {
    try {
      const res = await casesApi.listCases({ page: 1, page_size: 50 });
      setCasesList(res.items || []);
    } catch (err) {
      console.error('Failed to load cases list:', err);
    }
  };

  const handlePrev = () => {
    const next = new Date(currentDate);
    if (viewMode === 'day') next.setDate(next.getDate() - 1);
    else if (viewMode === 'week') next.setDate(next.getDate() - 7);
    else if (viewMode === 'month') next.setMonth(next.getMonth() - 1);
    else next.setDate(next.getDate() - 14);
    setCurrentDate(next);
  };

  const handleNext = () => {
    const next = new Date(currentDate);
    if (viewMode === 'day') next.setDate(next.getDate() + 1);
    else if (viewMode === 'week') next.setDate(next.getDate() + 7);
    else if (viewMode === 'month') next.setMonth(next.getMonth() + 1);
    else next.setDate(next.getDate() + 14);
    setCurrentDate(next);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const toggleTypeFilter = (type) => {
    setSelectedTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    );
  };

  // Group events by date for agenda and week views
  const eventsByDate = useMemo(() => {
    const map = {};
    events.forEach(evt => {
      const d = new Date(evt.start_at).toDateString();
      if (!map[d]) map[d] = [];
      map[d].push(evt);
    });
    return map;
  }, [events]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-slate-900/60 p-6 rounded-3xl border border-slate-800 backdrop-blur-xl shadow-xl">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-white tracking-tight">My Schedule</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
              <Clock className="w-3 h-3" /> America/Regina (CST)
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Personal appointments, court dates, staffing sessions, and synchronized case follow-ups
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center bg-slate-800/80 rounded-2xl p-1 border border-slate-700/60">
            {['day', 'week', 'month', 'agenda'].map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium capitalize transition-all ${
                  viewMode === mode
                    ? 'bg-amber-500 text-slate-950 font-semibold shadow-lg shadow-amber-500/20'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2.5 rounded-2xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-amber-500/20 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>New Appointment</span>
          </button>
        </div>
      </div>

      {/* Date Navigation & Type Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 p-4 rounded-2xl border border-slate-800/80">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleToday}
            className="px-3 py-1.5 rounded-xl bg-slate-800 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
          >
            Today
          </button>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={handlePrev}
              className="p-1.5 rounded-lg bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={handleNext}
              className="p-1.5 rounded-lg bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <span className="text-sm font-semibold text-white">
            {rangeStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            {' — '}
            {rangeEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </span>
        </div>

        {/* Event Type Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {Object.entries(EVENT_TYPE_COLORS).map(([type, cfg]) => {
            const active = selectedTypes.includes(type);
            return (
              <button
                key={type}
                type="button"
                onClick={() => toggleTypeFilter(type)}
                className={`px-2.5 py-1 rounded-xl text-[11px] font-medium transition-all border ${
                  active
                    ? `${cfg.bg} ${cfg.text} ${cfg.border}`
                    : 'bg-slate-800/40 text-slate-500 border-slate-800 hover:border-slate-700'
                }`}
              >
                {cfg.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Schedule Container */}
      {loading ? (
        <div className="py-24 text-center text-slate-500 text-sm flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-500/80" />
          <span>Synchronizing schedule events...</span>
        </div>
      ) : events.length === 0 ? (
        <div className="py-20 text-center bg-slate-900/30 border border-slate-800/60 rounded-3xl p-8 flex flex-col items-center gap-3">
          <CalendarIcon className="w-12 h-12 text-slate-700" />
          <h3 className="text-base font-semibold text-slate-300">No scheduled events in this time window</h3>
          <p className="text-xs text-slate-500 max-w-md">
            You have no appointments, court hearings, or staffing sessions matching the selected filter criteria.
          </p>
          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="mt-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-semibold transition-colors"
          >
            Create Appointment
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Agenda / Grouped List Layout */}
          {Object.entries(eventsByDate).map(([dateStr, dateEvents]) => (
            <div key={dateStr} className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
              <div className="px-5 py-3 bg-slate-800/40 border-b border-slate-800 flex items-center justify-between">
                <span className="text-sm font-semibold text-white flex items-center gap-2">
                  <CalendarIcon className="w-4 h-4 text-amber-400" />
                  {dateStr}
                </span>
                <span className="text-xs font-medium text-slate-400">
                  {dateEvents.length} {dateEvents.length === 1 ? 'event' : 'events'}
                </span>
              </div>

              <div className="divide-y divide-slate-800/60">
                {dateEvents.map((evt) => {
                  const style = EVENT_TYPE_COLORS[evt.event_type] || EVENT_TYPE_COLORS.OTHER;
                  const startTime = new Date(evt.start_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  const endTime = new Date(evt.end_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                  return (
                    <div
                      key={evt.id}
                      onClick={() => setSelectedEvent(evt)}
                      className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer hover:bg-slate-800/30 transition-colors ${
                        evt.is_redacted ? 'opacity-80 bg-slate-950/40' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3.5">
                        <div className={`px-2.5 py-1.5 rounded-xl border shrink-0 text-center ${style.bg} ${style.border}`}>
                          <div className={`text-xs font-bold ${style.text}`}>{startTime}</div>
                          <div className="text-[10px] text-slate-400">{endTime}</div>
                        </div>

                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`text-xs font-semibold px-2 py-0.5 rounded-md border ${style.bg} ${style.text} ${style.border}`}>
                              {style.label}
                            </span>
                            {evt.is_redacted ? (
                              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                                <FolderLock className="w-3 h-3" /> Case Restricted (Privacy Masked)
                              </span>
                            ) : null}
                            <span className="text-sm font-semibold text-white">
                              {evt.title}
                            </span>
                          </div>

                          {!evt.is_redacted && (
                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400 mt-1.5">
                              {evt.case_number && (
                                <span className="flex items-center gap-1 font-mono text-slate-300">
                                  <FileText className="w-3.5 h-3.5 text-slate-500" />
                                  {evt.case_number}
                                </span>
                              )}
                              {evt.person_name && (
                                <span className="flex items-center gap-1 text-slate-300">
                                  <User className="w-3.5 h-3.5 text-slate-500" />
                                  {evt.person_name}
                                </span>
                              )}
                              {evt.location && (
                                <span className="flex items-center gap-1">
                                  <MapPin className="w-3.5 h-3.5 text-slate-500" />
                                  {evt.location}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium px-2.5 py-1 rounded-lg ${
                          evt.status === 'SCHEDULED' ? 'bg-slate-800 text-slate-300' :
                          evt.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}>
                          {evt.status}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
              <div className="flex items-center gap-2.5">
                <span className={`px-2.5 py-1 rounded-xl text-xs font-semibold border ${
                  (EVENT_TYPE_COLORS[selectedEvent.event_type] || EVENT_TYPE_COLORS.OTHER).bg
                } ${(EVENT_TYPE_COLORS[selectedEvent.event_type] || EVENT_TYPE_COLORS.OTHER).text} ${
                  (EVENT_TYPE_COLORS[selectedEvent.event_type] || EVENT_TYPE_COLORS.OTHER).border
                }`}>
                  {(EVENT_TYPE_COLORS[selectedEvent.event_type] || EVENT_TYPE_COLORS.OTHER).label}
                </span>
                <span className="text-xs font-mono text-slate-400">{selectedEvent.status}</span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedEvent(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <h3 className="text-lg font-bold text-white">{selectedEvent.title}</h3>
                {selectedEvent.is_redacted && (
                  <div className="mt-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center gap-2">
                    <FolderLock className="w-4 h-4 shrink-0" />
                    <span>This event is linked to a restricted case. Sensitive information is hidden to preserve confidentiality.</span>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 bg-slate-800/40 p-4 rounded-2xl border border-slate-700/40 text-xs">
                <div>
                  <span className="text-slate-500 block mb-0.5">Start Time</span>
                  <span className="font-semibold text-white">
                    {new Date(selectedEvent.start_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block mb-0.5">End Time</span>
                  <span className="font-semibold text-white">
                    {new Date(selectedEvent.end_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                  </span>
                </div>
                {!selectedEvent.is_redacted && selectedEvent.location && (
                  <div className="col-span-2">
                    <span className="text-slate-500 block mb-0.5">Location</span>
                    <span className="font-semibold text-white flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {selectedEvent.location}
                    </span>
                  </div>
                )}
                {!selectedEvent.is_redacted && selectedEvent.case_number && (
                  <div>
                    <span className="text-slate-500 block mb-0.5">Case Reference</span>
                    <button
                      type="button"
                      onClick={() => navigate(`/cases/${selectedEvent.case_id}`)}
                      className="font-mono text-amber-400 hover:underline flex items-center gap-1"
                    >
                      {selectedEvent.case_number}
                    </button>
                  </div>
                )}
                {!selectedEvent.is_redacted && selectedEvent.person_name && (
                  <div>
                    <span className="text-slate-500 block mb-0.5">Person Involved</span>
                    <span className="text-slate-200">{selectedEvent.person_name}</span>
                  </div>
                )}
              </div>

              {!selectedEvent.is_redacted && selectedEvent.description && (
                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-1">Details & Agenda</span>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-800/20 p-3 rounded-xl border border-slate-800">
                    {selectedEvent.description}
                  </p>
                </div>
              )}
            </div>

            <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/90 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Appointment Modal */}
      {isCreateModalOpen && (
        <CreateAppointmentModal
          isOpen={isCreateModalOpen}
          cases={casesList}
          onClose={() => setIsCreateModalOpen(false)}
          onCreated={() => {
            setIsCreateModalOpen(false);
            loadSchedule();
          }}
        />
      )}
    </div>
  );
}

function CreateAppointmentModal({ isOpen, cases, onClose, onCreated }) {
  const [formData, setFormData] = useState({
    title: '',
    event_type: 'APPOINTMENT',
    start_date: new Date().toISOString().split('T')[0],
    start_time: '10:00',
    duration_minutes: 60,
    location: 'CRBCL Family Wellness Lodge',
    description: '',
    case_id: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title) {
      setError('Title is required.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const start = new Date(`${formData.start_date}T${formData.start_time}:00`);
      const end = new Date(start.getTime() + formData.duration_minutes * 60000);

      const payload = {
        title: formData.title,
        event_type: formData.event_type,
        start_at: start.toISOString(),
        end_at: end.toISOString(),
        location: formData.location || null,
        description: formData.description || null,
        case_id: formData.case_id || null,
        status: 'SCHEDULED',
      };

      await calendarApi.createEvent(payload);
      onCreated();
    } catch (err) {
      console.error('Failed to create appointment:', err);
      setError(err.response?.data?.detail || 'Failed to schedule appointment.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <CalendarIcon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Schedule Appointment</h3>
              <p className="text-xs text-slate-400">Add an appointment, home visit, or case consultation</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Event Title *</label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g., Kinship Caregiver Support Check-in"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Event Category</label>
              <select
                value={formData.event_type}
                onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40"
              >
                <option value="APPOINTMENT">Appointment</option>
                <option value="HOME_VISIT">Home Visit</option>
                <option value="VISITATION">Kinship Visitation</option>
                <option value="ASSESSMENT">Assessment Consultation</option>
                <option value="PLAN_MEETING">Plan Meeting</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Related Case</label>
              <select
                value={formData.case_id}
                onChange={(e) => setFormData({ ...formData, case_id: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40 font-mono"
              >
                <option value="">None / General Matter</option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.case_number} - {c.title?.substring(0, 24)}...
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-1">
              <label className="block text-xs font-medium text-slate-300 mb-1">Date</label>
              <input
                type="date"
                required
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40"
              >
              </input>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Time</label>
              <input
                type="time"
                required
                value={formData.start_time}
                onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40"
              >
              </input>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Duration</label>
              <select
                value={formData.duration_minutes}
                onChange={(e) => setFormData({ ...formData, duration_minutes: Number(e.target.value) })}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/40"
              >
                <option value={30}>30 min</option>
                <option value={60}>60 min</option>
                <option value={90}>90 min</option>
                <option value={120}>2 hours</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Location / Room</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="e.g., North Central Wellness Centre Room 2"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Discussion Agenda / Notes</label>
            <textarea
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Key discussion points, safety checks, or transportation coordination..."
              className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/40 resize-none"
            />
          </div>

          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50"
            >
              {submitting ? 'Scheduling...' : 'Confirm Appointment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

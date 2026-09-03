import React, { useEffect, useState } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { reportingApi } from '@/api/reporting';
import {
  LayoutGrid,
  Plus,
  Trash2,
  GripVertical,
  Check,
  FolderOpen,
  Users,
  Inbox,
  Clock,
  FileX,
  AlertTriangle,
  ClipboardCheck,
  DollarSign,
  Briefcase,
  X,
} from 'lucide-react';

const STORAGE_KEY = 'crbcl_dashboard_widgets_v2';

const WIDGET_ICONS = {
  active_cases: FolderOpen,
  children_out_of_home: Users,
  new_intakes: Inbox,
  pending_approvals: Clock,
  cases_without_recent_notes: FileX,
  cases_over_12_months: AlertTriangle,
  audits_due: ClipboardCheck,
  financial_summary: DollarSign,
  my_assigned_cases: Briefcase,
};

const DEFAULT_FALLBACK_WIDGETS = [
  { widget_key: 'active_cases', title: 'Active Cases', category: 'OPERATIONAL', is_visible: true, position: 0, value: 0 },
  { widget_key: 'new_intakes', title: 'New Intakes (30d)', category: 'OPERATIONAL', is_visible: true, position: 1, value: 0 },
  { widget_key: 'children_out_of_home', title: 'Children Out of Home', category: 'OPERATIONAL', is_visible: true, position: 2, value: 0 },
  { widget_key: 'pending_approvals', title: 'Pending Approvals', category: 'GOVERNANCE', is_visible: true, position: 3, value: 0 },
  { widget_key: 'my_assigned_cases', title: 'My Assigned Caseload', category: 'MY_WORK', is_visible: true, position: 4, value: 0 },
  { widget_key: 'financial_summary', title: 'Financial Spend Summary', category: 'FINANCE', is_visible: false, position: 5, value: 0 },
  { widget_key: 'audits_due', title: 'QA Audits Due', category: 'QA', is_visible: false, position: 6, value: 0 },
  { widget_key: 'cases_without_recent_notes', title: 'Cases Without Notes (30d+)', category: 'QA', is_visible: false, position: 7, value: 0 },
  { widget_key: 'cases_over_12_months', title: 'Long-Term Open Cases (12m+)', category: 'QA', is_visible: false, position: 8, value: 0 },
];

function formatWidgetValue(val) {
  if (val === null || val === undefined) return '0';
  if (typeof val === 'number') return val.toLocaleString();
  if (typeof val === 'string') return val;
  if (typeof val === 'object') {
    if (val.approved_spend !== undefined) {
      const num = parseFloat(val.approved_spend) || 0;
      return `$${num.toLocaleString()}`;
    }
    if (val.count !== undefined) return String(val.count);
    if (val.value !== undefined) return String(val.value);
    return '0';
  }
  return String(val);
}

export default function CustomizableWidgetGrid() {
  const [loading, setLoading] = useState(false);
  const [showCustomizeModal, setShowCustomizeModal] = useState(false);
  
  // Initial load from local storage if available for instant rendering
  const [availableWidgets, setAvailableWidgets] = useState(DEFAULT_FALLBACK_WIDGETS);
  const [activeWidgets, setActiveWidgets] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch { /* ignore */ }
    return DEFAULT_FALLBACK_WIDGETS.filter(w => w.is_visible);
  });

  useEffect(() => {
    loadUserLayout();
  }, []);

  const loadUserLayout = async () => {
    try {
      const res = await reportingApi.getUserDashboardLayout();
      const rawLayout = res?.layout || res?.data?.layout || (Array.isArray(res) ? res : []);
      const metrics = res?.metrics || res?.data?.metrics || {};

      if (Array.isArray(rawLayout) && rawLayout.length > 0) {
        const fullWidgets = rawLayout.map((w, idx) => ({
          ...w,
          title: w.title || w.widget_key?.replace(/_/g, ' '),
          category: w.category || 'OPERATIONAL',
          position: w.position !== undefined ? w.position : idx,
          value: metrics[w.widget_key] !== undefined ? metrics[w.widget_key] : 0,
        }));
        setAvailableWidgets(fullWidgets);

        // Check if user has saved preferences in localStorage
        const localSaved = localStorage.getItem(STORAGE_KEY);
        if (localSaved) {
          try {
            const parsed = JSON.parse(localSaved);
            if (Array.isArray(parsed) && parsed.length > 0) {
              const activeWithMetrics = parsed.map(p => ({
                ...p,
                value: metrics[p.widget_key] !== undefined ? metrics[p.widget_key] : (p.value || 0),
              }));
              setActiveWidgets(activeWithMetrics);
              return;
            }
          } catch { /* ignore */ }
        }

        const active = fullWidgets
          .filter((w) => w.is_visible && w.has_permission !== false)
          .sort((a, b) => (a.position ?? 0) - (b.position ?? 0));
        
        const finalActive = active.length > 0 ? active : fullWidgets.slice(0, 5);
        setActiveWidgets(finalActive);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(finalActive));
        } catch { /* ignore */ }
      }
    } catch (err) {
      console.warn('Dashboard layout API fallback:', err);
    }
  };

  const handleDragEnd = (result) => {
    if (!result.destination) return;
    const items = Array.from(activeWidgets);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    const updated = items.map((item, idx) => ({
      ...item,
      position: idx,
    }));
    setActiveWidgets(updated);
    saveLayout(updated);
  };

  const saveLayout = async (widgetsList) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(widgetsList));
    } catch { /* ignore */ }

    try {
      const payload = widgetsList.map((w, idx) => ({
        widget_key: w.widget_key,
        position: idx,
        is_visible: true,
      }));
      await reportingApi.saveUserDashboardLayout(payload);
    } catch (err) {
      console.warn('Failed to persist dashboard layout to server:', err);
    }
  };

  const toggleWidgetVisibility = (widgetKey) => {
    const isCurrentlyActive = activeWidgets.some((w) => w.widget_key === widgetKey);
    let updated;
    if (isCurrentlyActive) {
      updated = activeWidgets.filter((w) => w.widget_key !== widgetKey);
    } else {
      const target = availableWidgets.find((w) => w.widget_key === widgetKey);
      if (target) {
        updated = [
          ...activeWidgets,
          {
            ...target,
            position: activeWidgets.length,
            is_visible: true,
          },
        ];
      } else {
        return;
      }
    }
    setActiveWidgets(updated);
    saveLayout(updated);
  };

  return (
    <div className="space-y-4">
      {/* Header bar for widget customization */}
      <div className="flex items-center justify-between bg-card border border-border rounded-xl p-3 px-4 shadow-sm">
        <div className="flex items-center gap-2">
          <LayoutGrid className="w-4 h-4 text-primary" />
          <span className="text-xs font-semibold text-foreground">Custom User Widget Grid</span>
          <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded font-medium">
            {activeWidgets.length} Active • Drag to Reorder
          </span>
        </div>
        <button
          onClick={() => setShowCustomizeModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" /> Customize Widgets
        </button>
      </div>

      {/* Drag and Drop Grid Context */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="user-widgets-droppable" direction="horizontal">
          {(provided) => (
            <div
              ref={provided.innerRef}
              {...provided.droppableProps}
              className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
            >
              {activeWidgets.map((widget, index) => {
                const Icon = WIDGET_ICONS[widget.widget_key] || FolderOpen;
                return (
                  <Draggable key={widget.widget_key} draggableId={widget.widget_key} index={index}>
                    {(dragProvided, snapshot) => (
                      <div
                        ref={dragProvided.innerRef}
                        {...dragProvided.draggableProps}
                        className={`p-4 bg-card border rounded-xl shadow-sm space-y-2 transition-all ${
                          snapshot.isDragging
                            ? 'border-primary ring-2 ring-primary/20 shadow-lg scale-105 z-50 bg-background'
                            : 'border-border hover:border-primary/50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div
                              {...dragProvided.dragHandleProps}
                              className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground p-0.5"
                            >
                              <GripVertical className="w-4 h-4" />
                            </div>
                            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider truncate max-w-[150px]">
                              {widget.title}
                            </span>
                          </div>
                          <button
                            onClick={() => toggleWidgetVisibility(widget.widget_key)}
                            className="text-muted-foreground hover:text-destructive p-1 transition-colors"
                            title="Remove Widget"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <div className="flex items-center justify-between pt-1">
                          <div className="text-2xl font-extrabold text-foreground">
                            {formatWidgetValue(widget.value)}
                          </div>
                          <div className="p-2 rounded-lg bg-primary/10 text-primary">
                            <Icon className="w-5 h-5" />
                          </div>
                        </div>
                      </div>
                    )}
                  </Draggable>
                );
              })}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>

      {/* Customize Widgets Modal */}
      {showCustomizeModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="text-lg font-bold text-foreground">Customize Dashboard Widgets</h3>
                <p className="text-xs text-muted-foreground">
                  Select which role-authorized widgets to display on your personal layout.
                </p>
              </div>
              <button
                onClick={() => setShowCustomizeModal(false)}
                className="p-1 text-muted-foreground hover:text-foreground rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {availableWidgets.map((w) => {
                const isSelected = activeWidgets.some((act) => act.widget_key === w.widget_key);
                const Icon = WIDGET_ICONS[w.widget_key] || FolderOpen;
                return (
                  <div
                    key={w.widget_key}
                    onClick={() => toggleWidgetVisibility(w.widget_key)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
                      isSelected
                        ? 'border-primary bg-primary/5 text-foreground'
                        : 'border-border text-muted-foreground hover:border-muted-foreground/30'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${isSelected ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-foreground">{w.title}</div>
                        <div className="text-[10px] text-muted-foreground uppercase">{w.category}</div>
                      </div>
                    </div>
                    {isSelected ? (
                      <span className="px-2.5 py-1 bg-primary text-primary-foreground rounded-full text-xs font-semibold flex items-center gap-1">
                        <Check className="w-3.5 h-3.5" /> Added
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 border border-border text-muted-foreground rounded-full text-xs font-medium hover:text-foreground">
                        + Add Widget
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="border-t border-border pt-4 text-right">
              <button
                onClick={() => setShowCustomizeModal(false)}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

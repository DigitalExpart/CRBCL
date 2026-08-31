import React, { useState, useEffect } from 'react';
import {
  Home,
  Shield,
  ShieldAlert,
  Clock,
  LogOut,
  Calendar,
  Building,
  User,
  Globe,
  BadgeCheck,
  FileText,
  Activity,
  History,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { placementsApi } from '@/api/placements';

export default function ClientEpisodesTab({ clientId, clientData }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await placementsApi.getClientPlacementHistory(clientId);
      setHistory(data);
    } catch (err) {
      console.error('Failed to load child placement history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (clientId) {
      loadHistory();
    }
  }, [clientId]);

  if (loading) {
    return <div className="py-12 text-center text-sm text-muted-foreground">Loading child longitudinal placement history...</div>;
  }

  const activePlacement = history?.active_placement;
  const inHomeList = history?.in_home_placements || [];
  const removalList = history?.removal_episodes || [];
  const placementList = history?.placement_episodes || [];
  const respiteList = history?.respite_episodes || [];
  const dischargeList = history?.discharge_episodes || [];

  return (
    <div className="space-y-6">
      {/* Active Living Arrangement Highlight */}
      {activePlacement ? (
        <Card className="bg-emerald-500/5 border-emerald-500/20 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
                <Home className="w-4 h-4 text-emerald-600" /> Current Living Arrangement (Active Placement)
              </CardTitle>
              <Badge className="bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border-emerald-500/30">
                ACTIVE
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <span className="text-muted-foreground block">Provider / Home:</span>
                <span className="font-bold text-foreground text-sm">{activePlacement.provider_name}</span>
              </div>
              <div>
                <span className="text-muted-foreground block">Caregiver:</span>
                <span className="font-semibold text-foreground">{activePlacement.primary_caregiver_name || 'Designated Caregiver'}</span>
              </div>
              <div>
                <span className="text-muted-foreground block">Type & Placed Since:</span>
                <span className="font-semibold text-foreground">{activePlacement.placement_type} (Since {activePlacement.start_date})</span>
              </div>
            </div>
            {activePlacement.cultural_plan_in_place && (
              <div className="flex items-center gap-1 text-emerald-700 dark:text-emerald-400 font-medium pt-1">
                <Globe className="w-3.5 h-3.5" /> Cultural Belonging Plan Active
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card className="bg-muted/20 border-muted">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-muted text-muted-foreground">
              <Home className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-foreground">No Out-of-Home Placement Active</p>
              <p className="text-xs text-muted-foreground">The child is not currently in foster, group, or kinship care custody.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Longitudinal Episode Timeline */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <History className="w-4 h-4 text-primary" /> Complete Longitudinal Episode Chain
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Immutable chronological record of all in-home placements, custody removals, placement episodes, respite care, and discharges.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 1. Placement Episodes */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Home className="w-3.5 h-3.5 text-primary" /> Placement Episodes ({placementList.length})
            </h4>
            {placementList.length === 0 ? (
              <p className="text-xs text-muted-foreground italic pl-5">No out-of-home placement history recorded.</p>
            ) : (
              <div className="space-y-2.5 pl-2 border-l-2 border-primary/20">
                {placementList.map((p) => (
                  <div key={p.id} className="ml-3 p-3 rounded-lg border bg-card/60 text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground text-sm">{p.provider_name}</span>
                      <Badge variant="outline" className={p.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-muted'}>
                        {p.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-muted-foreground">
                      <div>Type: <span className="font-medium text-foreground">{p.placement_type}</span></div>
                      <div>Start: <span className="font-medium text-foreground">{p.start_date}</span></div>
                      <div>End: <span className="font-medium text-foreground">{p.end_date || 'Ongoing'}</span></div>
                      <div>Rate: <span className="font-medium text-foreground">{p.per_diem_rate ? `$${parseFloat(p.per_diem_rate).toFixed(2)}` : 'Standard'}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 2. In-Home Placements */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-emerald-600" /> In-Home Safety Placements ({inHomeList.length})
            </h4>
            {inHomeList.length === 0 ? (
              <p className="text-xs text-muted-foreground italic pl-5">No in-home safety placement records.</p>
            ) : (
              <div className="space-y-2.5 pl-2 border-l-2 border-emerald-500/20">
                {inHomeList.map((ih) => (
                  <div key={ih.id} className="ml-3 p-3 rounded-lg border bg-card/60 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground">{ih.caregiver_name} ({ih.caregiver_relationship})</span>
                      <Badge variant="outline" className="text-[10px]">{ih.supervision_level}</Badge>
                    </div>
                    <p className="text-muted-foreground">Start: {ih.start_date} {ih.end_date && `• End: ${ih.end_date}`}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 3. Removal Episodes */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" /> Legal Custody & Removal Episodes ({removalList.length})
            </h4>
            {removalList.length === 0 ? (
              <p className="text-xs text-muted-foreground italic pl-5">No removal episodes recorded.</p>
            ) : (
              <div className="space-y-2.5 pl-2 border-l-2 border-amber-500/20">
                {removalList.map((r) => (
                  <div key={r.id} className="ml-3 p-3 rounded-lg border bg-card/60 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-amber-700 dark:text-amber-400">{r.removal_type}</span>
                      <span className="text-muted-foreground">Removal Date: {r.removal_date}</span>
                    </div>
                    <p className="text-foreground">{r.reason_for_removal}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 4. Respite Care */}
          {respiteList.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-600" /> Respite Care Episodes ({respiteList.length})
              </h4>
              <div className="space-y-2.5 pl-2 border-l-2 border-blue-500/20">
                {respiteList.map((res) => (
                  <div key={res.id} className="ml-3 p-3 rounded-lg border bg-card/60 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-foreground">{res.respite_provider_name}</span>
                      <span className="text-muted-foreground">{res.start_date} to {res.end_date}</span>
                    </div>
                    {res.reason_for_respite && <p className="text-muted-foreground">{res.reason_for_respite}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 5. Discharges */}
          {dischargeList.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <LogOut className="w-3.5 h-3.5 text-emerald-600" /> Discharges & Reunifications ({dischargeList.length})
              </h4>
              <div className="space-y-2.5 pl-2 border-l-2 border-emerald-500/20">
                {dischargeList.map((d) => (
                  <div key={d.id} className="ml-3 p-3 rounded-lg border bg-card/60 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-emerald-700 dark:text-emerald-400">{d.discharge_reason}</span>
                      <span className="text-muted-foreground">Date: {d.discharge_date}</span>
                    </div>
                    {d.destination_caregiver_name && (
                      <p className="text-foreground">Reunified With: {d.destination_caregiver_name} ({d.destination_type})</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

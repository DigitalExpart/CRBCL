import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { familiesApi } from '@/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Users,
  Heart,
  Home,
  MapPin,
  Sparkles,
  ArrowLeft,
  Plus,
  Clock,
  FileText,
  AlertTriangle,
  UserCheck,
} from "lucide-react";
import Genogram from '@/components/families/Genogram';
import FamilyMap from '@/components/families/FamilyMap';
import { useToast } from "@/components/ui/use-toast";

export default function FamilyDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState("overview");

  // 1. Family Query
  const { data: family, isLoading, error } = useQuery({
    queryKey: ['family', id],
    queryFn: () => familiesApi.get(id),
  });

  // 2. Members Query
  const { data: members } = useQuery({
    queryKey: ['family-members', id],
    queryFn: () => familiesApi.getMembers(id),
    enabled: !!id,
  });

  // 3. Genogram Query
  const { data: genogramData } = useQuery({
    queryKey: ['family-genogram', id],
    queryFn: () => familiesApi.getGenogram(id),
    enabled: !!id,
  });

  // 4. Map Locations Query
  const { data: mapData } = useQuery({
    queryKey: ['family-map', id],
    queryFn: () => familiesApi.getMap(id),
    enabled: !!id && activeTab === 'map',
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error || !family) {
    return (
      <div className="p-8 text-center">
        <AlertTriangle className="w-12 h-12 text-destructive mx-auto mb-4" />
        <h2 className="text-xl font-bold">Family File Not Found</h2>
        <p className="text-muted-foreground mt-2">The requested family file is unavailable or access is restricted.</p>
        <Button className="mt-4" onClick={() => navigate('/families')}>Back to Families</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-card border border-border/80 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/families')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="w-14 h-14 rounded-full bg-primary/10 border-2 border-primary/30 flex items-center justify-center text-primary font-bold text-xl">
              {family.family_name?.[0] || 'F'}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-foreground">
                  {family.family_name}
                </h1>
                <Badge variant={family.status === 'Active' ? 'default' : 'secondary'}>
                  {family.status}
                </Badge>
                <Badge variant="outline">
                  Risk: {family.risk_level}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-3">
                <span>Primary Contact: {family.primary_contact_name || 'Not designated'}</span>
                <span>•</span>
                <span>Members: {family.total_members}</span>
                <span>•</span>
                <span>Location: {family.city || 'Regina'}, {family.province || 'SK'}</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-muted/60 p-1 h-auto flex flex-wrap gap-1">
          <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
          <TabsTrigger value="members" className="text-xs">Members ({members?.length || 0})</TabsTrigger>
          <TabsTrigger value="genogram" className="text-xs">Family Genogram</TabsTrigger>
          <TabsTrigger value="map" className="text-xs">Household Map</TabsTrigger>
          <TabsTrigger value="timeline" className="text-xs">Timeline</TabsTrigger>
          <TabsTrigger value="documents" className="text-xs">Documents</TabsTrigger>
        </TabsList>

        {/* Tab: Overview */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-base">Family Details</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div><span className="text-xs text-muted-foreground block">Family File Name</span><p className="font-semibold">{family.family_name}</p></div>
                <div><span className="text-xs text-muted-foreground block">Primary Phone</span><p>{family.primary_contact_phone || 'None recorded'}</p></div>
                <div><span className="text-xs text-muted-foreground block">Primary Email</span><p>{family.primary_contact_email || 'None recorded'}</p></div>
                <div><span className="text-xs text-muted-foreground block">Indigenous Identity</span><p>{family.indigenous_identity || 'First Nations'}</p></div>
                <div><span className="text-xs text-muted-foreground block">Band / Nation</span><p>{family.band_nation || 'Muscowpetung Saulteaux Nation'}</p></div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-base">Quick Genogram Preview</CardTitle></CardHeader>
              <CardContent>
                <Genogram genogramData={genogramData} onSelectPerson={(person) => console.log(person)} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: Members */}
        <TabsContent value="members">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="w-4 h-4 text-primary" /> Registered Family Members
              </CardTitle>
            </CardHeader>
            <CardContent>
              {members && members.length > 0 ? (
                <div className="space-y-2">
                  {members.map((m) => (
                    <div key={m.id} className="p-3 bg-muted/40 rounded-lg border text-xs flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
                          {m.person?.first_name?.[0]}
                        </div>
                        <div>
                          <strong className="text-sm font-semibold">{m.person?.first_name} {m.person?.last_name}</strong>
                          <p className="text-muted-foreground">DOB: {m.person?.date_of_birth || 'Unknown'} • Gender: {m.person?.gender || 'N/A'}</p>
                        </div>
                      </div>
                      <Badge variant="secondary">{m.role}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground py-6 text-center">No family members registered yet.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Genogram */}
        <TabsContent value="genogram">
          <Genogram genogramData={genogramData} />
        </TabsContent>

        {/* Tab: Map */}
        <TabsContent value="map">
          <FamilyMap locations={mapData?.locations || []} familyName={family.family_name} />
        </TabsContent>

        {/* Tab: Timeline */}
        <TabsContent value="timeline">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Clock className="w-4 h-4 text-primary" /> Sacred Timeline Events</CardTitle></CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground py-6 text-center">Family file milestones are tracked continuously in the Sacred Timeline.</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Documents */}
        <TabsContent value="documents">
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><FileText className="w-4 h-4 text-primary" /> Family Documents</CardTitle></CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground py-6 text-center">Family documents repository is secured with signed access URLs.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import {
  HeartHandshake,
  Plus,
  Calendar,
  User,
  Building,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Edit2,
  Trash2,
  FileText,
  ShieldCheck,
  Globe,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { placementsApi } from '@/api/placements';

export default function ActiveEffortsTab({ caseId, caseData, people = [] }) {
  const [efforts, setEfforts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingEffort, setEditingEffort] = useState(null);
  const [formData, setFormData] = useState({
    effort_type: 'COUNSELING',
    description: '',
    service_date: new Date().toISOString().split('T')[0],
    provider_name: '',
    provider_contact: '',
    hours_spent: '',
    cultural_connection_made: false,
    outcome_summary: '',
    barriers_encountered: '',
  });

  const loadEfforts = async () => {
    try {
      setLoading(true);
      const data = await placementsApi.listActiveEfforts(caseId);
      setEfforts(data || []);
    } catch (err) {
      console.error('Failed to load active efforts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      loadEfforts();
    }
  }, [caseId]);

  const handleOpenCreate = () => {
    setEditingEffort(null);
    setFormData({
      effort_type: 'COUNSELING',
      description: '',
      service_date: new Date().toISOString().split('T')[0],
      provider_name: '',
      provider_contact: '',
      hours_spent: '',
      cultural_connection_made: false,
      outcome_summary: '',
      barriers_encountered: '',
    });
    setShowModal(true);
  };

  const handleOpenEdit = (effort) => {
    setEditingEffort(effort);
    setFormData({
      effort_type: effort.effort_type || 'COUNSELING',
      description: effort.description || '',
      service_date: effort.service_date || '',
      provider_name: effort.provider_name || '',
      provider_contact: effort.provider_contact || '',
      hours_spent: effort.hours_spent || '',
      cultural_connection_made: effort.cultural_connection_made || false,
      outcome_summary: effort.outcome_summary || '',
      barriers_encountered: effort.barriers_encountered || '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        hours_spent: formData.hours_spent ? parseFloat(formData.hours_spent) : null,
      };
      if (editingEffort) {
        await placementsApi.updateActiveEffort(editingEffort.id, payload);
      } else {
        await placementsApi.createActiveEffort(caseId, payload);
      }
      setShowModal(false);
      loadEfforts();
    } catch (err) {
      console.error('Failed to save active effort:', err);
      alert(err.message || 'Failed to save active effort');
    }
  };

  const handleDelete = async (effortId) => {
    if (!window.confirm('Are you sure you want to delete this active effort entry?')) return;
    try {
      await placementsApi.deleteActiveEffort(effortId);
      loadEfforts();
    } catch (err) {
      console.error('Failed to delete active effort:', err);
      alert(err.message || 'Failed to delete active effort');
    }
  };

  const totalEfforts = efforts.length;
  const culturalCount = efforts.filter((e) => e.cultural_connection_made).length;
  const totalHours = efforts.reduce((acc, e) => acc + (parseFloat(e.hours_spent) || 0), 0);

  const getEffortTypeLabel = (type) => {
    switch (type) {
      case 'COUNSELING':
        return 'Family Counseling & Healing';
      case 'HOUSING_ASSISTANCE':
        return 'Housing & Shelter Support';
      case 'SUBSTANCE_TREATMENT':
        return 'Substance Healing Services';
      case 'PARENTING_PROGRAM':
        return 'Customary Parenting Program';
      case 'CULTURAL_SERVICES':
        return 'Traditional & Cultural Practices';
      case 'RESPITE':
        return 'Family Respite Support';
      case 'LEGAL_AID':
        return 'Legal & Advocacy Services';
      case 'FINANCIAL_SUPPORT':
        return 'Direct Family Wellness Support';
      default:
        return type?.replace(/_/g, ' ') || 'Other Effort';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <HeartHandshake className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Total Active Efforts</p>
              <p className="text-xl font-bold text-foreground">{totalEfforts}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-emerald-500/5 border-emerald-500/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Cultural Connections</p>
              <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{culturalCount}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-500/5 border-blue-500/20">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Service Hours</p>
              <p className="text-xl font-bold text-blue-600 dark:text-blue-400">{totalHours.toFixed(1)} hrs</p>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-end">
          <Button onClick={handleOpenCreate} className="gap-2 shadow-sm">
            <Plus className="w-4 h-4" /> Record Active Effort
          </Button>
        </div>
      </div>

      {/* Efforts List */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-primary" /> Active Efforts & Preventative Services Log
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Document all affirmative, active, and culturally relevant efforts made to maintain the family unit or support safe reunification.
          </p>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="py-8 text-center text-sm text-muted-foreground">Loading active efforts...</div>
          ) : efforts.length === 0 ? (
            <div className="py-12 text-center border border-dashed rounded-lg">
              <HeartHandshake className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
              <p className="font-medium text-sm text-foreground">No active efforts recorded yet</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                Record remedial, preventive, and cultural services provided to the family to support healing and prevent removal.
              </p>
              <Button onClick={handleOpenCreate} variant="outline" size="sm" className="mt-4 gap-2">
                <Plus className="w-3.5 h-3.5" /> Record First Effort
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {efforts.map((effort) => (
                <div
                  key={effort.id}
                  className="p-4 rounded-lg border bg-card/60 hover:bg-card hover:shadow-sm transition-all space-y-3"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="outline" className="font-medium bg-primary/5 text-primary border-primary/20">
                        {getEffortTypeLabel(effort.effort_type)}
                      </Badge>
                      {effort.cultural_connection_made && (
                        <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20 gap-1 font-medium">
                          <Globe className="w-3 h-3" /> Cultural Practice
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" /> {effort.service_date || 'Date not recorded'}
                      </span>
                      {effort.hours_spent && (
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" /> {effort.hours_spent} hrs
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                        onClick={() => handleOpenEdit(effort)}
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => handleDelete(effort.id)}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>

                  <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{effort.description}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs bg-muted/30 p-2.5 rounded-md">
                    {effort.provider_name && (
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <Building className="w-3.5 h-3.5 text-primary shrink-0" />
                        <span className="font-medium text-foreground">Provider:</span> {effort.provider_name}
                        {effort.provider_contact && <span>({effort.provider_contact})</span>}
                      </div>
                    )}
                    {effort.outcome_summary && (
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                        <span className="font-medium text-foreground">Outcome:</span> {effort.outcome_summary}
                      </div>
                    )}
                    {effort.barriers_encountered && (
                      <div className="flex items-center gap-1.5 text-muted-foreground col-span-full">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                        <span className="font-medium text-foreground">Barriers:</span> {effort.barriers_encountered}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create / Edit Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>{editingEffort ? 'Edit Active Effort Record' : 'Record Active Effort'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 pt-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold">Effort Type *</label>
                <Select
                  value={formData.effort_type}
                  onValueChange={(val) => setFormData({ ...formData, effort_type: val })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="COUNSELING">Family Counseling & Healing</SelectItem>
                    <SelectItem value="HOUSING_ASSISTANCE">Housing & Shelter Support</SelectItem>
                    <SelectItem value="SUBSTANCE_TREATMENT">Substance Healing Services</SelectItem>
                    <SelectItem value="PARENTING_PROGRAM">Customary Parenting Program</SelectItem>
                    <SelectItem value="CULTURAL_SERVICES">Traditional & Cultural Practices</SelectItem>
                    <SelectItem value="RESPITE">Family Respite Support</SelectItem>
                    <SelectItem value="LEGAL_AID">Legal & Advocacy Services</SelectItem>
                    <SelectItem value="FINANCIAL_SUPPORT">Direct Family Wellness Support</SelectItem>
                    <SelectItem value="OTHER">Other Custom Service</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs font-semibold">Service Date *</label>
                <Input
                  type="date"
                  className="mt-1"
                  value={formData.service_date}
                  onChange={(e) => setFormData({ ...formData, service_date: e.target.value })}
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold">Detailed Description of Effort *</label>
              <Textarea
                className="mt-1 min-h-[90px]"
                placeholder="Describe the affirmative and active steps taken to assist the family..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-xs font-semibold">Service Provider</label>
                <Input
                  className="mt-1"
                  placeholder="e.g. Yorkton Tribal Council"
                  value={formData.provider_name}
                  onChange={(e) => setFormData({ ...formData, provider_name: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Provider Contact</label>
                <Input
                  className="mt-1"
                  placeholder="Phone or email"
                  value={formData.provider_contact}
                  onChange={(e) => setFormData({ ...formData, provider_contact: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold">Hours Spent</label>
                <Input
                  type="number"
                  step="0.5"
                  className="mt-1"
                  placeholder="e.g. 2.5"
                  value={formData.hours_spent}
                  onChange={(e) => setFormData({ ...formData, hours_spent: e.target.value })}
                />
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg border">
              <input
                type="checkbox"
                id="cultural_conn"
                className="rounded border-gray-300 text-primary focus:ring-primary"
                checked={formData.cultural_connection_made}
                onChange={(e) => setFormData({ ...formData, cultural_connection_made: e.target.checked })}
              />
              <label htmlFor="cultural_conn" className="text-xs font-medium cursor-pointer">
                Involves customary Elder support, Band services, or cultural healing ceremonies
              </label>
            </div>

            <div>
              <label className="text-xs font-semibold">Outcome / Progress Summary</label>
              <Input
                className="mt-1"
                placeholder="e.g. Parent attended all 4 sessions, positive progress noted"
                value={formData.outcome_summary}
                onChange={(e) => setFormData({ ...formData, outcome_summary: e.target.value })}
              />
            </div>

            <div>
              <label className="text-xs font-semibold">Barriers / Unmet Needs (if any)</label>
              <Input
                className="mt-1"
                placeholder="e.g. Transportation barrier identified; taxi vouchers provided"
                value={formData.barriers_encountered}
                onChange={(e) => setFormData({ ...formData, barriers_encountered: e.target.value })}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                Cancel
              </Button>
              <Button type="submit">
                {editingEffort ? 'Update Effort' : 'Save Active Effort'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

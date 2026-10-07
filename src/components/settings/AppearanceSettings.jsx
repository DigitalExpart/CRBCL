import React, { useState } from 'react';
import { useTheme, VALID_ACCENTS } from '@/context/ThemeContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/components/ui/use-toast';
import {
  Sun,
  Moon,
  Laptop,
  Check,
  RotateCcw,
  Sparkles,
  Eye,
  Sliders,
  Maximize2,
  Minimize2,
  ShieldCheck,
  Mic,
  FileText,
  Volume2,
} from 'lucide-react';

export default function AppearanceSettings() {
  const {
    preferences,
    isDark,
    isSyncing,
    updatePreferences,
    resetToDefaults,
  } = useTheme();

  const [saving, setSaving] = useState(false);

  const handleModeChange = async (mode) => {
    setSaving(true);
    await updatePreferences({ theme_mode: mode });
    setSaving(false);
    toast({
      title: 'Theme Mode Updated',
      description: `Switched display to ${mode === 'system' ? 'System Preference' : mode} mode.`,
    });
  };

  const handleAccentChange = async (accentKey) => {
    setSaving(true);
    await updatePreferences({ accent_theme: accentKey });
    setSaving(false);
    const accentObj = VALID_ACCENTS.find((a) => a.key === accentKey);
    toast({
      title: 'Accent Palette Updated',
      description: `Accent color changed to ${accentObj?.label || accentKey}.`,
    });
  };

  const handleDensityChange = async (density) => {
    setSaving(true);
    await updatePreferences({ density });
    setSaving(false);
    toast({
      title: 'Density Mode Updated',
      description: `Workspace layout set to ${density}.`,
    });
  };

  const handleRadiusChange = async (radius) => {
    setSaving(true);
    await updatePreferences({ card_radius: radius });
    setSaving(false);
  };

  const handleToggleContrast = async (checked) => {
    setSaving(true);
    await updatePreferences({ high_contrast: checked });
    setSaving(false);
  };

  const handleToggleMotion = async (checked) => {
    setSaving(true);
    await updatePreferences({ reduced_motion: checked });
    setSaving(false);
  };

  const handleLandingChange = async (e) => {
    const val = e.target.value;
    setSaving(true);
    await updatePreferences({ default_landing_dashboard: val === 'default' ? null : val });
    setSaving(false);
    toast({
      title: 'Default Landing Workspace Updated',
      description: val === 'default' ? 'Landing reset to agency default.' : `Preferred landing set to ${val}.`,
    });
  };

  const handleReset = async () => {
    setSaving(true);
    await resetToDefaults();
    setSaving(false);
    toast({
      title: 'Reset to CRBCL Defaults',
      description: 'Your workspace appearance has been restored to default CRBCL settings.',
    });
  };

  return (
    <div className="space-y-6">
      {/* Overview & Security Disclaimer */}
      <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-primary shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-semibold text-foreground">Personalized Workspace Appearance</p>
          <p className="text-muted-foreground text-xs mt-0.5 leading-relaxed">
            Personalization customizes colors, density, and layout for your individual account. In accordance with CRBCL privacy and security policy, visual preferences never alter your authorized roles, permissions, or access to sensitive family records.
          </p>
        </div>
      </div>

      {/* 1. Theme Mode */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sun className="w-4 h-4 text-primary" />
            Display Mode
          </CardTitle>
          <CardDescription>
            Choose between Light, Dark, or automatically match your operating system theme.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { key: 'light', label: 'Light', desc: 'Clean, high-clarity background', icon: Sun },
              { key: 'dark', label: 'Dark', desc: 'Reduced glare for low light', icon: Moon },
              { key: 'system', label: 'System Sync', desc: 'Matches device preference', icon: Laptop },
            ].map(({ key, label, desc, icon: Icon }) => {
              const active = preferences.theme_mode === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => handleModeChange(key)}
                  className={`flex flex-col items-start p-4 rounded-lg border-2 text-left transition-all ${
                    active
                      ? 'border-primary bg-primary/5 shadow-sm'
                      : 'border-border/60 hover:border-border hover:bg-muted/40'
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-2">
                    <Icon className={`w-5 h-5 ${active ? 'text-primary' : 'text-muted-foreground'}`} />
                    {active && (
                      <span className="flex items-center text-[11px] font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                        <Check className="w-3 h-3 mr-1" /> Active
                      </span>
                    )}
                  </div>
                  <span className="font-medium text-sm text-foreground">{label}</span>
                  <span className="text-xs text-muted-foreground mt-0.5">{desc}</span>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 2. Controlled Accent Palette */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            Accent Palette
          </CardTitle>
          <CardDescription>
            Select from the accessible, culturally inspired lodge color palettes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {VALID_ACCENTS.map(({ key, label, color }) => {
              const currentKey = preferences.accent_theme ? preferences.accent_theme.replace('_', '-') : 'crbcl';
              const active = currentKey === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => handleAccentChange(key)}
                  className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-all text-left ${
                    active
                      ? 'border-primary bg-primary/5 shadow-sm'
                      : 'border-border/60 hover:border-border hover:bg-muted/30'
                  }`}
                >
                  <span
                    className="w-6 h-6 rounded-full shrink-0 shadow-inner flex items-center justify-center text-white"
                    style={{ backgroundColor: color }}
                  >
                    {active && <Check className="w-3.5 h-3.5" />}
                  </span>
                  <div className="truncate min-w-0">
                    <span className="text-xs font-semibold text-foreground block truncate">{label}</span>
                    <span className="text-[10px] text-muted-foreground capitalize">{key}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 3. Workspace Layout & Density */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sliders className="w-4 h-4 text-primary" />
            Density & Visual Comfort
          </CardTitle>
          <CardDescription>
            Tailor padding, table height, and card style to your workflow pace.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Density Selection */}
          <div>
            <Label className="text-sm font-semibold mb-2 block">Interface Density</Label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                {
                  key: 'comfortable',
                  label: 'Comfortable Density',
                  desc: 'Generous padding and breathing room for relaxed reading',
                  icon: Maximize2,
                },
                {
                  key: 'compact',
                  label: 'Compact Density',
                  desc: 'Tight table rows and card spacing for data-heavy workflows',
                  icon: Minimize2,
                },
              ].map(({ key, label, desc, icon: Icon }) => {
                const active = preferences.density === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => handleDensityChange(key)}
                    className={`flex items-start gap-3 p-3.5 rounded-lg border-2 text-left transition-all ${
                      active
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-border/60 hover:border-border hover:bg-muted/30'
                    }`}
                  >
                    <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${active ? 'text-primary' : 'text-muted-foreground'}`} />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground">{label}</span>
                        {active && <Check className="w-3.5 h-3.5 text-primary" />}
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Card Corner Style */}
          <div className="pt-2 border-t border-border">
            <Label className="text-sm font-semibold mb-2 block">Corner Radius Style</Label>
            <div className="grid grid-cols-2 gap-3 sm:w-80">
              {[
                { key: 'rounded', label: 'Rounded (0.625rem)', sampleClass: 'rounded-xl' },
                { key: 'subtle', label: 'Subtle (0.25rem)', sampleClass: 'rounded-sm' },
              ].map(({ key, label, sampleClass }) => {
                const active = preferences.card_radius === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => handleRadiusChange(key)}
                    className={`p-3 border-2 text-left transition-all ${sampleClass} ${
                      active ? 'border-primary bg-primary/5 font-semibold text-primary' : 'border-border text-foreground hover:bg-muted/40'
                    }`}
                  >
                    <span className="text-xs block">{label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Preferred Landing Dashboard */}
          <div className="pt-2 border-t border-border">
            <Label htmlFor="landing-select" className="text-sm font-semibold mb-1 block">
              Default Landing Workspace
            </Label>
            <p className="text-xs text-muted-foreground mb-2">
              If your staff account has access to multiple areas, choose which workspace to open by default upon logging in.
            </p>
            <select
              id="landing-select"
              value={preferences.default_landing_dashboard || 'default'}
              onChange={handleLandingChange}
              className="w-full sm:w-80 h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="default">CRBCL Standard Role Workspace (Default)</option>
              <option value="/cases">Assigned Cases Directory</option>
              <option value="/intakes">Intake & Referral Queue</option>
              <option value="/schedule">My Personal Schedule</option>
              <option value="/notifications">Notifications Hub</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* 4. Accessibility Options */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Eye className="w-4 h-4 text-primary" />
            Accessibility & Motion
          </CardTitle>
          <CardDescription>
            Enhanced visual contrast and motion reduction for assistive comfort.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-1">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">High-Contrast Mode</Label>
              <p className="text-xs text-muted-foreground">
                Enhances border definition and contrast ratios across cards, tables, and buttons.
              </p>
            </div>
            <Switch
              checked={preferences.high_contrast}
              onCheckedChange={handleToggleContrast}
            />
          </div>

          <div className="flex items-center justify-between py-1 border-t border-border pt-3">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Reduce Animations & Motion</Label>
              <p className="text-xs text-muted-foreground">
                Minimizes interface transitions, sliding effects, and background motion.
              </p>
            </div>
            <Switch
              checked={preferences.reduced_motion}
              onCheckedChange={handleToggleMotion}
            />
          </div>
        </CardContent>
      </Card>

      {/* 5. Live Interactive Theme Preview */}
      <Card className="border-primary/30">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              Live Preview
            </CardTitle>
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 text-xs">
              Theme: {preferences.accent_theme.toUpperCase()} • {isDark ? 'DARK' : 'LIGHT'}
            </Badge>
          </div>
          <CardDescription>
            Simulated demonstration of how your active accent palette, density, and speech dictation controls render.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-border p-4 bg-card shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <span className="font-semibold text-sm text-foreground">Case Note CN-2026-084</span>
                <Badge variant="outline" className="text-[10px] bg-success/10 text-success border-success/30">
                  Signed
                </Badge>
              </div>
              <span className="text-xs text-muted-foreground">Today at 10:45 AM</span>
            </div>

            <p className="text-xs text-foreground/80 leading-relaxed">
              Met with family for cultural ceremony preparation. Caseworker documented progress on reunification goals and scheduled wellness follow-up.
            </p>

            {/* Simulated Speech-to-Text Control inside Theme */}
            <div className="rounded-md border border-border/80 bg-muted/40 p-2.5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
                  <Mic className="w-3.5 h-3.5" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-foreground">Speech-to-Text Input Aid</p>
                  <p className="text-[10px] text-muted-foreground">Whisper self-hosted speech dictation ready</p>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <Button size="sm" variant="outline" className="h-7 text-xs px-2.5">
                  <Volume2 className="w-3 h-3 mr-1" /> Test Mic
                </Button>
                <Button size="sm" className="h-7 text-xs px-2.5 bg-primary text-primary-foreground">
                  Dictate Note
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex items-center justify-between border-t border-border/60 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleReset}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            Reset to CRBCL Defaults
          </Button>

          <span className="text-xs text-muted-foreground">
            {saving || isSyncing ? 'Synchronizing with cloud...' : 'All preferences saved'}
          </span>
        </CardFooter>
      </Card>
    </div>
  );
}

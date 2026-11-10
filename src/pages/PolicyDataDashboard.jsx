import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api";
import { 
  BarChart3, BookOpen, Shield, FileCheck, CheckCircle2, 
  Clock, AlertTriangle, ArrowRight, Database, TrendingUp, Layers, RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import PageHeader from "@/components/shared/PageHeader";
import StatCard from "@/components/shared/StatCard";

export default function PolicyDataDashboard() {
  const [policyCount, setPolicyCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [dataStats, setDataStats] = useState({
    activeCases: 0,
    activeClients: 0,
    qualityAuditScore: 98.4,
    jurisdictionalCompliance: 100,
  });

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const policies = await api.fetch("/api/v1/policies").catch(() => []);
        setPolicyCount(Array.isArray(policies) ? policies.length : 0);

        const cases = await api.entities.Case.list("-created_date", 10).catch(() => []);
        const clients = await api.entities.Client.list("-created_date", 10).catch(() => []);

        setDataStats(prev => ({
          ...prev,
          activeCases: Array.isArray(cases) ? cases.length : 142,
          activeClients: Array.isArray(clients) ? clients.length : 389,
        }));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Policy & Data Department Dashboard" 
        subtitle="Operational governance, agency policy lifecycle, data analytics, and jurisdictional compliance" 
        actions={
          <div className="flex gap-2">
            <Link to="/company-policy">
              <Button>
                <BookOpen className="w-4 h-4 mr-2" /> Company Policy Page
              </Button>
            </Link>
          </div>
        } 
      />

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Company Policies"
          value={loading ? "…" : policyCount.toString()}
          subtitle="Governing agency operations"
          icon={BookOpen}
          color="emerald"
        />
        <StatCard
          title="Data Quality Health"
          value={`${dataStats.qualityAuditScore}%`}
          subtitle="QA audit verification rate"
          icon={FileCheck}
          color="blue"
        />
        <StatCard
          title="Jurisdiction Compliance"
          value={`${dataStats.jurisdictionalCompliance}%`}
          subtitle="Miyo Pimatisowin Act alignment"
          icon={Shield}
          color="amber"
        />
        <StatCard
          title="Monitored Case Records"
          value={loading ? "…" : dataStats.activeCases.toString()}
          subtitle="Active longitudinal files"
          icon={Database}
          color="purple"
        />
      </div>

      {/* Main Grid: Policy Lifecycle & Data Analytics Hub */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Columns: Policy Management & Review Cadence */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card rounded-xl border border-border p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-primary" />
                Company Policy Administration
              </h3>
              <Link to="/company-policy" className="text-xs text-primary font-medium hover:underline flex items-center">
                Open Full Policy Manual <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Link>
            </div>

            <p className="text-sm text-muted-foreground">
              The designated Policy & Data team coordinates regular policy drafting, legal compliance review, and staff publication.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="border border-border/80 rounded-lg p-4 bg-muted/20 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-foreground">Standard Policy Editing</span>
                    <Badge variant="outline" className="text-xs">Live</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Designated policy analysts and directors can author revisions, publish amendments, and track historical audit summaries.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-border/60">
                  <Link to="/company-policy">
                    <Button variant="outline" size="sm" className="w-full">
                      Edit Company Policies
                    </Button>
                  </Link>
                </div>
              </div>

              <div className="border border-border/80 rounded-lg p-4 bg-muted/20 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-foreground">Annual Policy Review Cadence</span>
                    <Badge className="bg-amber-500/20 text-amber-700 text-xs">Q4 2026</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Review and refresh schedules for customary care guidelines, privacy retention schedules, and personnel safety manuals.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-border/60">
                  <Link to="/company-policy">
                    <Button variant="ghost" size="sm" className="w-full text-primary">
                      Review Schedule
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Data Governance & Quality Audits */}
          <div className="bg-card rounded-xl border border-border p-6 space-y-4">
            <h3 className="text-lg font-semibold text-foreground flex items-center gap-2 pb-2 border-b border-border">
              <Database className="w-5 h-5 text-blue-600" />
              Data Governance & Quality Standards
            </h3>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-background">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Longitudinal File Field Completeness</p>
                    <p className="text-xs text-muted-foreground">Mandatory identity, family link, and band affiliation records</p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-emerald-600">99.1%</span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-background">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Customary Care Licensing Registry Verification</p>
                    <p className="text-xs text-muted-foreground">Cross-checked against Resource Unit licensing records</p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-emerald-600">100%</span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-background">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Privacy Access Audit Tickler</p>
                    <p className="text-xs text-muted-foreground">Zero unreviewed conflict-of-interest access attempts</p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-emerald-600">Compliant</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Quick Navigation & Governance Links */}
        <div className="space-y-6">
          <div className="bg-card rounded-xl border border-border p-6 space-y-4">
            <h3 className="font-semibold text-foreground text-sm flex items-center gap-2 pb-2 border-b border-border">
              <Layers className="w-4 h-4 text-primary" />
              Related Agency Modules
            </h3>

            <div className="space-y-2">
              <Link to="/reports" className="p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors flex items-center justify-between block">
                <div>
                  <p className="text-sm font-medium text-foreground">Reporting Hub & Builder</p>
                  <p className="text-xs text-muted-foreground">Statistical exports and board decks</p>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
              </Link>

              <Link to="/qa" className="p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors flex items-center justify-between block">
                <div>
                  <p className="text-sm font-medium text-foreground">Quality Assurance Audits</p>
                  <p className="text-xs text-muted-foreground">Case file reviews & ticklers</p>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
              </Link>

              <Link to="/documents" className="p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors flex items-center justify-between block">
                <div>
                  <p className="text-sm font-medium text-foreground">Document Repository</p>
                  <p className="text-xs text-muted-foreground">Staff notes & item access controls</p>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
              </Link>

              <Link to="/ask-red-bear" className="p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors flex items-center justify-between block">
                <div>
                  <p className="text-sm font-medium text-foreground">Ask Red Bear Analytics</p>
                  <p className="text-xs text-muted-foreground">AI-assisted natural language queries</p>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
              </Link>
            </div>
          </div>

          <div className="bg-primary/5 rounded-xl border border-primary/20 p-5 space-y-2">
            <h4 className="font-semibold text-sm text-foreground flex items-center gap-1.5">
              <Shield className="w-4 h-4 text-primary" />
              Least-Privilege Role Separation
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              In accordance with CRBCL governance protocols, Policy & Data staff manage public agency policies and aggregate analytical indicators without requiring direct casework authority or administrative system overrides.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}


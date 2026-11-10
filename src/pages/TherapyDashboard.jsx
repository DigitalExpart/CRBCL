import React from "react";
import { Link } from "react-router-dom";
import {
  Heart,
  Users,
  BookOpen,
  ArrowLeft,
  AlertTriangle,
  Clock,
  FileText,
  Lock,
  Layers,
} from "lucide-react";
import PageHeader from "@/components/shared/PageHeader";
import StatCard from "@/components/shared/StatCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";

export default function TherapyDashboard() {
  return (
    <div className="space-y-6">
      {/* Header with Navigation Actions */}
      <PageHeader
        title="Therapy Department Dashboard"
        subtitle="Preliminary Department Shell"
        actions={
          <div className="flex items-center gap-2">
            <Link to="/teams">
              <Button variant="outline" size="sm">
                <ArrowLeft className="w-4 h-4 mr-1.5" />
                Team Dashboards
              </Button>
            </Link>
            <Link to="/company-policy">
              <Button variant="ghost" size="sm">
                <BookOpen className="w-4 h-4 mr-1.5" />
                Agency Policies
              </Button>
            </Link>
          </div>
        }
      />

      {/* Advisory Alert Banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 sm:p-5 flex items-start gap-4 text-foreground">
        <div className="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-700 dark:text-amber-400 flex items-center justify-center flex-shrink-0 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-sm sm:text-base text-amber-900 dark:text-amber-200">
              Preliminary Department Shell
            </h3>
            <Badge
              variant="outline"
              className="border-amber-500/40 text-amber-800 dark:text-amber-300 text-[11px] font-medium"
            >
              Requirements Pending Confirmation
            </Badge>
          </div>
          <p className="text-sm text-amber-800 dark:text-amber-300 leading-relaxed font-medium">
            This is a preliminary department dashboard shell. Department-specific workflows, information, reporting, and access requirements are pending confirmation.
          </p>
          <p className="text-xs text-muted-foreground pt-1">
            No department-specific records, workflows, forms, or staff accounts are configured on this shell.
          </p>
        </div>
      </div>

      {/* Status & Governance KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Department Status"
          value="Preliminary Shell"
          subtitle="Configuration pending confirmation"
          icon={Heart}
          color="accent"
        />
        <StatCard
          title="Department Workflows"
          value="Pending Review"
          subtitle="Requirements pending confirmation"
          icon={Clock}
          color="warning"
        />
        <StatCard
          title="Staff Roster"
          value="Unassigned"
          subtitle="Zero accounts provisioned"
          icon={Users}
          color="purple"
        />
        <StatCard
          title="Policy Governance"
          value="Agency Standards"
          subtitle="CRBCL operational policies apply"
          icon={BookOpen}
          color="success"
        />
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Department Overview & Workflows */}
        <div className="lg:col-span-2 space-y-6">
          {/* Department Overview */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-heading flex items-center gap-2">
                  <Heart className="w-5 h-5 text-primary" />
                  Department Overview
                </CardTitle>
                <Badge variant="secondary" className="text-xs">Preliminary Shell</Badge>
              </div>
              <CardDescription>
                Architectural shell for the Therapy department
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-muted-foreground leading-relaxed">
              <p>
                This is a preliminary department dashboard shell. Department-specific workflows, information, reporting, and access requirements are pending confirmation.
              </p>
              <div className="p-4 bg-muted/40 rounded-lg border border-border space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-foreground flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-primary" />
                  Configuration Notice
                </p>
                <p className="text-xs text-muted-foreground">
                  This is a preliminary department dashboard shell. Department-specific workflows, information, reporting, and access requirements are pending confirmation.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Operational Workflows Placeholder */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-heading flex items-center gap-2">
                <Layers className="w-5 h-5 text-primary" />
                Department Workflows & Operations
              </CardTitle>
              <CardDescription>
                Department operational workflows and reporting
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border border-dashed border-border rounded-xl p-8 text-center space-y-3 bg-muted/20">
                <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto text-muted-foreground">
                  <Clock className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-semibold text-foreground text-sm sm:text-base">
                    Workflow Configuration Pending Review
                  </h4>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto">
                    This is a preliminary department dashboard shell. Department-specific workflows, information, reporting, and access requirements are pending confirmation.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Governance & Quick Links */}
        <div className="space-y-6">
          {/* Governance & Access Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <Lock className="w-4 h-4 text-primary" />
                Access & Safeguards
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-muted-foreground leading-relaxed">
              <div className="p-3 bg-muted/50 rounded-lg space-y-1">
                <span className="font-semibold text-foreground block">Authentication Requirement</span>
                <span>
                  Access to this route is restricted to authenticated CRBCL personnel. No client information or records are exposed through this shell.
                </span>
              </div>
              <div className="p-3 bg-muted/50 rounded-lg space-y-1">
                <span className="font-semibold text-foreground block">Role & Account Status</span>
                <span>
                  No department-specific staff accounts, role assignments, or custom permissions have been configured.
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Quick Resources */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                Authorized Resources
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link
                to="/company-policy"
                className="flex items-center justify-between p-2.5 rounded-lg border border-border hover:bg-muted/50 transition-colors text-xs font-medium text-foreground group"
              >
                <span className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  Agency Operational Policies
                </span>
                <span className="text-[10px] text-muted-foreground uppercase">View</span>
              </Link>
              <Link
                to="/teams"
                className="flex items-center justify-between p-2.5 rounded-lg border border-border hover:bg-muted/50 transition-colors text-xs font-medium text-foreground group"
              >
                <span className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  All Team Dashboards
                </span>
                <span className="text-[10px] text-muted-foreground uppercase">Browse</span>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

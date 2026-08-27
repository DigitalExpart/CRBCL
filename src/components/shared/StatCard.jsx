import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export default function StatCard({ title, value, change, changeLabel, icon: Icon, color = "primary" }) {
  const colorMap = {
    primary: "bg-primary/10 text-primary",
    accent: "bg-accent/10 text-accent",
    success: "bg-emerald-100 text-emerald-700",
    warning: "bg-amber-100 text-amber-700",
    destructive: "bg-red-100 text-red-700",
    blue: "bg-blue-100 text-blue-700",
    purple: "bg-purple-100 text-purple-700",
  };

  const isPositive = change > 0;
  const isNegative = change < 0;

  return (
    <div className="bg-card rounded-xl border border-border p-5 hover:shadow-md transition-shadow duration-300">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
          {Icon && <Icon className="w-5 h-5" />}
        </div>
        {change !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${
            isPositive ? "bg-emerald-50 text-emerald-600" :
            isNegative ? "bg-red-50 text-red-600" :
            "bg-muted text-muted-foreground"
          }`}>
            {isPositive ? <TrendingUp className="w-3 h-3" /> : isNegative ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
            <span>{Math.abs(change)}%</span>
          </div>
        )}
      </div>
      <div className="space-y-1">
        <p className="text-2xl font-bold font-heading text-foreground">{value}</p>
        <p className="text-xs text-muted-foreground">{title}</p>
        {changeLabel && <p className="text-[10px] text-muted-foreground/70">{changeLabel}</p>}
      </div>
    </div>
  );
}
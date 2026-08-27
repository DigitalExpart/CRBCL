import React from "react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { ChevronDown, Check, LayoutGrid } from "lucide-react";
import { TEAMS } from "@/pages/Teams";
import { cn } from "@/lib/utils";

/**
 * Dropdown multi-select for team dashboard access.
 * - "All Teams" option selects ["all"]
 * - Individual teams add/remove their ID
 * @param {string[]} value - array of team IDs (strings) or ["all"]
 * @param {(val: string[]) => void} onChange
 */
export default function TeamAccessPicker({ value = [], onChange, disabled }) {
  const isAll = value.includes("all");
  const selectedCount = isAll ? TEAMS.length : value.length;

  const label = isAll
    ? "All Teams"
    : selectedCount === 0
      ? "Select teams..."
      : selectedCount === 1
        ? TEAMS.find((t) => String(t.id) === value[0])?.name || "1 team"
        : `${selectedCount} teams`;

  const toggleAll = () => {
    onChange(isAll ? [] : ["all"]);
  };

  const toggleTeam = (teamId) => {
    const idStr = String(teamId);
    if (isAll) {
      const allIds = TEAMS.map((t) => String(t.id));
      onChange(allIds.filter((id) => id !== idStr));
    } else {
      const next = value.includes(idStr)
        ? value.filter((v) => v !== idStr)
        : [...value, idStr];
      onChange(next);
    }
  };

  return (
    <div className="space-y-1.5">
      <Popover>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            role="combobox"
            disabled={disabled}
            className="w-full justify-between font-normal"
          >
            <span className="flex items-center gap-2 truncate">
              <LayoutGrid className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <span className={cn(selectedCount === 0 && "text-muted-foreground")}>{label}</span>
            </span>
            <ChevronDown className="w-4 h-4 opacity-50 flex-shrink-0" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[320px] p-0" align="start">
          <div className="max-h-64 overflow-y-auto scrollbar-thin">
            <button
              type="button"
              onClick={toggleAll}
              className={cn(
                "flex items-center gap-3 w-full px-3 py-2.5 text-left text-sm border-b border-border transition-colors",
                isAll ? "bg-primary/10 font-medium" : "hover:bg-muted/50"
              )}
            >
              <Checkbox checked={isAll} className="pointer-events-none" />
              <span>All Teams</span>
              {isAll && <Check className="w-4 h-4 ml-auto text-primary" />}
            </button>
            {TEAMS.map((t) => {
              const selected = isAll || value.includes(String(t.id));
              return (
              <button
                key={t.id}
                type="button"
                disabled={isAll}
                onClick={() => toggleTeam(t.id)}
                className={cn(
                  "flex items-center gap-3 w-full px-3 py-2.5 text-left text-sm transition-colors",
                  selected ? "bg-primary/10" : "hover:bg-muted/50",
                  isAll && "opacity-50 cursor-not-allowed"
                )}
              >
                <Checkbox checked={selected} className="pointer-events-none" />
                <span className="truncate">{t.name}</span>
              </button>
              );
            })}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
import React, { useState, useEffect } from "react";
import { casesApi } from "@/api/cases";
import { Link } from "react-router-dom";
import { ArrowRightLeft, Clock, CheckCircle2, XCircle, ArrowRight, ShieldAlert } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function TransferQueueWidget() {
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadPending = async () => {
    try {
      const data = await casesApi.getPendingTransfers();
      setTransfers(data || []);
    } catch (e) {
      console.warn("Could not load pending transfers:", e);
      setTransfers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPending();
  }, []);

  if (loading) {
    return null;
  }

  if (transfers.length === 0) {
    return null;
  }

  return (
    <Card className="border-amber-500/30 bg-amber-500/5 dark:bg-amber-950/10">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <ArrowRightLeft className="w-5 h-5" />
          </div>
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              Supervisor Transfer Queue
              <Badge variant="outline" className="bg-amber-500/20 text-amber-700 dark:text-amber-300 border-amber-500/30">
                {transfers.length} Pending Approval
              </Badge>
            </CardTitle>
            <p className="text-xs text-muted-foreground">Case and child transfers awaiting supervisor review</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="divide-y divide-border/60">
          {transfers.slice(0, 4).map((t) => (
            <div key={t.id} className="py-2.5 flex items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">
                    {t.case_number || "Case Transfer"}
                  </span>
                  {t.child_name && (
                    <span className="text-xs text-muted-foreground">
                      (Child: {t.child_name})
                    </span>
                  )}
                  <Badge variant="secondary" className="text-xs">
                    {t.source_team_name || "Current Team"} → {t.destination_team_name || "New Team"}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-1">
                  Reason: {t.reason}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Link to={`/cases/${t.case_id}?tab=transfers`}>
                  <Button size="sm" variant="outline" className="h-8 text-xs">
                    Review Transfer <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

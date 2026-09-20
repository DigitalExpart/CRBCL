import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Inbox, Plus, ChevronRight
} from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function IntakeWidgets() {
  const navigate = useNavigate();
  const [recentIntakes, setRecentIntakes] = useState([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const [authData] = useState(() => {
    try {
      const u = JSON.parse(localStorage.getItem("crbcl_current_user") || "{}");
      const r = (Array.isArray(u?.roles) ? u.roles : (u?.role ? [u.role] : []))
        .map(x => String(typeof x === "string" ? x : (x?.key || x?.name || "")).toLowerCase().trim());
      const perms = (Array.isArray(u?.permissions) ? u.permissions : [])
        .map(p => String(p).toLowerCase().trim());

      const isBoard = r.includes("board_member");
      const isPureItAdmin = r.includes("it_admin") && !r.some(role => ["front_desk", "navigator", "supervisor", "director_manager", "executive_director", "ceo", "caseworker"].includes(role));
      const hasIntakeAccess = perms.includes("intake.read") || r.some(role => ["front_desk", "navigator", "supervisor", "director_manager", "executive_director", "ceo"].includes(role));

      const canCreate =
        r.some(role => ["front_desk", "navigator"].includes(role)) &&
        !r.some(role => ["supervisor", "director_manager", "executive_director", "ceo", "board_member", "it_admin", "caseworker"].includes(role));

      const canApprove = perms.includes("intake.approve") || r.some(role => ["supervisor", "director_manager", "executive_director", "ceo"].includes(role));

      return {
        isVisible: !isBoard && !isPureItAdmin && hasIntakeAccess,
        canCreate,
        canApprove,
      };
    } catch {
      return { isVisible: false, canCreate: false, canApprove: false };
    }
  });

  useEffect(() => {
    if (!authData.isVisible) {
      setLoading(false);
      return;
    }

    const promises = [referralsApi.list({ page: 1, page_size: 5 })];
    if (authData.canApprove) {
      promises.push(referralsApi.getApprovalQueue({ page: 1, page_size: 1 }));
    }

    Promise.all(promises)
      .then(([listRes, queueRes]) => {
        setRecentIntakes(listRes?.items || []);
        if (queueRes) {
          setPendingCount(queueRes?.total || 0);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [authData.isVisible, authData.canApprove]);

  if (!authData.isVisible) {
    return null;
  }

  const canCreateIntake = authData.canCreate;

  return (
    <Card className="border shadow-sm">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <Inbox className="w-4 h-4 text-primary" />
            <span>Front-Door Intake & Referrals</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Recent screening intakes and supervisory approval state
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          {pendingCount > 0 && (
            <Link to="/intake/approvals">
              <Badge className="bg-purple-600 hover:bg-purple-700 text-white text-xs cursor-pointer">
                {pendingCount} Pending Supervisor
              </Badge>
            </Link>
          )}
          {canCreateIntake && (
            <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => navigate("/intake/new")}>
              <Plus className="w-3 h-3 mr-1" />
              <span>New Intake</span>
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y text-xs">
          {loading ? (
            <div className="p-6 text-center text-muted-foreground">Loading recent intakes...</div>
          ) : recentIntakes.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground italic">No intake referrals logged yet.</div>
          ) : (
            recentIntakes.map((ref) => (
              <div
                key={ref.id}
                onClick={() => navigate(`/intake/${ref.id}`)}
                className="p-3.5 flex items-center justify-between hover:bg-muted/20 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono font-bold text-primary">{ref.referral_number}</span>
                  <div>
                    <span className="font-medium text-foreground block capitalize truncate max-w-xs">
                      {ref.primary_concern?.replace(/_/g, ' ') || ref.summary || "General Concern"}
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      {ref.community || "Unspecified"} • {ref.received_date}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={ref.priority === "Crisis" ? "destructive" : "secondary"} className="text-[10px]">
                    {ref.priority}
                  </Badge>
                  <Badge variant="outline" className="text-[10px] capitalize">
                    {ref.status.replace(/_/g, ' ')}
                  </Badge>
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                </div>
              </div>
            ))
          )}
        </div>

        <div className="p-2 border-t bg-muted/10 text-center">
          <Link to="/intake" className="text-xs font-semibold text-primary hover:underline">
            View All Intake Referrals →
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

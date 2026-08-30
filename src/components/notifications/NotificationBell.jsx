import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Bell, Clock, AlertTriangle, CheckCircle, ChevronRight } from "lucide-react";
import { referralsApi } from "@/api/referrals";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function NotificationBell() {
  const [pendingItems, setPendingItems] = useState([]);
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    referralsApi.getApprovalQueue({ page: 1, page_size: 5 })
      .then(res => {
        setPendingItems(res.items || []);
        setPendingCount(res.total || 0);
      })
      .catch(() => {});
  }, []);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative h-9 w-9">
          <Bell className="w-5 h-5 text-muted-foreground" />
          {pendingCount > 0 && (
            <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-purple-600 text-[10px] font-bold text-white">
              {pendingCount > 9 ? "9+" : pendingCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0 shadow-lg">
        <DropdownMenuLabel className="p-3 bg-muted/30 border-b flex items-center justify-between">
          <span className="text-xs font-bold text-foreground">Supervisory Approvals</span>
          {pendingCount > 0 && (
            <Badge className="bg-purple-600 text-white text-[10px]">{pendingCount} Pending</Badge>
          )}
        </DropdownMenuLabel>

        <div className="max-h-64 overflow-y-auto divide-y">
          {pendingItems.length === 0 ? (
            <div className="p-4 text-center text-xs text-muted-foreground">
              No pending supervisory approvals
            </div>
          ) : (
            pendingItems.map((item) => (
              <DropdownMenuItem key={item.id} asChild className="p-3 cursor-pointer">
                <Link to={`/intake/${item.id}/decision`} className="flex flex-col gap-1 w-full">
                  <div className="flex items-center justify-between w-full">
                    <span className="font-mono font-bold text-primary text-xs">{item.referral_number}</span>
                    <Badge variant={item.priority === "Crisis" ? "destructive" : "secondary"} className="text-[10px]">
                      {item.priority}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground truncate">
                    {item.primary_concern?.replace(/_/g, ' ') || item.summary || "Pending review"}
                  </p>
                </Link>
              </DropdownMenuItem>
            ))
          )}
        </div>

        {pendingCount > 0 && (
          <div className="p-2 border-t bg-muted/10 text-center">
            <Link
              to="/intake/approvals"
              className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1"
            >
              <span>View Full Approval Queue</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

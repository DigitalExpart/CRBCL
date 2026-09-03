import React from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import NotificationBell from "@/components/notifications/NotificationBell";
import UserNav from "./UserNav";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-border px-4 lg:px-8 flex items-center justify-between bg-card/50 backdrop-blur-sm sticky top-0 z-30">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden sm:inline">
              Chief Red Bear Children's Lodge • Family Wellness Platform
            </span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <NotificationBell />
            <div className="h-5 w-px bg-border/60" />
            <UserNav />
          </div>
        </header>

        <main className="flex-1 overflow-x-hidden">
          <div className="p-4 lg:p-8 max-w-[1400px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
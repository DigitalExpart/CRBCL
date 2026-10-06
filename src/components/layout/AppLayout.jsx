import React from "react";
import { Outlet, Link } from "react-router-dom";
import Sidebar from "./Sidebar";
import NotificationBell from "@/components/notifications/NotificationBell";
import UserNav from "./UserNav";
import crbclEmblem from "@/assets/crbcl-emblem.png";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-border pl-16 pr-4 lg:px-8 flex items-center justify-between bg-card/50 backdrop-blur-sm sticky top-0 z-30">
          <div className="flex items-center gap-2.5">
            <Link to="/" className="flex items-center gap-2.5 group focus:outline-none">
              <img
                src={crbclEmblem}
                alt="Chief Red Bear Children's Lodge"
                className="w-6 h-6 object-contain transition-transform group-hover:scale-105"
              />
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden sm:inline group-hover:text-foreground transition-colors">
                Chief Red Bear Children's Lodge • Family Wellness Platform
              </span>
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider sm:hidden group-hover:text-foreground transition-colors">
                CRBCL
              </span>
            </Link>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <NotificationBell />
            <div className="h-5 w-px bg-border/60" />
            <UserNav />
          </div>
        </header>

        <main className="flex-1 overflow-x-hidden">
          <div className="p-3 sm:p-4 lg:p-8 max-w-[1400px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
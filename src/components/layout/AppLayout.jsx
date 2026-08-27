import React from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 min-w-0 overflow-x-hidden">
        <div className="p-4 lg:p-8 pt-16 lg:pt-8 max-w-[1400px]">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
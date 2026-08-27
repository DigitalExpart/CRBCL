import React from "react";

const statusColors = {
  "Active": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "Open": "bg-blue-100 text-blue-700 border-blue-200",
  "In Progress": "bg-sky-100 text-sky-700 border-sky-200",
  "Closed": "bg-gray-100 text-gray-600 border-gray-200",
  "Pending": "bg-amber-100 text-amber-700 border-amber-200",
  "Pending Intake": "bg-amber-100 text-amber-700 border-amber-200",
  "Pending Review": "bg-amber-100 text-amber-700 border-amber-200",
  "Applied": "bg-indigo-100 text-indigo-700 border-indigo-200",
  "Approved": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "Under Review": "bg-violet-100 text-violet-700 border-violet-200",
  "Escalated": "bg-red-100 text-red-700 border-red-200",
  "Critical": "bg-red-100 text-red-700 border-red-200",
  "High": "bg-orange-100 text-orange-700 border-orange-200",
  "Medium": "bg-amber-100 text-amber-700 border-amber-200",
  "Low": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "Urgent": "bg-red-100 text-red-700 border-red-200",
  "Inactive": "bg-gray-100 text-gray-600 border-gray-200",
  "Completed": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "Scheduled": "bg-blue-100 text-blue-700 border-blue-200",
  "Cancelled": "bg-gray-100 text-gray-500 border-gray-200",
  "No Show": "bg-red-100 text-red-600 border-red-200",
  "Reported": "bg-amber-100 text-amber-700 border-amber-200",
  "Under Investigation": "bg-violet-100 text-violet-700 border-violet-200",
  "Resolved": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "Referred": "bg-indigo-100 text-indigo-700 border-indigo-200",
  "Rejected": "bg-red-100 text-red-600 border-red-200",
  "Expired": "bg-gray-100 text-gray-500 border-gray-200",
  "Planning": "bg-indigo-100 text-indigo-700 border-indigo-200",
  "On Leave": "bg-amber-100 text-amber-700 border-amber-200",
  "Probation": "bg-orange-100 text-orange-700 border-orange-200",
  "Terminated": "bg-red-100 text-red-600 border-red-200",
};

const fallback = "bg-muted text-muted-foreground border-border";

export default function StatusBadge({ status }) {
  if (!status) return null;
  const classes = statusColors[status] || fallback;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${classes}`}>
      {status}
    </span>
  );
}
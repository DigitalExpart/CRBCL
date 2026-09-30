/**
 * Canonical CRBCL Staff Roles
 *
 * Authoritative client-side role definitions used across Admin invite,
 * edit, user approval, and access administration workflows.
 */

export const ROLES = [
  { key: "caseworker", label: "Caseworker — Direct Client & Case Management" },
  { key: "supervisor", label: "Supervisor — Casework Approvals & Reviews" },
  { key: "director_manager", label: "Director / Manager — Departmental Operations" },
  { key: "front_desk", label: "Front Desk / First Impression — Intake Reception & Form Triage" },
  { key: "office_coordinator", label: "Office Coordinator — Operations, Facilities & Fleet Coordination" },
  { key: "resource_worker", label: "Resource Worker — Kinship & Foster Caregiver Recruitment" },
  { key: "resource_supervisor", label: "Resource Supervisor — Approvals & Recruitment Reviews" },
  { key: "resource_director", label: "Resource Director — Resource Unit Leadership & Licensing" },
  { key: "executive_director", label: "Executive Director — Cross-Agency Leadership" },
  { key: "ceo", label: "Chief Executive Officer (CEO) — Strategic Leadership & Governance" },
  { key: "finance_staff", label: "Finance Staff — Billing & Invoices" },
  { key: "cultural_worker", label: "Cultural Worker — Cultural Supports & Elders" },
  { key: "clinical_staff", label: "Clinical Staff — Medical & Therapy" },
  { key: "case_aide", label: "Case Aide — Support Worker" },
  { key: "it_admin", label: "IT Administrator — Standalone System Admin" },
];

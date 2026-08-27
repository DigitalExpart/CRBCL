# Chief Red Bear Children's Lodge (CRBCL) Platform

**CRBCL Software** is a comprehensive child and family services management system designed specifically for Chief Red Bear Children's Lodge in Saskatchewan, Canada.

---

## 🌟 Overview

The CRBCL platform streamlines and centralizes child welfare services, family support initiatives, community prevention programs, caseload tracking, grant reporting, and AI-powered insights for staff, caseworkers, and leadership.

### ✨ Key Features

- **📊 Comprehensive Dashboard & Analytics**: Real-time stats on active cases, client risk levels, program enrollments, funding progress, and upcoming appointments.
- **📁 22 Dedicated Team Dashboards**: Tailored views and metrics for Executive Leadership, CFS, Prevention & Healing, Sacred Wolf Lodge, Home Fire, Legal/Jurisdiction, and more.
- **📂 Case Management**: Full lifecycle case tracking with priority tagging, risk levels, worker assignments, detailed notes, and progress logs.
- **👥 Client & Family Tracking**: Centralized intake, demographic details, Indigenous identity / Band / Nation records, and support plans.
- **🌿 Programs & Services**: Manage capacity, active enrollments, program budgets, and community coordinators across all service areas.
- **📅 Appointments & Calendar**: Schedule assessments, court hearings, family meetings, home visits, and counselling sessions.
- **💰 Grants, Funding & Donations**: Track provincial/federal grant allocations, expenditures, milestones, reporting deadlines, and individual donor contributions.
- **🚨 Incident Reporting**: Fast, standardized reporting of safety concerns, medical incidents, and emergency escalations.
- **🤖 Ask Red Bear**: Culturally grounded AI assistant providing automated case summaries, report drafts, data context insights, and policy support.
- **🔐 Role-Based Access Control**: Secure team access permissions and administrative user management.

---

## 🚀 Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/DigitalExpart/CRBCL.git
   cd CRBCL
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Build for production:
   ```bash
   npm run build
   ```

---

## ⚙️ Configuration

Create a `.env` or `.env.local` file in the root directory if connecting to a remote backend:

```env
VITE_API_BASE_URL=https://your-api-server.com
VITE_APP_ID=crbcl-software
```

When running without a backend configured, the application operates in standalone mode with local client persistence.

---

## 🏗️ Architecture & Tech Stack

- **Framework**: [React 18](https://reactjs.org/) + [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) + [Radix UI](https://www.radix-ui.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Charts & Data Visualization**: [Recharts](https://recharts.org/)
- **Routing**: [React Router v6](https://reactrouter.com/)
- **State & Querying**: [TanStack Query](https://tanstack.com/query)
- **HTTP Client**: [Axios](https://axios-http.com/)

---

## 🛡️ License

Copyright © 2026 Chief Red Bear Children's Lodge (CRBCL). All rights reserved.

import { Toaster } from "@/components/ui/toaster"
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClientInstance } from '@/lib/query-client'
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import PageNotFound from '@/pages/PageNotFound';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import UserNotRegisteredError from '@/components/auth/UserNotRegisteredError';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

// Auth pages
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import ForgotPassword from '@/pages/ForgotPassword';
import ResetPassword from '@/pages/ResetPassword';

// Layout
import AppLayout from '@/components/layout/AppLayout';

// Phase 3 Intake & Referrals
import IntakeList from '@/pages/IntakeList';
import NewIntake from '@/pages/NewIntake';
import IntakeDetail from '@/pages/IntakeDetail';
import IntakeDecision from '@/pages/IntakeDecision';
import SupervisorApprovalQueue from '@/pages/SupervisorApprovalQueue';

// Pages
import Dashboard from '@/pages/Dashboard';
import Cases from '@/pages/Cases';
import CaseDetail from '@/pages/CaseDetail';
import Clients from '@/pages/Clients';
import ClientDetail from '@/pages/ClientDetail';
import Families from '@/pages/Families';
import FamilyDetail from '@/pages/FamilyDetail';
import Programs from '@/pages/Programs';
import Employees from '@/pages/Employees';
import Appointments from '@/pages/Appointments';
import Funding from '@/pages/Funding';
import Donations from '@/pages/Donations';
import Documents from '@/pages/Documents';
import Incidents from '@/pages/Incidents';
import AskRedBear from '@/pages/AskRedBear';
import Teams from '@/pages/Teams';
import TeamDashboard from '@/pages/TeamDashboard';
import AdminDashboard from '@/pages/AdminDashboard';

const AuthenticatedApp = () => {
  const { isLoadingAuth, isLoadingPublicSettings, authError, navigateToLogin } = useAuth();

  if (isLoadingPublicSettings || isLoadingAuth) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-muted-foreground">Loading CRBCL Platform…</p>
        </div>
      </div>
    );
  }

  if (authError) {
    if (authError.type === 'user_not_registered') {
      return <UserNotRegisteredError />;
    } else if (authError.type === 'auth_required') {
      navigateToLogin();
      return null;
    }
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      <Route element={<ProtectedRoute unauthenticatedElement={<Navigate to="/login" replace />} />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/intake" element={<IntakeList />} />
          <Route path="/intake/new" element={<NewIntake />} />
          <Route path="/intake/approvals" element={<SupervisorApprovalQueue />} />
          <Route path="/intake/:id" element={<IntakeDetail />} />
          <Route path="/intake/:id/decision" element={<IntakeDecision />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:id" element={<CaseDetail />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/clients/:id" element={<ClientDetail />} />
          <Route path="/families" element={<Families />} />
          <Route path="/families/:id" element={<FamilyDetail />} />
          <Route path="/programs" element={<Programs />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/appointments" element={<Appointments />} />
          <Route path="/funding" element={<Funding />} />
          <Route path="/donations" element={<Donations />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/ask-red-bear" element={<AskRedBear />} />
          <Route path="/teams" element={<Teams />} />
          <Route path="/teams/:id" element={<TeamDashboard />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Route>
      </Route>

      <Route path="*" element={<PageNotFound />} />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClientInstance}>
        <Router>
          <AuthenticatedApp />
        </Router>
        <Toaster />
      </QueryClientProvider>
    </AuthProvider>
  )
}

export default App
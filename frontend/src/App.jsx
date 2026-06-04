import { useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "react-hot-toast";

import AppLayout from "./layouts/AppLayout";
import OnboardingRoute from "./routes/OnboardingRoute";
import ProtectedRoute from "./routes/ProtectedRoute";
import PublicRoute from "./routes/PublicRoute";
import TenantRoute from "./routes/TenantRoute";
import useAuthStore from "./store/authStore";

import LandingPage from "./pages/Landing";
import AcceptInvitePage from "./pages/auth/AcceptInvite";
import LoginPage from "./pages/auth/login";
import SignupPage from "./pages/auth/Signup";
import VerifyOtpPage from "./pages/auth/VerifyOtp";
import DashboardPage from "./pages/dashboard/Dashboard";
import DataQualityPage from "./pages/data-quality/DataQualityPage";
import DriftPage from "./pages/drift/DriftPage";
import IncidentsPage from "./pages/incidents/IncidentsPage";
import ModelsPage from "./pages/models/Modelspage";
import OnboardingPage from "./pages/onboarding/Onboarding";
import PipelinesPage from "./pages/pipelines/PipelinesPage";
import IncidentReportPage from "./pages/reports/IncidentReportPage";
import SchemaPage from "./pages/schema/Schema";
import SlackPage from "./pages/integrations/SlackPage";

export default function App() {
  const bootstrapAuth = useAuthStore((state) => state.bootstrapAuth);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await bootstrapAuth();
      } catch (error) {
        console.log(error);
      }
    };

    checkAuth();
  }, [bootstrapAuth]);

  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#0f172a",
            color: "#f8fafc",
            fontSize: "13px",
            borderRadius: "10px",
            padding: "12px 16px",
          },
          success: { iconTheme: { primary: "#10b981", secondary: "#f8fafc" } },
          error:   { iconTheme: { primary: "#ef4444", secondary: "#f8fafc" } },
        }}
      />
      <Routes>
        <Route
          path="/"
          element={
            <PublicRoute>
              <LandingPage />
            </PublicRoute>
          }
        />

        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />

        <Route
          path="/signup"
          element={
            <PublicRoute>
              <SignupPage />
            </PublicRoute>
          }
        />

        <Route path="/verify-otp" element={<VerifyOtpPage />} />
        <Route path="/accept-invite" element={<AcceptInvitePage />} />

        <Route
          path="/onboarding"
          element={
            <OnboardingRoute>
              <OnboardingPage />
            </OnboardingRoute>
          }
        />

        <Route
          element={
            <ProtectedRoute>
              <TenantRoute>
                <AppLayout />
              </TenantRoute>
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/pipelines" element={<PipelinesPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/data-quality" element={<DataQualityPage />} />
          <Route path="/drift" element={<DriftPage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/reports/incidents/:incidentId" element={<IncidentReportPage />} />
          <Route path="/schemas" element={<SchemaPage />} />
          <Route path="/integrations/slack" element={<SlackPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "./routes/ProtectedRoute";
import TenantRoute from "./routes/TenantRoute";
import OnboardingRoute from "./routes/OnboardingRoute";
import PublicRoute from "./routes/PublicRoute";
import { useEffect } from "react";
import useAuthStore from "./store/authStore";


import AppLayout from "./layouts/AppLayout";

import LandingPage from "./pages/Landing";
import LoginPage from "./pages/auth/login";
import SignupPage from "./pages/auth/Signup";
import VerifyOtpPage from "./pages/auth/VerifyOtp";
import DashboardPage from "./pages/dashboard/Dashboard";
import ModelsPage from "./pages/models/Modelspage";
import OpsSightLandingPage from "./pages/Landing";
import OnboardingPage from "./pages/onboarding/Onboarding";
import SchemaPage from "./pages/schema/Schema";
import PipelinesPage from "./pages/pipelines/PipelinesPage";
import IncidentsPage from "./pages/incidents/IncidentsPage";
import DataQualityPage from "./pages/data-quality/DataQualityPage";
import DriftPage from "./pages/drift/DriftPage";
import SignupPage from "./pages/Signup";
import VerifyOtpPage from "./pages/VerifyOtp";
import LoginPage from "./pages/Login";
import OnboardingPage from "./pages/Onboarding";
import DashboardPage from "./pages/Dashboard";
import OpsSightLandingPage from "./pages/Landing";


export default function App() {
  const me = useAuthStore(
    (state) => state.me
  );

  useEffect(() => {

    const checkAuth = async () => {
      try {
        await me();
      } catch (error) {
        console.log(error);
      }
    };

    checkAuth();

      <Routes>
        
        <Route path="/" element={<OpsSightLandingPage />} />
        <Route path="/signup" element={<SignupPage />} />


  }, []);
  return (
    <BrowserRouter>
      <Routes>
        {/* PUBLIC ROUTES */}
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
        <Route
          path="/onboarding"
          element={
            <OnboardingRoute>
              <OnboardingPage />
            </OnboardingRoute>
          }
        />

        {/* APP LAYOUT ROUTES */}
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
          <Route path="/schemas" element={<SchemaPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

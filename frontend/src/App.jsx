import { BrowserRouter, Routes, Route } from "react-router-dom";

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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* PUBLIC ROUTES */}
        <Route path="/" element={<LandingPage />} />

        <Route path="/login" element={<LoginPage />} />

        <Route path="/signup" element={<SignupPage />} />

        <Route path="/verify-otp" element={<VerifyOtpPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />

        {/* APP LAYOUT ROUTES */}
        <Route element={<AppLayout />}>
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

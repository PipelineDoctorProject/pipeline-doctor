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
          <Route path="/models" element={<ModelsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

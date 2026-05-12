import { BrowserRouter, Routes, Route } from "react-router-dom";

import SignupPage from "./pages/Signup";
import VerifyOtpPage from "./pages/VerifyOtp";
import LoginPage from "./pages/Login";
import OnboardingPage from "./pages/Onboarding";
import DashboardPage from "./pages/Dashboard";
import OpsSightLandingPage from "./pages/Landing";

export default function App() {

  return (
    <BrowserRouter>

      <Routes>
        
        <Route path="/" element={<OpsSightLandingPage />} />
        
        <Route path="/signup" element={<SignupPage />} />

        <Route path="/verify-otp" element={<VerifyOtpPage />} />

        <Route path="/login" element={<LoginPage />} />

        <Route path="/onboarding" element={<OnboardingPage />} />

        <Route path="/dashboard" element={<DashboardPage />} />

      </Routes>

    </BrowserRouter>
  );
}
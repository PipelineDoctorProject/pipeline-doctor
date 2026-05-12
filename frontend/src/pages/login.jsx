import React, { useState } from "react";
import { Eye, EyeOff, Apple } from "lucide-react";
import { FaGoogle } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import Logo from "../assets/logo_og.png";
import useAuthStore from "../store/authStore";
export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  const login = useAuthStore((state) => state.login);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();

    setIsLoading(true);

    try {
      await login(email, password);

      navigate("/dashboard");
    } catch (err) {
      alert(err?.detail || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black overflow-hidden relative flex items-center justify-center">
      {/* BACKGROUND */}
      <div className="absolute inset-0 bg-[#050505]" />

      {/* Metallic waves */}
      <div className="absolute -left-40 top-0 w-[600px] h-[600px] rounded-full border border-white/10 opacity-40 blur-sm" />
      <div className="absolute -left-20 top-10 w-[500px] h-[500px] rounded-full border border-white/5 opacity-30 blur-sm" />

      {/* MAIN CARD */}
      <div className="relative w-[1380px] h-[760px] rounded-[18px] overflow-hidden bg-[#0f0f12] border border-white/[0.06] shadow-[0_0_80px_rgba(0,0,0,0.9)] flex">
        {/* LEFT PANEL */}
        {/* LEFT PANEL */}
        <div className="w-[48%] bg-[#111114] relative px-14 py-10 flex flex-col">
          {/* subtle noise */}
          <div className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_center,white_1px,transparent_1px)] bg-[length:18px_18px]" />

          {/* TOP NAV */}
          <div className="relative z-10 flex justify-end">
            <div className="flex items-center gap-3 text-[11px]">
              <span className="text-gray-600">New here?</span>

              <button
                onClick={() => navigate("/signup")}
                className="px-3 py-1 rounded-md bg-white/[0.04] border border-white/[0.05] text-white hover:bg-white/[0.08] transition"
              >
                Sign Up
              </button>
            </div>
          </div>

          {/* CENTER CONTENT */}
          <div className="relative z-10 flex-1 flex items-center justify-center">
            <div className="w-[360px] flex flex-col">
              {/* LOGO */}
              <img
                src={Logo}
                className="w-[170px] mb-17 object-contain"
                alt="OpsSight Logo"
              />

              {/* TITLE */}
              <h1 className="text-white text-[28px] font-medium mb-1 tracking-[-0.02em]">
                Welcome Back
              </h1>

              <p className="text-gray-600 text-[12px] mb-8">
                Login to continue accessing your workspace.
              </p>

              {/* SOCIAL BUTTONS */}
              <div className="flex gap-2 mb-5">
                <button className="flex-1 h-[38px] rounded-lg bg-[#17171b] border border-white/[0.04] flex items-center justify-center text-gray-400 hover:bg-[#1c1c20] transition">
                  <FaGoogle size={12} />
                </button>

                <button className="flex-1 h-[38px] rounded-lg bg-[#17171b] border border-white/[0.04] flex items-center justify-center text-gray-400 hover:bg-[#1c1c20] transition">
                  <Apple size={13} />
                </button>
              </div>

              {/* DIVIDER */}
              <div className="flex items-center gap-3 mb-5">
                <div className="flex-1 h-px bg-white/[0.05]" />

                <span className="text-[9px] tracking-[0.35em] text-gray-700">
                  OR
                </span>

                <div className="flex-1 h-px bg-white/[0.05]" />
              </div>

              {/* FORM */}
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] text-gray-500 mb-2">
                    Email
                  </label>

                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="mail@example.com"
                    className="w-full h-[42px] px-4 rounded-lg bg-[#17171b] border border-white/[0.04] outline-none text-[13px] text-white placeholder:text-gray-700 focus:border-white/20 transition"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-[11px] text-gray-500">
                      Password
                    </label>

                    <button className="text-[11px] text-gray-600 hover:text-gray-300 transition">
                      Forgot password?
                    </button>
                  </div>

                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full h-[42px] px-4 rounded-lg bg-[#17171b] border border-white/[0.04] outline-none text-[13px] text-white placeholder:text-gray-700 focus:border-white/20 transition"
                    />

                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-600 hover:text-white"
                    >
                      {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                {/* LOGIN BUTTON */}
                <button
                  type="submit"
                  onClick={handleLogin}
                  disabled={isLoading}
                  className="w-full h-[42px] rounded-lg bg-[#3563ff] hover:bg-[#2957f5] transition text-white text-[13px] font-medium shadow-[0_0_30px_rgba(53,99,255,0.25)] disabled:opacity-50"
                >
                  {isLoading ? "Logging in..." : "Login"}
                </button>

                {/* FOOTER */}
                <p className="text-center text-[11px] text-gray-600 pt-2">
                  Don’t have an account?{" "}
                  <span
                    onClick={() => navigate("/signup")}
                    className="text-white cursor-pointer hover:underline"
                  >
                    Create account
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="flex-1 relative overflow-hidden bg-[#0d0f14]">
          {/* TEXTURE LAYERS */}
          <div className="absolute inset-0 overflow-hidden">
            {/* massive soft gradient */}
            <div className="absolute top-[-10%] right-[-10%] w-[700px] h-[700px] rounded-full bg-white/[0.03] blur-[140px]" />

            {/* metallic beam */}
            <div className="absolute top-[15%] left-[-10%] w-[900px] h-[180px] rotate-[-18deg] bg-white/[0.025] blur-3xl" />

            {/* subtle grid texture */}
            <div className="absolute inset-0 opacity-[0.025] bg-[linear-gradient(to_right,white_1px,transparent_1px),linear-gradient(to_bottom,white_1px,transparent_1px)] bg-[size:44px_44px]" />

            {/* vignette */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent,rgba(0,0,0,0.55))]" />

            {/* hidden system text */}
            <div className="absolute top-[12%] left-[10%] text-[11px] leading-8 tracking-[0.35em] uppercase text-white/[0.05]">
              MODEL MONITORING
              <br />
              DATA VALIDATION
              <br />
              PIPELINE OBSERVABILITY
              <br />
              DRIFT ANALYSIS
              <br />
              SCHEMA GOVERNANCE
              <br />
              INCIDENT DETECTION
            </div>
          </div>

          {/* MAIN CONTENT */}
          <div className="relative z-10 h-full flex flex-col justify-center px-20">
            {/* small label */}
            <div className="mb-10">
              <span className="text-[10px] tracking-[0.4em] uppercase text-gray-600">
                OpsSight Platform
              </span>
            </div>

            {/* giant visual typography */}
            <div className="relative">
              <h2 className="text-[96px] leading-[0.88] font-semibold tracking-[-0.08em] text-white/95">
                Trust
                <br />
                your
                <br />
                models.
              </h2>

              {/* faded giant word */}
              <div className="absolute -top-47 left-[38%] rotate-10 text-[180px] font-semibold tracking-[-0.1em] text-white/[0.025] select-none">
                Artificial
              </div>
              <div className="absolute -top-10 left-[25%] text-[180px] font-semibold tracking-[-0.1em] text-white/[0.025] select-none">
                Intelligence
              </div>
            </div>

            {/* supporting text */}
            <p className="mt-10 max-w-[480px] text-[15px] leading-8 text-gray-500">
              Monitor data quality, detect silent failures, validate schema
              evolution, and maintain reliable machine learning infrastructure
              from one unified operational layer.
            </p>

            {/* bottom signal */}
            <div className="mt-16 flex items-center gap-4">
              <div className="w-2 h-2 rounded-full bg-white/30 animate-pulse" />

              <div className="h-px w-[180px] bg-gradient-to-r from-white/[0.12] to-transparent" />

              <span className="text-[11px] tracking-[0.3em] uppercase text-gray-700">
                Production Systems Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

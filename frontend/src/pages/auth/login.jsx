import React, { useState } from "react";
import { Eye, EyeOff, Apple } from "lucide-react";
import { FaGoogle } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

import Logo from "../../assets/logo2.png";
import useAuthStore from "../../store/authStore";

export default function LoginPage() {

  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  const login = useAuthStore((state) => state.login);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");

  const [isLoading, setIsLoading] = useState(false);

  const getLoginErrorMessage = (err) => {
    const detail = err?.detail;

    if (detail?.message) {
      return detail.message;
    }

    if (typeof detail === "string") {
      return detail;
    }

    return "We could not log you in. Please check your details and try again.";
  };

  const handleLogin = async (e) => {

    e.preventDefault();

    setLoginError("");
    setIsLoading(true);

    try {

      await login(email, password);

      navigate("/dashboard");

    } catch (err) {

      setLoginError(getLoginErrorMessage(err));

    } finally {

      setIsLoading(false);
    }
  };

  return (

    <div className="min-h-screen overflow-hidden relative flex items-center justify-center bg-[#f4f7fb]">

      {/* BACKGROUND */}
      <div className="absolute inset-0 overflow-hidden">

        {/* soft glows */}
        <div className="absolute top-[-15%] right-[-10%] w-[900px] h-[900px] rounded-full bg-[#3563ff]/[0.08] blur-[140px]" />

        <div className="absolute bottom-[-20%] left-[-10%] w-[700px] h-[700px] rounded-full bg-[#7c3aed]/[0.05] blur-[140px]" />

        {/* subtle grid */}
        <div className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(to_right,rgba(15,23,42,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.08)_1px,transparent_1px)] bg-[size:42px_42px]" />
      </div>

      {/* MAIN CARD */}
      <div className="relative w-[1380px] h-[760px] rounded-[28px] overflow-hidden bg-white border border-black/[0.05] shadow-[0_20px_80px_rgba(15,23,42,0.08)] flex">

        {/* LEFT PANEL */}
        <div className="w-[48%] bg-[#fcfcfd] relative px-14 py-10 flex flex-col border-r border-black/[0.04]">

          {/* noise texture */}
          <div className="absolute inset-0 opacity-[0.015] bg-[radial-gradient(circle_at_center,black_1px,transparent_1px)] bg-[length:18px_18px]" />

          {/* TOP NAV */}
          <div className="relative z-10 flex justify-end">

            <div className="flex items-center gap-3 text-[11px]">

              <span className="text-gray-500">
                New here?
              </span>

              <button
                onClick={() => navigate("/signup")}
                className="px-4 py-2 rounded-xl bg-[#f7f8fb] border border-black/[0.05] text-[#111827] hover:bg-[#eef2ff] transition"
              >
                Sign Up
              </button>
            </div>
          </div>

          {/* CENTER */}
          <div className="relative z-10 flex-1 flex items-center justify-center">

            <div className="w-[370px] flex flex-col">

              {/* LOGO */}
              <img
                src={Logo}
                className="w-[170px] mb-16 object-contain"
                alt="OpsSight Logo"
              />

              {/* TITLE */}
              <h1 className="text-[#111827] text-[34px] font-semibold tracking-[-0.04em] mb-2">

                Welcome Back
              </h1>

              <p className="text-gray-500 text-[14px] leading-7 mb-10">

                Access your workspace and monitor production
                ML infrastructure in real time.
              </p>

              {/* SOCIAL */}
              
              

              {/* FORM */}
              <form
                onSubmit={handleLogin}
                className="space-y-5"
              >
                {loginError && (
                  <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-[13px] leading-6 text-red-700">
                    {loginError}
                  </div>
                )}

                {/* EMAIL */}
                <div>

                  <label className="block text-[12px] text-gray-500 mb-3">

                    Email
                  </label>

                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="mail@example.com"
                    className="w-full h-[52px] px-5 rounded-2xl bg-[#f7f8fb] border border-black/[0.05] outline-none text-[14px] text-[#111827] placeholder:text-gray-400 focus:border-[#3563ff]/30 transition"
                  />
                </div>

                {/* PASSWORD */}
                <div>

                  <div className="flex items-center justify-between mb-3">

                    <label className="text-[12px] text-gray-500">

                      Password
                    </label>

                    <button
                      type="button"
                      className="text-[12px] text-[#3563ff] hover:underline"
                    >
                      Forgot Password?
                    </button>
                  </div>

                  <div className="relative">

                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full h-[52px] px-5 rounded-2xl bg-[#f7f8fb] border border-black/[0.05] outline-none text-[14px] text-[#111827] placeholder:text-gray-400 focus:border-[#3563ff]/30 transition"
                    />

                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#111827]"
                    >
                      {showPassword ? (
                        <EyeOff size={17} />
                      ) : (
                        <Eye size={17} />
                      )}
                    </button>
                  </div>
                </div>

                {/* LOGIN BUTTON */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-[54px] rounded-2xl bg-[#3563ff] hover:bg-[#2957f5] transition text-white text-[14px] font-medium shadow-[0_10px_40px_rgba(53,99,255,0.18)] disabled:opacity-50"
                >
                  {isLoading
                    ? "Logging In..."
                    : "Login"}
                </button>

                {/* FOOTER */}
                <p className="text-center text-[12px] text-gray-500 pt-3">

                  Don’t have an account?{" "}

                  <span
                    onClick={() => navigate("/signup")}
                    className="text-[#3563ff] cursor-pointer hover:underline"
                  >
                    Create Account
                  </span>
                </p>
              </form>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="flex-1 relative overflow-hidden bg-[#f8fafc]">

          {/* TEXTURE */}
          <div className="absolute inset-0 overflow-hidden">

            {/* glow */}
            <div className="absolute top-[8%] left-[10%] w-[600px] h-[600px] rounded-full bg-[#3563ff]/[0.06] blur-[120px]" />

            {/* beam */}
            <div className="absolute top-[18%] left-[-10%] w-[900px] h-[220px] rotate-[-18deg] bg-[#3563ff]/[0.04] blur-3xl" />

            {/* rings */}
            <div className="absolute right-[-20%] top-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full border border-[#3563ff]/10" />

            <div className="absolute right-[-10%] top-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full border border-[#3563ff]/10" />

            {/* grid */}
            <div className="absolute inset-0 opacity-[0.025] bg-[linear-gradient(to_right,rgba(15,23,42,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.08)_1px,transparent_1px)] bg-[size:44px_44px]" />

        
          </div>

          {/* CONTENT */}
          <div className="relative z-10 h-full flex flex-col justify-center px-20">

            {/* LABEL */}
            <div className="mb-10">

              <span className="text-[11px] tracking-[0.35em] uppercase text-gray-400">

                Enterprise AI Infrastructure
              </span>
            </div>

            {/* HERO */}
            <div className="relative">

              <h2 className="text-[92px] leading-[0.88] font-semibold tracking-[-0.08em] text-[#111827]">

                Trust
                <br />

                your
                <br />

                models.
              </h2>

              {/* bg text */}
              <div className="absolute -top-6 -left-[58%] -rotate-70 text-[190px] font-bold tracking-[-0.1em] text-[#3563ff]/[0.03] select-none">

                Artificial
              </div>

              <div className="absolute -top-15 left-[25%] text-[180px] -rotate-4 font-bold tracking-[-0.1em] text-[#3563ff]/[0.03] select-none">

                Intelligence
              </div>
            </div>

            {/* DESCRIPTION */}
            <p className="mt-10 max-w-[500px] text-[15px] leading-8 text-gray-600">

              Monitor data quality, detect silent failures,
              validate schema evolution, and maintain
              reliable machine learning infrastructure
              from one unified operational layer.
            </p>

            {/* SIGNAL */}
            <div className="mt-16 flex items-center gap-4">

              <div className="w-2 h-2 rounded-full bg-[#3563ff]/40 animate-pulse" />

              <div className="h-px w-[180px] bg-gradient-to-r from-[#3563ff]/20 to-transparent" />

              <span className="text-[11px] tracking-[0.3em] uppercase text-gray-400">

                Production Systems Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import React, { useState } from "react";
import { Eye, EyeOff, Apple } from "lucide-react";
import { FaGoogle } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

import Logo from "../../assets/logo_og.png";
import Logo2 from "../../assets/logo2.png";
import useAuthStore from "../../store/authStore";

export default function SignupPage() {

  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  const signup = useAuthStore((state) => state.signup);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [isLoading, setIsLoading] = useState(false);

  const handleSignup = async (e) => {

    e.preventDefault();

    setIsLoading(true);

    try {

      await signup(email, password);

      navigate("/verify-otp", {
        state: { email },
      }, { replace: true });

    } catch (err) {

      alert(err?.detail || "Signup failed");

    } finally {

      setIsLoading(false);
    }
  };

  return (

    <div className="min-h-screen overflow-hidden relative flex items-center justify-center bg-[#f4f7fb]">

      {/* BACKGROUND */}
      <div className="absolute inset-0 overflow-hidden">

        {/* soft glow */}
        <div className="absolute top-[-20%] right-[-10%] w-[900px] h-[900px] rounded-full bg-[#3563ff]/[0.08] blur-[140px]" />

        <div className="absolute bottom-[-30%] left-[-10%] w-[800px] h-[800px] rounded-full bg-[#7c3aed]/[0.05] blur-[140px]" />

        {/* subtle grid */}
        <div className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(to_right,rgba(15,23,42,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.08)_1px,transparent_1px)] bg-[size:42px_42px]" />
      </div>

      {/* MAIN CARD */}
      <div className="relative w-[1380px] h-[760px] rounded-[28px] overflow-hidden bg-white border border-black/[0.05] shadow-[0_20px_80px_rgba(15,23,42,0.08)] flex">

        {/* LEFT PANEL */}
        <div className="w-[48%] bg-[#fcfcfd] relative px-14 py-10 flex flex-col border-r border-black/[0.04]">

          {/* texture */}
          <div className="absolute inset-0 opacity-[0.015] bg-[radial-gradient(circle_at_center,black_1px,transparent_1px)] bg-[length:18px_18px]" />

          {/* top nav */}
          <div className="relative z-10 flex justify-end">

            <div className="flex items-center gap-3 text-[11px]">

              <span className="text-gray-500">
                Already registered?
              </span>

              <button
                onClick={() => navigate("/login")}
                className="px-4 py-2 rounded-xl bg-[#f7f8fb] border border-black/[0.05] text-[#111827] hover:bg-[#eef2ff] transition"
              >
                Login
              </button>
            </div>
          </div>

          {/* CENTER */}
          <div className="relative z-10 flex-1 flex items-center justify-center">

            <div className="w-[380px] flex flex-col">

              {/* LOGO */}
              <img
                src={Logo2}
                className="w-[170px] mb-16 object-contain"
                alt="OpsSight Logo"
              />

              {/* TITLE */}
              <h1 className="text-[#111827] text-[34px] font-semibold tracking-[-0.04em] mb-2">

                Create Workspace
              </h1>

              <p className="text-gray-500 text-[14px] leading-7 mb-10">

                Build a centralized workspace to monitor, validate,
                and govern production machine learning systems.
              </p>

           

            

              {/* FORM */}
              <form onSubmit={handleSignup} className="space-y-5">

                {/* EMAIL */}
                <div>

                  <label className="block text-[12px] text-gray-500 mb-3">

                    Work Email
                  </label>

                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="mail@example.com"
                    className="w-full h-[52px] px-5 rounded-2xl bg-[#f7f8fb] border border-black/[0.06] outline-none text-[14px] text-[#111827] placeholder:text-gray-400 focus:border-[#3563ff]/30 transition"
                  />
                </div>

                {/* PASSWORD */}
                <div>

                  <label className="block text-[12px] text-gray-500 mb-3">

                    Password
                  </label>

                  <div className="relative">

                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Create secure password"
                      className="w-full h-[52px] px-5 rounded-2xl bg-[#f7f8fb] border border-black/[0.06] outline-none text-[14px] text-[#111827] placeholder:text-gray-400 focus:border-[#3563ff]/30 transition"
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

                {/* BUTTON */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-[54px] rounded-2xl bg-[#3563ff] hover:bg-[#2957f5] transition text-white text-[14px] font-medium shadow-[0_10px_40px_rgba(53,99,255,0.18)] disabled:opacity-50"
                >
                  {isLoading
                    ? "Creating Workspace..."
                    : "Create Workspace"}
                </button>

                {/* FOOTER */}
                <p className="text-center text-[12px] text-gray-500 pt-3">

                  Already have an account?{" "}

                  <span
                    onClick={() => navigate("/login")}
                    className="text-[#3563ff] cursor-pointer hover:underline"
                  >
                    Login
                  </span>
                </p>
              </form>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="flex-1 relative overflow-hidden bg-[#f8fafc]">

          {/* BACKGROUND */}
          <div className="absolute inset-0 overflow-hidden">

            {/* soft glow */}
            <div className="absolute top-[12%] left-[10%] w-[500px] h-[500px] rounded-full bg-[#3563ff]/[0.08] blur-[120px]" />

            {/* diagonal light */}
            <div className="absolute top-[35%] right-[-10%] w-[900px] h-[220px] rotate-[18deg] bg-[#3563ff]/[0.04] blur-3xl" />

            {/* subtle rings */}
            <div className="absolute right-[-20%] top-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full border border-[#3563ff]/10" />

            <div className="absolute right-[-10%] top-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full border border-[#3563ff]/10" />

            {/* texture */}
            <div className="absolute inset-0 opacity-[0.025] bg-[radial-gradient(circle_at_center,black_1px,transparent_1px)] bg-[length:24px_24px]" />
          </div>

          {/* CONTENT */}
          <div className="relative z-10 h-full flex flex-col justify-center px-20">

            {/* label */}
            <div className="mb-10">

              <span className="text-[11px] tracking-[0.35em] uppercase text-gray-400">

                Enterprise MLOps Platform
              </span>
            </div>

            {/* hero */}
            <div className="relative">

              <h2 className="text-[92px] leading-[0.88] font-semibold tracking-[-0.08em] text-[#111827]">

                Reliable
                <br />

                AI starts
                <br />

                with visibility.
              </h2>

              {/* faded bg text */}
              <div className="absolute rotate-[-10deg] -bottom-4 left-[32%] text-[190px] font-bold tracking-[-0.1em] text-[#3563ff]/[0.05] select-none">

                MLOps
              </div>
            </div>

            {/* description */}
            <p className="mt-10 max-w-[520px] text-[15px] leading-8 text-gray-600">

              OpsSight helps teams monitor model behavior,
              validate incoming datasets, detect drift,
              and maintain operational reliability across
              production AI infrastructure.
            </p>

            {/* bottom line */}
            <div className="mt-16 flex items-center gap-4">

              <span className="text-[11px] tracking-[0.3em] uppercase text-gray-400">

                Initialize Workspace
              </span>

              <div className="h-px w-[180px] bg-gradient-to-r from-[#3563ff]/20 to-transparent" />

              <div className="w-2 h-2 rounded-full bg-[#3563ff]/40 animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
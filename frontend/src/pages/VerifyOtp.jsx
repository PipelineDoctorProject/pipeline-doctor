import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";

import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import Logo from "../assets/logo_og.png";
import useAuthStore from "../store/authStore";

export default function VerifyOtpPage() {

  const navigate = useNavigate();
  const location = useLocation();

  const email = location.state?.email;

  const verifyOtp = useAuthStore(
    (state) => state.verifyOtp
  );

  const [otp, setOtp] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleVerify = async (e) => {
    e.preventDefault();

    setIsLoading(true);

    try {

      const response = await verifyOtp(email, otp);

      if (response.onboarding_required) {
        navigate("/onboarding");
      } else {
        navigate("/dashboard");
      }

    } catch (err) {

      alert(err?.detail || "OTP verification failed");

    } finally {

      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#06070b] font-sans text-white">

      {/* BACKGROUND */}
      <div className="absolute inset-0 overflow-hidden">

        {/* glow */}
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full bg-white/[0.025] blur-[160px]" />

        {/* metallic beam */}
        <div className="absolute top-[30%] left-[-20%] w-[1400px] h-[240px] rotate-[12deg] bg-white/[0.02] blur-3xl" />

        {/* subtle texture */}
        <div className="absolute inset-0 opacity-[0.02] bg-[linear-gradient(to_right,white_1px,transparent_1px),linear-gradient(to_bottom,white_1px,transparent_1px)] bg-[size:48px_48px]" />

        {/* hidden system text */}
        <div className="absolute top-[12%] right-[8%] text-right text-[10px] leading-7 tracking-[0.35em] uppercase text-white/[0.05]">

          SECURE ACCESS<br />
          AUTHORIZATION<br />
          SESSION VALIDATION<br />
          ENCRYPTED WORKSPACE
        </div>

        {/* vignette */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent,rgba(0,0,0,0.68))]" />
      </div>

      {/* LOGO */}
      <div className="absolute top-10 left-10 z-20">

        <img
          src={Logo}
          alt="OpsSight Logo"
          className="w-[145px] object-contain opacity-90"
        />
      </div>

      {/* MAIN CONTENT */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6">

        {/* badge */}
        <div className="mb-10">

          
        </div>

        {/* heading */}
        <div className="relative text-center">

          <h1 className="text-[78px] leading-[0.9] tracking-[-0.08em] font-semibold text-white">

            Verify
            <br />

            your access.
          </h1>

          {/* faded bg text */}
          <div className="pointer-events-none absolute rotate-[15deg] top-[-150px] left-1/2 -translate-x-1/2 text-[590px] tracking-[-0.1em] font-semibold text-white/[0.015] select-none">
  OpsSight.ai
</div>
        </div>

        {/* paragraph */}
        <p className="mt-8 max-w-[520px] text-center text-[15px] leading-8 text-gray-500">

          Enter the verification code sent to

          <span className="text-gray-300">
            {" "} {email || "your email"}
          </span>

          {" "}to continue securely accessing your
          OpsSight workspace.
        </p>

        {/* FORM */}
        <form
          onSubmit={handleVerify}
          className="mt-12 w-full max-w-[420px]"
        >

          {/* otp input */}
          <input
            type="text"
            placeholder="ENTER OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            className="w-full h-[64px] rounded-2xl border border-white/[0.05] bg-white/[0.03] backdrop-blur-xl px-6 text-center text-[22px] tracking-[0.55em] text-white outline-none transition placeholder:text-gray-700 focus:border-white/[0.12]"
          />

          {/* button */}
          <button
            type="submit"
            disabled={isLoading}
            className="mt-5 w-full h-[58px] rounded-2xl bg-[#3563ff] hover:bg-[#2957f5] transition text-white text-[13px] font-medium shadow-[0_0_40px_rgba(53,99,255,0.18)] disabled:opacity-50"
          >
            {isLoading
              ? "Verifying..."
              : "Verify Access"}
          </button>
        </form>

        {/* footer */}
        <button
          type="button"
          className="mt-8 text-[12px] text-gray-600 hover:text-gray-400 transition"
        >
          Resend verification code
        </button>

        {/* bottom signal */}
        <div className="mt-16 flex items-center gap-4">

          <div className="h-px w-[120px] bg-gradient-to-r from-transparent via-white/[0.12] to-transparent" />

          <div className="w-2 h-2 rounded-full bg-white/30 animate-pulse" />

          <div className="h-px w-[120px] bg-gradient-to-r from-transparent via-white/[0.12] to-transparent" />
        </div>
      </div>
    </div>
  );
}
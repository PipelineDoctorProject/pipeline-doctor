import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/700.css";
import { useNavigate } from "react-router-dom";
import Logo from "../assets/logo_og.png";

export default function OpsSightLandingPage() {
    const navigate = useNavigate()
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#06070b] px-6 text-white font-sans">

      {/* BACKGROUND */}
      <div className="absolute inset-0 overflow-hidden">

        {/* rings */}
        <div className="absolute right-[-10%] top-1/2 h-[1400px] w-[1400px] -translate-y-1/2 rounded-full border border-white/[0.03]" />

        <div className="absolute right-[2%] top-1/2 h-[1100px] w-[1100px] -translate-y-1/2 rounded-full border border-white/[0.025]" />

        <div className="absolute right-[12%] top-1/2 h-[850px] w-[850px] -translate-y-1/2 rounded-full border border-white/[0.02]" />

        {/* bottom glow */}
        <div className="absolute left-1/2 top-[72%] h-[1200px] w-[2000px] -translate-x-1/2 rounded-[100%] bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.14),transparent_70%)] blur-3xl" />

        {/* noise */}
        <div className="absolute inset-0 opacity-[0.08] bg-[radial-gradient(circle_at_center,white_1px,transparent_1px)] bg-[length:28px_28px]" />
      </div>

      {/* LOGO */}
      <div className="absolute top-8 left-8 z-50 sm:left-10 sm:top-10">
        <img
          src={Logo}
          alt="OpsSight Logo"
          className="w-[135px] object-contain opacity-90"
        />
      </div>

      {/* CONTENT */}
      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-col items-center text-center">

        

        {/* HEADING */}
        <h1 className="max-w-6xl text-5xl font-semibold leading-[0.92] tracking-[-0.07em] text-white sm:text-7xl lg:text-[104px]">

          Detect failures
          <br />

          before your users
          <br />

          ever notice them.
        </h1>

        {/* SUBTEXT */}
        <p className="mt-10 max-w-3xl text-[18px] font-normal leading-9 text-gray-500 sm:text-[20px]">

          Monitor data quality, schema evolution, drift detection,
          and pipeline reliability across your production ML systems
          from one unified observability platform.
        </p>

        {/* BUTTONS */}
        <div className="mt-14 flex flex-col items-center gap-5 sm:flex-row">

          <button
            type="button"
            onClick={()=> navigate('/signup')}
            className="rounded-2xl bg-[#3563ff] px-10 py-4 text-sm font-medium text-white shadow-[0_0_40px_rgba(53,99,255,0.22)] transition duration-300 hover:bg-[#2957f5]"
          >
            Start Free
          </button>

          <button
            type="button"
            onClick={()=> navigate('/logi')}
            className="rounded-2xl border border-white/[0.06] bg-white/[0.02] px-10 py-4 text-sm font-medium text-white backdrop-blur-xl transition duration-300 hover:bg-white/[0.04]"
          >
            Login
          </button>
        </div>
      </div>
    </div>
  );
}
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/700.css";
import { useNavigate } from "react-router-dom";
import Logo from "../assets/logo_og.png";
import Logo2 from '../assets/logo2.png';

export default function OpsSightLandingPage() {

  const navigate = useNavigate();

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#f7f8fb] px-6 text-white font-sans">

      {/* BACKGROUND */}
      <div className="absolute inset-0 overflow-hidden">

 
       
        {/* bottom glow */}
        <div className="absolute left-1/2 top-[72%] h-[1200px] w-[2000px] -translate-x-1/2 rounded-[100%] bg-[radial-gradient(circle_at_center,rgba(53,99,255,0.36),transparent_1110%)] blur-3xl" />

        {/* noise */}
        <div className="absolute inset-0 opacity-[0.11] bg-[radial-gradient(circle_at_center,blue_1px,transparent_1px)] bg-[length:28px_28px]" />
      </div>

      {/* LOGO */}
      <div className="absolute top-8 left-8 z-50 sm:left-10 sm:top-10">
        <img
          src={Logo2}
          alt="OpsSight Logo"
          className="w-[135px] object-contain opacity-90"
        />
      </div>

      {/* CONTENT */}
      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-col items-center text-center">

        {/* HEADING */}
        <h1 className="max-w-6xl text-5xl font-semibold leading-[0.92] tracking-[-0.07em] text-[#111827] sm:text-7xl lg:text-[104px]">

          Detect failures
          <br />

          before your users
          <br />

          ever notice them.
        </h1>

        {/* SUBTEXT */}
        <p className="mt-10 max-w-3xl text-[18px] font-normal leading-9 text-gray-600 sm:text-[20px]">

          Monitor data quality, schema evolution, drift detection,
          and pipeline reliability across your production ML systems
          from one unified observability platform.
        </p>

        {/* BUTTONS */}
        <div className="mt-14 flex flex-col items-center gap-5 sm:flex-row">

          <button
            type="button"
            onClick={() => navigate('/signup')}
            className="rounded-2xl bg-[#3563ff] px-10 py-4 text-sm font-medium text-white shadow-[0_0_40px_rgba(53,99,255,0.22)] transition duration-300 hover:bg-[#2957f5]"
          >
            Start Free
          </button>

          <button
            type="button"
            onClick={() => navigate('/login')}
            className="rounded-2xl border border-black/[0.06] bg-white/70 px-10 py-4 text-sm font-medium text-[#111827] backdrop-blur-xl transition duration-300 hover:bg-white"
          >
            Login
          </button>
        </div>
      </div>
    </div>
  );
}
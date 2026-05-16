import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";

// import Logo from ".../assets/logo_og.png";
import Logo2 from '../../assets/logo2.png';

export default function AcceptInvitePage() {

  const navigate = useNavigate();

  const [searchParams] = useSearchParams();

  const token = searchParams.get("token");

  const [showPassword, setShowPassword] =
    useState(false);

  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);

  const [password, setPassword] = useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [isLoading, setIsLoading] = useState(false);

  const handleAcceptInvite = async (e) => {

  e.preventDefault();

  if (password !== confirmPassword) {

    alert("Passwords do not match");

    return;
  }

  setIsLoading(true);

  try {

    const response = await fetch(
      "http://localhost:8000/invite/accept",
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        credentials: "include",

        body: JSON.stringify({
          token,
          password,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw data;
    }

    navigate("/dashboard");

  } catch (err) {

    alert(
      err?.detail || "Failed to accept invitation"
    );

  } finally {

    setIsLoading(false);
  }
};
  return (
    <div className="min-h-screen bg-[#f4f6fb] overflow-hidden relative flex items-center justify-center font-sans">

      {/* BACKGROUND */}
      <div className="absolute inset-0 overflow-hidden">

        {/* soft gradients */}
        <div className="absolute top-[-10%] left-[10%] w-[700px] h-[700px] rounded-full bg-[#3563ff]/[0.06] blur-[140px]" />

        <div className="absolute bottom-[-20%] right-[5%] w-[600px] h-[600px] rounded-full bg-[#3563ff]/[0.04] blur-[120px]" />

        {/* subtle beam */}
        <div className="absolute top-[30%] left-[-10%] w-[1200px] h-[180px] rotate-[12deg] bg-[#3563ff]/[0.04] blur-3xl" />

        {/* texture */}
        <div className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_center,#3563ff_1px,transparent_1px)] bg-[length:24px_24px]" />
      </div>

      {/* MAIN CARD */}
      <div className="relative w-[1360px] h-[760px] rounded-[28px] overflow-hidden bg-white border border-black/[0.04] shadow-[0_40px_120px_rgba(0,0,0,0.08)] flex">

        {/* LEFT PANEL */}
        <div className="w-[48%] bg-[#fbfcff] relative px-14 py-10 flex flex-col border-r border-black/[0.04]">



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
              <h1 className="text-[#111827] text-[32px] font-semibold mb-2 tracking-[-0.03em]">

                Join Workspace
              </h1>

              <p className="text-gray-500 text-[13px] mb-10 leading-7">

                You've been invited to collaborate inside
                an OpsSight workspace built for monitoring,
                validating, and managing production AI
                systems.
              </p>

              {/* INVITE BADGE */}
              <div className="mb-8 inline-flex w-fit items-center gap-3 rounded-2xl border border-black/[0.04] bg-[#f7f8fc] px-4 py-3">

                <div className="w-2 h-2 rounded-full bg-[#3563ff]" />

                <span className="text-[12px] text-gray-600">
                  Invitation Verified
                </span>
              </div>

              {/* FORM */}
              <form
                onSubmit={handleAcceptInvite}
                className="space-y-5"
              >

                {/* PASSWORD */}
                <div>

                  <label className="block text-[12px] text-gray-500 mb-3">

                    Create Password
                  </label>

                  <div className="relative">

                    <input
                      type={
                        showPassword
                          ? "text"
                          : "password"
                      }
                      value={password}
                      onChange={(e) =>
                        setPassword(e.target.value)
                      }
                      placeholder="Create secure password"
                      className="w-full h-[54px] px-5 rounded-2xl bg-[#f7f8fc] border border-black/[0.05] outline-none text-[14px] text-[#111827] placeholder:text-gray-400 focus:border-[#3563ff]/40 focus:bg-white transition"
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowPassword(!showPassword)
                      }
                      className="absolute right-5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#111827]"
                    >

                      {showPassword
                        ? <EyeOff size={16} />
                        : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* CONFIRM PASSWORD */}
                <div>

                  <label className="block text-[12px] text-gray-500 mb-3">

                    Confirm Password
                  </label>

                  <div className="relative">

                    <input
                      type={
                        showConfirmPassword
                          ? "text"
                          : "password"
                      }
                      value={confirmPassword}
                      onChange={(e) =>
                        setConfirmPassword(
                          e.target.value
                        )
                      }
                      placeholder="Confirm password"
                      className="w-full h-[54px] px-5 rounded-2xl bg-[#f7f8fc] border border-black/[0.05] outline-none text-[14px] text-[#111827] placeholder:text-gray-400 focus:border-[#3563ff]/40 focus:bg-white transition"
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(
                          !showConfirmPassword
                        )
                      }
                      className="absolute right-5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#111827]"
                    >

                      {showConfirmPassword
                        ? <EyeOff size={16} />
                        : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* SUBMIT */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-[54px] rounded-2xl bg-[#3563ff] hover:bg-[#2957f5] transition text-white text-[14px] font-medium shadow-[0_0_40px_rgba(53,99,255,0.22)] disabled:opacity-50"
                >

                  {isLoading
                    ? "Accessing Workspace..."
                    : "Access Workspace"}
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="flex-1 relative overflow-hidden bg-[#f7f9fd]">

          {/* textures */}
          <div className="absolute inset-0 overflow-hidden">

            <div className="absolute bottom-[-10%] left-[5%] w-[700px] h-[700px] rounded-full bg-[#3563ff]/[0.06] blur-[140px]" />

            <div className="absolute top-[25%] right-[-10%] w-[1000px] h-[220px] rotate-[16deg] bg-[#3563ff]/[0.04] blur-3xl" />

            {/* faded text */}
            <div className="absolute bottom-[10%] right-[10%] text-right text-[11px] leading-8 tracking-[0.35em] uppercase text-[#111827]/[0.05]">

              SECURE ACCESS
              <br />

              TEAM COLLABORATION
              <br />

              MODEL OPERATIONS
              <br />

              AI GOVERNANCE
              <br />

              WORKSPACE SECURITY
            </div>
          </div>

          {/* content */}
          <div className="relative z-10 h-full flex flex-col justify-center px-20">

            {/* label */}
            <div className="mb-10">

              <span className="text-[10px] tracking-[0.4em] uppercase text-gray-400">

                Invitation Access
              </span>
            </div>

            {/* heading */}
            <div className="relative">

              <h2 className="text-[96px] leading-[0.88] font-semibold tracking-[-0.08em] text-[#111827]">

                Join
                <br />

                Your AI
                <br />

                Workspace
              </h2>

              {/* faded word */}
              <div className="absolute rotate-[-10deg] -bottom-3 left-[38%] text-[180px] font-bold tracking-[-0.1em] text-[#111827]/[0.03] select-none">

                Team
              </div>
            </div>

            {/* desc */}
            <p className="mt-10 max-w-[520px] text-[15px] leading-8 text-gray-500">

              Accept your invitation and securely access
              your organization’s collaborative MLOps
              environment powered by OpsSight.
            </p>

            {/* bottom line */}
            <div className="mt-16 flex items-center gap-4">

              <span className="text-[11px] tracking-[0.3em] uppercase text-gray-400">

                Secure Workspace Access
              </span>

              <div className="h-px w-[180px] bg-gradient-to-r from-black/[0.08] to-transparent" />

              <div className="w-2 h-2 rounded-full bg-[#3563ff] animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
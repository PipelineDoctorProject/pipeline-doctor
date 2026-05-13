import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";

import { useState, useEffect } from "react";
import useAuthStore from "../../store/authStore";

import Logo from "../../assets/logo_og.png";
import { useNavigate } from "react-router-dom";

export default function OnboardingPage() {
  const navigate = useNavigate()
  const createCompany = useAuthStore(
    (state) => state.createCompany
  );

  const inviteMember = useAuthStore(
    (state) => state.inviteMember
  );

  const workspace = useAuthStore(
  (state) => state.workspace
);

const [step, setStep] = useState(
  workspace?.tenant_id ? 2 : 1
);

  const [companyName, setCompanyName] = useState("");

  const [memberEmail, setMemberEmail] = useState("");

  const [members, setMembers] = useState([]);

  const [isLoading, setIsLoading] = useState(false);

  const handleCreateCompany = async (e) => {

    e.preventDefault();

    if (!companyName.trim()) return;

    setIsLoading(true);

    try {

      await createCompany(companyName);

      setStep(2);

    } catch (err) {

      alert(err?.detail || "Company Creation Failed");

    } finally {

      setIsLoading(false);
    }
  };

  useEffect(() => {

  if (workspace?.tenant_id) {
    setStep(2);
  }

}, [workspace]);
  
  const handleAddMember = () => {

  if (!memberEmail.trim()) return;

  if (members.includes(memberEmail)) return;

  setMembers([...members, memberEmail]);

  setMemberEmail("");
};

  const handleRemoveMember = (email) => {

    setMembers(
      members.filter((member) => member !== email)
    );
  };

  const handleFinish = async () => {

  try {

    for (const email of members) {

      await inviteMember(email);
    }

    console.log("Invited Members:", members);

    navigate("/dashboard", { replace: true });

  } catch (err) {

    alert(err?.detail || "Invite Failed");
  }
};

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#07090d] font-sans text-white">

      {/* BACKGROUND */}
      <div className="absolute inset-0 overflow-hidden">

        <div className="absolute top-[-10%] left-[20%] w-[700px] h-[700px] rounded-full bg-white/[0.025] blur-[160px]" />

        <div className="absolute bottom-[-20%] right-[10%] w-[600px] h-[600px] rounded-full bg-white/[0.02] blur-[140px]" />

        <div className="absolute top-[35%] left-[-10%] w-[1200px] h-[180px] rotate-[10deg] bg-white/[0.02] blur-3xl" />

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent,rgba(0,0,0,0.78))]" />
      </div>

      {/* LOGO */}
      <div className="absolute top-10 left-10 z-20">

        <img
          src={Logo}
          alt="OpsSight Logo"
          className="w-[145px] object-contain opacity-90"
        />
      </div>

      {/* MAIN */}
      <div className="relative z-10 flex min-h-screen items-center justify-center px-6">

        <div className="w-full max-w-[760px]">

          {/* PROGRESS */}
          <div className="mb-14">

            <div className="flex items-center justify-between mb-4">

              <span className="text-[11px] tracking-[0.3em] text-gray-600 uppercase">
                Workspace Setup
              </span>

              <span className="text-[11px] text-gray-700">
                Step {step} Of 2
              </span>
            </div>

            <div className="h-px w-full bg-white/[0.05]">

              <div
                className={`h-full bg-white/[0.18] transition-all duration-500 ${
                  step === 1
                    ? "w-1/2"
                    : "w-full"
                }`}
              />
            </div>
          </div>

          {/* CONTENT */}
          <div className="relative">

            <div className="absolute -top-20 left-1/2 -translate-x-1/2 text-[220px] tracking-[-0.12em] font-semibold text-white/[0.02] select-none pointer-events-none">

              OPS
            </div>

            <div className="relative z-10 text-center">

              {/* STEP 1 */}
              {step === 1 && (
                <>
                  <h1 className="text-[72px] leading-[0.92] tracking-[-0.08em] font-semibold text-white">

                    Create Your
                    <br />

                    AI Workspace
                  </h1>

                  <p className="mt-8 max-w-[560px] mx-auto text-[15px] leading-8 text-gray-500">

                    Set up your organization workspace to monitor
                    production ML systems, validate incoming data,
                    detect model drift, and maintain operational
                    reliability across your infrastructure.
                  </p>

                  <form
                    onSubmit={handleCreateCompany}
                    className="mt-16"
                  >

                    <div className="relative max-w-[540px] mx-auto">

                      <div className="absolute inset-0 bg-black/30 blur-3xl scale-110" />

                      <div className="relative bg-white/[0.03] px-8 py-8">

                        <label className="block text-left text-[11px] tracking-[0.25em] uppercase text-gray-600 mb-5">

                          Organization Name
                        </label>

                        <input
                          type="text"
                          placeholder="Enter Workspace Name"
                          value={companyName}
                          onChange={(e) =>
                            setCompanyName(e.target.value)
                          }
                          className="w-full h-[72px] bg-transparent border-b border-white/[0.08] text-white text-[22px] placeholder:text-gray-700 outline-none focus:border-white/[0.18] transition"
                        />

                        <div className="mt-10 flex items-center justify-between">

                          <p className="text-[11px] leading-6 text-gray-700 uppercase tracking-[0.2em]">

                            Continue To Team Setup
                          </p>

                          <button
                            type="submit"
                            disabled={isLoading}
                            className="group flex items-center gap-4 text-[12px] tracking-[0.25em] uppercase text-white"
                          >

                            <div className="h-px w-10 bg-white/20 transition-all duration-300 group-hover:w-16" />

                            {isLoading
                              ? "Creating"
                              : "Continue"}
                          </button>
                        </div>
                      </div>
                    </div>
                  </form>
                </>
              )}

              {/* STEP 2 */}
              {step === 2 && (
                <>
                  <h1 className="text-[68px] leading-[0.92] tracking-[-0.08em] font-semibold text-white">

                    Invite Your
                    <br />

                    Team Members
                  </h1>

                  <p className="mt-8 max-w-[560px] mx-auto text-[15px] leading-8 text-gray-500">

                    Collaborate with engineers, analysts, and ML teams
                    inside a unified operational workspace built for
                    production AI systems.
                  </p>

                  <div className="mt-16 relative max-w-[540px] mx-auto">

                    <div className="absolute inset-0 bg-black/30 blur-3xl scale-110" />

                    <div className="relative bg-white/[0.03] px-8 py-8">

                      <label className="block text-left text-[11px] tracking-[0.25em] uppercase text-gray-600 mb-5">

                        Team Email Address
                      </label>

                      <div className="flex items-center gap-4">

                        <input
                          type="email"
                          placeholder="Enter Team Member Email"
                          value={memberEmail}
                          onChange={(e) =>
                            setMemberEmail(e.target.value)
                          }
                          className="flex-1 h-[68px] bg-transparent border-b border-white/[0.08] text-white text-[18px] placeholder:text-gray-700 outline-none focus:border-white/[0.18] transition"
                        />

                        <button
                          type="button"
                          onClick={handleAddMember}
                          className="h-[48px] px-5 border border-white/[0.08] text-[11px] uppercase tracking-[0.25em] text-white hover:bg-white/[0.04] transition"
                        >
                          Add
                        </button>
                      </div>

                      <div className="mt-8 flex flex-wrap gap-3">

                        {members.map((email) => (
                          <div
                            key={email}
                            className="flex items-center gap-3 bg-white/[0.04] border border-white/[0.05] px-4 py-3"
                          >

                            <span className="text-[13px] text-gray-300">
                              {email}
                            </span>

                            <button
                              type="button"
                              onClick={() =>
                                handleRemoveMember(email)
                              }
                              className="text-gray-500 hover:text-white transition"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>

                      <div className="mt-12 flex items-center justify-between">

                        <button
                          type="button"
                          onClick={()=> navigate("/dashboard",{replace: true})}
                          className="text-[11px] tracking-[0.25em] uppercase text-gray-600 hover:text-white transition"
                        >
                          Skip For Now
                        </button>

                        <button
                          type="button"
                          onClick={handleFinish}
                          className="group flex items-center gap-4 text-[12px] tracking-[0.25em] uppercase text-white"
                        >

                          <div className="h-px w-10 bg-white/20 transition-all duration-300 group-hover:w-16" />

                          Finish Setup
                        </button>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* FOOTER */}
          <div className="mt-20 flex items-center justify-between">

            <div className="flex items-center gap-4">

              <div className="w-2 h-2 rounded-full bg-white/30 animate-pulse" />

              <div className="h-px w-[120px] bg-gradient-to-r from-white/[0.12] to-transparent" />

              <span className="text-[10px] tracking-[0.35em] uppercase text-gray-700">

                Production Infrastructure Ready
              </span>
            </div>

            <div className="text-right text-[10px] leading-7 tracking-[0.35em] uppercase text-white/[0.04]">

              DATA QUALITY<br />
              DRIFT DETECTION<br />
              OBSERVABILITY
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
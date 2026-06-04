import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";

import { useState, useEffect, useRef } from "react";
import useAuthStore from "../../store/authStore";

import Logo2 from "../../assets/logo2.png";
import { useNavigate, useSearchParams } from "react-router-dom";

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const createCompany = useAuthStore((state) => state.createCompany);

  const inviteMember = useAuthStore((state) => state.inviteMember);

  const workspace = useAuthStore((state) => state.workspace);

  const inviteStepRequested = searchParams.get("step") === "invite";
  const [step, setStep] = useState(inviteStepRequested ? 2 : 1);

  const [companyName, setCompanyName] = useState("");

  const [memberEmail, setMemberEmail] = useState("");

  const [members, setMembers] = useState([]);

  const [isLoading, setIsLoading] = useState(false);
  const [isStepTransitioning, setIsStepTransitioning] = useState(false);
  const transitionTimerRef = useRef(null);

  useEffect(() => {
    setStep(inviteStepRequested ? 2 : 1);
  }, [inviteStepRequested]);

  useEffect(() => {
    if (step !== 2) {
      setIsStepTransitioning(false);
      return;
    }

    setIsStepTransitioning(true);
    transitionTimerRef.current = window.setTimeout(() => {
      setIsStepTransitioning(false);
      transitionTimerRef.current = null;
    }, 600);
  }, [step]);

  useEffect(() => {
    return () => {
      if (transitionTimerRef.current) {
        window.clearTimeout(transitionTimerRef.current);
      }
    };
  }, []);

  const handleCreateCompany = async () => {

    if (!companyName.trim()) return;

    setIsLoading(true);

    try {
      await createCompany(companyName);
      navigate("/onboarding?step=invite", { replace: true });
    } catch (err) {
      alert(err?.detail || "Company Creation Failed");
    } finally {
      setIsLoading(false);
    }
  };

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
    if (isStepTransitioning) return;

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
    <div className="min-h-screen bg-[#ffffff] overflow-hidden">
      {/* BACKGROUND */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[10%] right-[-10%] w-[600px] h-[600px] rounded-full bg-[#3563ff]/[0.05] blur-[140px]" />

        <div className="absolute bottom-[-20%] left-[-10%] w-[700px] h-[700px] rounded-full bg-[#7c3aed]/[0.04] blur-[140px]" />

        <div className="absolute inset-0 opacity-[0.025] bg-[linear-gradient(to_right,rgba(15,23,42,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.08)_1px,transparent_1px)] bg-[size:42px_42px]" />
      </div>

      {/* LOGO */}
      <div className="absolute top-10 left-10 z-20">
        <img
          src={Logo2}
          alt="OpsSight Logo"
          className="w-[150px] object-contain"
        />
      </div>

      {/* MAIN */}
      <div className="relative z-10 flex min-h-screen items-center justify-center px-6 py-20">
        <div className="w-full max-w-[760px]">

          {/* PROGRESS */}
          <div className="mb-14">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-[11px] font-medium uppercase tracking-[0.12em] text-[#6b7280]">
                Workspace Setup
              </span>

              <span className="text-[11px] text-[#9ca3af]">
                Step {step} Of 2
              </span>
            </div>

            <div className="h-[6px] overflow-hidden rounded-full bg-[#eef2ff]">
              <div
                className={`h-full rounded-full bg-[#3563ff] transition-all duration-500 ${
                  step === 1 ? "w-1/2" : "w-full"
                }`}
              />
            </div>
          </div>

          {/* CARD */}
          <div className="rounded-[24px] border border-black/[0.05] bg-white p-12 shadow-[0_20px_80px_rgba(15,23,42,0.06)]">

            {/* STEP 1 */}
            {step === 1 && (
              <>
                <div className="text-center">
                  <h1 className="text-[48px] font-semibold tracking-[-0.06em] text-[#111827]">
                    Create Your
                    &nbsp;
                    Workspace
                  </h1>

                  <p className="mx-auto mt-6 max-w-[560px] text-[15px] leading-8 text-[#6b7280]">
                    Set up your organization workspace to monitor production ML
                    systems, validate incoming data, detect drift, and maintain
                    operational reliability.
                  </p>
                </div>

                <div className="mt-14">
                  <div className="space-y-6">
                    <div>
                      <label className="mb-3 block text-[12px] font-medium text-[#6b7280]">
                        Organization Name
                      </label>

                      <input
                        type="text"
                        placeholder="Enter Workspace Name"
                        value={companyName}
                        onChange={(e) =>
                          setCompanyName(e.target.value)
                        }
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            event.preventDefault();
                            handleCreateCompany();
                          }
                        }}
                        className="h-[56px] w-full rounded-[14px] border border-[#e5e7eb] bg-[#fafafa] px-5 text-[15px] text-[#111827] outline-none transition focus:border-[#3563ff] focus:bg-white"
                      />
                    </div>

                    <div className="flex items-center justify-between pt-4">
                      <p className="text-[12px] text-[#9ca3af]">
                        Continue to team setup
                      </p>

                      <button
                        type="button"
                        onClick={handleCreateCompany}
                        disabled={isLoading}
                        className="h-[50px] rounded-[14px] bg-[#3563ff] px-6 text-[14px] font-medium text-white transition hover:bg-[#2957f5] disabled:opacity-50"
                      >
                        {isLoading
                          ? "Creating..."
                          : "Continue"}
                      </button>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* STEP 2 */}
            {step === 2 && (
              <>
                <div className="text-center">
                  <h1 className="text-[48px] font-semibold tracking-[-0.05em] text-[#111827]">
                    Invite Your
                    <br />
                    Team Members
                  </h1>

                  <p className="mx-auto mt-6 max-w-[560px] text-[15px] leading-8 text-[#6b7280]">
                    Collaborate with engineers, analysts, and ML teams inside a
                    unified operational workspace.
                  </p>
                </div>

                <div className="mt-14 space-y-6">
                  <div>
                    <label className="mb-3 block text-[12px] font-medium text-[#6b7280]">
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
                        className="h-[56px] flex-1 rounded-[14px] border border-[#e5e7eb] bg-[#fafafa] px-5 text-[15px] text-[#111827] outline-none transition focus:border-[#3563ff] focus:bg-white"
                      />

                      <button
                        type="button"
                        onClick={handleAddMember}
                        className="h-[56px] rounded-[14px] border border-[#dbe1ea] bg-white px-6 text-[13px] font-medium text-[#111827] transition hover:bg-[#f8fafc]"
                      >
                        Add
                      </button>
                    </div>
                  </div>

                  {/* MEMBERS */}
                  {members.length > 0 && (
                    <div className="flex flex-wrap gap-3">
                      {members.map((email) => (
                        <div
                          key={email}
                          className="flex items-center gap-3 rounded-[12px] border border-[#e5e7eb] bg-[#f8fafc] px-4 py-3"
                        >
                          <span className="text-[13px] text-[#374151]">
                            {email}
                          </span>

                          <button
                            type="button"
                            onClick={() =>
                              handleRemoveMember(email)
                            }
                            className="text-[#9ca3af] transition hover:text-red-500"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* ACTIONS */}
                  <div className="flex items-center justify-between pt-6">
                      <button
                        type="button"
                        onClick={() =>
                          navigate("/dashboard")
                        }
                        disabled={isStepTransitioning}
                        className="text-[13px] font-medium text-[#6b7280] transition hover:text-[#111827]"
                      >
                        Skip For Now
                      </button>

                      <button
                        type="button"
                        onClick={handleFinish}
                        disabled={isStepTransitioning}
                        className="h-[50px] rounded-[14px] bg-[#3563ff] px-6 text-[14px] font-medium text-white transition hover:bg-[#2957f5] disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Finish Setup
                      </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* FOOTER */}
          <div className="mt-10 flex items-center justify-center gap-3">
            <div className="h-2 w-2 rounded-full bg-[#3563ff]" />

            <span className="text-[11px] uppercase tracking-[0.12em] text-[#9ca3af]">
              Production Infrastructure Ready
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

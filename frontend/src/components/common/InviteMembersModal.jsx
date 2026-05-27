import { useMemo, useState } from "react";
import { MailPlus, Send, UserPlus, X } from "lucide-react";
import toast from "react-hot-toast";

import useAuthStore from "../../store/authStore";

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export default function InviteMembersModal({ isOpen, onClose }) {
  const inviteMember = useAuthStore((state) => state.inviteMember);
  const [emailInput, setEmailInput] = useState("");
  const [members, setMembers] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const normalizedMembers = useMemo(
    () => members.map((email) => email.toLowerCase()),
    [members],
  );

  if (!isOpen) return null;

  const resetState = () => {
    setEmailInput("");
    setMembers([]);
    setIsSubmitting(false);
  };

  const handleClose = () => {
    if (isSubmitting) return;
    resetState();
    onClose();
  };

  const addMember = () => {
    const nextEmail = emailInput.trim().toLowerCase();

    if (!nextEmail) return;

    if (!isValidEmail(nextEmail)) {
      toast.error("Enter a valid email address.");
      return;
    }

    if (normalizedMembers.includes(nextEmail)) {
      toast.error("That member is already in the invite list.");
      return;
    }

    setMembers((current) => [...current, nextEmail]);
    setEmailInput("");
  };

  const removeMember = (email) => {
    if (isSubmitting) return;
    setMembers((current) => current.filter((item) => item !== email));
  };

  const handleSubmit = async () => {
    if (members.length === 0) {
      toast.error("Add at least one member email first.");
      return;
    }

    setIsSubmitting(true);

    try {
      for (const email of members) {
        await inviteMember(email);
      }

      toast.success(
        `${members.length} invitation${members.length === 1 ? "" : "s"} sent.`,
      );
      handleClose();
    } catch (error) {
      toast.error(error?.detail || "Failed to send member invitations.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4 backdrop-blur-sm">
      <button
        type="button"
        aria-label="Close invite members modal"
        className="absolute inset-0 cursor-default"
        onClick={handleClose}
      />

      <div className="relative w-full max-w-[640px] overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.18)]">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-2xl border border-blue-100 bg-blue-50 text-blue-700">
              <UserPlus size={20} />
            </div>
            <h2 className="text-[22px] font-semibold text-slate-950">Invite members</h2>
            <p className="mt-1 max-w-[460px] text-[13px] leading-6 text-slate-500">
              Invite teammates into this workspace as members. They will receive an
              email with a secure invite link to finish account setup.
            </p>
          </div>

          <button
            type="button"
            onClick={handleClose}
            className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
          >
            <X size={16} />
          </button>
        </div>

        <div className="space-y-6 px-6 py-6">
          <div>
            <label className="mb-3 block text-[12px] font-medium uppercase tracking-[0.08em] text-slate-500">
              Member email
            </label>
            <div className="flex items-center gap-3">
              <div className="flex h-12 flex-1 items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4">
                <MailPlus size={16} className="shrink-0 text-slate-400" />
                <input
                  type="email"
                  value={emailInput}
                  onChange={(event) => setEmailInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      addMember();
                    }
                  }}
                  placeholder="Enter teammate email"
                  className="h-full min-w-0 flex-1 bg-transparent text-[14px] text-slate-800 outline-none placeholder:text-slate-400"
                />
              </div>

              <button
                type="button"
                onClick={addMember}
                className="inline-flex h-12 items-center justify-center rounded-2xl border border-slate-200 bg-white px-5 text-[13px] font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Add
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-[13px] font-semibold text-slate-900">Invite queue</p>
              <span className="text-[12px] text-slate-500">
                {members.length} member{members.length === 1 ? "" : "s"}
              </span>
            </div>

            {members.length === 0 ? (
              <p className="text-[13px] leading-6 text-slate-500">
                Add one or more email addresses to send invites after login.
              </p>
            ) : (
              <div className="flex flex-wrap gap-3">
                {members.map((email) => (
                  <div
                    key={email}
                    className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-[13px] text-slate-700"
                  >
                    <span>{email}</span>
                    <button
                      type="button"
                      onClick={() => removeMember(email)}
                      className="text-slate-400 transition hover:text-red-500"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-6 py-4">
          <p className="text-[12px] leading-5 text-slate-500">
            Only workspace admins can send invites.
          </p>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="inline-flex h-11 items-center justify-center rounded-2xl border border-slate-200 bg-white px-5 text-[13px] font-semibold text-slate-700 transition hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl bg-blue-600 px-5 text-[13px] font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Send size={14} />
              {isSubmitting ? "Sending..." : "Send invites"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

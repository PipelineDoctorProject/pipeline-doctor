import { Loader2 } from "lucide-react";

export default function LoadingScreen() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#f8fafc]">
      <Loader2 className="h-10 w-10 animate-spin text-[#111827]" />
      <p className="mt-4 text-[14px] font-medium text-gray-500 tracking-wide uppercase">
        Loading...
      </p>
    </div>
  );
}

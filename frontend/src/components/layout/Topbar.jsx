// components/layout/Topbar.jsx

import { Bell, Search, ChevronDown } from "lucide-react";
import useDashboard from "../../hooks/useDashboard";

export default function Topbar() {
  const { dashboardData, loading } = useDashboard();

  // const user = dashboardData?.user
  const workspace = dashboardData?.workspace;
  console.log(workspace);
  
  return (
    <header className="flex h-[80px] items-center justify-between border-b border-black/[0.05] bg-white/80 px-8 backdrop-blur-xl">
      {/* LEFT */}
      <div></div>

      {/* RIGHT */}
      <div className="flex items-center gap-4">
        {/* SEARCH */}
        <div className="relative">
          <Search
            size={16}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
          />

          <input
            type="text"
            placeholder="Search..."
            className="h-[46px] w-[260px] rounded-2xl border border-black/[0.05] bg-[#f7f8fb] pl-11 pr-4 text-[14px] text-[#111827] outline-none placeholder:text-gray-400 focus:border-[#3563ff]/30"
          />
        </div>

        {/* NOTIFICATIONS */}
        <button className="relative flex h-[46px] w-[46px] items-center justify-center rounded-2xl border border-black/[0.05] bg-[#f7f8fb] text-gray-500 transition hover:text-[#111827]">
          <Bell size={18} />

          <div className="absolute right-3 top-3 h-2 w-2 rounded-full bg-[#3563ff]" />
        </button>

        {/* PROFILE */}
        <button className="flex items-center gap-3 rounded-2xl border border-black/[0.05] bg-[#f7f8fb] px-4 py-2 transition hover:bg-white">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#3563ff] text-[13px] font-semibold text-white">
            S
          </div>

          <div className="text-left">
            <p className="text-[13px] font-medium text-[#111827]">{workspace?.workspace_name}</p>

            <p className="text-[11px] text-gray-500">Workspace Admin</p>
          </div>

          <ChevronDown size={16} className="text-gray-400" />
        </button>
      </div>
    </header>
  );
}

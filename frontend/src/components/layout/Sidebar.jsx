// components/layout/Sidebar.jsx

import {
  LayoutDashboard,
  Database,
  Activity,
  AlertTriangle,
  FileCode2,
  Workflow,
  Settings,
  Brain,
} from "lucide-react";

import { NavLink } from "react-router-dom";

import Logo from "../../assets/logo_og.png";
import Logo2 from "../../assets/logo2.png";

const navItems = [
  {
    label: "Overview",
    icon: LayoutDashboard,
    path: "/dashboard",
  },
  {
    label: "Pipelines",
    icon: Workflow,
    path: "/pipelines",
  },
  {
    label: "ML Models",
    icon: Brain,
    path: "/models",
  },
  {
    label: "Data Quality",
    icon: Database,
    path: "/data-quality",
  },
  {
    label: "Drift Detection",
    icon: Activity,
    path: "/drift",
  },
  {
    label: "Incidents",
    icon: AlertTriangle,
    path: "/incidents",
  },
  {
    label: "Schemas",
    icon: FileCode2,
    path: "/schemas",
  },
];

export default function Sidebar() {
  return (
    <aside className="flex h-full w-[270px] flex-col border-r border-black/[0.05] bg-white">
      {/* LOGO */}
      <div className="flex h-[80px] items-center border-b border-black/[0.04] px-8">
        <img
          src={Logo2}
          alt="OpsSight Logo"
          className="w-[130px] object-contain"
        />
      </div>

      {/* NAVIGATION */}
      <div className="flex-1 px-4 py-6">
        <div className="mb-4 px-4 text-[11px] font-medium uppercase tracking-[0.28em] text-gray-400">
          Workspace
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-4 rounded-2xl px-4 py-3 text-[14px] font-medium transition ${
                    isActive
                      ? "bg-gray-700 text-white shadow-[0_0_30px_rgba(53,99,255,0.18)]"
                      : "text-gray-500 hover:bg-[#f3f5fb] hover:text-[#111827]"
                  }`
                }
              >
                <Icon size={18} />

                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* FOOTER */}
      <div className="border-t border-black/[0.04] p-4">
        <button className="flex w-full items-center gap-4 rounded-2xl px-4 py-3 text-[14px] font-medium text-gray-500 transition hover:bg-[#f3f5fb] hover:text-[#111827]">
          <Settings size={18} />
          Settings
        </button>
      </div>
    </aside>
  );
}

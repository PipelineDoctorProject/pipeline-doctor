// components/layout/Sidebar.jsx

import {
  LayoutDashboard,
  Database,
  Activity,
  AlertTriangle,
  FileCode2,
  Workflow,
  Brain,
  LogOut,
} from "lucide-react";

import { NavLink } from "react-router-dom";
import useAuthStore from "../../store/authStore";
import Logo2 from "../../assets/logo2.png";

function SlackNavIcon({ size = 18, ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      {...props}
    >
      <path
        d="M9.75 2.75A2.75 2.75 0 1 0 4.25 2.75V8.5H9.75V2.75Z"
        fill="currentColor"
      />
      <path
        d="M12 2.75A2.75 2.75 0 1 1 17.5 2.75V8.5H12V2.75Z"
        fill="currentColor"
        opacity="0.7"
      />
      <path
        d="M21.25 9.75A2.75 2.75 0 1 0 21.25 4.25H15.5V9.75H21.25Z"
        fill="currentColor"
      />
      <path
        d="M21.25 12A2.75 2.75 0 1 1 21.25 17.5H15.5V12H21.25Z"
        fill="currentColor"
        opacity="0.7"
      />
      <path
        d="M14.25 21.25A2.75 2.75 0 1 0 19.75 21.25V15.5H14.25V21.25Z"
        fill="currentColor"
      />
      <path
        d="M12 21.25A2.75 2.75 0 1 1 6.5 21.25V15.5H12V21.25Z"
        fill="currentColor"
        opacity="0.7"
      />
      <path
        d="M2.75 14.25A2.75 2.75 0 1 0 2.75 19.75H8.5V14.25H2.75Z"
        fill="currentColor"
      />
      <path
        d="M2.75 12A2.75 2.75 0 1 1 2.75 6.5H8.5V12H2.75Z"
        fill="currentColor"
        opacity="0.7"
      />
    </svg>
  );
}

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
  {
    label: "Slack",
    icon: SlackNavIcon,
    path: "/integrations/slack",
  },
];

export default function Sidebar() {
    const logOut = useAuthStore((state) => state.logout);

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
        <button onClick={()=> logOut()} className="flex w-full items-center gap-4 rounded-2xl px-4 py-3 text-[14px] font-medium text-gray-500 transition hover:bg-[#f3f5fb] hover:text-[#111827]">
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  );
}

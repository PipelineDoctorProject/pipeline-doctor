// layouts/AppLayout.jsx

import { Outlet } from "react-router-dom";

import Sidebar from "../components/layout/Sidebar";
import Topbar from "../components/layout/Topbar";

export default function AppLayout() {

  return (

    <div className="ops-theme-navy flex h-screen overflow-hidden bg-[#f3f6fb]">

      <Sidebar />

      <div className="flex flex-1 flex-col overflow-hidden">

        <Topbar />

        <main className="flex-1 overflow-y-auto px-8 py-7">

          <div className="mx-auto w-full max-w-[1440px]">

            <Outlet />

          </div>

        </main>
      </div>
    </div>
  );
}

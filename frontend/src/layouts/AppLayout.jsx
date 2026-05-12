// layouts/AppLayout.jsx

import { Outlet } from "react-router-dom";

import Sidebar from "../components/layout/Sidebar";
import Topbar from "../components/layout/Topbar";

export default function AppLayout() {

  return (

    <div className="flex h-screen overflow-hidden bg-[#f7f8fb]">

      <Sidebar />

      <div className="flex flex-1 flex-col overflow-hidden">

        <Topbar />

        <main className="flex-1 overflow-y-auto p-8">

          <Outlet />

        </main>
      </div>
    </div>
  );
}
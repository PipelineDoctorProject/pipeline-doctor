import { useState } from "react";



export default function SchemaPage() {
  const [selectedBaseline, setSelectedBaseline] = useState(null);

  const baselines = [
    {
      id: 26,
      model_id: 1,
      version: 1,
      status: "approved",
      is_active: false,
      created_at: "2026-05-10 15:08",
      schema_count: 12,
    },
    {
      id: 27,
      model_id: 1,
      version: 2,
      status: "approved",
      is_active: true,
      created_at: "2026-05-10 15:13",
      schema_count: 14,
    },
    {
      id: 28,
      model_id: 2,
      version: 1,
      status: "approved",
      is_active: true,
      created_at: "2026-05-11 04:45",
      schema_count: 8,
    },
    {
      id: 29,
      model_id: 2,
      version: 2,
      status: "draft",
      is_active: false,
      created_at: "2026-05-11 04:50",
      schema_count: 10,
    },
  ];

  const schemaColumns = [
    {
      name: "customer_id",
      dtype: "integer",
      nullable: false,
      unique: true,
      status: "Validated",
    },
    {
      name: "age",
      dtype: "integer",
      nullable: false,
      unique: false,
      status: "Validated",
    },
    {
      name: "monthly_income",
      dtype: "float",
      nullable: false,
      unique: false,
      status: "Validated",
    },
    {
      name: "employment_type",
      dtype: "string",
      nullable: true,
      unique: false,
      status: "Validated",
    },
    {
      name: "loan_default",
      dtype: "boolean",
      nullable: false,
      unique: false,
      status: "Target",
    },
  ];

  return (
    <div className="space-y-8">
      {/* TOP HEADER */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          

          <h1 className="text-[34px] font-semibold tracking-[-0.05em] text-[#111827]">
            Baseline Schema
          </h1>

          <p className="mt-2 max-w-[760px] text-[14px] leading-7 text-gray-500">
            Upload and manage your baseline/reference dataset schema for data
            quality validation, schema evolution detection, drift monitoring,
            and production observability.
          </p>
        </div>

        <div className="flex items-center gap-3">

          <button className="rounded-2xl bg-gray-700 px-5 py-3 text-[13px] font-medium text-white shadow-[0_10px_40px_rgba(17,24,39,0.12)] transition hover:bg-black">
            Upload Baseline CSV
          </button>
        </div>
      </div>

      {/* SUCCESS INFO */}
    

      
      {/* MAIN GRID */}
      <div className="relative flex gap-6 transition-all duration-300">
        {/* BASELINE TABLE */}
        <div
          className={`transition-all duration-300 ${
            selectedBaseline ? "w-[68%]" : "w-full"
          }`}
        >
          <div className="overflow-hidden rounded-[28px] border border-black/[0.05] bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-black/[0.05] px-7 py-6">
              <div>
                <h3 className="text-[22px] font-semibold tracking-[-0.04em] text-[#111827]">
                  Baseline Registry
                </h3>

                <p className="mt-1 text-[13px] text-gray-500">
                  Approved and draft baseline schema versions.
                </p>
              </div>

            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-black/[0.05] bg-[#fafafa] text-left">
                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                      ID
                    </th>

                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                      Model ID
                    </th>

                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                      Version
                    </th>

                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                      Columns
                    </th>

                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                      Status
                    </th>

                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                      Active
                    </th>

                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                      Created
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {baselines.map((baseline) => (
                    <tr
                      key={baseline.id}
                      onClick={() => setSelectedBaseline(baseline)}
                      className={`cursor-pointer border-b border-black/[0.04] transition hover:bg-[#fafafa] ${
                        selectedBaseline?.id === baseline.id
                          ? "bg-[#f8fafc]"
                          : ""
                      }`}
                    >
                      <td className="px-6 py-5 text-[13px] font-medium text-[#111827]">
                        {baseline.id}
                      </td>

                      <td className="px-6 py-5 text-[13px] text-gray-600">
                        {baseline.model_id}
                      </td>

                      <td className="px-6 py-5">
                        <div className="inline-flex rounded-full border border-black/[0.06] bg-[#f8fafc] px-3 py-1 text-[12px] font-medium text-[#111827]">
                          v{baseline.version}
                        </div>
                      </td>

                      <td className="px-6 py-5 text-[13px] text-gray-600">
                        {baseline.schema_count} columns
                      </td>

                      <td className="px-6 py-5">
                        <div
                          className={`inline-flex rounded-full px-3 py-1 text-[12px] font-medium ${
                            baseline.status === "approved"
                              ? "bg-green-50 text-green-700"
                              : "bg-yellow-50 text-yellow-700"
                          }`}
                        >
                          {baseline.status}
                        </div>
                      </td>

                      <td className="px-6 py-5">
                        <div
                          className={`inline-flex rounded-full px-3 py-1 text-[12px] font-medium ${
                            baseline.is_active
                              ? "bg-[#eef2ff] text-[#3563ff]"
                              : "bg-gray-100 text-gray-500"
                          }`}
                        >
                          {baseline.is_active ? "TRUE" : "FALSE"}
                        </div>
                      </td>

                      <td className="px-6 py-5 text-[13px] text-gray-500">
                        {baseline.created_at}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* RIGHT DRAWER */}
        <div
          className={`fixed right-0 top-0 z-40 h-screen border-l border-black/[0.05] bg-white shadow-[-10px_0_60px_rgba(15,23,42,0.08)] transition-all duration-300 ${
            selectedBaseline
              ? "w-[32%] translate-x-0"
              : "w-[32%] translate-x-full"
          }`}
        >
          {selectedBaseline && (
            <div className="flex h-full flex-col overflow-hidden">
              <div className="flex items-start justify-between border-b border-black/[0.05] px-7 py-6">
                <div>
                  <div className="mb-3 inline-flex rounded-full border border-black/[0.05] bg-[#f8fafc] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-gray-500">
                    Baseline Details
                  </div>

                  <h2 className="text-[28px] font-semibold tracking-[-0.05em] text-[#111827]">
                    Baseline v{selectedBaseline.version}
                  </h2>

                  <p className="mt-2 text-[13px] leading-6 text-gray-500">
                    Schema profile, validation metadata, and baseline structure.
                  </p>
                </div>

                <button
                  onClick={() => setSelectedBaseline(null)}
                  className="flex h-10 w-10 items-center justify-center rounded-xl border border-black/[0.05] bg-[#f8fafc] text-gray-500 transition hover:bg-[#eef2ff]"
                >
                  ✕
                </button>
              </div>

              <div className="flex-1 overflow-y-auto px-7 py-6">
                <div className="mb-6 grid grid-cols-2 gap-4">
                  <div className="rounded-2xl border border-black/[0.05] bg-[#f8fafc] p-5">
                    <div className="text-[11px] uppercase tracking-[0.18em] text-gray-400">
                      Model ID
                    </div>

                    <div className="mt-2 text-[24px] font-semibold text-[#111827]">
                      {selectedBaseline.model_id}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-black/[0.05] bg-[#f8fafc] p-5">
                    <div className="text-[11px] uppercase tracking-[0.18em] text-gray-400">
                      Schema Columns
                    </div>

                    <div className="mt-2 text-[24px] font-semibold text-[#111827]">
                      {selectedBaseline.schema_count}
                    </div>
                  </div>
                </div>

                <div className="overflow-hidden rounded-[24px] border border-black/[0.05] bg-white">
                  <div className="border-b border-black/[0.05] px-5 py-4">
                    <h3 className="text-[18px] font-semibold text-[#111827]">
                      Schema Columns
                    </h3>
                  </div>

                  <div className="overflow-hidden">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b border-black/[0.05] bg-[#fafafa] text-left">
                          <th className="px-5 py-3 text-[10px] uppercase tracking-[0.18em] text-gray-400">
                            Column
                          </th>

                          <th className="px-5 py-3 text-[10px] uppercase tracking-[0.18em] text-gray-400">
                            Type
                          </th>
                        </tr>
                      </thead>

                      <tbody>
                        {schemaColumns.map((column) => (
                          <tr
                            key={column.name}
                            className="border-b border-black/[0.04]"
                          >
                            <td className="px-5 py-4 text-[13px] font-medium text-[#111827]">
                              {column.name}
                            </td>

                            <td className="px-5 py-4 text-[13px] text-gray-500">
                              {column.dtype}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

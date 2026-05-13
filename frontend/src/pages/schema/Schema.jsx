import { useEffect, useState } from "react";

import UploadBaselineModal from "../schema/UploadBaselineModal";

import { getBaselines } from "../../store/baselineStorre";

export default function SchemaPage() {
  const [showUploadModal, setShowUploadModal] = useState(false);

  const [selectedBaseline, setSelectedBaseline] = useState(null);

  const [baselines, setBaselines] = useState([]);

  // ==========================================
  // LOAD BASELINES
  // ==========================================
  useEffect(() => {
    fetchBaselines();
  }, []);

  const fetchBaselines = async () => {
    try {
      const data = await getBaselines();

      setBaselines(data || []);
    } catch (err) {
      console.log(err);
    }
  };

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-[34px] font-semibold tracking-[-0.05em] text-[#111827]">
            Baseline Registry
          </h1>

          <p className="mt-2 max-w-[760px] text-[14px] leading-7 text-gray-500">
            Manage approved baseline schemas and production validation datasets.
          </p>
        </div>

        <button
          onClick={() => setShowUploadModal(true)}
          className="rounded-2xl bg-[#111827] px-5 py-3 text-[13px] font-medium text-white transition hover:bg-black"
        >
          Upload Baseline
        </button>
      </div>

      {/* TABLE + DRAWER */}
      {/* TABLE + DRAWER */}
      <div className="relative flex gap-0 transition-all duration-300">
        {/* TABLE */}
        <div
          className={`transition-all duration-300 ${
            selectedBaseline ? "w-[72%]" : "w-full"
          }`}
        >
          <div className="overflow-hidden rounded-[12px] border border-[#e5e7eb] bg-white">
            {/* HEADER */}
            <div className="flex items-center justify-between border-b border-[#f1f3f5] px-5 py-4">
              <div>
                <h3 className="text-[15px] font-semibold tracking-[-0.02em] text-[#111827]">
                  Baselines
                </h3>

                <p className="mt-0.5 text-[12px] text-[#6b7280]">
                  Production schema registry
                </p>
              </div>

              <button
                onClick={() => setShowUploadModal(true)}
                className="h-9 rounded-[10px] bg-[#111827] px-4 text-[12px] font-medium text-white transition hover:bg-black"
              >
                Upload
              </button>
            </div>

            {/* TABLE */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-[#f3f4f6] bg-[#fcfcfd]">
                    <th className="px-5 py-3 text-left text-[11px] font-medium uppercase tracking-[0.08em] text-[#9ca3af]">
                      Baseline
                    </th>

                    <th className="px-5 py-3 text-left text-[11px] font-medium uppercase tracking-[0.08em] text-[#9ca3af]">
                      Model
                    </th>

                    <th className="px-5 py-3 text-left text-[11px] font-medium uppercase tracking-[0.08em] text-[#9ca3af]">
                      Columns
                    </th>

                    <th className="px-5 py-3 text-left text-[11px] font-medium uppercase tracking-[0.08em] text-[#9ca3af]">
                      Status
                    </th>

                    <th className="px-5 py-3 text-left text-[11px] font-medium uppercase tracking-[0.08em] text-[#9ca3af]">
                      Created
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {baselines.map((baseline) => (
                    <tr
                      key={baseline.id}
                      onClick={() => setSelectedBaseline(baseline)}
                      className={`cursor-pointer border-b border-[#f3f4f6] transition-all hover:bg-[#fafafa] ${
                        selectedBaseline?.id === baseline.id
                          ? "bg-[#f7f7f8]"
                          : ""
                      }`}
                    >
                      <td className="px-5 py-4">
                        <div>
                          <div className="text-[13px] font-semibold tracking-[-0.01em] text-[#111827]">
                            Baseline v{baseline.version}
                          </div>

                          <div className="mt-1 text-[12px] text-[#9ca3af]">
                            ID #{baseline.id}
                          </div>
                        </div>
                      </td>

                      <td className="px-5 py-4 text-[13px] font-medium text-[#374151]">
                        Model #{baseline.model_id}
                      </td>

                      <td className="px-5 py-4 text-[13px] font-medium text-[#374151]">
                        {Object.keys(baseline.schema || {}).length} fields
                      </td>

                      <td className="px-5 py-4">
                        <div className="inline-flex items-center gap-2">
                          <div className="h-2 w-2 rounded-full bg-emerald-500" />

                          <span className="text-[12px] font-medium text-[#374151]">
                            {baseline.status}
                          </span>
                        </div>
                      </td>

                      <td className="px-5 py-4 text-[12px] text-[#9ca3af]">
                        {new Date(baseline.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* INSPECTOR DRAWER */}
        <div
          className={`fixed right-0 top-0 z-40 h-screen border-l border-[#eceef1] bg-white transition-all duration-300 ${
            selectedBaseline
              ? "w-[28%] translate-x-0"
              : "w-[28%] translate-x-full"
          }`}
        >
          {selectedBaseline && (
            <div className="flex h-full flex-col">
              {/* TOP */}
              <div className="border-b border-[#f3f4f6] px-5 py-4">
                <div className="mb-5 flex items-start justify-between">
                  <div>
                    <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-[#9ca3af]">
                      Baseline Inspector
                    </div>

                    <h2 className="text-[22px] font-semibold tracking-[-0.03em] text-[#111827]">
                      Version {selectedBaseline.version}
                    </h2>
                  </div>

                  <button
                    onClick={() => setSelectedBaseline(null)}
                    className="flex h-8 w-8 items-center justify-center rounded-[8px] border border-[#eceef1] text-[#6b7280] transition hover:bg-[#f9fafb]"
                  >
                    ✕
                  </button>
                </div>

                {/* META */}
                <div className="flex items-center gap-5 text-[12px]">
                  <div>
                    <div className="text-[#9ca3af]">Columns</div>

                    <div className="mt-1 font-semibold text-[#111827]">
                      {Object.keys(selectedBaseline.schema || {}).length}
                    </div>
                  </div>

                  <div>
                    <div className="text-[#9ca3af]">Model</div>

                    <div className="mt-1 font-semibold text-[#111827]">
                      #{selectedBaseline.model_id}
                    </div>
                  </div>

                  <div>
                    <div className="text-[#9ca3af]">Status</div>

                    <div className="mt-1 font-semibold text-emerald-600">
                      {selectedBaseline.status}
                    </div>
                  </div>
                </div>
              </div>

              {/* BODY */}
              <div className="flex-1 overflow-y-auto px-5 py-4">
                {/* SCHEMA */}
                <div className="mb-6">
                  <h3 className="mb-3 text-[13px] font-semibold uppercase tracking-[0.08em] text-[#9ca3af]">
                    Schema
                  </h3>

                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(selectedBaseline.schema || {}).map(
                      ([name, dtype]) => (
                        <div
                          key={name}
                          className="rounded-[10px] border border-[#eceef1] bg-white px-3 py-3"
                        >
                          <div className="text-[13px] font-semibold tracking-[-0.01em] text-[#111827]">
                            {name}
                          </div>

                          <div className="mt-2 inline-flex rounded-[7px] bg-[#f3f4f6] px-2 py-1 font-mono text-[11px] text-[#4b5563]">
                            {dtype}
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </div>

                {/* PROFILE */}
                <div>
                  <h3 className="mb-3 text-[13px] font-semibold uppercase tracking-[0.08em] text-[#9ca3af]">
                    Profiles
                  </h3>

                  <div className="space-y-3">
                    {Object.entries(selectedBaseline.profile || {}).map(
                      ([name, profile]) => (
                        <div
                          key={name}
                          className="rounded-[10px] border border-[#eceef1] p-4"
                        >
                          <div className="mb-3 flex items-center justify-between">
                            <div className="text-[13px] font-semibold text-[#111827]">
                              {name}
                            </div>

                            <div className="font-mono text-[11px] text-[#9ca3af]">
                              {profile.type}
                            </div>
                          </div>

                          {profile.type === "numeric" ? (
                            <div className="grid grid-cols-3 gap-2">
                              <div>
                                <div className="text-[10px] text-[#9ca3af]">
                                  Min
                                </div>

                                <div className="mt-1 text-[13px] font-semibold text-[#111827]">
                                  {profile.min}
                                </div>
                              </div>

                              <div>
                                <div className="text-[10px] text-[#9ca3af]">
                                  Max
                                </div>

                                <div className="mt-1 text-[13px] font-semibold text-[#111827]">
                                  {profile.max}
                                </div>
                              </div>

                              <div>
                                <div className="text-[10px] text-[#9ca3af]">
                                  Mean
                                </div>

                                <div className="mt-1 text-[13px] font-semibold text-[#111827]">
                                  {Number(profile.mean).toFixed(2)}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="flex flex-wrap gap-2">
                              {profile.unique_values
                                ?.slice(0, 8)
                                .map((value, index) => (
                                  <div
                                    key={index}
                                    className="rounded-[8px] bg-[#f3f4f6] px-2 py-1 text-[11px] font-medium text-[#4b5563]"
                                  >
                                    {value}
                                  </div>
                                ))}
                            </div>
                          )}
                        </div>
                      ),
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* MODAL */}
      {showUploadModal && (
        <UploadBaselineModal
          onClose={() => setShowUploadModal(false)}
          onUploaded={fetchBaselines}
        />
      )}
    </div>
  );
}

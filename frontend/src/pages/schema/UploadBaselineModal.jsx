import { useEffect, useState } from "react";

import {
  X,
  Upload,
  Database,
} from "lucide-react";

import { getModels } from "../../store/modelStore";

import { uploadBaseline } from "../../store/baselineStorre"
export default function UploadBaselineModal({
  onClose,
  onUploaded,
}) {
  const [models, setModels] = useState([]);

  const [selectedModel, setSelectedModel] =
    useState("");

  const [file, setFile] = useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] = useState("");

  // ==========================================
  // LOAD MODELS
  // ==========================================
  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const data = await getModels();

      setModels(data || []);
    } catch (err) {
      console.log(err);

      setError("Failed to load models");
    }
  };

  // ==========================================
  // HANDLE UPLOAD
  // ==========================================
  const handleUpload = async () => {
    if (!selectedModel || !file) return;

    try {
      setLoading(true);

      setError("");

      await uploadBaseline(
        selectedModel,
        file,
      );

      onUploaded();

      onClose();
    } catch (err) {
      console.log(err);

      setError(
        err?.response?.data?.detail ||
          "Upload failed",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-sm px-6">
      <div className="relative w-full max-w-[620px] overflow-hidden rounded-[28px] border border-black/[0.05] bg-white shadow-[0_30px_100px_rgba(15,23,42,0.12)]">
        {/* HEADER */}
        <div className="flex items-start justify-between border-b border-black/[0.05] px-8 py-6">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-black/[0.05] bg-[#f8fafc] px-3 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-gray-500">
              <Database size={12} />
              Baseline Dataset
            </div>

            <h2 className="text-[28px] font-semibold tracking-[-0.05em] text-[#111827]">
              Upload Baseline CSV
            </h2>

            <p className="mt-2 text-[14px] leading-7 text-gray-500">
              Upload reference dataset and
              assign it to a registered
              model.
            </p>
          </div>

          <button
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-black/[0.05] bg-[#f8fafc]"
          >
            <X size={16} />
          </button>
        </div>

        {/* BODY */}
        <div className="px-8 py-7">
          {/* ERROR */}
          {error && (
            <div className="mb-5 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-[12px] text-red-600">
              {error}
            </div>
          )}

          {/* MODEL */}
          <div className="mb-5">
            <label className="mb-2 block text-[11px] font-medium uppercase tracking-[0.18em] text-gray-400">
              Select Model
            </label>

            <select
              value={selectedModel}
              onChange={(e) =>
                setSelectedModel(
                  e.target.value,
                )
              }
              className="h-[54px] w-full rounded-2xl border border-black/[0.05] bg-[#f8fafc] px-4 text-[14px] outline-none"
            >
              <option value="">
                Select registered model
              </option>

              {models.map((model) => (
                <option
                  key={model.id}
                  value={model.id}
                >
                  {model.name} v
                  {model.version}
                </option>
              ))}
            </select>
          </div>

          {/* FILE */}
          <div>
            <label className="mb-2 block text-[11px] font-medium uppercase tracking-[0.18em] text-gray-400">
              Baseline CSV
            </label>

            <label className="flex cursor-pointer flex-col items-center justify-center rounded-[24px] border border-dashed border-[#cbd5e1] bg-[#f8fafc] px-6 py-14 transition hover:bg-[#f1f5f9]">
              <Upload
                size={32}
                className="mb-4 text-gray-400"
              />

              <div className="text-[14px] font-medium text-[#111827]">
                {file
                  ? file.name
                  : "Select baseline CSV"}
              </div>

              <div className="mt-2 text-[12px] text-gray-500">
                Upload reference dataset
              </div>

              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) =>
                  setFile(
                    e.target.files[0],
                  )
                }
              />
            </label>
          </div>

          {/* FOOTER */}
          <div className="mt-8 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="rounded-2xl border border-black/[0.05] bg-[#f8fafc] px-5 py-3 text-[13px] font-medium text-[#111827]"
            >
              Cancel
            </button>

            <button
              onClick={handleUpload}
              disabled={
                !selectedModel ||
                !file ||
                loading
              }
              className="rounded-2xl bg-[#111827] px-5 py-3 text-[13px] font-medium text-white transition hover:bg-black disabled:opacity-50"
            >
              {loading
                ? "Uploading..."
                : "Upload Baseline"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
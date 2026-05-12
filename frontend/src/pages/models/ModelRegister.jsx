import { useEffect, useState } from "react";

import {
  X,
  Database,
  GitBranch,
  Layers3,
  ShieldCheck,
  ServerCog,
} from "lucide-react";

import {
  discoverModels,
  getModelVersions,
  registerModel,
} from "../../store/modelStore";

export default function RegisterModelModal({ onClose }) {

  const [trackingUri, setTrackingUri] = useState("");

  const [isLoadingModels, setIsLoadingModels] =
    useState(false);

  const [isRegistering, setIsRegistering] =
    useState(false);

  const [selectedModel, setSelectedModel] =
    useState("");

  const [selectedVersion, setSelectedVersion] =
    useState("");

  const [models, setModels] = useState([]);

  const [versions, setVersions] = useState([]);

  const [connectionError, setConnectionError] =
    useState("");

  const [successMessage, setSuccessMessage] =
    useState("");

  // ==========================================
  // LOAD MODELS FROM URI
  // ==========================================
  useEffect(() => {

    if (!trackingUri) {

      setModels([]);
      return;
    }

    const timer = setTimeout(async () => {

      try {

        setConnectionError("");

        setIsLoadingModels(true);

        const response =
          await discoverModels(
            trackingUri
          );

        setModels(
          response.models || []
        );

      } catch (err) {

        console.log(err);

        setModels([]);

        setConnectionError(
          err?.detail ||
          "Unable to connect registry"
        );

      } finally {

        setIsLoadingModels(false);
      }

    }, 700);

    return () => clearTimeout(timer);

  }, [trackingUri]);

  // ==========================================
  // LOAD MODEL VERSIONS
  // ==========================================
  useEffect(() => {

    if (!selectedModel) {

      setVersions([]);
      return;
    }

    const fetchVersions = async () => {

      try {

        const response =
          await getModelVersions(
            trackingUri,
            selectedModel
          );

        setVersions(
          response.versions || []
        );

      } catch (err) {

        console.log(err);

        setVersions([]);
      }
    };

    fetchVersions();

  }, [selectedModel]);

  // ==========================================
  // REGISTER MODEL
  // ==========================================
  const handleRegister = async () => {

    try {

      setIsRegistering(true);

      setConnectionError("");

      setSuccessMessage("");

      const versionData =
        versions.find(
          (v) =>
            String(v.version) ===
            String(selectedVersion)
        );

      await registerModel({

        name: selectedModel,

        version: selectedVersion,

        framework: null,

        mlflow_model_name:
          selectedModel,

        mlflow_alias:
          versionData?.stage,

        mlflow_run_id:
          versionData?.run_id,

        mlflow_tracking_uri:
          trackingUri,

        expected_features: [],
      });

      setSuccessMessage(
        "Model registered successfully"
      );

      setTimeout(() => {

        onClose();

      }, 1200);

    } catch (err) {

      console.log(err);

      setConnectionError(
        err?.detail ||
        "Model registration failed"
      );

    } finally {

      setIsRegistering(false);
    }
  };

  return (

    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm px-6">

      {/* MODAL */}
      <div className="relative w-full max-w-[860px] overflow-hidden rounded-[24px] border border-black/[0.05] bg-white shadow-[0_30px_100px_rgba(15,23,42,0.12)]">

        {/* BACKGROUND */}
        <div className="absolute inset-0 overflow-hidden">

          <div className="absolute top-[-20%] right-[-10%] h-[380px] w-[380px] rounded-full bg-[#3563ff]/[0.06] blur-[120px]" />

          <div className="absolute bottom-[-30%] left-[-10%] h-[300px] w-[300px] rounded-full bg-[#7c3aed]/[0.04] blur-[120px]" />

          <div className="absolute inset-0 opacity-[0.025] bg-[linear-gradient(to_right,rgba(15,23,42,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.06)_1px,transparent_1px)] bg-[size:42px_42px]" />
        </div>

        {/* HEADER */}
        <div className="relative z-10 flex items-start justify-between border-b border-black/[0.05] px-8 py-6">

          <div>

            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-black/[0.05] bg-[#f7f8fb] px-3 py-1 text-[10px] font-medium uppercase tracking-[0.2em] text-gray-500">

              <ShieldCheck size={12} />

              MLflow Registry Connection
            </div>

            <h2 className="text-[28px] font-semibold tracking-[-0.04em] text-[#111827]">

              Connect ML Model
            </h2>

            <p className="mt-2 max-w-[580px] text-[14px] leading-7 text-gray-500">

              Connect your MLflow registry, discover available
              models, and register production versions for
              monitoring, drift analysis, and observability.
            </p>
          </div>

          <button
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-black/[0.05] bg-[#f7f8fb] text-gray-500 transition hover:bg-[#eef2ff] hover:text-[#111827]"
          >
            <X size={16} />
          </button>
        </div>

        {/* CONTENT */}
        <div className="relative z-10 px-8 py-7">

          {/* SUCCESS */}
          {successMessage && (

            <div className="mb-5 rounded-xl border border-green-100 bg-green-50 px-4 py-3 text-[12px] text-green-700">

              {successMessage}
            </div>
          )}

          {/* ERROR */}
          {connectionError && (

            <div className="mb-5 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-[12px] text-red-600">

              {connectionError}
            </div>
          )}

          {/* FLOW */}
          <div className="mb-8 flex items-center gap-3">

            <div className="flex items-center gap-2 rounded-xl border border-black/[0.05] bg-[#f7f8fb] px-3 py-2">

              <Database size={14} className="text-[#3563ff]" />

              <span className="text-[11px] font-medium text-[#111827]">

                Registry URI
              </span>
            </div>

            <div className="h-px flex-1 bg-gradient-to-r from-[#3563ff]/20 to-transparent" />

            <div className="flex items-center gap-2 rounded-xl border border-black/[0.05] bg-[#f7f8fb] px-3 py-2">

              <GitBranch size={14} className="text-[#3563ff]" />

              <span className="text-[11px] font-medium text-[#111827]">

                Models
              </span>
            </div>

            <div className="h-px flex-1 bg-gradient-to-r from-[#3563ff]/20 to-transparent" />

            <div className="flex items-center gap-2 rounded-xl border border-black/[0.05] bg-[#f7f8fb] px-3 py-2">

              <Layers3 size={14} className="text-[#3563ff]" />

              <span className="text-[11px] font-medium text-[#111827]">

                Versions
              </span>
            </div>
          </div>

          {/* GRID */}
          <div className="grid grid-cols-2 gap-5">

            {/* LEFT */}
            <div className="space-y-5">

              {/* URI */}
              <div>

                <label className="mb-2 block text-[11px] font-medium uppercase tracking-[0.18em] text-gray-400">

                  MLflow Tracking URI
                </label>

                <div className="relative">

                  <ServerCog
                    size={16}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                  />

                  <input
                    type="text"
                    value={trackingUri}
                    onChange={(e) =>
                      setTrackingUri(
                        e.target.value
                      )
                    }
                    placeholder="http://localhost:5000"
                    className="h-[50px] w-full rounded-xl border border-black/[0.05] bg-[#f7f8fb] pl-11 pr-4 text-[13px] text-[#111827] outline-none placeholder:text-gray-400 focus:border-[#3563ff]/30"
                  />
                </div>
              </div>

              {/* MODEL */}
              <div>

                <label className="mb-2 block text-[11px] font-medium uppercase tracking-[0.18em] text-gray-400">

                  Available Models
                </label>

                <select
                  value={selectedModel}
                  onChange={(e) =>
                    setSelectedModel(
                      e.target.value
                    )
                  }
                  className="h-[50px] w-full rounded-xl border border-black/[0.05] bg-[#f7f8fb] px-4 text-[13px] text-[#111827] outline-none focus:border-[#3563ff]/30"
                >

                  <option value="">
                    {isLoadingModels
                      ? "Loading models..."
                      : "Select model"}
                  </option>

                  {models.map((model) => (

                    <option
                      key={model.name}
                      value={model.name}
                    >
                      {model.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* VERSION */}
              <div>

                <label className="mb-2 block text-[11px] font-medium uppercase tracking-[0.18em] text-gray-400">

                  Model Version
                </label>

                <select
                  value={selectedVersion}
                  onChange={(e) =>
                    setSelectedVersion(
                      e.target.value
                    )
                  }
                  className="h-[50px] w-full rounded-xl border border-black/[0.05] bg-[#f7f8fb] px-4 text-[13px] text-[#111827] outline-none focus:border-[#3563ff]/30"
                >

                  <option value="">
                    Select version
                  </option>

                  {versions.map((version) => (

                    <option
                      key={version.version}
                      value={version.version}
                    >
                      v{version.version}
                      {" "}
                      (
                      {version.stage || "None"}
                      )
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* RIGHT PANEL */}
            <div className="relative overflow-hidden rounded-[20px] border border-black/[0.05] bg-[#f8fafc] p-6">

              <div className="absolute top-[-20%] right-[-10%] h-[240px] w-[240px] rounded-full bg-[#3563ff]/[0.08] blur-[90px]" />

              <div className="relative z-10">

                <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-black/[0.05] bg-white px-3 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-gray-500 shadow-sm">

                  Production Monitoring
                </div>

                <h3 className="max-w-[300px] text-[30px] leading-[1] font-semibold tracking-[-0.05em] text-[#111827]">

                  Monitor
                  <br />

                  model behavior
                  <br />

                  automatically.
                </h3>

                <p className="mt-5 max-w-[320px] text-[13px] leading-7 text-gray-500">

                  Connected models become available for
                  schema validation, prediction monitoring,
                  drift detection, incident analysis,
                  and operational observability.
                </p>
              </div>
            </div>
          </div>

          {/* FOOTER */}
          <div className="relative z-10 mt-8 flex items-center justify-between border-t border-black/[0.05] pt-6">

            <p className="max-w-[460px] text-[12px] leading-6 text-gray-500">

              OpsSight connects securely to your MLflow registry
              and stores only monitoring metadata and model references.
            </p>

            <div className="flex items-center gap-3">

              <button
                onClick={onClose}
                className="rounded-xl border border-black/[0.05] bg-[#f7f8fb] px-5 py-3 text-[13px] font-medium text-[#111827] transition hover:bg-[#eef2ff]"
              >
                Cancel
              </button>

              <button
                onClick={handleRegister}
                disabled={
                  !trackingUri ||
                  !selectedModel ||
                  !selectedVersion ||
                  isRegistering
                }
                className="rounded-xl bg-gray-700 px-5 py-3 text-[13px] font-medium text-white shadow-[0_10px_40px_rgba(53,99,255,0.18)] transition hover:bg-[#2957f5] disabled:cursor-not-allowed disabled:opacity-50"
              >

                {isRegistering
                  ? "Registering..."
                  : "Register Model"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
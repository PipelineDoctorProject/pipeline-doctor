import { useEffect, useState } from "react";
import {
  CheckCircle2,
  Database,
  GitBranch,
  Layers3,
  Loader2,
  ServerCog,
  X,
} from "lucide-react";

import {
  discoverModels,
  getModelVersions,
  registerModel,
} from "../../store/modelStore";

export default function RegisterModelModal({ onClose }) {
  const [trackingUri, setTrackingUri] = useState("");
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedVersion, setSelectedVersion] = useState("");
  const [models, setModels] = useState([]);
  const [versions, setVersions] = useState([]);
  const [connectionError, setConnectionError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (!trackingUri) return;

    const timer = setTimeout(async () => {
      try {
        setConnectionError("");
        setIsLoadingModels(true);

        const response = await discoverModels(trackingUri);

        setModels(response.models || []);
      } catch (err) {
        console.log(err);

        setModels([]);
        setConnectionError(err?.detail || "Unable to connect registry");
      } finally {
        setIsLoadingModels(false);
      }
    }, 700);

    return () => clearTimeout(timer);
  }, [trackingUri]);

  useEffect(() => {
    if (!selectedModel) return;

    const fetchVersions = async () => {
      try {
        const response = await getModelVersions(
          trackingUri,
          selectedModel,
        );

        setVersions(response.versions || []);
      } catch (err) {
        console.log(err);

        setVersions([]);
      }
    };

    fetchVersions();
  }, [selectedModel, trackingUri]);

  const handleRegister = async () => {
    try {
      setIsRegistering(true);
      setConnectionError("");
      setSuccessMessage("");

      const versionData = versions.find(
        (version) => String(version.version) === String(selectedVersion),
      );

      await registerModel({
        name: selectedModel,
        version: selectedVersion,
        framework: "sklearn",
        mlflow_model_name: selectedModel,
        mlflow_alias: versionData?.stage,
        mlflow_run_id: versionData?.run_id,
        mlflow_tracking_uri: trackingUri,
        expected_features: [],
      });

      setSuccessMessage(
        "Model registered successfully. Upload a baseline dataset from the Schema page to enable validation.",
      );
    } catch (err) {
      console.log(err);

      setConnectionError(err?.detail || "Model registration failed");
    } finally {
      setIsRegistering(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-6 backdrop-blur-sm">
      <div className="relative w-full max-w-[900px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.24)]">
        {successMessage && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/95 px-6 backdrop-blur-sm">
            <div className="w-full max-w-[420px] rounded-lg border border-emerald-200 bg-white p-7 shadow-xl">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-md bg-emerald-50 text-emerald-700">
                <CheckCircle2 size={24} />
              </div>

              <h3 className="text-[22px] font-semibold text-slate-950">
                Registration Successful
              </h3>

              <p className="mt-3 text-[14px] leading-6 text-slate-500">
                {successMessage}
              </p>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={onClose}
                  className="h-10 rounded-md bg-slate-950 px-5 text-[13px] font-semibold text-white transition hover:bg-slate-800"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-5">
          <div>
            

            <h2 className="text-[26px] font-semibold leading-tight text-slate-950">
              Connect ML Model
            </h2>

            <p className="mt-2 max-w-[640px] text-[14px] leading-6 text-slate-500">
              Discover models from an MLflow tracking server and register the
              version you want Pipeline Doctor to monitor.
            </p>
          </div>

          <button
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 hover:text-slate-950"
            aria-label="Close connect model modal"
          >
            <X size={16} />
          </button>
        </div>

        <div className="grid gap-0 lg:grid-cols-[1fr_300px]">
          <div className="px-6 py-6">
            {connectionError && (
              <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-[13px] font-medium text-red-700">
                {connectionError}
              </div>
            )}

            <div className="mb-6 grid gap-3 md:grid-cols-3">
              <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3">
                <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-md bg-white text-slate-600">
                  <Database size={15} />
                </div>
                <div className="text-[12px] font-semibold text-slate-950">
                  Registry URI
                </div>
                <p className="mt-1 text-[11px] leading-5 text-slate-500">
                  Connect the tracking server.
                </p>
              </div>

              <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3">
                <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-md bg-white text-slate-600">
                  <GitBranch size={15} />
                </div>
                <div className="text-[12px] font-semibold text-slate-950">
                  Select Model
                </div>
                <p className="mt-1 text-[11px] leading-5 text-slate-500">
                  Choose a registered model.
                </p>
              </div>

              <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3">
                <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-md bg-white text-slate-600">
                  <Layers3 size={15} />
                </div>
                <div className="text-[12px] font-semibold text-slate-950">
                  Version
                </div>
                <p className="mt-1 text-[11px] leading-5 text-slate-500">
                  Register one version.
                </p>
              </div>
            </div>

            <div className="space-y-5">
              <div>
                <label className="mb-2 block text-[12px] font-semibold text-slate-700">
                  MLflow Tracking URI
                </label>

                <div className="relative">
                  <ServerCog
                    size={16}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                  />

                  <input
                    type="text"
                    value={trackingUri}
                    onChange={(event) => {
                      setTrackingUri(event.target.value);
                      setSelectedModel("");
                      setSelectedVersion("");
                      setModels([]);
                      setVersions([]);
                    }}
                    placeholder="http://localhost:5000"
                    className="h-11 w-full rounded-md border border-slate-200 bg-slate-50 pl-10 pr-4 text-[14px] text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:bg-white"
                  />
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-[12px] font-semibold text-slate-700">
                    Available Models
                  </label>

                  <select
                    value={selectedModel}
                    onChange={(event) => {
                      setSelectedModel(event.target.value);
                      setSelectedVersion("");
                      setVersions([]);
                    }}
                    className="h-11 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-[14px] text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  >
                    <option value="">
                      {isLoadingModels ? "Loading models..." : "Select model"}
                    </option>

                    {models.map((model) => (
                      <option key={model.name} value={model.name}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-[12px] font-semibold text-slate-700">
                    Model Version
                  </label>

                  <select
                    value={selectedVersion}
                    onChange={(event) => setSelectedVersion(event.target.value)}
                    className="h-11 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-[14px] text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  >
                    <option value="">Select version</option>

                    {versions.map((version) => (
                      <option key={version.version} value={version.version}>
                        v{version.version} ({version.stage || "None"})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          <aside className="border-t border-slate-200 bg-slate-50 px-6 py-6 lg:border-l lg:border-t-0">
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-slate-950 text-white">
                <CheckCircle2 size={18} />
              </div>

              <h3 className="mt-4 text-[17px] font-semibold text-slate-950">
                Monitoring-ready setup
              </h3>

              <p className="mt-2 text-[13px] leading-6 text-slate-500">
                Once connected, the model can be paired with a baseline schema
                for validation, drift detection, and incident review.
              </p>

              <div className="mt-5 space-y-3 border-t border-slate-200 pt-4">
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-slate-500">Discovered models</span>
                  <span className="font-semibold text-slate-950">
                    {models.length}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-slate-500">Versions loaded</span>
                  <span className="font-semibold text-slate-950">
                    {versions.length}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-slate-500">Selected version</span>
                  <span className="font-semibold text-slate-950">
                    {selectedVersion ? `v${selectedVersion}` : "-"}
                  </span>
                </div>
              </div>
            </div>
          </aside>
        </div>

        <div className="flex flex-col gap-3 border-t border-slate-200 px-6 py-4 md:flex-row md:items-center md:justify-between">
          <p className="text-[12px] leading-5 text-slate-500">
            Pipeline Doctor stores model metadata and MLflow references for
            monitoring workflows.
          </p>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="h-10 rounded-md border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-700 transition hover:bg-slate-50"
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
              className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isRegistering && <Loader2 size={15} className="animate-spin" />}
              {isRegistering ? "Registering..." : "Register Model"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

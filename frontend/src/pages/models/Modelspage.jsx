import {
  lazy,
  Suspense,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Activity,
  Brain,
  CheckCircle2,
  Database,
  GitBranch,
  Plus,
  RefreshCw,
  Search,
  ServerCog,
} from "lucide-react";

import { getModels } from "../../store/modelStore";

const RegisterModelModal = lazy(() => import("./ModelRegister"));

function getFrameworkColor(framework) {
  const key = String(framework || "").toLowerCase();

  if (key.includes("sklearn")) return "bg-blue-50 text-blue-700";
  if (key.includes("torch")) return "bg-orange-50 text-orange-700";
  if (key.includes("tensorflow")) return "bg-amber-50 text-amber-700";
  if (key.includes("xgboost")) return "bg-emerald-50 text-emerald-700";

  return "bg-slate-100 text-slate-700";
}

function getRegistryStatus(model) {
  const status = String(model.registry_status || "available").toLowerCase();

  if (status === "missing") {
    return {
      label: "Registry missing",
      className: "text-rose-700",
      icon: Activity,
    };
  }

  if (status === "local_only") {
    return {
      label: "Local only",
      className: "text-amber-700",
      icon: Database,
    };
  }

  return {
    label: "Ready",
    className: "text-emerald-700",
    icon: CheckCircle2,
  };
}

export default function ModelsPage() {
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  async function loadModels() {
    try {
      setLoading(true);
      const data = await getModels();
      setModels(data || []);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadModels();
  }, []);

  const filteredModels = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return models;

    return models.filter((model) =>
      [
        model.name,
        model.version,
        model.framework,
        model.mlflow_model_name,
        model.mlflow_alias,
        model.mlflow_run_id,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }, [models, query]);

  const frameworks = new Set(models.map((model) => model.framework).filter(Boolean));
  const registeredVersions = models.filter((model) => model.version).length;

  return (
    <>
      <div className="flex flex-col gap-5">
        <section className="rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          <div className="flex flex-col gap-4 border-b border-slate-200 px-6 py-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              

              <h1 className="text-[30px] font-semibold leading-tight text-slate-950">
                Connected ML Models
              </h1>

              <p className="mt-2 max-w-[760px] text-[14px] leading-6 text-slate-500">
                Manage registered model versions, registry metadata, and
                monitoring readiness from one operational view.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadModels}
                className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                <RefreshCw size={15} />
                Refresh
              </button>

              <button
                onClick={() => setShowRegisterModal(true)}
                className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800"
              >
                <Plus size={15} />
                Connect Model
              </button>
            </div>
          </div>

          <div className="grid border-b border-slate-200 md:grid-cols-3">
            <div className="border-b border-slate-200 px-6 py-4 md:border-b-0 md:border-r">
              <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
                Total models
                <Database size={16} />
              </div>
              <div className="mt-2 text-[26px] font-semibold text-slate-950">
                {models.length}
              </div>
            </div>

            <div className="border-b border-slate-200 px-6 py-4 md:border-b-0 md:border-r">
              <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
                Registered versions
                <GitBranch size={16} />
              </div>
              <div className="mt-2 text-[26px] font-semibold text-slate-950">
                {registeredVersions}
              </div>
            </div>

            <div className="px-6 py-4">
              <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
                Frameworks
                <ServerCog size={16} />
              </div>
              <div className="mt-2 text-[26px] font-semibold text-slate-950">
                {frameworks.size}
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-[16px] font-semibold text-slate-950">
                Registry Inventory
              </h2>
              <p className="mt-1 text-[13px] text-slate-500">
                Compact view of model versions available for monitoring.
              </p>
            </div>

            <label className="flex h-10 w-full items-center gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 md:max-w-[320px]">
              <Search size={16} className="text-slate-400" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search model, framework, version"
                className="h-full min-w-0 flex-1 bg-transparent text-[14px] text-slate-700 outline-none placeholder:text-slate-400"
              />
            </label>
          </div>

          {loading && (
            <div className="px-6 py-12 text-center text-[14px] text-slate-500">
              Loading models...
            </div>
          )}

          {!loading && filteredModels.length === 0 && (
            <div className="px-6 py-14 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400">
                <Brain size={22} />
              </div>
              <h3 className="mt-4 text-[17px] font-semibold text-slate-950">
                No models found
              </h3>
              <p className="mx-auto mt-2 max-w-[420px] text-[14px] leading-6 text-slate-500">
                Connect an MLflow model or adjust your search to view registered
                production assets.
              </p>
            </div>
          )}

          {!loading && filteredModels.length > 0 && (
            <div className="divide-y divide-slate-200">
              {filteredModels.map((model, index) => {
                const registry = getRegistryStatus(model);
                const RegistryIcon = registry.icon;

                return (
                  <article
                    key={model.id || `${model.name}-${model.version}-${index}`}
                    className="grid gap-4 px-5 py-4 transition hover:bg-slate-50/70 lg:grid-cols-[minmax(260px,1.4fr)_120px_150px_150px_170px]"
                    title={model.registry_message || ""}
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-700">
                        <Brain size={18} />
                      </div>

                      <div className="min-w-0">
                        <h3 className="truncate text-[15px] font-semibold text-slate-950">
                          {model.name || model.mlflow_model_name || "Unnamed model"}
                        </h3>
                        <p className="mt-1 truncate text-[12px] text-slate-500">
                          {model.mlflow_run_id
                            ? `Run ${model.mlflow_run_id}`
                            : "MLflow registry"}
                        </p>
                      </div>
                    </div>

                    <div>
                      <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                        Version
                      </div>
                      <div className="mt-1 inline-flex rounded-md border border-slate-200 bg-white px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-800 lg:mt-0">
                        v{model.version || "-"}
                      </div>
                    </div>

                    <div>
                      <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                        Framework
                      </div>
                      <div
                        className={`mt-1 inline-flex rounded-md px-2.5 py-1 text-[12px] font-semibold lg:mt-0 ${getFrameworkColor(
                          model.framework,
                        )}`}
                      >
                        {model.framework || "unknown"}
                      </div>
                    </div>

                    <div>
                      <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                        Alias
                      </div>
                      <div className="mt-1 truncate text-[13px] font-medium text-slate-700 lg:mt-0">
                        {model.mlflow_alias || "No alias"}
                      </div>
                    </div>

                    <div className="flex items-center justify-between gap-3 lg:justify-end">
                      <div className={`inline-flex items-center gap-2 text-[12px] font-semibold ${registry.className}`}>
                        <RegistryIcon size={15} />
                        {registry.label}
                      </div>
                      <button className="inline-flex h-9 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-[12px] font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-100">
                        <Activity size={14} />
                        View
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>

      {showRegisterModal && (
        <Suspense
          fallback={
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
              <div className="rounded-lg border border-slate-200 bg-white px-6 py-4 text-sm text-slate-600 shadow-xl">
                Loading Model Registry...
              </div>
            </div>
          }
        >
          <RegisterModelModal
            onClose={() => {
              setShowRegisterModal(false);
              loadModels();
            }}
          />
        </Suspense>
      )}
    </>
  );
}

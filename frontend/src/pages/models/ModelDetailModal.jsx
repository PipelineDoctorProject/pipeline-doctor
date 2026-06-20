import { useEffect, useState, useCallback, useRef } from "react";
import {
  AlertCircle,
  Award,
  Check,
  CheckCircle2,
  Database,
  GitBranch,
  Loader2,
  RefreshCw,
  ServerCog,
  X,
} from "lucide-react";
import { getModelVersions, updateModelAlias } from "../../store/modelStore";

export default function ModelDetailModal({ model, onClose }) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retrying, setRetrying] = useState(false);
  const [promotingVersion, setPromotingVersion] = useState(null);
  const [actionSuccess, setActionSuccess] = useState("");
  const retryCountRef = useRef(0);

  const trackingUri = model.mlflow_tracking_uri;
  const modelName = model.mlflow_model_name;

  const fetchVersions = useCallback(async ({ isAutoRetry = false } = {}) => {
    if (!modelName) {
      setLoading(false);
      return;
    }
    try {
      if (!isAutoRetry) setLoading(true);
      setError("");
      const response = await getModelVersions(trackingUri, modelName);
      // Sort versions descending by version number
      const sorted = (response.versions || []).sort((a, b) => {
        return Number(b.version) - Number(a.version);
      });
      setVersions(sorted);
      retryCountRef.current = 0;
    } catch (err) {
      console.error(err);
      const errMsg =
        err?.detail ||
        err?.message ||
        "Failed to fetch model versions from registry.";

      // Auto-retry up to 2 times (MLflow container may be cold-starting)
      if (retryCountRef.current < 2) {
        retryCountRef.current += 1;
        setRetrying(true);
        setTimeout(() => {
          setRetrying(false);
          fetchVersions({ isAutoRetry: true });
        }, 3000);
      } else {
        setError(errMsg);
        retryCountRef.current = 0;
      }
    } finally {
      if (!isAutoRetry) setLoading(false);
    }
  }, [modelName, trackingUri]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchVersions();
  }, [fetchVersions]);

  const handlePromote = async (versionObj) => {
    try {
      setPromotingVersion(versionObj.version);
      setError("");
      setActionSuccess("");
      await updateModelAlias(model.id, {
        version: String(versionObj.version),
        run_id: versionObj.run_id,
        alias: "champion",
      });
      setActionSuccess(`Successfully promoted Version ${versionObj.version} to champion.`);
      await fetchVersions();
    } catch (err) {
      console.error(err);
      const detail =
        err?.detail ||
        err?.message ||
        (typeof err === "string" ? err : "Failed to promote version to champion. The MLflow registry may be temporarily unreachable.");
      setError(detail);
    } finally {
      setPromotingVersion(null);
    }
  };

  function getFrameworkColor(framework) {
    const key = String(framework || "").toLowerCase();
    if (key.includes("sklearn")) return "bg-blue-50 text-blue-700 border border-blue-150";
    if (key.includes("torch")) return "bg-orange-50 text-orange-700 border border-orange-150";
    if (key.includes("tensorflow")) return "bg-amber-50 text-amber-700 border border-amber-150";
    if (key.includes("xgboost")) return "bg-emerald-50 text-emerald-700 border border-emerald-150";
    return "bg-slate-100 text-slate-700 border border-slate-200";
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-6 backdrop-blur-sm">
      <div className="relative w-full max-w-[1000px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.24)]">
        
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-[22px] font-semibold leading-tight text-slate-950">
                {model.name}
              </h2>
              <span className={`inline-flex rounded-md px-2.5 py-0.5 text-[11px] font-semibold ${getFrameworkColor(model.framework)}`}>
                {model.framework || "unknown"}
              </span>
            </div>
            <p className="mt-1 text-[13px] text-slate-500">
              {modelName ? `MLflow Registry Model: ${modelName}` : "Local Model (No registry configuration)"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 hover:text-slate-950"
            aria-label="Close details modal"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content Body Grid */}
        <div className="grid gap-0 lg:grid-cols-[1fr_320px]">
          
          {/* Left panel: Version History */}
          <div className="px-6 py-6 overflow-y-auto max-h-[60vh] min-h-[350px]">
            {(error || retrying) && (
              <div className="mb-5 flex items-start gap-3 rounded-md border border-red-200 bg-red-50 p-4 text-[13px] text-red-700">
                <AlertCircle size={18} className="shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold">
                    {retrying ? "Registry Unreachable — Retrying..." : "Registry Error"}
                  </h4>
                  <p className="mt-1 leading-5">
                    {retrying
                      ? "The MLflow registry may be starting up. Retrying automatically..."
                      : error}
                  </p>
                </div>
                {retrying ? (
                  <Loader2 size={16} className="animate-spin shrink-0 mt-0.5" />
                ) : (
                  <button
                    onClick={() => { retryCountRef.current = 0; fetchVersions(); }}
                    className="shrink-0 flex items-center gap-1 rounded border border-red-300 bg-red-100 px-2 py-1 text-[11px] font-semibold text-red-700 hover:bg-red-200 transition"
                  >
                    <RefreshCw size={11} /> Retry
                  </button>
                )}
              </div>
            )}

            {actionSuccess && (
              <div className="mb-5 flex items-start gap-3 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-[13px] text-emerald-700">
                <CheckCircle2 size={18} className="shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold">Operation Completed</h4>
                  <p className="mt-1 leading-5">{actionSuccess}</p>
                </div>
              </div>
            )}

            {!modelName ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400">
                  <Database size={22} />
                </div>
                <h3 className="mt-4 text-[16px] font-semibold text-slate-950">Local Deployment Only</h3>
                <p className="mt-2 max-w-[420px] text-[13px] leading-6 text-slate-500">
                  This model was registered locally in Pipeline Doctor without an associated MLflow registry tracking URI.
                  To track versions, view runs, and manage champion rollbacks, edit or re-register this model with an MLflow server.
                </p>
              </div>
            ) : loading ? (
              <div className="flex flex-col items-center justify-center py-16 text-center text-slate-500">
                <Loader2 size={32} className="animate-spin text-slate-400" />
                <p className="mt-4 text-[13px] font-medium">Fetching registered model versions from MLflow registry...</p>
              </div>
            ) : versions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-slate-500">
                <div className="flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400">
                  <GitBranch size={22} />
                </div>
                <h3 className="mt-4 text-[16px] font-semibold text-slate-950">No Versions Found</h3>
                <p className="mt-2 max-w-[420px] text-[13px] leading-6 text-slate-500">
                  We found the model registration record, but MLflow returned no registered versions for "{modelName}".
                </p>
              </div>
            ) : (
              <div>
                <h3 className="mb-4 text-[14px] font-semibold text-slate-950">Model Versions & Aliases</h3>
                
                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <table className="w-full border-collapse bg-white text-left text-[13px] text-slate-700">
                    <thead className="border-b border-slate-200 bg-slate-50 font-semibold text-slate-900">
                      <tr>
                        <th className="px-4 py-3">Version</th>
                        <th className="px-4 py-3">MLflow Run ID</th>
                        <th className="px-4 py-3">Aliases & Stage</th>
                        <th className="px-4 py-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-150">
                      {versions.map((ver) => {
                        const isChamp = (ver.aliases || []).some(
                          (alias) => String(alias).toLowerCase() === "champion"
                        );
                        
                        return (
                          <tr key={ver.version} className={`hover:bg-slate-50/50 ${isChamp ? 'bg-slate-50/20' : ''}`}>
                            <td className="px-4 py-3 font-semibold text-slate-950">
                              v{ver.version}
                            </td>
                            <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                              <span title={ver.run_id}>
                                {ver.run_id ? ver.run_id.slice(0, 12) + "..." : "-"}
                              </span>
                            </td>
                             <td className="px-4 py-3">
                               <div className="flex flex-wrap gap-1 items-center">
                                 {/* Aliases */}
                                 {(ver.aliases || []).map((alias) => {
                                   const isAliasChamp = String(alias).toLowerCase() === "champion";
                                   return (
                                     <span
                                       key={alias}
                                       className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium border ${
                                         isAliasChamp
                                           ? "bg-emerald-50 text-emerald-700 border-emerald-100"
                                           : "bg-blue-50 text-blue-700 border-blue-100"
                                       }`}
                                     >
                                       {isAliasChamp && <Award size={10} />}
                                       @{alias}
                                     </span>
                                   );
                                 })}
 
                                 {/* Stage */}
                                 {ver.stage && ver.stage !== "None" && ver.stage !== "none" && (
                                   <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200">
                                     {ver.stage}
                                   </span>
                                 )}
 
                                 {ver.artifacts_exist === false && (
                                   <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-[10px] font-medium text-rose-700 border border-rose-100">
                                     <AlertCircle size={10} className="text-rose-500" />
                                     Artifacts Missing
                                   </span>
                                 )}
 
                                 {(!ver.aliases || ver.aliases.length === 0) && (!ver.stage || ver.stage === "None" || ver.stage === "none") && ver.artifacts_exist !== false && (
                                   <span className="text-[12px] text-slate-400 italic">No alias / inactive</span>
                                 )}
                               </div>
                             </td>
                             <td className="px-4 py-3 text-right">
                               {isChamp ? (
                                 <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-100 px-2.5 py-1 text-[12px] font-semibold text-emerald-800 border border-emerald-200">
                                   <Check size={13} />
                                   Active Champion
                                 </span>
                               ) : (
                                 <button
                                   onClick={() => handlePromote(ver)}
                                   disabled={promotingVersion !== null || ver.artifacts_exist === false}
                                   title={ver.artifacts_exist === false ? "Cannot promote version: model artifacts are missing in storage." : ""}
                                   className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 text-[12px] font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                                 >
                                   {promotingVersion === ver.version ? (
                                     <>
                                       <Loader2 size={13} className="animate-spin text-slate-400" />
                                       Promoting...
                                     </>
                                   ) : (
                                     <>
                                       <Award size={13} className="text-slate-400" />
                                       Promote to Champion
                                     </>
                                   )}
                                 </button>
                               )}
                             </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Right panel: Sidebar Details */}
          <aside className="border-t border-slate-200 bg-slate-50 px-6 py-6 lg:border-l lg:border-t-0 overflow-y-auto max-h-[60vh]">
            <div className="space-y-6">
              
              {/* Local Db Card */}
              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <h4 className="text-[13px] font-semibold text-slate-950 flex items-center gap-2">
                  <Database size={14} className="text-slate-500" />
                  Active Configuration
                </h4>
                <div className="mt-3.5 space-y-2.5 border-t border-slate-100 pt-3 text-[12px]">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Local Version:</span>
                    <span className="font-semibold text-slate-950">v{model.version || "-"}</span>
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-slate-500 font-medium">Tracking URI:</span>
                    <span className="truncate font-mono text-[10px] bg-slate-50 p-1.5 rounded border border-slate-150 text-slate-700" title={trackingUri}>
                      {trackingUri || "Local only"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium font-medium">Registered At:</span>
                    <span className="text-slate-800">
                      {model.created_at ? new Date(model.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      }) : "-"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Expected Features */}
              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <h4 className="text-[13px] font-semibold text-slate-950 flex items-center gap-2">
                  <ServerCog size={14} className="text-slate-500" />
                  Expected Features
                </h4>
                <p className="mt-1 text-[11px] text-slate-500 leading-4">
                  Features required by the model baseline schema.
                </p>
                <div className="mt-3 border-t border-slate-100 pt-3">
                  {model.expected_features && model.expected_features.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 max-h-[140px] overflow-y-auto">
                      {model.expected_features.map((feature, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center rounded bg-slate-50 border border-slate-150 px-2 py-0.5 font-mono text-[10px] text-slate-600"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[12px] text-slate-400 italic">No expected features registered.</p>
                  )}
                </div>
              </div>

              {/* Deployment Info Alert */}
              <div className="rounded-lg border border-blue-100 bg-blue-50/50 p-4 text-[12px] leading-5 text-blue-700">
                <div className="flex gap-2">
                  <Award size={15} className="shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-semibold">Rollback & Propagation</h5>
                    <p className="mt-1 text-blue-600/90">
                      Promoting an older version assigns the `@champion` alias to it in MLflow registry and updates Pipeline Doctor databases. 
                      Any scoring service routing models using this model's reference will automatically pick up the new configuration.
                    </p>
                  </div>
                </div>
              </div>

            </div>
          </aside>

        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-6 py-4">
          <p className="text-[12px] text-slate-500 flex items-center gap-1.5">
            <ServerCog size={13} />
            Pipeline Doctor Version Control
          </p>
          <button
            onClick={onClose}
            className="h-9 rounded-md border border-slate-200 bg-white px-4 text-[12px] font-semibold text-slate-700 transition hover:bg-slate-100"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}

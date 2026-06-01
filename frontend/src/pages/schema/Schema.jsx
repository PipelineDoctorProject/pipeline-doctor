import { useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight,
  Database,
  FileSpreadsheet,
  Plus,
  Search,
} from "lucide-react";

import UploadBaselineModal from "../schema/UploadBaselineModal";
import {
  activateBaseline,
  getBaselines,
} from "../../store/baselineStorre";

const statusStyles = {
  active: "border-emerald-200 bg-emerald-50 text-emerald-700",
  approved: "border-emerald-200 bg-emerald-50 text-emerald-700",
  production: "border-emerald-200 bg-emerald-50 text-emerald-700",
  draft: "border-amber-200 bg-amber-50 text-amber-700",
  pending: "border-amber-200 bg-amber-50 text-amber-700",
  archived: "border-slate-200 bg-slate-50 text-slate-600",
};

function formatDate(value) {
  if (!value) return "Not available";

  return new Date(value).toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function getStatusClass(status) {
  return (
    statusStyles[String(status || "").toLowerCase()] ||
    "border-sky-200 bg-sky-50 text-sky-700"
  );
}

function canActivateBaseline(baseline) {
  return String(baseline?.status || "").toLowerCase() !== "archived";
}

function getProfileSummary(profile) {
  if (!profile) return "No profile data";

  if (profile.type === "numeric") {
    const mean = Number(profile.mean);
    return `min ${profile.min ?? "-"} / max ${profile.max ?? "-"} / mean ${
      Number.isFinite(mean) ? mean.toFixed(2) : "-"
    }`;
  }

  const values = profile.unique_values || [];
  return values.length ? `${values.slice(0, 3).join(", ")}` : "No sample values";
}

export default function SchemaPage() {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedBaseline, setSelectedBaseline] = useState(null);
  const [baselines, setBaselines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [activatingId, setActivatingId] = useState(null);
  const [activationError, setActivationError] = useState("");

  async function fetchBaselines() {
    try {
      setLoading(true);
      const data = await getBaselines();
      setBaselines(data || []);
      setSelectedBaseline((current) => {
        if (!current) return current;

        return data?.find((baseline) => baseline.id === current.id) || null;
      });
    } catch (err) {
      console.log(err);
      setBaselines([]);
      setSelectedBaseline(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchBaselines();
  }, []);

  const filteredBaselines = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return baselines;

    return baselines.filter((baseline) => {
      const searchable = [
        baseline.id,
        baseline.version,
        baseline.model_name,
        baseline.status,
        baseline.model_id,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return searchable.includes(needle);
    });
  }, [baselines, query]);

  const inspectedBaseline = selectedBaseline || filteredBaselines[0] || null;

  async function handleActivateBaseline(baseline) {
    if (baseline.is_active || activatingId) return;

    if (!canActivateBaseline(baseline)) {
      setActivationError("Archived baselines cannot be activated.");
      return;
    }

    setActivationError("");
    setActivatingId(baseline.id);

    try {
      const activated = await activateBaseline(baseline.id);

      setBaselines((current) =>
        current.map((item) =>
          item.model_id === activated.model_id
            ? {
                ...item,
                is_active: item.id === activated.id,
                status: item.id === activated.id ? activated.status : item.status,
              }
            : item,
        ),
      );

      setSelectedBaseline((current) =>
        current?.id === activated.id
          ? {
              ...current,
              ...activated,
            }
          : current,
      );
    } catch (err) {
      setActivationError(
        err?.response?.data?.detail ||
          "Could not activate this baseline.",
      );
    } finally {
      setActivatingId(null);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col gap-5 border-b border-slate-200 px-6 py-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-[760px]">
            <h1 className="text-[30px] font-semibold leading-tight text-slate-950">
              Baseline Registry
            </h1>

            <p className="mt-2 text-[14px] leading-6 text-slate-500">
              Review approved schemas, compare field profiles, and keep model
              validation baselines ready for production checks.
            </p>
          </div>

          <button
            onClick={() => setShowUploadModal(true)}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800"
          >
            <Plus size={17} />
            Upload Baseline
          </button>
        </div>

      </section>

      <section className="grid gap-5 bg-transparent xl:grid-cols-[minmax(0,1fr)_400px]">
        <div className="flex bg-transparent min-w-0 flex-col gap-4">
          <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white px-5 py-4 shadow-[0_12px_34px_rgba(15,23,42,0.04)] md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-[16px] font-semibold text-slate-950">
                Schema Baselines
              </h2>
              <p className="mt-1 text-[13px] text-slate-500">
                Select a baseline to inspect schema fields and data profiles.
              </p>
            </div>

            <label className="flex h-10 w-full items-center gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 md:max-w-[300px]">
              <Search size={16} className="text-slate-400" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search model, status, version"
                className="h-full min-w-0 flex-1 bg-transparent text-[14px] text-slate-700 outline-none placeholder:text-slate-400"
              />
            </label>
          </div>

          {activationError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-[13px] font-medium text-red-700">
              {activationError}
            </div>
          )}

          {loading && (
            <div className="rounded-lg border border-slate-200 bg-white px-8 py-12 text-center text-[14px] text-slate-500">
              Loading schema baselines...
            </div>
          )}

          {!loading && filteredBaselines.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-300 bg-white px-8 py-14 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400">
                <FileSpreadsheet size={24} />
              </div>
              <h3 className="mt-5 text-[18px] font-semibold text-slate-950">
                No baselines found
              </h3>
              <p className="mx-auto mt-2 max-w-[420px] text-[14px] leading-6 text-slate-500">
                Upload a CSV baseline or adjust your search to view registered
                schema contracts.
              </p>
            </div>
          )}

          {!loading && filteredBaselines.length > 0 && (
            <div className="grid gap-3 lg:grid-cols-2 2xl:grid-cols-3">
              {filteredBaselines.map((baseline) => {
                const fields = Object.keys(baseline.schema || {});
                const isSelected = inspectedBaseline?.id === baseline.id;
                const isActive = Boolean(baseline.is_active);
                const isActivating = activatingId === baseline.id;
                const activationDisabled =
                  isActive || isActivating || !canActivateBaseline(baseline);

                return (
                  <button
                    key={baseline.id}
                    onClick={() => setSelectedBaseline(baseline)}
                    className={`group flex min-h-[172px] flex-col justify-between rounded-lg border bg-white p-4 text-left shadow-[0_12px_34px_rgba(15,23,42,0.04)] transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50/50 hover:shadow-[0_18px_40px_rgba(15,23,42,0.06)] ${
                      isSelected
                        ? "border-slate-150 ring-2 ring-slate-100"
                        : "border-slate-200"
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-950 text-white">
                              <Database size={15} />
                            </span>
                            <span
                              className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold capitalize ${getStatusClass(
                                baseline.status,
                              )}`}
                            >
                              {baseline.status || "registered"}
                            </span>
                          </div>

                          <h3 className="mt-3 truncate text-[16px] font-semibold text-slate-950">
                            {baseline.model_name || "Unnamed model"} v
                            {baseline.version}
                          </h3>
                          <p className="mt-1 text-[12px] text-slate-500">
                            Baseline v{baseline.version} / ID #{baseline.id}
                          </p>
                        </div>

                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded-md px-2 py-0.5 text-[10px] font-semibold ${
                              isActive
                                ? "bg-emerald-100 text-emerald-700"
                                : "bg-slate-100 text-slate-500"
                            }`}
                          >
                            {isActive ? "Active" : "Inactive"}
                          </span>
                          <ArrowUpRight
                            size={18}
                            className="text-slate-300 transition group-hover:text-slate-700"
                          />
                        </div>
                      </div>

                      <div className="mt-4 grid grid-cols-3 gap-2">
                        <div className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-2">
                          <div className="text-[11px] font-medium text-slate-500">
                            Fields
                          </div>
                          <div className="mt-1 text-[16px] font-semibold text-slate-950">
                            {fields.length}
                          </div>
                        </div>

                        <div className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-2">
                          <div className="text-[11px] font-medium text-slate-500">
                            Model
                          </div>
                          <div className="mt-1 truncate text-[16px] font-semibold text-slate-950">
                            #{baseline.model_id || "-"}
                          </div>
                        </div>

                        <div className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-2">
                          <div className="text-[11px] font-medium text-slate-500">
                            Created
                          </div>
                          <div className="mt-1 truncate text-[12px] font-semibold text-slate-950">
                            {formatDate(baseline.created_at)}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {fields.slice(0, 5).map((field) => (
                        <span
                          key={field}
                          className="rounded-md border border-slate-200 bg-white px-2.5 py-0.5 text-[11px] font-medium text-slate-600"
                        >
                          {field}
                        </span>
                      ))}
                      {fields.length > 5 && (
                        <span className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-[11px] font-medium text-slate-500">
                          +{fields.length - 5} more
                        </span>
                      )}
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                      <span className="text-[11px] font-medium text-slate-500">
                        Active for this model
                      </span>
                      <span
                        role="switch"
                        aria-checked={isActive}
                        aria-disabled={activationDisabled}
                        title={
                          canActivateBaseline(baseline)
                            ? "Activate baseline"
                            : "Archived baselines cannot be activated"
                        }
                        onClick={(event) => {
                          event.stopPropagation();
                          handleActivateBaseline(baseline);
                        }}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full border transition ${
                          isActive
                            ? "bg-gray-700"
                            : "border-slate-300 bg-slate-200"
                        } ${
                          activationDisabled
                            ? "cursor-not-allowed opacity-700"
                            : "cursor-pointer hover:border-slate-400"
                        }`}
                      >
                        <span
                          className={`inline-block h-5 w-5 rounded-full bg-white shadow-sm transition ${
                            isActive ? "translate-x-5" : "translate-x-0.5"
                          }`}
                        />
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <aside className="rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)] xl:sticky xl:top-0 xl:max-h-[calc(100vh-128px)] xl:overflow-hidden">
          {inspectedBaseline ? (
            <div className="flex h-full flex-col">
              <div className="border-b border-slate-200 px-6 py-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    
                    <h2 className="text-[24px] font-semibold leading-tight text-slate-950">
                      {inspectedBaseline.model_name || "Unnamed model"} v{inspectedBaseline.version}
                    </h2>
                    <p className="mt-2 text-[13px] text-slate-500">
                      Version {inspectedBaseline.version} / Created{" "}
                      {formatDate(inspectedBaseline.created_at)}
                    </p>
                  </div>

                  
                </div>

                <div className="mt-6 grid grid-cols-3 gap-3">
                  <div className="rounded-md border border-slate-200 p-3">
                    <div className="text-[11px] font-medium text-slate-500">
                      Columns
                    </div>
                    <div className="mt-1 text-[20px] font-semibold text-slate-950">
                      {Object.keys(inspectedBaseline.schema || {}).length}
                    </div>
                  </div>
                  <div className="rounded-md border border-slate-200 p-3">
                    <div className="text-[11px] font-medium text-slate-500">
                      Profiles
                    </div>
                    <div className="mt-1 text-[20px] font-semibold text-slate-950">
                      {Object.keys(inspectedBaseline.profile || {}).length}
                    </div>
                  </div>
                  <div className="rounded-md border border-slate-200 p-3">
                    <div className="text-[11px] font-medium text-slate-500">
                      Status
                    </div>
                    <div className="mt-2 truncate text-[13px] font-semibold capitalize text-emerald-700">
                      {inspectedBaseline.status || "registered"}
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 px-4 py-3">
                  <div>
                    <div className="text-[13px] font-semibold text-slate-950">
                      Baseline activation
                    </div>
                    <p className="mt-1 text-[12px] text-slate-500">
                      One active baseline is allowed per model.
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={
                      inspectedBaseline.is_active ||
                      activatingId === inspectedBaseline.id ||
                      !canActivateBaseline(inspectedBaseline)
                    }
                    onClick={() => handleActivateBaseline(inspectedBaseline)}
                    className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full border transition ${
                      inspectedBaseline.is_active
                        ? "bg-gray-700"
                        : "border-slate-300 bg-slate-200"
                    } disabled:cursor-not-allowed disabled:opacity-100`}
                    aria-label="Activate inspected baseline"
                  >
                    <span
                      className={`inline-block h-6 w-6 rounded-full bg-white shadow-sm transition ${
                        inspectedBaseline.is_active
                          ? "translate-x-5"
                          : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>
              </div>

              <div className="flex-1 space-y-6 overflow-y-auto px-6 py-6">
                <div>
                  <h3 className="mb-3 text-[13px] font-semibold text-slate-950">
                    Schema Fields
                  </h3>

                  <div className="space-y-2">
                    {Object.entries(inspectedBaseline.schema || {}).map(
                      ([name, dtype]) => (
                        <div
                          key={name}
                          className="flex items-center justify-between gap-3 rounded-md border border-slate-200 bg-slate-50 px-4 py-3"
                        >
                          <span className="min-w-0 truncate text-[13px] font-semibold text-slate-800">
                            {name}
                          </span>
                          <span className="shrink-0 rounded-md border border-slate-200 bg-white px-2.5 py-1 font-mono text-[11px] text-slate-600">
                            {dtype}
                          </span>
                        </div>
                      ),
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="mb-3 text-[13px] font-semibold text-slate-950">
                    Field Profiles
                  </h3>

                  <div className="space-y-3">
                    {Object.entries(inspectedBaseline.profile || {}).map(
                      ([name, profile]) => (
                        <div
                          key={name}
                          className="rounded-md border border-slate-200 p-4"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="min-w-0">
                              <div className="truncate text-[14px] font-semibold text-slate-950">
                                {name}
                              </div>
                              <p className="mt-1 text-[12px] leading-5 text-slate-500">
                                {getProfileSummary(profile)}
                              </p>
                            </div>
                            <span className="rounded-md bg-slate-100 px-2.5 py-1 font-mono text-[11px] text-slate-600">
                              {profile.type || "unknown"}
                            </span>
                          </div>

                          {profile.type !== "numeric" && (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {(profile.unique_values || [])
                                .slice(0, 6)
                                .map((value, index) => (
                                  <span
                                    key={`${value}-${index}`}
                                    className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600"
                                  >
                                    {String(value)}
                                  </span>
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
          ) : (
            <div className="flex min-h-[420px] flex-col items-center justify-center px-8 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400">
                <Database size={24} />
              </div>
              <h3 className="mt-5 text-[18px] font-semibold text-slate-950">
                Select a baseline
              </h3>
              <p className="mt-2 max-w-[300px] text-[14px] leading-6 text-slate-500">
                Schema fields and profiling details will appear here.
              </p>
            </div>
          )}
        </aside>
      </section>

      {showUploadModal && (
        <UploadBaselineModal
          onClose={() => setShowUploadModal(false)}
          onUploaded={fetchBaselines}
        />
      )}
    </div>
  );
}

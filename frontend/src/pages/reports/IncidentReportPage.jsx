import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  Brain,
  CalendarClock,
  CheckCircle2,
  Database,
  Download,
  FileText,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import toast from "react-hot-toast";

import { getLatestIncidentReport } from "../../store/reportStore";

const severityClasses = {
  critical: "border-red-200 bg-red-50 text-red-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-blue-200 bg-blue-50 text-blue-700",
};

export default function IncidentReportPage() {
  const { incidentId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function loadReport() {
      try {
        setLoading(true);
        const data = await getLatestIncidentReport(incidentId);
        if (mounted) setReport(data);
      } catch (error) {
        toast.error(error.response?.data?.detail || "Failed to load report");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadReport();
    return () => {
      mounted = false;
    };
  }, [incidentId]);

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-100 px-6 py-10">
        <div className="mx-auto max-w-5xl rounded-2xl border border-slate-200 bg-white p-8 text-slate-500">
          Loading report...
        </div>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="min-h-screen bg-slate-100 px-6 py-10">
        <div className="mx-auto max-w-5xl rounded-2xl border border-slate-200 bg-white p-8">
          <Link to="/incidents" className="text-sm font-semibold text-blue-700">
            Back to incidents
          </Link>
          <p className="mt-4 text-slate-600">No report is available for this incident yet.</p>
        </div>
      </main>
    );
  }

  const content = report.content || {};
  const severity = String(content.severity || report.severity || "medium").toLowerCase();
  const severityClass = severityClasses[severity] || severityClasses.medium;
  const generatedAt = formatDate(report.created_at || content.generated_at);

  return (
    <main className="min-h-screen bg-[linear-gradient(135deg,#eef4ff_0%,#f8fafc_46%,#fff7ed_100%)] px-4 py-6 print:bg-white print:px-0 print:py-0">
      <div className="mx-auto max-w-6xl print:max-w-none">
        <div className="mb-5 flex items-center justify-between gap-3 print:hidden">
          <Link
            to="/incidents"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            <ArrowLeft size={16} />
            Back to incidents
          </Link>
          <button
            type="button"
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800"
          >
            <Download size={16} />
            Download PDF
          </button>
        </div>

        <article className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.10)] print:rounded-none print:border-0 print:shadow-none">
          <header className="border-b border-slate-200 bg-slate-950 px-8 py-8 text-white print:bg-white print:text-slate-950">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-blue-100 print:border-slate-200 print:bg-slate-50 print:text-slate-600">
                  <FileText size={14} />
                  OpsSight Production Report
                </div>
                <h1 className="mt-5 max-w-4xl text-4xl font-black tracking-[-0.04em]">
                  {report.title}
                </h1>
                <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-300 print:text-slate-600">
                  {report.executive_summary}
                </p>
              </div>
              <div className="rounded-2xl border border-white/15 bg-white/10 p-4 text-sm print:border-slate-200 print:bg-slate-50">
                <p className="text-xs uppercase tracking-[0.14em] text-slate-300 print:text-slate-500">
                  Report version
                </p>
                <p className="mt-1 text-2xl font-black">v{report.version}</p>
                <p className="mt-3 text-xs text-slate-300 print:text-slate-500">{generatedAt}</p>
              </div>
            </div>
          </header>

          <section className="grid gap-4 border-b border-slate-200 bg-slate-50 px-8 py-5 md:grid-cols-4 print:bg-white">
            <SummaryTile icon={AlertTriangle} label="Severity" value={severity} className={severityClass} />
            <SummaryTile icon={Database} label="Run" value={`#${content.run_context?.run_id || report.run_id}`} />
            <SummaryTile icon={Brain} label="RCA source" value={content.root_cause?.provider || "stored evidence"} />
            <SummaryTile icon={ShieldCheck} label="Report status" value={content.remediation?.report_status || report.status} />
          </section>

          <section className="grid gap-8 px-8 py-8 lg:grid-cols-[1.45fr_0.95fr]">
            <div className="space-y-7">
              <ReportSection icon={Sparkles} title="Executive Narrative">
                <ProseText text={report.narrative || content.narrative} />
              </ReportSection>

              <ReportSection icon={Brain} title="Root Cause Analysis">
                <p className="text-sm leading-7 text-slate-700">
                  {content.root_cause?.summary || "No root-cause summary was stored."}
                </p>
                <TagRow items={content.root_cause?.failure_types || []} />
              </ReportSection>

              <ReportSection icon={AlertTriangle} title="Key Findings">
                <div className="space-y-3">
                  {(content.findings || []).length > 0 ? (
                    content.findings.map((finding, index) => (
                      <div key={`${finding.title}-${index}`} className="rounded-xl border border-slate-200 p-4">
                        <div className="flex items-start justify-between gap-3">
                          <p className="font-semibold text-slate-950">{finding.title}</p>
                          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-bold uppercase text-slate-600">
                            {finding.severity}
                          </span>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-600">
                          {stringifySummary(finding.summary)}
                        </p>
                        <TagRow items={(finding.affected_columns || []).filter(Boolean)} />
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-500">No structured findings were stored.</p>
                  )}
                </div>
              </ReportSection>
            </div>

            <aside className="space-y-5">
              <ReportSection icon={CalendarClock} title="Timeline">
                <div className="space-y-4">
                  {(content.timeline || []).map((item, index) => (
                    <div key={`${item.label}-${index}`} className="border-l-2 border-blue-200 pl-4">
                      <p className="text-sm font-semibold text-slate-950">{item.label}</p>
                      <p className="mt-1 text-xs text-slate-500">{formatDate(item.time)}</p>
                      <p className="mt-1 text-sm leading-6 text-slate-600">{item.detail}</p>
                    </div>
                  ))}
                </div>
              </ReportSection>

              <ReportSection icon={ShieldCheck} title="Remediation">
                <KeyValue label="Action type" value={content.remediation?.action_type} />
                <KeyValue label="Mode" value={content.remediation?.action_mode} />
                <KeyValue label="Status" value={content.remediation?.report_status} />
                <KeyValue label="Candidate" value={content.remediation?.candidate_model_uri} />
                <KeyValue label="Staged" value={content.remediation?.staged_model_uri} />
                <KeyValue label="Deployed" value={content.remediation?.deployed_model_uri} />
              </ReportSection>

              <ReportSection icon={Database} title="Model and Run Context">
                <KeyValue label="Model" value={content.model_context?.model_name} />
                <KeyValue label="Framework" value={content.model_context?.framework} />
                <KeyValue label="Training mode" value={content.model_context?.training_mode} />
                <KeyValue label="MLflow model" value={content.model_context?.mlflow_model_name} />
                <KeyValue label="Baseline" value={content.run_context?.baseline_version} />
                <KeyValue label="Cleaned data" value={content.run_context?.cleaned_data_path} />
              </ReportSection>

              <ReportSection icon={CheckCircle2} title="Next Actions">
                <ol className="space-y-2 text-sm leading-6 text-slate-700">
                  {(content.next_actions || []).map((action, index) => (
                    <li key={`${action}-${index}`} className="flex gap-2">
                      <span className="font-bold text-blue-700">{index + 1}.</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ol>
              </ReportSection>
            </aside>
          </section>

          <section className="border-t border-slate-200 px-8 py-6">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Evidence Hash
            </p>
            <p className="mt-2 break-all font-mono text-xs text-slate-500">{report.evidence_hash}</p>
          </section>
        </article>
      </div>
    </main>
  );
}

function SummaryTile({ icon: Icon, label, value, className = "border-slate-200 bg-white text-slate-800" }) {
  return (
    <div className={`rounded-2xl border p-4 ${className}`}>
      <Icon size={16} />
      <p className="mt-3 text-xs font-semibold uppercase tracking-[0.12em] opacity-70">{label}</p>
      <p className="mt-1 text-lg font-black capitalize">{value || "Unknown"}</p>
    </div>
  );
}

function ReportSection({ icon: Icon, title, children }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
          <Icon size={16} />
        </div>
        <h2 className="text-sm font-black uppercase tracking-[0.12em] text-slate-700">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function ProseText({ text }) {
  return (
    <div className="space-y-3">
      {String(text || "No narrative was generated.")
        .split("\n")
        .filter(Boolean)
        .map((paragraph, index) => (
          <p key={index} className="text-sm leading-7 text-slate-700">
            {paragraph}
          </p>
        ))}
    </div>
  );
}

function KeyValue({ label, value }) {
  return (
    <div className="border-b border-slate-100 py-2 last:border-b-0">
      <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold text-slate-800">{value || "Not available"}</p>
    </div>
  );
}

function TagRow({ items }) {
  if (!Array.isArray(items) || items.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {items.slice(0, 10).map((item) => (
        <span key={String(item)} className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
          {String(item)}
        </span>
      ))}
    </div>
  );
}

function formatDate(value) {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString();
}

function stringifySummary(value) {
  if (!value) return "No summary available.";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

import { useEffect, useState } from "react";
import { Database, CheckCircle2, XCircle, FileSearch, Filter } from "lucide-react";
import { getDataQualityFindings } from "../../store/dataQualityStore";

export default function DataQualityPage() {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);

  // ==========================================
  // LOAD DATA QUALITY FINDINGS
  // ==========================================
  const loadFindings = async () => {
    try {
      setLoading(true);
      const data = await getDataQualityFindings();
      setFindings(data);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFindings();
  }, []);

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[34px] font-semibold tracking-[-0.04em] text-[#111827]">
            Data Quality
          </h1>
          <p className="mt-2 max-w-[720px] text-[15px] leading-7 text-gray-500">
            Monitor the health and integrity of incoming inference data. 
            Review schema validations, missing values, and type mismatches detected during pipeline runs.
          </p>
        </div>
        <button
          onClick={loadFindings}
          className="flex items-center gap-3 rounded-2xl border border-black/[0.05] bg-white px-5 py-3 text-[13px] font-medium text-[#111827] shadow-sm transition hover:bg-[#f7f8fb]"
        >
          <Database size={16} />
          Refresh Validations
        </button>
      </div>

      {/* STATS ROW (Mocked for now, can be computed from findings) */}
      <div className="grid grid-cols-3 gap-6">
        <div className="rounded-3xl border border-black/[0.05] bg-white p-6 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-green-50 flex items-center justify-center text-green-600">
              <CheckCircle2 size={18} />
            </div>
            <span className="text-[13px] font-medium text-gray-500 uppercase tracking-wider">Passed Checks</span>
          </div>
          <p className="text-3xl font-semibold text-[#111827]">{findings.filter(f => f.success).length}</p>
        </div>
        
        <div className="rounded-3xl border border-black/[0.05] bg-white p-6 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-red-50 flex items-center justify-center text-red-600">
              <XCircle size={18} />
            </div>
            <span className="text-[13px] font-medium text-gray-500 uppercase tracking-wider">Failed Checks</span>
          </div>
          <p className="text-3xl font-semibold text-[#111827]">{findings.filter(f => !f.success).length}</p>
        </div>

        <div className="rounded-3xl border border-black/[0.05] bg-white p-6 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
              <FileSearch size={18} />
            </div>
            <span className="text-[13px] font-medium text-gray-500 uppercase tracking-wider">Total Validations</span>
          </div>
          <p className="text-3xl font-semibold text-[#111827]">{findings.length}</p>
        </div>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="rounded-3xl border border-black/[0.05] bg-white p-12 text-center text-[14px] text-gray-500 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          Loading Data Quality Findings...
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && findings.length === 0 && (
        <div className="rounded-3xl border border-dashed border-black/[0.08] bg-white p-16 text-center shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gray-50 mb-4 border border-gray-100">
            <Database size={28} className="text-gray-400" />
          </div>
          <h3 className="text-[18px] font-semibold text-[#111827]">
            No Validations Found
          </h3>
          <p className="mt-2 text-[14px] text-gray-500 max-w-sm mx-auto">
            Data quality checks will appear here once inference pipelines start processing data.
          </p>
        </div>
      )}

      {/* DATA TABLE */}
      {!loading && findings.length > 0 && (
        <div className="overflow-hidden rounded-3xl border border-black/[0.05] bg-white shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          
          {/* TABLE TOOLBAR */}
          <div className="flex items-center justify-between border-b border-black/[0.04] px-6 py-4">
             <h3 className="text-[15px] font-medium text-[#111827]">Recent Validations</h3>
             <button className="flex items-center gap-2 text-xs font-medium text-gray-500 hover:text-gray-900">
               <Filter size={14} /> Filter
             </button>
          </div>

          <table className="w-full text-left text-[14px]">
            <thead className="bg-[#f7f8fb] text-[12px] font-medium uppercase tracking-[0.1em] text-gray-500">
              <tr>
                <th className="px-6 py-5">Result</th>
                <th className="px-6 py-5">Feature / Column</th>
                <th className="px-6 py-5">Check Type</th>
                <th className="px-6 py-5">Run ID</th>
                <th className="px-6 py-5 text-right">Detected At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/[0.04]">
              {findings.map((finding) => (
                <tr
                  key={finding.id}
                  className="transition hover:bg-[#f7f8fb]/50 group"
                >
                  <td className="px-6 py-5">
                    {finding.success ? (
                      <div className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                        <CheckCircle2 size={14} className="mr-1.5" />
                        Passed
                      </div>
                    ) : (
                      <div className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200">
                        <XCircle size={14} className="mr-1.5" />
                        Failed
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-5">
                    <span className="font-mono text-[13px] bg-gray-50 px-2 py-1 rounded text-gray-700 border border-gray-100">
                      {finding.column_name || "N/A"}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    <span className="text-gray-600 font-medium">
                      {finding.check_type}
                    </span>
                    {/* DETAILS PREVIEW IF ANY */}
                    {finding.details && !finding.success && (
                      <p className="text-xs text-red-500 mt-1">
                        {JSON.stringify(finding.details)}
                      </p>
                    )}
                  </td>
                  <td className="px-6 py-5 text-gray-600">
                    <a href={`/pipelines?run=${finding.pipeline_run_id}`} className="hover:text-blue-600 hover:underline">
                      #{finding.pipeline_run_id}
                    </a>
                  </td>
                  <td className="px-6 py-5 text-right text-gray-500">
                    {new Date(finding.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

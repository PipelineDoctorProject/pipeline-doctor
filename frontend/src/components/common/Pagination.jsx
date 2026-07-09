import React from "react";

export default function Pagination({
  page,
  pageSize,
  totalCount,
  onPageChange,
  loading = false,
}) {
  if (totalCount === 0) return null;

  const startIndex = (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, totalCount);

  return (
    <div className="flex items-center justify-between border-t border-slate-200 bg-white px-6 py-3">
      <div className="text-sm text-slate-500">
        Showing <span className="font-medium">{startIndex}</span> to{" "}
        <span className="font-medium">{endIndex}</span> of{" "}
        <span className="font-medium">{totalCount}</span> results
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page === 1 || loading}
          className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition"
        >
          Previous
        </button>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page * pageSize >= totalCount || loading}
          className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition"
        >
          Next
        </button>
      </div>
    </div>
  );
}

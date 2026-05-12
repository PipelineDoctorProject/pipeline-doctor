export default function SchemaPage() {
  const schemaColumns = [
    {
      name: "customer_id",
      dtype: "integer",
      nullable: false,
      unique: true,
      status: "Validated",
    },
    {
      name: "age",
      dtype: "integer",
      nullable: false,
      unique: false,
      status: "Validated",
    },
    {
      name: "monthly_income",
      dtype: "float",
      nullable: false,
      unique: false,
      status: "Validated",
    },
    {
      name: "employment_type",
      dtype: "string",
      nullable: true,
      unique: false,
      status: "Validated",
    },
    {
      name: "loan_default",
      dtype: "boolean",
      nullable: false,
      unique: false,
      status: "Target",
    },
  ];

  return (
    <div className="min-h-screen bg-[#f6f8fb] px-8 py-8">
      {/* TOP HEADER */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-black/[0.05] bg-white px-3 py-1 text-[10px] font-medium uppercase tracking-[0.2em] text-gray-500 shadow-sm">
            Schema Governance
          </div>

          <h1 className="text-[34px] font-semibold tracking-[-0.05em] text-[#111827]">
            Baseline Schema
          </h1>

          <p className="mt-2 max-w-[760px] text-[14px] leading-7 text-gray-500">
            Upload and manage your baseline/reference dataset schema for data
            quality validation, schema evolution detection, drift monitoring,
            and production observability.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button className="rounded-2xl border border-black/[0.05] bg-white px-5 py-3 text-[13px] font-medium text-[#111827] shadow-sm transition hover:bg-[#f3f4f6]">
            Download Template
          </button>

          <button className="rounded-2xl bg-[#111827] px-5 py-3 text-[13px] font-medium text-white shadow-[0_10px_40px_rgba(17,24,39,0.12)] transition hover:bg-black">
            Upload Baseline CSV
          </button>
        </div>
      </div>

      {/* SUCCESS INFO */}
      <div className="mb-8 overflow-hidden rounded-[24px] border border-[#dbeafe] bg-gradient-to-r from-[#eff6ff] to-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-8">
          <div>
            <div className="mb-3 inline-flex rounded-full border border-[#bfdbfe] bg-white px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#2563eb]">
              Baseline Ready
            </div>

            <h2 className="text-[26px] font-semibold tracking-[-0.04em] text-[#111827]">
              Your baseline dataset is active.
            </h2>

            <p className="mt-3 max-w-[720px] text-[14px] leading-7 text-gray-600">
              PipelineDoctor will compare all incoming production datasets
              against this approved baseline schema to detect missing columns,
              new columns, datatype mismatches, null anomalies, and schema
              evolution events.
            </p>
          </div>

          <div className="rounded-2xl border border-[#dbeafe] bg-white px-5 py-4 shadow-sm">
            <div className="text-[11px] uppercase tracking-[0.18em] text-gray-400">
              Current Version
            </div>

            <div className="mt-2 text-[26px] font-semibold tracking-[-0.04em] text-[#111827]">
              v1.0
            </div>

            <div className="mt-1 text-[12px] text-gray-500">
              Approved baseline schema
            </div>
          </div>
        </div>
      </div>

      {/* METRICS */}
      <div className="mb-8 grid grid-cols-4 gap-5">
        <div className="rounded-[24px] border border-black/[0.05] bg-white p-6 shadow-sm">
          <div className="text-[11px] uppercase tracking-[0.18em] text-gray-400">
            Total Columns
          </div>

          <div className="mt-3 text-[34px] font-semibold tracking-[-0.05em] text-[#111827]">
            5
          </div>

          <div className="mt-2 text-[13px] text-gray-500">
            Schema feature count
          </div>
        </div>

        <div className="rounded-[24px] border border-black/[0.05] bg-white p-6 shadow-sm">
          <div className="text-[11px] uppercase tracking-[0.18em] text-gray-400">
            Required Fields
          </div>

          <div className="mt-3 text-[34px] font-semibold tracking-[-0.05em] text-[#111827]">
            4
          </div>

          <div className="mt-2 text-[13px] text-gray-500">
            Non-null enforced
          </div>
        </div>

        <div className="rounded-[24px] border border-black/[0.05] bg-white p-6 shadow-sm">
          <div className="text-[11px] uppercase tracking-[0.18em] text-gray-400">
            Validation Rules
          </div>

          <div className="mt-3 text-[34px] font-semibold tracking-[-0.05em] text-[#111827]">
            12
          </div>

          <div className="mt-2 text-[13px] text-gray-500">
            Active quality checks
          </div>
        </div>

        <div className="rounded-[24px] border border-black/[0.05] bg-white p-6 shadow-sm">
          <div className="text-[11px] uppercase tracking-[0.18em] text-gray-400">
            Monitoring Status
          </div>

          <div className="mt-3 inline-flex rounded-full border border-green-100 bg-green-50 px-4 py-2 text-[13px] font-medium text-green-700">
            Active
          </div>

          <div className="mt-3 text-[13px] text-gray-500">
            Production validation enabled
          </div>
        </div>
      </div>

      {/* MAIN GRID */}
      <div className="grid grid-cols-[1.4fr_0.6fr] gap-6">
        {/* SCHEMA TABLE */}
        <div className="overflow-hidden rounded-[28px] border border-black/[0.05] bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-black/[0.05] px-7 py-6">
            <div>
              <h3 className="text-[22px] font-semibold tracking-[-0.04em] text-[#111827]">
                Schema Definition
              </h3>

              <p className="mt-1 text-[13px] text-gray-500">
                Approved baseline schema structure and validation metadata.
              </p>
            </div>

            <input
              placeholder="Search column"
              className="h-[44px] w-[220px] rounded-xl border border-black/[0.05] bg-[#f8fafc] px-4 text-[13px] outline-none focus:border-[#111827]/20"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] border-collapse">
              <thead>
                <tr className="border-b border-black/[0.05] bg-[#fafafa] text-left">
                  <th className="px-7 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                    Column
                  </th>

                  <th className="px-7 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                    Data Type
                  </th>

                  <th className="px-7 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                    Nullable
                  </th>

                  <th className="px-7 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                    Unique
                  </th>

                  <th className="px-7 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-400">
                    Status
                  </th>
                </tr>
              </thead>

              <tbody>
                {schemaColumns.map((column) => (
                  <tr
                    key={column.name}
                    className="border-b border-black/[0.04] transition hover:bg-[#fafafa]"
                  >
                    <td className="px-7 py-5">
                      <div className="font-medium text-[#111827]">
                        {column.name}
                      </div>
                    </td>

                    <td className="px-7 py-5">
                      <div className="inline-flex rounded-full border border-black/[0.06] bg-[#f8fafc] px-3 py-1 text-[12px] font-medium text-[#111827]">
                        {column.dtype}
                      </div>
                    </td>

                    <td className="px-7 py-5 text-[13px] text-gray-600">
                      {column.nullable ? "Yes" : "No"}
                    </td>

                    <td className="px-7 py-5 text-[13px] text-gray-600">
                      {column.unique ? "Yes" : "No"}
                    </td>

                    <td className="px-7 py-5">
                      <div
                        className={`inline-flex rounded-full px-3 py-1 text-[12px] font-medium ${
                          column.status === "Target"
                            ? "bg-purple-50 text-purple-700"
                            : "bg-green-50 text-green-700"
                        }`}
                      >
                        {column.status}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT SIDEBAR */}
        <div className="space-y-6">
          {/* UPLOAD CARD */}
          <div className="rounded-[28px] border border-dashed border-[#cbd5e1] bg-white p-7 shadow-sm">
            <div className="mb-4 inline-flex rounded-full border border-black/[0.05] bg-[#f8fafc] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-gray-500">
              Upload Dataset
            </div>

            <h3 className="text-[24px] font-semibold tracking-[-0.04em] text-[#111827]">
              Upload baseline CSV
            </h3>

            <p className="mt-3 text-[13px] leading-7 text-gray-500">
              Upload your approved reference dataset to generate schema
              profiles, validation rules, and monitoring baselines.
            </p>

            <div className="mt-6 rounded-2xl border border-dashed border-[#cbd5e1] bg-[#f8fafc] px-6 py-10 text-center">
              <div className="text-[14px] font-medium text-[#111827]">
                Drag & drop CSV file
              </div>

              <div className="mt-2 text-[12px] text-gray-500">
                Supports .csv baseline datasets
              </div>
            </div>

            <button className="mt-5 w-full rounded-2xl bg-[#111827] px-5 py-4 text-[13px] font-medium text-white transition hover:bg-black">
              Select File
            </button>
          </div>

          {/* VALIDATION INFO */}
          <div className="rounded-[28px] border border-black/[0.05] bg-white p-7 shadow-sm">
            <div className="mb-4 inline-flex rounded-full border border-black/[0.05] bg-[#f8fafc] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-gray-500">
              Validation Engine
            </div>

            <div className="space-y-5">
              <div>
                <div className="text-[13px] font-medium text-[#111827]">
                  Missing Column Detection
                </div>

                <div className="mt-1 text-[12px] leading-6 text-gray-500">
                  Detect removed or unavailable production features.
                </div>
              </div>

              <div>
                <div className="text-[13px] font-medium text-[#111827]">
                  New Column Detection
                </div>

                <div className="mt-1 text-[12px] leading-6 text-gray-500">
                  Identify unexpected schema evolution changes.
                </div>
              </div>

              <div>
                <div className="text-[13px] font-medium text-[#111827]">
                  Datatype Validation
                </div>

                <div className="mt-1 text-[12px] leading-6 text-gray-500">
                  Validate incoming datasets against approved dtypes.
                </div>
              </div>

              <div>
                <div className="text-[13px] font-medium text-[#111827]">
                  Drift Monitoring
                </div>

                <div className="mt-1 text-[12px] leading-6 text-gray-500">
                  Compare production data distributions with baseline.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

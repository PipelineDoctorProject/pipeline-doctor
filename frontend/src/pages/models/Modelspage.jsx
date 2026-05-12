import { useEffect, useState, lazy, Suspense } from "react";

import { Plus } from "lucide-react";

// import { getModels } from "../../store/modelStore";

// LAZY LOAD MODAL
const RegisterModelModal = lazy(() =>
  import("./ModelRegister")
);

export default function ModelsPage() {

  const [showRegisterModal, setShowRegisterModal] = useState(false);

  const models = [
    {
      name: "Customer Churn Predictor",
      version: "v2.1.0",
      status: "Healthy",
      framework: "XGBoost",
    },
    {
      name: "Fraud Detection Engine",
      version: "v1.8.4",
      status: "Drift Detected",
      framework: "TensorFlow",
    },
    {
      name: "Demand Forecasting",
      version: "v3.0.2",
      status: "Healthy",
      framework: "LightGBM",
    },
  ];

//   useEffect(() => {

//     getModels();

//   }, []);

  return (
    <>

      <div className="space-y-8">

        {/* HEADER */}
        <div className="flex items-start justify-between">

          <div>

            <h1 className="text-[34px] font-semibold tracking-[-0.04em] text-[#111827]">

              Connected ML Models
            </h1>

            <p className="mt-2 max-w-[720px] text-[15px] leading-7 text-gray-500">

              Monitor deployed machine learning models,
              validate model versions, and manage production-ready
              ML assets across your operational infrastructure.
            </p>
          </div>

          {/* REGISTER BUTTON */}
          <button
            onClick={() => setShowRegisterModal(true)}
            className="flex items-center gap-3 rounded-2xl bg-gray-800 px-5 py-3 text-[13px] font-medium text-white shadow-[0_10px_40px_rgba(53,99,255,0.18)] transition hover:bg-[#2957f5]"
          >

            <Plus size={16} />

            Conect ML Model
          </button>
        </div>

        {/* MODEL GRID */}
        <div className="grid grid-cols-3 gap-6">

          {models.map((model, index) => (

            <div
              key={index}
              className="rounded-3xl border border-black/[0.05] bg-white p-6 transition hover:shadow-[0_20px_50px_rgba(15,23,42,0.06)]"
            >

              {/* TOP */}
              <div className="flex items-start justify-between">

                <div>

                  <h2 className="text-[18px] font-semibold text-[#111827]">

                    {model.name}
                  </h2>

                  <p className="mt-1 text-[13px] text-gray-500">

                    {model.framework}
                  </p>
                </div>

                <div
                  className={`rounded-full px-3 py-1 text-[11px] font-medium ${
                    model.status === "Healthy"
                      ? "bg-green-100 text-green-700"
                      : "bg-orange-100 text-orange-700"
                  }`}
                >

                  {model.status}
                </div>
              </div>

              {/* DETAILS */}
              <div className="mt-8 space-y-4">

                <div className="flex items-center justify-between">

                  <p className="text-[13px] text-gray-500">

                    Version
                  </p>

                  <p className="text-[13px] font-medium text-[#111827]">

                    {model.version}
                  </p>
                </div>

                <div className="flex items-center justify-between">

                  <p className="text-[13px] text-gray-500">

                    Last Updated
                  </p>

                  <p className="text-[13px] font-medium text-[#111827]">

                    2 hours ago
                  </p>
                </div>

                <div className="flex items-center justify-between">

                  <p className="text-[13px] text-gray-500">

                    Predictions
                  </p>

                  <p className="text-[13px] font-medium text-[#111827]">

                    1.2M
                  </p>
                </div>
              </div>

              {/* BUTTON */}
              <button className="mt-8 w-full rounded-2xl bg-[#f7f8fb] border border-black/[0.05] px-4 py-3 text-[13px] font-medium text-[#111827] transition hover:bg-[#eef2ff]">

                View Model
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* LAZY LOADED MODAL */}
      {showRegisterModal && (

        <Suspense
          fallback={

            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">

              <div className="rounded-2xl bg-white px-6 py-4 text-sm text-gray-600 shadow-xl">

                Loading Model Registry...
              </div>
            </div>
          }
        >

          <RegisterModelModal
            onClose={() => setShowRegisterModal(false)}
          />
        </Suspense>
      )}
    </>
  );
}
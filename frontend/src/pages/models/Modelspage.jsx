import {
  useEffect,
  useState,
  lazy,
  Suspense,
} from "react";

import { Plus } from "lucide-react";

import {
  getModels,
} from "../../store/modelStore";

// LAZY LOAD MODAL
const RegisterModelModal = lazy(() =>
  import("./ModelRegister")
);

export default function ModelsPage() {

  const [
    showRegisterModal,
    setShowRegisterModal,
  ] = useState(false);

  const [models, setModels] = useState([]);

  const [loading, setLoading] =
    useState(true);

  // ==========================================
  // LOAD TENANT MODELS
  // ==========================================
  const loadModels = async () => {

    try {

      const data =
        await getModels();

      setModels(data);

    } catch (err) {

      console.log(err);

    } finally {

      setLoading(false);
    }
  };

  // ==========================================
  // INITIAL LOAD
  // ==========================================
  useEffect(() => {

    loadModels();

  }, []);

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
            onClick={() =>
              setShowRegisterModal(true)
            }
            className="flex items-center gap-3 rounded-2xl bg-gray-800 px-5 py-3 text-[13px] font-medium text-white shadow-[0_10px_40px_rgba(53,99,255,0.18)] transition hover:bg-[#2957f5]"
          >

            <Plus size={16} />

            Conect ML Model
          </button>
        </div>

        {/* LOADING */}
        {loading && (

          <div className="rounded-3xl border border-black/[0.05] bg-white p-8 text-[14px] text-gray-500">

            Loading Models...
          </div>
        )}

        {/* EMPTY */}
        {!loading &&
          models.length === 0 && (

          <div className="rounded-3xl border border-dashed border-black/[0.08] bg-white p-12 text-center">

            <h3 className="text-[18px] font-semibold text-[#111827]">

              No Models Connected
            </h3>

            <p className="mt-2 text-[14px] text-gray-500">

              Connect your first MLflow model
              to start monitoring production
              behavior and drift.
            </p>
          </div>
        )}

        {/* MODEL GRID */}
        {!loading &&
          models.length > 0 && (

          <div className="grid grid-cols-3 gap-6">

            {models.map(
              (model, index) => (

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

                  <div className="rounded-full bg-green-100 px-3 py-1 text-[11px] font-medium text-green-700">

                    Healthy
                  </div>
                </div>

                {/* DETAILS */}
                <div className="mt-8 space-y-4">

                  <div className="flex items-center justify-between">

                    <p className="text-[13px] text-gray-500">

                      Version
                    </p>

                    <p className="text-[13px] font-medium text-[#111827]">

                      v{model.version}
                    </p>
                  </div>

                  <div className="flex items-center justify-between">

                    <p className="text-[13px] text-gray-500">

                      Registry
                    </p>

                    <p className="max-w-[160px] truncate text-[13px] font-medium text-[#111827]">

                      MLflow
                    </p>
                  </div>

                  <div className="flex items-center justify-between">

                    <p className="text-[13px] text-gray-500">

                      Framework
                    </p>

                    <p className="text-[13px] font-medium text-[#111827]">

                      {model.framework}
                    </p>
                  </div>
                </div>

                {/* BUTTON */}
                <button className="mt-8 w-full rounded-2xl border border-black/[0.05] bg-[#f7f8fb] px-4 py-3 text-[13px] font-medium text-[#111827] transition hover:bg-[#eef2ff]">

                  View Model
                </button>
              </div>
            ))}
          </div>
        )}
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
            onClose={() => {

              setShowRegisterModal(false);

              // REFRESH AFTER REGISTER
              loadModels();
            }}
          />
        </Suspense>
      )}
    </>
  );
}
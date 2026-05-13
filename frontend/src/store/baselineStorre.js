import api from "../api/client";
// ==========================================
// GET BASELINES
// ==========================================
export const getBaselines = async () => {
  const response = await api.get("/baselines/");

  return response.data;
};

// ==========================================
// UPLOAD BASELINE
// ==========================================
export const uploadBaseline = async (
  modelId,
  file,
) => {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post(
    `/baseline/upload?model_id=${modelId}`,
    formData,
    {
      headers: {
        "Content-Type":
          "multipart/form-data",
      },
    },
  );

  return response.data;
};
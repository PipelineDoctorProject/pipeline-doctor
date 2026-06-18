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

// ==========================================
// ACTIVATE BASELINE
// ==========================================
export const activateBaseline = async (
  baselineId,
) => {
  const response = await api.patch(
    `/baselines/${baselineId}/activate`,
  );

  return response.data;
};

export const getPendingSchemaEvents = async (modelId) => {
  if (!modelId) return [];

  const response = await api.get(`/schema/pending/${modelId}`);
  return response.data;
};

export const approveSchemaChange = async (
  eventId,
  approvedFeatureColumns = [],
) => {
  const response = await api.post(`/schema/approve/${eventId}`, {
    approved_feature_columns: approvedFeatureColumns,
  });

  return response.data;
};

export const rejectSchemaChange = async (eventId) => {
  const response = await api.post(`/schema/reject/${eventId}`);
  return response.data;
};

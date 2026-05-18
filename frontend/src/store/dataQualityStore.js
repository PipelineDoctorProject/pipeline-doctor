import api from "../api/client";

export const getDataQualityFindings = async (modelId) => {
  const response = await api.get("/data-quality/", {
    params: modelId && modelId !== "all" ? { model_id: modelId } : {},
  });
  return response.data;
};

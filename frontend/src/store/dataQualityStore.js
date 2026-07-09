import api from "../api/client";

export const getDataQualityFindings = async (modelId, skip = 0, limit = 10) => {
  const params = { skip, limit };
  if (modelId && modelId !== "all") {
    params.model_id = modelId;
  }
  const response = await api.get("/data-quality/", { params });
  return response.data;
};

export const getDataQualityExplanation = async (runId) => {
  const response = await api.get("/data-quality/explain", {
    params: { run_id: runId },
  });
  return response.data;
};

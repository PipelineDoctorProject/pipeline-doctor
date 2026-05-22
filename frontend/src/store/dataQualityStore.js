import api from "../api/client";

export const getDataQualityFindings = async (modelId) => {
  const response = await api.get("/data-quality/", {
    params: modelId && modelId !== "all" ? { model_id: modelId } : {},
  });
  return response.data;
};

export const getDataQualityExplanation = async (runId) => {
  const response = await api.get("/data-quality/explain", {
    params: { run_id: runId },
  });
  return response.data;
};

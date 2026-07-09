import api from "../api/client";

export const getDriftFindings = async (modelId, skip = 0, limit = 10) => {
  const params = { skip, limit };
  if (modelId && modelId !== "all") {
    params.model_id = modelId;
  }
  const response = await api.get("/drift-findings/", { params });
  return response.data;
};

export const getDriftFindingsByRun = async (runId, skip = 0, limit = 10) => {
  const response = await api.get("/drift-findings/", {
    params: { run_id: runId, skip, limit },
  });
  return response.data;
};

export const getDriftExplanation = async (runId) => {
  const response = await api.get("/drift-findings/explain", {
    params: { run_id: runId },
  });
  return response.data;
};

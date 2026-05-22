import api from "../api/client";

export const getDriftFindings = async (modelId) => {
  const response = await api.get("/drift-findings/", {
    params: modelId && modelId !== "all" ? { model_id: modelId } : {},
  });
  return response.data;
};

export const getDriftFindingsByRun = async (runId) => {
  const response = await api.get("/drift-findings/", {
    params: { run_id: runId },
  });
  return response.data;
};

export const getDriftExplanation = async (runId) => {
  const response = await api.get("/drift-findings/explain", {
    params: { run_id: runId },
  });
  return response.data;
};

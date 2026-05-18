import api from "../api/client";

export const getIncidents = async (modelId) => {
  const response = await api.get("/incidents/", {
    params: modelId && modelId !== "all" ? { model_id: modelId } : {},
  });
  return response.data;
};

import api from "../api/client";

export const getIncidents = async (modelId, skip = 0, limit = 10) => {
  const params = { skip, limit };
  if (modelId && modelId !== "all") {
    params.model_id = modelId;
  }
  const response = await api.get("/incidents/", { params });
  return response.data;
};

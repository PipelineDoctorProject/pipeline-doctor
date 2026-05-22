import api from "../api/client";

export const getPipelineRuns = async () => {
  const response = await api.get("/runs/");
  return response.data;
};

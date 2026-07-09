import api from "../api/client";

export const getPipelineRuns = async (skip = 0, limit = 10) => {
  const response = await api.get(`/runs/?skip=${skip}&limit=${limit}`);
  return response.data;
};

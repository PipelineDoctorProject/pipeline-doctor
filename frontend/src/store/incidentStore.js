import api from "../api/client";

export const getIncidents = async () => {
  const response = await api.get("/incidents/");
  return response.data;
};

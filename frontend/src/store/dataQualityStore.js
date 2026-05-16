import api from "../api/client";

export const getDataQualityFindings = async () => {
  const response = await api.get("/data-quality/");
  return response.data;
};
